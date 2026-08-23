#!/usr/bin/env python3
"""
DikaAI v3 - AI Coding Agent & Chat System

Usage:
    python main.py              # Interactive chat
    python main.py chat         # Interactive chat  
    python main.py run "task"   # Single task
    python main.py agent        # Agent mode
    python main.py api          # Start API server
    python main.py stats        # Show stats
    python main.py index        # Index project for RAG
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


BANNER = """
╔═══════════════════════════════════════════════════╗
║        DikaAI v3 - Coding Agent & Chat 🧠         ║
║                                                   ║
║  Input → Context → Memory → RAG → Agent → Model   ║
║                                                   ║
║  Commands:                                        ║
║    python main.py              # Interactive chat  ║
║    python main.py run "task"   # Single task       ║
║    python main.py agent        # Agent mode        ║
║    python main.py api          # REST API          ║
║    python main.py benchmark    # Run benchmark     ║
║    python main.py stats        # Statistics        ║
║    python main.py index        # Index project     ║
╚═══════════════════════════════════════════════════╝
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

    from dikaai.chat import DikaAIChat
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

            # Process message through full pipeline
            result = chat.send(user_input)
            response = result['response']
            route = result['route']
            t = result['time']

            # Color by route type
            color = {'code': '96', 'tool': '93', 'reason': '95',
                     'search': '94', 'chat': '92'}.get(route, '92')

            print(f"\n\033[{color}m  DikaAI [{route}]:\033[0m {response}")
            print(f"  \033[90m({t})\033[0m")

        except KeyboardInterrupt:
            print("\n  Bye! 👋")
            break
        except Exception as e:
            print(f"  Error: {e}")


def handle_command(cmd, chat):
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


def run_single(task):
    """Run a single task."""
    from dikaai.chat import DikaAIChat
    chat = DikaAIChat(workspace=os.getcwd())
    result = chat.send(task)
    print(f"\n  {result['response']}")
    print(f"  ({result['time']})")


def show_stats():
    """Show statistics."""
    from dikaai.chat import DikaAIChat
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
        elif cmd == 'agent':
            # Agent mode - continuous coding assistance
            from dikaai.chat import DikaAIChat
            print(BANNER)
            print("  🤖 Agent Mode - DikaAI will help with coding tasks\n")
            chat = DikaAIChat(workspace=os.getcwd())
            while True:
                try:
                    task = input("\033[96m  Task:\033[0m ").strip()
                    if not task:
                        continue
                    if task.lower() in ('quit', 'exit', 'q'):
                        break
                    result = chat.send(task)
                    print(f"\n  {result['response']}")
                    if result.get('success'):
                        print(f"  \033[92m✅ Done\033[0m ({result['time']})")
                    else:
                        print(f"  \033[91m❌ Failed\033[0m ({result['time']})")
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"  Error: {e}")
        elif cmd == 'api':
            from server.api import start_server
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
            start_server(port)
        elif cmd == 'token':
            from server.auth import AuthManager
            auth = AuthManager()
            name = sys.argv[2] if len(sys.argv) > 2 else 'api-key'
            scopes = sys.argv[3].split(',') if len(sys.argv) > 3 else ['chat', 'agent', 'tools']
            result = auth.create_token(name=name, scopes=scopes)
            print(f"\n  🔑 API Token Created!")
            print(f"  Token:   {result['token']}")
            print(f"  Name:    {result['name']}")
            print(f"  Scopes:  {result['scopes']}")
            print(f"\n  Usage:")
            print(f"    export DIKAAI_API_KEY={result['token'][:20]}...")
            print(f"    curl -H 'Authorization: Bearer {result['token'][:20]}...' http://localhost:8080/v1/chat/completions")
            print()
        elif cmd == 'stats':
            show_stats()
        elif cmd == 'index':
            from dikaai.rag.retriever import Retriever
            r = Retriever()
            count = r.index_directory(os.getcwd())
            print(f"  ✅ Indexed {count} files for RAG")
        elif cmd == 'benchmark':
            from dikaai.benchmark import BenchmarkRunner, Evaluator
            cat = sys.argv[2] if len(sys.argv) > 2 else None
            diff = sys.argv[3] if len(sys.argv) > 3 else None
            max_t = int(sys.argv[4]) if len(sys.argv) > 4 else None
            runner = BenchmarkRunner(workspace=os.getcwd())
            results = runner.run(category=cat, difficulty=diff, max_tasks=max_t)
            report = runner.report(results)
            Evaluator().print_report(report)
        elif cmd == 'train-code':
            from dikaai.model.trainer import DikaTrainer
            from dikaai.database import DikaDB
            epochs = int(sys.argv[2]) if len(sys.argv) > 2 else 100
            db = DikaDB()
            trainer = DikaTrainer(db)
            print(f"\n  🧠 Training on coding dataset ({epochs} epochs)...")
            loss, steps = trainer.train_coding(epochs=epochs)
            print(f"  ✅ Done! loss={loss:.4f}, steps={trainer.model.step}")
        else:
            print(BANNER)
    else:
        interactive_chat()


if __name__ == '__main__':
    main()
