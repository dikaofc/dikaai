#!/usr/bin/env python3
"""
DikaAi - Google Colab Runner
========================================
Copy-paste SEMUA ke SATU cell di Colab.
Ganti config di bawah, lalu Run!
Dashboard Vercel: https://dikaai.vercel.app
========================================
"""

# ============================================================
# STEP 1: Install + Clone (shallow - cepat!)
# ============================================================
!pip install telethon aiohttp nest_asyncio -q
!git clone --depth 1 https://github.com/dikaofc/dikaai.git /content/dikaai
%cd /content/dikaai

# ============================================================
# STEP 2: CONFIG (GANTI INI!)
# ============================================================

# Telegram (wajib) - dari https://my.telegram.org
TELEGRAM_API_ID = 12345678                # Ganti!
TELEGRAM_API_HASH = "abc123def456"        # Ganti!
TELEGRAM_PHONE = "+628123456789"          # Ganti!

# Upstash Redis (WAJIB biar dashboard Vercel jalan!)
# Daftar gratis: https://upstash.com → Create Database → Copy URL + Token
UPSTASH_REDIS_URL = "https://xxx.upstash.io"   # Ganti!
UPSTASH_REDIS_TOKEN = "AXxx..."                 # Ganti!

# Simpan ke config.env
with open('config.env', 'w') as f:
    f.write(f"""TELEGRAM_API_ID={TELEGRAM_API_ID}
TELEGRAM_API_HASH={TELEGRAM_API_HASH}
TELEGRAM_PHONE={TELEGRAM_PHONE}
UPSTASH_REDIS_REST_URL={UPSTASH_REDIS_URL}
UPSTASH_REDIS_REST_TOKEN={UPSTASH_REDIS_TOKEN}
""")
print("✅ Config saved!")
print(f"📱 Telegram: {TELEGRAM_PHONE}")
print(f"🔴 Redis: {UPSTASH_REDIS_URL[:30]}...")

# ============================================================
# STEP 3: RUN DIKAAI
# ============================================================
import sys, os, time, signal, threading, asyncio
import nest_asyncio
nest_asyncio.apply()

sys.path.insert(0, '/content/dikaai')
os.chdir('/content/dikaai')

from database import DikaDB
from tokenizer import DikaTokenizer
from model import DikaModel
from trainer import DikaTrainer
from bot import DikaBot
from webscraper import DikaWebScraper
from config import API_ID, API_HASH, PHONE, UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN, USE_REDIS

print("\n" + "=" * 55)
print("  🧠 DikaAi - Google Colab Runner")
print("  ⏱️  Auto-stop: 12 jam")
print("  🌐 Web scrape → Training → Telegram")
print("  📊 Dashboard: https://dikaai.vercel.app")
print("=" * 55)

if not API_ID or not API_HASH:
    print("❌ Telegram API belum dikonfigurasi!")
    raise SystemExit(1)

if not USE_REDIS:
    print("⚠️  Redis belum dikonfigurasi!")
    print("   Dashboard Vercel TIDAK akan update.")
    print("   Isi UPSTASH_REDIS_URL dan UPSTASH_REDIS_TOKEN dulu!")

# Init
db = DikaDB()
tokenizer = DikaTokenizer()
model = DikaModel()
trainer = DikaTrainer(db)
bot = DikaBot(db, model=model, tokenizer=tokenizer)

model.load()
tokenizer.load()

running = True
start_time = time.time()
max_runtime = 12 * 3600

def stop_handler(sig, frame):
    global running
    print("\n⏹️ Stopping...")
    running = False
signal.signal(signal.SIGINT, stop_handler)

# --- Threads ---
def web_scrape():
    try:
        DikaWebScraper(db).scrape_all()
        print("  [WEB] ✅ Done!")
    except Exception as e:
        print(f"  [WEB] Error: {e}")

def redis_sync():
    """Sync SQLite → Redis setiap 60 detik (biar dashboard Vercel update)"""
    if not USE_REDIS:
        print("  [REDIS] ⚠️ Skip (not configured)")
        return
    try:
        from sync_to_redis import UpstashRedis, sync_messages, sync_model, sync_vocab
        r = UpstashRedis(UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN)
        r.ping()
        print("  [REDIS] ✅ Connected to Upstash!")
        print("  [REDIS] 📊 Dashboard: https://dikaai.vercel.app")
        n = 0
        while running:
            time.sleep(60)
            if not running: break
            try:
                sync_messages(r, limit=200)
                sync_model(r)
                sync_vocab(r)
                n += 1
                if n % 5 == 0:
                    stats = db.get_stats()
                    print(f"  [REDIS] ✅ Sync #{n} | {stats['total']} msgs → Vercel")
            except Exception as e:
                print(f"  [REDIS] ⚠️ Sync error: {e}")
    except Exception as e:
        print(f"  [REDIS] ❌ Connection failed: {e}")

def train():
    print("  [TRAIN] 🧠 Training started...")
    if db.get_stats()['total'] > 0:
        trainer.build_vocab()
        print(f"  [TRAIN] ✅ Vocab: {tokenizer.vocab_size} tokens")
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

async def telegram():
    global running
    if not await bot.connect():
        print("❌ Telegram connect failed, skipping...")
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
            print(f"\n⏰ {rem:.1f}h left | {stats['total']} msgs | model step {model.step}")
            await asyncio.sleep(6 * 3600)
            if not running: break
            n += 1
            print(f"\n🔄 Re-scrape #{n}...")
            wt = threading.Thread(target=web_scrape, daemon=True)
            wt.start()
            await bot.scrape_recent(hours=6)
            wt.join(timeout=120)
            trainer.build_vocab()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"  Error: {e}")
            await asyncio.sleep(300)

# Start threads
print("\n🚀 Starting all threads...")
for name, fn in [("Redis sync", redis_sync), ("Training", train), ("Web scrape", web_scrape)]:
    t = threading.Thread(target=fn, daemon=True)
    t.start()
    print(f"  ✅ {name} thread started")

try:
    print("\n⏳ Waiting for web scrape (priority)...")
    time.sleep(10)
    if db.get_stats()['total'] > 0:
        trainer.build_vocab()
        print(f"✅ Vocab: {tokenizer.vocab_size} tokens")

    print(f"\n📊 Dashboard: https://dikaai.vercel.app")
    asyncio.run(telegram())
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
