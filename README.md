# 🧠 DikaAi - Ultra Lightweight AI Personal Assistant

**Paling Ringan Sedunia 🚀** - AI Indonesia yang belajar dari chat Telegram + web scraping

> 100% otomatis. Sekali jalan, langsung kerja. Web scrape → Training → Telegram auto-reply → Dashboard monitoring.

---

## ✨ Features

### 🌐 Web Scraping (Prioritas)
- **Wikipedia Indonesia** - 70+ articles (teknologi, programming, AI, dll)
- **StackOverflow** - Q&A programming
- **GitHub** - Trending repos + README
- **Indonesian Corpus** - 100+ phrases (casual, tech, bisnis)

### 🧠 Training (Auto)
- **200 epochs** web data training sebelum Telegram
- **32 pairs/epoch** (batch size lebih gede)
- **LSTM model** 48K params (pure Python, no numpy)
- **Adam optimizer** + cosine LR scheduler
- **Loss turun** dari 2.0 → 0.12 dalam 7000+ steps

### 📱 Telegram Bot
- **Auto-reply** cerdas (100+ pola Indonesian)
- **Scrape semua chat** (private, group, channel)
- **Parallel scraping** (15 concurrent)
- **Real-time listener** + auto-reply

### 📊 Dashboard
- **Vercel** - Web UI monitoring (auto-refresh 10s)
- **Loss chart** - Grafik training real-time
- **Controls** - Toggle on/off fitur
- **Chat** - Web chat dengan AI
- **CSV export** - Download training data

### 🔴 Redis Sync
- **Auto-sync** SQLite → Upstash Redis tiap 60 detik
- **Dashboard Vercel** always updated
- **Hybrid mode** - SQLite (training) + Redis (Vercel)

---

## 🚀 Cara Run

### Google Colab (Paling Gampang!)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/dikaofc/dikaai/blob/main/colab_simple.py)

```python
# 1. Buka Colab
# 2. Paste colab_simple.py
# 3. Ganti 5 config ini:
TELEGRAM_API_ID = 12345678        # dari my.telegram.org
TELEGRAM_API_HASH = "abc123def456"
TELEGRAM_PHONE = "+628123456789"
UPSTASH_REDIS_URL = "https://xxx.upstash.io"   # dari upstash.com
UPSTASH_REDIS_TOKEN = "AXxx..."
# 4. Run!
```

**Flow otomatis:**
```
PHASE 1 → 🌐 Web scrape (Wikipedia, SO, GitHub)
PHASE 2 → 🧠 Training 200 epochs dari web data
PHASE 3 → 📱 Telegram loop (auto-reply + scrape)
⏱️ Auto-stop: 12 jam
```

### Termux (Android)

```bash
pkg install python git
pip install telethon aiohttp nest_asyncio
git clone https://github.com/dikaofc/dikaai.git
cd dikaai
nano config.env  # Isi API credentials
python main.py
```

### PC / Laptop

```bash
git clone https://github.com/dikaofc/dikaai.git
cd dikaai
pip install telethon aiohttp nest_asyncio
cp config.env.example config.env
nano config.env
python main.py
```

### Vercel (Dashboard Only)

```bash
# 1. Import repo ke Vercel
# 2. Set env vars:
#    UPSTASH_REDIS_REST_URL = https://xxx.upstash.io
#    UPSTASH_REDIS_REST_TOKEN = AXxx...
# 3. Deploy
```

---

## 📋 Commands

| Command | Fungsi |
|---------|--------|
| `python main.py` | Jalankan semua (scrape + train + bot) |
| `python main.py scrape` | Scrape Telegram saja |
| `python main.py train` | Training saja |
| `python main.py chat` | Chat interaktif dengan AI |
| `python main.py stats` | Lihat statistik |
| `python main.py dashboard` | Dashboard web saja |

---

## 📁 Project Structure

```
dikaai/
├── main.py              # Entry point - jalankan semua
├── config.py            # Configuration (auto-detect device)
├── database.py          # SQLite + Redis hybrid database
├── model.py             # LSTM model (pure Python, 48K params)
├── tokenizer.py         # Indonesian text tokenizer (slang-aware)
├── trainer.py           # Auto training (200 epochs web data)
├── bot.py               # Telegram bot + scraper (parallel)
├── webscraper.py        # Web scraper (Wikipedia, SO, GitHub)
├── smart_reply.py       # 100+ Indonesian reply patterns
├── dashboard.py         # Local web dashboard (port 8888)
├── sync_to_redis.py     # SQLite → Upstash Redis sync
├── api/index.py         # Vercel serverless dashboard
├── colab_simple.py      # ⭐ Google Colab runner (1 cell)
├── colab_run.ipynb      # Colab notebook
├── vercel.json          # Vercel config
├── model_checkpoints/   # Model weights
│   └── dikaai_latest.json
├── vocab.json           # Vocabulary (auto-built)
└── training_history.csv # Loss history
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
| Vocab | Auto-built from messages (2000 max) |

---

## 🧠 Smart Reply System

Bot reply **natural & nyambung** ke 15+ topik:

| Topik | Contoh |
|-------|--------|
| Greeting | "halo" → "Hei! Ada apa nih?" 😊 |
| Tech | "error dong" → "Coba print dulu datanya!" 🧑‍💻 |
| Casual | "lagi apa" → "Lagi ngoding nih!" 😄 |
| Emotions | "sedih banget" → "Sabar ya! 💪" |
| Food | "kopi enak ga" → "Jangan lupa makan ya!" 🍚 |
| Sports | "main bola" → "Tim mana yang kamu suka?" ⚽ |
| Anime | "anime apa" → "Solo Leveling lagi hype!" 🎌 |
| Phone | "HP baru" → "iPhone atau Android?" 📱 |
| Music | "dengerin musik" → "Genre apa yang kamu suka?" 🎵 |
| Help | "tolong dong" → "Siap! Ceritain aja!" 🙌 |
| Thanks | "makasih" → "Sama-sama! 😊" |
| Bye | "dah" → "Hati-hati ya! 👋" |
| Relationship | "jomblo" → "Single itu enak, bebas! 🔥" |
| Religion | "sholat" → "Jangan lupa sholat 5 waktu! 🤲" |
| Money | "gaji" → "Semangat kerja! 💪" |

**Garbage detection:** Bot deteksi output sampah (repetisi, echo, karakter acak) → auto fallback ke smart reply.

---

## ⚡ Performance

| Metric | Value |
|--------|-------|
| Model size | ~190KB |
| Training speed | ~14 steps/sec |
| Memory usage | < 100MB |
| Vocab size | 2000 tokens |
| Web sources | 4 (Wikipedia, SO, GitHub, Corpus) |
| Telegram concurrent | 15 chats |
| Dashboard refresh | 10 seconds |
| Redis sync | 60 seconds |
| Auto-stop | 12 jam (Colab) |

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

Made with ❤️ by DikaAi
