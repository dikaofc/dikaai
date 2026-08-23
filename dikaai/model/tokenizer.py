"""DikaAi Tokenizer - Optimized for Indonesian chat

Features:
- Handles Indonesian slang/abbreviations
- Filters noise (bot notifications, spam)
- Better tokenization for informal text
"""
import json
import re
from collections import Counter
from pathlib import Path
from dikaai.config import VOCAB_SIZE, VOCAB_FILE

PAD_TOKEN = '<pad>'
UNK_TOKEN = '<unk>'
BOS_TOKEN = '<bos>'
EOS_TOKEN = '<eos>'
SEP_TOKEN = '<sep>'

SPECIAL_TOKENS = [PAD_TOKEN, UNK_TOKEN, BOS_TOKEN, EOS_TOKEN, SEP_TOKEN]

# Indonesian slang/abbreviation dictionary
SLANG_MAP = {
    'gw': 'aku', 'gue': 'aku', 'gw': 'aku',
    'lo': 'kamu', 'lu': 'kamu', 'loe': 'kamu',
    'bg': 'bang', 'br': 'bang', 'bro': 'bang',
    'sis': 'sis', 'sis': 'sis',
    'yg': 'yang', 'yng': 'yang',
    'dgn': 'dengan', 'dngn': 'dengan',
    'utk': 'untuk', 'buat': 'untuk',
    'dr': 'dari', 'dri': 'dari',
    'aja': 'saja', 'aj': 'saja',
    'bgt': 'banget', 'bngt': 'banget',
    'knp': 'kenapa', 'kp': 'kenapa',
    'gmn': 'gimana', 'gmna': 'gimana',
    'udh': 'sudah', 'udah': 'sudah', 'sdh': 'sudah',
    'blm': 'belum', 'blom': 'belum',
    'lg': 'lagi', 'lgi': 'lagi',
    'tuh': 'itu', 'tdk': 'tidak', 'gak': 'tidak', 'gk': 'tidak',
    'bisa': 'bisa', 'bs': 'bisa',
    'mau': 'mau', 'mw': 'mau',
    'nih': 'nih', 'nih': 'nih',
    'dong': 'dong', 'dh': 'dong',
    'sih': 'sih', 'sh': 'sih',
    'kok': 'kok', 'ko': 'kok',
    'deh': 'deh', 'dah': 'deh',
    'yah': 'ya', 'y': 'ya',
    'ok': 'oke', 'okk': 'oke',
    'thx': 'thanks', 'ty': 'thanks',
    'pls': 'please', 'plis': 'please',
    'idk': 'nggak tahu',
    'om': 'om', 'tante': 'tante',
    'sekali': 'sekali', 'skli': 'sekali',
    'banget': 'banget', 'bgt': 'banget',
    'emang': 'memang', 'emg': 'memang',
    'gini': 'begini', 'kayak': 'seperti',
    'kaya': 'seperti', 'sprti': 'seperti',
    'bener': 'benar', 'bnr': 'benar',
    'banyak': 'banyak', 'byk': 'banyak',
    'suka': 'suka', 'suk': 'suka',
    'maaf': 'maaf', 'mf': 'maaf',
    'haha': 'haha', 'wkwk': 'wkwk', 'wk': 'wkwk',
    'mantap': 'mantap', 'mntp': 'mantap',
    'sip': 'sip', 'sipp': 'sip',
    'gas': 'gas', 'gass': 'gas',
    'oke': 'oke', 'ok': 'oke',
    'siap': 'siap', 'sipp': 'siap',
}

# Noise patterns to filter out
NOISE_PATTERNS = [
    r'^@\w+bot\b',           # Bot mentions
    r'^https?://',           # Links
    r'^t\.me/',              # Telegram links
    r'荥|✨|🎬|🆕|🔞',       # Bot emojis
    r'ᴠɪᴅᴇᴏ|ʜᴅ|ɴᴇᴡ|ᴜᴘᴅᴀᴛᴇ',  # Bot text (fancy unicode)
    r'ᴀsᴜᴘᴀɴ|ᴛᴇʀʙᴀᴜ!|ʙᴀʀᴜ',
    r'\*\*\[',               # Bot formatting
    r'github\)',             # Bot patterns
    r'status:\*\*',
    r'sɪʟᴀʜᴋᴀɴ|ᴋʟɪᴋ|ᴛᴏᴍʙᴏʟ',
    r'ᴅɪ|ʙᴀᴡᴀʜ|ᴜɴᴛᴜᴋ|ᴍᴇɴᴏɴᴛᴏɴ',
]


def _is_indonesian(text):
    """Check if text is likely Indonesian."""
    text_lower = text.lower().split()
    indo_words = {'yang', 'dan', 'ini', 'itu', 'untuk', 'dengan', 'tidak', 'ada',
                  'bisa', 'saya', 'kamu', 'dia', 'mereka', 'akan', 'sudah',
                  'belum', 'lagi', 'mau', 'halo', 'kabar', 'apa', 'siapa',
                  'kenapa', 'gimana', 'kapan', 'dimana', 'sih', 'dong', 'nih',
                  'deh', 'lah', 'kok', 'aja', 'banget', 'mantap', 'sip', 'oke',
                  'gas', 'bro', 'bang', 'bg', 'gw', 'gu', 'lu', 'lo', 'bgst',
                  'anjing', 'bangsat', 'kontol', 'memek', 'kntl', 'mmk'}
    count = sum(1 for w in text_lower if w in indo_words)
    return count >= 1


def _is_noise(text):
    """Check if message is bot/spam noise."""
    text_lower = text.lower().strip()
    if len(text_lower) < 3:
        return True
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    # Bot notification pattern: starts with @ and contains "bot"
    if re.match(r'^@\w*bot', text_lower):
        return True
    return False


def _normalize_indonesian(text):
    """Normalize Indonesian text (slang → formal)."""
    words = text.split()
    normalized = []
    for word in words:
        w_lower = word.lower()
        if w_lower in SLANG_MAP:
            normalized.append(SLANG_MAP[w_lower])
        else:
            normalized.append(word)
    return ' '.join(normalized)


class DikaTokenizer:
    def __init__(self):
        self.word2idx = {}
        self.idx2word = {}
        self.vocab_size = 0
        self._loaded = False

    def build_vocab(self, texts: list):
        """Build vocabulary from list of texts."""
        counter = Counter()

        for text in texts:
            # Filter noise
            if _is_noise(text):
                continue

            # Normalize Indonesian
            text = _normalize_indonesian(text)

            tokens = self._tokenize(text)
            counter.update(tokens)

        most_common = counter.most_common(VOCAB_SIZE - len(SPECIAL_TOKENS))

        self.word2idx = {t: i for i, t in enumerate(SPECIAL_TOKENS)}
        self.idx2word = {i: t for t, i in self.word2idx.items()}

        for word, _ in most_common:
            idx = len(self.word2idx)
            self.word2idx[word] = idx
            self.idx2word[idx] = word

        self.vocab_size = len(self.word2idx)
        self._loaded = True

    def _tokenize(self, text: str) -> list:
        """Tokenization optimized for Indonesian chat."""
        text = text.lower().strip()
        # Split: words and individual punctuation
        tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
        return tokens

    def encode(self, text: str, max_length: int = None) -> list:
        """Encode text to token indices."""
        # Normalize Indonesian
        text = _normalize_indonesian(text)

        tokens = self._tokenize(text)
        indices = [self.word2idx.get(t, self.word2idx[UNK_TOKEN]) for t in tokens]

        if max_length:
            indices = indices[:max_length]
            while len(indices) < max_length:
                indices.append(self.word2idx[PAD_TOKEN])

        return indices

    def decode(self, indices: list) -> str:
        """Decode token indices back to text."""
        words = []
        for idx in indices:
            if isinstance(idx, (list, tuple)):
                idx = idx[0]
            idx = int(idx)
            if idx in (self.word2idx.get(PAD_TOKEN, 0), self.word2idx.get(EOS_TOKEN, 0)):
                continue
            if idx == self.word2idx.get(BOS_TOKEN, 0):
                continue
            word = self.idx2word.get(idx, UNK_TOKEN)
            if word not in SPECIAL_TOKENS:
                words.append(word)
        return ' '.join(words)

    def save(self):
        """Save vocab to file."""
        data = {
            'word2idx': self.word2idx,
            'vocab_size': self.vocab_size
        }
        with open(VOCAB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self) -> bool:
        """Load vocab from file. Returns False if not found."""
        if not VOCAB_FILE.exists():
            return False

        try:
            with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.word2idx = data['word2idx']
            self.idx2word = {int(v): k for k, v in self.word2idx.items()}
            self.vocab_size = data['vocab_size']
            self._loaded = True
            return True
        except Exception:
            return False

    def __len__(self):
        return self.vocab_size
