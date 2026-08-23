"""DikaAi Vercel Dashboard - Serverless Version

Serves the dashboard UI and API endpoints on Vercel.
Reads data from: Upstash Redis (primary) or local files (fallback).
"""
import csv
import json
import io
import os
import sqlite3
import time
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

# Import config (loads .env.local too)
from config import (
    UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN, USE_REDIS,
    DB_PATH, MODEL_DIR, VOCAB_FILE
)

# Try to import RedisDB
try:
    from database import RedisDB, UpstashRedis
except ImportError:
    RedisDB = None
    UpstashRedis = None

HISTORY_FILE = BASE_DIR / "training_history.csv"


# ============================================================
# Redis Data Fetching (for Vercel)
# ============================================================

_redis_client = None

def _get_redis():
    """Get Redis client (lazy init)."""
    global _redis_client
    if _redis_client is None and USE_REDIS and UpstashRedis:
        try:
            _redis_client = UpstashRedis(UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN)
        except Exception as e:
            print(f"  [REDIS] Init error: {e}")
    return _redis_client


def _redis_get_stats():
    """Get stats from Redis."""
    r = _get_redis()
    if not r:
        return None
    try:
        total = int(r.get('dikaai:total') or 0)
        processed = int(r.get('dikaai:processed') or 0)
        unique_chats = int(r.get('dikaai:unique_chats') or 0)
        return {
            'total': total,
            'processed': processed,
            'unprocessed': total - processed,
            'unique_chats': unique_chats
        }
    except Exception as e:
        print(f"  [REDIS] Stats error: {e}")
        return None


def _redis_get_recent(limit=15):
    """Get recent messages from Redis."""
    r = _get_redis()
    if not r:
        return []
    try:
        msgs = r.lrange('dikaai:recent', 0, limit - 1)
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
    except Exception:
        return []


def _redis_get_model_info():
    """Get model info from Redis."""
    r = _get_redis()
    if not r:
        return None
    try:
        info = r.hgetall('dikaai:model')
        if info:
            return {
                'params': int(info.get('params', 0)),
                'step': int(info.get('step', 0)),
                'vocab_size': int(info.get('vocab_size', 0))
            }
    except Exception:
        pass
    return None


def _read_history():
    """Read training history from CSV."""
    if not HISTORY_FILE.exists():
        return []
    history = []
    try:
        with open(HISTORY_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
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
    """Get stats from SQLite database."""
    stats = {'total': 0, 'processed': 0, 'unprocessed': 0, 'unique_chats': 0}
    if not DB_PATH.exists():
        return stats
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.execute("SELECT COUNT(*) FROM messages")
        stats['total'] = cur.fetchone()[0]
        cur = conn.execute("SELECT COUNT(*) FROM messages WHERE processed = 1")
        stats['processed'] = cur.fetchone()[0]
        stats['unprocessed'] = stats['total'] - stats['processed']
        cur = conn.execute("SELECT COUNT(DISTINCT chat_id) FROM messages")
        stats['unique_chats'] = cur.fetchone()[0]
        conn.close()
    except Exception:
        pass
    return stats


def _get_model_info():
    """Get model info from JSON checkpoint."""
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


def _get_vocab_size():
    """Get vocab size from vocab.json."""
    if not VOCAB_FILE.exists():
        return 0
    try:
        with open(VOCAB_FILE, 'r') as f:
            data = json.load(f)
        return data.get('vocab_size', 0)
    except Exception:
        return 0


def _get_recent_messages(limit=15):
    """Get recent messages from DB."""
    if not DB_PATH.exists():
        return []
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.execute(
            "SELECT message FROM messages ORDER BY id DESC LIMIT ?", (limit,)
        )
        msgs = [row[0] for row in cur.fetchall()]
        conn.close()
        return msgs
    except Exception:
        return []


def _generate_reply(text):
    """Generate a reply using the model."""
    try:
        model_file = MODEL_DIR / "dikaai_latest.json"
        if not model_file.exists():
            return "Model belum trained. Jalankan training dulu di server."

        sys.path.insert(0, str(BASE_DIR))
        from model import DikaModel
        from tokenizer import DikaTokenizer
        from config import CONTEXT_LEN

        model = DikaModel()
        if not model.load(model_file):
            return "Gagal load model."

        tokenizer = DikaTokenizer()
        if not tokenizer.load():
            return "Tokenizer belum ready."

        tokens = tokenizer.encode(text, max_length=CONTEXT_LEN)
        if len(tokens) < 1:
            return "Input terlalu pendek."

        generated = model.generate(tokens, max_len=25, temperature=0.75)
        response = tokenizer.decode(generated)

        if not response or len(response.strip()) < 2:
            return "(model masih belajar...)"

        return response.strip()

    except Exception as e:
        return f"Error: {str(e)[:50]}"


# ============================================================
# HTML Frontend
# ============================================================

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DikaAi Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Courier New', monospace;
    background: #0a0a0a;
    color: #00ff88;
    min-height: 100vh;
}
.header {
    background: linear-gradient(135deg, #0d1117, #161b22);
    border-bottom: 2px solid #00ff88;
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
}
.header h1 { font-size: 20px; color: #00ff88; text-shadow: 0 0 10px #00ff8866; }
.header-right { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.status {
    padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;
}
.status-training { background: #00ff8822; color: #00ff88; border: 1px solid #00ff88; }
.status-idle { background: #ff880022; color: #ff8800; border: 1px solid #ff8800; }
.status-ready { background: #aa88ff22; color: #aa88ff; border: 1px solid #aa88ff; }

.btn {
    background: #1a1a2e; color: #00ccff; border: 1px solid #00ccff44;
    padding: 6px 14px; border-radius: 6px; font-family: 'Courier New', monospace;
    font-size: 12px; cursor: pointer; transition: all 0.2s;
}
.btn:hover { background: #00ccff22; border-color: #00ccff; }

.container { max-width: 1200px; margin: 0 auto; padding: 16px; }
.row { display: grid; gap: 16px; margin-bottom: 16px; }
.row-2 { grid-template-columns: 1fr 1fr; }
@media (max-width: 768px) { .row-2 { grid-template-columns: 1fr; } }

.stats-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px; margin-bottom: 16px;
}
.stat-card {
    background: #111; border: 1px solid #222; border-radius: 8px;
    padding: 14px; text-align: center;
}
.stat-card .label { color: #666; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; }
.stat-card .value { color: #00ff88; font-size: 24px; font-weight: bold; margin-top: 4px; }
.stat-card .sub { color: #555; font-size: 11px; margin-top: 2px; }

.panel {
    background: #111; border: 1px solid #222; border-radius: 8px;
    overflow: hidden; display: flex; flex-direction: column;
}
.panel-header {
    background: #1a1a1a; padding: 12px 16px; border-bottom: 1px solid #222;
    font-size: 13px; color: #888; display: flex; justify-content: space-between; align-items: center;
}
.panel-body { padding: 16px; flex: 1; overflow: auto; }
.panel-body.np { padding: 0; }

canvas { width: 100%; height: 200px; }

.messages { max-height: 250px; overflow-y: auto; font-size: 12px; }
.msg { padding: 5px 0; border-bottom: 1px solid #1a1a1a; color: #aaa; word-break: break-all; }
.msg:last-child { border-bottom: none; }

.progress-bar { width: 100%; height: 6px; background: #222; border-radius: 3px; overflow: hidden; margin-top: 8px; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #00ff88, #00cc6a); transition: width 0.5s; border-radius: 3px; }

.chat-container { display: flex; flex-direction: column; height: 350px; }
.chat-messages { flex: 1; overflow-y: auto; padding: 12px; font-size: 13px; }
.chat-msg { margin-bottom: 10px; padding: 8px 12px; border-radius: 8px; max-width: 85%; word-break: break-word; }
.chat-msg.user { background: #00ff8822; border: 1px solid #00ff8844; margin-left: auto; color: #00ff88; text-align: right; }
.chat-msg.ai { background: #1a1a2e; border: 1px solid #0088ff44; color: #00ccff; }
.chat-msg .sender { font-size: 10px; color: #555; margin-bottom: 2px; }
.chat-input { display: flex; gap: 8px; padding: 12px; border-top: 1px solid #222; }
.chat-input input {
    flex: 1; background: #0a0a0a; border: 1px solid #333; color: #00ff88;
    padding: 10px 14px; border-radius: 6px; font-family: 'Courier New', monospace; font-size: 13px; outline: none;
}
.chat-input input:focus { border-color: #00ff88; }
.chat-input button {
    background: #00ff8822; color: #00ff88; border: 1px solid #00ff88;
    padding: 10px 18px; border-radius: 6px; cursor: pointer; font-family: 'Courier New', monospace; font-weight: bold;
}
.chat-input button:hover { background: #00ff8844; }

.footer { text-align: center; padding: 16px; color: #333; font-size: 11px; }
.toast { position: fixed; bottom: 20px; right: 20px; background: #00ff8822; border: 1px solid #00ff88; color: #00ff88; padding: 12px 20px; border-radius: 8px; font-size: 13px; opacity: 0; transition: opacity 0.3s; pointer-events: none; z-index: 100; }
.toast.show { opacity: 1; }
</style>
</head>
<body>
<div class="header">
    <h1>🧠 DikaAi Dashboard</h1>
    <div class="header-right">
        <span id="status-badge" class="status status-idle">IDLE</span>
        <button class="btn" onclick="exportCSV()">📥 Export</button>
    </div>
</div>

<div class="container">
    <div class="stats-grid">
        <div class="stat-card">
            <div class="label">Messages</div>
            <div class="value" id="total-msgs">0</div>
            <div class="sub" id="unique-chats">0 chats</div>
        </div>
        <div class="stat-card">
            <div class="label">Processed</div>
            <div class="value" id="processed">0</div>
            <div class="progress-bar"><div class="progress-fill" id="process-bar" style="width:0%"></div></div>
        </div>
        <div class="stat-card">
            <div class="label">Steps</div>
            <div class="value" id="train-steps">0</div>
            <div class="sub" id="model-params">0 params</div>
        </div>
        <div class="stat-card">
            <div class="label">Loss</div>
            <div class="value" id="current-loss">-</div>
            <div class="sub" id="avg-loss">avg: -</div>
        </div>
        <div class="stat-card">
            <div class="label">Vocab</div>
            <div class="value" id="vocab-size">0</div>
        </div>
        <div class="stat-card">
            <div class="label">Uptime</div>
            <div class="value" id="uptime">0m</div>
        </div>
    </div>

    <div class="row row-2">
        <div class="panel">
            <div class="panel-header"><span>💬 Chat with DikaAi</span><span id="chat-status" style="color:#555;font-size:11px">ready</span></div>
            <div class="panel-body np">
                <div class="chat-container">
                    <div class="chat-messages" id="chat-box">
                        <div class="chat-msg ai"><div class="sender">DikaAi</div>Halo! Aku DikaAi. Chat sama aku! 🚀</div>
                    </div>
                    <div class="chat-input">
                        <input type="text" id="chat-input" placeholder="Ketik pesan..." onkeydown="if(event.key==='Enter')sendChat()">
                        <button onclick="sendChat()">Kirim</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="panel">
            <div class="panel-header"><span>💬 Recent Messages</span><span id="msg-count">0</span></div>
            <div class="panel-body">
                <div class="messages" id="msg-list"></div>
            </div>
        </div>
    </div>

    <div class="panel">
        <div class="panel-header"><span>📈 Training Loss</span><span id="chart-info">0 points</span></div>
        <div class="panel-body"><canvas id="lossChart"></canvas></div>
    </div>
</div>

<div class="footer">DikaAi v1.2 - Paling Ringan Sedunia 🚀 | Auto-refresh: 10s | Powered by Vercel</div>
<div class="toast" id="toast"></div>

<script>
const $ = id => document.getElementById(id);
function formatNum(n) {
    if (n >= 1000000) return (n/1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n/1000).toFixed(1) + 'K';
    return n.toString();
}
function formatTime(s) {
    if (s >= 3600) return Math.floor(s/3600) + 'h ' + Math.floor((s%3600)/60) + 'm';
    return Math.floor(s/60) + 'm';
}
function toast(msg) {
    const t = $('toast'); t.textContent = msg; t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2000);
}
function escapeHtml(t) {
    return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
async function sendChat() {
    const input = $('chat-input');
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    addChatMsg('user', 'Kamu', text);
    $('chat-status').textContent = 'thinking...';
    $('chat-status').style.color = '#ff8800';
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: text})
        });
        const data = await res.json();
        addChatMsg('ai', 'DikaAi', data.reply || '(no reply)');
    } catch(e) {
        addChatMsg('ai', 'DikaAi', '⚠️ Error connecting');
    }
    $('chat-status').textContent = 'ready';
    $('chat-status').style.color = '#555';
}
function addChatMsg(type, sender, text) {
    const box = $('chat-box');
    const div = document.createElement('div');
    div.className = 'chat-msg ' + type;
    div.innerHTML = '<div class="sender">' + escapeHtml(sender) + '</div>' + escapeHtml(text);
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}
function exportCSV() {
    fetch('/api/export').then(r => r.blob()).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url;
        a.download = 'dikaai_' + new Date().toISOString().slice(0,10) + '.csv';
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        URL.revokeObjectURL(url); toast('✅ CSV exported!');
    }).catch(() => toast('❌ Export failed'));
}
function drawChart(losses) {
    const canvas = $('lossChart');
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.offsetWidth * dpr;
    canvas.height = 200 * dpr;
    ctx.scale(dpr, dpr);
    const w = canvas.offsetWidth, h = 200;
    ctx.clearRect(0, 0, w, h);
    if (!losses || losses.length < 2) {
        ctx.fillStyle = '#333'; ctx.font = '14px Courier New'; ctx.textAlign = 'center';
        ctx.fillText('Waiting for training data...', w/2, h/2); return;
    }
    const maxL = Math.max(...losses) * 1.1 || 1;
    ctx.strokeStyle = '#1a1a1a'; ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = (i / 4) * h;
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
        ctx.fillStyle = '#333'; ctx.font = '10px Courier New'; ctx.textAlign = 'left';
        ctx.fillText((maxL - (i/4)*maxL).toFixed(2), 4, y + 12);
    }
    ctx.strokeStyle = '#00ff88'; ctx.lineWidth = 2; ctx.shadowColor = '#00ff88'; ctx.shadowBlur = 4;
    ctx.beginPath();
    for (let i = 0; i < losses.length; i++) {
        const x = (i / (losses.length - 1)) * w;
        const y = h - (losses[i] / maxL) * h;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke(); ctx.shadowBlur = 0;
    ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.closePath();
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, '#00ff8822'); grad.addColorStop(1, '#00ff8800');
    ctx.fillStyle = grad; ctx.fill();
}
async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const d = await res.json();
        updateUI(d);
    } catch(e) {}
}
function updateUI(d) {
    const db = d.db || {}, m = d.model || {};
    $('status-badge').textContent = (d.status || 'idle').toUpperCase();
    $('status-badge').className = 'status status-' + (d.status || 'idle');
    $('total-msgs').textContent = formatNum(db.total || 0);
    $('unique-chats').textContent = (db.unique_chats || 0) + ' chats';
    $('processed').textContent = formatNum(db.processed || 0);
    $('process-bar').style.width = (db.total ? Math.round(db.processed/db.total*100) : 0) + '%';
    $('train-steps').textContent = formatNum(m.step || 0);
    $('model-params').textContent = formatNum(m.params || 0) + ' params';
    const chart = d.loss_chart || {}, losses = chart.losses || [];
    if (losses.length > 0) $('current-loss').textContent = losses[losses.length-1].toFixed(4);
    if (d.total_loss !== undefined && d.total_steps > 0) $('avg-loss').textContent = 'avg: ' + (d.total_loss/d.total_steps).toFixed(4);
    $('vocab-size').textContent = d.vocab_tokens || m.vocab_size || 0;
    $('uptime').textContent = formatTime(d.uptime || 0);
    drawChart(losses);
    $('chart-info').textContent = losses.length + ' points';
    const msgs = d.recent_messages || [];
    $('msg-count').textContent = msgs.length + ' recent';
    $('msg-list').innerHTML = msgs.slice().reverse().map(m =>
        '<div class="msg"><span class="text">' + escapeHtml(m) + '</span></div>'
    ).join('');
}
setInterval(fetchStats, 10000);
fetchStats();
</script>
</body>
</html>"""


class handler(BaseHTTPRequestHandler):
    """Vercel Python serverless function handler."""

    def log_message(self, format, *args):
        pass

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _send_html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())

    def _read_body(self):
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
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/' or path == '/index.html':
            self._send_html(HTML_PAGE)

        elif path == '/api/stats':
            # Try Redis first (Vercel), then local files
            redis_stats = _redis_get_stats()
            redis_model = _redis_get_model_info()
            redis_recent = _redis_get_recent(15)

            if redis_stats:
                # Redis mode (Vercel)
                history = _read_history()
                losses = [h['loss'] for h in history]
                timestamps = [h['timestamp'] for h in history]

                stats = {
                    'db': redis_stats,
                    'model': redis_model or {'params': 0, 'step': 0, 'vocab_size': 0},
                    'vocab_tokens': (redis_model or {}).get('vocab_size', 0),
                    'status': 'ready' if (redis_model or {}).get('step', 0) > 0 else 'idle',
                    'uptime': 0,
                    'toggles': {'auto_reply': True, 'training': True, 'scraping': True},
                    'loss_chart': {
                        'timestamps': timestamps,
                        'losses': losses,
                        'steps': [h['steps'] for h in history],
                    },
                    'recent_messages': redis_recent,
                    'total_loss': sum(h.get('avg_loss', 0) * h.get('steps', 0) for h in history),
                    'total_steps': sum(h.get('steps', 0) for h in history),
                    'source': 'redis'
                }
            else:
                # Local mode (fallback)
                history = _read_history()
                db_stats = _get_db_stats()
                model_info = _get_model_info()
                vocab_size = _get_vocab_size()

                losses = [h['loss'] for h in history]
                timestamps = [h['timestamp'] for h in history]

                stats = {
                    'db': db_stats,
                    'model': {
                        'params': model_info['params'],
                        'step': model_info['step'],
                        'vocab_size': model_info['vocab_size'],
                    },
                    'vocab_tokens': vocab_size,
                    'status': 'ready' if model_info['step'] > 0 else 'idle',
                    'uptime': 0,
                    'toggles': {'auto_reply': True, 'training': True, 'scraping': True},
                    'loss_chart': {
                        'timestamps': timestamps,
                        'losses': losses,
                        'steps': [h['steps'] for h in history],
                    },
                    'recent_messages': _get_recent_messages(15),
                    'total_loss': sum(h.get('avg_loss', 0) * h.get('steps', 0) for h in history),
                    'total_steps': sum(h.get('steps', 0) for h in history),
                    'source': 'local'
                }
            self._send_json(stats)

        elif path == '/api/export':
            history = _read_history()
            db_stats = _get_db_stats()

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                'timestamp', 'datetime', 'loss', 'steps_per_epoch',
                'total_model_steps', 'avg_loss', 'total_messages',
                'total_processed', 'total_unprocessed', 'unique_chats'
            ])
            for h in history:
                dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(h['timestamp']))
                writer.writerow([
                    f"{h['timestamp']:.3f}", dt, f"{h['loss']:.6f}", h['steps'],
                    h['total_steps'], f"{h['avg_loss']:.6f}", h['total_messages'],
                    db_stats['processed'], db_stats['unprocessed'], db_stats['unique_chats']
                ])

            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="dikaai_training.csv"')
            self.end_headers()
            self.wfile.write(output.getvalue().encode())

        elif path == '/api/health':
            self._send_json({'ok': True})

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/api/toggle':
            body = self._read_body()
            self._send_json({'ok': True, 'feature': body.get('feature', ''), 'enabled': body.get('enabled', True)})

        elif path == '/api/chat':
            body = self._read_body()
            text = body.get('message', '').strip()
            if not text:
                self._send_json({'error': 'empty message'}, 400)
                return
            reply = _generate_reply(text)
            self._send_json({'reply': reply})

        else:
            self.send_response(404)
            self.end_headers()
