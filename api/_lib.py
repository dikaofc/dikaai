"""DikaAI shared backend library.

Holds everything the serverless handler needs that is NOT per-request:
Redis client, token auth, the ML Engine, data fetching, and reply generation.

Kept separate from api/index.py so the handler stays a thin HTTP layer.
"""
import csv
import io
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from dikaai.config import (
    UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN, USE_REDIS,
    DB_PATH, MODEL_DIR, VOCAB_FILE,
)

# Lazy-import Engine (heavy, only load when needed)
_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        try:
            from dikaai.engine import Engine
            _engine = Engine(workspace=str(BASE_DIR))
        except Exception as e:
            print(f"[ENGINE] Init error: {e}")
    return _engine


# ============================================================
# Redis Client (Upstash REST API)
# ============================================================

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None and USE_REDIS and UPSTASH_REDIS_URL:
        try:
            import urllib.request
            import urllib.parse

            class Redis:
                def __init__(self, url, token):
                    self.url = url.rstrip('/')
                    self.token = token

                def _api(self, cmd, *args):
                    parts = [urllib.parse.quote(str(a), safe='') for a in args]
                    path = '/'.join([cmd] + parts)
                    req = urllib.request.Request(
                        f"{self.url}/{path}",
                        headers={'Authorization': f'Bearer {self.token}'}
                    )
                    resp = urllib.request.urlopen(req, timeout=10)
                    data = json.loads(resp.read().decode('utf-8'))
                    return data.get('result', data)

                def get(self, key):
                    return self._api('get', key)

                def set(self, key, value, ex=None):
                    if ex:
                        return self._api('set', key, value, 'EX', ex)
                    return self._api('set', key, value)

                def hgetall(self, key):
                    result = self._api('hgetall', key)
                    if isinstance(result, list):
                        d = {}
                        for i in range(0, len(result), 2):
                            d[result[i]] = result[i + 1]
                        return d
                    return result if isinstance(result, dict) else {}

                def lrange(self, key, start, end):
                    return self._api('lrange', key, start, end)

                def lpush(self, key, *values):
                    r = 0
                    for v in values:
                        r = self._api('lpush', key, v)
                    return r

                def ltrim(self, key, start, end):
                    return self._api('ltrim', key, start, end)

                def hset(self, key, *args):
                    return self._api('hset', key, *args)

                def hget(self, key, field):
                    return self._api('hget', key, field)

                def incr(self, key):
                    return self._api('incr', key)

                def ping(self):
                    return self._api('ping')

                def exists(self, key):
                    return self._api('exists', key)

                def delete(self, key):
                    return self._api('del', key)

                def llen(self, key):
                    return self._api('llen', key)

                def scard(self, key):
                    return self._api('scard', key)

                def sadd(self, key, *members):
                    r = 0
                    for m in members:
                        r = self._api('sadd', key, m)
                    return r

            _redis_client = Redis(UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN)
        except Exception as e:
            print(f"[REDIS] Init error: {e}")
    return _redis_client


# ============================================================
# Token Auth (stored in Redis)
# ============================================================

class TokenAuth:
    def __init__(self):
        self.r = _get_redis()

    def validate(self, token, scope=None):
        if not token or not self.r:
            return False, "No token or Redis"
        try:
            info = self.r.hgetall(f"dikaai:token:{token}")
            if not info:
                return False, "Invalid token"
            if info.get('revoked') == '1':
                return False, "Token revoked"
            if scope and scope not in (info.get('scopes', '') or ''):
                return False, f"Missing scope: {scope}"
            return True, info
        except Exception:
            return False, "Token check failed"

    def create(self, name, scopes='chat,code,agent'):
        if not self.r:
            return None
        token = f"dka_{hashlib.md5(f'{name}{time.time()}'.encode()).hexdigest()[:24]}"
        self.r.hset(f"dikaai:token:{token}",
                     'name', name, 'scopes', scopes,
                     'created', str(time.time()), 'revoked', '0')
        self.r.sadd('dikaai:tokens', token)
        return token

    def list_tokens(self):
        if not self.r:
            return []
        try:
            tokens = self.r._api('smembers', 'dikaai:tokens')
            if not tokens:
                return []
            if isinstance(tokens, str):
                tokens = [tokens]
            result = []
            for t in tokens:
                info = self.r.hgetall(f"dikaai:token:{t}")
                if info:
                    result.append({
                        'token': t[:8] + '...',
                        'name': info.get('name', ''),
                        'scopes': info.get('scopes', ''),
                        'created': info.get('created', ''),
                        'revoked': info.get('revoked', '0') == '1',
                    })
            return result
        except Exception:
            return []

    def revoke(self, token):
        if not self.r:
            return False
        try:
            self.r.hset(f"dikaai:token:{token}", 'revoked', '1')
            return True
        except Exception:
            return False


# ============================================================
# Data Fetching
# ============================================================

HISTORY_FILE = BASE_DIR / "training_history.csv"


def _read_history():
    if not HISTORY_FILE.exists():
        return []
    history = []
    try:
        with open(HISTORY_FILE, 'r') as f:
            for row in csv.DictReader(f):
                history.append({
                    'timestamp': float(row['timestamp']),
                    'loss': float(row['loss']),
                    'steps': int(row['steps']),
                    'total_steps': int(row.get('total_steps', 0)),
                    'avg_loss': float(row.get('avg_loss', 0)),
                    'total_messages': int(row.get('total_messages', 0)),
                })
    except Exception:
        pass
    return history


def _get_db_stats():
    stats = {'total': 0, 'processed': 0, 'unprocessed': 0, 'unique_chats': 0}
    if not DB_PATH.exists():
        return stats
    try:
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH))
        stats['total'] = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        stats['processed'] = conn.execute("SELECT COUNT(*) FROM messages WHERE processed=1").fetchone()[0]
        stats['unprocessed'] = stats['total'] - stats['processed']
        stats['unique_chats'] = conn.execute("SELECT COUNT(DISTINCT chat_id) FROM messages").fetchone()[0]
        conn.close()
    except Exception:
        pass
    return stats


def _get_model_info():
    info = {'params': 0, 'step': 0, 'vocab_size': 0}
    model_file = MODEL_DIR / "dikaai_latest.json"
    if not model_file.exists():
        return info
    try:
        with open(model_file, 'r') as f:
            data = json.load(f)
        info['vocab_size'] = data.get('vocab_size', 0)
        info['step'] = data.get('step', 0)
        # Prefer explicit 'params' written by the (torch) model.save() sidecar.
        params = data.get('params', 0)
        if not params:
            embed = data.get('embedding', [])
            if embed and isinstance(embed[0], list):
                params = len(embed) * len(embed[0])
        info['params'] = params
    except Exception:
        pass
    return info


def _get_stats():
    r = _get_redis()
    if r:
        try:
            total = int(r.get('dikaai:total') or 0)
            processed = int(r.get('dikaai:processed') or 0)
            unique = int(r.get('dikaai:unique_chats') or 0)
            model = r.hgetall('dikaai:model')
            recent = r.lrange('dikaai:recent', 0, 14)
            history = []
            try:
                raw = r.lrange('dikaai:training', 0, -1)
                for h in (raw or []):
                    try:
                        e = json.loads(h) if isinstance(h, str) else h
                        if isinstance(e, dict) and 'loss' in e:
                            history.append(e)
                    except Exception:
                        pass
            except Exception:
                pass
            losses = [float(h.get('loss', 0)) for h in history]
            uptime = 0
            if history:
                uptime = int(time.time() - float(history[0].get('ts', 0)))
            return {
                'db': {'total': total, 'processed': processed,
                       'unprocessed': total - processed, 'unique_chats': unique},
                'model': {
                    'params': int(model.get('params', 0)),
                    'step': int(model.get('step', 0)),
                    'vocab_size': int(model.get('vocab_size', 0)),
                },
                'vocab_tokens': int(model.get('vocab_size', 0)),
                'status': 'ready' if int(model.get('step', 0)) > 0 else 'idle',
                'uptime': max(0, uptime),
                'toggles': {'auto_reply': True, 'training': True, 'scraping': True},
                'loss_chart': {
                    'timestamps': [float(h.get('ts', 0)) for h in history],
                    'losses': losses,
                    'steps': [int(h.get('steps', 0)) for h in history],
                },
                'recent_messages': [_parse_recent(m) for m in (recent or [])],
                'total_loss': sum(float(h.get('avg_loss', 0)) * int(h.get('steps', 0)) for h in history),
                'total_steps': sum(int(h.get('steps', 0)) for h in history),
                'source': 'redis',
            }
        except Exception:
            pass
    history = _read_history()
    db = _get_db_stats()
    model = _get_model_info()
    losses = [h['loss'] for h in history]
    uptime = int(time.time() - history[0]['timestamp']) if history else 0
    return {
        'db': db, 'model': model, 'vocab_tokens': model['vocab_size'],
        'status': 'ready' if model['step'] > 0 else 'idle',
        'uptime': max(0, uptime),
        'toggles': {'auto_reply': True, 'training': True, 'scraping': True},
        'loss_chart': {
            'timestamps': [h['timestamp'] for h in history],
            'losses': losses,
            'steps': [h['steps'] for h in history],
        },
        'recent_messages': [],
        'total_loss': sum(h.get('avg_loss', 0) * h.get('steps', 0) for h in history),
        'total_steps': sum(h.get('steps', 0) for h in history),
        'source': 'local',
    }


def _parse_recent(raw):
    try:
        d = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(d, dict):
            return d.get('m', d.get('message', ''))
    except Exception:
        pass
    return str(raw) if raw else ''


def _generate_reply(text):
    """Generate reply using Engine pipeline. Returns dict."""
    meta = {'route': 'chat', 'topic': 'general', 'time': '', 'success': True}

    # 1. Try code templates first
    try:
        from dikaai.coding.code_templates import match_template
        tmpl = match_template(text)
        if tmpl['matched']:
            return {
                'response': f"```python\n{tmpl['code']}\n```\n\nTemplate: {tmpl['template_name']}",
                **meta, 'route': 'code',
            }
    except Exception:
        pass

    # 2. Engine (reasoning + templates + memory)
    engine = _get_engine()
    if engine:
        try:
            result = engine.process(text)
            response = result.get('response', '')
            if _looks_like_garbage(response):
                from dikaai.coding.smart_reply import get_smart_reply
                return {'response': get_smart_reply(text), **meta}
            return {
                'response': response,
                'route': result.get('route', 'chat'),
                'topic': result.get('topic', 'general'),
                'time': result.get('time', ''),
                'success': result.get('success', True),
            }
        except Exception as e:
            print(f"[ENGINE] Error: {e}")

    # 3. Fallback: smart_reply
    try:
        from dikaai.coding.smart_reply import get_smart_reply
        return {'response': get_smart_reply(text), **meta}
    except Exception:
        return {'response': "DikaAI is processing. Please try again.", **meta, 'success': False}


def _looks_like_garbage(text):
    if not text or len(text) < 5:
        return True
    text = text.strip()
    garbage_patterns = [
        r'^[a-z_]+ [a-z_]+ [a-z_]+',
        r'\b(func|def|class|import|return|print)\b.*\b(func|def|class|import|return|print)\b',
        r'_\s*$',
        r'\b(test|error|none|null|undefined|false|true)\b.*\b(test|error|none|null|undefined|false|true)\b',
    ]
    for pat in garbage_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True
    sentences = [s.strip() for s in re.split(r'[.!?\n]', text) if s.strip()]
    if sentences:
        has_proper = any(s[0].isupper() or s.startswith('```') for s in sentences if len(s) > 3)
        if not has_proper and not text.startswith('```'):
            return True
    return False


# ============================================================
# Default token bootstrap
# ============================================================

_default_token = None


def _ensure_default_token():
    """Auto-generate API token if none exists."""
    global _default_token
    if _default_token:
        return _default_token
    try:
        r = _get_redis()
        if r:
            tokens = r._api('smembers', 'dikaai:tokens')
            if tokens and len(tokens) > 0:
                _default_token = tokens[0] if isinstance(tokens, list) else tokens
                return _default_token
        # No tokens exist, create one
        ta = TokenAuth()
        token = ta.create('dikaai-default', 'chat,code,agent,tools,admin')
        if token:
            _default_token = token
            return token
    except Exception:
        pass
    return None


# `re` is imported lazily via _looks_like_garbage; ensure it is available here.
import re  # noqa: E402
