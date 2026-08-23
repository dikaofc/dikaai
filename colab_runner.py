#!/usr/bin/env python3
"""
DikaAi - Google Colab Runner
Jalan di Colab 12 jam, auto-sync ke Redis, dashboard di Vercel.

Usage di Colab:
    1. Copy cell 1 (install)
    2. Copy cell 2 (config)
    3. Copy cell 3 (run)
"""

# ============================================================
# CELL 1: Install Dependencies (run sekali aja)
# ============================================================
"""
!pip install telethon aiohttp -q
!git clone https://github.com/dikaofc/dikaai.git /content/dikaai
%cd /content/dikaai
"""

# ============================================================
# CELL 2: Setup Config (isi dulu sebelum run)
# ============================================================
"""
# ============================================
# ISI DATA LU DISINI!
# ============================================

# Telegram API (dari my.telegram.org)
TELEGRAM_API_ID = 12345678        # Ganti!
TELEGRAM_API_HASH = "abc123def456" # Ganti!
TELEGRAM_PHONE = "+628123456789"   # Ganti!

# Upstash Redis (dari upstash.com)
UPSTASH_REDIS_URL = "https://xxx.upstash.io"  # Ganti!
UPSTASH_REDIS_TOKEN = "AXxx..."               # Ganti!

# Simpan ke config.env
with open('config.env', 'w') as f:
    f.write(f'''TELEGRAM_API_ID={TELEGRAM_API_ID}
TELEGRAM_API_HASH={TELEGRAM_API_HASH}
TELEGRAM_PHONE={TELEGRAM_PHONE}
UPSTASH_REDIS_REST_URL={UPSTASH_REDIS_URL}
UPSTASH_REDIS_REST_TOKEN={UPSTASH_REDIS_TOKEN}
''')

print("✅ Config saved!")
print(f"📱 Telegram: {TELEGRAM_PHONE}")
print(f"🔴 Redis: {UPSTASH_REDIS_URL[:30]}...")
"""

# ============================================================
# CELL 3: Run DikaAi (auto 12 jam)
# ============================================================
"""
import sys
import os
import time
import signal
import threading
import asyncio
from datetime import datetime, timedelta

# Setup path
sys.path.insert(0, '/content/dikaai')
os.chdir('/content/dikaai')

# Import modules
from database import DikaDB
from tokenizer import DikaTokenizer
from model import DikaModel
from trainer import DikaTrainer
from bot import DikaBot
from config import API_ID, API_HASH, PHONE
from sync_to_redis import UpstashRedis, sync_messages, sync_model, sync_vocab
from config import UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN, USE_REDIS

# ============================================================
# DISPLAY BANNER
# ============================================================
print("=" * 60)
print("  🧠 DikaAi - Google Colab Runner")
print("  ⏱️  Runtime: 12 jam")
print("  🔄 Auto-sync ke Redis setiap 60 detik")
print("  📊 Dashboard: https://dikaai.vercel.app")
print("=" * 60)

# ============================================================
# CHECK CONFIG
# ============================================================
if not API_ID or not API_HASH:
    print("❌ ERROR: Telegram API belum dikonfigurasi!")
    print("Jalankan Cell 2 dulu!")
    raise SystemExit(1)

print(f"📱 Telegram: {PHONE}")
print(f"🔴 Redis: {'✅ Connected' if USE_REDIS else '❌ Not configured'}")

# ============================================================
# INITIALIZE COMPONENTS
# ============================================================
print("\n[1/5] Initializing components...")

db = DikaDB()
tokenizer = DikaTokenizer()
model = DikaModel()
trainer = DikaTrainer(db)
bot = DikaBot(db, model=model, tokenizer=tokenizer)

# Load existing model/vocab
if model.load():
    print(f"  ✅ Model loaded (step {model.step})")
else:
    print("  ⚠️ No saved model, starting fresh")

if tokenizer.load():
    print(f"  ✅ Vocab loaded ({tokenizer.vocab_size} tokens)")
else:
    print("  ⚠️ No vocab, will build from data")

# ============================================================
# SYNC TO REDIS FUNCTION
# ============================================================
def redis_sync_loop():
    """Background thread: sync SQLite → Redis every 60s"""
    if not USE_REDIS:
        print("  ⚠️ Redis not configured, skipping sync")
        return
    
    try:
        r = UpstashRedis(UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN)
        r.ping()
        print("  ✅ Redis connected!")
    except Exception as e:
        print(f"  ❌ Redis connection failed: {e}")
        return
    
    sync_count = 0
    while running:
        try:
            time.sleep(60)
            if not running:
                break
            
            sync_messages(r, limit=200)
            sync_model(r)
            sync_vocab(r)
            sync_count += 1
            
            if sync_count % 5 == 0:  # Log setiap 5 menit
                stats = db.get_stats()
                print(f"  [REDIS] ✅ Sync #{sync_count} | {stats['total']} messages")
                
        except Exception as e:
            print(f"  [REDIS] ⚠️ Sync error: {e}")
            time.sleep(30)

# ============================================================
# TRAINING LOOP
# ============================================================
def train_loop():
    """Background thread: continuous training"""
    print("  🧠 Training started...")
    
    # Build vocab first
    stats = db.get_stats()
    if stats['total'] > 0:
        trainer.build_vocab()
        print(f"  ✅ Vocab ready: {tokenizer.vocab_size} tokens")
    
    epoch = 0
    while running:
        try:
            epoch += 1
            loss, count = trainer.train_one_epoch()
            
            if count > 0:
                print(f"  [Ep {epoch:3d}] loss={loss:.4f} steps={count} total={model.step}")
                
                # Save every 50 steps
                if model.step % 50 == 0:
                    model.save()
                    tokenizer.save()
            
            time.sleep(5)  # Training interval
            
        except Exception as e:
            print(f"  [TRAIN] Error: {e}")
            time.sleep(10)

# ============================================================
# MAIN RUNNER
# ============================================================
running = True
start_time = time.time()
max_runtime = 12 * 3600  # 12 jam

def signal_handler(sig, frame):
    global running
    print("\n⏹️ Stopping DikaAi...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

# Start Redis sync thread
redis_thread = threading.Thread(target=redis_sync_loop, daemon=True)
redis_thread.start()

# Start training thread
train_thread = threading.Thread(target=train_loop, daemon=True)
train_thread.start()

# ============================================================
# TELEGRAM SCRAPE + BOT
# ============================================================
async def run_telegram():
    """Run Telegram scraper + bot"""
    global running
    
    print("\n[2/5] Connecting to Telegram...")
    
    if not await bot.connect():
        print("❌ Failed to connect to Telegram!")
        print("Continuing with training only...")
        return
    
    print("✅ Connected to Telegram!")
    
    # Phase 1: Build vocab
    print("\n[3/5] Building vocab...")
    stats = db.get_stats()
    if stats['total'] > 0:
        trainer.build_vocab()
        print(f"  ✅ Vocab ready: {tokenizer.vocab_size} tokens")
    
    # Phase 2: Scrape all chats
    print("\n[4/5] Scraping Telegram chats...")
    await bot.scrape_all()
    
    # Phase 3: Rebuild vocab after scrape
    print("\n[5/5] Rebuilding vocab...")
    trainer.build_vocab()
    print(f"  ✅ Vocab updated: {tokenizer.vocab_size} tokens")
    
    # Phase 4: Setup auto-reply
    print("\n[6/6] Starting auto-reply...")
    bot.setup_auto_reply()
    
    # Phase 5: Periodic re-scrape (every 6 jam)
    scrape_count = 0
    while running:
        try:
            # Check runtime
            elapsed = time.time() - start_time
            remaining = max_runtime - elapsed
            
            if remaining <= 0:
                print(f"\n⏱️ 12 jam reached! Stopping...")
                running = False
                break
            
            hours_remaining = remaining / 3600
            print(f"\n⏰ {hours_remaining:.1f} jam tersisa | {stats['total']} messages")
            
            # Wait 6 jam
            await asyncio.sleep(6 * 3600)
            
            if not running:
                break
            
            # Re-scrape
            scrape_count += 1
            print(f"\n🔄 Re-scrape #{scrape_count}...")
            await bot.scrape_recent(hours=6)
            
            # Rebuild vocab
            trainer.build_vocab()
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"  [SCRAPE] Error: {e}")
            await asyncio.sleep(300)

# ============================================================
# RUN
# ============================================================
print("\n" + "=" * 60)
print("  🚀 DikaAi Started!")
print("  ⏱️  Auto-stop: 12 jam")
print("  📊 Dashboard: https://dikaai.vercel.app")
print("  🔄 Sync: Redis setiap 60 detik")
print("=" * 60)

try:
    asyncio.run(run_telegram())
except KeyboardInterrupt:
    print("\n⏹️ Stopped by user")
finally:
    running = False
    model.save()
    tokenizer.save()
    
    # Final stats
    stats = db.get_stats()
    print("\n" + "=" * 60)
    print("  📊 Final Stats")
    print(f"  Messages: {stats['total']}")
    print(f"  Processed: {stats['processed']}")
    print(f"  Unique chats: {stats['unique_chats']}")
    print(f"  Model steps: {model.step}")
    print(f"  Runtime: {(time.time() - start_time) / 3600:.1f} jam")
    print("=" * 60)
    print("  ✅ Data saved! Check dashboard di Vercel.")
    print("=" * 60)
"""

# ============================================================
# QUICK COPY-PASTE VERSION (Satu Cell Aja)
# ============================================================
"""
# ============================================
# 🧠 DikaAi - Google Colab Runner
# ============================================
# Copy paste ini ke Colab, isi config, lalu run!

# STEP 1: Install
!pip install telethon aiohttp -q
!git clone https://github.com/dikaofc/dikaai.git /content/dikaai
%cd /content/dikaai

# STEP 2: Config (GANTI INI!)
TELEGRAM_API_ID = 12345678
TELEGRAM_API_HASH = "abc123def456"
TELEGRAM_PHONE = "+628123456789"
UPSTASH_REDIS_URL = "https://xxx.upstash.io"
UPSTASH_REDIS_TOKEN = "AXxx..."

# Simpan config
with open('config.env', 'w') as f:
    f.write(f'''TELEGRAM_API_ID={TELEGRAM_API_ID}
TELEGRAM_API_HASH={TELEGRAM_API_HASH}
TELEGRAM_PHONE={TELEGRAM_PHONE}
UPSTASH_REDIS_REST_URL={UPSTASH_REDIS_URL}
UPSTASH_REDIS_REST_TOKEN={UPSTASH_REDIS_TOKEN}
''')

# STEP 3: Run!
exec(open('colab_runner.py').read())
"""
