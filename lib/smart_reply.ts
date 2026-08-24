/**
 * Smart Reply system — TypeScript port of dikaai/coding/smart_reply.py
 * Real, context-aware pattern matching with intent detection.
 */

function isGarbage(text: string): boolean {
  if (!text || text.trim().length < 2) return true;
  const t = text.trim().toLowerCase();
  if (t.length < 5) return true;
  if (/^[\s\W]+$/.test(t)) return true;
  const chars = t.replace(/\s/g, '');
  if (new Set(chars).size <= 3) return true;
  const words = t.split(/\s+/);
  if (words.length > 1 && new Set(words).size / words.length < 0.5) return true;
  if (!/[aeiou]/.test(chars)) return true;
  return false;
}

function echoCheck(reply: string, userMsg: string): boolean {
  if (!reply || !userMsg) return false;
  const r = reply.trim().toLowerCase();
  const u = userMsg.trim().toLowerCase();
  if (r === u) return true;
  if (u.length > 5 && r.includes(u) && r.length < u.length * 1.5) return true;
  return false;
}

// ============================================================
// INTENT-BASED REPLIES
// ============================================================
const INTENT_REPLIES: Record<string, string[]> = {
  'bisa coding': [
    "Bisa dong! Aku bisa bantu:\n🔧 **Python** - fibonacci, sorting, algorithms\n🌐 **JavaScript** - debounce, fetch, DOM\n🦀 **Rust** - structs, traits, ownership\n🔷 **C++** - vectors, lambdas, STL\n🐹 **Go** - goroutines, channels\n\nCoba bilang 'buatin function fibonacci' atau 'write a debounce function'!",
  ],
  'kamu bisa apa': [
    "Aku DikaAI, AI coding assistant! 🧠\n\nYang bisa aku lakuin:\n📝 **Buat kode** - Python, JS, Rust, C++, Go\n🐛 **Fix error** - kasih error message, aku fix\n📂 **Git** - status, commit, branch\n🔍 **Cari kode** - search dalam project\n🧠 **Jelaskan** - algoritma, konsep programming\n\nTanya aja, gas! 🚀",
  ],
  'siapa kamu': [
    "Aku DikaAI! 🧠 AI Coding Agent yang dibuat buat bantu coding.\n\nAku bisa:\n✅ Buat kode (Python, JS, Rust, C++, Go)\n✅ Fix error & debugging\n✅ Jelaskan konsep programming\n✅ Operasi Git\n✅ Search dalam codebase\n\nMau coba? Bilang aja mau bikin apa!",
  ],
  'apa itu dikaai': [
    "DikaAI adalah AI Coding Agent & Chat System 🧠\n\nArsitekturnya:\n```\nUser → Context → Memory → RAG → Agent → Model → Response\n```\n\nFitur:\n📝 Multi-language code generation\n🧠 Memory & context management\n🔧 Tool system (files, terminal, git)\n📊 Benchmark & evaluation\n🔄 Continuous learning from training data",
  ],
  'buatin code': [
    "Oke! Aku bisa buatin code. Spesifik nya mau bahasa apa?\n\n🔢 `fibonacci function` - Python/JS/Rust\n🔍 `binary search` - semua bahasa\n📊 `merge sort` / `quicksort`\n🏗️ `stack` / `queue` / `linked list`\n🌐 `HTTP GET request`\n📁 `read file` / `write file`\n\nTinggal bilang aja mau bikin apa!",
  ],
  'buat function': [
    "Siap! Mau function apa? Contoh:\n\n🔢 `fibonacci(n)` - angka Fibonacci\n📊 `factorial(n)` - faktorial\n🔍 `binary_search(arr, target)` - cari di sorted array\n✅ `is_palindrome(s)` - cek palindrome\n📝 `reverse_string(s)` - balik string\n🧮 `two_sum(nums, target)` - cari pasangan\n\nTinggal pilih atau sebutkan sendiri!",
  ],
  'write.*function': [
    "Sure! What function do you need?\n\n🔢 **fibonacci(n)** - Fibonacci sequence\n🔍 **binary_search(arr, target)** - Search sorted array\n📊 **merge_sort(arr)** / **quicksort(arr)** - Sorting\n✅ **is_palindrome(s)** - Check palindrome\n📝 **reverse_string(s)** - Reverse string\n🧮 **two_sum(nums, target)** - Find pair\n\nJust say what you need!",
  ],
  'debounce': [
    "Here's a clean debounce function:\n\n```javascript\nfunction debounce(fn, delay = 300) {\n    let timer;\n    return function (...args) {\n        clearTimeout(timer);\n        timer = setTimeout(() => fn.apply(this, args), delay);\n    };\n}\n\n// Usage\nconst search = debounce(fetchResults, 500);\ninput.addEventListener('input', search);\n```\n\nGunanya: delay execution sampai user berhenti input.",
  ],
  'git status': [
    "Ini command git yang sering dipake:\n\n```bash\ngit status              # Lihat status file\ngit add .              # Stage semua file\ngit commit -m 'msg'    # Commit\ngit push               # Push ke remote\ngit pull               # Pull dari remote\ngit log --oneline      # Lihat history\ngit branch             # Lihat branches\ngit diff               # Lihat perubahan\n```\n\nMau aku jalanin yang mana?",
  ],
  'git': [
    "Git commands yang tersedia:\n\n📊 `git status` - Status working tree\n📝 `git log` - Commit history\n🔀 `git branch` - List branches\n📋 `git diff` - Show changes\n\nMau run yang mana?",
  ],
  'apa itu': [
    "Mau jelasin tentang apa? Contoh:\n\n🧠 **algoritma** - step-by-step solving\n📊 **data structure** - array, linked list, tree\n🔍 **binary search** - cari di sorted data\n🔄 **recursion** - function panggil diri sendiri\n🌐 **API** - Application Programming Interface\n🔐 **authentication** - verifikasi user\n\nTanya spesifik biar aku bisa jelasin lebih detail!",
  ],
  'jelaskan': [
    "Mau dijelasin tentang apa? Contoh:\n\n🧠 **quicksort** - divide & conquer sorting\n📊 **linked list** - data structure linear\n🔄 **recursion** - function calling itself\n🌐 **REST API** - web service architecture\n🔐 **JWT** - JSON Web Token auth\n\nSpesifik ya biar jelas!",
  ],
  'apa itu python': [
    "Python 🐍 - bahasa pemrograman serbaguna. Simple syntax, banyak library. Cocok buat web (Django/Flask), data science (pandas/numpy), AI (tensorflow/pytorch), automation.\n\nContoh kode Python:\n```python\n# Hello World\nprint('Hello, DikaAI!')\n\n# Function\ndef fibonacci(n):\n    if n <= 1: return n\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b\n```\n\nMau belajar Python dari mana?",
  ],
  'halo': ["Halo juga! 😊 Ada apa nih?", "Hai! Apa kabar? 🙌", "Hey! Ada yang perlu dibantu?", "Yo! Mau ngobrol apa? 🚀", "Halo~ Siap bantu! 💪"],
  'hai': ["Hai! 👋 Ada yang bisa dibantu?", "Hey! Mau ngobrol apa?", "Hai hai! Gas aja tanya! 🚀"],
  'hi': ["Hi there! 👋 Ada apa?", "Hey! Ready to help! 🚀", "Hi! Mau coding atau ngobrol?"],
  'test': ["Oke, test berhasil! ✅\nAku DikaAI, siap bantu coding kamu! 🧠\n\nCoba tanya:\n- 'buatin fibonacci function'\n- 'apa itu binary search'\n- 'git status'\n- 'apa itu python'"],
  'makasih': ["Sama-sama! 😊 Seneng bisa bantu!", "No problem! 👍 Kapan aja boleh tanya lagi!", "Santai aja! Happy coding! 🚀"],
  'terima kasih': ["Sama-sama! 😊", "Santai! Glad to help! 🙌", "Anytime! 💪"],
  'kamu lagi apa': ["Lagi standby nih, nunggu kamu tanya! 😄\nMau coding atau ngobrol aja?"],
  'anjing': ["Woah, sabar bro! 😅 Ada yang bikin kesel? Cerita aja, aku dengerin."],
  'bodoh': ["Hmm, aku masih belajar nih. Tapi aku bisa bantu kok! 🧠\nCoba tanya sesuatu yang spesifik."],
  'pagi': ["Selamat pagi! ☀️ Semangat hari ini! Mau mulai coding?"],
  'siang': ["Siang! 🌤️ Udah makan belum? Siap coding?"],
  'sore': ["Sore! 🌅 Gimana harinya? Mau ngobrol apa?"],
  'malam': ["Malam! 🌙 Masih begadang? Siap bantu coding!"],
  'help': ["Apa yang bisa aku bantu? 🤔\n\n📝 **Coding** - 'buatin fibonacci function'\n🐛 **Debug** - 'fix error di main.py'\n📂 **Git** - 'git status'\n🔍 **Search** - 'cari function login'\n🧠 **Explain** - 'apa itu binary search'\n💬 **Chat** - tanya apa aja!"],
  'bantuin': ["Tentu! Cerita aja masalahnya apa. 🤝\n\nMau coding, debug, atau tanya sesuatu?"],
};

const KNOWLEDGE_REPLIES: Record<string, string> = {
  'python': "Python 🐍 - bahasa pemrograman serbaguna. Simple syntax, banyak library. Cocok buat web (Django/Flask), data science (pandas/numpy), AI (tensorflow/pytorch), automation.",
  'javascript': "JavaScript 🌐 - bahasa web. Browser + Node.js. Framework: React, Vue, Angular. Package: npm/yarn.",
  'rust': "Rust 🦀 - sistem bahasa, memory safe tanpa garbage collector. Cepat & aman. Cocok buat system programming, WebAssembly.",
  'golang': "Go 🐹 - bahasa Google. Simpel, cepat, concurrent. Cocok buat microservices, CLI tools, server-side.",
  'c++': "C++ 🔷 - sistem bahasa, high performance. STL library powerful. Cocok buat game, OS, embedded systems.",
  'react': "React ⚛️ - library UI dari Facebook. Component-based, virtual DOM. Next.js untuk fullstack.",
  'node': "Node.js 📦 - JavaScript runtime. Package manager: npm/yarn. Framework: Express, Fastify.",
  'docker': "Docker 🐳 - container platform. Isolasi environment. Dockerfile → Image → Container.",
  'kubernetes': "Kubernetes ☸️ - container orchestration. Manage banyak containers. Auto-scaling, load balancing.",
  'linux': "Linux 🐧 - open source OS. Command line powerful. Distro: Ubuntu, Debian, CentOS, Arch.",
  'git': "Git 📂 - version control. Track perubahan kode. Branch, merge, commit, push/pull.",
  'api': "API 🌐 - Application Programming Interface. REST (HTTP methods), GraphQL (query), WebSocket (realtime).",
  'database': "Database 🗄️ - SQL (MySQL, PostgreSQL) untuk structured data. NoSQL (MongoDB, Redis) untuk flexible data.",
  'machine learning': "Machine Learning 🤖 - subset AI. Supervised (labeled data), Unsupervised (clustering), Reinforcement (rewards). Framework: TensorFlow, PyTorch.",
  'html': "HTML 📄 - HyperText Markup Language. Struktur web page. Tag: div, p, a, img, form.",
  'css': "CSS 🎨 - Cascading Style Sheets. Styling web. Flexbox, Grid, Responsive design.",
  'typescript': "TypeScript 📘 - JavaScript + static typing. Better IDE support, fewer runtime errors.",
};

const SHORT_REPLIES = [
  "Oke! 👍 Mau tanya apa?",
  "Siap! Gas aja! 🚀",
  "Noted! Ada lagi?",
  "Gas! 🏎️",
];

const FALLBACK_REPLIES = [
  "Hmm, menarik! 🤔 Bisa dijelasin lebih detail?",
  "Oke aku catet! Mau lanjut ke mana?",
  "Wah, bisa dijelasin lagi? Biar aku bisa bantu lebih spesifik! 😊",
  "Noted! Ada yang spesifik yang mau ditanyain? 🤔",
];

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

export function getSmartReply(userMsg: string, modelReply?: string): string {
  // Try model reply first if it's good
  if (modelReply && !isGarbage(modelReply) && !echoCheck(modelReply, userMsg)) {
    return modelReply;
  }

  const text = userMsg.toLowerCase().trim();

  // Check intent-based replies
  for (const [intent, replies] of Object.entries(INTENT_REPLIES)) {
    if (new RegExp(intent).test(text)) {
      return pick(replies);
    }
  }

  // Check knowledge replies
  for (const [keyword, reply] of Object.entries(KNOWLEDGE_REPLIES)) {
    if (text.includes(keyword)) {
      return reply;
    }
  }

  // Short replies for short messages
  if (text.split(/\s+/).length <= 2) {
    return pick(SHORT_REPLIES);
  }

  // Fallback
  return pick(FALLBACK_REPLIES);
}
