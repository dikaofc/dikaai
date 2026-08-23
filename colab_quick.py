#!/usr/bin/env python3
"""
DikaAi - Quick Colab Script (Copy-Paste Satu Cell)
"""

# ============================================
# STEP 1: Install + Clone
# ============================================
!pip install telethon aiohttp -q
!git clone https://github.com/dikaofc/dikaai.git /content/dikaai
%cd /content/dikaai

# ============================================
# STEP 2: Config (GANTI INI!)
# ============================================
TELEGRAM_API_ID = 12345678        # Ganti!
TELEGRAM_API_HASH = "abc123def456" # Ganti!
TELEGRAM_PHONE = "+628123456789"   # Ganti!
UPSTASH_REDIS_URL = "https://xxx.upstash.io"  # Ganti!
UPSTASH_REDIS_TOKEN = "AXxx..."               # Ganti!

# Simpan config
with open('config.env', 'w') as f:
    f.write(f'''TELEGRAM_API_ID={TELEGRAM_API_ID}
TELEGRAM_API_HASH={TELEGRAM_API_HASH}
TELEGRAM_PHONE={TELEGRAM_PHONE}
UPSTASH_REDIS_REST_URL={UPSTASH_REDIS_URL}
UPSTASH_REDIS_REST_TOKEN={UPSTASH_REDIS_TOKEN}
''')

print("✅ Config saved!")

# ============================================
# STEP 3: Run!
# ============================================
exec(open('colab_runner.py').read())
