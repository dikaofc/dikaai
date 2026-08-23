"""DikaAi Smart Reply - Fallback system when model output is garbage"""
import random
import re

# ============================================================
# SMART REPLIES - Indonesian conversational patterns
# ============================================================

GREETINGS = {
    'pattern': r'\b(halo|hai|hi|hey|yo|pagi|siang|sore|malam|assalam|assalamualaikum|oke|ok)\b',
    'replies': [
        'Halo! Ada yang bisa dibantu? 😊',
        'Hai! Apa kabar? 🙌',
        'Oke, ada apa nih?',
        'Halo juga! Mau ngobrol apa?',
        'Hey! Ada yang perlu?',
        'Pagi! Semangat ya hari ini 💪',
        'Siang! Lagi sibuk ga?',
        'Sore! Gimana harinya?',
        'Malam! Udah istirahat belum?',
    ]
}

QUESTIONS = {
    'pattern': r'\b(gimana|bagaimana|gmn|kenapa|knp|apa|siapa|dimana|dmna|kapan|kp|berapa)\b',
    'replies': [
        'Hmm, menurutku sih oke-oke aja',
        'Wah, pertanyaan bagus tuh!',
        'Bisa dijelasin lebih detail?',
        'Hm, aku juga lagi mikir tentang itu',
        'Kalau menurutku, tergantung situasinya sih',
        'Good question! Aku belum tau pasti, tapi coba search aja ya',
    ]
}

AGREEMENT = {
    'pattern': r'\b(setuju|bener|betul|iya|benar|mantap|oke|sip|gas|bagus|keren|ok)\b',
    'replies': [
        'Iya bener banget! 👍',
        'Setuju! Mantap jiwa 🔥',
        'Gas! Kita gas bareng 🚀',
        'Oke siap!',
        'Betul tuh!',
        'Mantap, lanjut!',
    ]
}

TECH = {
    'pattern': r'\b(python|javascript|coding|program|code|bug|error|deploy|server|database|api|react|node|docker|linux)\b',
    'replies': [
        'Wah, lagi bahas coding ya! Aku juga suka coding 🧑‍💻',
        'Coding emang seru tapi kadang bikin pusing ya 😅',
        'Error lagi? Coba print dulu datanya, biasanya ketemu',
        'Deploy ke mana? Vercel gampang banget lho',
        'Python atau JavaScript nih? Dua-duanya oke sih',
        'Bug itu teman developer, hadapi aja 💪',
        'Stack overflow solusinya selalu haha',
    ]
}

CASUAL = {
    'pattern': r'\b(lagi apa|lagi sibuk|udah makan|mau kemana|weekend|nonton|game|anime|film)\b',
    'replies': [
        'Lagi ngoding nih, hobi banget 😄',
        'Udah dong! Kamu gimana?',
        'Weekend enaknya santai aja sih',
        'Nonton apa? Kasih rekomendasi dong!',
        'Game apa yang lagi dimainkan?',
        'Anime apa yang lagi hot?',
    ]
}

THANKS = {
    'pattern': r'\b(makasih|terima kasih|thanks|thx|ty|mantap)\b',
    'replies': [
        'Sama-sama! 😊',
        'Santai aja, glad to help!',
        'No problem! 👍',
        'Anytime! 🙌',
    ]
}

NEGATIVE = {
    'pattern': r'\b(sedih|galau|kesel|dongkol|benci|maaf|sorry|error|bug|parah|jelek)\b',
    'replies': [
        'Sabar ya, pasti ada jalan keluarnya 💪',
        'Tenang, semua pasti berlalu!',
        'Aku di sini kalau mau cerita 😊',
        'Gapapa, yang penting terus semangat!',
        'Eh jangan sedih dong, ada aku nih!',
    ]
}

# ============================================================
# PATTERN LIST (order matters - most specific first)
# ============================================================

PATTERNS = [TECH, QUESTIONS, GREETINGS, AGREEMENT, CASUAL, THANKS, NEGATIVE]


def _is_garbage(text):
    """Check if model output is garbage/unusable."""
    if not text or len(text.strip()) < 2:
        return True
    text = text.strip().lower()
    if len(text) < 5:
        return True
    # Just punctuation/symbols
    if re.match(r'^[\s\W]+$', text):
        return True
    words = text.split()
    # Too few unique words
    if len(words) > 1:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.5:  # More than 50% repeated
            return True
    # Single repeated character or very few chars
    chars = text.replace(' ', '')
    if len(set(chars)) <= 2:
        return True
    # Repeated pattern (us us hc us hc)
    if len(words) >= 4:
        # Check if pattern repeats
        for window in range(1, len(words) // 2 + 1):
            pattern = words[:window]
            is_repeated = True
            for i in range(window, len(words), window):
                chunk = words[i:i+window]
                if chunk != pattern[:len(chunk)]:
                    is_repeated = False
                    break
            if is_repeated and window <= 3:
                return True
    # No vowels (likely garbled text)
    vowels = set('aeiou')
    if not any(c in vowels for c in chars):
        return True
    return False


def _echo_check(reply, user_msg):
    """Check if reply is just echoing the user message."""
    if not reply or not user_msg:
        return False
    r = reply.strip().lower()
    u = user_msg.strip().lower()
    # Exact match
    if r == u:
        return True
    # Reply contains 80%+ of user message
    if len(u) > 5 and u in r and len(r) < len(u) * 1.5:
        return True
    return False


def get_smart_reply(user_msg, model_reply=None):
    """Get a smart reply. Falls back to pattern matching if model output is garbage."""
    # First: try model reply
    if model_reply and not _is_garbage(model_reply) and not _echo_check(model_reply, user_msg):
        return model_reply

    # Second: pattern matching fallback
    text_lower = user_msg.lower()
    for pattern_group in PATTERNS:
        if re.search(pattern_group['pattern'], text_lower):
            return random.choice(pattern_group['replies'])

    # Third: generic fallback
    fallbacks = [
        'Hmm, menarik juga tuh! 🤔',
        'Oke, aku catet ya!',
        'Wah, bisa dijelasin lagi?',
        'Noted! Ada lagi?',
        'Interesting! Tell me more',
        'Aku masih belajar nih, tapi semoga bisa bantu!',
        'Hm, aku belum paham banget, tapi nice!',
    ]
    return random.choice(fallbacks)
