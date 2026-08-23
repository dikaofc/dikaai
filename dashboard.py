"""DikaAi Dashboard - Web UI with Chat + Controls

Zero dependencies - uses only Python built-in http.server
Features:
- Real-time stats monitoring
- Loss chart with Canvas
- Web chat with DikaAi
- Control panel (on/off auto-reply, training, scraping)
- CSV export
"""
import csv
import io
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

DASHBOARD_PORT = 8888
HISTORY_FILE = Path(__file__).parent / "training_history.csv"

# Global state
_state = {
    'model': None,
    'tokenizer': None,
    'trainer': None,
    'db': None,
    'bot': None,
    'start_time': time.time(),
    'loss_history': [],
    'status': 'idle',
    # Feature toggles
    'auto_reply': True,
    'training': True,
    'scraping': True,
    # Chat history
    'chat_history': [],
}


def set_state(model=None, tokenizer=None, trainer=None, db=None, bot=None, status=None):
    if model: _state['model'] = model
    if tokenizer: _state['tokenizer'] = tokenizer
    if trainer: _state['trainer'] = trainer
    if db: _state['db'] = db
    if bot: _state['bot'] = bot
    if status: _state['status'] = status


def _load_history():
    if not HISTORY_FILE.exists():
        return []
    history = []
    try:
        with open(HISTORY_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                history.append((
                    float(row['timestamp']),
                    float(row['loss']),
                    int(row['steps']),
                    int(row.get('total_steps', 0)),
                    float(row.get('avg_loss', 0)),
                    int(row.get('total_messages', 0)),
                ))
    except Exception:
        pass
    return history


def _save_history():
    try:
        with open(HISTORY_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'loss', 'steps', 'total_steps',
                'avg_loss', 'total_messages'
            ])
            for h in _state['loss_history']:
                writer.writerow([
                    f'{h[0]:.3f}', f'{h[1]:.6f}', h[2], h[3],
                    f'{h[4]:.6f}', h[5]
                ])
    except Exception:
        pass


def record_loss(loss, steps):
    total_steps = 0
    total_msgs = 0
    avg_loss = 0.0

    trainer = _state.get('trainer')
    if trainer:
        total_steps = trainer.model.step if hasattr(trainer, 'model') else 0
        total_loss = trainer.total_loss if hasattr(trainer, 'total_loss') else 0
        total_steps_count = trainer.total_steps if hasattr(trainer, 'total_steps') else 0
        avg_loss = total_loss / max(total_steps_count, 1)

    db = _state.get('db')
    if db:
        try:
            stats = db.get_stats()
            total_msgs = stats.get('total', 0)
        except Exception:
            pass

    _state['loss_history'].append((
        time.time(), loss, steps, total_steps, avg_loss, total_msgs
    ))

    if len(_state['loss_history']) > 500:
        _state['loss_history'] = _state['loss_history'][-500:]

    n = len(_state['loss_history'])
    if n % 10 == 0 or n == 1:
        _save_history()


def _get_stats():
    stats = {}
    db = _state.get('db')
    model = _state.get('model')
    tokenizer = _state.get('tokenizer')

    if db:
        try:
            stats['db'] = db.get_stats()
        except Exception:
            stats['db'] = {'total': 0, 'processed': 0, 'unprocessed': 0, 'unique_chats': 0}
    else:
        stats['db'] = {'total': 0, 'processed': 0, 'unprocessed': 0, 'unique_chats': 0}

    if model:
        try:
            stats['model'] = {
                'params': model.get_param_count(),
                'step': model.step,
                'vocab_size': getattr(model, 'vocab_size', 0),
                'embed_dim': getattr(model, 'embed_dim', 0),
                'hidden_dim': getattr(model, 'hidden_dim', 0),
            }
        except Exception:
            stats['model'] = {'params': 0, 'step': 0}
    else:
        stats['model'] = {'params': 0, 'step': 0}

    if tokenizer:
        stats['vocab_tokens'] = getattr(tokenizer, 'vocab_size', 0)
    else:
        stats['vocab_tokens'] = 0

    stats['status'] = _state['status']
    stats['uptime'] = int(time.time() - _state['start_time'])

    # Feature toggles
    stats['toggles'] = {
        'auto_reply': _state['auto_reply'],
        'training': _state['training'],
        'scraping': _state['scraping'],
    }

    # Loss chart
    hist = _state['loss_history']
    if hist:
        stats['loss_chart'] = {
            'timestamps': [h[0] for h in hist],
            'losses': [h[1] for h in hist],
            'steps': [h[2] for h in hist],
        }
    else:
        stats['loss_chart'] = {'timestamps': [], 'losses': [], 'steps': []}

    # Recent messages
    db_obj = _state.get('db')
    if db_obj:
        try:
            msgs = db_obj.get_all_messages(limit=15)
            stats['recent_messages'] = msgs[-15:] if msgs else []
        except Exception:
            stats['recent_messages'] = []
    else:
        stats['recent_messages'] = []

    return stats


def _generate_csv():
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'timestamp', 'datetime', 'loss', 'steps_per_epoch',
        'total_model_steps', 'avg_loss', 'total_messages',
        'total_processed', 'total_unprocessed', 'unique_chats'
    ])

    db = _state.get('db')
    db_stats = {'total': 0, 'processed': 0, 'unprocessed': 0, 'unique_chats': 0}
    if db:
        try:
            db_stats = db.get_stats()
        except Exception:
            pass

    for h in _state['loss_history']:
        ts, loss, steps, total_steps, avg_loss, total_msgs = h
        dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
        writer.writerow([
            f'{ts:.3f}', dt, f'{loss:.6f}', steps,
            total_steps, f'{avg_loss:.6f}', total_msgs,
            db_stats['processed'], db_stats['unprocessed'],
            db_stats['unique_chats']
        ])

    writer.writerow([])
    writer.writerow(['# Summary'])
    writer.writerow(['total_messages', db_stats['total']])
    writer.writerow(['processed', db_stats['processed']])
    writer.writerow(['unique_chats', db_stats['unique_chats']])

    model = _state.get('model')
    if model:
        writer.writerow(['model_params', model.get_param_count()])
        writer.writerow(['model_steps', model.step])

    return output.getvalue()


def _handle_chat(text):
    """Generate a smart reply - model + fallback system."""
    from smart_reply import get_smart_reply

    model_reply = None
    model = _state.get('model')
    tokenizer = _state.get('tokenizer')

    if model and tokenizer and tokenizer._loaded:
        try:
            from config import CONTEXT_LEN
            tokens = tokenizer.encode(text, max_length=CONTEXT_LEN)
            if len(tokens) >= 1:
                generated = model.generate(tokens, max_len=25, temperature=0.75)
                model_reply = tokenizer.decode(generated)
        except Exception:
            pass

    return get_smart_reply(text, model_reply)


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
.status-scraping { background: #0088ff22; color: #0088ff; border: 1px solid #0088ff; }
.status-ready { background: #aa88ff22; color: #aa88ff; border: 1px solid #aa88ff; }

.btn {
    background: #1a1a2e; color: #00ccff; border: 1px solid #00ccff44;
    padding: 6px 14px; border-radius: 6px; font-family: 'Courier New', monospace;
    font-size: 12px; cursor: pointer; transition: all 0.2s;
}
.btn:hover { background: #00ccff22; border-color: #00ccff; }
.btn-danger { color: #ff4444; border-color: #ff444444; }
.btn-danger:hover { background: #ff444422; border-color: #ff4444; }
.btn-success { color: #00ff88; border-color: #00ff8844; }
.btn-success:hover { background: #00ff8822; border-color: #00ff88; }

.container { max-width: 1200px; margin: 0 auto; padding: 16px; }
.row { display: grid; gap: 16px; margin-bottom: 16px; }
.row-2 { grid-template-columns: 1fr 1fr; }
.row-3 { grid-template-columns: 1fr 1fr 1fr; }
@media (max-width: 768px) { .row-2, .row-3 { grid-template-columns: 1fr; } }

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
.msg .text { color: #ddd; }

.progress-bar { width: 100%; height: 6px; background: #222; border-radius: 3px; overflow: hidden; margin-top: 8px; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #00ff88, #00cc6a); transition: width 0.5s; border-radius: 3px; }

/* Toggle switches */
.toggle-group { display: flex; flex-direction: column; gap: 12px; }
.toggle-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: #0d0d0d; border-radius: 6px; border: 1px solid #222; }
.toggle-label { font-size: 13px; color: #ccc; }
.toggle-desc { font-size: 10px; color: #555; margin-top: 2px; }
.switch { position: relative; width: 44px; height: 24px; cursor: pointer; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: #333; border-radius: 24px; transition: 0.3s; }
.slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background: #666; border-radius: 50%; transition: 0.3s; }
.switch input:checked + .slider { background: #00ff8844; }
.switch input:checked + .slider:before { transform: translateX(20px); background: #00ff88; }

/* Chat */
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
.typing { color: #555; font-style: italic; padding: 8px 12px; }
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
    <!-- Stats Cards -->
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

    <!-- Main layout: Controls + Chat -->
    <div class="row row-2">
        <!-- Controls Panel -->
        <div class="panel">
            <div class="panel-header"><span>🎛️ Controls</span></div>
            <div class="panel-body">
                <div class="toggle-group">
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">🤖 Auto-Reply</div>
                            <div class="toggle-desc">Balas otomatis di chat Telegram</div>
                        </div>
                        <label class="switch">
                            <input type="checkbox" id="toggle-reply" checked onchange="toggleFeature('auto_reply', this.checked)">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">🧠 Training</div>
                            <div class="toggle-desc">Model belajar dari data</div>
                        </div>
                        <label class="switch">
                            <input type="checkbox" id="toggle-training" checked onchange="toggleFeature('training', this.checked)">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">📱 Scraping</div>
                            <div class="toggle-desc">Ambil chat dari Telegram</div>
                        </div>
                        <label class="switch">
                            <input type="checkbox" id="toggle-scraping" checked onchange="toggleFeature('scraping', this.checked)">
                            <span class="slider"></span>
                        </label>
                    </div>
                </div>
            </div>
        </div>

        <!-- Chat Panel -->
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
    </div>

    <!-- Loss Chart -->
    <div class="panel">
        <div class="panel-header"><span>📈 Training Loss</span><span id="chart-info">0 points</span></div>
        <div class="panel-body"><canvas id="lossChart"></canvas></div>
    </div>

    <!-- Recent Messages -->
    <div class="panel">
        <div class="panel-header"><span>💬 Recent Telegram Messages</span><span id="msg-count">0</span></div>
        <div class="panel-body">
            <div class="messages" id="msg-list"></div>
        </div>
    </div>
</div>

<div class="footer">DikaAi v1.2 - Paling Ringan Sedunia 🚀 | Auto-refresh: 5s</div>
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

// Toggle feature
async function toggleFeature(feature, enabled) {
    try {
        const res = await fetch('/api/toggle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({feature, enabled})
        });
        const data = await res.json();
        toast(data.ok ? '✅ ' + feature + (enabled ? ' ON' : ' OFF') : '❌ Error');
    } catch(e) { toast('❌ Connection error'); }
}

// Chat
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

// Export CSV
function exportCSV() {
    fetch('/api/export').then(r => r.blob()).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url;
        a.download = 'dikaai_' + new Date().toISOString().slice(0,10) + '.csv';
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        URL.revokeObjectURL(url); toast('✅ CSV exported!');
    }).catch(() => toast('❌ Export failed'));
}

// Chart
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

// Fetch stats
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

    // Sync toggle states
    const t = d.toggles || {};
    $('toggle-reply').checked = t.auto_reply !== false;
    $('toggle-training').checked = t.training !== false;
    $('toggle-scraping').checked = t.scraping !== false;
}

setInterval(fetchStats, 5000);
fetchStats();
</script>
</body>
</html>"""


class DashboardHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

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

        if parsed.path == '/' or parsed.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())

        elif parsed.path == '/api/stats':
            stats = _get_stats()
            stats['total_loss'] = getattr(_state.get('trainer'), 'total_loss', 0)
            stats['total_steps'] = getattr(_state.get('trainer'), 'total_steps', 0)
            self._send_json(stats)

        elif parsed.path == '/api/export':
            csv_data = _generate_csv()
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="dikaai_training.csv"')
            self.end_headers()
            self.wfile.write(csv_data.encode())

        elif parsed.path == '/api/health':
            self._send_json({'ok': True})

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == '/api/chat':
            body = self._read_body()
            text = body.get('message', '').strip()
            if not text:
                self._send_json({'error': 'empty message'}, 400)
                return

            reply = _handle_chat(text)

            # Store in chat history
            _state['chat_history'].append({
                'user': text,
                'ai': reply,
                'time': time.time()
            })
            if len(_state['chat_history']) > 100:
                _state['chat_history'] = _state['chat_history'][-100:]

            self._send_json({'reply': reply})

        elif parsed.path == '/api/toggle':
            body = self._read_body()
            feature = body.get('feature', '')
            enabled = body.get('enabled', True)

            if feature in ('auto_reply', 'training', 'scraping'):
                _state[feature] = enabled

                # Apply toggle to bot if available
                bot = _state.get('bot')
                if bot and feature == 'auto_reply':
                    # Toggle will be checked in bot's handler
                    pass

                # Apply toggle to trainer
                trainer = _state.get('trainer')
                if trainer and feature == 'training':
                    if enabled:
                        trainer.training = True
                    else:
                        trainer.training = False

                self._send_json({'ok': True, 'feature': feature, 'enabled': enabled})
            else:
                self._send_json({'error': 'unknown feature'}, 400)

        else:
            self.send_response(404)
            self.end_headers()


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


def start_dashboard(port=DASHBOARD_PORT, daemon=True):
    """Start dashboard server in background thread."""
    _state['loss_history'] = _load_history()
    if _state['loss_history']:
        print(f"  [DASH] Loaded {len(_state['loss_history'])} history points")

    server = ReusableHTTPServer(('0.0.0.0', port), DashboardHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=daemon)
    thread.start()

    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = 'localhost'

    print(f"\n  🌐 Dashboard: http://{local_ip}:{port}")
    print(f"  💬 Web Chat + Controls available")
    print(f"  📥 Export CSV: http://{local_ip}:{port}/api/export\n")

    return server
