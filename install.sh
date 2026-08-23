#!/bin/bash
# DikaAi Installer - Setup di Termux/Android
set -e

echo "========================================="
echo "  DikaAi - Ultra Light AI Installer"
echo "  Paling Ringan Sedunia 🚀"
echo "========================================="
echo ""

# Check if in Termux
if command -v pkg &> /dev/null; then
    echo "[1/5] Installing Termux packages..."
    pkg update -y
    pkg install -y python termux-api
else
    echo "[1/5] Not in Termux, skipping pkg install"
fi

echo "[2/5] Creating virtual environment..."
python -m venv venv 2>/dev/null || python3 -m venv venv
source venv/bin/activate

echo "[3/5] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/5] Setting up config..."
if [ ! -f config.env ]; then
    cat > config.env << 'ENVEOF'
# DikaAi Configuration
# ====================
# Isi dengan data Telegram kamu dari https://my.telegram.org

TELEGRAM_API_ID=ISI_API_ID_DI_SINI
TELEGRAM_API_HASH=ISI_API_HASH_DI_SINI
TELEGRAM_PHONE=+62XXXXXXXXXXX

# Model Settings (paling ringan!)
MODEL_NAME=DikaAi
MAX_VOCAB_SIZE=5000
EMBEDDING_DIM=48
HIDDEN_DIM=96
CONTEXT_LENGTH=32

# Training Settings
BATCH_SIZE=4
LEARNING_RATE=0.002
TRAIN_EVERY_SECONDS=15
MAX_TRAIN_STEPS=200

# Auto-reply (balas otomatis di chat)
AUTO_REPLY=true
AUTO_REPLY_DELAY=1.5
AUTO_REPLY_MIN_LEN=20

# Channels/Groups to scrape (comma separated, leave empty for all)
# Contoh: -1001234567890,channelname
TARGET_ENTITIES=
ENVEOF
    echo "  -> config.env created! Edit with your Telegram API credentials."
else
    echo "  -> config.env already exists, skipping."
fi

echo "[5/5] Setup complete!"
echo ""
echo "========================================="
echo "  Next steps:"
echo "  1. Edit config.env with your API credentials"
echo "  2. source venv/bin/activate"
echo "  3. python main.py"
echo "========================================="
