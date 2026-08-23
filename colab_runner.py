#!/usr/bin/env python3
"""
DikaAi - Google Colab Runner
Jalan di Colab 12 jam, auto-sync ke Redis, dashboard di Vercel.

Usage di Colab:
    1. Copy paste semua ke satu cell
    2. Isi config (API_ID, REDIS_URL)
    3. Click Run
"""

# ============================================================
# IMPORTS (Paling atas!)
# ============================================================
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
from webscraper import DikaWebScraper
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
    print("Isi config dulu sebelum run!")
    raise SystemExit(1)

print(f"📱 Telegram: {PHONE}")
print(f"🔴 Redis: {'✅ Connected' if USE_REDIS else '❌ Not configured'}")

# ============================================================
# INITIALIZE COMPONENTS
# ============================================================
print("\n[1/6] Initializing components...")

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
# GLOBAL VARIABLES
# ============================================================
running = True
start_time = time.time()
max_runtime = 12 * 3600  # 12 jam

def signal_handler(sig, frame):
    global running
    print("\n⏹️ Stopping DikaAi...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

# ============================================================
# WEB SCRAPE FUNCTION (PRIORITY)
# ============================================================
def web_scrape_loop():
    """Web scrape dari internet (PRIORITY)"""
    try:
        web_scraper = DikaWebScraper(db)
        web_scraper.scrape_all()
        print("  [WEB] ✅ Web scrape complete!")
    except Exception as e:
        print(f"  [WEB] Error: {e}")

# ============================================================
# REDIS SYNC FUNCTION
# ============================================================
def redis_sync_loop():
    """Background thread: sync SQLite → Redis every 60s"""
    if not USE_REDIS:
        print("  [REDIS] ⚠️ Redis not configured, skipping sync")
        return
    
    try:
        r = UpstashRedis(UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN)
        r.ping()
        print("  [REDIS] ✅ Redis connected!")
    except Exception as e:
        print(f"  [REDIS] ❌ Redis connection failed: {e}")
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
    print("  [TRAIN] 🧠 Training started...")
    
    # Build vocab first
    stats = db.get_stats()
    if stats['total'] > 0:
        trainer.build_vocab()
        print(f"  [TRAIN] ✅ Vocab ready: {tokenizer.vocab_size} tokens")
    
    epoch = 0
    while running:
        try:
            epoch += 1
            loss, count = trainer.train_one_epoch()
            
            if count > 0:
                print(f"  [TRAIN] [Ep {epoch:3d}] loss={loss:.4f} steps={count} total={model.step}")
                
                # Save every 50 steps
                if model.step % 50 == 0:
                    model.save()
                    tokenizer.save()
            
            time.sleep(5)  # Training interval
            
        except Exception as e:
            print(f"  [TRAIN] Error: {e}")
            time.sleep(10)

# ============================================================
# TELEGRAM SCRAPE FUNCTION (PARALLEL)
# ============================================================
async def run_telegram():
    """Run Telegram scraper + bot (PARALLEL dengan web scrape)"""
    global running
    
    print("\n[3/6] Connecting to Telegram...")
    
    if not await bot.connect():
        print("❌ Failed to connect to Telegram!")
        print("Continuing with training + web scrape only...")
        return
    
    print("✅ Connected to Telegram!")
    
    # Phase 1: Scrape all chats PARALLEL
    print("\n[4/6] Scraping Telegram chats (PARALLEL)...")
    await bot.scrape_all()
    
    # Phase 2: Setup auto-reply
    print("\n[5/6] Starting auto-reply...")
    bot.setup_auto_reply()
    
    # Phase 3: Periodic re-scrape (every 6 jam)
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
            stats = db.get_stats()
            print(f"\n⏰ {hours_remaining:.1f} jam tersisa | {stats['total']} messages")
            
            # Wait 6 jam
            await asyncio.sleep(6 * 3600)
            
            if not running:
                break
            
            # Re-scrape PARALLEL
            scrape_count += 1
            print(f"\n🔄 Re-scrape #{scrape_count} (PARALLEL)...")
            
            # Web scrape (PRIORITY)
            web_task = threading.Thread(target=web_scrape_loop, daemon=True)
            web_task.start()
            
            # Telegram scrape PARALLEL
            await bot.scrape_recent(hours=6)
            
            web_task.join(timeout=120)
            
            # Rebuild vocab
            trainer.build_vocab()
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"  [SCRAPE] Error: {e}")
            await asyncio.sleep(300)

# ============================================================
# START ALL THREADS PARALLEL
# ============================================================
print("\n[2/6] Starting ALL threads PARALLEL...")

# Start Redis sync thread
redis_thread = threading.Thread(target=redis_sync_loop, daemon=True)
redis_thread.start()
print("  ✅ Redis sync thread started")

# Start training thread
train_thread = threading.Thread(target=train_loop, daemon=True)
train_thread.start()
print("  ✅ Training thread started")

# Start web scrape thread (PRIORITY)
web_thread = threading.Thread(target=web_scrape_loop, daemon=True)
web_thread.start()
print("  ✅ Web scrape thread started (PRIORITY)")

# ============================================================
# RUN ALL PARALLEL
# ============================================================
print("\n" + "=" * 60)
print("  🚀 DikaAi Started - ALL PARALLEL!")
print("  ⏱️  Auto-stop: 12 jam")
print("  📊 Dashboard: https://dikaai.vercel.app")
print("  🔄 Sync: Redis setiap 60 detik")
print("  🌐 Web scrape: PRIORITY")
print("  📱 Telegram: PARALLEL")
print("=" * 60)

try:
    # Wait for web scrape to finish first (PRIORITY)
    print("\n  [WAIT] Waiting for web scrape to finish (PRIORITY)...")
    web_thread.join(timeout=180)
    print("  [WAIT] ✅ Web scrape finished!")
    
    # Rebuild vocab after web scrape
    print("\n  [WAIT] Rebuilding vocab after web scrape...")
    trainer.build_vocab()
    print(f"  [WAIT] ✅ Vocab ready: {tokenizer.vocab_size} tokens")
    
    # Now run Telegram (PARALLEL)
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
