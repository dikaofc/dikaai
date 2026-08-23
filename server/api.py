"""DikaAI REST API - HTTP interface for chat, code, status.

Endpoints:
  POST /chat      - Send message, get response
  POST /code      - Execute coding task
  GET  /status    - Get engine status
  GET  /health    - Health check
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dikaai.engine import Engine

# Global engine
engine = Engine(workspace=os.getcwd())


class DikaAIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length:
            return json.loads(self.rfile.read(length))
        return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/health':
            self._json({'ok': True, 'version': '2.0.0'})
        elif path == '/status':
            self._json(engine.get_stats())
        else:
            self._json({'error': 'Not found'}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._body()

        if path == '/chat':
            message = body.get('message', '').strip()
            if not message:
                self._json({'error': 'Empty message'}, 400)
                return
            result = engine.process(message)
            self._json(result)

        elif path == '/code':
            task = body.get('task', '').strip()
            if not task:
                self._json({'error': 'Empty task'}, 400)
                return
            result = engine.process(task)
            self._json(result)

        else:
            self._json({'error': 'Not found'}, 404)


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


def start_server(port: int = 8080):
    """Start DikaAI API server."""
    server = ReusableHTTPServer(('0.0.0.0', port), DikaAIHandler)
    print(f"  DikaAI API: http://localhost:{port}")
    print(f"  POST /chat - Send message")
    print(f"  POST /code - Execute task")
    print(f"  GET  /status - Engine status")
    print(f"  GET  /health - Health check")
    server.serve_forever()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    start_server(port)
