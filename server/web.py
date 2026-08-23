"""
DikaAI Web Server - Chat UI + API

Serves:
  /                    → Chat UI (HTML)
  /api/chat            → Chat endpoint (streaming)
  /api/history         → Chat history
  /api/stats           → Engine stats
  /api/memory          → Memory stats
  /v1/chat/completions → OpenAI-compatible API
  /v1/health           → Health check
"""

import json
import os
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dikaai.engine import Engine

# Global engine
engine = None
chat_history = []


def get_engine():
    global engine
    if engine is None:
        engine = Engine(workspace=os.getcwd())
    return engine


# ============================================================
# CHAT UI HTML
# ============================================================

CHAT_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DikaAI Chat</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --bg: #0a0a0f;
  --surface: #12121a;
  --surface2: #1a1a25;
  --border: #2a2a3a;
  --text: #e0e0e8;
  --text2: #888899;
  --primary: #6c5ce7;
  --primary2: #a29bfe;
  --green: #00b894;
  --red: #e17055;
  --yellow: #fdcb6e;
  --code-bg: #0d1117;
  --radius: 12px;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  height: 100vh;
  display: flex;
  flex-direction: column;
}
/* Header */
.header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.header .logo {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary), var(--primary2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.header .status {
  font-size: 12px;
  color: var(--green);
  display: flex;
  align-items: center;
  gap: 6px;
}
.header .status::before {
  content: '';
  width: 8px;
  height: 8px;
  background: var(--green);
  border-radius: 50%;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
.header .stats {
  margin-left: auto;
  font-size: 11px;
  color: var(--text2);
}
/* Sidebar */
.container {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.sidebar {
  width: 280px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar h3 {
  padding: 16px;
  font-size: 13px;
  color: var(--text2);
  text-transform: uppercase;
  letter-spacing: 1px;
  border-bottom: 1px solid var(--border);
}
.sidebar .memory-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.memory-item {
  padding: 10px 12px;
  border-radius: 8px;
  margin-bottom: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}
.memory-item:hover { background: var(--surface2); }
.memory-item .label {
  color: var(--primary2);
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  margin-bottom: 4px;
}
.memory-item .value {
  color: var(--text);
  line-height: 1.4;
}
.memory-item .meta {
  color: var(--text2);
  font-size: 11px;
  margin-top: 4px;
}
/* Chat area */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.message {
  max-width: 80%;
  animation: fadeIn 0.3s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.message.user {
  align-self: flex-end;
}
.message.assistant {
  align-self: flex-start;
}
.message .bubble {
  padding: 12px 16px;
  border-radius: var(--radius);
  line-height: 1.6;
  font-size: 14px;
  white-space: pre-wrap;
  word-wrap: break-word;
}
.message.user .bubble {
  background: var(--primary);
  color: white;
  border-bottom-right-radius: 4px;
}
.message.assistant .bubble {
  background: var(--surface2);
  color: var(--text);
  border-bottom-left-radius: 4px;
}
.message .meta {
  font-size: 11px;
  color: var(--text2);
  margin-top: 4px;
  padding: 0 4px;
  display: flex;
  gap: 12px;
}
.message.user .meta { text-align: right; justify-content: flex-end; }
.message .route-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
}
.route-tag.code { background: #6c5ce720; color: var(--primary2); }
.route-tag.tool { background: #00b89420; color: var(--green); }
.route-tag.reason { background: #e1705520; color: var(--red); }
.route-tag.search { background: #fdcb6e20; color: var(--yellow); }
.route-tag.chat { background: #88889920; color: var(--text2); }
/* Code blocks */
.bubble code {
  background: var(--code-bg);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 13px;
}
.bubble pre {
  background: var(--code-bg);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}
.bubble pre code {
  background: none;
  padding: 0;
}
/* Typing indicator */
.typing {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: var(--surface2);
  border-radius: var(--radius);
  border-bottom-left-radius: 4px;
  width: fit-content;
}
.typing span {
  width: 8px;
  height: 8px;
  background: var(--text2);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}
.typing span:nth-child(1) { animation-delay: 0s; }
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
/* Input area */
.input-area {
  padding: 16px 20px;
  background: var(--surface);
  border-top: 1px solid var(--border);
}
.input-wrapper {
  display: flex;
  gap: 8px;
  max-width: 900px;
  margin: 0 auto;
}
.input-wrapper textarea {
  flex: 1;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 16px;
  color: var(--text);
  font-size: 14px;
  font-family: inherit;
  resize: none;
  min-height: 44px;
  max-height: 200px;
  line-height: 1.5;
  transition: border-color 0.2s;
}
.input-wrapper textarea:focus {
  outline: none;
  border-color: var(--primary);
}
.input-wrapper textarea::placeholder {
  color: var(--text2);
}
.send-btn {
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius);
  padding: 0 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 60px;
}
.send-btn:hover { background: var(--primary2); }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
/* Welcome */
.welcome {
  text-align: center;
  padding: 60px 20px;
  color: var(--text2);
}
.welcome h2 {
  font-size: 28px;
  margin-bottom: 8px;
  background: linear-gradient(135deg, var(--primary), var(--primary2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.welcome p { font-size: 14px; max-width: 500px; margin: 0 auto; line-height: 1.6; }
.welcome .chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 24px;
}
.welcome .chip {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 8px 16px;
  font-size: 13px;
  color: var(--text);
  cursor: pointer;
  transition: all 0.2s;
}
.welcome .chip:hover {
  border-color: var(--primary);
  color: var(--primary2);
}
/* Mobile */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .message { max-width: 95%; }
}
</style>
</head>
<body>
<div class="header">
  <div class="logo">🧠 DikaAI</div>
  <div class="status">Online</div>
  <div class="stats" id="stats">Loading...</div>
</div>
<div class="container">
  <div class="sidebar">
    <h3>📊 Memory</h3>
    <div class="memory-list" id="memory">
      <div class="memory-item">
        <div class="label">Episodes</div>
        <div class="value" id="mem-episodes">-</div>
      </div>
      <div class="memory-item">
        <div class="label">Facts</div>
        <div class="value" id="mem-facts">-</div>
      </div>
      <div class="memory-item">
        <div class="label">Topics</div>
        <div class="value" id="mem-topics">-</div>
      </div>
      <div class="memory-item">
        <div class="label">Tokens Stored</div>
        <div class="value" id="mem-tokens">-</div>
      </div>
      <div class="memory-item">
        <div class="label">Tasks</div>
        <div class="value" id="mem-tasks">-</div>
      </div>
    </div>
  </div>
  <div class="chat-area">
    <div class="messages" id="messages">
      <div class="welcome">
        <h2>DikaAI v3</h2>
        <p>AI Coding Agent & Chat System with memory, context, and multi-language support.</p>
        <div class="chips">
          <div class="chip" onclick="send('Write a fibonacci function')">🔢 Fibonacci</div>
          <div class="chip" onclick="send('Write a binary search in Python')">🔍 Binary Search</div>
          <div class="chip" onclick="send('Fix this error: TypeError on line 5')">🐛 Fix Error</div>
          <div class="chip" onclick="send('git status')">📂 Git Status</div>
          <div class="chip" onclick="send('Explain quicksort algorithm')">🧠 Explain</div>
          <div class="chip" onclick="send('Write a Rust struct with methods')">🦀 Rust Struct</div>
          <div class="chip" onclick="send('Write a JavaScript debounce function')">⚡ Debounce</div>
        </div>
      </div>
    </div>
    <div class="input-area">
      <div class="input-wrapper">
        <textarea id="input" placeholder="Ask DikaAI anything... (Enter to send, Shift+Enter for new line)" rows="1" autofocus></textarea>
        <button class="send-btn" id="sendBtn" onclick="sendFromInput()">Send</button>
      </div>
    </div>
  </div>
</div>
<script>
const messages = document.getElementById('messages');
const input = document.getElementById('input');
const sendBtn = document.getElementById('sendBtn');
let isLoading = false;

// Auto-resize textarea
input.addEventListener('input', () => {
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 200) + 'px';
});

// Enter to send
input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendFromInput();
  }
});

function sendFromInput() {
  const text = input.value.trim();
  if (!text || isLoading) return;
  send(text);
  input.value = '';
  input.style.height = 'auto';
}

async function send(text) {
  if (isLoading) return;
  isLoading = true;
  sendBtn.disabled = true;

  // Remove welcome
  const welcome = messages.querySelector('.welcome');
  if (welcome) welcome.remove();

  // Add user message
  addMessage('user', text);

  // Add typing indicator
  const typing = document.createElement('div');
  typing.className = 'message assistant';
  typing.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
  messages.appendChild(typing);
  messages.scrollTop = messages.scrollHeight;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();

    // Remove typing
    typing.remove();

    // Add assistant message
    addMessage('assistant', data.response, {
      route: data.route,
      time: data.time,
      topic: data.topic,
    });

    // Update stats
    loadStats();
  } catch (err) {
    typing.remove();
    addMessage('assistant', '❌ Error: ' + err.message, { route: 'error' });
  }

  isLoading = false;
  sendBtn.disabled = false;
  input.focus();
}

function addMessage(role, content, meta = {}) {
  const div = document.createElement('div');
  div.className = 'message ' + role;

  let metaHtml = '';
  if (meta.route) {
    metaHtml += `<span class="route-tag ${meta.route}">${meta.route}</span>`;
  }
  if (meta.time) {
    metaHtml += `<span>⏱️ ${meta.time}</span>`;
  }
  if (meta.topic) {
    metaHtml += `<span>📁 ${meta.topic}</span>`;
  }

  // Format code blocks
  let formatted = escapeHtml(content);
  formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
  formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');

  div.innerHTML = `
    <div class="bubble">${formatted}</div>
    ${metaHtml ? '<div class="meta">' + metaHtml + '</div>' : ''}
  `;

  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();

    document.getElementById('stats').textContent =
      `${data.total || 0} tasks | ${data.rate || '0%'}`;

    if (data.episodic) {
      document.getElementById('mem-episodes').textContent =
        `${data.episodic.total_episodes || 0} (${data.episodic.success_rate || '0%'})`;
    }
    if (data.semantic) {
      document.getElementById('mem-facts').textContent = data.semantic.total_facts || 0;
    }
    if (data.long_context) {
      document.getElementById('mem-topics').textContent = data.long_context.topics || 0;
      document.getElementById('mem-tokens').textContent = (data.long_context.total_tokens_stored || 0).toLocaleString();
    }
    document.getElementById('mem-tasks').textContent = data.total || 0;
  } catch (e) {}
}

// Load stats on start
loadStats();
setInterval(loadStats, 30000);
</script>
</body>
</html>'''


# ============================================================
# HTTP HANDLER
# ============================================================

class WebHandler(BaseHTTPRequestHandler):
    """DikaAI Web Server Handler."""

    def log_message(self, format, *args):
        pass

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
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
            except json.JSONDecodeError:
                return {}
        return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == '/':
            self._html(CHAT_HTML)
            return

        if path == '/api/stats':
            e = get_engine()
            self._json(e.get_stats())
            return

        if path == '/api/history':
            self._json({'history': chat_history[-50:]})
            return

        if path == '/v1/health':
            self._json({'status': 'ok', 'version': '3.1.0'})
            return

        if path == '/':
            self._json({
                'name': 'DikaAI Web',
                'endpoints': {
                    '/': 'Chat UI',
                    '/api/chat': 'POST - Send message',
                    '/api/stats': 'GET - Engine stats',
                    '/api/history': 'GET - Chat history',
                },
            })
            return

        self._json({'error': 'Not found'}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._body()

        if path == '/api/chat':
            message = body.get('message', '')
            if not message:
                self._json({'error': 'message is required'}, 400)
                return

            e = get_engine()
            result = e.process(message)

            # Save to history
            chat_history.append({
                'user': message,
                'assistant': result.get('response', ''),
                'route': result.get('route', ''),
                'topic': result.get('topic', ''),
                'time': result.get('time', ''),
                'timestamp': time.time(),
            })

            self._json({
                'response': result.get('response', ''),
                'route': result.get('route', ''),
                'topic': result.get('topic', ''),
                'intent': result.get('intent', ''),
                'time': result.get('time', ''),
                'success': result.get('success', True),
                'validation': result.get('validation', {}),
            })
            return

        # OpenAI-compatible endpoint
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

            e = get_engine()
            result = e.process(user_msg)

            self._json({
                'id': f'chatcmpl-{int(time.time()*1000)}',
                'object': 'chat.completion',
                'created': int(time.time()),
                'model': 'dikaai-v3',
                'choices': [{
                    'index': 0,
                    'message': {'role': 'assistant', 'content': result.get('response', '')},
                    'finish_reason': 'stop',
                }],
                'usage': {
                    'prompt_tokens': len(user_msg.split()),
                    'completion_tokens': len(result.get('response', '').split()),
                    'total_tokens': len(user_msg.split()) + len(result.get('response', '').split()),
                },
            })
            return

        self._json({'error': 'Not found'}, 404)


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


def start_server(port: int = 8080):
    """Start DikaAI Web Server."""
    server = ReusableHTTPServer(('0.0.0.0', port), WebHandler)
    print(f"""
╔═══════════════════════════════════════════════════╗
║         DikaAI Web Chat v3.1 🌐                  ║
╠═══════════════════════════════════════════════════╣
║  Chat UI:   http://localhost:{port}                ║
║  API:       http://localhost:{port}/v1/chat       ║
║  Stats:     http://localhost:{port}/api/stats     ║
║  Health:    http://localhost:{port}/v1/health     ║
║                                                   ║
║  OpenAI-compatible:                               ║
║    POST /v1/chat/completions                      ║
║                                                   ║
║  Connect Claude Code / Codex:                     ║
║    export OPENAI_API_BASE=http://localhost:{port}/v1║
╚═══════════════════════════════════════════════════╝
""")
    server.serve_forever()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    start_server(port)
