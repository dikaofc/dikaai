#!/usr/bin/env python3
"""
DikaAI - Google Colab Runner (v5 - 180+ SOURCES PARALLEL)
==========================================================
Copy-paste SEMUA ke SATU cell di Colab.
Ganti config, lalu Run! Semua fitur jalan otomatis.

Features (ALL automatic):
  1. Web Scrape (180+ sources: NusaCrowd, HuggingFace, Wikipedia, StackOverflow,
     GitHub, Python/JS/Rust/Go/Kotlin/C++ docs, MDN, Linux/DevOps, Android,
     ML/AI, conversational, DuckDuckGo, news, Kaskus - ALL PARALLEL)
  2. Training (500 epochs from web data + continuous background)
  3. Benchmark (coding capability test)
  4. Telegram Bot (auto-reply + scrape all chats)
  5. Redis Sync (Vercel dashboard auto-update every 30s)
  6. Continuous Training (background, max speed)
  7. Periodic Web Scraping (every 1h, all sources parallel)
  8. Google Drive session persistence

Dashboard: https://dikaai.vercel.app
==========================================================
"""

# ============================================================
# STEP 0: FIX WORKING DIRECTORY (CRITICAL FOR COLAB!)
# ============================================================
import os
import sys
import shutil
import importlib

os.chdir('/content')
print("[0] CWD: " + os.getcwd())

# ============================================================
# STEP 1: MOUNT GOOGLE DRIVE + INSTALL + CLONE
# ============================================================
print("\n[1] Mounting Google Drive + installing dependencies...")

_gdrive_mounted = False
try:
    from google.colab import drive
    drive.mount('/content/drive', force_remount=False)
    _gdrive_mounted = True
    print("    Google Drive mounted!")
except Exception:
    print("    Google Drive not available (not Colab?)")

os.system('pip install telethon aiohttp nest_asyncio -q')
# PyTorch (Colab GPU runtime has it preinstalled; install as fallback / pin CPU-free)
os.system('pip install torch -q')

if os.path.exists('/content/dikaai'):
    print("    Removing old clone...")
    shutil.rmtree('/content/dikaai', ignore_errors=True)

exit_code = os.system('git clone --depth 1 https://github.com/dikaofc/dikaai.git /content/dikaai')
if exit_code != 0:
    print("ERROR: git clone failed!")
    raise SystemExit(1)

if not os.path.exists('/content/dikaai/main.py'):
    print("ERROR: Clone incomplete!")
    raise SystemExit(1)

os.chdir('/content/dikaai')
sys.path.insert(0, '/content/dikaai')
print("    Project CWD: " + os.getcwd())

# ============================================================
# SELF-HEAL: ensure webscraper.py has the latest API (max_workers).
# git clone sometimes fetches a stale CDN copy; force-pull the canonical
# file via raw URL so the constructor signature is correct.
# ============================================================
try:
    import urllib.request
    _ws_url = "https://raw.githubusercontent.com/dikaofc/dikaai/main/webscraper.py"
    _ws_path = os.path.join('/content/dikaai', 'webscraper.py')
    _req = urllib.request.Request(_ws_url, headers={'User-Agent': 'colab'})
    _ws_code = urllib.request.urlopen(_req, timeout=30).read().decode('utf-8')
    if 'max_workers' in _ws_code:
        with open(_ws_path, 'w', encoding='utf-8') as _f:
            _f.write(_ws_code)
        print("    webscraper.py self-healed (latest version)")
    else:
        print("    webscraper.py kept (remote also lacked max_workers)")
except Exception as _e:
    print("    webscraper.py self-heal skipped: " + str(_e))

# Restore Telegram session from Google Drive
SESSION_FILE = 'dikaai_session.session'
SESSION_DRIVE_PATH = '/content/drive/MyDrive/dikaai_sessions/'

if _gdrive_mounted:
    os.makedirs(SESSION_DRIVE_PATH, exist_ok=True)
    saved_session = os.path.join(SESSION_DRIVE_PATH, SESSION_FILE)
    local_session = os.path.join('/content/dikaai', SESSION_FILE)
    if os.path.exists(saved_session):
        shutil.copy2(saved_session, local_session)
        print("    Session restored from Google Drive!")
    else:
        print("    No saved session (first time - will need login)")

# Clear ALL Python bytecode cache
for root, dirs, files in os.walk('/content/dikaai'):
    for d in dirs:
        if d == '__pycache__':
            shutil.rmtree(os.path.join(root, d), ignore_errors=True)

importlib.invalidate_caches()

for root, dirs, files in os.walk('/content/dikaai'):
    for f in files:
        if f.endswith('.pyc'):
            os.remove(os.path.join(root, f))

print("    Cache cleared!")

# ============================================================
# STEP 2: CONFIG
# ============================================================
print("\n[2] Writing config...")

# =====================================================
# GANTI BAGIAN INI DENGAN DATA KAMU!
# =====================================================
TELEGRAM_API_ID = 12345678
TELEGRAM_API_HASH = "abc123def456789"
TELEGRAM_PHONE = "+6281234567890"
UPSTASH_REDIS_URL = "https://xxx.upstash.io"
UPSTASH_REDIS_TOKEN = "AXxxxxxx=="
# =====================================================

config_content = "TELEGRAM_API_ID=" + str(TELEGRAM_API_ID) + "\n"
config_content += "TELEGRAM_API_HASH=" + str(TELEGRAM_API_HASH) + "\n"
config_content += "TELEGRAM_PHONE=" + str(TELEGRAM_PHONE) + "\n"
config_content += "UPSTASH_REDIS_REST_URL=" + str(UPSTASH_REDIS_URL) + "\n"
config_content += "UPSTASH_REDIS_REST_TOKEN=" + str(UPSTASH_REDIS_TOKEN) + "\n"
# GPU XL model sizing (T4)
config_content += "MAX_VOCAB_SIZE=25000\n"
config_content += "EMBEDDING_DIM=512\n"
config_content += "HIDDEN_DIM=1024\n"
config_content += "NUM_LAYERS=3\n"
config_content += "CONTEXT_LENGTH=128\n"
config_content += "CHUNK_SIZE=64\n"
config_content += "BATCH_SIZE=128\n"

config_path = os.path.join('/content/dikaai', 'config.env')
with open(config_path, 'w') as f:
    f.write(config_content)

print("    Config saved: " + config_path)
print("    Telegram: " + str(TELEGRAM_PHONE))
print("    Redis: " + str(UPSTASH_REDIS_URL)[:30] + "...")

# ============================================================
# STEP 3: IMPORTS + MAX PERFORMANCE
# ============================================================
print("\n[3] Importing DikaAI modules + optimizing...")

import time
import signal
import threading
import asyncio
import json
import multiprocessing

# Max performance settings for Colab
_num_cores = multiprocessing.cpu_count()
os.environ['OMP_NUM_THREADS'] = str(_num_cores)
os.environ['MKL_NUM_THREADS'] = str(_num_cores)
os.environ['OPENBLAS_NUM_THREADS'] = str(_num_cores)
os.environ['VECLIB_MAXIMUM_THREADS'] = str(_num_cores)
os.environ['NUMEXPR_NUM_THREADS'] = str(_num_cores)
os.environ['TOKENIZERS_PARALLELISM'] = 'true'
print("    CPU cores: " + str(_num_cores) + " | All threads maximized!")

import nest_asyncio
nest_asyncio.apply()

from dikaai.database import DikaDB
from dikaai.model.tokenizer import DikaTokenizer
from dikaai.model.model import DikaModel
from dikaai.model.trainer import DikaTrainer
from bot import DikaBot
from webscraper import DikaWebScraper
from dikaai.config import (
    API_ID, API_HASH, PHONE,
    UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN,
    USE_REDIS, CONTEXT_LEN
)

print("    All imports OK!")

# Report compute device (T4 GPU if runtime is set to GPU)
try:
    import torch as _torch
    _cuda = _torch.cuda.is_available()
    print("    [GPU] CUDA available: " + str(_cuda) + " | device: " + ("cuda" if _cuda else "cpu"))
    if _cuda:
        print("    [GPU] Using: " + _torch.cuda.get_device_name(0))
except Exception as _e:
    print("    [GPU] torch not available: " + str(_e))

# ============================================================
# LIVE STATS DISPLAY
# ============================================================
from IPython.display import display, HTML, clear_output

_live_stats = {
    'phase': 'init',
    'messages': 0,
    'step': 0,
    'vocab': 0,
    'loss': 0,
    'episodes': 0,
    'facts': 0,
    'redis_syncs': 0,
    'replies': 0,
    'web_new': 0,
    'telegram_connected': False,
    'threads': {},
}

def _update_live_stats():
    try:
        s = db.get_stats()
        _live_stats['messages'] = s.get('total', 0)
    except Exception:
        pass
    try:
        _live_stats['step'] = model.step
        _live_stats['vocab'] = getattr(model, 'vocab_size', 0) or getattr(tokenizer, 'vocab_size', 0)
    except Exception:
        pass
    try:
        _live_stats['loss'] = getattr(model, 'last_loss', 0)
    except Exception:
        pass
    try:
        _live_stats['replies'] = bot.stats.get('replies', 0)
        _live_stats['web_new'] = bot.stats.get('new', 0)
    except Exception:
        pass

def _render_stats_html():
    _update_live_stats()
    elapsed = time.time() - start_time
    remaining = max(0, (max_runtime - elapsed) / 3600)
    elapsed_h = elapsed / 3600

    phase = _live_stats['phase']
    phase_colors = {
        'init': '#94a3b8', 'web_scrape': '#f59e0b',
        'training': '#3b82f6', 'benchmark': '#a855f7',
        'telegram': '#10b981', 'done': '#6b7280',
    }
    phase_labels = {
        'init': 'Initializing', 'web_scrape': 'Web Scraping (180+ sources)',
        'training': 'Training Model', 'benchmark': 'Benchmarking',
        'telegram': 'Telegram Live', 'done': 'Completed',
    }
    pc = phase_colors.get(phase, '#94a3b8')
    pl = phase_labels.get(phase, phase)

    threads = _live_stats.get('threads', {})

    def dot(name):
        st = threads.get(name, 'off')
        c = '#10b981' if st == 'on' else '#6b7280'
        return '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + c + ';margin-right:4px"></span>' + name

    msgs = str(_live_stats['messages'])
    step = str(_live_stats['step'])
    vocab = str(_live_stats['vocab'])
    replies = str(_live_stats['replies'])
    web_new = str(_live_stats['web_new'])
    syncs = str(_live_stats['redis_syncs'])
    rem = str(round(remaining, 1))
    elh = str(round(elapsed_h, 1))

    h = '<div style="font-family:monospace;background:#0c0c14;color:#e0e0e8;border:2px solid #2d2d40;border-radius:16px;padding:20px;margin:8px 0;max-width:600px">'
    h += '<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">'
    h += '<div style="width:12px;height:12px;border-radius:50%;background:' + pc + ';box-shadow:0 0 8px ' + pc + ';animation:pulse 2s infinite"></div>'
    h += '<span style="font-size:16px;font-weight:800;color:#a78bfa">DikaAI Live v5</span>'
    h += '<span style="font-size:11px;color:' + pc + ';font-weight:600;background:' + pc + '22;padding:2px 8px;border-radius:6px;border:1px solid ' + pc + '44">' + pl + '</span>'
    h += '<span style="margin-left:auto;font-size:11px;color:#606078">' + elh + 'h / 12h</span>'
    h += '</div>'

    h += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:14px">'
    for label, val, color in [('Messages', msgs, '#10b981'), ('Model Step', step, '#3b82f6'), ('Vocab', vocab, '#a855f7')]:
        h += '<div style="background:#16161f;border:2px solid #2d2d40;border-radius:10px;padding:12px;text-align:center">'
        h += '<div style="font-size:10px;color:#606078;text-transform:uppercase;letter-spacing:0.5px">' + label + '</div>'
        h += '<div style="font-size:22px;font-weight:800;color:' + color + '">' + val + '</div>'
        h += '</div>'
    h += '</div>'

    h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px">'
    h += '<div style="background:#16161f;border:2px solid #2d2d40;border-radius:10px;padding:10px">'
    h += '<div style="font-size:10px;color:#606078;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">Stats</div>'
    h += '<div style="font-size:12px;color:#94a3b8;line-height:1.8">'
    h += 'Replies: <span style="color:#10b981;font-weight:700">' + replies + '</span><br>'
    h += 'Web New: <span style="color:#f59e0b;font-weight:700">' + web_new + '</span><br>'
    h += 'Redis Syncs: <span style="color:#06b6d4;font-weight:700">' + syncs + '</span>'
    h += '</div></div>'
    h += '<div style="background:#16161f;border:2px solid #2d2d40;border-radius:10px;padding:10px">'
    h += '<div style="font-size:10px;color:#606078;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">Threads</div>'
    h += '<div style="font-size:12px;color:#94a3b8;line-height:1.8">'
    h += dot('redis') + '<br>' + dot('training') + '<br>' + dot('web_scrape') + '<br>' + dot('telegram')
    h += '</div></div></div>'

    h += '<div style="display:flex;justify-content:space-between;align-items:center;padding-top:10px;border-top:2px solid #2d2d40">'
    h += '<span style="font-size:11px;color:#606078">Remaining: <span style="color:#f59e0b;font-weight:700">' + rem + 'h</span></span>'
    h += '<a href="https://dikaai.vercel.app" target="_blank" style="font-size:11px;color:#a78bfa;text-decoration:none">Dashboard</a>'
    h += '</div></div>'
    h += '<style>@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }</style>'
    return h

def _stats_display_thread():
    time.sleep(3)
    while running:
        try:
            html = _render_stats_html()
            clear_output(wait=True)
            display(HTML(html))
        except Exception:
            pass
        time.sleep(5)
    try:
        _live_stats['phase'] = 'done'
        _live_stats['threads'] = {}
        html = _render_stats_html()
        clear_output(wait=True)
        display(HTML(html))
    except Exception:
        pass

_stats_t = threading.Thread(target=_stats_display_thread, daemon=True)
_stats_t.start()
print("  Live stats display started!")

# ============================================================
# STEP 4: BANNER
# ============================================================
print("\n" + "=" * 60)
print("  DikaAI v5 - 180+ Sources PARALLEL")
print("=" * 60)
print("  Auto-stop : 12 jam")
print("  Flow      : Scrape(180+) -> Train(500) -> Bench -> Telegram")
print("  Dashboard : https://dikaai.vercel.app")
print("=" * 60)
print("  Features ALL otomatis:")
print("    [1] Web Scrape 180+ sources PARALLEL (8 threads)")
print("        A: NusaCrowd, HF Indonesian, Wikipedia ID")
print("        B: Kaskus, Detik, Kompas, Liputan6, CNN, DuckDuckGo")
print("        C: Python/JS/Rust/Go/Kotlin/C++ docs, SO, GitHub")
print("        D: Git/Docker/K8s/Nginx/Linux/Redis docs")
print("        E: Android/Termux docs")
print("        F: PyTorch/TensorFlow/HuggingFace ML docs")
print("        G: The Stack, CodeSearchNet, StarCoder info")
print("        H: Conversational Indonesian Q&A dataset")
print("    [2] Training      (500 epochs + continuous background)")
print("    [3] Benchmark     (coding capability test)")
print("    [4] Telegram Bot  (auto-reply + scrape all chats)")
print("    [5] Redis Sync    (dashboard Vercel auto-update 30s)")
print("    [6] Engine Sync   (episodes, facts, traces)")
print("=" * 60)

if not API_ID or not API_HASH:
    print("\nERROR: Telegram API belum dikonfigurasi!")
    raise SystemExit(1)

if not USE_REDIS:
    print("\nWARNING: Redis belum dikonfigurasi!")
    print("Dashboard Vercel TIDAK akan update.")

# ============================================================
# STEP 5: INIT
# ============================================================
print("\n[5] Initializing components...")

db = DikaDB()
trainer = DikaTrainer(db)
model = trainer.model
tokenizer = trainer.tokenizer
bot = DikaBot(db, model=model, tokenizer=tokenizer)

running = True
start_time = time.time()
max_runtime = 12 * 3600

def stop_handler(sig, frame):
    global running
    print("\n[STOP] Stopping all threads...")
    running = False

try:
    signal.signal(signal.SIGINT, stop_handler)
except ValueError:
    pass

print("    All components initialized!")

# ============================================================
# BACKGROUND THREAD: Redis Sync (every 30s for real-time dashboard)
# ============================================================
def redis_sync_thread():
    if not USE_REDIS:
        print("  [REDIS] Skipped (not configured)")
        return
    try:
        from sync_to_redis import (
            UpstashRedis, sync_messages, sync_model,
            sync_vocab, sync_training_history, sync_engine_state
        )
        r = UpstashRedis(UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN)
        r.ping()
        print("  [REDIS] Connected!")
        n = 0
        while running:
            time.sleep(30)
            if not running:
                break
            try:
                sync_messages(r, limit=200)
                sync_model(r)
                sync_vocab(r)
                sync_training_history(r)
                sync_engine_state(r)
                n += 1
                _live_stats['redis_syncs'] = n
                if n % 5 == 0:
                    stats = db.get_stats()
                    print("  [REDIS] Sync #" + str(n) + " | " + str(stats['total']) + " msgs -> Vercel")
            except Exception as e:
                print("  [REDIS] Sync error: " + str(e))
    except Exception as e:
        print("  [REDIS] Connection failed: " + str(e))

# ============================================================
# BACKGROUND THREAD: Continuous Training (max speed)
# ============================================================
def training_thread():
    print("  [TRAIN] Max-speed training started...")
    ep = 0
    while running:
        try:
            ep += 1
            loss, count = trainer.train_one_epoch()
            if count > 0:
                _live_stats['loss'] = loss
            if count > 0 and ep % 20 == 0:
                print("  [TRAIN] Ep " + str(ep) + " | loss=" + str(round(loss, 4)) + " | step=" + str(model.step))
            if model.step % 50 == 0:
                model.save()
                tokenizer.save()
            # Mark messages as processed for dashboard (every 100 epochs)
            if ep % 100 == 0:
                try:
                    db.mark_all_processed()
                except Exception:
                    pass
        except Exception as e:
            print("  [TRAIN] Error: " + str(e))
            time.sleep(1)

# ============================================================
# BACKGROUND THREAD: Periodic Web Scraping (every 1h, ALL 180+ sources)
# ============================================================
def web_scrape_thread():
    while running:
        for _ in range(3600):
            if not running:
                return
            time.sleep(1)
        if not running:
            return
        try:
            print("  [WEB] Periodic scrape (180+ sources, parallel)...")
            scraper = DikaWebScraper(db)
            scraper.scrape_all()
            print("  [WEB] Periodic done! New: " + str(scraper.stats['new']))
        except Exception as e:
            print("  [WEB] Periodic error: " + str(e))

# ============================================================
# PHASE 1: WEB SCRAPE (ALL 180+ SOURCES PARALLEL)
# ============================================================
_live_stats['phase'] = 'web_scrape'
print("\n" + "=" * 60)
print("  PHASE 1: Web Scrape (180+ sources, PARALLEL)")
print("=" * 60)

# Start Redis sync immediately
redis_t = threading.Thread(target=redis_sync_thread, daemon=True)
redis_t.start()
_live_stats['threads']['redis'] = 'on'
print("  Redis sync thread started!")

# Web scrape ALL 180+ sources in parallel.
# Be robust to the clone having an OLD DikaWebScraper (no max_workers kwarg).
import inspect
_scraper_kwargs = {}
try:
    _params = inspect.signature(DikaWebScraper.__init__).parameters
    if 'max_workers' in _params:
        _scraper_kwargs['max_workers'] = 8
except Exception:
    pass
try:
    scraper = DikaWebScraper(db, **_scraper_kwargs)
    scraper.scrape_all()
except Exception as e:
    print("  [WEB] Error: " + str(e))

stats = db.get_stats()
print("\n  Web scrape done: " + str(stats['total']) + " total messages")

# Start background training IMMEDIATELY
train_t = threading.Thread(target=training_thread, daemon=True)
train_t.start()
_live_stats['threads']['training'] = 'on'
print("  Background training started!")

# ============================================================
# PHASE 2: TRAINING (500 epochs max speed)
# ============================================================
_live_stats['phase'] = 'training'
print("\n" + "=" * 60)
print("  PHASE 2: Training dari Web Data (500 epochs)")
print("=" * 60)

# Always build vocab from whatever data exists (web + any prior DB),
# so a web-scrape failure can never silently skip training.
try:
    trainer.build_vocab()
    print("  Vocab: " + str(tokenizer.vocab_size) + " tokens")
except Exception as e:
    print("  [TRAIN] Vocab build skipped: " + str(e))

if stats['total'] > 0:
    print("  Training 500 epochs (max speed)...")
    for ep in range(1, 501):
        if not running:
            break
        try:
            loss, count = trainer.train_one_epoch()
            if count > 0:
                _live_stats['loss'] = loss
                if ep % 50 == 0 or ep == 1 or ep == 500:
                    print("  [TRAIN] Ep " + str(ep) + "/500 | loss=" + str(round(loss, 4)) + " | step=" + str(model.step))
                if ep % 25 == 0:
                    model.save()
                    tokenizer.save()
        except Exception as e:
            print("  [TRAIN] Error: " + str(e))

    model.save()
    tokenizer.save()
    # Mark all messages as processed for dashboard
    try:
        db.mark_all_processed()
    except Exception:
        pass
    print("  Training done! Model step: " + str(model.step))
else:
    print("  No web data yet -> background thread will train on Telegram data")

# ============================================================
# PHASE 3: BENCHMARK
# ============================================================
_live_stats['phase'] = 'benchmark'
print("\n" + "=" * 60)
print("  PHASE 3: Benchmark")
print("=" * 60)

try:
    from dikaai.benchmark import BenchmarkRunner, Evaluator, BenchmarkHistory
    runner = BenchmarkRunner(workspace=os.getcwd())
    results = runner.run(max_tasks=10)
    report = runner.report(results)
    Evaluator().print_report(report)

    history = BenchmarkHistory()
    history.record(report, model_step=model.step)
    print("  Saved to benchmark history")
except Exception as e:
    print("  Benchmark skipped: " + str(e))

# ============================================================
# PHASE 4: TELEGRAM LOOP (all features running)
# ============================================================
_live_stats['phase'] = 'telegram'
print("\n" + "=" * 60)
print("  PHASE 4: Telegram Loop (all features running)")
print("  Auto-reply + scrape + training + Redis sync + web scrape")
print("  Auto-stop: 12 jam")
print("=" * 60)

web_t = threading.Thread(target=web_scrape_thread, daemon=True)
web_t.start()
_live_stats['threads']['web_scrape'] = 'on'
print("  Web scrape thread started (every 1h, 180+ sources)")

async def telegram_loop():
    global running

    if not await bot.connect():
        print("Telegram connect failed!")
        return

    print("Telegram connected!")
    _live_stats['telegram_connected'] = True
    _live_stats['threads']['telegram'] = 'on'

    # Save session to Google Drive
    if _gdrive_mounted:
        try:
            src = os.path.join('/content/dikaai', SESSION_FILE)
            dst = os.path.join(SESSION_DRIVE_PATH, SESSION_FILE)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print("  Session saved to Google Drive!")
        except Exception as e:
            print("  Session save failed: " + str(e))

    print("\nScraping ALL Telegram chats...")
    await bot.scrape_all()

    bot.setup_auto_reply()
    print("Auto-reply listener active!")

    n = 0
    while running:
        try:
            rem = (max_runtime - (time.time() - start_time)) / 3600
            if rem <= 0:
                print("\n12 hour limit reached!")
                running = False
                break

            stats = db.get_stats()
            print("\n[STATUS] " + str(round(rem, 1)) + "h left | " + str(stats['total']) + " msgs | step " + str(model.step) + " | " + str(tokenizer.vocab_size) + " vocab")

            await asyncio.sleep(6 * 3600)
            if not running:
                break

            n += 1
            print("\nRe-scrape #" + str(n) + "...")
            await bot.scrape_recent(hours=6)
            trainer.build_vocab()

        except asyncio.CancelledError:
            break
        except Exception as e:
            print("  Error: " + str(e))
            await asyncio.sleep(300)

try:
    asyncio.run(telegram_loop())
except KeyboardInterrupt:
    print("\nInterrupted!")
except RuntimeError as e:
    print("  Async error: " + str(e))
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(telegram_loop())
    except Exception:
        pass
finally:
    running = False
    model.save()
    tokenizer.save()

    s = db.get_stats()
    runtime_hours = (time.time() - start_time) / 3600

    print("\n" + "=" * 60)
    print("  FINAL STATS")
    print("=" * 60)
    print("  Messages : " + str(s['total']))
    print("  Model    : step " + str(model.step))
    print("  Vocab    : " + str(tokenizer.vocab_size) + " tokens")
    print("  Runtime  : " + str(round(runtime_hours, 1)) + " jam")
    print("  Dashboard: https://dikaai.vercel.app")
    print("=" * 60)
    print("  All features completed!")
    print("=" * 60)
