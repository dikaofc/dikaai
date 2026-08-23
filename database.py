"""DikaAi Database - SQLite + Upstash Redis

Local: SQLite (fast, offline)
Vercel: Upstash Redis (serverless, no filesystem)
Sync: push SQLite → Redis
"""
import sqlite3
import hashlib
import time
import threading
import json
import urllib.request
import urllib.error
from pathlib import Path
from config import DB_PATH, UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN, USE_REDIS


# ============================================================
# Upstash Redis REST API Client (path-based)
# ============================================================

class UpstashRedis:
    """Minimal Upstash Redis REST API client (path-based)."""

    def __init__(self, url, token):
        self.url = url.rstrip('/')
        self.token = token

    def _api(self, cmd, *args):
        """Execute a Redis command via path-based REST API.
        Uses URL encoding to handle special characters in values.
        """
        import urllib.parse
        parts = [urllib.parse.quote(str(a), safe='') for a in args]
        path = '/'.join([cmd] + parts)
        req = urllib.request.Request(
            f"{self.url}/{path}",
            headers={'Authorization': f'Bearer {self.token}'}
        )
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read().decode('utf-8'))
            return data.get('result', data)
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='ignore')
            raise Exception(f"Redis error {e.code}: {body}")

    def get(self, key):
        return self._api('get', key)

    def set(self, key, value, ex=None):
        if ex:
            return self._api('set', key, value, 'EX', ex)
        return self._api('set', key, value)

    def del_key(self, key):
        return self._api('del', key)

    def exists(self, key):
        return self._api('exists', key)

    def incr(self, key):
        return self._api('incr', key)

    def ping(self):
        return self._api('ping')

    def hset(self, key, *args):
        """HSET key field1 value1 field2 value2 ..."""
        return self._api('hset', key, *args)

    def hget(self, key, field):
        return self._api('hget', key, field)

    def hgetall(self, key):
        result = self._api('hgetall', key)
        if isinstance(result, list):
            d = {}
            for i in range(0, len(result), 2):
                d[result[i]] = result[i+1]
            return d
        return result if isinstance(result, dict) else {}

    def zadd(self, key, score, member):
        return self._api('zadd', key, score, member)

    def zrange(self, key, start, end, withscores=False):
        if withscores:
            return self._api('zrange', key, start, end, 'WITHSCORES')
        return self._api('zrange', key, start, end)

    def zcard(self, key):
        return self._api('zcard', key)

    def lpush(self, key, *values):
        results = []
        for v in values:
            results.append(self._api('lpush', key, v))
        return results[-1] if results else 0

    def lrange(self, key, start, end):
        return self._api('lrange', key, start, end)

    def llen(self, key):
        return self._api('llen', key)

    def ltrim(self, key, start, end):
        return self._api('ltrim', key, start, end)

    def sadd(self, key, *members):
        results = []
        for m in members:
            results.append(self._api('sadd', key, m))
        return results[-1] if results else 0

    def scard(self, key):
        return self._api('scard', key)

    def pipeline(self, commands):
        """Execute multiple commands sequentially (path-based doesn't support true pipelines)."""
        results = []
        for cmd_args in commands:
            try:
                result = self._api(*cmd_args)
                results.append(result)
            except Exception as e:
                results.append({'error': str(e)})
        return results

    def pipeline_cmds(self, commands):
        return self.pipeline(commands)


# ============================================================
# Redis Database (for Vercel)
# ============================================================

class RedisDB:
    """Redis-backed database for Vercel deployment.
    
    Redis schema:
    - dikaai:msgs       -> Sorted Set (score=timestamp, member=msg_hash)
    - dikaai:msg:{hash} -> Hash {chat_id, chat_title, sender, message, timestamp, processed}
    - dikaai:stats      -> Hash {total, processed, unique_chats}
    - dikaai:recent     -> List (recent messages, capped at 100)
    - dikaai:training   -> List (training history entries)
    """

    PREFIX = 'dikaai'

    def __init__(self):
        if not USE_REDIS:
            raise Exception("Redis not configured")
        self.r = UpstashRedis(UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN)
        self.lock = threading.Lock()

    def _key(self, name):
        return f"{self.PREFIX}:{name}"

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.md5(text.lower().strip().encode('utf-8')).hexdigest()

    def is_duplicate(self, message: str) -> bool:
        msg_hash = self._hash(message)
        return bool(self.r.exists(self._key(f"msg:{msg_hash}")))

    def add_message(self, chat_id, chat_title, sender_name, message, timestamp) -> bool:
        from config import MIN_MESSAGE_LEN, MAX_MESSAGE_LEN
        if len(message.strip()) < MIN_MESSAGE_LEN:
            return False
        if len(message) > MAX_MESSAGE_LEN:
            message = message[:MAX_MESSAGE_LEN]
        # Skip noise (simplified check)
        text_lower = message.lower().strip()
        if len(text_lower) < 3:
            return False

        msg_hash = self._hash(message)
        msg_key = self._key(f"msg:{msg_hash}")

        # Check if exists
        if self.r.exists(msg_key):
            return False

        # Store message
        self.r.hset(msg_key,
            'chat_id', str(chat_id),
            'chat_title', chat_title or '',
            'sender_name', sender_name or '',
            'message', message,
            'timestamp', str(timestamp),
            'processed', '0'
        )

        # Add to sorted set (by timestamp)
        self.r.zadd(self._key('msgs'), timestamp, msg_hash)

        # Add to recent list (keep last 100)
        self.r.lpush(self._key('recent'), json.dumps({
            'chat_title': chat_title or '',
            'sender': sender_name or '',
            'message': message[:100],
            'ts': timestamp
        }))
        # Trim to 100
        self.r.ltrim(self._key('recent'), 0, 99)

        # Track unique chats
        self.r.sadd(self._key('chats'), str(chat_id))
        chat_count = self.r.scard(self._key('chats'))
        if chat_count:
            self.r.set(self._key('unique_chats'), str(chat_count))

        # Update stats
        self.r.incr(self._key('total'))
        self.r.incr(self._key('unprocessed'))

        return True

    def get_stats(self) -> dict:
        total = self.r.get(self._key('total')) or 0
        processed = self.r.get(self._key('processed')) or 0
        unique_chats = self.r.get(self._key('unique_chats')) or 0
        return {
            'total': int(total),
            'processed': int(processed),
            'unprocessed': int(total) - int(processed),
            'unique_chats': int(unique_chats)
        }

    def get_all_messages(self, limit=None) -> list:
        """Get recent messages from Redis list."""
        msgs = self.r.lrange(self._key('recent'), 0, -1)
        result = []
        for m in msgs:
            try:
                data = json.loads(m) if isinstance(m, str) else {}
                result.append(data.get('message', ''))
            except Exception:
                pass
        if limit:
            return result[:limit]
        return result

    def get_recent_messages(self, limit=15) -> list:
        """Get recent messages for dashboard."""
        msgs = self.r.lrange(self._key('recent'), 0, limit - 1)
        result = []
        for m in msgs:
            try:
                data = json.loads(m) if isinstance(m, str) else {}
                msg = data.get('message', '')
                if msg:
                    result.append(msg)
            except Exception:
                pass
        return result

    def get_unprocessed(self, limit=500) -> list:
        # For training - not needed on Vercel
        return []

    def mark_processed(self, ids):
        pass

    def close(self):
        pass

class DikaDB:
    def __init__(self):
        # Auto-detect: use Redis on Vercel, SQLite locally
        if USE_REDIS:
            print("  [DB] Using Upstash Redis (Vercel mode)")
            self._redis = RedisDB()
            self.conn = None
            self.lock = threading.Lock()
            return

        self._redis = None
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.lock = threading.Lock()
        self._setup_tables()
    
    def _setup_tables(self):
        with self.lock:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    msg_hash TEXT UNIQUE NOT NULL,
                    chat_id INTEGER NOT NULL,
                    chat_title TEXT,
                    sender_name TEXT,
                    message TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    processed INTEGER DEFAULT 0,
                    length INTEGER DEFAULT 0
                );
                
                CREATE INDEX IF NOT EXISTS idx_hash ON messages(msg_hash);
                CREATE INDEX IF NOT EXISTS idx_processed ON messages(processed);
                CREATE INDEX IF NOT EXISTS idx_chat ON messages(chat_id);
                CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp);
            """)
            self.conn.commit()
    
    @staticmethod
    def _hash(text: str) -> str:
        """Generate dedup hash for a message."""
        normalized = text.lower().strip()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, message: str) -> bool:
        """Check if message already exists (anti-dupe)."""
        if self._redis:
            return self._redis.is_duplicate(message)
        msg_hash = self._hash(message)
        with self.lock:
            cur = self.conn.execute(
                "SELECT 1 FROM messages WHERE msg_hash = ?", (msg_hash,)
            )
            return cur.fetchone() is not None
    
    @staticmethod
    def _is_noise(text: str) -> bool:
        """Check if message is bot/spam noise."""
        import re
        text_lower = text.lower().strip()
        if len(text_lower) < 3:
            return True
        # Bot patterns
        noise = [
            r'^@\w*bot\b', r'^https?://', r'^t\.me/',
            r'荥|✨|🎬|🆕|🔞', r'ᴠɪᴅᴇᴏ|ʜᴅ|ɴᴇᴡ|ᴜᴘᴅᴀᴛᴇ',
            r'ᴀsᴜᴘᴀɴ|ᴛᴇʀʙᴀᴜ|ʙᴀʀᴜ', r'\*\*\[',
            r'status:\*\*', r'sɪʟᴀʜᴋᴀɴ|ᴋʟɪᴋ|ᴛᴏᴍʙᴏʟ',
            r'ᴅɪ|ʙᴀᴡᴀʜ|ᴜɴᴛᴜᴋ|ᴍᴇɴᴏɴᴛᴏɴ', r'github\)',
        ]
        for p in noise:
            if re.search(p, text_lower):
                return True
        return False

    def add_message(self, chat_id: int, chat_title: str,
                    sender_name: str, message: str, timestamp: float) -> bool:
        """Add message, returns False if duplicate or noise."""
        if self._redis:
            return self._redis.add_message(chat_id, chat_title, sender_name, message, timestamp)

        from config import MIN_MESSAGE_LEN, MAX_MESSAGE_LEN

        # Filter junk
        if len(message.strip()) < MIN_MESSAGE_LEN:
            return False
        if len(message) > MAX_MESSAGE_LEN:
            message = message[:MAX_MESSAGE_LEN]
        if self._is_noise(message):
            return False
        
        msg_hash = self._hash(message)
        
        with self.lock:
            try:
                self.conn.execute(
                    """INSERT INTO messages 
                       (msg_hash, chat_id, chat_title, sender_name, message, timestamp, length)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (msg_hash, chat_id, chat_title, sender_name,
                     message, timestamp, len(message))
                )
                self.conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False  # Duplicate
    
    def get_unprocessed(self, limit: int = 500) -> list:
        """Get unprocessed messages for training."""
        if self._redis:
            return self._redis.get_unprocessed(limit)
        with self.lock:
            cur = self.conn.execute(
                """SELECT id, message FROM messages 
                   WHERE processed = 0 
                   ORDER BY timestamp ASC 
                   LIMIT ?""", (limit,)
            )
            return cur.fetchall()
    
    def mark_processed(self, ids: list):
        """Mark messages as processed."""
        if self._redis:
            return self._redis.mark_processed(ids)
        if not ids:
            return
        with self.lock:
            placeholders = ','.join('?' * len(ids))
            self.conn.execute(
                f"UPDATE messages SET processed = 1 WHERE id IN ({placeholders})",
                ids
            )
            self.conn.commit()
    
    def get_stats(self) -> dict:
        """Get database stats."""
        if self._redis:
            return self._redis.get_stats()
        with self.lock:
            total = self.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            processed = self.conn.execute(
                "SELECT COUNT(*) FROM messages WHERE processed = 1"
            ).fetchone()[0]
            unprocessed = total - processed
            unique_chats = self.conn.execute(
                "SELECT COUNT(DISTINCT chat_id) FROM messages"
            ).fetchone()[0]
            
            return {
                'total': total,
                'processed': processed,
                'unprocessed': unprocessed,
                'unique_chats': unique_chats
            }
    
    def get_all_messages(self, limit: int = None) -> list:
        """Get all messages as text."""
        if self._redis:
            return self._redis.get_all_messages(limit)
        with self.lock:
            if limit:
                cur = self.conn.execute(
                    "SELECT message FROM messages ORDER BY timestamp ASC LIMIT ?",
                    (limit,)
                )
            else:
                cur = self.conn.execute(
                    "SELECT message FROM messages ORDER BY timestamp ASC"
                )
            return [row[0] for row in cur.fetchall()]
    
    def close(self):
        if self._redis:
            self._redis.close()
            return
        self.conn.close()
