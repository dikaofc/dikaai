#!/usr/bin/env python3
"""
DikaAI v2 - Intelligent AI Coding Agent

Usage:
    python main.py              # Interactive chat
    python main.py chat         # Interactive chat
    python main.py run "task"   # Single task
    python main.py api          # Start API server
    python main.py stats        # Show stats
    python main.py index        # Index project
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import interactive_chat, run_single, show_stats, BANNER


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'chat':
            interactive_chat()
        elif cmd == 'run' and len(sys.argv) > 2:
            run_single(' '.join(sys.argv[2:]))
        elif cmd == 'api':
            from server.api import start_server
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
            start_server(port)
        elif cmd == 'stats':
            show_stats()
        elif cmd == 'index':
            from dikaai.engine import Engine
            e = Engine(os.getcwd())
            count = e.retriever.index_directory(os.getcwd())
            print(f"  Indexed {count} files for RAG")
        else:
            print(BANNER)
            print("  Usage:")
            print("    python main.py              # Interactive chat")
            print("    python main.py chat         # Interactive chat")
            print("    python main.py run 'task'   # Single task")
            print("    python main.py api          # Start API server")
            print("    python main.py stats        # Show stats")
            print("    python main.py index        # Index project")
    else:
        interactive_chat()


if __name__ == '__main__':
    main()
