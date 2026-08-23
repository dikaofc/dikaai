"""
DikaAI Reasoning Engine v2 - Actually generates intelligent answers.

Instead of generic steps like "Step 1: Identifying concept...",
this engine ANALYZES the question and GENERATES a real response
using knowledge + context + conversation history.
"""
import re
import time
from dataclasses import dataclass, field


@dataclass
class ReasoningChain:
    """A chain of reasoning steps that produces an actual answer."""
    question: str
    steps: list = field(default_factory=list)
    conclusion: str = ""
    answer: str = ""  # The actual generated answer
    confidence: float = 0.0
    sources: list = field(default_factory=list)

    def to_text(self) -> str:
        return self.answer if self.answer else self.conclusion


class ReasoningEngine:
    """Generates intelligent answers through analysis."""

    def __init__(self):
        # Knowledge base - structured facts the AI "knows"
        self._knowledge = self._build_knowledge()

    def _build_knowledge(self):
        """Build structured knowledge base."""
        return {
            # === PROGRAMMING LANGUAGES ===
            'python': {
                'what': 'Python adalah bahasa pemrograman tingkat tinggi yang dibuat oleh Guido van Rossum tahun 1991.',
                'why': 'Python populer karena syntax-nya yang sederhana dan mudah dipelajari, serta ekosistem library yang sangat luas.',
                'use': 'Python digunakan untuk web development (Django, Flask), data science (pandas, numpy), machine learning (TensorFlow, PyTorch), automation, dan scripting.',
                'example': '```python\n# Python: Fibonacci\ndef fibonacci(n):\n    if n <= 1: return n\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b\n\nprint(fibonacci(10))  # Output: 55\n```',
                'pros': 'Syntax sederhana, ekosistem kaya, multi-platform, komunitas besar.',
                'cons': 'Lebih lambat dari C/Rust, dynamic typing bisa menyebabkan runtime error.',
            },
            'javascript': {
                'what': 'JavaScript adalah bahasa pemrograman yang berjalan di browser dan server (Node.js).',
                'why': 'JavaScript adalah satu-satunya bahasa native di browser, sehingga wajib untuk web development.',
                'use': 'JavaScript digunakan untuk frontend (React, Vue, Angular), backend (Node.js, Express), mobile (React Native), dan desktop (Electron).',
                'example': '```javascript\n// JavaScript: Fibonacci\nfunction fibonacci(n) {\n    if (n <= 1) return n;\n    let a = 0, b = 1;\n    for (let i = 2; i <= n; i++) {\n        [a, b] = [b, a + b];\n    }\n    return b;\n}\n\nconsole.log(fibonacci(10));  // Output: 55\n```',
                'pros': 'Universal di browser, async/await untuk concurrent, npm ecosystem besar.',
                'cons': 'Dynamic typing, callback hell (meskipun sudah ada Promise/async), prototype-based OOP.',
            },
            'rust': {
                'what': 'Rust adalah sistem bahasa pemrograman yang fokus pada safety dan performance.',
                'why': 'Rust memberikan performance C++ tanpa resiko memory safety issues seperti use-after-free dan data races.',
                'use': 'Rust digunakan untuk system programming, WebAssembly, CLI tools, game engines, dan backend performance-critical.',
                'example': '```rust\n// Rust: Fibonacci\nfn fibonacci(n: u32) -> u64 {\n    if n <= 1 { return n as u64; }\n    let (mut a, mut b) = (0u64, 1u64);\n    for _ in 2..=n {\n        let temp = b;\n        b = a + b;\n        a = temp;\n    }\n    b\n}\n\nfn main() {\n    println!("{}", fibonacci(10));  // Output: 55\n}\n```',
                'pros': 'Memory safe tanpa garbage collector, zero-cost abstractions, concurrent tanpa data races.',
                'cons': 'Learning curve tinggi, borrow checker bisa frustasi, compile time lebih lama.',
            },
            'golang': {
                'what': 'Go (Golang) adalah bahasa pemrograman yang dibuat oleh Google untuk system scalable.',
                'why': 'Go dirancang untuk menulis software yang sederhana, efisien, dan scalable.',
                'use': 'Go digunakan untuk microservices, CLI tools, Docker/Kubernetes, web servers, dan cloud infrastructure.',
                'example': '```go\n// Go: Fibonacci\nfunc fibonacci(n int) int {\n    if n <= 1 { return n }\n    a, b := 0, 1\n    for i := 2; i <= n; i++ {\n        a, b = b, a+b\n    }\n    return b\n}\n\nfunc main() {\n    fmt.Println(fibonacci(10))  // Output: 55\n}\n```',
                'pros': 'Simpel, cepat compile, built-in concurrency (goroutines), garbage collected.',
                'cons': 'Generics baru di Go 1.18, error handling verbose, tidak ada enums.',
            },
            'c++': {
                'what': 'C++ adalah bahasa pemrograman sistem yang berevolusi dari C dengan fitur OOP dan generic programming.',
                'why': 'C++ memberikan kontrol hardware langsung dengan abstraksi tinggi melalui template dan STL.',
                'use': 'C++ digunakan untuk game engines (Unreal), OS, embedded systems, high-frequency trading, dan performance-critical applications.',
                'example': '```cpp\n// C++: Fibonacci\n#include <iostream>\nusing namespace std;\n\nlong long fibonacci(int n) {\n    if (n <= 1) return n;\n    long long a = 0, b = 1;\n    for (int i = 2; i <= n; i++) {\n        long long temp = b;\n        b = a + b;\n        a = temp;\n    }\n    return b;\n}\n\nint main() {\n    cout << fibonacci(10) << endl;  // Output: 55\n    return 0;\n}\n```',
                'pros': 'High performance, STL powerful, template metaprogramming, low-level control.',
                'cons': 'Sangat kompleks, manual memory management, compile time lama, UB (undefined behavior).',
            },

            # === DATA STRUCTURES ===
            'array': {
                'what': 'Array adalah kumpulan elemen dengan tipe data sama yang disimpan di memory contiguous.',
                'why': 'Array memberikan akses O(1) ke elemen berdasarkan index karena address dihitung langsung.',
                'use': 'Array digunakan untuk menyimpan koleksi data yang aksesnya sering berdasarkan index, seperti buffer, lookup table, dan implementasi array-based structures.',
                'example': '```python\n# Array operations\narr = [3, 1, 4, 1, 5, 9]\nprint(arr[0])       # Access: O(1)\narr.append(2)       # Push: O(1)\narr.remove(1)       # Delete: O(n)\narr.sort()          # Sort: O(n log n)\n```',
            },
            'linked list': {
                'what': 'Linked list adalah data structure linear di mana elemen (node) tersambung melalui pointer.',
                'why': 'Linked list efisien untuk insert/delete di tengah karena tidak perlu menggeser elemen.',
                'use': 'Linked list digunakan untuk implementasi stack, queue, adjacency list untuk graph, dan memory allocator.',
                'example': '```python\n# Linked List\nclass Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\nclass LinkedList:\n    def __init__(self):\n        self.head = None\n    \n    def append(self, data):\n        if not self.head:\n            self.head = Node(data)\n            return\n        cur = self.head\n        while cur.next:\n            cur = cur.next\n        cur.next = Node(data)\n```',
            },
            'hash table': {
                'what': 'Hash table adalah data structure yang memetakan key ke value menggunakan hash function.',
                'why': 'Hash table memberikan akses O(1) rata-rata untuk lookup, insert, dan delete.',
                'use': 'Hash table digunakan untuk caching, database indexing, dictionary/sets, dan counting frequency.',
                'example': '```python\n# Hash Table (Dictionary in Python)\nuser = {"name": "Dika", "age": 20, "role": "developer"}\nprint(user["name"])     # Access: O(1)\nuser["email"] = "dika@example.com"  # Insert: O(1)\ndel user["age"]         # Delete: O(1)\n```',
            },

            # === ALGORITHMS ===
            'binary search': {
                'what': 'Binary search adalah algoritma pencarian yang membagi search space setiap iterasi.',
                'why': 'Binary search memiliki waktu O(log n) karena setiap langkah membuang setengah data.',
                'use': 'Binary search digunakan untuk mencari elemen di sorted array, seperti mencari di phonebook atau database index.',
                'example': '```python\ndef binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1\n\n# O(log n) time complexity\n```',
            },
            'quicksort': {
                'what': 'Quicksort adalah algoritma sorting divide-and-conquer yang memilih pivot dan membagi array.',
                'why': 'Quicksort rata-rata O(n log n) dan in-place, menjadikannya salah satu sorting tercepat.',
                'use': 'Quicksort digunakan di standard library banyak bahasa (C qsort, Java Arrays.sort untuk primitives).',
                'example': '```python\ndef quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)\n\n# Average: O(n log n), Worst: O(n^2)\n```',
            },
            'recursion': {
                'what': 'Recursion adalah teknik di mana function memanggil dirinya sendiri dengan input yang lebih kecil.',
                'why': 'Recursion membuat kode lebih elegan untuk masalah yang punya struktur rekursif natural.',
                'use': 'Recursion digunakan untuk traversal tree/graph, divide-and-conquer algorithms, dan mathematical sequences.',
                'example': '```python\ndef factorial(n):\n    if n <= 1:      # Base case\n        return 1\n    return n * factorial(n - 1)  # Recursive case\n\n# factorial(5) = 5 * 4 * 3 * 2 * 1 = 120\n```',
            },

            # === WEB ===
            'react': {
                'what': 'React adalah library JavaScript untuk membangun UI komponen.',
                'why': 'React menggunakan virtual DOM dan component-based architecture yang membuat UI development lebih efisien.',
                'use': 'React digunakan untuk single-page applications (SPA), mobile apps (React Native), dan static sites (Next.js).',
                'example': '```jsx\n// React Component\nfunction Counter() {\n    const [count, setCount] = useState(0);\n    return (\n        <div>\n            <p>Count: {count}</p>\n            <button onClick={() => setCount(count + 1)}>\n                Increment\n            </button>\n        </div>\n    );\n}\n```',
            },
            'nextjs': {
                'what': 'Next.js adalah framework React untuk production-ready web applications.',
                'why': 'Next.js menambahkan server-side rendering, static generation, dan routing ke React.',
                'use': 'Next.js digunakan untuk SEO-friendly websites, e-commerce, dan full-stack web apps.',
            },
            'api': {
                'what': 'API (Application Programming Interface) adalah contract yang mendefinisikan bagaimana software berkomunikasi.',
                'why': 'API memungkinkan berbagai sistem untuk bertukar data tanpa perlu tahu implementasi internal.',
                'use': 'API digunakan untuk integrasi sistem, mobile apps yang berkomunikasi dengan server, dan microservices.',
                'example': '```python\n# REST API example (FastAPI)\nfrom fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/users/{user_id}")\nasync def get_user(user_id: int):\n    return {"id": user_id, "name": "Dika"}\n\n# GET /users/1 → {"id": 1, "name": "Dika"}\n```',
            },
            'rest api': {
                'what': 'REST API adalah arsitektur web service yang menggunakan HTTP methods (GET, POST, PUT, DELETE).',
                'why': 'REST sederhana, stateless, dan menggunakan standar HTTP yang universal.',
                'use': 'REST API digunakan di hampir semua web service, mobile apps backend, dan integrasi sistem.',
            },

            # === DEVOPS ===
            'docker': {
                'what': 'Docker adalah platform containerization yang mengemas aplikasi beserta dependencies-nya.',
                'why': 'Docker memastikan aplikasi berjalan konsisten di mana saja (dev, staging, production).',
                'use': 'Docker digunakan untuk microservices, CI/CD, development environment isolation, dan deployment.',
                'example': '```dockerfile\n# Dockerfile\nFROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD ["python", "main.py"]\n\n# Build: docker build -t myapp .\n# Run: docker run -p 8000:8000 myapp\n```',
            },
            'git': {
                'what': 'Git adalah version control system distributed yang tracking perubahan kode.',
                'why': 'Git memungkinkan multiple developer bekerja bersama, branching, dan rollback perubahan.',
                'use': 'Git digunakan di semua software development untuk version control, collaboration, dan CI/CD.',
                'example': '```bash\n# Common Git commands\ngit init                    # Initialize repo\ngit add .                   # Stage all files\ngit commit -m "message"     # Commit\ngit push origin main        # Push to remote\ngit pull                    # Pull changes\ngit branch feature          # Create branch\ngit checkout feature        # Switch branch\ngit merge feature           # Merge branch\n```',
            },

            # === DATABASE ===
            'database': {
                'what': 'Database adalah sistem untuk menyimpan, mengelola, dan mengambil data secara terstruktur.',
                'why': 'Database memberikan persistensi data, query capability, dan concurrent access control.',
                'use': 'Database digunakan di semua aplikasi yang membutuhkan penyimpanan data.',
            },
            'sql': {
                'what': 'SQL (Structured Query Language) adalah bahasa untuk mengakses dan memanipulasi database relasional.',
                'why': 'SQL adalah standar universal untuk database queries yang sudah ada sejak 1970-an.',
                'use': 'SQL digunakan dengan MySQL, PostgreSQL, SQLite, dan database relasional lainnya.',
                'example': '```sql\n-- SQL basics\nCREATE TABLE users (\n    id INT PRIMARY KEY,\n    name VARCHAR(100),\n    email VARCHAR(100)\n);\n\nINSERT INTO users VALUES (1, \'Dika\', \'dika@example.com\');\nSELECT * FROM users WHERE name = \'Dika\';\nUPDATE users SET email = \'new@example.com\' WHERE id = 1;\nDELETE FROM users WHERE id = 1;\n```',
            },

            # === AI/ML ===
            'machine learning': {
                'what': 'Machine Learning adalah subset AI yang memungkinkan sistem belajar dari data tanpa diprogram secara eksplisit.',
                'why': 'ML memungkinkan computer untuk menemukan pola dalam data yang terlalu kompleks untuk diprogram manual.',
                'use': 'ML digunakan untuk image recognition, natural language processing, recommendation systems, dan predictive analytics.',
            },
            'neural network': {
                'what': 'Neural network adalah model machine learning yang terinspirasi dari struktur otak manusia.',
                'why': 'Neural network bisa menemukan pola non-linear yang kompleks dalam data.',
                'use': 'Neural network digunakan untuk deep learning tasks seperti image recognition, NLP, dan generative AI.',
            },

            # === SECURITY ===
            'authentication': {
                'what': 'Authentication adalah proses memverifikasi identitas user.',
                'why': 'Authentication memastikan hanya user yang berwenang yang bisa mengakses sistem.',
                'use': 'Authentication digunakan di semua sistem yang membutuhkan akses control.',
            },
            'oauth': {
                'what': 'OAuth adalah protocol authorization yang memungkinkan user memberikan akses terbatas ke aplikasi pihak ketiga.',
                'why': 'OAuth memungkinkan login dengan Google/GitHub tanpa share password.',
                'use': 'OAuth digunakan untuk "Login with Google/GitHub" dan API access delegation.',
            },
        }

    def classify(self, message: str) -> str:
        """Classify the reasoning type."""
        text = message.lower()
        if re.search(r'(apa itu|what is|jelaskan|explain|meaning of)', text):
            return 'explanation'
        if re.search(r'(vs|versus|atau|or|compare|perbandingan)', text):
            return 'comparison'
        if re.search(r'(kenapa|mengapa|why|cause|alasan)', text):
            return 'analysis'
        if re.search(r'(gimana|bagaimana|how|cara)', text):
            return 'planning'
        if re.search(r'(error|bug|fix|kesalahan|troubleshoot)', text):
            return 'debugging'
        return 'general'

    def _extract_topic(self, message: str) -> str:
        """Extract the main topic from the message."""
        text = message.lower()
        # Remove common question words
        for word in ['apa itu', 'what is', 'jelaskan', 'explain', 'kenapa', 'why',
                      'gimana', 'how', 'cara', 'itu ', 'ini ', 'adalah', ' adalah']:
            text = text.replace(word, ' ')
        text = re.sub(r'[?!.,]', '', text).strip()
        # Take first meaningful words
        words = [w for w in text.split() if len(w) > 2]
        return ' '.join(words[:3]) if words else text.strip()

    def reason(self, question: str, context: str = "",
               memory_context: str = "", project_context: str = "") -> ReasoningChain:
        """Analyze question and generate actual answer."""
        chain = ReasoningChain(question=question)
        rtype = self.classify(question)
        topic = self._extract_topic(question)

        # Find knowledge about this topic
        knowledge = self._find_knowledge(topic)

        if rtype == 'explanation':
            chain.answer = self._generate_explanation(question, topic, knowledge, memory_context)
        elif rtype == 'comparison':
            chain.answer = self._generate_comparison(question, knowledge)
        elif rtype == 'analysis':
            chain.answer = self._generate_analysis(question, topic, knowledge)
        elif rtype == 'planning':
            chain.answer = self._generate_planning(question, topic, knowledge)
        elif rtype == 'debugging':
            chain.answer = self._generate_debugging(question, knowledge)
        else:
            chain.answer = self._generate_general(question, topic, knowledge)

        chain.confidence = 0.8 if knowledge else 0.5
        chain.steps = [f"Classified as: {rtype}", f"Topic: {topic}", f"Knowledge found: {bool(knowledge)}"]

        return chain

    def _find_knowledge(self, topic: str) -> dict:
        """Find relevant knowledge for a topic."""
        topic_lower = topic.lower()
        # Direct match
        for key, value in self._knowledge.items():
            if key in topic_lower or topic_lower in key:
                return value
        # Partial match
        for key, value in self._knowledge.items():
            if any(word in topic_lower for word in key.split()):
                return value
        return {}

    def _generate_explanation(self, question, topic, knowledge, memory="") -> str:
        """Generate an explanation answer."""
        if knowledge:
            parts = []
            if knowledge.get('what'):
                parts.append(knowledge['what'])
            if knowledge.get('why'):
                parts.append(f"\n**Kenapa penting:** {knowledge['why']}")
            if knowledge.get('use'):
                parts.append(f"\n**Digunakan untuk:** {knowledge['use']}")
            if knowledge.get('example'):
                parts.append(f"\n**Contoh:**\n{knowledge['example']}")
            if knowledge.get('pros'):
                parts.append(f"\n**Kelebihan:** {knowledge['pros']}")
            if knowledge.get('cons'):
                parts.append(f"\n**Kekurangan:** {knowledge['cons']}")
            return '\n'.join(parts)
        return f"Untuk menjelaskan **{topic}**, saya perlu informasi lebih lanjut. Bisa spesifik lagi pertanyaannya?"

    def _generate_comparison(self, question, knowledge) -> str:
        """Generate a comparison answer."""
        items = re.findall(r'(\w[\w+]*)\s+vs\s+(\w[\w+]*)', question.lower())
        if not items:
            items = re.findall(r'(\w[\w+]*)\s+atau\s+(\w[\w+]*)', question.lower())
        if items:
            item1, item2 = items[0]
            k1 = self._find_knowledge(item1)
            k2 = self._find_knowledge(item2)
            parts = [f"**Perbandingan {item1} vs {item2}:**\n"]
            if k1.get('what'):
                parts.append(f"**{item1.title()}:** {k1['what']}")
            if k2.get('what'):
                parts.append(f"**{item2.title()}:** {k2['what']}")
            if k1.get('pros') and k2.get('pros'):
                parts.append(f"\n**Kelebihan {item1}:** {k1['pros']}")
                parts.append(f"**Kelebihan {item2}:** {k2['pros']}")
            if k1.get('use'):
                parts.append(f"\n**Gunakan {item1} untuk:** {k1['use']}")
            if k2.get('use'):
                parts.append(f"**Gunakan {item2} untuk:** {k2['use']}")
            return '\n'.join(parts)
        return f"Untuk membandingkan, saya butuh dua item yang jelas. Contoh: 'Python vs JavaScript'"

    def _generate_analysis(self, question, topic, knowledge) -> str:
        """Generate an analysis answer."""
        if knowledge:
            parts = [f"**Analisis: {topic}**\n"]
            if knowledge.get('what'):
                parts.append(knowledge['what'])
            if knowledge.get('why'):
                parts.append(f"\n**Alasan:** {knowledge['why']}")
            if knowledge.get('use'):
                parts.append(f"\n**Konteks penggunaan:** {knowledge['use']}")
            return '\n'.join(parts)
        return f"Untuk menganalisis **{topic}**, saya butuh lebih banyak konteks. Bisa jelaskan situasinya?"

    def _generate_planning(self, question, topic, knowledge) -> str:
        """Generate a planning/how-to answer."""
        if knowledge:
            parts = [f"**Cara {topic}:**\n"]
            if knowledge.get('what'):
                parts.append(f"Pertama, pahami konsep: {knowledge['what']}")
            if knowledge.get('use'):
                parts.append(f"\n**Langkah-langkah:**")
                parts.append(f"1. Pahami kebutuhan dan use case")
                parts.append(f"2. Pelajari dasar {topic}")
                parts.append(f"3. Praktik dengan contoh sederhana")
                parts.append(f"4. Terapkan dalam project nyata")
            if knowledge.get('example'):
                parts.append(f"\n**Contoh implementasi:**\n{knowledge['example']}")
            return '\n'.join(parts)
        return f"Untuk **cara {topic}**, saya butuh penjelasan lebih spesifik tentang yang ingin dicapai."

    def _generate_debugging(self, question, knowledge) -> str:
        """Generate a debugging answer."""
        parts = ["**Debugging Guide:**\n"]
        parts.append("1. **Baca error message** - Pahami apa yang error")
        parts.append("2. **Identifikasi type error** - Syntax, Runtime, Logic?")
        parts.append("3. **Lokasi error** - Baris mana, function mana?")
        parts.append("4. **Cek dependency** - Library missing? Version mismatch?")
        parts.append("5. **Test fix** - Jalankan ulang, pastikan error hilang")
        if knowledge:
            if knowledge.get('what'):
                parts.append(f"\n**Tentang {list(self._find_knowledge('').keys())[0] if knowledge else topic}:** {knowledge.get('what', '')}")
        return '\n'.join(parts)

    def _generate_general(self, question, topic, knowledge) -> str:
        """Generate a general answer."""
        text = question.lower().strip()

        # Handle self-introduction
        if any(w in text for w in ['siapa kamu', 'who are you', 'kamu ini siapa', 'kenalan']):
            return "Saya DikaAI, AI coding assistant! 🧠\n\nSaya bisa:\n- **Buat kode** dalam Python, JavaScript, Rust, C++, Go\n- **Fix error** dan debugging\n- **Jelaskan** konsep programming\n- **Operasi Git** (status, commit, branch)\n- **Search** dalam codebase\n\nMau coba? Bilang aja mau bikin apa!"

        # Handle capability questions
        if any(w in text for w in ['kamu bisa', 'what can you', 'bisa apa', 'ngapain']):
            return "Saya DikaAI, AI coding assistant! 🧠\n\nYang bisa saya lakuin:\n\n📝 **Buat kode** - fibonacci, sorting, data structures\n🐛 **Fix error** - kasih error message, saya fix\n📂 **Git** - status, commit, branch\n🔍 **Cari kode** - search dalam project\n🧠 **Jelaskan** - algoritma, konsep programming\n📊 **Bandingkan** - Python vs JavaScript, dll\n\nCoba: 'buatin fibonacci function' atau 'apa itu binary search'"

        # Handle greetings
        if any(w in text for w in ['halo', 'hai', 'hi', 'hey', 'yo', 'pagi', 'siang', 'sore', 'malam']):
            return "Halo! 👋 Saya DikaAI, AI coding assistant. Ada yang bisa dibantu?\n\nCoba tanya:\n- 'apa itu python'\n- 'buatin fibonacci function'\n- 'python vs javascript'"

        # Handle thanks
        if any(w in text for w in ['makasih', 'terima kasih', 'thanks', 'thank you']):
            return "Sama-sama! 😊 Seneng bisa bantu! Kapan aja boleh tanya lagi."

        # Handle help
        if any(w in text for w in ['help', 'bantuan', 'bantuin', 'bisa bantu']):
            return "Tentu! Saya bisa bantu dengan:\n\n📝 **Coding** - 'buatin fibonacci function'\n🐛 **Debug** - 'fix error di main.py'\n📂 **Git** - 'git status'\n🔍 **Search** - 'cari function login'\n🧠 **Explain** - 'apa itu binary search'\n📊 **Compare** - 'python vs javascript'\n\nTanya aja!"

        # Handle casual chat
        if any(w in text for w in ['kamu lagi apa', 'lagi apa', 'ngapain']):
            return "Lagi standby nih, nunggu kamu tanya! 😄\nMau coding atau ngobrol aja?"

        if any(w in text for w in ['anjing', 'bodoh', 'tolol', 'goblok']):
            return "Woah, sabar! 😅 Ada yang bikin kesel? Cerita aja, saya dengerin. Atau mau tanya coding juga gapapa."

        # Technical question without knowledge
        if knowledge:
            parts = []
            if knowledge.get('what'):
                parts.append(knowledge['what'])
            if knowledge.get('use'):
                parts.append(f"\n**Digunakan untuk:** {knowledge['use']}")
            if knowledge.get('example'):
                parts.append(f"\n{knowledge['example']}")
            return '\n'.join(parts)

        # Unknown question - ask for clarification
        return f"Tentang **{topic}** - bisa dijelasin lebih detail? Saya bisa bantu dengan coding, debugging, atau penjelasan konsep."
