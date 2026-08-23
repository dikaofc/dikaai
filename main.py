#!/usr/bin/env python3
"""
DikaAi - Ultra Lightweight AI Personal Assistant
Paling Ringan Sedunia 🚀

Features:
- Belajar dari semua chat Telegram (24/7)
- Auto-reply di chat Telegram
- Anti duplikasi
- Fast learning
- Jalan lancar di Android Termux

Usage:
    python main.py              # Start everything
    python main.py scrape       # Scrape only
    python main.py train        # Train only
    python main.py chat         # Interactive chat
    python main.py stats        # Show stats
"""
import asyncio
import sys
import time
import signal
import threading
from pathlib import Path

from database import DikaDB
from tokenizer import DikaTokenizer
from model import DikaModel
from trainer import DikaTrainer
from bot import DikaBot
from config import (
    API_ID, API_HASH, MODEL_DIR, CONTEXT_LEN, TRAIN_INTERVAL,
    AUTO_REPLY_ENABLED, USE_REDIS, UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN
)
from dashboard import start_dashboard, set_state, record_loss
from webscraper import DikaWebScraper

# Redis sync (auto-import if available)
try:
    from sync_to_redis import UpstashRedis, sync_messages, sync_model, sync_vocab, sync_training_history
except ImportError:
    UpstashRedis = None

BANNER = """
╔══════════════════════════════════════════╗
║         DikaAi v2.0                      ║
║   Paling Ringan Sedunia 🚀               ║
║   Ultra-Light AI Personal                ║
║   Auto-Reply + 24/7 Learning             ║
║   Dashboard + Redis Sync                 ║
╚══════════════════════════════════════════╝
"""


class DikaAi:
    def __init__(self):
        MODEL_DIR.mkdir(exist_ok=True)

        self.db = DikaDB()
        self.tokenizer = DikaTokenizer()
        self.model = DikaModel()
        self.trainer = DikaTrainer(self.db)
        self.bot = DikaBot(self.db, model=self.model, tokenizer=self.tokenizer)

        self.running = False
        self.train_thread = None
        self._redis_thread = None

        # Setup dashboard state
        set_state(
            model=self.model,
            tokenizer=self.tokenizer,
            db=self.db,
            bot=self.bot
        )

    def show_stats(self):
        """Show current stats."""
        stats = self.db.get_stats()
        param_count = self.model.get_param_count()

        print("\n" + "=" * 45)
        print("  DikaAi Statistics 📊")
        print("=" * 45)
        print(f"  Total messages : {stats['total']}")
        print(f"  Processed      : {stats['processed']}")
        print(f"  Unprocessed    : {stats['unprocessed']}")
        print(f"  Unique chats   : {stats['unique_chats']}")
        print(f"  Model params   : {param_count:,}")
        print(f"  Model steps    : {self.model.step}")
        print(f"  Vocab size     : {self.tokenizer.vocab_size}")
        print(f"  Model dir      : {MODEL_DIR}")
        print("=" * 45)

    def chat(self):
        """Interactive chat mode."""
        print("\n  DikaAi Chat Mode 💬")
        print("  Type 'quit' to exit\n")

        if not self.model.load():
            print("  ❌ No model found! Run training first.")
            return

        if not self.tokenizer.load():
            print("  ❌ No vocabulary found! Run training first.")
            return

        while True:
            try:
                user_input = input("  You: ").strip()

                if user_input.lower() in ('quit', 'exit', 'q', 'keluar'):
                    print("  DikaAi: Bye! 👋")
                    break

                if not user_input:
                    continue

                tokens = self.tokenizer.encode(user_input, max_length=CONTEXT_LEN)
                generated = self.model.generate(tokens, max_len=30, temperature=0.7)
                response = self.tokenizer.decode(generated)

                print(f"  DikaAi: {response}")

            except KeyboardInterrupt:
                print("\n  DikaAi: Bye! 👋")
                break
            except Exception as e:
                print(f"  Error: {e}")

    async def scrape_only(self, limit=None):
        """Scrape Telegram only."""
        if not await self.bot.connect():
            return
        try:
            await self.bot.scrape_all(limit_per_chat=limit)
        finally:
            await self.bot.client.disconnect()

    def train_only(self):
        """Train only."""
        # Start dashboard
        start_dashboard()
        set_state(
            model=self.trainer.model,
            tokenizer=self.trainer.tokenizer,
            trainer=self.trainer,
            db=self.db,
            status='training'
        )

        if not self.tokenizer._loaded:
            if not self.tokenizer.load():
                self.trainer.build_vocab()

        self.running = True
        self.trainer.continuous_train()

    def _train_loop(self):
        """Training loop in background thread."""
        try:
            self.trainer.continuous_train()
        except Exception as e:
            print(f"  [TRAIN] Error: {e}")

    def _web_scrape_loop(self):
        """Web scraper loop in background thread."""
        try:
            web_scraper = DikaWebScraper(self.db)
            web_scraper.scrape_all()
            print("  [WEB] ✅ Web scrape complete!")
        except Exception as e:
            print(f"  [WEB] Error: {e}")

    def _redis_sync_loop(self):
        """Auto-sync SQLite → Redis every 60s."""
        if not USE_REDIS or not UpstashRedis:
            return

        try:
            r = UpstashRedis(UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN)
            r.ping()
            print("  [REDIS] ✅ Connected to Upstash Redis")
        except Exception as e:
            print(f"  [REDIS] ❌ Connection failed: {e}")
            return

        # Initial sync
        try:
            sync_messages(r, limit=200)
            sync_model(r)
            sync_vocab(r)
            sync_training_history(r)
            print("  [REDIS] ✅ Initial sync complete")
        except Exception as e:
            print(f"  [REDIS] ⚠️  Initial sync error: {e}")

        # Periodic sync every 60s
        while self.running:
            try:
                time.sleep(60)
                if not self.running:
                    break
                sync_messages(r, limit=200)
                sync_model(r)
                sync_vocab(r)
            except Exception as e:
                print(f"  [REDIS] ⚠️  Sync error: {e}")
                time.sleep(30)

    async def run_all(self):
        """Run everything AUTOMATICALLY: web scrape + train + listen + auto-reply.
        
        Fully automatic flow (100% otomatis):
        1. Start Dashboard (port 8888)
        2. Web scrape (ambil data dari internet)
        3. Build vocab dari data
        4. Start training (background)
        5. [Optional] Connect Telegram + auto-reply + scrape chat
        6. Periodic re-scrape (setiap 6 jam)
        """
        self.running = True

        # ================================================================
        # PHASE 1: Start Dashboard
        # ================================================================
        print("\n  [SYS] 🚀 Starting DikaAi - Fully Automatic!")
        start_dashboard()
        set_state(
            model=self.trainer.model,
            tokenizer=self.trainer.tokenizer,
            trainer=self.trainer,
            db=self.db,
            bot=self.bot
        )

        print(BANNER)
        self.show_stats()

        # Show Redis status
        if USE_REDIS:
            print("  [SYS] ✅ Redis: Auto-sync ON (every 60s)")
        else:
            print("  [SYS] ⚠️  Redis: Not configured (local only)")

        # Show Telegram status
        tg_configured = bool(API_ID and API_HASH)
        if tg_configured:
            print("  [SYS] ✅ Telegram: Configured")
        else:
            print("  [SYS] ⚠️  Telegram: Not configured (web scrape only)")

        # ================================================================
        # PHASE 2: Web Scrape (ambil data dari internet)
        # ================================================================
        print("\n  [PHASE 1] 🌐 Web scraping dari internet...")
        self._web_thread = threading.Thread(
            target=self._web_scrape_loop,
            daemon=True
        )
        self._web_thread.start()
        # Wait for initial web scrape to finish (max 120s)
        self._web_thread.join(timeout=120)
        print("  [PHASE 1] ✅ Web scrape selesai!")

        # ================================================================
        # PHASE 3: Build Vocab dari data
        # ================================================================
        print("\n  [PHASE 2] 📖 Building vocab dari data...")
        existing = self.db.get_stats()
        if existing['total'] > 0:
            self.trainer.build_vocab()
            print(f"  [PHASE 2] ✅ Vocab ready: {self.tokenizer.vocab_size} tokens dari {existing['total']} messages")
        else:
            print("  [PHASE 2] ⚠️  No data yet, will build after scrape")

        # ================================================================
        # PHASE 4: Start Training (background)
        # ================================================================
        print("\n  [PHASE 3] 🧠 Starting training (background)...")
        self.train_thread = threading.Thread(
            target=self._train_loop,
            daemon=True
        )
        self.train_thread.start()

        # ================================================================
        # PHASE 5: Connect Telegram (optional)
        # ================================================================
        telegram_connected = False
        if tg_configured:
            print("\n  [PHASE 4] 📱 Connecting to Telegram...")
            if await self.bot.connect():
                telegram_connected = True
                print("  [PHASE 4] ✅ Telegram connected!")

                # Setup auto-reply
                print("  [PHASE 4] 👂 Starting auto-reply + listener...")
                self.bot.setup_auto_reply()

                # Scrape Telegram chats (training runs in parallel!)
                print("  [PHASE 4] 📥 Scraping ALL Telegram chats...")
                await self.bot.scrape_all()
            else:
                print("  [PHASE 4] ⚠️  Telegram connection failed, continuing without it...")
        else:
            print("\n  [PHASE 4] ⏭️  Skipping Telegram (not configured)")

        # ================================================================
        # PHASE 6: Rebuild vocab (after all scrapes done)
        # ================================================================
        print("\n  [PHASE 5] 🔄 Rebuilding vocab dari semua data...")
        self.trainer.build_vocab()
        print(f"  [PHASE 5] ✅ Vocab updated: {self.tokenizer.vocab_size} tokens")

        # ================================================================
        # PHASE 7: Redis auto-sync (if configured)
        # ================================================================
        if USE_REDIS:
            print("\n  [PHASE 6] 🔴 Starting Redis auto-sync (every 60s)...")
            self._redis_thread = threading.Thread(
                target=self._redis_sync_loop,
                daemon=True
            )
            self._redis_thread.start()
        else:
            print("\n  [PHASE 6] Redis not configured, skipping sync")

        # ================================================================
        # PHASE 8: Periodic re-scrape (setiap 6 jam)
        # ================================================================
        print("\n  [PHASE 7] ⏰ Periodic re-scrape setiap 6 jam...")
        print("  [SYS] ✅ DikaAi berjalan otomatis! Ctrl+C untuk stop.")
        print("  [SYS] 🌐 Dashboard: http://localhost:8888")
        scrape_count = 0

        while self.running:
            try:
                await asyncio.sleep(6 * 3600)  # Every 6 hours
                scrape_count += 1
                print(f"\n  [RE-SCRAPE #{scrape_count}] 🔄 Updating data...")
                
                # Web scrape (always)
                web_task = threading.Thread(target=self._web_scrape_loop, daemon=True)
                web_task.start()
                
                # Telegram scrape (if connected)
                if telegram_connected and self.bot.client:
                    try:
                        tg_task = asyncio.create_task(self.bot.scrape_recent(hours=6))
                        await tg_task
                    except Exception as e:
                        print(f"  [RE-SCRAPE] Telegram error: {e}")
                
                web_task.join(timeout=120)
                
                # Rebuild vocab after re-scrape
                if self.tokenizer.vocab_size == 0 or not self.tokenizer._loaded:
                    self.trainer.build_vocab()
                else:
                    self.trainer.build_vocab()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"  [RE-SCRAPE] Error: {e}")
                await asyncio.sleep(300)

    def stop(self):
        """Stop everything."""
        self.running = False
        self.trainer.stop()
        if self.bot.client:
            try:
                self.bot.close()
            except Exception:
                pass
        self.model.save()
        self.tokenizer.save()
        print("  DikaAi stopped. Model saved! 💾")


def main():
    dika = DikaAi()

    def signal_handler(sig, frame):
        print("\n  Stopping DikaAi...")
        dika.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    command = sys.argv[1] if len(sys.argv) > 1 else 'all'

    if command == 'stats':
        dika.show_stats()

    elif command == 'scrape':
        asyncio.run(dika.scrape_only())

    elif command == 'train':
        dika.train_only()

    elif command == 'chat':
        dika.chat()

    elif command == 'dashboard':
        from dashboard import start_dashboard, set_state
        set_state(model=dika.model, tokenizer=dika.tokenizer,
                  db=dika.db, bot=dika.bot, trainer=dika.trainer,
                  status='idle')
        start_dashboard()
        print("  Dashboard running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    elif command == 'all':
        try:
            asyncio.run(dika.run_all())
        except KeyboardInterrupt:
            dika.stop()

    else:
        print(BANNER)
        print("  Usage:")
        print("    python main.py             # Start everything")
        print("    python main.py scrape      # Scrape Telegram only")
        print("    python main.py train       # Train only")
        print("    python main.py chat        # Chat with DikaAi")
        print("    python main.py stats       # Show statistics")
        print("    python main.py dashboard   # Web dashboard only")


if __name__ == '__main__':
    main()
