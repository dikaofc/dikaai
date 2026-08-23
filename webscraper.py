"""DikaAi Web Scraper - Train from Indonesian websites

Sources:
- Indonesian tech forums
- Indonesian coding tutorials
- Indonesian design resources
- Indonesian phone modding
- Indonesian slang/gaul
- Indonesian documentation
"""
import urllib.request
import urllib.error
import json
import time
import re
import html
from database import DikaDB

# Indonesian content sources
SOURCES = {
    # Tech & Coding
    "stack_overflow_id": "https://api.stackexchange.com/2.3/questions?order=desc&sort=creation&site=stackoverflow&filter=withbody&tagged=indonesian&pagesize=100",
    "github_trending_id": "https://api.github.com/search/repositories?q=language:indonesian+README&sort=stars&per_page=50",
    
    # Indonesian text corpus (common phrases, slang, etc.)
    "common_phrases": [
        # Greeting & Social
        "halo apa kabar", "selamat pagi", "selamat siang", "selamat sore", "selamat malam",
        "terima kasih", "sama sama", "permisi", "maaf ya", "minta tolong",
        "selamat datang", "selamat jalan", "hati hati", "take care", "sampai jumpa",
        
        # Questions
        "apa kabar", "kamu lagi apa", "udah makan belum", "lagi dimana",
        "siapa nama kamu", "berapa umur kamu", "kapan ketemu",
        "kenapa gitu", "gimana caranya", "dimana lokasinya",
        
        # Responses
        "baik baik saja", "alhamdulillah", "lumayan", "biasa aja",
        "mantap", "oke siap", "gas gas gas", "yuk kita mulai",
        "setuju", "bener banget", "iyalah", "pasti dong",
        
        # Slang/Gaul
        "anjay", "masyaallah", "astagfirullah", "waduh", "wah keren",
        "gokil", "gila sih", "parah banget", "edan", "najong",
        "cuaks", "mantul", "kece", "hits", "viral",
        "auto", "skill issue", "noob", "pro player", "main character",
        
        # Tech/Coding
        "error dong", "bug apa nih", "fix udah", "deploy yuk",
        "push ke main", "merge conflict", "code review",
        "function ini buat apa", "return apa ya", "parameter apa nih",
        "database down", "server error", "404 not found",
        "api call gagal", "timeout", "connection refused",
        
        # Phone/Oprek
        "root dulu hp nya", "unlock bootloader", "install custom recovery",
        "flash custom rom", "backup data dulu", "wipe cache",
        "custom kernel", "overclock gpu", "tweak performance",
        "battery drain", "overheating", "bootloop",
        "twrp recovery", "magisk root", "lsposed",
        
        # Chat casual
        "bro", "bang", "sis", "gan", "sis", "min", "kak",
        "gw", "gue", "lu", "lo", "gw", "loe", "kamu",
        "yang", "yg", "dong", "sih", "nih", "deh", "lah",
        "aja", "aja", "banget", "bgt", "bngt", "parah",
        "mantap", "mntp", "sip", "sipp", "oke", "ok",
        "gas", "gass", "yuk", "yuks", "ayo", "ay",
        
        # Emotions
        "sedih banget", "seneng banget", "kesel", "dongkol",
        " excited", "cant wait", "udah ga sabar", "paling suka",
        "benci", "maafin", "tolong", "please", "plis",
        
        # Common patterns
        "gue cerita ya", "kamu tau ga", "menurut gua",
        "kayak gini", "kayak gitu", "contohnya",
        "intinya", "singkatnya", "simple aja",
        "bahasanya", "kodenya", "codenya",
        
        # Coding specific
        "python indo", "javascript indo", "react indo",
        "node js indonesia", "php indo", "laravel indo",
        "django indo", "flask indo", "fastapi indo",
        "mysql indonesia", "postgresql indo", "mongodb indo",
        "docker indonesia", "kubernetes indo", "aws indo",
        "git github", "cicd pipeline", "devops indo",
        
        # Design
        "figma indo", "canva indo", "photoshop indo",
        "ui ux indonesia", "design system", "color palette",
        "typography indo", "responsive design", "mobile first",
        "dark mode", "light mode", "glassmorphism",
        
        # Full Stack
        "frontend indo", "backend indo", "fullstack indo",
        "api design", "rest api", "graphql indo",
        "authentication", "authorization", "middleware",
        "database design", "schema design", "migration",
        "testing", "unit test", "integration test",
        "deployment", "ci cd", "monitoring",
        
        # Coding Q&A Indonesia
        "cara install python di ubuntu",
        "gimana cara buat function di python",
        "error module not found python",
        "cara package di python",
        "python list comprehension",
        "python dictionary comprehension",
        "python async await",
        "python decorators",
        "python context manager",
        "cara baca file di python",
        "cara tulis file di python",
        "python error handling try except",
        "python class dan object",
        "python inheritance",
        "python lambda function",
        "cara buat api di python",
        "python requests library",
        "python beautifulsoup web scraping",
        "python sqlalchemy ORM",
        "python flask web app",
        "python fastapi rest api",
        "python django web framework",
        
        # JavaScript Q&A
        "cara buat function di javascript",
        "javascript array methods",
        "javascript promise async await",
        "javascript event loop",
        "javascript closure",
        "javascript prototype chain",
        "cara buat api express js",
        "react hooks useState useEffect",
        "react context api",
        "next js server side rendering",
        "vue js composition api",
        "node js event emitters",
        
        # Database Q&A
        "cara buat table di mysql",
        "mysql join query",
        "postgresql vs mysql",
        "mongodb aggregation pipeline",
        "redis caching strategy",
        "database indexing optimization",
        "sql query optimization",
        "database migration strategy",
        
        # DevOps Q&A
        "cara install docker ubuntu",
        "docker compose tutorial",
        "dockerfile best practices",
        "kubernetes pods explained",
        "nginx reverse proxy setup",
        "linux command line basics",
        "git branching strategy",
        "github actions tutorial",
        "ci cd pipeline setup",
        "aws lambda tutorial",
        "cloud deployment strategy",
        
        # Mobile Q&A
        "cara buat app android kotlin",
        "flutter state management",
        "react native navigation",
        "android studio setup tutorial",
        "mobile app testing strategy",
        "app publishing google play",
        
        # Security Q&A
        "authentication vs authorization",
        "jwt token explained",
        "oauth2 flow diagram",
        "cors policy setup",
        "sql injection prevention",
        "xss attack prevention",
        "csrf protection explained",
        "https ssl certificate setup",
        "password hashing bcrypt",
        "security headers best practices",
        
        # AI/ML Q&A
        "machine learning algorithm types",
        "neural network explained simply",
        "tensorflow vs pytorch comparison",
        "nlp text processing steps",
        "computer vision basics",
        "transformer architecture explained",
        "gpt model explained simply",
        "training vs inference explained",
        "overfitting underfitting solution",
        "data preprocessing steps",
    ],
    
    # Indonesian documentation
    "indo_docs": [
        # Python Indonesia
        "panduan python untuk pemula",
        "tutorial python bahasa indonesia",
        "belajar python dari nol",
        "python untuk data science",
        "python untuk web development",
        "python untuk automation",
        "django tutorial indonesia",
        "flask tutorial indonesia",
        "fastapi tutorial indonesia",
        
        # JavaScript Indonesia
        "tutorial javascript indonesia",
        "belajar javascript pemula",
        "react tutorial indonesia",
        "vue tutorial indonesia",
        "node js indonesia",
        "express js indonesia",
        "next js indonesia",
        
        # Mobile Development
        "tutorial android studio",
        "belajar kotlin android",
        "flutter tutorial indonesia",
        "react native indonesia",
        "ionic tutorial indonesia",
        
        # DevOps
        "tutorial docker indonesia",
        "belajar kubernetes",
        "tutorial linux indonesia",
        "belajar git github",
        "tutorial nginx",
        "tutorial ubuntu server",
        
        # Database
        "tutorial mysql indonesia",
        "belajar postgresql",
        "tutorial mongodb indonesia",
        "belajar redis",
        "tutorial elasticsearch",
        
        # Security
        "tutorial cybersecurity indonesia",
        "belajar ethical hacking",
        "tutorial penetration testing",
        "belajar network security",
        
        # AI/ML
        "tutorial machine learning indonesia",
        "belajar deep learning",
        "tutorial tensorflow indonesia",
        "belajar pytorch indonesia",
        "tutorial nlp indonesia",
    ],
}


class DikaWebScraper:
    def __init__(self, db: DikaDB):
        self.db = db
        self.stats = {
            'scraped': 0,
            'new': 0,
            'duplicates': 0,
            'errors': 0
        }
        # Add web-specific chat IDs
        self._web_chats = set()
    
    def _fetch_url(self, url, timeout=10):
        """Fetch URL content."""
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'DikaAi/1.0 (Indonesian AI Training)',
                'Accept': 'application/json'
            })
            response = urllib.request.urlopen(req, timeout=timeout)
            return response.read().decode('utf-8', errors='ignore')
        except Exception as e:
            self.stats['errors'] += 1
            return None
    
    def _clean_html(self, text):
        """Remove HTML tags and entities."""
        text = html.unescape(text)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _is_valid_message(self, text):
        """Check if text is valid for training."""
        if not text or len(text) < 5:
            return False
        if len(text) > 500:
            return False
        # Skip code blocks
        if '```' in text or 'def ' in text or 'function ' in text:
            return False
        return True
    
    def _safe_add(self, chat_id, chat_title, sender_name, message, timestamp):
        """Add message with error handling for locks."""
        import sqlite3
        try:
            return self.db.add_message(chat_id, chat_title, sender_name, message, timestamp)
        except sqlite3.OperationalError:
            time.sleep(0.1)  # Wait and retry
            try:
                return self.db.add_message(chat_id, chat_title, sender_name, message, timestamp)
            except Exception:
                return False
    
    def scrape_common_phrases(self):
        """Add common Indonesian phrases to database."""
        print("  [WEB] Adding common Indonesian phrases...")
        count = 0
        
        for phrase in SOURCES['common_phrases']:
            if self._safe_add(
                chat_id=-100,  # Special ID for web data
                chat_title='Common Indonesian',
                sender_name='corpus',
                message=phrase,
                timestamp=time.time()
            ):
                count += 1
                self.stats['new'] += 1
            self.stats['scraped'] += 1
        
        print(f"  [WEB] ✅ Added {count} common phrases")
        return count
    
    def scrape_stackoverflow(self):
        """Scrape Indonesian StackOverflow questions."""
        print("  [WEB] Scraping StackOverflow (Indonesian)...")
        count = 0
        
        url = SOURCES['stack_overflow_id']
        data = self._fetch_url(url)
        
        if data:
            try:
                items = json.loads(data).get('items', [])
                for item in items:
                    title = item.get('title', '')
                    body = self._clean_html(item.get('body', ''))
                    
                    if self._is_valid_message(title):
                        if self._safe_add(
                            chat_id=-101,
                            chat_title='StackOverflow ID',
                            sender_name='developer',
                            message=title,
                            timestamp=time.time()
                        ):
                            count += 1
                            self.stats['new'] += 1
                        self.stats['scraped'] += 1
                    
                    if self._is_valid_message(body):
                        # Split long body into sentences
                        sentences = re.split(r'[.!?]+', body)
                        for sent in sentences[:3]:  # Max 3 sentences
                            sent = sent.strip()
                    if self._is_valid_message(sent):
                        if self._safe_add(
                            chat_id=-101,
                            chat_title='StackOverflow ID',
                            sender_name='developer',
                            message=sent,
                            timestamp=time.time()
                        ):
                            count += 1
                            self.stats['new'] += 1
                        self.stats['scraped'] += 1
            except json.JSONDecodeError:
                pass
        
        print(f"  [WEB] ✅ Added {count} StackOverflow messages")
        return count
    
    def scrape_github_readmes(self):
        """Scrape Indonesian GitHub README content."""
        print("  [WEB] Scraping GitHub READMEs (Indonesian)...")
        count = 0
        
        url = SOURCES['github_trending_id']
        data = self._fetch_url(url)
        
        if data:
            try:
                repos = json.loads(data).get('items', [])
                for repo in repos[:20]:  # Top 20 repos
                    readme_url = f"https://raw.githubusercontent.com/{repo['full_name']}/main/README.md"
                    readme = self._fetch_url(readme_url, timeout=5)
                    
                    if readme:
                        # Clean and split into sentences
                        readme = self._clean_html(readme)
                        sentences = re.split(r'[.!?]+', readme)
                        
                        for sent in sentences[:10]:  # Max 10 sentences per repo
                            sent = sent.strip()
                            if self._is_valid_message(sent):
                                if self._safe_add(
                                    chat_id=-102,
                                    chat_title='GitHub README',
                                    sender_name='developer',
                                    message=sent,
                                    timestamp=time.time()
                                ):
                                    count += 1
                                    self.stats['new'] += 1
                                self.stats['scraped'] += 1
            except json.JSONDecodeError:
                pass
        
        print(f"  [WEB] ✅ Added {count} GitHub messages")
        return count
    
    def scrape_indo_docs(self):
        """Add Indonesian documentation content."""
        print("  [WEB] Adding Indonesian documentation...")
        count = 0
        
        for doc in SOURCES['indo_docs']:
            if self._safe_add(
                chat_id=-103,
                chat_title='Indonesian Docs',
                sender_name='documentation',
                message=doc,
                timestamp=time.time()
            ):
                count += 1
                self.stats['new'] += 1
            self.stats['scraped'] += 1
        
        print(f"  [WEB] ✅ Added {count} documentation entries")
        return count
    
    def scrape_code_snippets(self):
        """Add coding examples and snippets."""
        print("  [WEB] Adding coding examples...")
        count = 0
        
        code_examples = [
            # Python
            "def hello_world(): print('Hello World')",
            "for i in range(10): print(i)",
            "if x > 0: print('positive')",
            "try: result = 10 / 0 except: print('error')",
            "class Animal: def __init__(self, name): self.name = name",
            "import os; print(os.getcwd())",
            "with open('file.txt') as f: data = f.read()",
            "lambda x: x * 2",
            "[i for i in range(10) if i % 2 == 0]",
            "{'key': 'value' for key in ['a', 'b']}",
            
            # JavaScript
            "const hello = () => console.log('Hello')",
            "for (let i = 0; i < 10; i++) console.log(i)",
            "if (x > 0) console.log('positive')",
            "try { } catch (e) { console.log(e) }",
            "class Animal { constructor(name) { this.name = name } }",
            "import React from 'react'",
            "const [state, setState] = useState(0)",
            "useEffect(() => {}, [])",
            "fetch('api/data').then(res => res.json())",
            "async function getData() { await fetch(url) }",
            
            # HTML/CSS
            "<div class='container'>Content</div>",
            "<form method='POST' action='/submit'>",
            "<input type='text' placeholder='Name'>",
            "<button type='submit'>Submit</button>",
            ".container { max-width: 1200px; margin: 0 auto; }",
            ".btn { background: blue; color: white; padding: 10px; }",
            "@media (max-width: 768px) { .container { width: 100%; } }",
            "display: flex; justify-content: center; align-items: center;",
            "position: absolute; top: 0; left: 0; right: 0; bottom: 0;",
            
            # SQL
            "SELECT * FROM users WHERE age > 18",
            "INSERT INTO users (name, email) VALUES ('John', 'john@test.com')",
            "UPDATE users SET name = 'Jane' WHERE id = 1",
            "DELETE FROM users WHERE id = 1",
            "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))",
            "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id",
            "SELECT department, COUNT(*) as count FROM employees GROUP BY department",
            "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)",
            
            # Git
            "git init; git add .; git commit -m 'initial commit'",
            "git clone https://github.com/user/repo.git",
            "git checkout -b feature/new-feature",
            "git merge feature/new-feature",
            "git pull origin main",
            "git push origin main",
            "git stash; git stash pop",
            "git log --oneline --graph",
            
            # Docker
            "docker run -d -p 8080:80 nginx",
            "docker build -t myapp .",
            "docker-compose up -d",
            "docker exec -it container_name bash",
            "docker logs container_name",
            "docker ps -a",
            "docker stop container_name",
            
            # Linux
            "ls -la; cd /home; mkdir newdir",
            "chmod 755 script.sh; ./script.sh",
            "grep -r 'pattern' /path/to/dir",
            "find / -name '*.py' -type f",
            "curl -X POST -H 'Content-Type: application/json' -d '{\"key\":\"value\"}' url",
            "ssh user@server -p 22",
            "scp file.txt user@server:/path/",
            "tar -czvf archive.tar.gz /path/to/dir",
            "wget https://example.com/file.zip",
            "apt update; apt install -y package",
            
            # API
            "GET /api/users - list all users",
            "POST /api/users - create new user",
            "PUT /api/users/1 - update user 1",
            "DELETE /api/users/1 - delete user 1",
            "GET /api/users?page=1&limit=10 - pagination",
            "POST /api/auth/login - user login",
            "GET /api/auth/profile - get user profile",
            
            # Common patterns
            "for item in list: process(item)",
            "result = [transform(x) for x in data if condition(x)]",
            "data = {k: v for k, v in items if v is not None}",
            "sorted_list = sorted(data, key=lambda x: x['name'])",
            "total = sum(item['price'] for item in cart)",
            "unique = list(set(duplicate_list))",
        ]
        
        for code in code_examples:
            if self._safe_add(
                chat_id=-104,
                chat_title='Code Snippets',
                sender_name='developer',
                message=code,
                timestamp=time.time()
            ):
                count += 1
                self.stats['new'] += 1
            self.stats['scraped'] += 1
        
        print(f"  [WEB] ✅ Added {count} code snippets")
        return count

    def scrape_all(self):
        """Scrape all sources."""
        print("\n" + "=" * 50)
        print("  DikaAi Web Scraper 🌐")
        print("=" * 50)
        
        start = time.time()
        
        # Scrape all sources
        self.scrape_common_phrases()
        time.sleep(0.5)
        
        self.scrape_stackoverflow()
        time.sleep(0.5)
        
        self.scrape_github_readmes()
        time.sleep(0.5)
        
        self.scrape_indo_docs()
        time.sleep(0.5)
        
        self.scrape_code_snippets()
        
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
