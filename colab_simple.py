#!/usr/bin/env python3
"""
DikaAI - Google Colab Runner (v4 - BULLETPROOF)
================================================
Copy-paste SEMUA ke SATU cell di Colab.
Ganti config, lalu Run! Semua fitur jalan otomatis.

Features (ALL automatic):
  1. Web Scrape (Wikipedia, StackOverflow, GitHub, Indonesian Corpus)
  2. Training (200 epochs from web data)
  3. Benchmark (coding capability test)
  4. Telegram Bot (auto-reply + scrape all chats)
  5. Redis Sync (Vercel dashboard auto-update)
  6. Continuous Training (background)
  7. Periodic Web Scraping (every 2h)

Dashboard: https://dikaai.vercel.app
================================================
"""

# ============================================================
# STEP 0: FIX WORKING DIRECTORY (CRITICAL FOR COLAB!)
# ============================================================
import os
import sys
import shutil
import importlib

# Always start from /content to avoid getcwd errors
os.chdir('/content')
print(f"[0] CWD: {os.getcwd()}")

# ============================================================
# STEP 1: INSTALL + CLONE (CLEAN)
# ============================================================
print("\n[1] Installing dependencies + cloning repo...")

# Install packages
os.system('pip install telethon aiohttp nest_asyncio -q')

# Remove old clone (prevents stale cache issues)
if os.path.exists('/content/dikaai'):
    print("    Removing old clone...")
    shutil.rmtree('/content/dikaai', ignore_errors=True)

# Clone fresh (shallow for speed)
exit_code = os.system('git clone --depth 1 https://github.com/dikaofc/dikaai.git /content/dikaai')
if exit_code != 0:
    print("ERROR: git clone failed! Check internet.")
    raise SystemExit(1)

# Verify clone
if not os.path.exists('/content/dikaai/main.py'):
    print("ERROR: Clone incomplete!")
    raise SystemExit(1)

# cd into project
os.chdir('/content/dikaai')
sys.path.insert(0, '/content/dikaai')
print(f"    Project CWD: {os.getcwd()}")

# Clear ALL Python bytecode cache
for root, dirs, files in os.walk('/content/dikaai'):
    for d in dirs:
        if d == '__pycache__':
            shutil.rmtree(os.path.join(root, d), ignore_errors=True)

# Invalidate Python import cache
importlib.invalidate_caches()

# Remove any stale .pyc files
for root, dirs, files in os.walk('/content/dikaai'):
    for f in files:
        if f.endswith('.pyc'):
            os.remove(os.path.join(root, f))

print("    Cache cleared!")

# ============================================================
# STEP 2: CONFIG (GANTI INI SEBELUM RUN!)
# ============================================================
print("\n[2] Writing config...")

# =====================================================
# GANTI BAGIAN INI DENGAN DATA KAMU!
# =====================================================
TELEGRAM_API_ID = 12345678                     # dari https://my.telegram.org
TELEGRAM_API_HASH = "abc123def456789"          # dari https://my.telegram.org
TELEGRAM_PHONE = "+6281234567890"              # nomor HP Telegram kamu

# Daftar gratis: https://upstash.com → Create Database → Copy URL + Token
UPSTASH_REDIS_URL = "https://xxx.upstash.io"       # ganti!
UPSTASH_REDIS_TOKEN = "AXxxxxxx=="                  # ganti!
# =====================================================

# Write config.env
config_content = f"""TELEGRAM_API_ID={TELEGRAM_API_ID}
TELEGRAM_API_HASH={TELEGRAM_API_HASH}
TELEGRAM_PHONE={TELEGRAM_PHONE}
UPSTASH_REDIS_REST_URL={UPSTASH_REDIS_URL}
UPSTASH_REDIS_REST_TOKEN={UPSTASH_REDIS_TOKEN}
"""

config_path = os.path.join('/content/dikaai', 'config.env')
with open(config_path, 'w') as f:
    f.write(config_content)

print(f"    Config saved: {config_path}")
print(f"    Telegram: {TELEGRAM_PHONE}")
print(f"    Redis: {UPSTASH_REDIS_URL[:30]}...")

# ============================================================
# STEP 3: IMPORTS (after config.env is written!)
# ============================================================
print("\n[3] Importing DikaAI modules...")

import time
import signal
import threading
import asyncio
import json

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

# ============================================================
# STEP 4: BANNER
# ============================================================
print("\n" + "=" * 60)
print("  DikaAI v3.2 - FULL AUTO Google Colab Runner")
print("=" * 60)
print("  Auto-stop : 12 jam")
print("  Flow      : Web Scrape -> Train -> Benchmark -> Telegram")
print("  Dashboard : https://dikaai.vercel.app")
print("=" * 60)
print("  Features ALL otomatis:")
print("    [1] Web Scraping  (Wikipedia, SO, GitHub, Corpus, etc)")
print("    [2] Training      (200 epochs + continuous background)")
print("    [3] Benchmark     (coding capability test)")
print("    [4] Telegram Bot  (auto-reply + scrape all chats)")
print("    [5] Redis Sync    (dashboard Vercel auto-update)")
print("    [6] Engine Sync   (episodes, facts, traces)")
print("=" * 60)

if not API_ID or not API_HASH:
    print("\nERROR: Telegram API belum dikonfigurasi!")
    print("Ganti TELEGRAM_API_ID dan TELEGRAM_API_HASH di bagian STEP 2!")
    raise SystemExit(1)

if not USE_REDIS:
    print("\nWARNING: Redis belum dikonfigurasi!")
    print("Dashboard Vercel TIDAK akan update.")
    print("Isi UPSTASH_REDIS_URL dan UPSTASH_REDIS_TOKEN dulu!")

# ============================================================
# STEP 5: INIT
# ============================================================
print("\n[5] Initializing components...")

db = DikaDB()
tokenizer = DikaTokenizer()
model = DikaModel()
trainer = DikaTrainer(db)
bot = DikaBot(db, model=model, tokenizer=tokenizer)

running = True
start_time = time.time()
max_runtime = 12 * 3600  # 12 hours

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
# BACKGROUND THREAD: Redis Sync (every 60s)
# ============================================================
def redis_sync_thread():
    """Sync SQLite -> Redis for Vercel dashboard."""
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
            time.sleep(60)
            if not running:
                break
            try:
                sync_messages(r, limit=200)
                sync_model(r)
                sync_vocab(r)
                sync_training_history(r)
                sync_engine_state(r)
                n += 1
                if n % 5 == 0:
                    stats = db.get_stats()
                    print(f"  [REDIS] Sync #{n} | {stats['total']} msgs -> Vercel")
            except Exception as e:
                print(f"  [REDIS] Sync error: {e}")
    except Exception as e:
        print(f"  [REDIS] Connection failed: {e}")

# ============================================================
# BACKGROUND THREAD: Continuous Training
# ============================================================
def training_thread():
    """Continuous model training in background."""
    print("  [TRAIN] Continuous training started...")
    ep = 0
    while running:
        try:
            ep += 1
            loss, count = trainer.train_one_epoch()
            if count > 0 and ep % 50 == 0:
                print(f"  [TRAIN] Ep {ep} | loss={loss:.4f} | step={model.step}")
            if model.step % 100 == 0:
                model.save()
                tokenizer.save()
            time.sleep(5)
        except Exception as e:
            print(f"  [TRAIN] Error: {e}")
            time.sleep(10)

# ============================================================
# BACKGROUND THREAD: Periodic Web Scraping (every 2h)
# ============================================================
def web_scrape_thread():
    """Periodic web scraping every 2 hours."""
    while running:
        # Wait 2 hours first
        for _ in range(7200):
            if not running:
                return
            time.sleep(1)
        if not running:
            return
        try:
            print("  [WEB] Periodic scrape starting...")
            scraper = DikaWebScraper(db)
            scraper.scrape_all()
            print("  [WEB] Periodic scrape done!")
        except Exception as e:
            print(f"  [WEB] Periodic error: {e}")

# ============================================================
# PHASE 1: WEB SCRAPE (BLOCKING - priority!)
# ============================================================
print("\n" + "=" * 60)
print("  PHASE 1: Web Scrape (from internet)")
print("=" * 60)

# Start Redis sync immediately (so dashboard updates ASAP)
redis_t = threading.Thread(target=redis_sync_thread, daemon=True)
redis_t.start()
print("  Redis sync thread started!")

# Do web scrape FIRST (blocking - get data before training)
try:
    scraper = DikaWebScraper(db)
    scraper.scrape_all()
except Exception as e:
    print(f"  [WEB] Error: {e}")

stats = db.get_stats()
print(f"\n  Web scrape result: {stats['total']} total messages")

# ============================================================
# PHASE 2: TRAINING (from web data)
# ============================================================
print("\n" + "=" * 60)
print("  PHASE 2: Training dari Web Data")
print("=" * 60)

if stats['total'] > 0:
    trainer.build_vocab()
    print(f"  Vocab: {tokenizer.vocab_size} tokens")

    print("  Training 200 epochs...")
    for ep in range(1, 201):
        if not running:
            break
        try:
            loss, count = trainer.train_one_epoch()
            if count > 0:
                if ep % 20 == 0 or ep == 1 or ep == 200:
                    print(f"  [TRAIN] Ep {ep:3d}/200 | loss={loss:.4f} | total={model.step}")
                if ep % 10 == 0:
                    model.save()
                    tokenizer.save()
            time.sleep(3)
        except Exception as e:
            print(f"  [TRAIN] Error: {e}")
            time.sleep(5)

    model.save()
    tokenizer.save()
    print(f"  Training done! Model step: {model.step}")
else:
    print("  No web data, skipping training")

# ============================================================
# PHASE 3: BENCHMARK (quick test)
# ============================================================
print("\n" + "=" * 60)
print("  PHASE 3: Benchmark")
print("=" * 60)

try:
    from dikaai.benchmark import BenchmarkRunner, Evaluator, BenchmarkHistory
    runner = BenchmarkRunner(workspace=os.getcwd())
    results = runner.run(max_tasks=10)
    report = runner.report(results)
    Evaluator().print_report(report)

    # Save to history
    history = BenchmarkHistory()
    history.record(report, model_step=model.step)
    print("  Saved to benchmark history")
except Exception as e:
    print(f"  Benchmark skipped: {e}")

# ============================================================
# PHASE 4: TELEGRAM LOOP (blocking until 12h)
# ============================================================
print("\n" + "=" * 60)
print("  PHASE 4: Telegram Loop (all features running)")
print("  Auto-reply + scrape + training + Redis sync")
print("  Auto-stop: 12 jam")
print("=" * 60)

# Start background threads
train_t = threading.Thread(target=training_thread, daemon=True)
train_t.start()
print("  Training thread started (background)")

web_t = threading.Thread(target=web_scrape_thread, daemon=True)
web_t.start()
print("  Web scrape thread started (every 2h)")

# Telegram loop (main blocking loop)
async def telegram_loop():
    global running

    if not await bot.connect():
        print("Telegram connect failed!")
        print("Make sure TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE are correct!")
        return

    print("Telegram connected!")

    # Initial scrape of ALL chats
    print("\nScraping ALL Telegram chats...")
    await bot.scrape_all()

    # Setup auto-reply listener
    bot.setup_auto_reply()
    print("Auto-reply listener active!")

    # Periodic re-scrape every 6 hours
    n = 0
    while running:
        try:
            rem = (max_runtime - (time.time() - start_time)) / 3600
            if rem <= 0:
                print("\n12 hour limit reached!")
                running = False
                break

            stats = db.get_stats()
            print(f"\n[STATUS] {rem:.1f}h left | {stats['total']} msgs | step {model.step} | {model.vocab_size} vocab")

            # Sleep 6 hours then re-scrape
            await asyncio.sleep(6 * 3600)
            if not running:
                break

            n += 1
            print(f"\nRe-scrape #{n}...")
            await bot.scrape_recent(hours=6)

            # Rebuild vocab with new data
            trainer.build_vocab()

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"  Error: {e}")
            await asyncio.sleep(300)

# Run telegram loop
try:
    asyncio.run(telegram_loop())
except KeyboardInterrupt:
    print("\nInterrupted!")
except RuntimeError as e:
    # nest_asyncio handles this, but just in case
    print(f"  Async error: {e}")
    # Try alternative approach
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(telegram_loop())
    except Exception:
        pass
finally:
    running = False

    # Save everything
    model.save()
    tokenizer.save()

    # Final stats
    s = db.get_stats()
    runtime_hours = (time.time() - start_time) / 3600

    print("\n" + "=" * 60)
    print("  FINAL STATS")
    print("=" * 60)
    print(f"  Messages : {s['total']}")
    print(f"  Model    : step {model.step}")
    print(f"  Vocab    : {tokenizer.vocab_size} tokens")
    print(f"  Runtime  : {runtime_hours:.1f} jam")
    print(f"  Dashboard: https://dikaai.vercel.app")
    print("=" * 60)
    print("  All features completed!")
    print("=" * 60)
