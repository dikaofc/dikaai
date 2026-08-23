# 🧠 DikaAi - Ultra Lightweight AI Personal Assistant

**Paling Ringan Sedunia 🚀** - AI yang belajar dari chat Telegram + web scraping

## Features

- 🌐 **Web Scraping** - Belajar dari Wikipedia, StackOverflow, GitHub
- 📱 **Telegram Bot** - Auto-reply + scrape chat 24/7
- 🧠 **Training** - Model LSTM belajar otomatis
- 📊 **Dashboard** - Web UI monitoring + chat
- 🔴 **Redis Sync** - Data ter-sync ke Vercel

---

## 🚀 Cara Run di Google Colab (Paling Gampang)

### 1. Buka Colab

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/dikaofc/dikaai/blob/main/colab_simple.py)

Atau manual: https://colab.research.google.com

### 2. Copy `colab_simple.py`

Buka file [`colab_simple.py`](colab_simple.py), copy SEMUA isinya.

### 3. Paste ke Colab → Ganti Config → Run!

```python
# Ganti 5 baris ini:
TELEGRAM_API_ID = 12345678                # dari my.telegram.org
TELEGRAM_API_HASH = "abc123def456"        # dari my.telegram.org
TELEGRAM_PHONE = "+628123456789"          # nomor HP kamu
UPSTASH_REDIS_URL = ""                     # optional: https://xxx.upstash.io
UPSTASH_REDIS_TOKEN = ""                   # optional: AXxx...
```

Lalu klik **▶ Run**. Selesai!

### Apa yang Terjadi?

```
1. 🌐 Web scrape → Wikipedia, StackOverflow, GitHub
2. 📖 Build vocab dari semua data
3. 🧠 Training model otomatis
4. 📱 Connect Telegram → auto-reply + scrape chat
5. 🔄 Re-scrape tiap 6 jam
6. ⏱️ Auto-stop setelah 12 jam
```

---

## 📱 Cara Run di Termux (Android)

```bash
# Install
pkg install python git
pip install telethon aiohttp

# Clone
git clone https://github.com/dikaofc/dikaai.git
cd dikaai

# Setup config
nano config.env
# Isi:
# TELEGRAM_API_ID=12345678
# TELEGRAM_API_HASH=abc123def456
# TELEGRAM_PHONE=+628123456789

# Run
python main.py
```

---

## 💻 Cara Run di PC/Laptop

```bash
git clone https://github.com/dikaofc/dikaai.git
cd dikaai
pip install telethon aiohttp

# Setup
cp config.env.example config.env
nano config.env

# Run
python main.py
```

---

## 🌐 Deploy ke Vercel (Dashboard)

1. Buka https://vercel.com → Import `dikaofc/dikaai`
2. Set env vars di **Settings**:
   - `UPSTASH_REDIS_REST_URL` = URL dari Upstash
   - `UPSTASH_REDIS_REST_TOKEN` = Token dari Upstash
3. Deploy → Dashboard aktif!

---

## 📋 Commands

| Command | Fungsi |
|---------|--------|
| `python main.py` | Jalankan semua |
| `python main.py scrape` | Scrape Telegram saja |
| `python main.py train` | Training saja |
| `python main.py chat` | Chat interaktif |
| `python main.py stats` | Lihat statistik |

---

## 📁 Structure

```
dikaai/
├── main.py              # Entry point
├── config.py            # Configuration
├── database.py          # SQLite + Redis hybrid
├── model.py             # LSTM model (pure Python)
├── tokenizer.py         # Indonesian tokenizer
├── trainer.py           # Auto training
├── bot.py               # Telegram bot
├── webscraper.py        # Web scraper
├── dashboard.py         # Local dashboard
├── sync_to_redis.py     # SQLite → Redis sync
├── api/index.py         # Vercel dashboard
├── colab_simple.py      # ⭐ Google Colab runner
├── vercel.json          # Vercel config
├── model_checkpoints/   # Model weights
└── training_history.csv # Loss history
```

---

## 🔗 Links

- **GitHub**: https://github.com/dikaofc/dikaai
- **Telegram API**: https://my.telegram.org
- **Upstash Redis**: https://upstash.com (free tier)

---

Made with ❤️ by DikaAi
