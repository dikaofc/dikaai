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
    AUTO_REPLY_ENABLED
)
from dashboard import start_dashboard, set_state, record_loss
from webscraper import DikaWebScraper

BANNER = """
╔══════════════════════════════════════╗
║         DikaAi v1.1                  ║
║   Paling Ringan Sedunia 🚀           ║
║   Ultra-Light AI Personal            ║
║   Auto-Reply + 24/7 Learning         ║
╚══════════════════════════════════════╝
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

    async def run_all(self):
        """Run everything AUTOMATICALLY: scrape + train + listen + auto-reply."""
        self.running = True

        # Start dashboard
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

        # Check Telegram config
        if not API_ID or not API_HASH:
            print("\n  ❌ Telegram API not configured!")
            print("  Continuing with training only...")
            if not self.tokenizer.load():
                self.trainer.build_vocab()
            self.trainer.continuous_train()
            return

        # Connect to Telegram
        if not await self.bot.connect():
            print("  ❌ Failed to connect. Check config.")
            return

        # Phase 1: Build vocab from existing data (if any)
        print("\n  [PHASE 1] Building vocab from existing data...")
        existing = self.db.get_stats()
        if existing['total'] > 0:
            self.trainer.build_vocab()
            print(f"  [PHASE 1] ✅ Vocab ready: {self.tokenizer.vocab_size} tokens")
        else:
            print("  [PHASE 1] No data yet, will build after scrape")

        # Phase 2: Start training IMMEDIATELY (if data exists)
        print("\n  [PHASE 2] Starting training (background)...")
        self.train_thread = threading.Thread(
            target=self._train_loop,
            daemon=True
        )
        self.train_thread.start()

        # Phase 3: Setup auto-reply + real-time listener
        print("\n  [PHASE 3] Starting auto-reply + listener...")
        self.bot.setup_auto_reply()

        # Phase 4: Scrape ALL chats (training runs in parallel!)
        print("\n  [PHASE 4] Scraping ALL chats (training runs in parallel!)...")
        await self.bot.scrape_all()

        # Phase 5: Scrape web content in background
        print("\n  [PHASE 5] Starting web scraper (background)...")
        self._web_thread = threading.Thread(
            target=self._web_scrape_loop,
            daemon=True
        )
        self._web_thread.start()

        # Phase 6: Rebuild vocab after scrape
        print("\n  [PHASE 6] Rebuilding vocab from new data...")
        self.trainer.build_vocab()
        print(f"  [PHASE 6] ✅ Vocab updated: {self.tokenizer.vocab_size} tokens")

        # Phase 6: Periodic re-scrape (every 6 hours)
        print("\n  [PHASE 7] Periodic re-scrape every 6 hours...")
        scrape_count = 0

        while self.running:
            try:
                await asyncio.sleep(6 * 3600)  # Every 6 hours
                scrape_count += 1
                print(f"\n  [RE-SCRAPE #{scrape_count}] Updating from Telegram + Web...")
                
                # Parallel: Telegram + Web scrape
                tg_task = asyncio.create_task(self.bot.scrape_recent(hours=6))
                web_task = threading.Thread(target=self._web_scrape_loop, daemon=True)
                web_task.start()
                
                await tg_task
                web_task.join(timeout=60)
                
                # Rebuild vocab if needed
                if self.tokenizer.vocab_size == 0 or not self.tokenizer._loaded:
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
            self.bot.close()
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
