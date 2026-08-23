#!/usr/bin/env python3
"""
DikaAI v2 - Intelligent AI Coding Agent
=========================================
Bukan cuma chatbot. DikaAI bisa:
- Baca, tulis, edit kode
- Jalankan program + test
- Debug error otomatis
- Belajar dari pengalaman coding
- Cari knowledge (RAG)
- Git operations

Usage:
    python main.py              # Start everything
    python main.py chat         # Interactive chat
    python main.py agent        # Coding agent mode
    python main.py stats        # Show stats
    python main.py index        # Index project for RAG
    python main.py benchmark    # Run coding benchmarks
"""
import asyncio
import sys
import os
import time
import signal
import threading
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from core.orchestrator import Orchestrator
from core.router import Router, TaskType
from core.config import BASE_DIR as PROJ_DIR
from memory.coding_memory import CodingMemory
from rag.retriever import Retriever

# Legacy imports (for backward compat)
try:
    from database import DikaDB
    from tokenizer import DikaTokenizer
    from model import DikaModel
    from trainer import DikaTrainer
    from bot import DikaBot
    from config import (API_ID, API_HASH, MODEL_DIR, CONTEXT_LEN,
                        AUTO_REPLY_ENABLED, USE_REDIS,
                        UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN)
    from dashboard import start_dashboard, set_state
    from webscraper import DikaWebScraper
    LEGACY = True
except ImportError:
    LEGACY = False

try:
    from sync_to_redis import UpstashRedis, sync_messages, sync_model, sync_vocab, sync_training_history
except ImportError:
    UpstashRedis = None

BANNER = """
╔═══════════════════════════════════════════════╗
║         DikaAI v2 - Coding Agent 🧠           ║
║   Bukan cuma chatbot. Bisa coding beneran.    ║
║   Plan → Code → Test → Debug → Learn          ║
╚═══════════════════════════════════════════════╝
"""


class DikaAI:
    def __init__(self):
        self.workspace = str(PROJ_DIR)
        self.orchestrator = Orchestrator(self.workspace)

        # Legacy components (for Telegram bot)
        if LEGACY:
            self.db = DikaDB()
            self.tokenizer = DikaTokenizer()
            self.model = DikaModel()
            self.trainer = DikaTrainer(self.db)
            self.bot = DikaBot(self.db, model=self.model, tokenizer=self.tokenizer)

        self.running = False

    def show_stats(self):
        """Show DikaAI statistics."""
        stats = self.orchestrator.get_stats()

        print("\n" + "=" * 55)
        print("  DikaAI v2 Statistics 📊")
        print("=" * 55)
        print(f"  Total tasks     : {stats['total_tasks']}")
        print(f"  Successful      : {stats['successful_tasks']}")
        print(f"  Success rate    : {stats['success_rate']}")
        print(f"  Uptime          : {stats['uptime']}")
        print(f"  Coding memory   : {stats['coding_memory']['total']} experiences")
        print(f"  Success rate    : {stats['coding_memory']['success_rate']}")
        print(f"  RAG documents   : {stats['rag']['documents']}")
        print(f"  Conversation    : {stats['conversation_messages']} messages")

        if LEGACY:
            db_stats = self.db.get_stats()
            print(f"\n  --- Legacy ---")
            print(f"  Messages        : {db_stats['total']}")
            print(f"  Model step      : {self.model.step}")
            print(f"  Vocab           : {self.tokenizer.vocab_size}")

        print("=" * 55)

    def chat(self):
        """Interactive chat with DikaAI."""
        print("\n  DikaAI v2 Chat 💬")
        print("  Type 'quit' to exit\n")
        print("  Commands:")
        print("    /stats    - Show statistics")
        print("    /memory   - Show coding memory")
        print("    /index    - Index project for RAG")
        print("    /clear    - Clear conversation")
        print("    /help     - Show help\n")

        while True:
            try:
                user_input = input("  You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ('quit', 'exit', 'q', 'keluar'):
                    print("  DikaAI: Bye! 👋")
                    break

                if user_input.startswith('/'):
                    self._handle_command(user_input)
                    continue

                # Process through orchestrator
                result = self.orchestrator.process(user_input)

                response = result.get('response', '(no response)')
                route = result.get('route', 'chat')
                time_taken = result.get('time', '?s')

                print(f"\n  DikaAI [{route}]: {response}")
                print(f"  ({time_taken})\n")

            except KeyboardInterrupt:
                print("\n  DikaAI: Bye! 👋")
                break
            except Exception as e:
                print(f"  Error: {e}")

    def _handle_command(self, cmd: str):
        """Handle chat commands."""
        cmd = cmd.lower().strip()

        if cmd == '/stats':
            self.show_stats()
        elif cmd == '/memory':
            stats = self.orchestrator.coding_memory.get_stats()
            print(f"\n  Coding Memory: {stats['total']} experiences")
            print(f"  Success rate: {stats['success_rate']}")
            print(f"  Languages: {', '.join(stats['languages'])}\n")
        elif cmd == '/index':
            print("  Indexing project for RAG...")
            count = self.orchestrator.retriever.index_directory(self.workspace)
            print(f"  ✅ Indexed {count} files")
        elif cmd == '/clear':
            self.orchestrator.context.short_term.clear()
            print("  ✅ Conversation cleared")
        elif cmd == '/help':
            print("\n  Commands:")
            print("    /stats    - Show statistics")
            print("    /memory   - Show coding memory")
            print("    /index    - Index project for RAG")
            print("    /clear    - Clear conversation")
            print("    /quit     - Exit\n")
        else:
            print(f"  Unknown command: {cmd}")

    def agent_mode(self):
        """Run in agent mode - accepts tasks and executes them."""
        print("\n  DikaAI Agent Mode 🤖")
        print("  Enter coding tasks, DikaAI will plan + execute + debug\n")

        while True:
            try:
                task = input("\n  Task: ").strip()
                if not task or task.lower() in ('quit', 'exit', 'q'):
                    break

                print(f"\n  🔄 Processing: {task}")
                result = self.orchestrator.process(task)

                print(f"\n  {'✅' if result.get('success') else '❌'} Result:")
                print(f"  {result.get('response', 'No response')}")
                print(f"  Route: {result.get('route', '?')} | Time: {result.get('time', '?')}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"  Error: {e}")

    def index_project(self):
        """Index project for RAG."""
        print("  Indexing project for RAG...")
        count = self.orchestrator.retriever.index_directory(self.workspace)
        print(f"  ✅ Indexed {count} files")
        stats = self.orchestrator.retriever.get_stats()
        print(f"  Total documents: {stats['documents']}")

    def run_benchmark(self):
        """Run coding benchmark."""
        print("  Benchmarks coming in Phase 5...")
        print("  Current capabilities:")
        print(f"    Router accuracy: testing...")
        print(f"    Coding agent: active")
        print(f"    Memory: {self.orchestrator.coding_memory.get_stats()['total']} experiences")
        print(f"    RAG: {self.orchestrator.retriever.get_stats()['documents']} documents")


def main():
    dika = DikaAI()

    def signal_handler(sig, frame):
        print("\n  Stopping DikaAI...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    command = sys.argv[1] if len(sys.argv) > 1 else 'all'

    if command == 'stats':
        dika.show_stats()

    elif command == 'chat':
        dika.chat()

    elif command == 'agent':
        dika.agent_mode()

    elif command == 'index':
        dika.index_project()

    elif command == 'benchmark':
        dika.run_benchmark()

    elif command == 'all':
        print(BANNER)
        dika.show_stats()
        print("\n  Starting DikaAI v2...")
        print("  For interactive mode: python main.py chat")
        print("  For agent mode: python main.py agent\n")

        # Start dashboard if available
        if LEGACY:
            start_dashboard()
            set_state(model=dika.model, tokenizer=dika.tokenizer,
                      db=dika.db, bot=dika.bot, trainer=dika.trainer)

            # Start training
            if not dika.tokenizer.load():
                dika.trainer.build_vocab()

            dika.running = True
            dika.trainer.continuous_train()
        else:
            dika.chat()

    else:
        print(BANNER)
        print("  Usage:")
        print("    python main.py              # Start everything")
        print("    python main.py chat         # Interactive chat")
        print("    python main.py agent        # Coding agent mode")
        print("    python main.py stats        # Show statistics")
        print("    python main.py index        # Index project for RAG")
        print("    python main.py benchmark    # Run benchmarks")


if __name__ == '__main__':
    main()
