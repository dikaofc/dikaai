"""DikaAI Vercel Deployment - Dashboard + Full API + Chat UI

All DikaAI functions live on Vercel:
  /                         -> Dashboard (training stats + controls)
  /chat                     -> Full Chat UI (Engine-powered)
  /docs                     -> API documentation
  /api/stats                -> Training stats (Redis/local)
  /api/chat                 -> Chat endpoint
  /api/export               -> CSV export
  /v1/health                -> Health check
  /v1/models                -> List models
  /v1/chat/completions      -> OpenAI-compatible chat
  /v1/completions           -> OpenAI-compatible completion
  /v1/agent                 -> Coding agent
  /v1/tools/read            -> Read file
  /v1/tools/search          -> Search code
  /v1/tools/run             -> Run command
  /v1/auth/token            -> Create API token
  /v1/auth/tokens           -> List tokens
  /v1/auth/revoke           -> Revoke token

Training runs on local/Colab, syncs to Redis.
Vercel serves the live AI from Redis state.
"""
import csv
import json
import io
import os
import sqlite3
import time
import sys
import re
import hashlib
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

# Import config
from dikaai.config import (
    UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN, USE_REDIS,
    DB_PATH, MODEL_DIR, VOCAB_FILE
)

# Import design templates (neobrutalism + liquid SVG icons)
from dikaai.ui.templates import dashboard_page, chat_page, docs_page

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
        embed = data.get('embedding', [])
        if embed and isinstance(embed[0], list):
            info['params'] = len(embed) * len(embed[0])
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
# Page Cache (generated from design system)
# ============================================================

_dash_cache = None
_chat_cache = None
_docs_cache = None
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


def _get_dash():
    global _dash_cache
    if _dash_cache is None:
        _dash_cache = dashboard_page()
    return _dash_cache


def _get_chat():
    global _chat_cache
    if _chat_cache is None:
        _chat_cache = chat_page()
    return _chat_cache


def _get_docs():
    global _docs_cache
    if _docs_cache is None:
        _docs_cache = docs_page()
    return _docs_cache


# ============================================================
# HTTP Handler
# ============================================================

class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler - Dashboard + Chat + Full API."""

    def log_message(self, format, *args):
        pass

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _html(self, html, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length:
            try:
                return json.loads(self.rfile.read(length))
            except Exception:
                return {}
        return {}

    def _get_token(self):
        auth = self.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            return auth[7:]
        return self.headers.get('X-API-Key', '')

    def _check_auth(self, scope=None):
        token = self._get_token()
        if not token:
            return False, {'error': 'Missing Authorization. Use: Bearer dka_xxx'}
        ta = TokenAuth()
        valid, info = ta.validate(token, scope)
        if not valid:
            return False, {'error': info}
        return True, None

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
        self.end_headers()

    # ---- GET ----

    def do_GET(self):
        path = urlparse(self.path).path

        # UI Pages
        if path == '/' or path == '/index.html':
            self._html(_get_dash())
            return
        if path == '/chat':
            self._html(_get_chat())
            return
        if path == '/docs' or path == '/api':
            self._html(_get_docs())
            return

        # Dashboard API
        if path == '/api/stats':
            stats = _get_stats()
            engine = _get_engine()
            if engine:
                try:
                    es = engine.get_stats()
                    stats['engine'] = {
                        'total': es.get('total', 0),
                        'rate': es.get('rate', '0%'),
                        'episodes': es.get('episodic', {}).get('total_episodes', 0),
                        'facts': es.get('semantic', {}).get('total_facts', 0),
                        'topics': es.get('long_context', {}).get('topics', 0),
                        'tokens': es.get('long_context', {}).get('total_tokens_stored', 0),
                    }
                except Exception:
                    pass
            self._json(stats)
            return

        if path == '/api/export':
            history = _read_history()
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['timestamp', 'datetime', 'loss', 'steps', 'total_steps', 'avg_loss', 'total_messages'])
            for h in history:
                dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(h['timestamp']))
                writer.writerow([f"{h['timestamp']:.3f}", dt, f"{h['loss']:.6f}",
                                 h['steps'], h['total_steps'], f"{h['avg_loss']:.6f}", h['total_messages']])
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="dikaai_training.csv"')
            self.end_headers()
            self.wfile.write(output.getvalue().encode())
            return

        # Public API
        if path == '/v1/health':
            engine = _get_engine()
            token = _ensure_default_token()
            self._json({
                'status': 'ok', 'version': '3.2.0', 'timestamp': time.time(),
                'engine': engine is not None, 'redis': USE_REDIS,
                'token': token,
            })
            return

        if path == '/v1/models':
            self._json({'data': [
                {'id': 'dikaai-v3', 'object': 'model',
                 'capabilities': ['chat', 'code', 'agent', 'tools', 'reasoning']}
            ]})
            return

        if path == '/v1/auth/tokens':
            ok, err = self._check_auth('admin')
            if not ok:
                self._json(err, 401)
                return
            self._json({'tokens': TokenAuth().list_tokens()})
            return

        self.send_response(404)
        self.end_headers()

    # ---- POST ----

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._body()

        if path == '/api/toggle':
            self._json({'ok': True, 'feature': body.get('feature', ''),
                        'enabled': body.get('enabled', True)})
            return

        if path == '/api/chat':
            text = body.get('message', '').strip()
            if not text:
                self._json({'error': 'empty message'}, 400)
                return
            start_t = time.time()
            r = _generate_reply(text)
            elapsed = time.time() - start_t
            response = r if isinstance(r, str) else r.get('response', str(r))
            self._json({
                'response': response, 'reply': response,
                'route': 'chat', 'topic': 'general',
                'time': f'{elapsed:.1f}s', 'success': True,
            })
            return

        # OpenAI-compatible (no auth required for easy integration)
        if path == '/v1/chat/completions':
            messages = body.get('messages', [])
            user_msg = ''
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_msg = msg.get('content', '')
                    break
            if not user_msg:
                self._json({'error': 'No user message'}, 400)
                return
            engine = _get_engine()
            if engine:
                try:
                    result = engine.process(user_msg)
                    response = result.get('response', '')
                except Exception:
                    response = _generate_reply(user_msg).get('response', '')
            else:
                response = _generate_reply(user_msg).get('response', '')
            self._json({
                'id': f'chatcmpl-{int(time.time() * 1000)}',
                'object': 'chat.completion',
                'created': int(time.time()),
                'model': 'dikaai-v3',
                'choices': [{'index': 0,
                             'message': {'role': 'assistant', 'content': response},
                             'finish_reason': 'stop'}],
                'usage': {'prompt_tokens': len(user_msg.split()),
                          'completion_tokens': len(response.split()),
                          'total_tokens': len(user_msg.split()) + len(response.split())},
            })
            return

        if path == '/v1/completions':
            prompt = body.get('prompt', '')
            if not prompt:
                self._json({'error': 'No prompt'}, 400)
                return
            response = _generate_reply(prompt).get('response', '')
            self._json({
                'id': f'cmpl-{int(time.time() * 1000)}',
                'object': 'text_completion',
                'created': int(time.time()),
                'model': 'dikaai-v3',
                'choices': [{'text': response, 'finish_reason': 'stop'}],
            })
            return

        if path == '/v1/agent':
            task = body.get('task', '') or body.get('message', '')
            if not task:
                self._json({'error': 'No task'}, 400)
                return
            engine = _get_engine()
            if engine:
                try:
                    result = engine.process(task)
                    self._json({'task': task, 'response': result.get('response', ''),
                                'route': result.get('route', ''),
                                'success': result.get('success', True)})
                except Exception as e:
                    self._json({'task': task, 'error': str(e), 'success': False})
            else:
                self._json({'task': task,
                            'response': _generate_reply(task).get('response', ''),
                            'success': True})
            return

        # Tools
        if path == '/v1/tools/read':
            file_path = body.get('path', '')
            if not file_path:
                self._json({'error': 'No path'}, 400)
                return
            try:
                full = BASE_DIR / file_path
                if full.exists() and full.is_file():
                    content = full.read_text(encoding='utf-8', errors='ignore')[:10000]
                    self._json({'path': file_path, 'content': content, 'size': len(content)})
                else:
                    self._json({'error': f'File not found: {file_path}'}, 404)
            except Exception as e:
                self._json({'error': str(e)}, 500)
            return

        if path == '/v1/tools/search':
            query = body.get('query', '') or body.get('q', '')
            if not query:
                self._json({'error': 'No query'}, 400)
                return
            matches = []
            try:
                import subprocess
                result = subprocess.run(
                    ['grep', '-rn', '--include=*.py', '--include=*.js',
                     '--include=*.ts', '-i', query, str(BASE_DIR)],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.strip().split('\n')[:20]:
                    if ':' in line:
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            matches.append({
                                'file': parts[0].replace(str(BASE_DIR) + '/', ''),
                                'line': parts[1],
                                'content': parts[2][:100]
                            })
            except Exception:
                pass
            self._json({'query': query, 'matches': matches, 'count': len(matches)})
            return

        if path == '/v1/tools/run':
            command = body.get('command', '') or body.get('cmd', '')
            if not command:
                self._json({'error': 'No command'}, 400)
                return
            safe = ['ls', 'pwd', 'echo', 'date', 'whoami', 'cat', 'head', 'tail', 'wc', 'grep']
            cmd_first = command.strip().split()[0] if command.strip() else ''
            if cmd_first not in safe:
                self._json({'error': f'Command not allowed. Allowed: {", ".join(safe)}'}, 403)
                return
            try:
                import subprocess
                result = subprocess.run(command, shell=True, capture_output=True,
                                        text=True, timeout=5, cwd=str(BASE_DIR))
                self._json({'command': command, 'stdout': result.stdout[:5000],
                            'stderr': result.stderr[:1000], 'exit_code': result.returncode})
            except Exception as e:
                self._json({'error': str(e)}, 500)
            return

        # Auth
        if path == '/v1/auth/token':
            ok, err = self._check_auth('admin')
            if not ok:
                self._json(err, 401)
                return
            name = body.get('name', 'unnamed')
            scopes = body.get('scopes', 'chat,code,agent')
            token = TokenAuth().create(name, scopes)
            if token:
                self._json({'token': token, 'name': name, 'scopes': scopes})
            else:
                self._json({'error': 'Failed to create token'}, 500)
            return

        if path == '/v1/auth/revoke':
            ok, err = self._check_auth('admin')
            if not ok:
                self._json(err, 401)
                return
            token = body.get('token', '')
            if not token:
                self._json({'error': 'No token'}, 400)
                return
            self._json({'ok': TokenAuth().revoke(token)})
            return

        self.send_response(404)
        self.end_headers()
