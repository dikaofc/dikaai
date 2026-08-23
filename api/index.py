"""DikaAI Vercel Deployment - Dashboard + Full API + Chat UI

All DikaAI functions live on Vercel:
  /                         → Dashboard (training stats + controls)
  /chat                     → Full Chat UI (Engine-powered)
  /api/stats                → Training stats (Redis/local)
  /api/chat                 → Chat endpoint
  /api/export               → CSV export
  /v1/health                → Health check
  /v1/models                → List models
  /v1/chat/completions      → OpenAI-compatible chat
  /v1/completions           → OpenAI-compatible completion
  /v1/agent                 → Coding agent
  /v1/tools/read            → Read file
  /v1/tools/write           → Write file
  /v1/tools/search          → Search code
  /v1/tools/run             → Run command
  /v1/auth/token            → Create API token
  /v1/auth/tokens           → List tokens
  /v1/auth/revoke           → Revoke token

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
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

# Import config (safe for Vercel read-only filesystem)
from dikaai.config import (
    UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN, USE_REDIS,
    DB_PATH, MODEL_DIR, VOCAB_FILE
)

# Lazy-import Engine (heavy, only load when needed)
_engine = None

def _get_engine():
    """Lazy-load Engine for chat/API endpoints."""
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
                def get(self, key): return self._api('get', key)
                def set(self, key, value, ex=None):
                    if ex: return self._api('set', key, value, 'EX', ex)
                    return self._api('set', key, value)
                def hgetall(self, key):
                    result = self._api('hgetall', key)
                    if isinstance(result, list):
                        d = {}
                        for i in range(0, len(result), 2):
                            d[result[i]] = result[i+1]
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
    """API token management via Redis."""
    
    def __init__(self):
        self.r = _get_redis()
    
    def validate(self, token, scope=None):
        """Validate API token. Returns (valid, info)."""
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
        """Create new API token."""
        if not self.r:
            return None
        token = f"dka_{hashlib.md5(f'{name}{time.time()}'.encode()).hexdigest()[:24]}"
        self.r.hset(f"dikaai:token:{token}",
            'name', name,
            'scopes', scopes,
            'created', str(time.time()),
            'revoked', '0',
        )
        self.r.sadd('dikaai:tokens', token)
        return token
    
    def list_tokens(self):
        """List all tokens."""
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
        """Revoke a token."""
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
    """Unified stats from Redis or local."""
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
    # Local fallback
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
    """Parse recent message from Redis JSON."""
    try:
        d = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(d, dict):
            return d.get('m', d.get('message', ''))
    except Exception:
        pass
    return str(raw) if raw else ''

def _generate_reply(text):
    """Generate reply using templates + Engine (NO raw model output on Vercel)."""
    # 1. Try code templates first (instant, correct, no model needed)
    try:
        from dikaai.coding.code_templates import match_template
        tmpl = match_template(text)
        if tmpl['matched']:
            return f"```python\n{tmpl['code']}\n```\n\n✅ {tmpl['template_name']} template"
    except Exception:
        pass

    # 2. Try Engine (uses templates + smart_reply, NO model)
    engine = _get_engine()
    if engine:
        try:
            result = engine.process(text)
            response = result.get('response', '')
            # Safety: if response looks like model garbage, use smart_reply
            if _looks_like_garbage(response):
                from dikaai.coding.smart_reply import get_smart_reply
                return get_smart_reply(text)
            return response
        except Exception as e:
            print(f"[ENGINE] Error: {e}")

    # 3. Fallback: smart_reply (pattern matching, no model)
    try:
        from dikaai.coding.smart_reply import get_smart_reply
        return get_smart_reply(text)
    except Exception:
        return "DikaAI is processing. Please try again."


def _looks_like_garbage(text):
    """Extra garbage detection for model output that passes basic checks."""
    if not text or len(text) < 5:
        return True
    text = text.strip()
    # Check for common model garbage patterns
    garbage_patterns = [
        r'^[a-z_]+ [a-z_]+ [a-z_]+',  # random words separated by spaces
        r'\b(func|def|class|import|return|print)\b.*\b(func|def|class|import|return|print)\b',
        r'_\s*$',  # ends with underscore
        r'\b(test|error|none|null|undefined|false|true)\b.*\b(test|error|none|null|undefined|false|true)\b',
    ]
    for pat in garbage_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True
    # If response has no proper sentences (no capital letters, no punctuation)
    sentences = [s.strip() for s in re.split(r'[.!?\n]', text) if s.strip()]
    if sentences:
        has_proper = any(s[0].isupper() or s.startswith('```') for s in sentences if len(s) > 3)
        if not has_proper and not text.startswith('```'):
            return True
    return False


# ============================================================
# HTML - Dashboard
# ============================================================

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DikaAI Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Courier New',monospace;background:#0a0a0a;color:#00ff88;min-height:100vh}
.header{background:linear-gradient(135deg,#0d1117,#161b22);border-bottom:2px solid #00ff88;padding:16px 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.header h1{font-size:20px;color:#00ff88;text-shadow:0 0 10px #00ff8866}
.header-right{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.nav{display:flex;gap:4px}
.nav a{background:#1a1a2e;color:#00ccff;border:1px solid #00ccff44;padding:6px 14px;border-radius:6px;font-family:'Courier New',monospace;font-size:12px;text-decoration:none;transition:all 0.2s}
.nav a:hover{background:#00ccff22;border-color:#00ccff}
.nav a.active{background:#00ff8822;color:#00ff88;border-color:#00ff88}
.status{padding:4px 12px;border-radius:12px;font-size:12px;font-weight:bold}
.status-training{background:#00ff8822;color:#00ff88;border:1px solid #00ff88}
.status-idle{background:#ff880022;color:#ff8800;border:1px solid #ff8800}
.status-ready{background:#aa88ff22;color:#aa88ff;border:1px solid #aa88ff}
.btn{background:#1a1a2e;color:#00ccff;border:1px solid #00ccff44;padding:6px 14px;border-radius:6px;font-family:'Courier New',monospace;font-size:12px;cursor:pointer;transition:all 0.2s}
.btn:hover{background:#00ccff22;border-color:#00ccff}
.container{max-width:1200px;margin:0 auto;padding:16px}
.row{display:grid;gap:16px;margin-bottom:16px}
.row-2{grid-template-columns:1fr 1fr}
@media(max-width:768px){.row-2{grid-template-columns:1fr}}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:16px}
.stat-card{background:#111;border:1px solid #222;border-radius:8px;padding:14px;text-align:center}
.stat-card .label{color:#666;font-size:10px;text-transform:uppercase;letter-spacing:1px}
.stat-card .value{color:#00ff88;font-size:24px;font-weight:bold;margin-top:4px}
.stat-card .sub{color:#555;font-size:11px;margin-top:2px}
.panel{background:#111;border:1px solid #222;border-radius:8px;overflow:hidden;display:flex;flex-direction:column}
.panel-header{background:#1a1a1a;padding:12px 16px;border-bottom:1px solid #222;font-size:13px;color:#888;display:flex;justify-content:space-between;align-items:center}
.panel-body{padding:16px;flex:1;overflow:auto}
.panel-body.np{padding:0}
canvas{width:100%;height:200px}
.messages{max-height:250px;overflow-y:auto;font-size:12px}
.msg{padding:5px 0;border-bottom:1px solid #1a1a1a;color:#aaa;word-break:break-all}
.progress-bar{width:100%;height:6px;background:#222;border-radius:3px;overflow:hidden;margin-top:8px}
.progress-fill{height:100%;background:linear-gradient(90deg,#00ff88,#00cc6a);transition:width 0.5s;border-radius:3px}
.toggle-group{display:flex;flex-direction:column;gap:12px}
.toggle-row{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:#0d0d0d;border-radius:6px;border:1px solid #222}
.toggle-label{font-size:13px;color:#ccc}
.toggle-desc{font-size:10px;color:#555;margin-top:2px}
.switch{position:relative;width:44px;height:24px;cursor:pointer}
.switch input{opacity:0;width:0;height:0}
.slider{position:absolute;top:0;left:0;right:0;bottom:0;background:#333;border-radius:24px;transition:0.3s}
.slider:before{position:absolute;content:"";height:18px;width:18px;left:3px;bottom:3px;background:#666;border-radius:50%;transition:0.3s}
.switch input:checked+.slider{background:#00ff8844}
.switch input:checked+.slider:before{transform:translateX(20px);background:#00ff88}
.footer{text-align:center;padding:16px;color:#333;font-size:11px}
.toast{position:fixed;bottom:20px;right:20px;background:#00ff8822;border:1px solid #00ff88;color:#00ff88;padding:12px 20px;border-radius:8px;font-size:13px;opacity:0;transition:opacity 0.3s;pointer-events:none;z-index:100}
.toast.show{opacity:1}
</style>
</head>
<body>
<div class="header">
    <h1>🧠 DikaAI Dashboard</h1>
    <div class="header-right">
        <div class="nav">
            <a href="/" class="active">📊 Dashboard</a>
            <a href="/chat">💬 Chat</a>
            <a href="/v1/health">🔌 API</a>
        </div>
        <span id="status-badge" class="status status-idle">IDLE</span>
        <button class="btn" onclick="exportCSV()">📥 Export</button>
    </div>
</div>
<div class="container">
    <div class="stats-grid">
        <div class="stat-card"><div class="label">Messages</div><div class="value" id="total-msgs">0</div><div class="sub" id="unique-chats">0 chats</div></div>
        <div class="stat-card"><div class="label">Processed</div><div class="value" id="processed">0</div><div class="progress-bar"><div class="progress-fill" id="process-bar" style="width:0%"></div></div></div>
        <div class="stat-card"><div class="label">Steps</div><div class="value" id="train-steps">0</div><div class="sub" id="model-params">0 params</div></div>
        <div class="stat-card"><div class="label">Loss</div><div class="value" id="current-loss">-</div><div class="sub" id="avg-loss">avg: -</div></div>
        <div class="stat-card"><div class="label">Vocab</div><div class="value" id="vocab-size">0</div></div>
        <div class="stat-card"><div class="label">Uptime</div><div class="value" id="uptime">0m</div></div>
    </div>
    <div class="row row-2">
        <div class="panel">
            <div class="panel-header"><span>🎛️ Controls</span></div>
            <div class="panel-body">
                <div class="toggle-group">
                    <div class="toggle-row"><div><div class="toggle-label">🤖 Auto-Reply</div><div class="toggle-desc">Balas otomatis di Telegram</div></div><label class="switch"><input type="checkbox" id="toggle-reply" checked onchange="toggleFeature('auto_reply',this.checked)"><span class="slider"></span></label></div>
                    <div class="toggle-row"><div><div class="toggle-label">🧠 Training</div><div class="toggle-desc">Model belajar dari data</div></div><label class="switch"><input type="checkbox" id="toggle-training" checked onchange="toggleFeature('training',this.checked)"><span class="slider"></span></label></div>
                    <div class="toggle-row"><div><div class="toggle-label">📱 Scraping</div><div class="toggle-desc">Ambil chat dari Telegram</div></div><label class="switch"><input type="checkbox" id="toggle-scraping" checked onchange="toggleFeature('scraping',this.checked)"><span class="slider"></span></label></div>
                </div>
            </div>
        </div>
        <div class="panel">
            <div class="panel-header"><span>💬 Quick Chat</span><a href="/chat" style="color:#00ccff;font-size:11px;text-decoration:none">Open Full Chat →</a></div>
            <div class="panel-body np">
                <div style="display:flex;flex-direction:column;height:200px">
                    <div id="quick-chat" style="flex:1;overflow-y:auto;padding:12px;font-size:13px"></div>
                    <div style="display:flex;gap:8px;padding:12px;border-top:1px solid #222">
                        <input type="text" id="quick-input" placeholder="Quick ask..." style="flex:1;background:#0a0a0a;border:1px solid #333;color:#00ff88;padding:8px 12px;border-radius:6px;font-family:'Courier New',monospace;font-size:12px;outline:none" onkeydown="if(event.key==='Enter')quickChat()">
                        <button onclick="quickChat()" style="background:#00ff8822;color:#00ff88;border:1px solid #00ff88;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:'Courier New',monospace;font-weight:bold">Send</button>
                    </div>
                </div>
            </div>
        </div>
        <div class="panel">
            <div class="panel-header"><span>💬 Recent Messages</span><span id="msg-count">0</span></div>
            <div class="panel-body"><div class="messages" id="msg-list"></div></div>
        </div>
    </div>
    <div class="panel">
        <div class="panel-header"><span>📈 Training Loss</span><span id="chart-info">0 points</span></div>
        <div class="panel-body"><canvas id="lossChart"></canvas></div>
    </div>
</div>
<div class="footer">DikaAI v3.1 - Live Dashboard | Auto-refresh: 10s | Powered by Vercel + Upstash Redis</div>
<div class="toast" id="toast"></div>
<script>
const $=id=>document.getElementById(id);
function formatNum(n){if(n>=1e6)return(n/1e6).toFixed(1)+'M';if(n>=1e3)return(n/1e3).toFixed(1)+'K';return n.toString()}
function formatTime(s){if(s>=3600)return Math.floor(s/3600)+'h '+Math.floor((s%3600)/60)+'m';return Math.floor(s/60)+'m'}
function toast(msg){const t=$('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2000)}
function esc(t){return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
async function toggleFeature(f,e){try{const r=await fetch('/api/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({feature:f,enabled:e})});const d=await r.json();toast(d.ok?'✅ '+f+(e?' ON':' OFF'):'❌ Error')}catch(x){toast('❌ Connection error')}}
async function quickChat(){const i=$('quick-input');const t=i.value.trim();if(!t)return;i.value='';const box=$('quick-chat');box.innerHTML+=`<div style="color:#00ff88;text-align:right;margin:4px 0;font-size:12px">${esc(t)}</div>`;try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:t})});const d=await r.json();box.innerHTML+=`<div style="color:#00ccff;margin:4px 0;font-size:12px">${esc(d.reply||'(no reply)')}</div>`}catch(x){box.innerHTML+=`<div style="color:#ff4444;margin:4px 0;font-size:12px">Error</div>`}box.scrollTop=box.scrollHeight}
function exportCSV(){fetch('/api/export').then(r=>r.blob()).then(b=>{const u=URL.createObjectURL(b);const a=document.createElement('a');a.href=u;a.download='dikaai_'+new Date().toISOString().slice(0,10)+'.csv';document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(u);toast('✅ CSV exported!')}).catch(()=>toast('❌ Export failed'))}
function drawChart(losses){const c=$('lossChart');const ctx=c.getContext('2d');const dpr=window.devicePixelRatio||1;c.width=c.offsetWidth*dpr;c.height=200*dpr;ctx.scale(dpr,dpr);const w=c.offsetWidth,h=200;ctx.clearRect(0,0,w,h);if(!losses||losses.length<2){ctx.fillStyle='#333';ctx.font='14px Courier New';ctx.textAlign='center';ctx.fillText('Waiting for training data...',w/2,h/2);return}const maxL=Math.max(...losses)*1.1||1;ctx.strokeStyle='#1a1a1a';ctx.lineWidth=1;for(let i=0;i<=4;i++){const y=(i/4)*h;ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();ctx.fillStyle='#333';ctx.font='10px Courier New';ctx.textAlign='left';ctx.fillText((maxL-(i/4)*maxL).toFixed(2),4,y+12)}ctx.strokeStyle='#00ff88';ctx.lineWidth=2;ctx.shadowColor='#00ff88';ctx.shadowBlur=4;ctx.beginPath();for(let i=0;i<losses.length;i++){const x=(i/(losses.length-1))*w;const y=h-(losses[i]/maxL)*h;i===0?ctx.moveTo(x,y):ctx.lineTo(x,y)}ctx.stroke();ctx.shadowBlur=0;ctx.lineTo(w,h);ctx.lineTo(0,h);ctx.closePath();const g=ctx.createLinearGradient(0,0,0,h);g.addColorStop(0,'#00ff8822');g.addColorStop(1,'#00ff8800');ctx.fillStyle=g;ctx.fill()}
async function fetchStats(){try{const r=await fetch('/api/stats');const d=await r.json();updateUI(d)}catch(e){}}
function updateUI(d){const db=d.db||{},m=d.model||{};$('status-badge').textContent=(d.status||'idle').toUpperCase();$('status-badge').className='status status-'+(d.status||'idle');$('total-msgs').textContent=formatNum(db.total||0);$('unique-chats').textContent=(db.unique_chats||0)+' chats';$('processed').textContent=formatNum(db.processed||0);$('process-bar').style.width=(db.total?Math.round(db.processed/db.total*100):0)+'%';$('train-steps').textContent=formatNum(m.step||0);$('model-params').textContent=formatNum(m.params||0)+' params';const chart=d.loss_chart||{},losses=chart.losses||[];if(losses.length>0)$('current-loss').textContent=losses[losses.length-1].toFixed(4);if(d.total_loss!==undefined&&d.total_steps>0)$('avg-loss').textContent='avg: '+(d.total_loss/d.total_steps).toFixed(4);$('vocab-size').textContent=d.vocab_tokens||m.vocab_size||0;$('uptime').textContent=formatTime(d.uptime||0);const t=d.toggles||{};if($('toggle-reply'))$('toggle-reply').checked=t.auto_reply!==false;if($('toggle-training'))$('toggle-training').checked=t.training!==false;if($('toggle-scraping'))$('toggle-scraping').checked=t.scraping!==false;drawChart(losses);$('chart-info').textContent=losses.length+' points';const msgs=d.recent_messages||[];$('msg-count').textContent=msgs.length+' recent';$('msg-list').innerHTML=msgs.slice().reverse().map(m=>'<div class="msg">'+esc(m)+'</div>').join('')}
setInterval(fetchStats,10000);fetchStats();
</script>
</body>
</html>"""


# ============================================================
# HTML - Full Chat UI
# ============================================================

CHAT_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DikaAI Chat</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0a0a0f;--surface:#12121a;--surface2:#1a1a25;--border:#2a2a3a;--text:#e0e0e8;--text2:#888899;--primary:#6c5ce7;--primary2:#a29bfe;--green:#00b894;--red:#e17055;--yellow:#fdcb6e;--code-bg:#0d1117;--radius:12px}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column}
.header{background:var(--surface);border-bottom:1px solid var(--border);padding:12px 20px;display:flex;align-items:center;gap:12px}
.header .logo{font-size:20px;font-weight:700;background:linear-gradient(135deg,var(--primary),var(--primary2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header .nav{display:flex;gap:4px;margin-left:12px}
.header .nav a{color:var(--text2);text-decoration:none;font-size:13px;padding:4px 10px;border-radius:6px;transition:all 0.2s}
.header .nav a:hover{color:var(--text);background:var(--surface2)}
.header .nav a.active{color:var(--primary2);background:var(--primary)20}
.header .status{font-size:12px;color:var(--green);display:flex;align-items:center;gap:6px}
.header .status::before{content:'';width:8px;height:8px;background:var(--green);border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}
.header .stats{margin-left:auto;font-size:11px;color:var(--text2)}
.container{display:flex;flex:1;overflow:hidden}
.sidebar{width:260px;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden}
.sidebar h3{padding:16px;font-size:13px;color:var(--text2);text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid var(--border)}
.sidebar .memory-list{flex:1;overflow-y:auto;padding:8px}
.memory-item{padding:10px 12px;border-radius:8px;margin-bottom:4px;font-size:13px;cursor:pointer;transition:background 0.2s}
.memory-item:hover{background:var(--surface2)}
.memory-item .label{color:var(--primary2);font-weight:600;font-size:11px;text-transform:uppercase;margin-bottom:4px}
.memory-item .value{color:var(--text);line-height:1.4}
.chat-area{flex:1;display:flex;flex-direction:column;overflow:hidden}
.messages{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:16px}
.message{max-width:80%;animation:fadeIn 0.3s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.message.user{align-self:flex-end}
.message.assistant{align-self:flex-start}
.message .bubble{padding:12px 16px;border-radius:var(--radius);line-height:1.6;font-size:14px;white-space:pre-wrap;word-wrap:break-word}
.message.user .bubble{background:var(--primary);color:white;border-bottom-right-radius:4px}
.message.assistant .bubble{background:var(--surface2);color:var(--text);border-bottom-left-radius:4px}
.message .meta{font-size:11px;color:var(--text2);margin-top:4px;padding:0 4px;display:flex;gap:12px}
.message.user .meta{text-align:right;justify-content:flex-end}
.route-tag{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;text-transform:uppercase}
.route-tag.code{background:#6c5ce720;color:var(--primary2)}
.route-tag.tool{background:#00b89420;color:var(--green)}
.route-tag.reason{background:#e1705520;color:var(--red)}
.route-tag.search{background:#fdcb6e20;color:var(--yellow)}
.route-tag.chat{background:#88889920;color:var(--text2)}
.bubble code{background:var(--code-bg);padding:2px 6px;border-radius:4px;font-family:'SF Mono','Fira Code',monospace;font-size:13px}
.bubble pre{background:var(--code-bg);padding:12px;border-radius:8px;overflow-x:auto;margin:8px 0}
.bubble pre code{background:none;padding:0}
.typing{display:flex;gap:4px;padding:12px 16px;background:var(--surface2);border-radius:var(--radius);border-bottom-left-radius:4px;width:fit-content}
.typing span{width:8px;height:8px;background:var(--text2);border-radius:50%;animation:bounce 1.4s infinite ease-in-out}
.typing span:nth-child(1){animation-delay:0s}
.typing span:nth-child(2){animation-delay:0.2s}
.typing span:nth-child(3){animation-delay:0.4s}
@keyframes bounce{0%,80%,100%{transform:scale(0)}40%{transform:scale(1)}}
.input-area{padding:16px 20px;background:var(--surface);border-top:1px solid var(--border)}
.input-wrapper{display:flex;gap:8px;max-width:900px;margin:0 auto}
.input-wrapper textarea{flex:1;background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);padding:12px 16px;color:var(--text);font-size:14px;font-family:inherit;resize:none;min-height:44px;max-height:200px;line-height:1.5;transition:border-color 0.2s}
.input-wrapper textarea:focus{outline:none;border-color:var(--primary)}
.input-wrapper textarea::placeholder{color:var(--text2)}
.send-btn{background:var(--primary);color:white;border:none;border-radius:var(--radius);padding:0 20px;font-size:14px;font-weight:600;cursor:pointer;transition:all 0.2s;min-width:60px}
.send-btn:hover{background:var(--primary2)}
.send-btn:disabled{opacity:0.5;cursor:not-allowed}
.welcome{text-align:center;padding:60px 20px;color:var(--text2)}
.welcome h2{font-size:28px;margin-bottom:8px;background:linear-gradient(135deg,var(--primary),var(--primary2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.welcome p{font-size:14px;max-width:500px;margin:0 auto;line-height:1.6}
.welcome .chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:24px}
.welcome .chip{background:var(--surface2);border:1px solid var(--border);border-radius:20px;padding:8px 16px;font-size:13px;color:var(--text);cursor:pointer;transition:all 0.2s}
.welcome .chip:hover{border-color:var(--primary);color:var(--primary2)}
@media(max-width:768px){.sidebar{display:none}.message{max-width:95%}}
</style>
</head>
<body>
<div class="header">
  <div class="logo">🧠 DikaAI</div>
  <div class="nav">
    <a href="/">📊 Dashboard</a>
    <a href="/chat" class="active">💬 Chat</a>
    <a href="/v1/health">🔌 API</a>
  </div>
  <div class="status">Online</div>
  <div class="stats" id="stats">Loading...</div>
</div>
<div class="container">
  <div class="sidebar">
    <h3>📊 Engine</h3>
    <div class="memory-list" id="memory">
      <div class="memory-item"><div class="label">Total Tasks</div><div class="value" id="mem-tasks">-</div></div>
      <div class="memory-item"><div class="label">Success Rate</div><div class="value" id="mem-rate">-</div></div>
      <div class="memory-item"><div class="label">Episodes</div><div class="value" id="mem-episodes">-</div></div>
      <div class="memory-item"><div class="label">Facts</div><div class="value" id="mem-facts">-</div></div>
      <div class="memory-item"><div class="label">Topics</div><div class="value" id="mem-topics">-</div></div>
      <div class="memory-item"><div class="label">Tokens</div><div class="value" id="mem-tokens">-</div></div>
      <div class="memory-item"><div class="label">Model Step</div><div class="value" id="mem-step">-</div></div>
      <div class="memory-item"><div class="label">Vocab</div><div class="value" id="mem-vocab">-</div></div>
    </div>
  </div>
  <div class="chat-area">
    <div class="messages" id="messages">
      <div class="welcome">
        <h2>DikaAI v3.1</h2>
        <p>AI Coding Agent with memory, context, multi-language code generation, and tools.</p>
        <div class="chips">
          <div class="chip" onclick="send('Write a fibonacci function')">🔢 Fibonacci</div>
          <div class="chip" onclick="send('Write a binary search in Python')">🔍 Binary Search</div>
          <div class="chip" onclick="send('Fix this error: TypeError on line 5')">🐛 Fix Error</div>
          <div class="chip" onclick="send('git status')">📂 Git Status</div>
          <div class="chip" onclick="send('Explain quicksort algorithm')">🧠 Explain</div>
          <div class="chip" onclick="send('Write a Rust struct with methods')">🦀 Rust</div>
          <div class="chip" onclick="send('Write a JavaScript debounce function')">⚡ JS Debounce</div>
          <div class="chip" onclick="send('Write a C++ vector sort with lambda')">🔷 C++ Sort</div>
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
const messages=document.getElementById('messages');const input=document.getElementById('input');const sendBtn=document.getElementById('sendBtn');let isLoading=false;
input.addEventListener('input',()=>{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,200)+'px'});
input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendFromInput()}});
function sendFromInput(){const t=input.value.trim();if(!t||isLoading)return;send(t);input.value='';input.style.height='auto'}
async function send(text){if(isLoading)return;isLoading=true;sendBtn.disabled=true;const welcome=messages.querySelector('.welcome');if(welcome)welcome.remove();addMessage('user',text);const typing=document.createElement('div');typing.className='message assistant';typing.innerHTML='<div class="typing"><span></span><span></span><span></span></div>';messages.appendChild(typing);messages.scrollTop=messages.scrollHeight;try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});const d=await r.json();typing.remove();addMessage('assistant',d.response,{route:d.route,time:d.time,topic:d.topic});loadStats()}catch(err){typing.remove();addMessage('assistant','Error: '+err.message,{route:'error'})}isLoading=false;sendBtn.disabled=false;input.focus()}
function addMessage(role,content,meta={}){const div=document.createElement('div');div.className='message '+role;let metaHtml='';if(meta.route)metaHtml+=`<span class="route-tag ${meta.route}">${meta.route}</span>`;if(meta.time)metaHtml+=`<span>\u23f1 ${meta.time}</span>`;if(meta.topic)metaHtml+=`<span>📁 ${meta.topic}</span>`;let formatted=escHtml(content);formatted=formatted.replace(/```(\w+)?\n([\s\S]*?)```/g,'<pre><code>$2</code></pre>');formatted=formatted.replace(/`([^`]+)`/g,'<code>$1</code>');div.innerHTML=`<div class="bubble">${formatted}</div>${metaHtml?'<div class="meta">'+metaHtml+'</div>':''}`;messages.appendChild(div);messages.scrollTop=messages.scrollHeight}
function escHtml(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML}
async function loadStats(){try{const r=await fetch('/api/stats');const d=await r.json();document.getElementById('stats').textContent=`${d.db?.total||0} tasks | ${d.status||'idle'}`;if(d.model)document.getElementById('mem-step').textContent=d.model.step||0;if(d.model)document.getElementById('mem-vocab').textContent=d.model.vocab_size||0;const e=d.engine||{};document.getElementById('mem-tasks').textContent=e.total||0;document.getElementById('mem-rate').textContent=e.rate||'0%';document.getElementById('mem-episodes').textContent=e.episodes||0;document.getElementById('mem-facts').textContent=e.facts||0;document.getElementById('mem-topics').textContent=e.topics||0;document.getElementById('mem-tokens').textContent=e.tokens||0}catch(e){}}
loadStats();setInterval(loadStats,30000);
</script>
</body>
</html>"""


# ============================================================
# HTML - API Docs
# ============================================================

API_DOCS_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DikaAI API</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a0f;color:#e0e0e8;padding:40px 20px}
.container{max-width:900px;margin:0 auto}
h1{font-size:32px;margin-bottom:8px;background:linear-gradient(135deg,#6c5ce7,#a29bfe);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{color:#888;margin-bottom:32px;font-size:14px}
h2{font-size:20px;margin:32px 0 16px;color:#a29bfe;border-bottom:1px solid #2a2a3a;padding-bottom:8px}
.endpoint{background:#12121a;border:1px solid #2a2a3a;border-radius:12px;padding:16px;margin-bottom:12px}
.endpoint .method{display:inline-block;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:700;margin-right:8px}
.method.get{background:#00b89420;color:#00b894}
.method.post{background:#6c5ce720;color:#a29bfe}
.endpoint .path{font-family:'SF Mono',monospace;font-size:14px;color:#e0e0e8}
.endpoint .desc{color:#888;font-size:13px;margin-top:8px}
.endpoint .auth{color:#fdcb6e;font-size:11px;margin-top:4px}
pre{background:#12121a;border:1px solid #2a2a3a;border-radius:8px;padding:16px;overflow-x:auto;font-size:13px;margin:12px 0}
code{font-family:'SF Mono',monospace}
.cli{background:#1a1a25;border:1px solid #2a2a3a;border-radius:8px;padding:16px;margin:12px 0;font-size:13px}
.cli .comment{color:#666}
.cli .cmd{color:#00b894}
a{color:#a29bfe;text-decoration:none}
a:hover{text-decoration:underline}
.nav{display:flex;gap:8px;margin-bottom:24px}
.nav a{color:#888;font-size:14px;padding:6px 14px;border-radius:6px;border:1px solid #2a2a3a;transition:all 0.2s}
.nav a:hover{color:#a29bfe;border-color:#a29bfe}
</style>
</head>
<body>
<div class="container">
<h1>DikaAI API</h1>
<p class="sub">OpenAI-compatible API for coding, chat, and agent tasks. <a href="/">← Back to Dashboard</a></p>
<div class="nav"><a href="/">Dashboard</a><a href="/chat">Chat</a><a href="/v1/health">Health</a><a href="/v1/models">Models</a></div>

<h2>Authentication</h2>
<p>All endpoints require Bearer token:</p>
<pre><code>Authorization: Bearer dka_xxxxxxxx</code></pre>
<p>Get a token: <code>python main.py token my-app</code></p>

<h2>Chat (OpenAI-compatible)</h2>
<div class="endpoint"><span class="method post">POST</span><span class="path">/v1/chat/completions</span><div class="desc">Chat with DikaAI. OpenAI-compatible format.</div><div class="auth">🔑 Required: chat scope</div></div>
<pre><code>curl -X POST https://your-app.vercel.app/v1/chat/completions \
  -H "Authorization: Bearer dka_xxx" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Write a fibonacci function"}]}'</code></pre>

<h2>Coding Agent</h2>
<div class="endpoint"><span class="method post">POST</span><span class="path">/v1/agent</span><div class="desc">Run coding agent with plan → code → test → debug loop.</div><div class="auth">🔑 Required: agent scope</div></div>
<pre><code>curl -X POST https://your-app.vercel.app/v1/agent \
  -H "Authorization: Bearer dka_xxx" \
  -H "Content-Type: application/json" \
  -d '{"task": "Fix the error in main.py"}'</code></pre>

<h2>Tools</h2>
<div class="endpoint"><span class="method post">POST</span><span class="path">/v1/tools/read</span><div class="desc">Read file content.</div><div class="auth">🔑 Required: tools scope</div></div>
<div class="endpoint"><span class="method post">POST</span><span class="path">/v1/tools/search</span><div class="desc">Search codebase.</div><div class="auth">🔑 Required: tools scope</div></div>
<div class="endpoint"><span class="method post">POST</span><span class="path">/v1/tools/run</span><div class="desc">Run shell command.</div><div class="auth">🔑 Required: tools scope</div></div>

<h2>Connect External Tools</h2>
<div class="cli">
<span class="comment"># Claude Code / Cursor / Codex</span><br>
<span class="cmd">export OPENAI_API_BASE=https://your-app.vercel.app/v1</span><br>
<span class="cmd">export OPENAI_API_KEY=dka_xxx</span><br><br>
<span class="comment"># Or use curl directly</span><br>
<span class="cmd">curl https://your-app.vercel.app/v1/chat/completions \</span><br>
<span class="cmd">  -H "Authorization: Bearer dka_xxx" \</span><br>
<span class="cmd">  -d '{"messages":[{"role":"user","content":"hello"}]}'</span>
</div>

<h2>Endpoints</h2>
<table style="width:100%;border-collapse:collapse;margin-top:12px">
<tr style="border-bottom:1px solid #2a2a3a"><th style="text-align:left;padding:8px;color:#a29bfe">Method</th><th style="text-align:left;padding:8px;color:#a29bfe">Path</th><th style="text-align:left;padding:8px;color:#a29bfe">Auth</th><th style="text-align:left;padding:8px;color:#a29bfe">Description</th></tr>
<tr style="border-bottom:1px solid #1a1a25"><td style="padding:8px;color:#00b894">GET</td><td style="padding:8px;font-family:monospace">/v1/health</td><td style="padding:8px;color:#666">No</td><td style="padding:8px;color:#888">Health check</td></tr>
<tr style="border-bottom:1px solid #1a1a25"><td style="padding:8px;color:#00b894">GET</td><td style="padding:8px;font-family:monospace">/v1/models</td><td style="padding:8px;color:#666">No</td><td style="padding:8px;color:#888">List models</td></tr>
<tr style="border-bottom:1px solid #1a1a25"><td style="padding:8px;color:#a29bfe">POST</td><td style="padding:8px;font-family:monospace">/v1/chat/completions</td><td style="padding:8px;color:#fdcb6e">chat</td><td style="padding:8px;color:#888">Chat (OpenAI-compat)</td></tr>
<tr style="border-bottom:1px solid #1a1a25"><td style="padding:8px;color:#a29bfe">POST</td><td style="padding:8px;font-family:monospace">/v1/completions</td><td style="padding:8px;color:#fdcb6e">chat</td><td style="padding:8px;color:#888">Completion</td></tr>
<tr style="border-bottom:1px solid #1a1a25"><td style="padding:8px;color:#a29bfe">POST</td><td style="padding:8px;font-family:monospace">/v1/agent</td><td style="padding:8px;color:#fdcb6e">agent</td><td style="padding:8px;color:#888">Coding agent</td></tr>
<tr style="border-bottom:1px solid #1a1a25"><td style="padding:8px;color:#a29bfe">POST</td><td style="padding:8px;font-family:monospace">/v1/tools/read</td><td style="padding:8px;color:#fdcb6e">tools</td><td style="padding:8px;color:#888">Read file</td></tr>
<tr style="border-bottom:1px solid #1a1a25"><td style="padding:8px;color:#a29bfe">POST</td><td style="padding:8px;font-family:monospace">/v1/tools/search</td><td style="padding:8px;color:#fdcb6e">tools</td><td style="padding:8px;color:#888">Search code</td></tr>
<tr style="border-bottom:1px solid #1a1a25"><td style="padding:8px;color:#a29bfe">POST</td><td style="padding:8px;font-family:monospace">/v1/tools/run</td><td style="padding:8px;color:#fdcb6e">tools</td><td style="padding:8px;color:#888">Run command</td></tr>
<tr style="border-bottom:1px solid #1a1a25"><td style="padding:8px;color:#a29bfe">POST</td><td style="padding:8px;font-family:monospace">/v1/auth/token</td><td style="padding:8px;color:#fdcb6e">admin</td><td style="padding:8px;color:#888">Create token</td></tr>
<tr><td style="padding:8px;color:#00b894">GET</td><td style="padding:8px;font-family:monospace">/v1/auth/tokens</td><td style="padding:8px;color:#fdcb6e">admin</td><td style="padding:8px;color:#888">List tokens</td></tr>
</table>
</div>
</body>
</html>"""


# ============================================================
# HTTP Handler
# ============================================================

class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler - Dashboard + Chat + Full API."""

    def log_message(self, format, *args):
        pass

    # ---- helpers ----

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

        # Dashboard UI
        if path == '/' or path == '/index.html':
            self._html(DASHBOARD_HTML)
            return

        # Full Chat UI
        if path == '/chat':
            self._html(CHAT_HTML)
            return

        # API Docs
        if path == '/docs' or path == '/api':
            self._html(API_DOCS_HTML)
            return

        # ---- Dashboard API ----

        if path == '/api/stats':
            stats = _get_stats()
            # Add engine stats if available
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
            writer.writerow(['timestamp','datetime','loss','steps','total_steps','avg_loss','total_messages'])
            for h in history:
                dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(h['timestamp']))
                writer.writerow([f"{h['timestamp']:.3f}", dt, f"{h['loss']:.6f}", h['steps'], h['total_steps'], f"{h['avg_loss']:.6f}", h['total_messages']])
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="dikaai_training.csv"')
            self.end_headers()
            self.wfile.write(output.getvalue().encode())
            return

        # ---- Public API (no auth) ----

        if path == '/v1/health':
            engine = _get_engine()
            self._json({
                'status': 'ok', 'version': '3.1.0', 'timestamp': time.time(),
                'engine': engine is not None,
                'redis': USE_REDIS,
            })
            return

        if path == '/v1/models':
            self._json({'data': [
                {'id': 'dikaai-v3', 'object': 'model', 'capabilities': ['chat','code','agent','tools','reasoning']}
            ]})
            return

        # ---- Auth endpoints ----

        if path == '/v1/auth/tokens':
            ok, err = self._check_auth('admin')
            if not ok:
                self._json(err, 401)
                return
            ta = TokenAuth()
            self._json({'tokens': ta.list_tokens()})
            return

        # ---- Fallback ----
        self.send_response(404)
        self.end_headers()

    # ---- POST ----

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._body()

        # ---- Dashboard API ----

        if path == '/api/toggle':
            self._json({'ok': True, 'feature': body.get('feature',''), 'enabled': body.get('enabled',True)})
            return

        if path == '/api/chat':
            text = body.get('message', '').strip()
            if not text:
                self._json({'error': 'empty message'}, 400)
                return
            reply = _generate_reply(text)
            self._json({'reply': reply})
            return

        # ---- Public API ----

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

            # Use Engine for full processing
            engine = _get_engine()
            if engine:
                try:
                    result = engine.process(user_msg)
                    response = result.get('response', '')
                except Exception:
                    response = _generate_reply(user_msg)
            else:
                response = _generate_reply(user_msg)

            self._json({
                'id': f'chatcmpl-{int(time.time()*1000)}',
                'object': 'chat.completion',
                'created': int(time.time()),
                'model': 'dikaai-v3',
                'choices': [{
                    'index': 0,
                    'message': {'role': 'assistant', 'content': response},
                    'finish_reason': 'stop',
                }],
                'usage': {
                    'prompt_tokens': len(user_msg.split()),
                    'completion_tokens': len(response.split()),
                    'total_tokens': len(user_msg.split()) + len(response.split()),
                },
            })
            return

        if path == '/v1/completions':
            prompt = body.get('prompt', '')
            if not prompt:
                self._json({'error': 'No prompt'}, 400)
                return
            response = _generate_reply(prompt)
            self._json({
                'id': f'cmpl-{int(time.time()*1000)}',
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
                    self._json({'task': task, 'response': result.get('response',''), 'route': result.get('route',''), 'success': result.get('success',True)})
                except Exception as e:
                    self._json({'task': task, 'error': str(e), 'success': False})
            else:
                self._json({'task': task, 'response': _generate_reply(task), 'success': True})
            return

        # ---- Tools (execute locally on Vercel - limited) ----

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
            # Simple grep in project
            matches = []
            try:
                import subprocess
                result = subprocess.run(
                    ['grep', '-rn', '--include=*.py', '--include=*.js', '--include=*.ts', '-i', query, str(BASE_DIR)],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.strip().split('\n')[:20]:
                    if ':' in line:
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            matches.append({'file': parts[0].replace(str(BASE_DIR)+'/', ''), 'line': parts[1], 'content': parts[2][:100]})
            except Exception:
                pass
            self._json({'query': query, 'matches': matches, 'count': len(matches)})
            return

        if path == '/v1/tools/run':
            command = body.get('command', '') or body.get('cmd', '')
            if not command:
                self._json({'error': 'No command'}, 400)
                return
            # Safety: only allow safe commands
            safe = ['ls', 'pwd', 'echo', 'date', 'whoami', 'cat', 'head', 'tail', 'wc', 'grep']
            cmd_first = command.strip().split()[0] if command.strip() else ''
            if cmd_first not in safe:
                self._json({'error': f'Command not allowed on Vercel. Allowed: {", ".join(safe)}'}, 403)
                return
            try:
                import subprocess
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5, cwd=str(BASE_DIR))
                self._json({'command': command, 'stdout': result.stdout[:5000], 'stderr': result.stderr[:1000], 'exit_code': result.returncode})
            except Exception as e:
                self._json({'error': str(e)}, 500)
            return

        # ---- Auth management ----

        if path == '/v1/auth/token':
            ok, err = self._check_auth('admin')
            if not ok:
                self._json(err, 401)
                return
            name = body.get('name', 'unnamed')
            scopes = body.get('scopes', 'chat,code,agent')
            ta = TokenAuth()
            token = ta.create(name, scopes)
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
            ta = TokenAuth()
            success = ta.revoke(token)
            self._json({'ok': success})
            return

        # ---- Fallback ----
        self.send_response(404)
        self.end_headers()
