#!/usr/bin/env python3
"""
DikaAI - Google Colab Runner (v2 - BULLETPROOF)
=============================================
FIXED: cd /content FIRST (before everything), then clone, then cd into project.
This prevents "getcwd: cannot access parent directories" errors.
=============================================
"""

# ============================================================
# STEP 0: Fix working directory (CRITICAL!)
# ============================================================
import os
os.chdir('/content')  # <-- FIX: always start from /content
print(f"✅ CWD: {os.getcwd()}")

# ============================================================
# STEP 1: Install + Clone
# ============================================================
!pip install telethon aiohttp nest_asyncio -q

# Remove old clone if exists
!rm -rf /content/dikaai

# Clone fresh
!git clone --depth 1 https://github.com/dikaofc/dikaai.git /content/dikaai

# Verify clone succeeded
if not os.path.exists('/content/dikaai'):
    raise FileNotFoundError("Clone failed! Check internet connection.")

# NOW cd into project (after clone is verified)
os.chdir('/content/dikaai')
print(f"✅ Project CWD: {os.getcwd()}")

# Clear ALL Python bytecode cache (prevents stale .pyc errors)
import shutil
for root, dirs, files in os.walk('/content/dikaai'):
    for d in dirs:
        if d == '__pycache__':
            shutil.rmtree(os.path.join(root, d), ignore_errors=True)
import importlib
importlib.invalidate_caches()

# ============================================================
# STEP 2: CONFIG (GANTI INI!)
# ============================================================

# Telegram (wajib) - dari https://my.telegram.org
TELEGRAM_API_ID = 12345678                # Ganti!
TELEGRAM_API_HASH = "abc123def456"        # Ganti!
TELEGRAM_PHONE = "+628123456789"          # Ganti!

# Upstash Redis (WAJIB biar dashboard Vercel jalan!)
UPSTASH_REDIS_URL = "https://xxx.upstash.io"   # Ganti!
UPSTASH_REDIS_TOKEN = "AXxx..."                 # Ganti!

# Simpan ke config.env (dengan full path safety)
config_path = os.path.join(os.getcwd(), 'config.env')
config_content = f"""TELEGRAM_API_ID={TELEGRAM_API_ID}
TELEGRAM_API_HASH={TELEGRAM_API_HASH}
TELEGRAM_PHONE={TELEGRAM_PHONE}
UPSTASH_REDIS_REST_URL={UPSTASH_REDIS_URL}
UPSTASH_REDIS_REST_TOKEN={UPSTASH_REDIS_TOKEN}
"""

with open(config_path, 'w') as f:
    f.write(config_content)

print(f"✅ Config saved to {config_path}")
print(f"📱 Telegram: {TELEGRAM_PHONE}")
print(f"🔴 Redis: {UPSTASH_REDIS_URL[:30]}...")

# ============================================================
# STEP 3: RUN DIKAAI
# ============================================================
import sys, time, signal, threading, asyncio
import nest_asyncio
nest_asyncio.apply()

sys.path.insert(0, '/content/dikaai')
os.chdir('/content/dikaai')

from dikaai.database import DikaDB
from dikaai.model.tokenizer import DikaTokenizer
from dikaai.model.model import DikaModel
from dikaai.model.trainer import DikaTrainer
from bot import DikaBot
from webscraper import DikaWebScraper
from dikaai.config import API_ID, API_HASH, PHONE, UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN, USE_REDIS

print("\n" + "=" * 55)
print("  🧠 DikaAI - Google Colab Runner")
print("  ⏱️  Auto-stop: 12 jam")
print("  🔄 Flow: Web Scrape → Train → Telegram Loop")
print("  📊 Dashboard: https://dikaai.vercel.app")
print("=" * 55)

if not API_ID or not API_HASH:
    print("❌ Telegram API belum dikonfigurasi!")
    raise SystemExit(1)

if not USE_REDIS:
    print("⚠️  Redis belum dikonfigurasi! Dashboard ga jalan.")

# Init (FRESH - ga load model lama)
db = DikaDB()
tokenizer = DikaTokenizer()
model = DikaModel()
trainer = DikaTrainer(db)
bot = DikaBot(db, model=model, tokenizer=tokenizer)

print("  🆕 Starting FRESH (no old model)")

running = True
start_time = time.time()
max_runtime = 12 * 3600

def stop_handler(sig, frame):
    global running
    print("\n⏹️ Stopping...")
    running = False
try:
    signal.signal(signal.SIGINT, stop_handler)
except ValueError:
    pass

# --- Redis Sync Thread ---
def redis_sync():
    if not USE_REDIS:
        return
    try:
        from sync_to_redis import UpstashRedis, sync_messages, sync_model, sync_vocab, sync_training_history
        r = UpstashRedis(UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN)
        r.ping()
        print("  [REDIS] ✅ Connected!")
        n = 0
        while running:
            time.sleep(60)
            if not running: break
            try:
                sync_messages(r, limit=200)
                sync_model(r)
                sync_vocab(r)
                sync_training_history(r)
                n += 1
                if n % 5 == 0:
                    stats = db.get_stats()
                    print(f"  [REDIS] ✅ Sync #{n} | {stats['total']} msgs → Vercel")
            except Exception as e:
                print(f"  [REDIS] ⚠️ {e}")
    except Exception as e:
        print(f"  [REDIS] ❌ {e}")

# --- Training Thread ---
def train():
    print("  [TRAIN] 🧠 Training started...")
    ep = 0
    while running:
        try:
            ep += 1
            loss, count = trainer.train_one_epoch()
            if count > 0:
                print(f"  [TRAIN] Ep {ep:3d} | loss={loss:.4f} | steps={count} | total={model.step}")
                if model.step % 50 == 0:
                    model.save()
                    tokenizer.save()
            time.sleep(5)
        except Exception as e:
            print(f"  [TRAIN] Error: {e}")
            time.sleep(10)

# --- Telegram Loop ---
async def telegram_loop():
    global running
    if not await bot.connect():
        print("❌ Telegram connect failed!")
        return
    print("✅ Telegram connected!")
    await bot.scrape_all()
    bot.setup_auto_reply()
    n = 0
    while running:
        try:
            rem = (max_runtime - (time.time() - start_time)) / 3600
            if rem <= 0:
                running = False
                break
            stats = db.get_stats()
            print(f"\n⏰ {rem:.1f}h left | {stats['total']} msgs | step {model.step}")
            await asyncio.sleep(6 * 3600)
            if not running: break
            n += 1
            print(f"\n🔄 Re-scrape #{n}...")
            wt = threading.Thread(target=web_scrape_fn, daemon=True)
            wt.start()
            await bot.scrape_recent(hours=6)
            wt.join(timeout=120)
            trainer.build_vocab()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"  Error: {e}")
            await asyncio.sleep(300)

def web_scrape_fn():
    try:
        DikaWebScraper(db).scrape_all()
        print("  [WEB] ✅ Done!")
    except Exception as e:
        print(f"  [WEB] Error: {e}")

# ============================================================
# PHASE 1: WEB SCRAPE (priority, blocking)
# ============================================================
print("\n" + "=" * 55)
print("  📡 PHASE 1: Web Scrape (dari internet)")
print("=" * 55)

redis_t = threading.Thread(target=redis_sync, daemon=True)
redis_t.start()

web_scrape_fn()

# ============================================================
# PHASE 2: BUILD VOCAB + TRAINING (web data only)
# ============================================================
print("\n" + "=" * 55)
print("  🧠 PHASE 2: Training dari Web Data")
print("=" * 55)

stats = db.get_stats()
print(f"  📊 Data: {stats['total']} messages dari web")

if stats['total'] > 0:
    trainer.build_vocab()
    print(f"  📖 Vocab: {tokenizer.vocab_size} tokens")

    print("  🏋️ Training 200 epochs dari web data...")
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
    print(f"  ✅ Training selesai! Model step: {model.step}")
else:
    print("  ⚠️ Tidak ada data web, skip training")

# ============================================================
# PHASE 3: TELEGRAM LOOP (auto-reply + scrape)
# ============================================================
print("\n" + "=" * 55)
print("  📱 PHASE 3: Telegram Loop")
print("  🔄 Auto-reply + scrape + training continues")
print("  ⏱️  Auto-stop: 12 jam")
print("=" * 55)

train_t = threading.Thread(target=train, daemon=True)
train_t.start()
print("  ✅ Training thread started (background)")

try:
    asyncio.run(telegram_loop())
except KeyboardInterrupt:
    pass
finally:
    running = False
    model.save()
    tokenizer.save()
    s = db.get_stats()
    print(f"\n{'='*55}")
    print(f"  📊 Final Stats")
    print(f"  Messages : {s['total']}")
    print(f"  Model    : step {model.step}")
    print(f"  Vocab    : {tokenizer.vocab_size} tokens")
    print(f"  Runtime  : {(time.time()-start_time)/3600:.1f} jam")
    print(f"  Dashboard: https://dikaai.vercel.app")
    print(f"{'='*55}")
