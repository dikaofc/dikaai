"""DikaAI Vercel API handler.

Serves ONLY the JSON API: /api/* and /v1/*.
The frontend (Dashboard, Chat, Docs) is now served by Next.js; this file
no longer renders HTML pages.

Training runs on local/Colab, syncs to Redis. Vercel serves the live AI
from Redis state.
"""
import io
import json
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

from _lib import (
    _get_redis, _get_engine, _get_stats, _generate_reply,
    _read_history, _ensure_default_token, TokenAuth,
)

# Endpoints this handler is responsible for. Anything else is a 404
# (Next.js serves the actual pages).
_API_PREFIXES = ('/api/', '/v1/', '/api', '/v1')


def _resolve_path(handler):
    """Get the real request path, robust to rewrite proxies.

    The function is mounted at /api/server via vercel.json. The `rewrites`
    send /api/* and /v1/* here, and Vercel preserves the original path in
    `self.path`. As a safety net, fall back to proxy headers if the path
    collapses to the function mount point.
    """
    path = urlparse(handler.path).path
    if path in ('/api/server', '/api/server/'):
        original = (
            handler.headers.get('x-vercel-original-url')
            or handler.headers.get('x-forwarded-path')
            or handler.headers.get('x-original-url')
        )
        if original:
            path = urlparse(original).path
    return path


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler - API only (no HTML pages)."""

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
        path = _resolve_path(self)

        # Dashboard API
        if path == '/api/stats':
            stats = _get_stats()
            engine = _get_engine()
            if engine:
                try:
                    info = engine.get_stats()
                    stats['engine'] = {
                        'total': info.get('total', 0),
                        'rate': info.get('rate', '0%'),
                        'episodes': info.get('episodic', {}).get('total_episodes', 0),
                        'facts': info.get('semantic', {}).get('total_facts', 0),
                        'topics': info.get('long_context', {}).get('topics', 0),
                        'tokens': info.get('long_context', {}).get('total_tokens_stored', 0),
                    }
                except Exception:
                    pass
            self._json(stats)
            return

        if path == '/api/export':
            history = _read_history()
            output = io.StringIO()
            writer = csv_export(history)
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
                'engine': engine is not None, 'redis': bool(_get_redis()),
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
        path = _resolve_path(self)
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
                from dikaai.security.sandbox import ToolSandbox
                sb = ToolSandbox(workspace=str(BASE_DIR))
                ok, reason = sb.check_permission(
                    __import__('dikaai.security.sandbox', fromlist=['ToolRequest']).ToolRequest(
                        'read', 'read', path=file_path))
                if not ok:
                    self._json({'error': reason}, 403)
                    return
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


def csv_export(history):
    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['timestamp', 'datetime', 'loss', 'steps', 'total_steps', 'avg_loss', 'total_messages'])
    for h in history:
        dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(h['timestamp']))
        writer.writerow([f"{h['timestamp']:.3f}", dt, f"{h['loss']:.6f}",
                         h['steps'], h['total_steps'], f"{h['avg_loss']:.6f}", h['total_messages']])
    return output


# `BASE_DIR` is referenced in tool handlers; re-export from _lib for clarity.
from _lib import BASE_DIR  # noqa: E402
