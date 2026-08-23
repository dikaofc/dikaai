"""DikaAi Web Scraper - Real Indonesian Web Sources

Sources:
- Wikipedia Indonesia (articles)
- Kaskus (Indonesian forum - slang/casual)
- Detik.com (news)
- Kompas.com (news)
- CodePolitan (coding tutorials)
- Duniailkom (tech tutorials)
- Indonesian blog posts
"""
import urllib.request
import urllib.error
import json
import time
import re
import html
import random
from dikaai.database import DikaDB


class DikaWebScraper:
    def __init__(self, db: DikaDB):
        self.db = db
        self.stats = {
            'scraped': 0,
            'new': 0,
            'duplicates': 0,
            'errors': 0
        }
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    def _fetch(self, url, timeout=15):
        """Fetch URL content with proper headers."""
        try:
            req = urllib.request.Request(url, headers=self._headers)
            resp = urllib.request.urlopen(req, timeout=timeout)
            return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
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
        if len(text) > 300:
            return False
        # Skip code
        if any(x in text for x in ['```', 'def ', 'function ', 'import ', 'from ']):
            return False
        # Skip URLs
        if re.search(r'https?://', text):
            return False
        # Skip very short words
        words = text.split()
        if len(words) < 3:
            return False
        return True

    def _add(self, chat_id, source, sender, message):
        """Add message to database."""
        if self._is_valid(message):
            if self.db.add_message(
                chat_id=chat_id,
                chat_title=source,
                sender_name=sender,
                message=message,
                timestamp=time.time()
            ):
                self.stats['new'] += 1
            self.stats['scraped'] += 1

    # ================================================================
    # SOURCES
    # ================================================================

    def scrape_wikipedia_id(self):
        """Scrape Indonesian Wikipedia articles."""
        print("  [WEB] 📚 Scraping Wikipedia Indonesia...")
        count = 0

        # Popular Indonesian Wikipedia articles
        articles = [
            'Teknologi_informasi', 'Komputer', 'Internet', 'Program_komputer',
            'Artificial_intelligence', 'Machine_learning', 'Python_(bahasa_pemrograman)',
            'JavaScript', 'Android_(sistem_operasi)', 'Linux',
            'Smartphone', 'Cloud_computing', 'Database', 'Web_development',
            'Mobile_app', 'Hackathon', 'Startup', 'Digital_marketing',
            'Social_media', 'E-commerce', 'Fintech', 'Blockchain',
            'Cybersecurity', 'Data_science', 'Big_data', 'Internet_of_things',
            'Virtual_reality', 'Augmented_reality', '5G', 'Open_source',
            'Kecerdasan_buatan', 'Pemrograman', 'Jaringan_komputer',
            'Sistem_operasi', 'Perangkat_lunak', 'Perangkat_keras',
        ]

        for article in articles:
            url = f"https://id.wikipedia.org/api/rest_v1/page/summary/{article}"
            data = self._fetch(url, timeout=10)
            if not data:
                continue

            try:
                info = json.loads(data)
                # Get extract (article summary)
                extract = info.get('extract', '')
                if extract and len(extract) > 50:
                    # Split into sentences
                    sentences = self._split_sentences(extract)
                    for sent in sentences[:5]:  # Max 5 per article
                        self._add(-200, 'Wikipedia ID', 'wiki', sent)
                        count += 1

                # Get description
                desc = info.get('description', '')
                if desc and len(desc) > 15:
                    self._add(-200, 'Wikipedia ID', 'wiki', desc)
                    count += 1

            except json.JSONDecodeError:
                pass

            time.sleep(0.3)  # Be polite

        print(f"  [WEB] ✅ Wikipedia: {count} sentences")
        return count

    def scrape_kaskus(self):
        """Scrape Kaskus trending/popular threads."""
        print("  [WEB] 💬 Scraping Kaskus...")
        count = 0

        # Kaskus API for popular threads
        url = "https://www.kaskus.co.id/api/v2/thread/popular?per_page=30"
        data = self._fetch(url, timeout=15)

        if data:
            try:
                threads = json.loads(data).get('data', [])
                for thread in threads:
                    title = thread.get('title', '')
                    content = thread.get('content', '')

                    if title and len(title) > 10:
                        self._add(-201, 'Kaskus', 'kaskuser', title)
                        count += 1

                    if content:
                        # Clean HTML
                        content = self._clean_html(content)
                        sentences = self._split_sentences(content)
                        for sent in sentences[:3]:
                            self._add(-201, 'Kaskus', 'kaskuser', sent)
                            count += 1

            except (json.JSONDecodeError, KeyError):
                pass

        # Also try Kaskus hot threads
        url2 = "https://www.kaskus.co.id/api/v2/thread/hot?per_page=20"
        data2 = self._fetch(url2, timeout=15)
        if data2:
            try:
                threads = json.loads(data2).get('data', [])
                for thread in threads:
                    title = thread.get('title', '')
                    if title and len(title) > 10:
                        self._add(-201, 'Kaskus Hot', 'kaskuser', title)
                        count += 1
            except (json.JSONDecodeError, KeyError):
                pass

        print(f"  [WEB] ✅ Kaskus: {count} posts")
        return count

    def scrape_detik(self):
        """Scrape Detik.com news headlines and snippets."""
        print("  [WEB] 📰 Scraping Detik.com...")
        count = 0

        # Detik RSS feeds (updated URLs)
        feeds = [
            'https://www.detik.com/tekno/rss',
            'https://www.detik.com/news/rss',
        ]

        for feed_url in feeds:
            data = self._fetch(feed_url, timeout=10)
            if not data:
                continue

            # Parse RSS XML (simple regex)
            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', data)
            descs = re.findall(r'<description><!\[CDATA\[(.*?)\]\]></description>', data)

            for title in titles:
                title = self._clean_html(title)
                if title and len(title) > 15:
                    self._add(-202, 'Detik', 'news', title)
                    count += 1

            for desc in descs:
                desc = self._clean_html(desc)
                sentences = self._split_sentences(desc)
                for sent in sentences[:2]:
                    self._add(-202, 'Detik', 'news', sent)
                    count += 1

            time.sleep(0.5)

        print(f"  [WEB] ✅ Detik: {count} articles")
        return count

    def scrape_kompas(self):
        """Scrape Kompas.com news."""
        print("  [WEB] 📰 Scraping Kompas.com...")
        count = 0

        # Kompas RSS (updated URLs)
        feeds = [
            'https://www.kompas.com/rss/tekno',
            'https://tekno.kompas.com/rss',
        ]

        for feed_url in feeds:
            data = self._fetch(feed_url, timeout=10)
            if not data:
                continue

            # Parse RSS
            items = re.findall(r'<item>(.*?)</item>', data, re.DOTALL)
            for item in items:
                title_match = re.search(r'<title>(.*?)</title>', item)
                desc_match = re.search(r'<description>(.*?)</description>', item, re.DOTALL)

                if title_match:
                    title = self._clean_html(title_match.group(1))
                    if title and len(title) > 15:
                        self._add(-203, 'Kompas', 'news', title)
                        count += 1

                if desc_match:
                    desc = self._clean_html(desc_match.group(1))
                    sentences = self._split_sentences(desc)
                    for sent in sentences[:2]:
                        self._add(-203, 'Kompas', 'news', sent)
                        count += 1

            time.sleep(0.5)

        print(f"  [WEB] ✅ Kompas: {count} articles")
        return count

    def scrape_medium_id(self):
        """Scrape Medium Indonesia tech articles."""
        print("  [WEB] 📝 Scraping Medium Indonesia...")
        count = 0

        # Medium tag search for Indonesian tech topics
        tags = ['python', 'javascript', 'react', 'nodejs', 'android', 'linux']
        for tag in tags:
            url = f"https://medium.com/tag/{tag}/recommended"
            data = self._fetch(url, timeout=10)
            if not data:
                continue

            # Extract article titles from HTML
            titles = re.findall(r'<h3[^>]*>(.*?)</h3>', data)
            for title in titles:
                title = self._clean_html(title)
                if title and len(title) > 15 and len(title) < 200:
                    self._add(-204, f'Medium #{tag}', 'writer', title)
                    count += 1

            time.sleep(0.3)

        print(f"  [WEB] ✅ Medium: {count} titles")
        return count

    def scrape_github_trending(self):
        """Scrape GitHub trending repos with Indonesian README."""
        print("  [WEB] 🐙 Scraping GitHub Trending...")
        count = 0

        # GitHub trending API
        url = "https://api.github.com/search/repositories?q=language:indonesian&sort=stars&per_page=30"
        data = self._fetch(url, timeout=15)

        if data:
            try:
                repos = json.loads(data).get('items', [])
                for repo in repos[:20]:
                    # Get description
                    desc = repo.get('description', '')
                    if desc and len(desc) > 10:
                        self._add(-205, 'GitHub', 'developer', desc)
                        count += 1

                    # Get README
                    full_name = repo.get('full_name', '')
                    readme_url = f"https://raw.githubusercontent.com/{full_name}/main/README.md"
                    readme = self._fetch(readme_url, timeout=5)
                    if readme:
                        readme = self._clean_html(readme)
                        sentences = self._split_sentences(readme)
                        for sent in sentences[:5]:
                            self._add(-205, 'GitHub README', 'developer', sent)
                            count += 1

                    time.sleep(0.2)

            except (json.JSONDecodeError, KeyError):
                pass

        print(f"  [WEB] ✅ GitHub: {count} entries")
        return count

    def scrape_stackoverflow_id(self):
        """Scrape StackOverflow Indonesian Q&A."""
        print("  [WEB] 🔍 Scraping StackOverflow Indonesia...")
        count = 0

        # StackOverflow API - search for Indonesian questions
        tags = ['python', 'javascript', 'android', 'linux', 'database']
        for tag in tags:
            url = f"https://api.stackexchange.com/2.3/questions?order=desc&sort=creation&site=stackoverflow&tagged={tag}&filter=withbody&pagesize=20"
            data = self._fetch(url, timeout=10)
            if not data:
                continue

            try:
                items = json.loads(data).get('items', [])
                for item in items:
                    title = item.get('title', '')
                    if title and len(title) > 10:
                        self._add(-206, f'SO #{tag}', 'developer', title)
                        count += 1
            except json.JSONDecodeError:
                pass

            time.sleep(0.3)

        print(f"  [WEB] ✅ StackOverflow: {count} questions")
        return count

    def scrape_indonesian_corpus(self):
        """Add curated Indonesian text corpus."""
        print("  [WEB] 📖 Adding Indonesian corpus...")
        count = 0

        # Indonesian common phrases (realistic, diverse)
        corpus = [
            # Conversational
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

            # Tech/Coding
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

            # Casual chat
            "lagi cari info soal hp baru nih",
            "recommend dong laptop buat coding budget 5 juta",
            "wifi kok lambat banget ya",
            "mau nonton film apa malam ini",
            "besok weekend mau kemana",
            "udah download game nya belum",
            "anime apa yang lagi hot sekarang",
            "recipe masakan sederhana buat pemula",
            "traveling ke mana ya weekend ini",
            "tips belajar coding buat pemula",
            "cara mengatasi laptop lemot",
            "rekomendasi HP gaming murah",
            "cara backup data android ke cloud",
            "aplikasi editing video yang ringan",
            "cara hemat kuota internet",
            "tips belajar bahasa inggris gratis",
            "cara membuat website portfolio",
            "tutorial photoshop untuk pemula",
            "cara instal linux di laptop",
            "belajar desain grafis dari mana",

            # Business/Tech news
            "startup Indonesia yang lagi naik daun",
            "fintech di Indonesia makin berkembang",
            "digital transformation untuk UMKM",
            "e-commerce Indonesia kompetitif banget",
            "crypto dan blockchain masa depan",
            "AI artificial intelligence makin canggih",
            "5G internet super cepat di Indonesia",
            "remote work trend setelah pandemi",
            "sustainability teknologi hijau",
            "smart city kota pintar di Indonesia",

            # Education
            "belajar pemrograman dari nol",
            "kursus online gratis sertifikat",
            "universitas terbaik di Indonesia untuk IT",
            "beasiswa kuliah ke luar negeri",
            "tips lulus ujian nasional",
            "belajar matematika yang menyenangkan",
            "cara belajar efektif dan efisien",
            "ilmu komputer itu apa aja isinya",
            "data science karir yang menjanjikan",
            "fullstack developer gajinya berapa",
        ]

        for text in corpus:
            self._add(-207, 'Indonesian Corpus', 'corpus', text)
            count += 1

        print(f"  [WEB] ✅ Corpus: {count} phrases")
        return count

    def scrape_duckduckgo(self):
        """Scrape DuckDuckGo for Indonesian content."""
        print("  [WEB] 🦆 Scraping DuckDuckGo...")
        count = 0

        queries = [
            'tutorial python indonesia', 'belajar javascript pemula',
            'cara install linux ubuntu', 'react native tutorial indo',
            'machine learning untuk pemula', 'cara buat website sendiri',
            'tips belajar coding', 'framework javascript terbaik 2024',
            'cara deploy aplikasi ke server', 'database postgresql tutorial',
            'docker untuk pemula', 'git tutorial bahasa indonesia',
            'cara buat api rest', 'mobile app development indonesia',
            'cybersecurity tips developer', 'cloud computing indonesia',
            'cara belajar data science', 'flutter tutorial indonesia',
            'node js express tutorial', 'django python web framework',
            'cara install docker di ubuntu', 'kubernetes untuk pemula',
            'nginx reverse proxy tutorial', 'redis caching tutorial',
            'mongodb tutorial indonesia', 'linux command line dasar',
            'cara buat bot telegram', 'web scraping python',
            'fastapi tutorial indonesia', 'svelte tutorial pemula',
            'tailwind css tutorial indonesia', 'typescript tutorial dasar',
            'golang tutorial indonesia', 'rust programming pemula',
            'cara belajar algorithm', 'data structure indonesia',
            'cara optimasi website', 'seo tips indonesia',
            'digital marketing strategy', 'social media management',
            'content creator indonesia tips', 'affiliate marketing indo',
        ]

        for query in queries:
            url = f'https://html.duckduckgo.com/html/?q={query.replace(" ", "+")}'
            data = self._fetch(url, timeout=10)
            if not data:
                continue

            # Extract result snippets
            snippets = re.findall(r'class="result__snippet">(.*?)</a>', data, re.DOTALL)
            for snippet in snippets[:3]:
                text = self._clean_html(snippet)
                if text and len(text) > 20:
                    self._add(-208, f'DDG #{query[:15]}', 'search', text)
                    count += 1

            # Extract result titles
            titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', data, re.DOTALL)
            for title in titles[:3]:
                text = self._clean_html(title)
                if text and len(text) > 10:
                    self._add(-208, f'DDG #{query[:15]}', 'search', text)
                    count += 1

            time.sleep(0.5)  # Be polite

        print(f"  [WEB] ✅ DuckDuckGo: {count} results")
        return count

    def scrape_wikipedia_full(self):
        """Scrape FULL Wikipedia articles (not just summaries)."""
        print("  [WEB] 📚 Scraping Wikipedia Full Articles...")
        count = 0

        articles = [
            # Core tech
            'Pemrograman', 'Python_(bahasa_pemrograman)', 'JavaScript',
            'Java_(bahasa_pemrograman)', 'C_(bahasa_pemrograman)', 'C++',
            'Go_(bahasa_pemrograman)', 'Rust_(bahasa_pemrograman)',
            'TypeScript', 'PHP', 'Ruby', 'Swift_(bahasa_pemrograman)',
            'Kotlin', 'Scala_(bahasa_pemrograman)',
            # Systems
            'Linux', 'Ubuntu_(sistem_operasi)', 'Windows', 'macOS',
            'Android_(sistem_operasi)', 'iOS', 'ChromeOS',
            'Sistem_operasi', 'Jaringan_komputer', 'Komputer',
            # Web & Mobile
            'Web_development', 'Mobile_app', 'React_(pustakaJavaScript)',
            'Vue.js', 'Angular_(frameworkweb)', 'Node.js', 'Django',
            'Laravel', 'Ruby_on_Rails', 'Express.js', 'Flask_(frameworkweb)',
            'WordPress', 'HTML', 'CSS', 'API',
            # Data & AI
            'Database', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis',
            'Kecerdasan_buatan', 'Machine_learning', 'Deep_learning',
            'Data_science', 'Big_data', 'Natural_language_processing',
            'TensorFlow', 'PyTorch', 'Pandas_(perangkat_lunak)',
            # Cloud & DevOps
            'Cloud_computing', 'Amazon_Web_Services', 'Microsoft_Azure',
            'Google_Cloud_Platform', 'Docker_(perangkat_lunak)',
            'Kubernetes', 'DevOps', 'CI/CD', 'Nginx', 'Apache',
            # Security
            'Cybersecurity', 'Keamanan_komputer', 'Kriptografi',
            'Ethical_hacking', 'Firewall_(jaringan)',
            # Business & Internet
            'Internet', 'Internet_of_things', 'Blockchain',
            'Cryptocurrency', 'Bitcoin', 'E-commerce', 'Fintech',
            'Startup', 'Digital_marketing', 'Social_media',
            'Open_source', 'GPL', 'MIT_License',
            # Misc tech
            '5G', 'Smartphone', 'Laptop', 'Komputer_pribadi',
            'Virtual_reality', 'Augmented_reality', 'Game',
            'Perangkat_lunak', 'Perangkat_keras',
            # Programming concepts
            'Algoritma', 'Struktur_data', 'Pemrograman berorientasi objek',
            'Functional_programming', 'Recursion', 'Sorting_algorithm',
            'Search_algorithm', 'Graph_theory',
        ]

        for article in articles:
            # Use Wikipedia REST API to get summary + extract
            url = f'https://id.wikipedia.org/api/rest_v1/page/summary/{article}'
            data = self._fetch(url, timeout=10)
            if not data:
                continue

            try:
                info = json.loads(data)
                extract = info.get('extract', '')
                if extract and len(extract) > 50:
                    sentences = self._split_sentences(extract)
                    for sent in sentences[:10]:
                        self._add(-209, 'Wikipedia Full', 'wiki', sent)
                        count += 1

                desc = info.get('description', '')
                if desc and len(desc) > 15:
                    self._add(-209, 'Wikipedia Full', 'wiki', desc)
                    count += 1
            except json.JSONDecodeError:
                pass

            time.sleep(0.2)

        print(f"  [WEB] ✅ Wikipedia Full: {count} sentences")
        return count

    def scrape_jalantikus(self):
        """Scrape Jalantikus tech articles."""
        print("  [WEB] 📱 Scraping Jalantikus...")
        count = 0

        # Jalantikus RSS
        feeds = [
            'https://www.jalantikus.com/feed/',
            'https://www.jalantikus.com/news/feed/',
        ]

        for feed_url in feeds:
            data = self._fetch(feed_url, timeout=10)
            if not data:
                continue

            # Parse RSS
            items = re.findall(r'<item>(.*?)</item>', data, re.DOTALL)
            for item in items:
                title_match = re.search(r'<title>(.*?)</title>', item)
                desc_match = re.search(r'<description>(.*?)</description>', item, re.DOTALL)

                if title_match:
                    title = self._clean_html(title_match.group(1))
                    if title and len(title) > 15:
                        self._add(-210, 'Jalantikus', 'tech', title)
                        count += 1

                if desc_match:
                    desc = self._clean_html(desc_match.group(1))
                    sentences = self._split_sentences(desc)
                    for sent in sentences[:3]:
                        self._add(-210, 'Jalantikus', 'tech', sent)
                        count += 1

            time.sleep(0.5)

        print(f"  [WEB] ✅ Jalantikus: {count} articles")
        return count

    def scrape_cnn_indonesia(self):
        """Scrape CNN Indonesia news."""
        print("  [WEB] 📰 Scraping CNN Indonesia...")
        count = 0

        feeds = [
            'https://www.cnnindonesia.com/nasional/rss',
            'https://www.cnnindalia.com/teknologi/rss',
        ]

        for feed_url in feeds:
            data = self._fetch(feed_url, timeout=10)
            if not data:
                continue

            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', data)
            for title in titles:
                title = self._clean_html(title)
                if title and len(title) > 15:
                    self._add(-211, 'CNN Indonesia', 'news', title)
                    count += 1

            descs = re.findall(r'<description><!\[CDATA\[(.*?)\]\]></description>', data)
            for desc in descs:
                desc = self._clean_html(desc)
                sentences = self._split_sentences(desc)
                for sent in sentences[:2]:
                    self._add(-211, 'CNN Indonesia', 'news', sent)
                    count += 1

            time.sleep(0.5)

        print(f"  [WEB] ✅ CNN Indonesia: {count} articles")
        return count

    def scrape_liputan6(self):
        """Scrape Liputan6 news."""
        print("  [WEB] 📰 Scraping Liputan6...")
        count = 0

        feeds = [
            'https://www.liputan6.com/rss',
            'https://www.liputan6.com/rss/tekno',
        ]

        for feed_url in feeds:
            data = self._fetch(feed_url, timeout=10)
            if not data:
                continue

            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', data)
            for title in titles:
                title = self._clean_html(title)
                if title and len(title) > 15:
                    self._add(-212, 'Liputan6', 'news', title)
                    count += 1

            descs = re.findall(r'<description><!\[CDATA\[(.*?)\]\]></description>', data)
            for desc in descs:
                desc = self._clean_html(desc)
                sentences = self._split_sentences(desc)
                for sent in sentences[:2]:
                    self._add(-212, 'Liputan6', 'news', sent)
                    count += 1

            time.sleep(0.5)

        print(f"  [WEB] ✅ Liputan6: {count} articles")
        return count

    def scrape_all(self):
        """Scrape ALL sources - prioritize web data for training."""
        print("\n" + "=" * 50)
        print("  DikaAi Web Scraper 🌐 (Priority Mode)")
        print("=" * 50)

        start = time.time()

        # Run working scrapers (skip broken sources)
        print("\n  --- Phase 1: Indonesian Corpus ---")
        self.scrape_indonesian_corpus()
        time.sleep(0.3)

        print("\n  --- Phase 2: Wikipedia (Full + Summary) ---")
        self.scrape_wikipedia_full()
        time.sleep(0.3)
        self.scrape_wikipedia_id()
        time.sleep(0.3)

        print("\n  --- Phase 3: Tech & Coding ---")
        self.scrape_stackoverflow_id()
        time.sleep(0.3)
        self.scrape_github_trending()
        time.sleep(0.3)

        elapsed = time.time() - start

        print("\n" + "=" * 50)
        print("  [WEB] 📊 Scrape Complete!")
        print(f"  [WEB] Time: {elapsed:.1f}s")
        print(f"  [WEB] Total scraped: {self.stats['scraped']}")
        print(f"  [WEB] New (unique): {self.stats['new']}")
        print(f"  [WEB] Errors: {self.stats['errors']}")
        print("=" * 50)

        return self.stats['new']


def run_web_scrape():
    """Run web scraping standalone."""
    db = DikaDB()
    scraper = DikaWebScraper(db)
    new = scraper.scrape_all()
    db.close()
    return new


if __name__ == '__main__':
    run_web_scrape()
