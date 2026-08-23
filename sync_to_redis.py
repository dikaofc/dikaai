#!/usr/bin/env python3
"""DikaAi Sync - Push local SQLite data to Upstash Redis

Usage:
    python sync_to_redis.py              # One-time sync
    python sync_to_redis.py --watch      # Auto-sync every 60s
    python sync_to_redis.py --stats      # Show Redis stats only
"""
import sys
import os
import json
import time
import hashlib
import sqlite3
import urllib.request
import urllib.error
from pathlib import Path

# Load config
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    DB_PATH, MODEL_DIR, VOCAB_FILE, HISTORY_FILE,
    UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN, USE_REDIS
)


# ============================================================
# Upstash Redis Client (path-based REST API)
# ============================================================

class UpstashRedis:
    def __init__(self, url, token):
        self.url = url.rstrip('/')
        self.token = token

    def _api(self, cmd, *args):
        """Execute Redis command via path-based REST API.
        Uses urllib.parse.quote to handle special characters.
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

    def _command(self, *args):
        """Alias for _api for compatibility."""
        return self._api(*args)


# ============================================================
# Hash helper
# ============================================================

def msg_hash(text):
    return hashlib.md5(text.lower().strip().encode('utf-8')).hexdigest()


# ============================================================
# Sync functions
# ============================================================

def sync_messages(r, limit=200):
    """Sync recent messages from SQLite to Redis.
    
    Only syncs the most recent `limit` messages for speed.
    Redis is only used for dashboard display - training uses local SQLite.
    """
    if not DB_PATH.exists():
        print("  ⚠️  No local database found")
        return 0

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute("SELECT COUNT(*) FROM messages")
    total = cur.fetchone()[0]
    print(f"  📊 Local messages: {total}")

    # Get last synced timestamp from Redis
    last_synced = r.get('dikaai:last_synced_ts')
    last_synced = float(last_synced) if last_synced else 0
    print(f"  📌 Last synced: {time.ctime(last_synced) if last_synced else 'never'}")

    # Get recent messages (last N from DB)
    cur = conn.execute(
        """SELECT msg_hash, chat_id, chat_title, sender_name, 
                  message, timestamp, processed
           FROM messages 
           ORDER BY timestamp DESC 
           LIMIT ?""",
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("  ✅ No messages to sync")
        return 0

    # Only sync messages newer than last synced
    new_rows = [row for row in rows if row[5] > last_synced]
    
    if not new_rows:
        print("  ✅ No new messages since last sync")
        return 0

    print(f"  📥 Syncing {len(new_rows)} new messages...")

    synced = 0
    max_ts = last_synced
    all_recent = []
    chat_ids = set()

    for h, chat_id, chat_title, sender, message, ts, processed in new_rows:
        # Store message details
        r.hset(f"dikaai:msg:{h}",
            'chat_id', str(chat_id),
            'chat_title', (chat_title or '')[:50],
            'sender_name', (sender or '')[:30],
            'message', message[:100],
            'timestamp', str(ts),
            'processed', str(processed)
        )

        # Collect for batch push
        all_recent.append(json.dumps({
            't': (chat_title or '')[:30],
            's': (sender or '')[:20],
            'm': message[:80],
            'ts': ts
        }))
        chat_ids.add(str(chat_id))

        if ts > max_ts:
            max_ts = ts
        synced += 1

    # Push all recent messages at once
    for item in all_recent:
        r.lpush('dikaai:recent', item)

    # Add all chat IDs at once
    for cid in chat_ids:
        r.sadd('dikaai:chats', cid)

    # Trim recent to 100
    r.ltrim('dikaai:recent', 0, 99)

    # Update stats
    r.set('dikaai:total', str(total))
    r.set('dikaai:last_synced_ts', str(max_ts))

    # Count unique chats
    unique_chats = r.scard('dikaai:chats') or 0
    r.set('dikaai:unique_chats', str(unique_chats))

    print(f"  ✅ Synced {synced} messages")
    return synced


def sync_model(r):
    """Sync model checkpoint to Redis."""
    model_file = MODEL_DIR / "dikaai_latest.json"
    if not model_file.exists():
        print("  ⚠️  No model checkpoint found")
        return False

    try:
        with open(model_file, 'r') as f:
            data = json.load(f)

        embed = data.get('embedding', [])
        params = len(embed) * len(embed[0]) if embed and isinstance(embed[0], list) else 0

        r.hset('dikaai:model',
            'vocab_size', str(data.get('vocab_size', 0)),
            'step', str(data.get('step', 0)),
            'params', str(params),
            'embed_dim', str(data.get('embed_dim', 0)),
            'hidden_dim', str(data.get('hidden_dim', 0)),
            'synced_at', str(time.time())
        )
        print(f"  ✅ Model synced (step {data.get('step', 0)})")
        return True
    except Exception as e:
        print(f"  ⚠️  Model sync error: {e}")
        return False


def sync_vocab(r):
    """Sync vocab size to Redis."""
    if not VOCAB_FILE.exists():
        return False
    try:
        with open(VOCAB_FILE, 'r') as f:
            data = json.load(f)
        r.set('dikaai:vocab_size', str(data.get('vocab_size', 0)))
        print(f"  ✅ Vocab synced: {data.get('vocab_size', 0)} tokens")
        return True
    except Exception:
        return False


def sync_training_history(r):
    """Sync training history CSV to Redis."""
    if not HISTORY_FILE.exists():
        return 0

    count = 0
    try:
        import csv
        with open(HISTORY_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entry = json.dumps({
                    'ts': float(row['timestamp']),
                    'loss': float(row['loss']),
                    'steps': int(row['steps']),
                })
                r.lpush('dikaai:training', entry)
                count += 1
        # Keep last 500
        r.ltrim('dikaai:training', 0, 499)
        print(f"  ✅ Training history synced: {count} entries")
    except Exception as e:
        print(f"  ⚠️  Training history sync error: {e}")

    return count


def show_stats(r):
    """Show Redis stats."""
    print("\n" + "=" * 50)
    print("  📊 Upstash Redis Stats")
    print("=" * 50)

    total = r.get('dikaai:total') or 0
    processed = r.get('dikaai:processed') or 0
    unique_chats = r.get('dikaai:unique_chats') or 0
    vocab_size = r.get('dikaai:vocab_size') or 0
    last_synced = r.get('dikaai:last_synced_ts') or 0

    model = r.hgetall('dikaai:model')
    recent_count = r.llen('dikaai:recent')

    print(f"  Total messages  : {total}")
    print(f"  Processed       : {processed}")
    print(f"  Unique chats    : {unique_chats}")
    print(f"  Vocab size      : {vocab_size}")
    print(f"  Recent messages : {recent_count}")
    print(f"  Last synced     : {time.ctime(float(last_synced)) if last_synced else 'never'}")

    if model:
        print(f"\n  Model step      : {model.get('step', '?')}")
        print(f"  Model params    : {model.get('params', '?')}")
        synced_at = model.get('synced_at', '0')
        print(f"  Synced at       : {time.ctime(float(synced_at)) if synced_at else '?'}")

    print("=" * 50)


# ============================================================
# Main
# ============================================================

def full_sync():
    """Run full sync."""
    print("\n" + "=" * 50)
    print("  🔄 DikaAi Sync: SQLite → Redis")
    print("=" * 50)

    if not USE_REDIS:
        print("  ❌ Redis not configured!")
        print("  Set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN in .env.local")
        return

    r = UpstashRedis(UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN)

    # Test connection
    try:
        result = r.ping()
        print(f"  ✅ Redis connected! (PING: {result})")
    except Exception as e:
        print(f"  ❌ Redis connection failed: {e}")
        return

    # Sync everything
    sync_messages(r)
    sync_model(r)
    sync_vocab(r)
    sync_training_history(r)

    # Show final stats
    show_stats(r)


def watch_mode(interval=60):
    """Auto-sync every N seconds."""
    print(f"\n  👁️  Watch mode: syncing every {interval}s (Ctrl+C to stop)")
    while True:
        try:
            full_sync()
            print(f"\n  ⏳ Next sync in {interval}s...")
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n  👋 Watch stopped")
            break


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--watch':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            watch_mode(interval)
        elif sys.argv[1] == '--stats':
            if USE_REDIS:
                r = UpstashRedis(UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN)
                show_stats(r)
            else:
                print("❌ Redis not configured")
        else:
            print("Usage:")
            print("  python sync_to_redis.py           # One-time sync")
            print("  python sync_to_redis.py --watch   # Auto-sync every 60s")
            print("  python sync_to_redis.py --stats   # Show Redis stats")
    else:
        full_sync()
