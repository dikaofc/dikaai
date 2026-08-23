"""
DikaAI Coding Dataset - Training data for code generation.

Contains:
    - Python Q&A pairs (instruction → code)
    - JavaScript Q&A pairs
    - Rust Q&A pairs
    - C++ Q&A pairs
    - Go Q&A pairs
    - Debugging pairs (error → fix)
    - Code completion pairs
    - Algorithm solutions
"""

import random
from pathlib import Path


# ============================================================
# PYTHON CODING Q&A PAIRS
# ============================================================

PYTHON_QA = [
    # Basic
    {"instruction": "Write a Python function to check if a number is prime",
     "code": "def is_prime(n):\n    if n < 2: return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0: return False\n    return True",
     "language": "python", "difficulty": "easy"},
    {"instruction": "Write a Python function to reverse a string",
     "code": "def reverse_string(s): return s[::-1]",
     "language": "python", "difficulty": "easy"},
    {"instruction": "Write a Python function to count vowels",
     "code": "def count_vowels(s): return sum(1 for c in s.lower() if c in 'aeiou')",
     "language": "python", "difficulty": "easy"},
    {"instruction": "Write a Python function to check palindrome",
     "code": "def is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]",
     "language": "python", "difficulty": "easy"},
    {"instruction": "Write a Python function to find largest element",
     "code": "def find_largest(lst):\n    if not lst: return None\n    largest = lst[0]\n    for item in lst[1:]:\n        if item > largest: largest = item\n    return largest",
     "language": "python", "difficulty": "easy"},
    {"instruction": "Write a Python function to calculate factorial",
     "code": "def factorial(n):\n    if n <= 1: return 1\n    return n * factorial(n - 1)",
     "language": "python", "difficulty": "easy"},
    {"instruction": "Write a Python function for fibonacci",
     "code": "def fibonacci(n):\n    if n <= 1: return n\n    a, b = 0, 1\n    for _ in range(2, n + 1): a, b = b, a + b\n    return b",
     "language": "python", "difficulty": "easy"},
    {"instruction": "Write a Python function to flatten nested list",
     "code": "def flatten(lst):\n    result = []\n    for item in lst:\n        if isinstance(item, list): result.extend(flatten(item))\n        else: result.append(item)\n    return result",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write a Python function to remove duplicates",
     "code": "def remove_duplicates(lst):\n    seen = set()\n    result = []\n    for item in lst:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result",
     "language": "python", "difficulty": "easy"},
    {"instruction": "Write a Python function to merge two sorted lists",
     "code": "def merge_sorted(a, b):\n    result = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]: result.append(a[i]); i += 1\n        else: result.append(b[j]); j += 1\n    result.extend(a[i:]); result.extend(b[j:])\n    return result",
     "language": "python", "difficulty": "medium"},
    # Data structures
    {"instruction": "Write a Python class for Stack",
     "code": "class Stack:\n    def __init__(self): self.items = []\n    def push(self, item): self.items.append(item)\n    def pop(self): return self.items.pop() if self.items else None\n    def peek(self): return self.items[-1] if self.items else None\n    def is_empty(self): return len(self.items) == 0\n    def size(self): return len(self.items)",
     "language": "python", "difficulty": "easy"},
    {"instruction": "Write a Python class for Queue",
     "code": "class Queue:\n    def __init__(self): self.items = []\n    def enqueue(self, item): self.items.insert(0, item)\n    def dequeue(self): return self.items.pop() if self.items else None\n    def is_empty(self): return len(self.items) == 0\n    def size(self): return len(self.items)",
     "language": "python", "difficulty": "easy"},
    {"instruction": "Write a Python class for LinkedList",
     "code": "class Node:\n    def __init__(self, data): self.data = data; self.next = None\nclass LinkedList:\n    def __init__(self): self.head = None\n    def append(self, data):\n        if not self.head: self.head = Node(data); return\n        cur = self.head\n        while cur.next: cur = cur.next\n        cur.next = Node(data)\n    def display(self):\n        elems, cur = [], self.head\n        while cur: elems.append(cur.data); cur = cur.next\n        return elems",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write a Python class for Binary Tree",
     "code": "class TreeNode:\n    def __init__(self, val=0): self.val = val; self.left = None; self.right = None\ndef insert(root, val):\n    if not root: return TreeNode(val)\n    if val < root.val: root.left = insert(root.left, val)\n    else: root.right = insert(root.right, val)\n    return root\ndef inorder(root):\n    if not root: return []\n    return inorder(root.left) + [root.val] + inorder(root.right)",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write a Python class for HashMap",
     "code": "class HashMap:\n    def __init__(self, size=16):\n        self.size = size\n        self.buckets = [[] for _ in range(size)]\n    def _hash(self, key): return hash(key) % self.size\n    def put(self, key, value):\n        idx = self._hash(key)\n        for i, (k, v) in enumerate(self.buckets[idx]):\n            if k == key: self.buckets[idx][i] = (key, value); return\n        self.buckets[idx].append((key, value))\n    def get(self, key):\n        for k, v in self.buckets[self._hash(key)]:\n            if k == key: return v\n        raise KeyError(key)",
     "language": "python", "difficulty": "medium"},
    # Algorithms
    {"instruction": "Write Python binary search",
     "code": "def binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target: return mid\n        elif arr[mid] < target: lo = mid + 1\n        else: hi = mid - 1\n    return -1",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write Python bubble sort",
     "code": "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]: arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr",
     "language": "python", "difficulty": "easy"},
    {"instruction": "Write Python quicksort",
     "code": "def quicksort(arr):\n    if len(arr) <= 1: return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    mid = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + mid + quicksort(right)",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write Python merge sort",
     "code": "def merge_sort(arr):\n    if len(arr) <= 1: return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)\ndef merge(l, r):\n    result, i, j = [], 0, 0\n    while i < len(l) and j < len(r):\n        if l[i] <= r[j]: result.append(l[i]); i += 1\n        else: result.append(r[j]); j += 1\n    result.extend(l[i:]); result.extend(r[j:])\n    return result",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write Python two sum",
     "code": "def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen: return [seen[complement], i]\n        seen[num] = i\n    return []",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write Python LCS (longest common subsequence)",
     "code": "def lcs(s1, s2):\n    m, n = len(s1), len(s2)\n    dp = [[0] * (n + 1) for _ in range(m + 1)]\n    for i in range(1, m + 1):\n        for j in range(1, n + 1):\n            if s1[i-1] == s2[j-1]: dp[i][j] = dp[i-1][j-1] + 1\n            else: dp[i][j] = max(dp[i-1][j], dp[i][j-1])\n    return dp[m][n]",
     "language": "python", "difficulty": "hard"},
    {"instruction": "Write Python knapsack problem",
     "code": "def knapsack(weights, values, capacity):\n    n = len(weights)\n    dp = [[0] * (capacity + 1) for _ in range(n + 1)]\n    for i in range(1, n + 1):\n        for w in range(capacity + 1):\n            dp[i][w] = dp[i-1][w]\n            if weights[i-1] <= w:\n                dp[i][w] = max(dp[i][w], dp[i-1][w-weights[i-1]] + values[i-1])\n    return dp[n][capacity]",
     "language": "python", "difficulty": "hard"},
    {"instruction": "Write Python edit distance",
     "code": "def edit_distance(s1, s2):\n    m, n = len(s1), len(s2)\n    dp = [[0] * (n + 1) for _ in range(m + 1)]\n    for i in range(m + 1): dp[i][0] = i\n    for j in range(n + 1): dp[0][j] = j\n    for i in range(1, m + 1):\n        for j in range(1, n + 1):\n            if s1[i-1] == s2[j-1]: dp[i][j] = dp[i-1][j-1]\n            else: dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])\n    return dp[m][n]",
     "language": "python", "difficulty": "hard"},
    {"instruction": "Write Python Kadane's max subarray",
     "code": "def max_subarray(arr):\n    max_sum = current_sum = arr[0]\n    for num in arr[1:]:\n        current_sum = max(num, current_sum + num)\n        max_sum = max(max_sum, current_sum)\n    return max_sum",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write Python valid parentheses",
     "code": "def valid_parentheses(s):\n    stack, mapping = [], {')': '(', ']': '[', '}': '{'}\n    for c in s:\n        if c in mapping:\n            if not stack or stack[-1] != mapping[c]: return False\n            stack.pop()\n        else: stack.append(c)\n    return len(stack) == 0",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write Python Dijkstra shortest path",
     "code": "import heapq\ndef dijkstra(graph, start):\n    dist = {n: float('inf') for n in graph}\n    dist[start] = 0\n    pq = [(0, start)]\n    while pq:\n        d, u = heapq.heappop(pq)\n        if d > dist[u]: continue\n        for v, w in graph[u]:\n            if dist[u] + w < dist[v]:\n                dist[v] = dist[u] + w\n                heapq.heappush(pq, (dist[v], v))\n    return dist",
     "language": "python", "difficulty": "hard"},
    {"instruction": "Write Python BFS traversal",
     "code": "from collections import deque\ndef bfs(graph, start):\n    visited = {start}\n    queue = deque([start])\n    order = []\n    while queue:\n        node = queue.popleft()\n        order.append(node)\n        for neighbor in graph.get(node, []):\n            if neighbor not in visited:\n                visited.add(neighbor)\n                queue.append(neighbor)\n    return order",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write Python DFS traversal",
     "code": "def dfs(graph, start, visited=None):\n    if visited is None: visited = set()\n    visited.add(start)\n    order = [start]\n    for neighbor in graph.get(start, []):\n        if neighbor not in visited:\n            order.extend(dfs(graph, neighbor, visited))\n    return order",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write Python Trie data structure",
     "code": "class TrieNode:\n    def __init__(self): self.children = {}; self.is_end = False\nclass Trie:\n    def __init__(self): self.root = TrieNode()\n    def insert(self, word):\n        node = self.root\n        for c in word:\n            if c not in node.children: node.children[c] = TrieNode()\n            node = node.children[c]\n        node.is_end = True\n    def search(self, word):\n        node = self.root\n        for c in word:\n            if c not in node.children: return False\n            node = node.children[c]\n        return node.is_end",
     "language": "python", "difficulty": "hard"},
    {"instruction": "Write Python timer decorator",
     "code": "import time\ndef timer(func):\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        result = func(*args, **kwargs)\n        print(f'{func.__name__} took {time.time()-start:.4f}s')\n        return result\n    return wrapper",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write Python memoize decorator",
     "code": "def memoize(func):\n    cache = {}\n    def wrapper(*args):\n        if args not in cache: cache[args] = func(*args)\n        return cache[args]\n    return wrapper",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write Python context manager",
     "code": "class FileManager:\n    def __init__(self, path, mode='r'): self.path = path; self.mode = mode\n    def __enter__(self): self.file = open(self.path, self.mode); return self.file\n    def __exit__(self, exc_type, exc_val, exc_tb):\n        if self.file: self.file.close()",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write Python property decorator example",
     "code": "class Circle:\n    def __init__(self, radius): self._radius = radius\n    @property\n    def radius(self): return self._radius\n    @radius.setter\n    def radius(self, value):\n        if value < 0: raise ValueError('Radius cannot be negative')\n        self._radius = value\n    @property\n    def area(self): import math; return math.pi * self._radius ** 2",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write Python iterator class",
     "code": "class Counter:\n    def __init__(self, start=0, end=10): self.current = start; self.end = end\n    def __iter__(self): return self\n    def __next__(self):\n        if self.current >= self.end: raise StopIteration\n        self.current += 1\n        return self.current - 1",
     "language": "python", "difficulty": "medium"},
    {"instruction": "Write Python HTTP GET request",
     "code": "import urllib.request, json\ndef http_get(url, headers=None):\n    req = urllib.request.Request(url, headers=headers or {})\n    with urllib.request.urlopen(req, timeout=10) as resp:\n        return json.loads(resp.read().decode('utf-8'))",
     "language": "python", "difficulty": "easy"},
    {"instruction": "Write Python SQLite create table",
     "code": "import sqlite3\ndef create_table(db_path, table_name, columns):\n    conn = sqlite3.connect(db_path)\n    col_defs = ', '.join(f'{n} {d}' for n, d in columns.items())\n    conn.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({col_defs})')\n    conn.commit(); conn.close()",
     "language": "python", "difficulty": "easy"},
    {"instruction": "Write Python unit test example",
     "code": "import unittest\nclass TestMath(unittest.TestCase):\n    def test_add(self): self.assertEqual(2 + 2, 4)\n    def test_sub(self): self.assertEqual(5 - 3, 2)\n    def test_mul(self): self.assertEqual(3 * 4, 12)\nif __name__ == '__main__': unittest.main()",
     "language": "python", "difficulty": "easy"},
]


# ============================================================
# JAVASCRIPT Q&A PAIRS
# ============================================================

JAVASCRIPT_QA = [
    {"instruction": "Write JavaScript function for fibonacci",
     "code": "function fibonacci(n) {\n    if (n <= 1) return n;\n    let a = 0, b = 1;\n    for (let i = 2; i <= n; i++) [a, b] = [b, a + b];\n    return b;\n}",
     "language": "javascript", "difficulty": "easy"},
    {"instruction": "Write JavaScript function for reverse string",
     "code": "function reverseString(s) { return s.split('').reverse().join(''); }",
     "language": "javascript", "difficulty": "easy"},
    {"instruction": "Write JavaScript function for palindrome check",
     "code": "function isPalindrome(s) {\n    const cleaned = s.toLowerCase().replace(/\\s/g, '');\n    return cleaned === cleaned.split('').reverse().join('');\n}",
     "language": "javascript", "difficulty": "easy"},
    {"instruction": "Write JavaScript binary search",
     "code": "function binarySearch(arr, target) {\n    let lo = 0, hi = arr.length - 1;\n    while (lo <= hi) {\n        const mid = Math.floor((lo + hi) / 2);\n        if (arr[mid] === target) return mid;\n        else if (arr[mid] < target) lo = mid + 1;\n        else hi = mid - 1;\n    }\n    return -1;\n}",
     "language": "javascript", "difficulty": "medium"},
    {"instruction": "Write JavaScript quicksort",
     "code": "function quicksort(arr) {\n    if (arr.length <= 1) return arr;\n    const pivot = arr[Math.floor(arr.length / 2)];\n    return [...quicksort(arr.filter(x => x < pivot)),\n            ...arr.filter(x => x === pivot),\n            ...quicksort(arr.filter(x => x > pivot))];\n}",
     "language": "javascript", "difficulty": "medium"},
    {"instruction": "Write JavaScript two sum",
     "code": "function twoSum(nums, target) {\n    const seen = {};\n    for (let i = 0; i < nums.length; i++) {\n        const complement = target - nums[i];\n        if (complement in seen) return [seen[complement], i];\n        seen[nums[i]] = i;\n    }\n    return [];\n}",
     "language": "javascript", "difficulty": "medium"},
    {"instruction": "Write JavaScript async fetch",
     "code": "async function fetchData(url) {\n    const response = await fetch(url);\n    if (!response.ok) throw new Error(`HTTP ${response.status}`);\n    return await response.json();\n}",
     "language": "javascript", "difficulty": "easy"},
    {"instruction": "Write JavaScript debounce function",
     "code": "function debounce(fn, delay = 300) {\n    let timer;\n    return function (...args) {\n        clearTimeout(timer);\n        timer = setTimeout(() => fn.apply(this, args), delay);\n    };\n}",
     "language": "javascript", "difficulty": "medium"},
    {"instruction": "Write JavaScript memoize function",
     "code": "function memoize(fn) {\n    const cache = new Map();\n    return function (...args) {\n        const key = JSON.stringify(args);\n        if (cache.has(key)) return cache.get(key);\n        const result = fn.apply(this, args);\n        cache.set(key, result);\n        return result;\n    };\n}",
     "language": "javascript", "difficulty": "medium"},
    {"instruction": "Write JavaScript event emitter class",
     "code": "class EventEmitter {\n    constructor() { this.events = {}; }\n    on(event, callback) {\n        (this.events[event] = this.events[event] || []).push(callback);\n        return this;\n    }\n    emit(event, ...args) {\n        (this.events[event] || []).forEach(fn => fn(...args));\n        return this;\n    }\n}",
     "language": "javascript", "difficulty": "medium"},
    {"instruction": "Write JavaScript valid parentheses",
     "code": "function validParentheses(s) {\n    const stack = [], map = {')': '(', ']': '[', '}': '{'};\n    for (const c of s) {\n        if (c in map) {\n            if (!stack.length || stack[stack.length - 1] !== map[c]) return false;\n            stack.pop();\n        } else stack.push(c);\n    }\n    return stack.length === 0;\n}",
     "language": "javascript", "difficulty": "medium"},
    {"instruction": "Write JavaScript flatten array",
     "code": "function flatten(arr) {\n    return arr.reduce((acc, val) =>\n        Array.isArray(val) ? acc.concat(flatten(val)) : acc.concat(val), []);\n}",
     "language": "javascript", "difficulty": "medium"},
    {"instruction": "Write JavaScript deep clone",
     "code": "function deepClone(obj) {\n    if (obj === null || typeof obj !== 'object') return obj;\n    if (obj instanceof Date) return new Date(obj);\n    if (Array.isArray(obj)) return obj.map(deepClone);\n    const cloned = {};\n    for (const key in obj) if (obj.hasOwnProperty(key)) cloned[key] = deepClone(obj[key]);\n    return cloned;\n}",
     "language": "javascript", "difficulty": "medium"},
]


# ============================================================
# RUST Q&A PAIRS
# ============================================================

RUST_QA = [
    {"instruction": "Write Rust function for fibonacci",
     "code": "fn fibonacci(n: u32) -> u64 {\n    if n <= 1 { return n as u64; }\n    let (mut a, mut b) = (0u64, 1u64);\n    for _ in 2..=n { let t = b; b = a + b; a = t; }\n    b\n}",
     "language": "rust", "difficulty": "easy"},
    {"instruction": "Write Rust struct with methods",
     "code": "struct Point { x: f64, y: f64 }\nimpl Point {\n    fn new(x: f64, y: f64) -> Self { Point { x, y } }\n    fn distance(&self, other: &Point) -> f64 {\n        ((self.x - other.x).powi(2) + (self.y - other.y).powi(2)).sqrt()\n    }\n}",
     "language": "rust", "difficulty": "easy"},
    {"instruction": "Write Rust trait example",
     "code": "trait Drawable { fn draw(&self) -> String; fn area(&self) -> f64; }\nstruct Circle { radius: f64 }\nimpl Drawable for Circle {\n    fn draw(&self) -> String { format!(\"Circle r={}\", self.radius) }\n    fn area(&self) -> f64 { std::f64::consts::PI * self.radius * self.radius }\n}",
     "language": "rust", "difficulty": "medium"},
    {"instruction": "Write Rust binary search",
     "code": "fn binary_search(arr: &[i32], target: i32) -> Option<usize> {\n    let (mut lo, mut hi) = (0, arr.len());\n    while lo < hi {\n        let mid = lo + (hi - lo) / 2;\n        match arr[mid].cmp(&target) {\n            std::cmp::Ordering::Equal => return Some(mid),\n            std::cmp::Ordering::Less => lo = mid + 1,\n            std::cmp::Ordering::Greater => hi = mid,\n        }\n    }\n    None\n}",
     "language": "rust", "difficulty": "medium"},
    {"instruction": "Write Rust Option and Result handling",
     "code": "fn divide(a: f64, b: f64) -> Result<f64, String> {\n    if b == 0.0 { Err(\"Cannot divide by zero\".to_string()) }\n    else { Ok(a / b) }\n}\nfn find_first_even(nums: &[i32]) -> Option<&i32> {\n    nums.iter().find(|&&n| n % 2 == 0)\n}",
     "language": "rust", "difficulty": "medium"},
    {"instruction": "Write Rust HashMap usage",
     "code": "use std::collections::HashMap;\nfn word_count(text: &str) -> HashMap<String, usize> {\n    let mut counts = HashMap::new();\n    for word in text.split_whitespace() {\n        *counts.entry(word.to_lowercase()).or_insert(0) += 1;\n    }\n    counts\n}",
     "language": "rust", "difficulty": "medium"},
    {"instruction": "Write Rust enum with match",
     "code": "enum TrafficLight { Red, Yellow, Green }\nimpl TrafficLight {\n    fn wait_time(&self) -> u32 {\n        match self {\n            TrafficLight::Red => 60,\n            TrafficLight::Yellow => 5,\n            TrafficLight::Green => 45,\n        }\n    }\n}",
     "language": "rust", "difficulty": "medium"},
    {"instruction": "Write Rust iterator chain",
     "code": "fn main() {\n    let nums = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];\n    let evens_sum: i32 = nums.iter().filter(|&&x| x % 2 == 0).sum();\n    let squared: Vec<i32> = nums.iter().map(|&x| x * x).collect();\n    println!(\"Evens sum: {}, Squared: {:?}\", evens_sum, squared);\n}",
     "language": "rust", "difficulty": "easy"},
]


# ============================================================
# GO Q&A PAIRS
# ============================================================

GO_QA = [
    {"instruction": "Write Go function for fibonacci",
     "code": "func fibonacci(n int) int {\n    if n <= 1 { return n }\n    a, b := 0, 1\n    for i := 2; i <= n; i++ { a, b = b, a+b }\n    return b\n}",
     "language": "go", "difficulty": "easy"},
    {"instruction": "Write Go struct with methods",
     "code": "type Person struct {\n    Name string\n    Age  int\n}\nfunc (p Person) Greet() string {\n    return fmt.Sprintf(\"Hi, I'm %s, %d years old\", p.Name, p.Age)\n}",
     "language": "go", "difficulty": "easy"},
    {"instruction": "Write Go interface example",
     "code": "type Shape interface {\n    Area() float64\n    Perimeter() float64\n}\ntype Circle struct { Radius float64 }\nfunc (c Circle) Area() float64 { return math.Pi * c.Radius * c.Radius }\nfunc (c Circle) Perimeter() float64 { return 2 * math.Pi * c.Radius }",
     "language": "go", "difficulty": "medium"},
    {"instruction": "Write Go goroutine worker pool",
     "code": "func worker(id int, jobs <-chan int, results chan<- int) {\n    for j := range jobs {\n        results <- j * 2\n    }\n}",
     "language": "go", "difficulty": "medium"},
    {"instruction": "Write Go HTTP server",
     "code": "func main() {\n    http.HandleFunc(\"/api/hello\", func(w http.ResponseWriter, r *http.Request) {\n        json.NewEncoder(w).Encode(map[string]string{\"message\": \"Hello!\"})\n    })\n    http.ListenAndServe(\":8080\", nil)\n}",
     "language": "go", "difficulty": "medium"},
    {"instruction": "Write Go error handling",
     "code": "func parseAge(input string) (int, error) {\n    age, err := strconv.Atoi(input)\n    if err != nil { return 0, fmt.Errorf(\"invalid age: %w\", err) }\n    if age < 0 || age > 150 { return 0, fmt.Errorf(\"out of range: %d\", age) }\n    return age, nil\n}",
     "language": "go", "difficulty": "medium"},
    {"instruction": "Write Go JSON marshal/unmarshal",
     "code": "type Config struct {\n    Host  string   `json:\"host\"`\n    Port  int      `json:\"port\"`\n    Debug bool     `json:\"debug,omitempty\"`\n}\nfunc loadConfig(data []byte) (*Config, error) {\n    var cfg Config\n    if err := json.Unmarshal(data, &cfg); err != nil { return nil, err }\n    return &cfg, nil\n}",
     "language": "go", "difficulty": "medium"},
]


# ============================================================
# C++ Q&A PAIRS
# ============================================================

CPP_QA = [
    {"instruction": "Write C++ fibonacci function",
     "code": "long long fibonacci(int n) {\n    if (n <= 1) return n;\n    long long a = 0, b = 1;\n    for (int i = 2; i <= n; i++) { long long t = b; b = a + b; a = t; }\n    return b;\n}",
     "language": "cpp", "difficulty": "easy"},
    {"instruction": "Write C++ class with constructor",
     "code": "class Point {\nprivate:\n    double x, y;\npublic:\n    Point(double x = 0, double y = 0) : x(x), y(y) {}\n    double getX() const { return x; }\n    double getY() const { return y; }\n    double distanceTo(const Point& other) const {\n        double dx = x - other.x, dy = y - other.y;\n        return std::sqrt(dx * dx + dy * dy);\n    }\n};",
     "language": "cpp", "difficulty": "easy"},
    {"instruction": "Write C++ template function",
     "code": "template <typename T>\nT findMax(const std::vector<T>& vec) {\n    if (vec.empty()) throw std::runtime_error(\"Empty\");\n    T maxVal = vec[0];\n    for (size_t i = 1; i < vec.size(); i++)\n        if (vec[i] > maxVal) maxVal = vec[i];\n    return maxVal;\n}",
     "language": "cpp", "difficulty": "medium"},
    {"instruction": "Write C++ lambda with algorithm",
     "code": "void processVector(std::vector<int>& nums) {\n    std::sort(nums.begin(), nums.end(), [](int a, int b) { return a > b; });\n    auto it = std::remove_if(nums.begin(), nums.end(), [](int n) { return n < 0; });\n    nums.erase(it, nums.end());\n}",
     "language": "cpp", "difficulty": "medium"},
    {"instruction": "Write C++ smart pointer example",
     "code": "class Resource { public: void doWork() {} };\nvoid useResource() {\n    auto ptr = std::make_unique<Resource>();\n    ptr->doWork();\n    auto shared = std::make_shared<Resource>();\n    shared->doWork();\n}",
     "language": "cpp", "difficulty": "medium"},
]


# ============================================================
# DEBUGGING PAIRS
# ============================================================

DEBUGGING_PAIRS = [
    {"error": "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
     "bad_code": "result = 5 + 'hello'",
     "fix": "result = str(5) + 'hello'",
     "explanation": "Convert int to str before concatenation."},
    {"error": "IndexError: list index out of range",
     "bad_code": "lst = [1, 2, 3]\nprint(lst[5])",
     "fix": "if len(lst) > 5:\n    print(lst[5])\nelse:\n    print('Index out of range')",
     "explanation": "Check list length before accessing."},
    {"error": "ModuleNotFoundError: No module named 'requests'",
     "bad_code": "import requests",
     "fix": "import subprocess\nsubprocess.run(['pip', 'install', 'requests'])\nimport requests",
     "explanation": "Install missing module first."},
    {"error": "SyntaxError: invalid syntax",
     "bad_code": "def greet(name)\n    print(f'Hello {name}')",
     "fix": "def greet(name):\n    print(f'Hello {name}')",
     "explanation": "Missing colon after function definition."},
    {"error": "IndentationError: expected an indented block",
     "bad_code": "if True:\nprint('hello')",
     "fix": "if True:\n    print('hello')",
     "explanation": "Code inside if block must be indented."},
    {"error": "KeyError: 'name'",
     "bad_code": "data = {'age': 25}\nprint(data['name'])",
     "fix": "data = {'age': 25}\nprint(data.get('name', 'Unknown'))",
     "explanation": "Use .get() with default value."},
    {"error": "AttributeError: 'NoneType' object has no attribute 'split'",
     "bad_code": "result = None\nwords = result.split(' ')",
     "fix": "result = None\nif result:\n    words = result.split(' ')",
     "explanation": "Check for None before calling methods."},
    {"error": "ZeroDivisionError: division by zero",
     "bad_code": "def divide(a, b):\n    return a / b",
     "fix": "def divide(a, b):\n    if b == 0:\n        raise ValueError('Cannot divide by zero')\n    return a / b",
     "explanation": "Check for zero divisor."},
    {"error": "RecursionError: maximum recursion depth exceeded",
     "bad_code": "def factorial(n):\n    return n * factorial(n - 1)",
     "fix": "def factorial(n, memo={}):\n    if n in memo: return memo[n]\n    if n <= 1: return 1\n    memo[n] = n * factorial(n - 1, memo)\n    return memo[n]",
     "explanation": "Add base case and memoization."},
    {"error": "FileNotFoundError: No such file or directory",
     "bad_code": "with open('data.txt') as f:\n    content = f.read()",
     "fix": "import os\nif os.path.exists('data.txt'):\n    with open('data.txt') as f:\n        content = f.read()\nelse:\n    content = ''",
     "explanation": "Check if file exists before opening."},
    {"error": "TypeError: 'int' object is not iterable",
     "bad_code": "for i in 5:\n    print(i)",
     "fix": "for i in range(5):\n    print(i)",
     "explanation": "Use range() to create iterable."},
    {"error": "ValueError: too many values to unpack",
     "bad_code": "a, b = [1, 2, 3]",
     "fix": "a, b, c = [1, 2, 3]\n# or\na, b = [1, 2, 3][:2]",
     "explanation": "Match number of variables to values."},
]


class CodingDataset:
    """Manages coding training data."""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir or 'data/datasets')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.python_qa = PYTHON_QA
        self.javascript_qa = JAVASCRIPT_QA
        self.rust_qa = RUST_QA
        self.go_qa = GO_QA
        self.cpp_qa = CPP_QA
        self.debugging_pairs = DEBUGGING_PAIRS

    def get_training_pairs(self, category: str = "all", max_pairs: int = 500) -> list:
        """Get training pairs as (input, target) format."""
        pairs = []

        all_qa = []
        if category in ('python', 'all'): all_qa.extend(self.python_qa)
        if category in ('javascript', 'all'): all_qa.extend(self.javascript_qa)
        if category in ('rust', 'all'): all_qa.extend(self.rust_qa)
        if category in ('go', 'all'): all_qa.extend(self.go_qa)
        if category in ('cpp', 'all'): all_qa.extend(self.cpp_qa)

        for item in all_qa:
            pairs.append({
                'input': item['instruction'],
                'target': item['code'],
                'type': 'code_generation',
                'language': item.get('language', 'python'),
                'difficulty': item.get('difficulty', 'easy'),
            })

        if category in ('debug', 'all'):
            for item in self.debugging_pairs:
                pairs.append({
                    'input': f"Fix this error: {item['error']}\nCode: {item['bad_code']}",
                    'target': item['fix'],
                    'type': 'debugging',
                    'language': 'python',
                    'difficulty': 'medium',
                })

        random.shuffle(pairs)
        return pairs[:max_pairs]

    def get_text_corpus(self) -> list:
        """Get all code as text for tokenizer training."""
        texts = []
        all_qa = self.python_qa + self.javascript_qa + self.rust_qa + self.go_qa + self.cpp_qa
        for item in all_qa:
            texts.append(item['instruction'])
            texts.append(item['code'])
        for item in self.debugging_pairs:
            texts.append(f"Fix: {item['error']}")
            texts.append(item['fix'])
            texts.append(item['explanation'])
        return texts

    def get_stats(self) -> dict:
        return {
            'python': len(self.python_qa),
            'javascript': len(self.javascript_qa),
            'rust': len(self.rust_qa),
            'go': len(self.go_qa),
            'cpp': len(self.cpp_qa),
            'debugging': len(self.debugging_pairs),
            'total': (len(self.python_qa) + len(self.javascript_qa) +
                     len(self.rust_qa) + len(self.go_qa) +
                     len(self.cpp_qa) + len(self.debugging_pairs)),
        }
