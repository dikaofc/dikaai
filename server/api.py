"""
DikaAI Public API - OpenAI-compatible REST API

Endpoints:
  POST /v1/chat/completions    - Chat (OpenAI-compatible)
  POST /v1/completions         - Completion (OpenAI-compatible)
  POST /v1/agent               - Coding agent
  GET  /v1/models              - List models
  GET  /v1/health              - Health check

  POST /v1/auth/token          - Create API token
  GET  /v1/auth/tokens         - List tokens
  POST /v1/auth/revoke         - Revoke token

  POST /v1/tools/read          - Read file
  POST /v1/tools/write         - Write file
  POST /v1/tools/edit          - Edit file
  POST /v1/tools/search        - Search code
  POST /v1/tools/run           - Run command
  GET  /v1/tools/git/status    - Git status

Usage:
    # With token
    curl -X POST https://api.dikaai.dev/v1/chat/completions \\
      -H "Authorization: Bearer dka_xxx" \\
      -H "Content-Type: application/json" \\
      -d '{"messages": [{"role": "user", "content": "hello"}]}'

    # Claude Code / Codex / Pi Agent compatible
    export DIKAAI_API_KEY=dka_xxx
    export DIKAAI_BASE_URL=https://api.dikaai.dev/v1
"""

import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dikaai.engine import Engine
from server.auth import AuthManager

# Global instances
engine = None
auth = AuthManager()


def get_engine():
    global engine
    if engine is None:
        engine = Engine(workspace=os.getcwd())
    return engine


class APIHandler(BaseHTTPRequestHandler):
    """DikaAI Public API Handler."""

    def log_message(self, format, *args):
        pass

    # ============================================================
    # Response helpers
    # ============================================================

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _error(self, message, code=400):
        self._json({'error': {'message': message, 'type': 'invalid_request_error', 'code': code}}, code)

    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length:
            try:
                return json.loads(self.rfile.read(length))
            except json.JSONDecodeError:
                return {}
        return {}

    def _get_token(self):
        """Extract Bearer token from Authorization header."""
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        # Also check X-API-Key header
        return self.headers.get('X-API-Key', '')

    def _check_auth(self, required_scope=None):
        """Validate token. Returns (valid, error_response)."""
        token = self._get_token()
        if not token:
            return False, {'error': 'Missing Authorization header. Use: Bearer dka_xxx'}

        result = auth.validate_token(token, required_scope)
        if not result['valid']:
            return False, {'error': result['error']}
        return True, None

    # ============================================================
    # CORS
    # ============================================================

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
        self.end_headers()

    # ============================================================
    # GET endpoints
    # ============================================================

    def do_GET(self):
        path = urlparse(self.path).path

        # Public endpoints (no auth)
        if path == '/v1/health':
            self._json({
                'status': 'ok',
                'version': '3.0.0',
                'timestamp': time.time(),
            })
            return

        if path == '/':
            self._json({
                'name': 'DikaAI API',
                'version': '3.0.0',
                'endpoints': {
                    'chat': 'POST /v1/chat/completions',
                    'completion': 'POST /v1/completions',
                    'agent': 'POST /v1/agent',
                    'tools': 'POST /v1/tools/{read,write,edit,search,run}',
                    'models': 'GET /v1/models',
                    'health': 'GET /v1/health',
                    'auth': 'POST /v1/auth/token',
                },
                'docs': 'https://github.com/dikaofc/dikaai#-api',
            })
            return

        # Auth endpoints
        if path == '/v1/auth/tokens':
            ok, err = self._check_auth('admin')
            if not ok:
                self._error(err['error'], 401)
                return
            self._json({'tokens': auth.list_tokens()})
            return

        # Authenticated endpoints
        if path == '/v1/models':
            ok, err = self._check_auth()
            if not ok:
                self._error(err['error'], 401)
                return
            self._json({
                'data': [
                    {
                        'id': 'dikaai-v3',
                        'object': 'model',
                        'created': 1700000000,
                        'owned_by': 'dikaai',
                        'capabilities': ['chat', 'code', 'agent', 'tools'],
                    }
                ]
            })
            return

        # Git status
        if path == '/v1/tools/git/status':
            ok, err = self._check_auth('tools')
            if not ok:
                self._error(err['error'], 401)
                return
            e = get_engine()
            result = e.git.status()
            self._json(result)
            return

        self._error('Not found', 404)

    # ============================================================
    # POST endpoints
    # ============================================================

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._body()

        # ========================================================
        # Auth endpoints
        # ========================================================

        if path == '/v1/auth/token':
            ok, err = self._check_auth('admin')
            if not ok:
                self._error(err['error'], 401)
                return
            name = body.get('name', 'api-key')
            scopes = body.get('scopes', ['chat', 'agent', 'tools'])
            rate_limit = body.get('rate_limit', 60)
            result = auth.create_token(name, scopes, rate_limit)
            self._json(result)
            return

        if path == '/v1/auth/revoke':
            ok, err = self._check_auth('admin')
            if not ok:
                self._error(err['error'], 401)
                return
            token = body.get('token', '')
            success = auth.revoke_token(token)
            self._json({'revoked': success})
            return

        # ========================================================
        # All other endpoints require auth
        # ========================================================

        ok, err = self._check_auth()
        if not ok:
            self._error(err['error'], 401)
            return

        e = get_engine()

        # ========================================================
        # OpenAI-compatible: Chat Completions
        # POST /v1/chat/completions
        # ========================================================

        if path == '/v1/chat/completions':
            messages = body.get('messages', [])
            if not messages:
                self._error('messages is required')
                return

            # Get last user message
            user_msg = ''
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_msg = msg.get('content', '')
                    break

            if not user_msg:
                self._error('No user message found')
                return

            # Process through DikaAI engine
            result = e.process(user_msg)

            # OpenAI-compatible response
            self._json({
                'id': f'chatcmpl-{int(time.time()*1000)}',
                'object': 'chat.completion',
                'created': int(time.time()),
                'model': 'dikaai-v3',
                'choices': [
                    {
                        'index': 0,
                        'message': {
                            'role': 'assistant',
                            'content': result.get('response', ''),
                        },
                        'finish_reason': 'stop',
                    }
                ],
                'usage': {
                    'prompt_tokens': len(user_msg.split()),
                    'completion_tokens': len(result.get('response', '').split()),
                    'total_tokens': len(user_msg.split()) + len(result.get('response', '').split()),
                },
                # DikaAI extensions
                'dikaai': {
                    'route': result.get('route', ''),
                    'topic': result.get('topic', ''),
                    'intent': result.get('intent', ''),
                    'time': result.get('time', ''),
                    'validation': result.get('validation', {}),
                },
            })
            return

        # ========================================================
        # OpenAI-compatible: Completions
        # POST /v1/completions
        # ========================================================

        if path == '/v1/completions':
            prompt = body.get('prompt', '')
            if not prompt:
                self._error('prompt is required')
                return

            result = e.process(prompt)

            self._json({
                'id': f'cmpl-{int(time.time()*1000)}',
                'object': 'text_completion',
                'created': int(time.time()),
                'model': 'dikaai-v3',
                'choices': [
                    {
                        'text': result.get('response', ''),
                        'index': 0,
                        'finish_reason': 'stop',
                    }
                ],
                'usage': {
                    'prompt_tokens': len(prompt.split()),
                    'completion_tokens': len(result.get('response', '').split()),
                    'total_tokens': len(prompt.split()) + len(result.get('response', '').split()),
                },
            })
            return

        # ========================================================
        # Agent endpoint
        # POST /v1/agent
        # ========================================================

        if path == '/v1/agent':
            task = body.get('task', '') or body.get('message', '')
            if not task:
                self._error('task or message is required')
                return

            max_retries = body.get('max_retries', 3)
            context = body.get('context', {})

            # Execute through agent
            result = e.executor.execute(task, context, max_retries=max_retries)

            self._json({
                'success': result.success,
                'output': result.output,
                'error': result.error,
                'steps': [str(s) for s in result.steps_executed],
                'retries': result.retries,
                'fixes': result.fixes_applied,
                'time': f'{result.total_time:.1f}s',
            })
            return

        # ========================================================
        # Tool endpoints
        # ========================================================

        if path == '/v1/tools/read':
            ok, err = self._check_auth('tools')
            if not ok:
                self._error(err['error'], 401)
                return
            file_path = body.get('path', '')
            if not file_path:
                self._error('path is required')
                return
            result = e.fs.read_file(file_path)
            self._json(result)
            return

        if path == '/v1/tools/write':
            ok, err = self._check_auth('tools')
            if not ok:
                self._error(err['error'], 401)
                return
            file_path = body.get('path', '')
            content = body.get('content', '')
            if not file_path or not content:
                self._error('path and content are required')
                return
            result = e.fs.write_file(file_path, content)
            self._json(result)
            return

        if path == '/v1/tools/edit':
            ok, err = self._check_auth('tools')
            if not ok:
                self._error(err['error'], 401)
                return
            file_path = body.get('path', '')
            old_text = body.get('old_text', '')
            new_text = body.get('new_text', '')
            if not file_path or not old_text:
                self._error('path and old_text are required')
                return
            result = e.fs.edit_file(file_path, old_text, new_text)
            self._json(result)
            return

        if path == '/v1/tools/search':
            ok, err = self._check_auth('tools')
            if not ok:
                self._error(err['error'], 401)
                return
            pattern = body.get('pattern', '')
            search_path = body.get('path', '.')
            if not pattern:
                self._error('pattern is required')
                return
            result = e.fs.search_code(pattern, search_path)
            self._json(result)
            return

        if path == '/v1/tools/run':
            ok, err = self._check_auth('tools')
            if not ok:
                self._error(err['error'], 401)
                return
            command = body.get('command', '')
            if not command:
                self._error('command is required')
                return
            result = e.terminal.run_command(command)
            self._json(result)
            return

        self._error('Not found', 404)


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


def start_server(port: int = 8080):
    """Start DikaAI API server."""
    server = ReusableHTTPServer(('0.0.0.0', port), APIHandler)
    print(f"""
╔═══════════════════════════════════════════════════╗
║         DikaAI Public API v3.0 🚀                ║
╠═══════════════════════════════════════════════════╣
║  http://localhost:{port}                          ║
║                                                   ║
║  Endpoints:                                       ║
║    POST /v1/chat/completions  (OpenAI-compatible) ║
║    POST /v1/completions       (OpenAI-compatible) ║
║    POST /v1/agent             (Coding agent)      ║
║    POST /v1/tools/{read,write,edit,search,run}    ║
║    GET  /v1/models                               ║
║    GET  /v1/health                               ║
║                                                   ║
║  Auth: Bearer token (dka_xxx)                     ║
║  Create token: POST /v1/auth/token                ║
╚═══════════════════════════════════════════════════╝
""")
    server.serve_forever()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    start_server(port)
