# 🧠 DikaAi - Ultra Lightweight AI Personal Assistant

**Paling Ringan Sedunia 🚀** - AI yang belajar dari chat Telegram + web scraping

## Features

- 🌐 **Web Scraping** - Belajar dari Wikipedia, StackOverflow, GitHub
- 📱 **Telegram Bot** - Auto-reply + scrape chat 24/7
- 🧠 **Training** - Model LSTM belajar otomatis
- 📊 **Dashboard** - Web UI monitoring + chat
- 🔴 **Redis Sync** - Data ter-sync ke Vercel

---

## 🚀 Cara Run di Google Colab

### Step 1: Buka Google Colab

Klik link ini untuk buka Colab langsung:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/dikaofc/dikaai/blob/main/colab_run.ipynb)

Atau buka manual: https://colab.research.google.com

### Step 2: Copy-Paste Script Ini ke Colab

Buat cell baru di Colab, paste script di bawah, lalu **Run All**:

```python
# ============================================================
# DikaAi - Google Colab Setup
# Jalankan cell ini untuk setup otomatis
# ============================================================

# 1. Clone repo
!git clone https://github.com/dikaofc/dikaai.git
%cd dikaai

# 2. Install dependencies
!pip install telethon aiohttp -q

# 3. Setup Telegram API (ISI DATA KAMU)
# Dapat dari https://my.telegram.org
import os
os.environ['TELEGRAM_API_ID'] = 'ISI_API_ID_KAMU'       # Contoh: 12345678
os.environ['TELEGRAM_API_HASH'] = 'ISI_API_HASH_KAMU'   # Contoh: abc123def456
os.environ['TELEGRAM_PHONE'] = 'ISI_NO_HP_KAMU'         # Contoh: +628123456789

# 4. Setup Upstash Redis (Optional - untuk Vercel dashboard)
# Daftar gratis di https://upstash.com
# os.environ['UPSTASH_REDIS_REST_URL'] = 'https://xxx.upstash.io'
# os.environ['UPSTASH_REDIS_REST_TOKEN'] = 'AXXXxxx...'

# 5. Run DikaAi (Web Scrape + Training otomatis)
!python main.py
```

### Step 3: Login Telegram

Setelah script jalan, Colab akan minta **kode verifikasi Telegram**. Cek HP kamu, masukkan kode-nya.

---

## 📋 Cara Run di Termux (Android)

### Install

```bash
# Install Python + Git
pkg install python git

# Clone repo
git clone https://github.com/dikaofc/dikaai.git
cd dikaai

# Install dependencies
pip install telethon aiohttp
```

### Setup Config

Buat file `config.env`:

```bash
nano config.env
```

Isi:

```
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abc123def456
TELEGRAM_PHONE=+628123456789
```

> **Cara dapat API_ID & API_HASH:**
> 1. Buka https://my.telegram.org
> 2. Login pakai nomor HP
> 3. Klik "API development tools"
> 4. Isi form, dapat API_ID dan API_HASH

### Run

```bash
python main.py
```

---

## 📋 Cara Run di PC/Laptop

```bash
# Clone
git clone https://github.com/dikaofc/dikaai.git
cd dikaai

# Install
pip install telethon aiohttp

# Setup config
cp config.env.example config.env
nano config.env  # Isi API credentials

# Run
python main.py
```

---

## 🌐 Deploy ke Vercel

1. Push repo ke GitHub (sudah public di `dikaofc/dikaai`)
2. Buka https://vercel.com
3. Import repo `dikaofc/dikaai`
4. Deploy otomatis
5. Set environment variables di **Settings**:
   - `UPSTASH_REDIS_REST_URL` = URL dari Upstash
   - `UPSTASH_REDIS_REST_TOKEN` = Token dari Upstash

---

## 📊 Commands

| Command | Fungsi |
|---------|--------|
| `python main.py` | Jalankan semua (scrape + train + bot) |
| `python main.py scrape` | Scrape Telegram saja |
| `python main.py train` | Training saja |
| `python main.py chat` | Chat interaktif dengan AI |
| `python main.py stats` | Lihat statistik |
| `python main.py dashboard` | Dashboard web saja |

---

## 📁 Structure

```
dikaai/
├── main.py              # Entry point - jalankan semua
├── config.py            # Configuration
├── database.py          # SQLite + Redis hybrid
├── model.py             # LSTM model (pure Python)
├── tokenizer.py         # Indonesian text tokenizer
├── trainer.py           # Auto training loop
├── bot.py               # Telegram bot + scraper
├── webscraper.py        # Web scraper (Wikipedia, SO, GitHub)
├── dashboard.py         # Local web dashboard
├── sync_to_redis.py     # Sync SQLite → Redis
├── api/index.py         # Vercel serverless dashboard
├── vercel.json          # Vercel config
├── vocab.json           # Vocabulary
├── model_checkpoints/   # Model weights
│   └── dikaai_latest.json
└── training_history.csv # Training loss history
```

---

## 🤖 Model Info

- **Architecture**: LSTM text predictor
- **Parameters**: ~32K (ultra lightweight)
- **Training**: Pure Python (no numpy/pytorch needed)
- **Vocab**: Auto-built from messages
- **Context**: 48 tokens

---

## ⚡ Performance

| Metric | Value |
|--------|-------|
| Model size | ~125KB |
| Training speed | ~14 steps/sec |
| Memory usage | < 100MB |
| Runs on | Phone, Laptop, Colab, Vercel |

---

## 📄 License

MIT License - Free untuk dipakai

---

## 🔗 Links

- **GitHub**: https://github.com/dikaofc/dikaai
- **Vercel Dashboard**: (deploy sendiri)
- **Telegram API**: https://my.telegram.org
- **Upstash Redis**: https://upstash.com

---

Made with ❤️ by DikaAi
