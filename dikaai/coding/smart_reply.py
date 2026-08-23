"""DikaAi Smart Reply - Fallback system when model output is garbage
100+ Indonesian conversational patterns for natural replies."""
import random
import re
import hashlib

# ============================================================
# GARBAGE DETECTION
# ============================================================

def _is_garbage(text):
    """Check if model output is garbage/unusable."""
    if not text or len(text.strip()) < 2:
        return True
    text = text.strip().lower()
    if len(text) < 5:
        return True
    if re.match(r'^[\s\W]+$', text):
        return True
    words = text.split()
    chars = text.replace(' ', '')
    # Too few unique chars (e.g. 'us us hc hc')
    if len(set(chars)) <= 3:
        return True
    # Very few unique words
    if len(words) > 1:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.5:
            return True
    # Repeated pattern (any window)
    if len(words) >= 4:
        for window in range(1, min(5, len(words) // 2 + 1)):
            pattern = words[:window]
            matches = sum(1 for i in range(0, len(words) - window + 1, window)
                         if words[i:i+window] == pattern)
            if matches >= 2:
                return True
    # Bigram repetition (us us hc hc -> us hc repeats)
    if len(words) >= 4:
        bigrams = [f'{words[i]}_{words[i+1]}' for i in range(0, len(words)-1, 2)]
        if len(set(bigrams)) <= 1 and len(bigrams) >= 2:
            return True
    vowels = set('aeiou')
    if not any(c in vowels for c in chars):
        return True
    return False

def _echo_check(reply, user_msg):
    """Check if reply echoes the user message."""
    if not reply or not user_msg:
        return False
    r = reply.strip().lower()
    u = user_msg.strip().lower()
    if r == u:
        return True
    if len(u) > 5 and u in r and len(r) < len(u) * 1.5:
        return True
    return False

# ============================================================
# CONVERSATIONAL PATTERNS (100+ replies)
# ============================================================

PATTERNS = [
    # === GREETINGS ===
    {
        'pattern': r'^(halo|hai|hi|hey|yo|hp|heh|heii|heloo|hellou|haloo|hayo|hay|oy|oi)\b',
        'replies': [
            'Halo juga! 😊 Ada apa nih?',
            'Hai! Apa kabar? 🙌',
            'Hey! Ada yang perlu?',
            'Yo! Mau ngobrol apa?',
            'Halo! Seneng bisa ngobrol sama kamu 😄',
            'Hay! Lagi sibuk ga?',
            'Hei! Ada apa nih?',
            'Halo~ Ada yang bisa dibantu?',
        ]
    },
    # === TIME-BASED GREETINGS ===
    {
        'pattern': r'\b(pagi|siang|sore|malam)\b',
        'replies': [
            'Selamat pagi! Semangat ya hari ini 💪',
            'Siang! Udah makan belum?',
            'Sore! Gimana harinya?',
            'Malam! Udah istirahat belum? 🌙',
            'Pagi-pagi udah aktif ya! 🌅',
            'Siang-siang enaknya ngopi nih ☕',
            'Sore enaknya jalan-jalan ya',
            'Malam-malam masih begadang? 😄',
        ]
    },
    # === HOW ARE YOU ===
    {
        'pattern': r'\b(kabar|kamu (?:gimana|apa|lagi)|gimana kabar|apa kabar|gmn kabar|kamu baik|you good|how are you)\b',
        'replies': [
            'Alhamdulillah baik! Kamu gimana?',
            'Baik dong! Lagi semangat nih 🔥',
            'Lumayan, lagi belajar jadi lebih pintar 🧠',
            'Oke oke aja! Ada yang bisa dibantu?',
            'Sehat alhamdulillah! Kamu juga ya 😊',
            'Baik! Makasih udah nanya 😄',
        ]
    },
    # === QUESTIONS (HOW/WHY/WHAT/WHERE/WHEN) ===
    {
        'pattern': r'\b(gimana|bagaimana|gmn|kenapa|knp|kenp|apa (?:itu|sih|aja|kabar)|siapa|dimana|dmna|diamna|kapan|kp|berapa|boleh)\b',
        'replies': [
            'Hmm, pertanyaan bagus! Menurutku sih...',
            'Bisa dijelasin lebih detail ga?',
            'Wah, topik yang menarik nih!',
            'Aku juga lagi mikir tentang itu sebenernya 🤔',
            'Good question! Coba search di Google juga ya',
            'Hm, tergantung situasinya sih',
            'Bisa banyak cara sebenernya, yang mana yang kamu mau?',
            'Wah aku belum tau pasti, tapi semoga bisa bantu!',
        ]
    },
    # === AGREEMENT / POSITIVE ===
    {
        'pattern': r'\b(setuju|bener|betul|iya|benar|mantap|oke|sip|gas|bagus|keren|ok|nice|good|great|wow|wah|asik|asyik|jos|joss|mantab|sipss|okeoke)\b',
        'replies': [
            'Iya bener banget! 👍',
            'Setuju! Mantap jiwa 🔥',
            'Gas! Kita gas bareng 🚀',
            'Oke siap!',
            'Betul tuh!mantap',
            'Mantap, lanjut terus!',
            'Wah keren! Aku juga suka 🔥',
            'Nice! Good job! 👏',
            'Jos! Emang bener tuh',
            'Asik! Lanjut terus ya',
        ]
    },
    # === THANKS ===
    {
        'pattern': r'\b(makasih|terima kasih|thanks|thx|ty|mantap|bagus|helpful|help|thanks ya|mksh|thx ya|thanks bgd|makasih banyak)\b',
        'replies': [
            'Sama-sama! 😊',
            'Santai aja, glad to help!',
            'No problem! 👍',
            'Anytime! 🙌',
            'Sama-sama, seneng bisa bantu!',
            'Santai bro, kapan aja boleh tanya lagi!',
            'Sama-sama ya! 😄',
        ]
    },
    # === TECH / CODING ===
    {
        'pattern': r'\b(python|javascript|coding|program|code|bug|error|deploy|server|database|api|react|node|docker|linux|github|git|css|html|php|laravel|flutter|android|ios|web|app|software|hardware|typing|keyboard|laptop|komputer|hp|android|iphone|samsung|xiaomi|oppo|vivo)\b',
        'replies': [
            'Wah lagi bahas coding ya! Aku juga suka coding 🧑‍💻',
            'Coding emang seru tapi kadang bikin pusing ya 😅',
            'Error lagi? Coba print dulu datanya, biasanya ketemu!',
            'Deploy ke mana? Vercel gampang banget lho',
            'Python atau JavaScript nih? Dua-duanya oke sih',
            'Bug itu teman developer, hadapi aja 💪',
            'Stack overflow solusinya selalu haha',
            'Coding itu kayak puzzle, susah tapi seru! 🧩',
            'Laptop baru? Buat coding enaknya yang minimal i5 ya',
            'Android atau iOS? Dua-duanya ada kelebihannya',
            'Web development seru! Mau frontend atau backend?',
        ]
    },
    # === CASUAL CHAT ===
    {
        'pattern': r'\b(lagi apa|lagi sibuk|udah makan|mau kemana|weekend|nonton|game|anime|film|music|musik|lagu|buku|olahraga|olah raga|travel|jalan|liburan|libur)\b',
        'replies': [
            'Lagi ngoding nih, hobi banget 😄',
            'Udah dong! Kamu gimana?',
            'Weekend enaknya santai aja sih',
            'Nonton apa? Kasih rekomendasi dong!',
            'Game apa yang lagi dimainkan?',
            'Anime apa yang lagi hot?',
            'Musik genre apa yang kamu suka?',
            'Liburan kemana? Aku iri 😭',
            'Olahraga apa nih? Sehat itu penting! 💪',
            'Buku bagus apa yang lagi dibaca?',
        ]
    },
    # === FEELINGS / EMOTIONS ===
    {
        'pattern': r'\b(sedih|galau|kesel|dongkol|benci|maaf|sorry|parah|jelek|gagal|fail|error|bug|rusak|error|pusing|bingung|confused|bloon|bodoh|tolol|goblog|gblk|anjing|bangsat|kontol|memek|kntl|mmk|asu|bgst|anjay)\b',
        'replies': [
            'Sabar ya, pasti ada jalan keluarnya 💪',
            'Tenang, semua pasti berlalu!',
            'Aku di sini kalau mau cerita 😊',
            'Gapapa, yang penting terus semangat!',
            'Eh jangan sedih dong, ada aku nih!',
            'Gagal itu wajar, yang penting coba lagi! 🔥',
            'Pusing ya? Coba istirahat dulu bentar',
            'Semua orang pernah kayak gitu kok, sabar ya 😊',
            'Jangan menyerah! Kamu pasti bisa! 💪',
        ]
    },
    # === COMPLIMENTS ===
    {
        'pattern': r'\b(keren|cantik|ganteng|pintar|cerdas|hebat|jago|pro|master|expert|suhu|guru|dosen|master)\b',
        'replies': [
            'Wah makasih! 😊 Kamu juga keren!',
            'Hehe, masih belajar nih 🙏',
            'Makasih! Tapi masih banyak yang perlu dipelajari',
            'Kamu juga hebat kok! 💪',
            'Wah jangan gitu, kita sama-sama belajar ya',
            'Makasih! Aku juga terus belajar jadi lebih baik',
        ]
    },
    # === IDK / CONFUSED ===
    {
        'pattern': r'\b(ga tau|gak tau|ngga tau|ga ngerti|gak ngerti|ngga ngerti|bingung|confused|pusing|gimana dong|gmn dong|gmn caranya|gimana caranya|cara|tutorial|belajar)\b',
        'replies': [
            'Coba search di Google ya, biasanya ada tutorialnya!',
            'YouTube banyak tutorial bagus kok, coba cari di sana',
            'Aku juga masih belajar, tapi coba langkah demi langkah ya',
            'Jangan pusing! Mulai dari yang basic dulu',
            'Banyak komunitas yang bisa bantu kok, coba gabung di Discord/Telegram',
            'Semua orang pernah bingung, yang penting terus coba! 💪',
        ]
    },
    # === GREETING RESPONSES ===
    {
        'pattern': r'\b(baik|alhamdulillah|lumayan|biasa aja|fine|good|ok|so so|sekedar|cuma|lagi|just)\b',
        'replies': [
            'Bagus dong! Seneng denger gitu 😊',
            'Alhamdulillah ya! Semoga terus baik',
            'Oke! Ada yang bisa dibantu?',
            'Lumayan tuh, semangat terus ya! 💪',
            'Good! Mau ngobrol apa nih?',
        ]
    },
    # === HELP REQUESTS ===
    {
        'pattern': r'\b(bantu|tolong|help|bisa tolong|tolong dong|bantuin|help me|bisa ga|bisa gak|bisa gk|ada yang bisa)\b',
        'replies': [
            'Tentu! Aku siap bantu, ceritain aja 😊',
            'Boleh! Tanya aja, insyaallah bisa bantu',
            'Gas, ceritain masalahnya apa!',
            'Siap! Aku dengerin nih 🎧',
            'Yuk kita bantu bareng! Ceritain aja',
        ]
    },
    # === YES/NO ===
    {
        'pattern': r'^(ya|y|iya|iye|yups|yep|yoi|bet|bener|emang|emg|iyalah|iya dong|iyain|iyain dong|ga|gak|nggak|enggak|kagak|no|n|nope|not really)\b',
        'replies': [
            'Oke noted! 👍',
            'Siap! Ada lagi?',
            'Oke gas!',
            'Noted ya!',
            'Oke oke, paham!',
        ]
    },
    # === BIRTHDAY / CELEBRATION ===
    {
        'pattern': r'\b(ulang tahun|birthday|hbd|happy birthday|selamat|congrats|congratulation|恭喜|menang|juara|winner|champion)\b',
        'replies': [
            'Selamat! 🎉🎊 Semoga sukses terus ya!',
            'Wah keren! Selamat! 🥳',
            'Happy birthday! Semoga panjang umur dan sehat selalu! 🎂',
            'Congrats! Kamu emang jago! 🏆',
            'Selamat ya! Semoga makin sukses! 🎊',
        ]
    },
    # === FOOD ===
    {
        'pattern': r'\b(makan|masak|resep|food|makanan|minum|kopi|teh|jus|snack|cemilan|buka puasa|sahur|buka|ngopi)\b',
        'replies': [
            'Enak tuh! Jangan lupa makan yang teratur ya 🍚',
            'Makan apa? Kasih tau dong!',
            'Kopi emang penyelamat saat ngoding ☕',
            'Jangan lupa makan ya, kesehatan penting! 💪',
            'Wah jadi lapar denger gitu 😋',
        ]
    },
    # === MONEY / WORK ===
    {
        'pattern': r'\b(gaji|kerja|kantor|office|wfh|remote|freelance|side job|bisnis|usaha|dagang|jual|beli|harga|murah|mahal|diskon|promo|rekening|bank|transfer|duit|uang|modal)\b',
        'replies': [
            'Kerja keras pasti成果 nya kok! 💪',
            'WFH enak ga? Aku lebih suka WFH sih',
            'Freelance itu seru tapi kadang ga stabil ya',
            'Bisnis online lagi trend banget nih',
            'Semangat kerja! Pasti成果 nya! 🔥',
            'Jangan lupa nabung ya! 💰',
        ]
    },
    # === RELIGION / SPIRITUAL ===
    {
        'pattern': r'\b(sholat|salat|doa|allah|tuhan|god|berkah|rezeki|rezeki|amal|sedekah|quran|alquran|ngaji|ibadah|puasa|ramadhan|lebaran|idul fitri|idul adha)\b',
        'replies': [
            'Aamiin! Semoga dilancarkan ya 🤲',
            'Semoga selalu dalam lindungan Allah SWT',
            'Ibadah itu penting, jangan lupa ya! 🙏',
            'Semoga berkah selalu! Aamiin 🤲',
            'Jangan lupa sholat 5 waktu ya! 😊',
        ]
    },
    # === TIME / SCHEDULE ===
    {
        'pattern': r'\b(jam|waktu|time|sekarang|saat ini|nanti|besok|lusa|kemarin|hari ini|today|tomorrow|yesterday|deadline|jadwal|schedule|menit|detik|jam berapa)\b',
        'replies': [
            'Waktu itu emas, jangan disia-siain ya! ⏰',
            'Deadline kapan nih? Jangan mepet ya!',
            'Jangan lupa istirahat juga ya, jangan kerja terus!',
            'Atur waktu yang baik ya, produktif tapi tetep santai',
            'Jangan begadang terus, tidur yang cukup! 🌙',
        ]
    },
    # === BYE ===
    {
        'pattern': r'\b(dah|bye|goodbye|selamat tinggal|see you|sampe ketemu|hati hati|take care|good night|gn|td)\b',
        'replies': [
            'Dah! Hati-hati ya! 👋',
            'Bye! See you next time! 🙌',
            'Take care! Jaga kesehatan ya 😊',
            'Sampai ketemu lagi! Semangat terus!',
            'Good night! Tidur yang nyenyak 🌙',
            'Dah! Seneng bisa ngobrol sama kamu!',
        ]
    },
    # === RELATIONSHIP ===
    {
        'pattern': r'\b(pacar|doi|couple|jadian|putus|cinta|love|sayang|kasih|hati|crush|gebetan|jomblo|single|married|nikah|menikah|tunangan|kawin)\b',
        'replies': [
            'Wah lagi galau soal cinta nih? 😄',
            'Single itu enak, bebas! Tapi kalau ada yang cocok gas aja 🔥',
            'Semoga langgeng ya! 💕',
            'Cinta itu indah, tapi jangan lupa belajar juga ya 😊',
            'Sabar, jodoh itu ga kemana kok! 🤲',
        ]
    },
    # === SPORTS ===
    {
        'pattern': r'\b(bola|sepak|futsal|basket|badminton|tennis|voli|moto gp|formula|nba|premier league|liga|champion|world cup|piala|olympic|olahraga|workout|gym|fitness|lari|running|joging|jogging|sepeda|cycling|renang|swimming|yoga)\b',
        'replies': [
            'Olahraga itu penting! Minimal jalan kaki 30 menit sehari 🏃',
            'Main bola seru tuh! Tim mana yang kamu suka?',
            'Gym rutin pasti hasilnya keliatan! 💪',
            'Badminton Indonesia emang juara! 🏸',
            'Jangan lupa pemanasan sebelum olahraga ya!',
        ]
    },
    # === MUSIC ===
    {
        'pattern': r'\b(music|musik|lagu|song|playlist|spotify|youtube music|genre|rock|pop|jazz|dangdut|koplo|hip hop|rap|r&b|edm|dj|concert|konser|band|gitar|drum|piano|biola|suling|gamelan)\b',
        'replies': [
            'Musik emang bikin semangat! 🎵',
            'Genre apa yang lagi kamu dengerin?',
            'Playlist bagus apa nih? Kasih tau dong!',
            'Dengerin musik sambil ngoding emang paling enak 🎧',
            'Konser kemana? Aku iri! 😭',
        ]
    },
    # === WEATHER ===
    {
        'pattern': r'\b(hujan|panas|dingin|cuaca|weather|gerimis|angin|banjir|kemarau|penghujan|panas banget|dingin banget|adem|sejuk)\b',
        'replies': [
            'Hujan enaknya di dalam nonton film 🎬',
            'Panas-panas gini enaknya minum es ya 🧊',
            'Jangan lupa bawa payung kalau keluar ya! ☂️',
            'Adem-em enaknya tidur 😴',
            'Cuaca ekstrem, jaga kesehatan ya! 💪',
        ]
    },
    # === ANIME / MANGA ===
    {
        'pattern': r'\b(anime|manga|naruto|one piece|dragon ball|attack on titan|demon slayer|jujutsu kaisen|my hero|haikyuu|bleach|opm|solo leveling|manhwa|donghua|otaku|weeb|waifu|husbando)\b',
        'replies': [
            'Anime apa yang lagi kamu tonton?',
            'One Piece emang terbaik! Luffy GOAT 🏴‍☠️',
            'Demon Slayer animation-nya keren banget! 🔥',
            'Solo Leveling lagi hype banget nih!',
            'Manga atau anime dulu? Aku lebih suka manga sih',
        ]
    },
    # === PHONE / GADGET ===
    {
        'pattern': r'\b(hp|handphone|smartphone|iphone|samsung|xiaomi|oppo|vivo|realme|oneplus|pixel|redmi|poco|asus|rog|gaming phone|tablet|ipad|apple|galaxy)\b',
        'replies': [
            'HP baru? Buat apa dipake-nya?',
            'iPhone atau Android nih? Dua-duanya oke sih',
            'Xiaomi value-for-money banget sih emang',
            'Samsung Galaxy emang mantap display-nya!',
            'Gaming phone emang kenceng, tapi buat daily use overkill ya 😄',
        ]
    },
    # === FILM / SERIES ===
    {
        'pattern': r'\b(movie|film|series|nonton|streaming|netflix|disney|hbo|prime|youtube|tiktok|reels|shorts|viral|trending|booming)\b',
        'replies': [
            'Film apa yang lagi kamu tonton?',
            'Netflix ada series bagus apa nih?',
            'Rekomendasi dong, lagi cari tontonan nih!',
            'TikTok bikin candu ya, tapi jangan kebanyakan juga 😄',
            'Film Indonesia lagi bagus-bagus lho belakangan!',
        ]
    },
]

# ============================================================
# GENERIC FALLBACKS
# ============================================================

FALLBACKS = [
    'Hmm, menarik juga tuh! 🤔',
    'Oke, aku catet ya!',
    'Wah, bisa dijelasin lagi?',
    'Noted! Ada lagi?',
    'Interesting! Tell me more 😊',
    'Aku masih belajar nih, tapi semoga bisa bantu!',
    'Hm, aku belum paham banget, tapi nice! 👍',
    'Wah seru! Lanjut dong ceritanya',
    'Oke gas! Mau ngobrol apa lagi?',
    'Asik! Ada topik lain ga?',
    'Hmm gitu ya... menarik!',
    'Wah keren! Aku juga mau tau lebih banyak',
    'Siap! Ada lagi yang mau ditanya?',
    'Oke noted, makasih infonya! 👍',
    'Wah foto apa nih? Kasih tau dong!',
]

# ============================================================
# CONTEXT-AWARE REPLIES (berdasarkan panjang pesan)
# ============================================================

SHORT_REPLIES = [
    'Oke! 👍',
    'Siap!',
    'Noted!',
    'Gas!',
    'Oke gas! 🚀',
    'Sip!',
    'Iya!',
    'Yoi!',
]

LONG_REPLIEWS = [
    'Wah panjang juga ceritanya! Aku baca ya 😊',
    'Oke aku coba bantu sebisaku!',
    'Menarik banget! Aku bookmark ya 📌',
    'Wah detail banget! Thanks udah share 😊',
]

# ============================================================
# MAIN FUNCTION
# ============================================================

def get_smart_reply(user_msg, model_reply=None):
    """Get a smart reply. Falls back to pattern matching if model output is garbage."""
    # First: try model reply
    if model_reply and not _is_garbage(model_reply) and not _echo_check(model_reply, user_msg):
        return model_reply

    # Second: pattern matching FIRST (before short/long check)
    text_lower = user_msg.lower()
    for pattern_group in PATTERNS:
        if re.search(pattern_group['pattern'], text_lower):
            return random.choice(pattern_group['replies'])

    # Third: context-aware for very short/long messages
    words = user_msg.split()
    if len(words) <= 2:
        return random.choice(SHORT_REPLIES)
    if len(words) > 30:
        return random.choice(LONG_REPLIEWS)

    # Fourth: generic fallback
    return random.choice(FALLBACKS)
