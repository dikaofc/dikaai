"""DikaAi Configuration - Auto-detect & Max Performance"""
import os
import json
import multiprocessing
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "dikaai.db"
MODEL_DIR = BASE_DIR / "model_checkpoints"
CONFIG_FILE = BASE_DIR / "config.env"
ENV_LOCAL = BASE_DIR / ".env.local"
VOCAB_FILE = BASE_DIR / "vocab.json"

def load_env():
    # Load config.env
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    key, val = key.strip(), val.strip()
                    if val and not val.startswith('ISI_'):
                        os.environ[key] = val
    # Load .env.local (Redis credentials etc)
    if ENV_LOCAL.exists():
        with open(ENV_LOCAL) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    key, val = key.strip(), val.strip()
                    if val:
                        os.environ[key] = val

load_env()

# ============================================================
# UPSTASH REDIS (for Vercel deployment)
# ============================================================
UPSTASH_REDIS_URL = os.environ.get('UPSTASH_REDIS_REST_URL', '')
UPSTASH_REDIS_TOKEN = os.environ.get('UPSTASH_REDIS_REST_TOKEN', '')
USE_REDIS = bool(UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN)
HISTORY_FILE = BASE_DIR / "training_history.csv"

if USE_REDIS:
    print(f"  [SYS] ✅ Redis connected: {UPSTASH_REDIS_URL[:30]}...")
else:
    print(f"  [SYS] ⚠️  Redis not configured, using local SQLite")

# Telegram
API_ID = int(os.environ.get('TELEGRAM_API_ID', 0))
API_HASH = os.environ.get('TELEGRAM_API_HASH', '')
PHONE = os.environ.get('TELEGRAM_PHONE', '')

# ============================================================
# AUTO-DETECT DEVICE CAPABILITIES
# ============================================================
CPU_CORES = multiprocessing.cpu_count()
# Use 75% of cores for workers (leave headroom)
MAX_WORKERS = max(2, int(CPU_CORES * 0.75))
# Telegram concurrent scrapers (more cores = more concurrent)
TG_CONCURRENT = min(15, CPU_CORES * 2)

print(f"  [SYS] CPU cores: {CPU_CORES} | Workers: {MAX_WORKERS} | TG concurrent: {TG_CONCURRENT}")

# ============================================================
# MODEL - Optimized for speed + quality
# ============================================================
MODEL_NAME = os.environ.get('MODEL_NAME', 'DikaAi')
VOCAB_SIZE = int(os.environ.get('MAX_VOCAB_SIZE', 2000))
EMBED_DIM = int(os.environ.get('EMBEDDING_DIM', 48))
HIDDEN_DIM = int(os.environ.get('HIDDEN_DIM', 96))
CONTEXT_LEN = int(os.environ.get('CONTEXT_LENGTH', 48))
CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', 24))
NUM_LAYERS = 1

# Training - Aggressive for fast convergence
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', MAX_WORKERS * 2))
LR = float(os.environ.get('LEARNING_RATE', 0.003))
LR_MIN = float(os.environ.get('LR_MIN', 0.0005))
LR_WARMUP = int(os.environ.get('LR_WARMUP', 30))
LR_DECAY = int(os.environ.get('LR_DECAY', 300))
TRAIN_INTERVAL = int(os.environ.get('TRAIN_EVERY_SECONDS', 8))  # Faster
MAX_TRAIN_STEPS = int(os.environ.get('MAX_TRAIN_STEPS', 500))
GRAD_ACCUM = int(os.environ.get('GRAD_ACCUM', 4))

# Anti-dupe
MIN_MESSAGE_LEN = 2
MAX_MESSAGE_LEN = 300

# Telegram entities to scrape
TARGET_ENTITIES = [
    e.strip() for e in os.environ.get('TARGET_ENTITIES', '').split(',') if e.strip()
]

# Auto-reply settings
AUTO_REPLY_ENABLED = os.environ.get('AUTO_REPLY', 'true').lower() == 'true'
AUTO_REPLY_DELAY = float(os.environ.get('AUTO_REPLY_DELAY', '1.5'))
AUTO_REPLY_MIN_LEN = int(os.environ.get('AUTO_REPLY_MIN_LEN', 20))
