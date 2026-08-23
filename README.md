# 🧠 DikaAI - Intelligent AI Coding Agent & Chat System

**AI Indonesia yang tidak hanya chatbot, tapi coding agent.** Belajar dari chat Telegram + web scraping + coding experience.

> Arsitektur: `User → Context → Memory → RAG → Agent → Model → Validator → Response`

---

## ✨ Features

### 🧠 AI Engine (dikaai/)
- **Context Management** - Topic tracking, anti-drift, hierarchical context
- **Memory System** - Short-term conversation + long-term coding experience
- **RAG** - Knowledge retrieval via vector search
- **Coding Agent** - Plan → Code → Test → Debug → Retry loop
- **Validator** - Response quality check (correctness, relevance, safety)
- **Smart Reply** - 100+ pola Indonesian dengan garbage detection

### 🤖 Coding Agent
- **Planner** - Breakdown task jadi langkah actionable
- **Executor** - Loop: Plan → Code → Run → Test → Debug → Retry
- **Tools** - Filesystem, terminal, git (sandboxed)
- **Coding Memory** - Belajar dari error→solution pairs
- **Auto-fix** - ModuleNotFoundError → auto `pip install`

### 🧠 Model
- **LSTM** 48K params (pure Python, no numpy)
- **Adam optimizer** + cosine LR scheduler
- **Indonesian tokenizer** dengan slang normalization
- **Training pipeline** - Auto from web data + chat

### 📱 Telegram Bot
- **Auto-reply** cerdas (100+ pola)
- **Parallel scraping** (15 concurrent)
- **Real-time listener** + auto-reply

### 📊 Dashboard
- **Vercel** - Web UI (auto-refresh 10s)
- **Loss chart** - Training real-time
- **Controls** - Toggle on/off fitur
- **Chat** - Web chat dengan AI
- **Redis sync** - SQLite → Upstash tiap 60 detik

---

## 🚀 Quick Start

### Google Colab (Paling Gampang!)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/dikaofc/dikaai/blob/main/colab_simple.py)

```python
# 1. Paste colab_simple.py ke Colab
# 2. Ganti 5 config:
TELEGRAM_API_ID = 12345678        # dari my.telegram.org
TELEGRAM_API_HASH = "abc123def456"
TELEGRAM_PHONE = "+628123456789"
UPSTASH_REDIS_URL = "https://xxx.upstash.io"   # dari upstash.com
UPSTASH_REDIS_TOKEN = "AXxx..."
# 3. Run!
```

**Flow otomatis:**
```
PHASE 1 → 🌐 Web scrape (Wikipedia, SO, GitHub)
PHASE 2 → 🧠 Training 200 epochs dari web data
PHASE 3 → 📱 Telegram loop (auto-reply + scrape)
```

### CLI (PC / Termux)

```bash
git clone https://github.com/dikaofc/dikaai.git
cd dikaai
pip install telethon aiohttp nest_asyncio

# Interactive chat
python main.py

# Single task
python main.py run "fix error di main.py"

# Agent mode
python main.py agent

# Stats
python main.py stats

# Index project untuk RAG
python main.py index
```

---

## 📋 Commands

| Command | Fungsi |
|---------|--------|
| `python main.py` | Interactive chat |
| `python main.py chat` | Interactive chat |
| `python main.py run "task"` | Single task execution |
| `python main.py agent` | Agent mode (continuous coding) |
| `python main.py api` | REST API server |
| `python main.py stats` | Show statistics |
| `python main.py index` | Index project for RAG |

### Chat Commands

| Command | Fungsi |
|---------|--------|
| `/stats` | Show statistics |
| `/memory` | Show coding memory |
| `/clear` | Clear conversation |
| `/help` | Show help |
| `/quit` | Exit |

---

## 📁 Architecture

```
DikaAI/
├── main.py                  ← Clean launcher
├── bot.py                   ← Telegram interface
├── cli.py                   ← CLI interface
├── dashboard.py             ← Local dashboard
├── webscraper.py            ← Web scraper
├── sync_to_redis.py         ← SQLite → Redis sync
│
├── dikaai/                  ← 🧠 AI Engine (canonical)
│   ├── __init__.py          ← Public API (20 exports)
│   ├── config.py            ← Configuration
│   ├── database.py          ← SQLite + Redis
│   ├── engine.py            ← Main brain (pipeline)
│   ├── chat.py              ← Chat interface
│   │
│   ├── model/               ← 🧠 Neural Network
│   │   ├── model.py         ← LSTM (pure Python)
│   │   ├── tokenizer.py     ← Indonesian tokenizer
│   │   └── trainer.py       ← Training pipeline
│   │
│   ├── context/             ← 💬 Topic tracking
│   │   └── tracker.py       ← Anti-drift, hierarchical
│   │
│   ├── memory/              ← 🧠 Memory system
│   │   ├── short_term.py    ← Conversation memory
│   │   └── coding_memory.py ← Error→solution DB
│   │
│   ├── rag/                 ← 📚 Knowledge retrieval
│   │   ├── embeddings.py    ← Text embeddings
│   │   ├── vector_db.py     ← Vector database
│   │   └── retriever.py     ← Knowledge search
│   │
│   ├── agent/               ← 🤖 Coding agent
│   │   ├── planner.py       ← Task breakdown
│   │   └── executor.py      ← Plan→Code→Test→Debug
│   │
│   ├── tools/               ← 🛠️ System tools
│   │   ├── filesystem.py    ← File operations
│   │   ├── terminal.py      ← Command execution
│   │   └── git_tools.py     ← Git operations
│   │
│   └── coding/              ← 🔍 Quality control
│       ├── validator.py     ← Response validation
│       ├── observer.py      ← Execution logging
│       └── smart_reply.py   ← Fallback replies
│
├── server/api.py            ← REST API
├── api/index.py             ← Vercel dashboard
├── data/                    ← Memory, RAG, knowledge
├── model_checkpoints/       ← Model weights
└── colab_simple.py          ← Google Colab runner
```

---

## 🧠 Pipeline

```
User Input
    │
    ▼
┌─────────────────────┐
│   InputProcessor    │ ← language, intent, entities
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   TopicTracker      │ ← detect topic, prevent drift
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   IntentResolver    │ ← "lanjut yang tadi" → understand
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   ContextManager    │ ← hierarchical L0-L5 context
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   Router            │ ← chat/code/reason/search/tool
└──────────┬──────────┘
           │
     ┌─────┼─────┬─────────┐
     ▼     ▼     ▼         ▼
  Memory  RAG  Project   Agent
     │     │     │         │
     └─────┼─────┼─────────┘
           ▼
┌─────────────────────┐
│   Agent             │ ← plan → code → test → debug
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   Model             │ ← LSTM inference
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   Validator         │ ← correctness, relevance, safety
└──────────┬──────────┘
           ▼
       Response
```

---

## 🤖 Usage Examples

### Python API

```python
from dikaai import DikaAIChat

chat = DikaAIChat(workspace="/path/to/project")

# Chat
result = chat.send("halo apa kabar")
print(result['response'])  # "Hei! Ada apa nih?"

# Code task
result = chat.send("fix error di main.py")
print(result['response'])  # Agent: plan → read → fix → test

# Tool
result = chat.send("git status")
print(result['response'])  # Actual git output

# Stats
stats = chat.stats()
print(f"Tasks: {stats['total']}, Success: {stats['rate']}")
```

### Sub-packages

```python
# Model
from dikaai.model import DikaModel, DikaTokenizer
model = DikaModel()
model.load()

# Context
from dikaai.context import ContextManager
ctx = ContextManager()
result = ctx.process_message("lanjut yang tadi")  # Resolves reference

# Agent
from dikaai.agent import Planner, Executor
planner = Planner()
steps = planner.plan("fix authentication bug")

# RAG
from dikaai.rag import Retriever
retriever = Retriever()
retriever.index_directory("/path/to/project")
context = retriever.retrieve("how does auth work?")

# Memory
from dikaai.memory import CodingMemory
memory = CodingMemory()
memory.save_experience("fix import error", success=True, error="ModuleNotFoundError")
solution = memory.find_solution("ModuleNotFoundError: requests")
```

---

## 🤖 Model Info

| Property | Value |
|----------|-------|
| Architecture | LSTM text predictor |
| Embedding | 64 dim |
| Hidden | 128 dim |
| Parameters | ~48,000 |
| Context | 64 tokens |
| Optimizer | Adam (β1=0.9, β2=0.999) |
| LR Schedule | Cosine with warmup |
| Training | Pure Python (no numpy/pytorch) |
| Vocab | Auto-built (2000 tokens max) |

---

## ⚡ Performance

| Metric | Value |
|--------|-------|
| Model size | ~190KB |
| Training speed | ~14 steps/sec |
| Memory usage | < 100MB |
| Pipeline latency | < 0.1s per message |
| Web sources | 4 (Wikipedia, SO, GitHub, Corpus) |
| Telegram concurrent | 15 chats |
| Dashboard refresh | 10 seconds |
| Redis sync | 60 seconds |

---

## 🔗 Links

- **GitHub**: https://github.com/dikaofc/dikaai
- **Dashboard**: https://dikaai.vercel.app
- **Telegram API**: https://my.telegram.org
- **Upstash Redis**: https://upstash.com (free tier)
- **Google Colab**: https://colab.research.google.com/github/dikaofc/dikaai/blob/main/colab_simple.py

---

## 📄 License

MIT License - Free untuk dipakai

---

Made with ❤️ by DikaAI

---

## 🔌 Public API

### Quick Start

```bash
# 1. Start API server
python main.py api

# 2. Create a token
curl -X POST http://localhost:8080/v1/auth/token \
  -H "Authorization: Bearer admin_token" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app", "scopes": ["chat", "agent", "tools"]}'
# → {"token": "dka_xxx...", "name": "my-app", "scopes": [...]}

# 3. Use the API
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer dka_xxx" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "fix error in main.py"}]}'
```

### OpenAI-Compatible Endpoints

```bash
# Chat Completions (compatible with Claude Code, Codex, Pi Agent)
POST /v1/chat/completions
{
  "messages": [{"role": "user", "content": "hello"}]
}

# Completion
POST /v1/completions
{
  "prompt": "write a fibonacci function"
}

# Coding Agent (plan → code → test → debug)
POST /v1/agent
{
  "task": "fix authentication bug",
  "max_retries": 3
}

# List models
GET /v1/models

# Health check
GET /v1/health
```

### Tool Endpoints

```bash
# Read file
POST /v1/tools/read    {"path": "main.py"}

# Write file
POST /v1/tools/write   {"path": "test.py", "content": "print('hello')"}

# Edit file
POST /v1/tools/edit    {"path": "main.py", "old_text": "foo", "new_text": "bar"}

# Search code
POST /v1/tools/search  {"pattern": "def ", "path": "."}

# Run command
POST /v1/tools/run     {"command": "python main.py --test"}

# Git status
GET /v1/tools/git/status
```

### Auth Endpoints

```bash
# Create token
POST /v1/auth/token    {"name": "my-app", "scopes": ["chat", "agent"]}

# List tokens
GET  /v1/auth/tokens

# Revoke token
POST /v1/auth/revoke   {"token": "dka_xxx"}
```

### Connect to Agent CLIs

```bash
# Claude Code
export DIKAAI_API_KEY=dka_xxx
export DIKAAI_BASE_URL=http://localhost:8080/v1

# Codex
export OPENAI_API_BASE=http://localhost:8080/v1
export OPENAI_API_KEY=dka_xxx

# Pi Agent
export PI_API_URL=http://localhost:8080/v1
export PI_API_KEY=dka_xxx
```

### Scopes

| Scope | Access |
|-------|--------|
| `chat` | Chat completions, completions |
| `agent` | Coding agent (plan→code→test→debug) |
| `tools` | File read/write/edit, search, run commands |
| `admin` | Token management, full access |

