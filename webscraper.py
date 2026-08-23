"""DikaAI Web Scraper v2 - Massive Parallel Training Data Collection

180+ sources organized into 8 categories:
A. Indonesian NLP / Language (NusaCrowd, IndoNLU, HuggingFace ID datasets)
B. Additional Indonesian Corpus (Aksara, IndoBloom, CulturaX, etc.)
C. Programming Docs (Python, JS, Rust, Go, Kotlin, C++, etc.)
D. Linux/Shell/Git/DevOps Docs
E. Android/Kotlin/Termux Docs
F. ML/AI/LLM Docs
G. AI Coding Benchmarks (HumanEval, MBPP, The Stack, etc.)
H. Conversational/Casual (PersonaChat, ELI5, movies, reviews)

All scrapers run in PARALLEL threads for max speed.
"""
import urllib.request
import urllib.error
import json
import time
import re
import html
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dikaai.database import DikaDB


class DikaWebScraper:
    def __init__(self, db: DikaDB, max_workers: int = 8):
        self.db = db
        self.max_workers = max_workers
        self.stats = {
            'scraped': 0,
            'new': 0,
            'duplicates': 0,
            'errors': 0
        }
        self._lock = threading.Lock()
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def _fetch(self, url, timeout=12):
        """Fetch URL content with proper headers."""
        try:
            req = urllib.request.Request(url, headers=self._headers)
            resp = urllib.request.urlopen(req, timeout=timeout)
            return resp.read().decode('utf-8', errors='ignore')
        except Exception:
            with self._lock:
                self.stats['errors'] += 1
            return None

    def _clean_html(self, text):
        """Remove HTML tags and clean text."""
        text = html.unescape(text)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _split_sentences(self, text):
        """Split text into sentences."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]

    def _is_valid(self, text):
        """Check if text is valid for training."""
        if not text or len(text) < 10:
            return False
        if len(text) > 500:
            return False
        # Skip code blocks
        if '```' in text:
            return False
        # Skip URLs
        if re.search(r'https?://', text):
            return False
        # Skip very short
        words = text.split()
        if len(words) < 3:
            return False
        return True

    def _add(self, chat_id, source, sender, message):
        """Add message to database (thread-safe)."""
        if not self._is_valid(message):
            return
        try:
            if self.db.add_message(
                chat_id=chat_id,
                chat_title=source,
                sender_name=sender,
                message=message,
                timestamp=time.time()
            ):
                with self._lock:
                    self.stats['new'] += 1
            with self._lock:
                self.stats['scraped'] += 1
        except Exception:
            pass

    def _add_batch(self, chat_id, source, sender, messages):
        """Add multiple messages at once."""
        count = 0
        for msg in messages:
            if self._is_valid(msg):
                try:
                    if self.db.add_message(
                        chat_id=chat_id,
                        chat_title=source,
                        sender_name=sender,
                        message=msg,
                        timestamp=time.time()
                    ):
                        count += 1
                except Exception:
                    pass
        with self._lock:
            self.stats['new'] += count
            self.stats['scraped'] += len(messages)
        return count

    # ================================================================
    # CATEGORY A: Indonesian NLP / Language (Priority!)
    # ================================================================

    def scrape_huggingface_indonesian(self):
        """Scrape HuggingFace API for Indonesian datasets info + samples."""
        print("  [WEB] [A] HuggingFace Indonesian datasets...")
        count = 0

        hf_datasets = [
            'indonesian-nlp/wikipedia-id',
            'indonesian-nlp/wikipedia-id-20231101',
            'indonesian-nlp/mc4-id',
            'indonesian-nlp/id_personachat',
            'indonesian-nlp/eli5_id',
            'indonesian-nlp/lfqa_id',
            'indonesian-nlp/id_newspapers_2018',
            'indonesian-nlp/librivox-indonesia',
            'indonesian-nlp/wikipedia-10k',
            'afaji/indonli',
            'vickyfatrian/vqfat-indo-corpus',
            'AksaraLLM/aksara-training-data',
            'AksaraLLM/aksara-pretrain-id',
            'AksaraLLM/aksara-pretrain-clean-v1',
            'AksaraLLM/aksara-sft-id',
            'AksaraLLM/aksara-sft-clean-v1',
            'AksaraLLM/aksara-bahasa-daerah-v1',
            'AksaraLLM/aksara-mega-sft',
            'Firmansyah-Ibrahim/indo-bloom-corpus',
            'Firmansyah-Ibrahim/indo-bloom-raw-bse',
            'hadadxyz/OpenBahasa-CoT',
            'Caplin43/IndoRobo-Instruction-Dataset-v1',
            'InfoBayAI/Indonesian-STEM-Textbook-Dataset',
            'InfoBayAI/Indonesian-Non-STEM-Textbook-Dataset',
            'img-gemina/indonesian-corpus-2b-deepclean-indo4b',
            'maleo-ai/maleo-short',
            'Nourivex/nourivex-id-story-gen-dataset',
            'soundstarrain/id-lightnovels-clean',
            'jakartaresearch/indo-movie-subtitle',
            'jakartaresearch/google-play-review',
            'jakartaresearch/indoqa',
            'talithaolga/Indonesian-Emotion-Classification',
            'uonlp/CulturaX',
        ]

        for ds_id in hf_datasets:
            # HuggingFace API - get dataset info
            url = f"https://huggingface.co/api/datasets/{ds_id}"
            data = self._fetch(url, timeout=10)
            if not data:
                continue

            try:
                info = json.loads(data)
                # Get dataset description
                desc = info.get('description', '') or info.get('cardData', {}).get('description', '')
                if desc:
                    desc = self._clean_html(desc)
                    sentences = self._split_sentences(desc)
                    for sent in sentences[:3]:
                        self._add(-300, f'HF #{ds_id.split("/")[-1]}', 'dataset', sent)
                        count += 1

                # Get tags
                tags = info.get('tags', [])
                if tags:
                    tag_str = f"Dataset {ds_id}: tags={', '.join(tags[:10])}"
                    self._add(-300, 'HF Tags', 'metadata', tag_str)
                    count += 1

            except json.JSONDecodeError:
                pass

            time.sleep(0.2)

        print(f"  [WEB] [A] HuggingFace: {count} entries")
        return count

    def scrape_huggingface_samples(self):
        """Get actual dataset rows from HuggingFace datasets API."""
        print("  [WEB] [A] HuggingFace dataset samples...")
        count = 0

        # Datasets that have viewer API (actual rows)
        ds_with_viewer = [
            'indonesian-nlp/wikipedia-id',
            'jakartaresearch/indoqa',
            'talithaolga/Indonesian-Emotion-Classification',
        ]

        for ds_id in ds_with_viewer:
            url = f"https://datasets-server.huggingface.co/rows?dataset={ds_id}&config=default&split=train&offset=0&length=20"
            data = self._fetch(url, timeout=15)
            if not data:
                continue

            try:
                rows = json.loads(data).get('rows', [])
                for row_data in rows:
                    row = row_data.get('row', {})
                    # Extract text fields
                    for key in ['text', 'context', 'question', 'answer',
                                'input', 'output', 'content', 'title',
                                'conversation', 'message', 'response',
                                'instruction', 'sentence', 'summary']:
                        val = row.get(key, '')
                        if isinstance(val, str) and len(val) > 15:
                            self._add(-301, f'HF Sample', 'sample', val[:500])
                            count += 1
                        elif isinstance(val, list):
                            for item in val[:3]:
                                if isinstance(item, str) and len(item) > 15:
                                    self._add(-301, 'HF Sample', 'sample', item[:500])
                                    count += 1
            except (json.JSONDecodeError, KeyError):
                pass

            time.sleep(0.3)

        print(f"  [WEB] [A] HF Samples: {count} rows")
        return count

    def scrape_wikipedia_id_full(self):
        """Scrape full Indonesian Wikipedia articles."""
        print("  [WEB] [A] Wikipedia Indonesia (full)...")
        count = 0

        articles = [
            # Programming
            'Pemrograman', 'Python_(bahasa_pemrograman)', 'JavaScript',
            'Java_(bahasa_pemrograman)', 'C_(bahasa_pemrograman)', 'C++',
            'Go_(bahasa_pemrograman)', 'Rust_(bahasa_pemrograman)',
            'TypeScript', 'PHP', 'Ruby', 'Kotlin',
            # Systems
            'Linux', 'Ubuntu_(sistem_operasi)', 'Sistem_operasi',
            'Jaringan_komputer', 'Komputer', 'Android_(sistem_operasi)',
            # Web
            'Web_development', 'React_(pustakaJavaScript)', 'Vue.js',
            'Node.js', 'Django', 'Laravel', 'HTML', 'CSS', 'API',
            # Data
            'Database', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis',
            # AI
            'Kecerdasan_buatan', 'Machine_learning', 'Deep_learning',
            'Data_science', 'TensorFlow', 'PyTorch',
            # Cloud
            'Cloud_computing', 'Docker_(perangkat_lunak)', 'Kubernetes', 'DevOps',
            # Security
            'Cybersecurity', 'Kriptografi',
            # Internet
            'Internet', 'Blockchain', 'E-commerce', 'Fintech', 'Startup',
            'Social_media', 'Open_source', 'Smartphone',
            # Concepts
            'Algoritma', 'Struktur_data', 'Recursion',
            'Sorting_algorithm', 'Graph_theory',
            'Artificial_intelligence', 'Natural_language_processing',
            # More tech
            'Virtual_reality', 'Augmented_reality', '5G',
            'Perangkat_lunak', 'Perangkat_keras',
            'Internet_of_things', 'Big_data', 'Data_mining',
            'Computer_vision', 'Robotika', 'Cryptography',
        ]

        for article in articles:
            url = f'https://id.wikipedia.org/api/rest_v1/page/summary/{article}'
            data = self._fetch(url, timeout=10)
            if not data:
                continue
            try:
                info = json.loads(data)
                extract = info.get('extract', '')
                if extract and len(extract) > 50:
                    sentences = self._split_sentences(extract)
                    for sent in sentences[:8]:
                        self._add(-302, 'Wikipedia ID', 'wiki', sent)
                        count += 1
                desc = info.get('description', '')
                if desc and len(desc) > 15:
                    self._add(-302, 'Wikipedia ID', 'wiki', desc)
                    count += 1
            except json.JSONDecodeError:
                pass
            time.sleep(0.15)

        print(f"  [WEB] [A] Wikipedia ID: {count} sentences")
        return count

    # ================================================================
    # CATEGORY B: Additional Indonesian Corpus
    # ================================================================

    def scrape_indonesian_news(self):
        """Scrape Indonesian news RSS feeds."""
        print("  [WEB] [B] Indonesian news feeds...")
        count = 0

        feeds = [
            ('Detik', 'https://www.detik.com/tekno/rss'),
            ('Detik News', 'https://www.detik.com/news/rss'),
            ('Kompas', 'https://www.kompas.com/rss/tekno'),
            ('Kompas Tek', 'https://tekno.kompas.com/rss'),
            ('Liputan6', 'https://www.liputan6.com/rss/tekno'),
            ('CNN ID', 'https://www.cnnindonesia.com/teknologi/rss'),
            ('Jalantikus', 'https://www.jalantikus.com/feed/'),
        ]

        for name, feed_url in feeds:
            data = self._fetch(feed_url, timeout=10)
            if not data:
                continue

            titles = re.findall(r'<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', data)
            descs = re.findall(r'<description[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>', data, re.DOTALL)

            for title in titles:
                title = self._clean_html(title)
                if title and len(title) > 15 and len(title) < 200:
                    self._add(-310, name, 'news', title)
                    count += 1

            for desc in descs:
                desc = self._clean_html(desc)
                sentences = self._split_sentences(desc)
                for sent in sentences[:2]:
                    self._add(-310, name, 'news', sent)
                    count += 1

            time.sleep(0.3)

        print(f"  [WEB] [B] News: {count} articles")
        return count

    def scrape_kaskus_casual(self):
        """Scrape Kaskus for casual Indonesian conversation."""
        print("  [WEB] [B] Kaskus casual Indonesian...")
        count = 0

        urls = [
            "https://www.kaskus.co.id/api/v2/thread/popular?per_page=30",
            "https://www.kaskus.co.id/api/v2/thread/hot?per_page=20",
        ]

        for url in urls:
            data = self._fetch(url, timeout=15)
            if not data:
                continue
            try:
                threads = json.loads(data).get('data', [])
                for t in threads:
                    title = t.get('title', '')
                    content = t.get('content', '')
                    if title and len(title) > 10:
                        self._add(-311, 'Kaskus', 'kaskuser', title)
                        count += 1
                    if content:
                        content = self._clean_html(content)
                        sentences = self._split_sentences(content)
                        for sent in sentences[:3]:
                            self._add(-311, 'Kaskus', 'kaskuser', sent)
                            count += 1
            except (json.JSONDecodeError, KeyError):
                pass
            time.sleep(0.3)

        print(f"  [WEB] [B] Kaskus: {count} posts")
        return count

    def scrape_indonesian_corpus(self):
        """Add curated Indonesian text corpus (diverse styles)."""
        print("  [WEB] [B] Indonesian corpus (curated)...")
        count = 0

        corpus = [
            # Conversational casual
            "halo apa kabar hari ini", "selamat pagi semuanya",
            "ada yang bisa saya bantu", "terima kasih banyak ya",
            "maaf saya terlambat", "oke siap gas",
            "wah keren banget itu", "gimana caranya sih",
            "udah coba belum", "beneran nih", "seriusan?",
            "anjay mantap jiwa", "waduh parah banget",
            "gas kita mulai", "yuk kita diskusi",
            "setuju banget sama kamu", "bener tuh kata kata",
            "haha iya juga ya", "wkwk lucu banget",
            "udah makan belum", "lagi sibuk apa nih",
            "kapan ketemu lagi", "hati hati di jalan",
            "semangat terus ya", "jangan lupa istirahat",
            "good morning semuanya", "selamat malam",
            "bro ini error kenapa ya", "kamu tau ga kenapa ini error",
            "gue udah coba tapi ga bisa", "udah di fix belum",
            "wkwk abis fix malah error baru", "parah sih ini bug",
            "mantap bro solusinya", "thankyou banyak ya",
            "sama sama bro", "gapapa lambat yang penting jalan",
            "wah keren bisa gitu ya", "gimana caranya dong",
            "ane baru belajar nih", "noob banget ane",
            "udah pro sih kamu", "belajar terus bro",
            "kalo error gini gimana", "coba clear cache dulu",
            "udah restart belum", "coba install ulang",
            "kemaren juga gitu", "tadi malem juga error",
            "oh gitu toh", "wah baru tau gua",
            "info dong soal hp baru", "recommend laptop buat coding",
            "budget 5 juta apa ya", "aduh wifi lambat banget",
            "mau nonton apa malam ini", "weekend kemana nih",
            "udah download game nya", "anime apa lagi hot",
            "recipe masakan sederhana", "tips traveling murah",
            "belajar coding dari mana", "cara backup android",
            "aplikasi edit video ringan", "cara hemat kuota",
            "belajar bahasa inggris gratis", "cara buat portfolio",
            "tutorial photoshop pemula", "cara install linux",
            "belajar desain grafis", "startup indo naik daun",
            "fintech makin maju", "digital transformasi umkm",
            "e-commerce kompetitif", "crypto masa depan",
            "5g di indonesia", "remote work trend",
            "teknologi hijau", "smart city indonesia",
            "belajar pemrograman nol", "kursus online gratis",
            "univ terbaik IT indo", "beasiswa luar negeri",
            "data science karir", "fullstack gaji berapa",

            # Tech/coding explanation
            "cara install python di ubuntu itu gampang",
            "error module not found solusinya gimana",
            "react hooks itu apa sih penjelasannya",
            "database mysql vs postgresql mana yang lebih bagus",
            "docker container itu kayak virtual machine",
            "linux command line dasar yang perlu diketahui",
            "git merge conflict gimana cara resolve nya",
            "api rest itu endpointnya apa aja",
            "mobile app development pake flutter atau react native",
            "cloud computing itu AWS vs GCP vs Azure",
            "machine learning untuk pemula mulai dari mana",
            "cybersecurity itu penting banget buat developer",
            "deployment pipeline yang bagus itu gimana",
            "testing unit test penting ga sih",
            "code review itu bagus buat improve quality",
            "agile methodology itu sprintnya berapa lama",
            "kubernetes pod itu kayak apa",
            "nginx reverse proxy setup step by step",
            "redis caching buat ngebutin aplikasi",
            "mongodb vs postgresql buat project kecil",
            "typescript itu kayak javascript tapi typed",
            "golang itu cocok buat backend server",
            "rust programming itu memory safe banget",
            "svelte itu framework yang simple dan cepet",
            "nextjs itu react yang bisa server side rendering",
            "tailwind css itu utility first styling",
            "graphql itu alternatif rest api",
            "websocket buat real-time communication",
            "rest api vs grpc mana yang lebih cepet",
            "jwt token itu cara auth yang stateless",
            "oauth2 flow itu gimana step by step",
            "cors error itu kenapa dan gimana fix",
            "sql injection itu bahaya banget",
            "xss attack itu cross site scripting",
            "ci cd pipeline itu continuous integration",
            "terraform itu infrastructure as code",
            "ansible itu configuration management",
            "prometheus buat monitoring metrics",
            "grafana dashboard buat visualisasi",
            "elasticsearch buat full text search",
            "kafka itu event streaming platform",
            "rabbitmq itu message broker",

            # Debugging/explanation style
            "error ini terjadi karena",
            "solusinya adalah dengan cara",
            "langkah pertama yang perlu dilakukan",
            "pastikan anda sudah install",
            "periksa apakah dependency sudah benar",
            "coba jalankan command ini",
            "jika masih error coba clear cache",
            "restart server dan coba lagi",
            "cek log untuk detail error",
            "gunakan try catch untuk error handling",
            "pastikan port belum digunakan",
            "cek apakah firewall memblokir",
            "update dependency ke versi terbaru",
            "gunakan environment variable untuk config",
            "backup database sebelum migrasi",

            # Indonesian formal/semi-formal
            "berikut adalah penjelasan lengkap",
            "dalam pengembangan perangkat lunak",
            "arsitektur microservices memungkinkan",
            "implementasi design pattern",
            "prinsip solid dalam oop",
            "pola MVC model view controller",
            "konsep responsive web design",
            "metodologi scrum dan kanban",
            "best practice dalam penulisan kode",
            "dokumentasi yang baik sangat penting",
        ]

        for text in corpus:
            self._add(-312, 'Indonesian Corpus', 'corpus', text)
            count += 1

        print(f"  [WEB] [B] Corpus: {count} phrases")
        return count

    def scrape_duckduckgo_indonesian(self):
        """Scrape DuckDuckGo for Indonesian tech content."""
        print("  [WEB] [B] DuckDuckGo Indonesian...")
        count = 0

        queries = [
            'tutorial python indonesia', 'belajar javascript pemula',
            'cara install linux ubuntu', 'react native tutorial indo',
            'machine learning pemula indonesia', 'cara buat website sendiri',
            'tips belajar coding pemula', 'framework javascript terbaik',
            'cara deploy aplikasi server', 'database postgresql tutorial',
            'docker untuk pemula', 'git tutorial bahasa indonesia',
            'cara buat api rest', 'mobile app development indo',
            'cybersecurity tips developer', 'cloud computing indonesia',
            'cara belajar data science', 'flutter tutorial indonesia',
            'node js express tutorial', 'django python web framework',
            'cara install docker ubuntu', 'kubernetes pemula',
            'nginx reverse proxy tutorial', 'redis caching tutorial',
            'mongodb tutorial indonesia', 'linux command line dasar',
            'cara buat bot telegram python', 'web scraping python',
            'fastapi tutorial indonesia', 'svelte tutorial pemula',
            'tailwind css tutorial indo', 'typescript tutorial dasar',
            'golang tutorial indonesia', 'rust programming pemula',
            'cara belajar algorithm', 'data structure tutorial',
            'cara optimasi website performance', 'seo tips indonesia',
            'digital marketing strategy', 'social media management',
            'cara install termux android', 'termux python tutorial',
            'android development kotlin pemula', 'jetpack compose tutorial',
            'react vs vue vs angular', 'svelte vs react performance',
            'python web scraping beautifulsoup', 'python fastapi rest api',
            'django vs flask vs fastapi', 'next js tutorial indonesia',
        ]

        for query in queries:
            url = f'https://html.duckduckgo.com/html/?q={query.replace(" ", "+")}'
            data = self._fetch(url, timeout=10)
            if not data:
                continue

            snippets = re.findall(r'class="result__snippet">(.*?)</a>', data, re.DOTALL)
            for snippet in snippets[:3]:
                text = self._clean_html(snippet)
                if text and len(text) > 20:
                    self._add(-313, f'DDG', 'search', text)
                    count += 1

            titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', data, re.DOTALL)
            for title in titles[:3]:
                text = self._clean_html(title)
                if text and len(text) > 10:
                    self._add(-313, 'DDG', 'search', text)
                    count += 1

            time.sleep(0.3)

        print(f"  [WEB] [B] DuckDuckGo: {count} results")
        return count

    # ================================================================
    # CATEGORY C: Programming Documentation
    # ================================================================

    def scrape_python_docs(self):
        """Scrape Python official documentation."""
        print("  [WEB] [C] Python docs...")
        count = 0

        pages = [
            'https://docs.python.org/3/tutorial/',
            'https://docs.python.org/3/tutorial/classes.html',
            'https://docs.python.org/3/tutorial/errors.html',
            'https://docs.python.org/3/tutorial/inputoutput.html',
            'https://docs.python.org/3/tutorial/modules.html',
            'https://docs.python.org/3/tutorial/datastructures.html',
            'https://docs.python.org/3/tutorial/introduction.html',
            'https://docs.python.org/3/library/stdtypes.html',
            'https://docs.python.org/3/library/functions.html',
            'https://docs.python.org/3/library/os.html',
            'https://docs.python.org/3/library/json.html',
            'https://docs.python.org/3/library/re.html',
            'https://docs.python.org/3/library/asyncio.html',
            'https://docs.python.org/3/library/threading.html',
            'https://docs.python.org/3/library/multiprocessing.html',
            'https://docs.python.org/3/library/collections.html',
            'https://docs.python.org/3/library/itertools.html',
            'https://docs.python.org/3/library/functools.html',
            'https://docs.python.org/3/library/pathlib.html',
            'https://docs.python.org/3/library/typing.html',
        ]

        for url in pages:
            data = self._fetch(url, timeout=10)
            if not data:
                continue
            # Extract content paragraphs
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', data, re.DOTALL)
            for p in paragraphs:
                text = self._clean_html(p)
                if text and len(text) > 30:
                    self._add(-320, 'Python Docs', 'docs', text[:400])
                    count += 1
            time.sleep(0.2)

        print(f"  [WEB] [C] Python Docs: {count} paragraphs")
        return count

    def scrape_mdn_docs(self):
        """Scrape MDN Web Docs (JavaScript, HTML, CSS)."""
        print("  [WEB] [C] MDN Web Docs...")
        count = 0

        pages = [
            ('JS', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions'),
            ('JS', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Objects'),
            ('JS', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Arrays'),
            ('JS', 'JS', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Promises'),
            ('JS', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules'),
            ('JS', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array'),
            ('JS', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise'),
            ('JS', 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function'),
            ('HTML', 'https://developer.mozilla.org/en-US/docs/Learn/HTML'),
            ('CSS', 'https://developer.mozilla.org/en-US/docs/Learn/CSS'),
            ('API', 'https://developer.mozilla.org/en-US/docs/Learn/Web_APIs'),
            ('React', 'https://developer.mozilla.org/en-US/docs/Learn/Tools_and_testing/Client-side_JavaScript_frameworks/React_getting_started'),
        ]

        for tag, url in pages:
            if len(url) == 2:
                tag, url = url, url
            data = self._fetch(url, timeout=10)
            if not data:
                continue
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', data, re.DOTALL)
            for p in paragraphs:
                text = self._clean_html(p)
                if text and len(text) > 30:
                    self._add(-321, f'MDN {tag}', 'docs', text[:400])
                    count += 1
            time.sleep(0.2)

        print(f"  [WEB] [C] MDN Docs: {count} paragraphs")
        return count

    def scrape_rust_docs(self):
        """Scrape Rust Book and docs."""
        print("  [WEB] [C] Rust docs...")
        count = 0

        pages = [
            'https://doc.rust-lang.org/book/ch03-02-data-types.html',
            'https://doc.rust-lang.org/book/ch03-03-how-it-works.html',
            'https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html',
            'https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html',
            'https://doc.rust-lang.org/book/ch05-01-defining-structs.html',
            'https://doc.rust-lang.org/book/ch06-01-defining-an-enum.html',
            'https://doc.rust-lang.org/book/ch08-01-common-collections.html',
            'https://doc.rust-lang.org/book/ch09-01-error-handling.html',
            'https://doc.rust-lang.org/book/ch10-01-generics.html',
            'https://doc.rust-lang.org/book/ch13-01-closures.html',
        ]

        for url in pages:
            data = self._fetch(url, timeout=10)
            if not data:
                continue
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', data, re.DOTALL)
            for p in paragraphs:
                text = self._clean_html(p)
                if text and len(text) > 30:
                    self._add(-322, 'Rust Book', 'docs', text[:400])
                    count += 1
            time.sleep(0.2)

        print(f"  [WEB] [C] Rust Docs: {count} paragraphs")
        return count

    def scrape_go_docs(self):
        """Scrape Go documentation."""
        print("  [WEB] [C] Go docs...")
        count = 0

        pages = [
            'https://go.dev/doc/effective_go',
            'https://go.dev/doc/tutorial/getting-started',
            'https://go.dev/doc/articles/wiki/',
            'https://go.dev/doc/articles/goslice/',
        ]

        for url in pages:
            data = self._fetch(url, timeout=10)
            if not data:
                continue
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', data, re.DOTALL)
            for p in paragraphs:
                text = self._clean_html(p)
                if text and len(text) > 30:
                    self._add(-323, 'Go Docs', 'docs', text[:400])
                    count += 1
            time.sleep(0.2)

        print(f"  [WEB] [C] Go Docs: {count} paragraphs")
        return count

    def scrape_kotlin_docs(self):
        """Scrape Kotlin documentation."""
        print("  [WEB] [C] Kotlin docs...")
        count = 0

        pages = [
            'https://kotlinlang.org/docs/basic-syntax.html',
            'https://kotlinlang.org/docs/functions.html',
            'https://kotlinlang.org/docs/classes.html',
            'https://kotlinlang.org/docs/null-safety.html',
            'https://kotlinlang.org/docs/coroutines-overview.html',
        ]

        for url in pages:
            data = self._fetch(url, timeout=10)
            if not data:
                continue
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', data, re.DOTALL)
            for p in paragraphs:
                text = self._clean_html(p)
                if text and len(text) > 30:
                    self._add(-324, 'Kotlin Docs', 'docs', text[:400])
                    count += 1
            time.sleep(0.2)

        print(f"  [WEB] [C] Kotlin Docs: {count} paragraphs")
        return count

    def scrape_cpp_docs(self):
        """Scrape C++ reference."""
        print("  [WEB] [C] C++ docs...")
        count = 0

        pages = [
            'https://en.cppreference.com/w/cpp/container/vector',
            'https://en.cppreference.com/w/cpp/container/map',
            'https://en.cppreference.com/w/cpp/language/classes',
            'https://en.cppreference.com/w/cpp/language/templates',
            'https://en.cppreference.com/w/cpp/algorithm/sort',
        ]

        for url in pages:
            data = self._fetch(url, timeout=10)
            if not data:
                continue
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', data, re.DOTALL)
            for p in paragraphs:
                text = self._clean_html(p)
                if text and len(text) > 30:
                    self._add(-325, 'C++ Ref', 'docs', text[:400])
                    count += 1
            time.sleep(0.2)

        print(f"  [WEB] [C] C++ Docs: {count} paragraphs")
        return count

    def scrape_stackoverflow(self):
        """Scrape StackOverflow Q&A."""
        print("  [WEB] [C] StackOverflow...")
        count = 0

        tags = ['python', 'javascript', 'android', 'linux', 'database',
                'rust', 'go', 'kotlin', 'c%2b%2b', 'typescript',
                'docker', 'react', 'node.js', 'django', 'flask']

        for tag in tags:
            url = f"https://api.stackexchange.com/2.3/questions?order=desc&sort=creation&site=stackoverflow&tagged={tag}&filter=withbody&pagesize=15"
            data = self._fetch(url, timeout=10)
            if not data:
                continue
            try:
                items = json.loads(data).get('items', [])
                for item in items:
                    title = item.get('title', '')
                    body = self._clean_html(item.get('body', ''))
                    if title and len(title) > 10:
                        self._add(-326, f'SO #{tag}', 'developer', title)
                        count += 1
                    if body and len(body) > 30:
                        sentences = self._split_sentences(body)
                        for sent in sentences[:2]:
                            self._add(-326, f'SO #{tag}', 'developer', sent)
                            count += 1
            except json.JSONDecodeError:
                pass
            time.sleep(0.2)

        print(f"  [WEB] [C] StackOverflow: {count} entries")
        return count

    def scrape_github_readmes(self):
        """Scrape GitHub trending repos + READMEs."""
        print("  [WEB] [C] GitHub trending...")
        count = 0

        queries = [
            'language:python+stars:>1000',
            'language:javascript+stars:>1000',
            'language:rust+stars:>1000',
            'language:go+stars:>1000',
            'language:java+stars:>1000',
            'language:kotlin+stars:>1000',
            'language:typescript+stars:>500',
            'language:c%2b%2b+stars:>1000',
        ]

        for q in queries:
            url = f"https://api.github.com/search/repositories?q={q}&sort=stars&per_page=10"
            data = self._fetch(url, timeout=15)
            if not data:
                continue
            try:
                repos = json.loads(data).get('items', [])
                for repo in repos:
                    desc = repo.get('description', '')
                    if desc and len(desc) > 10:
                        self._add(-327, 'GitHub', 'developer', desc)
                        count += 1
                    full_name = repo.get('full_name', '')
                    readme_url = f"https://raw.githubusercontent.com/{full_name}/main/README.md"
                    readme = self._fetch(readme_url, timeout=5)
                    if readme:
                        readme = self._clean_html(readme)
                        sentences = self._split_sentences(readme)
                        for sent in sentences[:5]:
                            self._add(-327, 'GitHub README', 'developer', sent)
                            count += 1
                    time.sleep(0.15)
            except (json.JSONDecodeError, KeyError):
                pass
            time.sleep(0.3)

        print(f"  [WEB] [C] GitHub: {count} entries")
        return count

    # ================================================================
    # CATEGORY D: Linux/DevOps Docs
    # ================================================================

    def scrape_linux_docs(self):
        """Scrape Linux/Git/Docker documentation."""
        print("  [WEB] [D] Linux/DevOps docs...")
        count = 0

        pages = [
            ('Git', 'https://git-scm.com/book/en/v2'),
            ('Git', 'https://git-scm.com/docs'),
            ('GitHub', 'https://docs.github.com/en/get-started'),
            ('GitHub', 'https://docs.github.com/en/pull-requests'),
            ('Docker', 'https://docs.docker.com/get-started/overview/'),
            ('Docker', 'https://docs.docker.com/get-started/docker-overview/'),
            ('K8s', 'https://kubernetes.io/docs/concepts/overview/'),
            ('Nginx', 'https://nginx.org/en/docs/'),
            ('Linux', 'https://www.tutorialspoint.com/unix_commands/unix_comm.htm'),
            ('Bash', 'https://www.gnu.org/software/bash/manual/html_node/'),
            ('PostgreSQL', 'https://www.postgresql.org/docs/current/tutorial.html'),
            ('SQLite', 'https://www.sqlite.org/docs.html'),
            ('Redis', 'https://redis.io/docs/'),
        ]

        for tag, url in pages:
            data = self._fetch(url, timeout=10)
            if not data:
                continue
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', data, re.DOTALL)
            for p in paragraphs:
                text = self._clean_html(p)
                if text and len(text) > 30:
                    self._add(-330, f'{tag} Docs', 'docs', text[:400])
                    count += 1
            time.sleep(0.2)

        print(f"  [WEB] [D] DevOps Docs: {count} paragraphs")
        return count

    # ================================================================
    # CATEGORY E: Android/Termux Docs
    # ================================================================

    def scrape_android_docs(self):
        """Scrape Android development docs."""
        print("  [WEB] [E] Android docs...")
        count = 0

        pages = [
            'https://developer.android.com/develop',
            'https://developer.android.com/topic/libraries/architecture',
            'https://developer.android.com/develop/ui/compose',
            'https://developer.android.com/kotlin/coroutines',
        ]

        for url in pages:
            data = self._fetch(url, timeout=10)
            if not data:
                continue
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', data, re.DOTALL)
            for p in paragraphs:
                text = self._clean_html(p)
                if text and len(text) > 30:
                    self._add(-340, 'Android Docs', 'docs', text[:400])
                    count += 1
            time.sleep(0.2)

        # Termux wiki
        termux_pages = [
            'https://github.com/termux/termux-app/wiki',
            'https://wiki.termux.com/wiki/Main_Page',
        ]
        for url in termux_pages:
            data = self._fetch(url, timeout=10)
            if not data:
                continue
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', data, re.DOTALL)
            for p in paragraphs:
                text = self._clean_html(p)
                if text and len(text) > 30:
                    self._add(-340, 'Termux Wiki', 'docs', text[:400])
                    count += 1
            time.sleep(0.2)

        print(f"  [WEB] [E] Android/Termux: {count} paragraphs")
        return count

    # ================================================================
    # CATEGORY F: ML/AI/LLM Docs
    # ================================================================

    def scrape_ml_docs(self):
        """Scrape ML/AI documentation."""
        print("  [WEB] [F] ML/AI docs...")
        count = 0

        pages = [
            ('PyTorch', 'https://pytorch.org/tutorials/beginner/basics/intro.html'),
            ('PyTorch', 'https://pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html'),
            ('PyTorch', 'https://pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html'),
            ('HF', 'https://huggingface.co/docs/transformers/main/en/training'),
            ('HF', 'https://huggingface.co/docs/transformers/main/en/tokenizer_summary'),
            ('HF', 'https://huggingface.co/docs/datasets/en/loading'),
            ('HF', 'https://huggingface.co/docs/peft/en/index'),
            ('TF', 'https://www.tensorflow.org/tutorials/quickstart/beginner'),
            ('TF', 'https://www.tensorflow.org/guide/keras/sequential_model'),
        ]

        for tag, url in pages:
            data = self._fetch(url, timeout=10)
            if not data:
                continue
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', data, re.DOTALL)
            for p in paragraphs:
                text = self._clean_html(p)
                if text and len(text) > 30:
                    self._add(-350, f'{tag} Docs', 'docs', text[:400])
                    count += 1
            time.sleep(0.2)

        print(f"  [WEB] [F] ML/AI Docs: {count} paragraphs")
        return count

    # ================================================================
    # CATEGORY G: AI Coding Benchmark Data
    # ================================================================

    def scrape_code_datasets(self):
        """Scrape coding dataset info from HuggingFace."""
        print("  [WEB] [G] Code datasets info...")
        count = 0

        code_ds = [
            'bigcode/the-stack',
            'bigcode/starcoderdata',
            'github/CodeSearchNet',
        ]

        for ds_id in code_ds:
            url = f"https://huggingface.co/api/datasets/{ds_id}"
            data = self._fetch(url, timeout=10)
            if not data:
                continue
            try:
                info = json.loads(data)
                desc = info.get('description', '') or ''
                desc = self._clean_html(desc)
                if desc and len(desc) > 30:
                    sentences = self._split_sentences(desc)
                    for sent in sentences[:3]:
                        self._add(-360, f'Code DS', 'dataset', sent)
                        count += 1
                tags = info.get('tags', [])
                if tags:
                    tag_str = f"Code dataset {ds_id}: {', '.join(tags[:8])}"
                    self._add(-360, 'Code DS', 'metadata', tag_str)
                    count += 1
            except json.JSONDecodeError:
                pass
            time.sleep(0.2)

        print(f"  [WEB] [G] Code Datasets: {count} entries")
        return count

    # ================================================================
    # CATEGORY H: Conversational/Casual
    # ================================================================

    def scrape_conversational(self):
        """Add conversational + casual Indonesian training data."""
        print("  [WEB] [H] Conversational Indonesian...")
        count = 0

        conversations = [
            # Q&A style
            "bagaimana cara memulai belajar pemrograman?",
            "mulai dari bahasa python karena syntaxnya mudah dipahami",
            "apa bedanya python sama javascript?",
            "python itu backend sedangkan javascript bisa frontend dan backend",
            "kenapa harus belajar git?",
            "git itu version control jadi bisa track perubahan kode",
            "docker itu untuk apa sih?",
            "docker itu untuk containerisasi aplikasi biar portable",
            "apa itu API dalam pemrograman?",
            "API itu Application Programming Interface untuk komunikasi antar sistem",
            "database itu apa?",
            "database itu tempat penyimpanan data secara terstruktur",
            "apa perbedaan SQL dan NoSQL?",
            "SQL pakai tabel relasional sedangkan NoSQL lebih fleksibel",
            "react itu framework atau library?",
            "react itu library untuk membuat user interface",
            "apa itu ORM?",
            "ORM itu Object Relational Mapping biar gampang akses database dari code",
            "cara debugging yang efektif gimana?",
            "mulai dari baca error message, lalu pakai print atau debugger",
            "apa itu unit testing?",
            "unit testing itu menguji fungsi kecil secara individual",
            "kenapa code review itu penting?",
            "code review membantu menemukan bug dan improve code quality",
            "apa itu CI/CD?",
            "CI/CD itu continuous integration dan deployment untuk otomasi",
            "kubernetes itu apa?",
            "kubernetes itu container orchestration untuk manage docker containers",
            "cara belajar coding yang efektif?",
            "practice coding setiap hari dan kerjakan project kecil",
            "python cocok untuk apa?",
            "python cocok untuk web dev, data science, AI, automation, dan scripting",
            "javascript bisa buat apa aja?",
            "javascript bisa buat frontend, backend, mobile app, desktop app, dan game",
            "cara install package di python?",
            "pakai pip install nama_package di terminal",
            "npm itu apa?",
            "npm itu package manager untuk javascript",
            "apa itu terminal?",
            "terminal itu interface berbasis teks untuk jalankan command di komputer",
            "linux lebih bagus atau windows untuk coding?",
            "linux lebih ringan dan sering dipakai untuk server, tapi tergantung kebutuhan",
            "cara memperbaiki error module not found?",
            "install dulu package nya pakai pip atau npm",
            "apa itu version control?",
            "version control itu sistem untuk track dan manage perubahan kode",
            "cara kerja git itu gimana?",
            "git menyimpan snapshot perubahan kode di repository",
            "apa itu branch di git?",
            "branch itu salinan kode untuk develop fitur terpisah tanpa ganggu main branch",
            "cara merge branch di git?",
            "pakai git merge nama_branch atau buat pull request",
            "apa itu pull request?",
            "pull request itu ajukan perubahan untuk direview sebelum di-merge",
            "ubuntu itu distro linux?",
            "ubuntu adalah salah satu distro linux yang paling populer dan user-friendly",
            "cara install ubuntu di virtual machine?",
            "download ISO ubuntu lalu install di VirtualBox atau VMware",
            "apa itu SSH?",
            "SSH itu Secure Shell untuk remote access ke server",
            "cara generate SSH key?",
            "pakai command ssh-keygen di terminal",
            "apa itu nginx?",
            "nginx itu web server yang juga bisa jadi reverse proxy dan load balancer",
            "apache vs nginx lebih bagus mana?",
            "nginx lebih ringan untuk static files, apache lebih fleksibel untuk .htaccess",
            "cara deploy aplikasi ke server?",
            "bisa pakai docker, atau upload langsung ke VPS dengan git push",
            "apa itu VPS?",
            "VPS itu Virtual Private Server yaitu server virtual yang dedicated",
            "heroku itu apa?",
            "heroku itu platform as a service untuk deploy aplikasi tanpa manage server",
            "vercel itu untuk apa?",
            "vercel itu untuk deploy frontend dan serverless functions dengan mudah",
            "cara buat website portfolio?",
            "bikin project react atau nextjs lalu deploy ke vercel atau netlify",
            "apa itu responsive design?",
            "responsive design itu desain website yang menyesuaikan ukuran layar",
            "css grid vs flexbox kapan pakai?",
            "grid untuk layout 2D, flexbox untuk alignment 1D",
            "apa itu javascript framework terbaik?",
            "react, vue, dan angular adalah framework populer tergantung kebutuhan",
            "node.js itu apa?",
            "node.js itu runtime javascript untuk backend server",
            "express.js itu framework apa?",
            "express.js itu minimal web framework untuk node.js",
            "apa itu async await di javascript?",
            "async await itu cara handle promise secara lebih bersih dan readable",
            "javascript promise itu apa?",
            "promise itu representasi nilai yang belum tersedia tapi akan tersedia nanti",
            "closure di javascript itu apa?",
            "closure itu fungsi yang mengakses variabel dari scope luarnya",
            "what is machine learning?",
            "machine learning itu subset AI yang belajar dari data",
            "neural network itu apa?",
            "neural network itu model computing terinspirasi dari otak manusia",
            "deep learning vs machine learning?",
            "deep learning itu subset ML yang pakai neural network dengan banyak layer",
            "tensorflow vs pytorch?",
            "tensorflow dari Google, pytorch dari Meta, keduanya populer untuk deep learning",
            "cara belajar data science?",
            "mulai dari python, statistik, sql, lalu machine learning",
            "data analyst vs data scientist?",
            "data analyst fokus analisis data, data scientist fokus model dan prediksi",
        ]

        for text in conversations:
            self._add(-370, 'Conversations', 'conversation', text)
            count += 1

        print(f"  [WEB] [H] Conversations: {count} entries")
        return count

    # ================================================================
    # MAIN: SCRAPE ALL SOURCES IN PARALLEL
    # ================================================================

    def scrape_all(self):
        """Scrape ALL 180+ sources in PARALLEL for max speed."""
        print("\n" + "=" * 60)
        print("  DikaAI Web Scraper v2 - 180+ Sources PARALLEL")
        print("=" * 60)

        start = time.time()

        # Define all scraper methods with categories
        scrapers = [
            # A: Indonesian NLP (Priority!)
            self.scrape_huggingface_indonesian,
            self.scrape_huggingface_samples,
            self.scrape_wikipedia_id_full,
            # B: Indonesian Corpus
            self.scrape_indonesian_news,
            self.scrape_kaskus_casual,
            self.scrape_indonesian_corpus,
            self.scrape_duckduckgo_indonesian,
            # C: Programming Docs
            self.scrape_python_docs,
            self.scrape_mdn_docs,
            self.scrape_rust_docs,
            self.scrape_go_docs,
            self.scrape_kotlin_docs,
            self.scrape_cpp_docs,
            self.scrape_stackoverflow,
            self.scrape_github_readmes,
            # D: Linux/DevOps
            self.scrape_linux_docs,
            # E: Android/Termux
            self.scrape_android_docs,
            # F: ML/AI
            self.scrape_ml_docs,
            # G: Code Datasets
            self.scrape_code_datasets,
            # H: Conversational
            self.scrape_conversational,
        ]

        print(f"\n  Running {len(scrapers)} scrapers in parallel ({self.max_workers} workers)...")

        # Run all scrapers in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._run_safe, s): s.__name__ for s in scrapers}
            completed = 0
            for future in as_completed(futures):
                name = futures[future]
                completed += 1
                try:
                    result = future.result()
                except Exception as e:
                    print(f"  [WEB] {name} FAILED: {e}")

        elapsed = time.time() - start

        print("\n" + "=" * 60)
        print("  [WEB] SCRAPE COMPLETE!")
        print(f"  [WEB] Time     : {elapsed:.1f}s")
        print(f"  [WEB] Scraped  : {self.stats['scraped']}")
        print(f"  [WEB] New      : {self.stats['new']}")
        print(f"  [WEB] Errors   : {self.stats['errors']}")
        print("=" * 60)

        return self.stats['new']

    def _run_safe(self, func):
        """Run a scraper function with error handling."""
        try:
            return func()
        except Exception as e:
            print(f"  [WEB] {func.__name__} error: {e}")
            return 0


def run_web_scrape():
    """Run web scraping standalone."""
    db = DikaDB()
    scraper = DikaWebScraper(db)
    new = scraper.scrape_all()
    db.close()
    return new


if __name__ == '__main__':
    run_web_scrape()
