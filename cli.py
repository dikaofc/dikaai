#!/usr/bin/env python3
"""
DikaAI CLI - Interactive command line interface.

Usage:
    python cli.py                    # Interactive chat
    python cli.py chat               # Interactive chat
    python cli.py run "fix main.py"  # Single task
    python cli.py stats              # Show stats
    python cli.py index              # Index project
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dikaai.chat import DikaAIChat


BANNER = """
╔═══════════════════════════════════════════╗
║       DikaAI v2 - Coding Agent 🧠         ║
║   Plan → Code → Test → Debug → Learn     ║
╚═══════════════════════════════════════════╝
"""


def interactive_chat():
    """Interactive chat mode."""
    print(BANNER)
    print("  Commands:")
    print("    /stats    - Show statistics")
    print("    /memory   - Show coding memory")
    print("    /clear    - Clear conversation")
    print("    /help     - Show help")
    print("    /quit     - Exit\n")

    chat = DikaAIChat(workspace=os.getcwd())

    while True:
        try:
            user_input = input("\033[92m  You:\033[0m ").strip()
            if not user_input:
                continue

            if user_input.lower() in ('quit', 'exit', 'q', '/quit'):
                print("  Bye! 👋")
                break

            if user_input.startswith('/'):
                handle_command(user_input, chat)
                continue

            # Process message
            result = chat.send(user_input)
            response = result['response']
            route = result['route']
            t = result['time']

            # Color output
            color = {'code': '96', 'tool': '93', 'reason': '95',
                     'search': '94', 'chat': '92'}.get(route, '92')

            print(f"\n\033[{color}m  DikaAI [{route}]:\033[0m {response}")
            print(f"  \033[90m({t})\033[0m")

        except KeyboardInterrupt:
            print("\n  Bye! 👋")
            break
        except Exception as e:
            print(f"  Error: {e}")


def handle_command(cmd: str, chat):
    """Handle chat commands."""
    cmd = cmd.lower().strip()
    if cmd == '/stats':
        stats = chat.stats()
        print(f"\n  Tasks: {stats['total']} | Success: {stats['rate']}")
        print(f"  Observer: {stats['observer']['total_observations']} observations")
    elif cmd == '/memory':
        print(f"\n  Coding memory: {chat.engine.coding_memory.get_stats()}")
    elif cmd == '/clear':
        chat.clear()
        print("  ✅ Conversation cleared")
    elif cmd == '/help':
        print("\n  Commands: /stats /memory /clear /help /quit")
    else:
        print(f"  Unknown: {cmd}")


def run_single(task: str):
    """Run a single task."""
    chat = DikaAIChat(workspace=os.getcwd())
    result = chat.send(task)
    print(f"\n  {result['response']}")
    print(f"  ({result['time']})")


def show_stats():
    """Show statistics."""
    chat = DikaAIChat(workspace=os.getcwd())
    stats = chat.stats()
    print(f"\n  DikaAI Stats:")
    print(f"  Tasks: {stats['total']}")
    print(f"  Success: {stats['rate']}")
    print(f"  Observer: {stats['observer']['total_observations']} obs")


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'chat':
            interactive_chat()
        elif cmd == 'run' and len(sys.argv) > 2:
            run_single(' '.join(sys.argv[2:]))
        elif cmd == 'stats':
            show_stats()
        else:
            print(BANNER)
            print("  Usage:")
            print("    python cli.py              # Interactive chat")
            print("    python cli.py chat         # Interactive chat")
            print("    python cli.py run 'task'   # Single task")
            print("    python cli.py stats        # Show stats")
    else:
        interactive_chat()


if __name__ == '__main__':
    main()
