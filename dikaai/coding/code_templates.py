"""
DikaAI Code Templates - Pre-built code patterns for instant code generation.

Supports: Python, JavaScript, TypeScript, Rust, C++, Go
Each template has regex patterns to match user intent across languages.
"""

import re


# ============================================================
# PYTHON CODE TEMPLATES
# ============================================================

PYTHON_TEMPLATES = {
    "fibonacci": {
        "pattern": r"fibonacci|fib\s*\(",
        "code": """def fibonacci(n):
    \"\"\"Calculate the nth Fibonacci number.\"\"\"
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b""",
    },
    "factorial": {
        "pattern": r"factorial|faktorial",
        "code": """def factorial(n):
    \"\"\"Calculate factorial of n.\"\"\"
    if n <= 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result""",
    },
    "is_prime": {
        "pattern": r"prime|prima|is_prime",
        "code": """def is_prime(n):
    \"\"\"Check if n is a prime number.\"\"\"
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True""",
    },
    "is_palindrome": {
        "pattern": r"palindrome|palindrom",
        "code": """def is_palindrome(s):
    \"\"\"Check if string is a palindrome.\"\"\"
    s = s.lower().replace(' ', '')
    return s == s[::-1]""",
    },
    "reverse_string": {
        "pattern": r"reverse.*string|string.*reverse|balik.*string",
        "code": """def reverse_string(s):
    \"\"\"Reverse a string.\"\"\"
    return s[::-1]""",
    },
    "count_vowels": {
        "pattern": r"count.*vowel|vowel.*count|hitung.*vocal",
        "code": """def count_vowels(s):
    \"\"\"Count vowels in a string.\"\"\"
    return sum(1 for c in s.lower() if c in 'aeiou')""",
    },
    "binary_search": {
        "pattern": r"binary.?search",
        "code": """def binary_search(arr, target):
    \"\"\"Binary search in sorted array.\"\"\"
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1""",
    },
    "bubble_sort": {
        "pattern": r"bubble.?sort",
        "code": """def bubble_sort(arr):
    \"\"\"Sort array using bubble sort.\"\"\"
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr""",
    },
    "quicksort": {
        "pattern": r"quick.?sort",
        "code": """def quicksort(arr):
    \"\"\"Sort array using quicksort.\"\"\"
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)""",
    },
    "merge_sort": {
        "pattern": r"merge.?sort",
        "code": """def merge_sort(arr):
    \"\"\"Sort array using merge sort.\"\"\"
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result""",
    },
    "two_sum": {
        "pattern": r"two.?sum|dua.*jumlah|pair.*sum",
        "code": """def two_sum(nums, target):
    \"\"\"Find two indices where values sum to target.\"\"\"
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []""",
    },
    "flatten": {
        "pattern": r"flatten|ratakan|nested.*list",
        "code": """def flatten(lst):
    \"\"\"Flatten a nested list.\"\"\"
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result""",
    },
    "anagram": {
        "pattern": r"anagram",
        "code": """def are_anagrams(s1, s2):
    \"\"\"Check if two strings are anagrams.\"\"\"
    return sorted(s1.lower().replace(' ', '')) == sorted(s2.lower().replace(' ', ''))""",
    },
    "stack": {
        "pattern": r"class.*stack|stack.*class|stack\s+data",
        "code": """class Stack:
    \"\"\"Stack data structure.\"\"\"
    def __init__(self):
        self.items = []
    def push(self, item):
        self.items.append(item)
    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        return None
    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        return None
    def is_empty(self):
        return len(self.items) == 0
    def size(self):
        return len(self.items)""",
    },
    "queue": {
        "pattern": r"class.*queue|queue.*class|queue\s+data",
        "code": """class Queue:
    \"\"\"Queue data structure.\"\"\"
    def __init__(self):
        self.items = []
    def enqueue(self, item):
        self.items.insert(0, item)
    def dequeue(self):
        if not self.is_empty():
            return self.items.pop()
        return None
    def is_empty(self):
        return len(self.items) == 0
    def size(self):
        return len(self.items)""",
    },
    "linked_list": {
        "pattern": r"linked.?list",
        "code": """class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    \"\"\"Linked list data structure.\"\"\"
    def __init__(self):
        self.head = None
    def append(self, data):
        if not self.head:
            self.head = Node(data)
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = Node(data)
    def display(self):
        elements = []
        current = self.head
        while current:
            elements.append(current.data)
            current = current.next
        return elements""",
    },
    "hashmap": {
        "pattern": r"hash.?map|hash.?table|dictionary",
        "code": """class HashMap:
    \"\"\"Simple hash map implementation.\"\"\"
    def __init__(self, size=16):
        self.size = size
        self.buckets = [[] for _ in range(size)]
    def _hash(self, key):
        return hash(key) % self.size
    def put(self, key, value):
        idx = self._hash(key)
        for i, (k, v) in enumerate(self.buckets[idx]):
            if k == key:
                self.buckets[idx][i] = (key, value)
                return
        self.buckets[idx].append((key, value))
    def get(self, key):
        idx = self._hash(key)
        for k, v in self.buckets[idx]:
            if k == key:
                return v
        raise KeyError(key)
    def delete(self, key):
        idx = self._hash(key)
        self.buckets[idx] = [(k, v) for k, v in self.buckets[idx] if k != key]""",
    },
    "lcs": {
        "pattern": r"lcs|longest.*common.*subsequence",
        "code": """def lcs(s1, s2):
    \"\"\"Find length of longest common subsequence.\"\"\"
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]""",
    },
    "knapsack": {
        "pattern": r"knapsack|tas.*ransel",
        "code": """def knapsack(weights, values, capacity):
    \"\"\"0/1 Knapsack problem.\"\"\"
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            dp[i][w] = dp[i-1][w]
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], dp[i-1][w-weights[i-1]] + values[i-1])
    return dp[n][capacity]""",
    },
    "edit_distance": {
        "pattern": r"edit.?distance|levenshtein",
        "code": """def edit_distance(s1, s2):
    \"\"\"Compute minimum edit distance between two strings.\"\"\"
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    return dp[m][n]""",
    },
    "max_subarray": {
        "pattern": r"max.*subarray|kadane|subarray.*terbesar",
        "code": """def max_subarray(arr):
    \"\"\"Find contiguous subarray with largest sum (Kadane's).\"\"\"
    max_sum = current_sum = arr[0]
    for num in arr[1:]:
        current_sum = max(num, current_sum + num)
        max_sum = max(max_sum, current_sum)
    return max_sum""",
    },
    "valid_parentheses": {
        "pattern": r"valid.*parenthes|bracket.*valid|kurung.*valid",
        "code": """def valid_parentheses(s):
    \"\"\"Check if string of brackets is valid.\"\"\"
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}
    for char in s:
        if char in mapping:
            if not stack or stack[-1] != mapping[char]:
                return False
            stack.pop()
        else:
            stack.append(char)
    return len(stack) == 0""",
    },
    "decorator_timer": {
        "pattern": r"decorator.*timer|timer.*decorator|measure.*time",
        "code": """import time

def timer(func):
    \"\"\"Decorator to measure function execution time.\"\"\"
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f'{func.__name__} took {elapsed:.4f}s')
        return result
    return wrapper""",
    },
    "decorator_cache": {
        "pattern": r"cache|memoize|memoization",
        "code": """def memoize(func):
    \"\"\"Decorator for memoization (caching).\"\"\"
    cache = {}
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrapper""",
    },
    "http_get": {
        "pattern": r"http.*get|fetch.*url|request.*get",
        "code": """import urllib.request
import json

def http_get(url, headers=None):
    \"\"\"Make an HTTP GET request.\"\"\"
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))""",
    },
    "read_file": {
        "pattern": r"read.*file|baca.*file",
        "code": """def read_file(path):
    \"\"\"Read file content.\"\"\"
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()""",
    },
    "write_file": {
        "pattern": r"write.*file|tulis.*file|simpan.*file",
        "code": """def write_file(path, content):
    \"\"\"Write content to file.\"\"\"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)""",
    },
    "sqlite_create": {
        "pattern": r"sqlite.*create|create.*table|buat.*table",
        "code": """import sqlite3

def create_table(db_path, table_name, columns):
    \"\"\"Create a SQLite table.\"\"\"
    conn = sqlite3.connect(db_path)
    col_defs = ', '.join(f'{name} {dtype}' for name, dtype in columns.items())
    conn.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({col_defs})')
    conn.commit()
    conn.close()""",
    },
    "dijkstra": {
        "pattern": r"dijkstra|shortest.?path|jalur.*pendek",
        "code": """import heapq

def dijkstra(graph, start):
    \"\"\"Dijkstra's shortest path algorithm.\"\"\"
    dist = {node: float('inf') for node in graph}
    dist[start] = 0
    pq = [(0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                heapq.heappush(pq, (dist[v], v))
    return dist""",
    },
    "bfs": {
        "pattern": r"\bbfs\b|breadth.?first",
        "code": """from collections import deque

def bfs(graph, start):
    \"\"\"Breadth-first search traversal.\"\"\"
    visited = set()
    queue = deque([start])
    visited.add(start)
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return order""",
    },
    "dfs": {
        "pattern": r"\bdfs\b|depth.?first",
        "code": """def dfs(graph, start, visited=None):
    \"\"\"Depth-first search traversal.\"\"\"
    if visited is None:
        visited = set()
    visited.add(start)
    order = [start]
    for neighbor in graph.get(start, []):
        if neighbor not in visited:
            order.extend(dfs(graph, neighbor, visited))
    return order""",
    },
    "trie": {
        "pattern": r"\btrie\b|prefix.?tree",
        "code": """class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    \"\"\"Prefix tree (Trie) data structure.\"\"\"
    def __init__(self):
        self.root = TrieNode()
    def insert(self, word):
        node = self.root
        for c in word:
            if c not in node.children:
                node.children[c] = TrieNode()
            node = node.children[c]
        node.is_end = True
    def search(self, word):
        node = self.root
        for c in word:
            if c not in node.children:
                return False
            node = node.children[c]
        return node.is_end
    def starts_with(self, prefix):
        node = self.root
        for c in prefix:
            if c not in node.children:
                return False
            node = node.children[c]
        return True""",
    },
    "graph_dijkstra": {
        "pattern": r"graph.*dijkstra|dijkstra.*graph",
        "code": """import heapq

class Graph:
    \"\"\"Weighted graph with Dijkstra shortest path.\"\"\"
    def __init__(self):
        self.edges = {}
    def add_edge(self, u, v, w):
        self.edges.setdefault(u, []).append((v, w))
        self.edges.setdefault(v, []).append((u, w))
    def dijkstra(self, start):
        dist = {start: 0}
        pq = [(0, start)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, float('inf')):
                continue
            for v, w in self.edges.get(u, []):
                nd = d + w
                if nd < dist.get(v, float('inf')):
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        return dist""",
    },
    "class_inheritance": {
        "pattern": r"inheritance|extends|inherit|class.*parent|subclass",
        "code": """class Animal:
    \"\"\"Base class.\"\"\"
    def __init__(self, name):
        self.name = name
    def speak(self):
        raise NotImplementedError

class Dog(Animal):
    \"\"\"Derived class.\"\"\"
    def speak(self):
        return f'{self.name} says Woof!'

class Cat(Animal):
    \"\"\"Derived class.\"\"\"
    def speak(self):
        return f'{self.name} says Meow!'""",
    },
    "context_manager": {
        "pattern": r"context.?manager|with.*open|__enter__|__exit__",
        "code": """class FileManager:
    \"\"\"Context manager for file operations.\"\"\"
    def __init__(self, path, mode='r'):
        self.path = path
        self.mode = mode
        self.file = None
    def __enter__(self):
        self.file = open(self.path, self.mode)
        return self.file
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()""",
    },
    "dataclass": {
        "pattern": r"dataclass|@dataclass|data.?class",
        "code": """from dataclasses import dataclass, field
from typing import List

@dataclass
class Person:
    \"\"\"A data class for Person.\"\"\"
    name: str
    age: int
    email: str = ''
    hobbies: List[str] = field(default_factory=list)""",
    },
    "iterator": {
        "pattern": r"iterator|iter.*class|__iter__|generator",
        "code": """class Counter:
    \"\"\"An iterator that counts up.\"\"\"
    def __init__(self, start=0, end=10):
        self.current = start
        self.end = end
    def __iter__(self):
        return self
    def __next__(self):
        if self.current >= self.end:
            raise StopIteration
        self.current += 1
        return self.current - 1""",
    },
    "property": {
        "pattern": r"@property|property.*decorator|getter.*setter",
        "code": """class Circle:
    \"\"\"Circle with property accessors.\"\"\"
    def __init__(self, radius):
        self._radius = radius
    @property
    def radius(self):
        return self._radius
    @radius.setter
    def radius(self, value):
        if value < 0:
            raise ValueError('Radius cannot be negative')
        self._radius = value
    @property
    def area(self):
        import math
        return math.pi * self._radius ** 2""",
    },
}


# ============================================================
# JAVASCRIPT TEMPLATES
# ============================================================

JAVASCRIPT_TEMPLATES = {
    "js_fibonacci": {
        "pattern": r"javascript.*fib|js.*fib|function.*fibonacci.*js|node.*fib",
        "code": """function fibonacci(n) {
    if (n <= 1) return n;
    let a = 0, b = 1;
    for (let i = 2; i <= n; i++) {
        [a, b] = [b, a + b];
    }
    return b;
}""",
    },
    "js_reverse_string": {
        "pattern": r"javascript.*reverse.*string|js.*reverse",
        "code": """function reverseString(s) {
    return s.split('').reverse().join('');
}""",
    },
    "js_is_palindrome": {
        "pattern": r"javascript.*palindrome|js.*palindrome",
        "code": """function isPalindrome(s) {
    const cleaned = s.toLowerCase().replace(/\\s/g, '');
    return cleaned === cleaned.split('').reverse().join('');
}""",
    },
    "js_binary_search": {
        "pattern": r"javascript.*binary.*search|js.*binary.*search",
        "code": """function binarySearch(arr, target) {
    let lo = 0, hi = arr.length - 1;
    while (lo <= hi) {
        const mid = Math.floor((lo + hi) / 2);
        if (arr[mid] === target) return mid;
        else if (arr[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}""",
    },
    "js_quicksort": {
        "pattern": r"javascript.*quick.*sort|js.*quick.*sort",
        "code": """function quicksort(arr) {
    if (arr.length <= 1) return arr;
    const pivot = arr[Math.floor(arr.length / 2)];
    const left = arr.filter(x => x < pivot);
    const middle = arr.filter(x => x === pivot);
    const right = arr.filter(x => x > pivot);
    return [...quicksort(left), ...middle, ...quicksort(right)];
}""",
    },
    "js_two_sum": {
        "pattern": r"javascript.*two.*sum|js.*two.*sum",
        "code": """function twoSum(nums, target) {
    const seen = {};
    for (let i = 0; i < nums.length; i++) {
        const complement = target - nums[i];
        if (complement in seen) return [seen[complement], i];
        seen[nums[i]] = i;
    }
    return [];
}""",
    },
    "js_fetch_api": {
        "pattern": r"javascript.*fetch|js.*fetch|node.*fetch|async.*fetch",
        "code": """async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}""",
    },
    "js_debounce": {
        "pattern": r"debounce|throttle.*js|js.*debounce",
        "code": """function debounce(fn, delay = 300) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}""",
    },
    "js_linked_list": {
        "pattern": r"javascript.*linked.*list|js.*linked.*list",
        "code": """class ListNode {
    constructor(val = 0, next = null) {
        this.val = val;
        this.next = next;
    }
}

class LinkedList {
    constructor() {
        this.head = null;
    }
    append(val) {
        if (!this.head) { this.head = new ListNode(val); return; }
        let cur = this.head;
        while (cur.next) cur = cur.next;
        cur.next = new ListNode(val);
    }
    toArray() {
        const result = [];
        let cur = this.head;
        while (cur) { result.push(cur.val); cur = cur.next; }
        return result;
    }
}""",
    },
    "js_valid_parentheses": {
        "pattern": r"javascript.*valid.*paren|js.*valid.*paren",
        "code": """function validParentheses(s) {
    const stack = [];
    const map = {')': '(', ']': '[', '}': '{'};
    for (const c of s) {
        if (c in map) {
            if (!stack.length || stack[stack.length - 1] !== map[c]) return false;
            stack.pop();
        } else {
            stack.push(c);
        }
    }
    return stack.length === 0;
}""",
    },
    "js_memoize": {
        "pattern": r"javascript.*memoize|js.*memoize|js.*cache|javascript.*cache",
        "code": """function memoize(fn) {
    const cache = new Map();
    return function (...args) {
        const key = JSON.stringify(args);
        if (cache.has(key)) return cache.get(key);
        const result = fn.apply(this, args);
        cache.set(key, result);
        return result;
    };
}""",
    },
    "js_class_person": {
        "pattern": r"javascript.*class|js.*class.*example",
        "code": """class Person {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }
    greet() {
        return `Hi, I'm ${this.name}, ${this.age} years old.`;
    }
    static create(name, age) {
        return new Person(name, age);
    }
}""",
    },
    "js_promise_all": {
        "pattern": r"javascript.*promise.*all|js.*promise.*all|parallel.*fetch",
        "code": """async function fetchAll(urls) {
    const results = await Promise.all(
        urls.map(url => fetch(url).then(r => r.json()))
    );
    return results;
}""",
    },
    "js_event_emitter": {
        "pattern": r"event.?emitter|event.?emitt|js.*event",
        "code": """class EventEmitter {
    constructor() {
        this.events = {};
    }
    on(event, callback) {
        (this.events[event] = this.events[event] || []).push(callback);
        return this;
    }
    emit(event, ...args) {
        (this.events[event] || []).forEach(fn => fn(...args));
        return this;
    }
    off(event, callback) {
        this.events[event] = (this.events[event] || []).filter(fn => fn !== callback);
        return this;
    }
}""",
    },
    "js_flatten": {
        "pattern": r"javascript.*flatten|js.*flatten",
        "code": """function flatten(arr) {
    return arr.reduce((acc, val) =>
        Array.isArray(val) ? acc.concat(flatten(val)) : acc.concat(val), []
    );
}""",
    },
    "js_deep_clone": {
        "pattern": r"deep.?clone|deep.?copy|clone.*object",
        "code": """function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') return obj;
    if (obj instanceof Date) return new Date(obj);
    if (Array.isArray(obj)) return obj.map(deepClone);
    const cloned = {};
    for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
            cloned[key] = deepClone(obj[key]);
        }
    }
    return cloned;
}""",
    },
    "js_array_group_by": {
        "pattern": r"group.?by|group.*array|js.*group",
        "code": """function groupBy(arr, keyFn) {
    return arr.reduce((groups, item) => {
        const key = keyFn(item);
        (groups[key] = groups[key] || []).push(item);
        return groups;
    }, {});
}""",
    },
    "js_throttle": {
        "pattern": r"throttle|throttle.*function|js.*throttle",
        "code": """function throttle(fn, limit) {
    let lastCall = 0;
    return function (...args) {
        const now = Date.now();
        if (now - lastCall >= limit) {
            lastCall = now;
            return fn.apply(this, args);
        }
    };
}""",
    },
    "js_curry": {
        "pattern": r"curry|curry.*function|currying",
        "code": """function curry(fn) {
    return function curried(...args) {
        if (args.length >= fn.length) {
            return fn.apply(this, args);
        }
        return function (...args2) {
            return curried.apply(this, args.concat(args2));
        };
    };
}""",
    },
    "js_async_retry": {
        "pattern": r"async.*retry|retry.*async|exponential.*backoff",
        "code": """async function retry(fn, retries = 3, delay = 1000) {
    for (let i = 0; i < retries; i++) {
        try {
            return await fn();
        } catch (err) {
            if (i === retries - 1) throw err;
            await new Promise(r => setTimeout(r, delay * Math.pow(2, i)));
        }
    }
}""",
    },
    "js_chunk": {
        "pattern": r"chunk|split.*array|chunk.*array",
        "code": """function chunk(arr, size) {
    const chunks = [];
    for (let i = 0; i < arr.length; i += size) {
        chunks.push(arr.slice(i, i + size));
    }
    return chunks;
}""",
    },
}


# ============================================================
# TYPESCRIPT TEMPLATES
# ============================================================

TYPESCRIPT_TEMPLATES = {
    "ts_fibonacci": {
        "pattern": r"typescript.*fib|ts.*fib|type.*fibonacci",
        "code": """function fibonacci(n: number): number {
    if (n <= 1) return n;
    let a = 0, b = 1;
    for (let i = 2; i <= n; i++) {
        [a, b] = [b, a + b];
    }
    return b;
}""",
    },
    "ts_interface": {
        "pattern": r"typescript.*interface|ts.*interface|type.*interface",
        "code": """interface User {
    id: number;
    name: string;
    email: string;
    role: 'admin' | 'user' | 'guest';
    createdAt?: Date;
}

function greet(user: User): string {
    return `Hello, ${user.name}!`;
}""",
    },
    "ts_generic": {
        "pattern": r"typescript.*generic|ts.*generic|type.*parameter",
        "code": """class Repository<T> {
    private items: T[] = [];

    add(item: T): void {
        this.items.push(item);
    }

    find(predicate: (item: T) => boolean): T | undefined {
        return this.items.find(predicate);
    }

    filter(predicate: (item: T) => boolean): T[] {
        return this.items.filter(predicate);
    }

    getAll(): T[] {
        return [...this.items];
    }
}""",
    },
    "ts_enum": {
        "pattern": r"typescript.*enum|ts.*enum",
        "code": """enum Direction {
    Up = 'UP',
    Down = 'DOWN',
    Left = 'LEFT',
    Right = 'RIGHT',
}

function move(direction: Direction): string {
    switch (direction) {
        case Direction.Up: return 'Moving up';
        case Direction.Down: return 'Moving down';
        case Direction.Left: return 'Moving left';
        case Direction.Right: return 'Moving right';
    }
}""",
    },
    "ts_type_guard": {
        "pattern": r"typescript.*type.?guard|ts.*type.?guard|is.*operator",
        "code": """interface Cat { meow(): void; }
interface Dog { bark(): void; }

function isCat(animal: Cat | Dog): animal is Cat {
    return (animal as Cat).meow !== undefined;
}

function makeSound(animal: Cat | Dog): string {
    if (isCat(animal)) {
        return 'Meow!';
    }
    return 'Woof!';
}""",
    },
}


# ============================================================
# RUST TEMPLATES
# ============================================================

RUST_TEMPLATES = {
    "rust_fibonacci": {
        "pattern": r"rust.*fib|rust.*fibonacci",
        "code": """fn fibonacci(n: u32) -> u64 {
    if n <= 1 { return n as u64; }
    let (mut a, mut b) = (0u64, 1u64);
    for _ in 2..=n {
        let temp = b;
        b = a + b;
        a = temp;
    }
    b
}""",
    },
    "rust_vector": {
        "pattern": r"rust.*vector|rust.*vec|rust.*array",
        "code": """fn main() {
    let mut nums = vec![3, 1, 4, 1, 5, 9, 2, 6];
    nums.sort();
    println!("Sorted: {:?}", nums);

    let doubled: Vec<i32> = nums.iter().map(|x| x * 2).collect();
    println!("Doubled: {:?}", doubled);

    let sum: i32 = nums.iter().sum();
    println!("Sum: {}", sum);
}""",
    },
    "rust_trait": {
        "pattern": r"rust.*trait|rust.*trait.*example|implement.*trait",
        "code": """trait Drawable {
    fn draw(&self) -> String;
    fn area(&self) -> f64;
}

struct Circle {
    radius: f64,
}

impl Drawable for Circle {
    fn draw(&self) -> String {
        format!("Drawing circle with radius {}", self.radius)
    }
    fn area(&self) -> f64 {
        std::f64::consts::PI * self.radius * self.radius
    }
}

struct Rectangle {
    width: f64,
    height: f64,
}

impl Drawable for Rectangle {
    fn draw(&self) -> String {
        format!("Drawing rectangle {}x{}", self.width, self.height)
    }
    fn area(&self) -> f64 {
        self.width * self.height
    }
}""",
    },
    "rust_struct": {
        "pattern": r"rust.*struct|rust.*impl|rust.*struct.*example",
        "code": """struct Point {
    x: f64,
    y: f64,
}

impl Point {
    fn new(x: f64, y: f64) -> Self {
        Point { x, y }
    }

    fn distance(&self, other: &Point) -> f64 {
        ((self.x - other.x).powi(2) + (self.y - other.y).powi(2)).sqrt()
    }

    fn midpoint(&self, other: &Point) -> Point {
        Point::new((self.x + other.x) / 2.0, (self.y + other.y) / 2.0)
    }
}""",
    },
    "rust_binary_search": {
        "pattern": r"rust.*binary.*search",
        "code": """fn binary_search(arr: &[i32], target: i32) -> Option<usize> {
    let mut lo = 0;
    let mut hi = arr.len();
    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        match arr[mid].cmp(&target) {
            std::cmp::Ordering::Equal => return Some(mid),
            std::cmp::Ordering::Less => lo = mid + 1,
            std::cmp::Ordering::Greater => hi = mid,
        }
    }
    None
}""",
    },
    "rust_hashmap": {
        "pattern": r"rust.*hashmap|rust.*hash.*map",
        "code": """use std::collections::HashMap;

fn word_count(text: &str) -> HashMap<String, usize> {
    let mut counts = HashMap::new();
    for word in text.split_whitespace() {
        let word = word.to_lowercase();
        *counts.entry(word).or_insert(0) += 1;
    }
    counts
}""",
    },
    "rust_option_result": {
        "pattern": r"rust.*option|rust.*result|rust.*unwrap|rust.*error.*handling",
        "code": """fn divide(a: f64, b: f64) -> Result<f64, String> {
    if b == 0.0 {
        Err("Cannot divide by zero".to_string())
    } else {
        Ok(a / b)
    }
}

fn find_first_even(numbers: &[i32]) -> Option<&i32> {
    numbers.iter().find(|&&n| n % 2 == 0)
}""",
    },
    "rust_closure": {
        "pattern": r"rust.*closure|rust.*fn.*pointer|rust.*lambda",
        "code": """fn apply_to_vec<F>(nums: &mut Vec<i32>, f: F)
where
    F: Fn(i32) -> i32,
{
    for num in nums.iter_mut() {
        *num = f(*num);
    }
}

fn main() {
    let mut nums = vec![1, 2, 3, 4, 5];
    apply_to_vec(&mut nums, |x| x * 2);
    println!("{:?}", nums); // [2, 4, 6, 8, 10]
}""",
    },
    "rust_iterator": {
        "pattern": r"rust.*iterator|rust.*iter|rust.*map.*filter",
        "code": """fn main() {
    let nums = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

    let evens_sum: i32 = nums.iter()
        .filter(|&&x| x % 2 == 0)
        .sum();

    let squared: Vec<i32> = nums.iter()
        .map(|&x| x * x)
        .collect();

    println!("Evens sum: {}", evens_sum);
    println!("Squared: {:?}", squared);
}""",
    },
    "rust_enum_match": {
        "pattern": r"rust.*enum|rust.*match",
        "code": """enum TrafficLight {
    Red,
    Yellow,
    Green,
}

impl TrafficLight {
    fn wait_time(&self) -> u32 {
        match self {
            TrafficLight::Red => 60,
            TrafficLight::Yellow => 5,
            TrafficLight::Green => 45,
        }
    }

    fn next(&self) -> TrafficLight {
        match self {
            TrafficLight::Red => TrafficLight::Green,
            TrafficLight::Green => TrafficLight::Yellow,
            TrafficLight::Yellow => TrafficLight::Red,
        }
    }
}""",
    },
    "rust_thread": {
        "pattern": r"rust.*thread|rust.*concurrent|rust.*parallel|rust.*spawn",
        "code": """use std::thread;

fn main() {
    let handles: Vec<_> = (0..5).map(|i| {
        thread::spawn(move || {
            println!("Thread {} started", i);
            thread::sleep(std::time::Duration::from_millis(100));
            println!("Thread {} finished", i);
            i * i
        })
    }).collect();

    let results: Vec<_> = handles.into_iter()
        .map(|h| h.join().unwrap())
        .collect();

    println!("Results: {:?}", results);
}""",
    },
    "rust_generic_max": {
        "pattern": r"rust.*generic.*max|rust.*max.*generic|generic.*PartialOrd",
        "code": """fn max_value<T: PartialOrd>(a: T, b: T) -> T {
    if a >= b { a } else { b }
}""",
    },
}


# ============================================================
# C++ TEMPLATES
# ============================================================

CPP_TEMPLATES = {
    "cpp_fibonacci": {
        "pattern": r"c\+\+.*fib|cpp.*fib|cplus.*fib",
        "code": """long long fibonacci(int n) {
    if (n <= 1) return n;
    long long a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        long long temp = b;
        b = a + b;
        a = temp;
    }
    return b;
}""",
    },
    "cpp_lambda": {
        "pattern": r"c\+\+.*lambda|cpp.*lambda|cplus.*lambda|c\+\+.*closure",
        "code": """void processVector(std::vector<int>& nums) {
    // Lambda for sorting
    std::sort(nums.begin(), nums.end(), [](int a, int b) {
        return a > b;  // Descending
    });

    // Lambda for filtering
    auto it = std::remove_if(nums.begin(), nums.end(), [](int n) {
        return n < 0;
    });
    nums.erase(it, nums.end());

    // Lambda for transform
    std::transform(nums.begin(), nums.end(), nums.begin(), [](int n) {
        return n * 2;
    });
}""",
    },
    "cpp_vector_sort": {
        "pattern": r"c\+\+.*sort|cpp.*sort|cplus.*sort",
        "code": """#include <vector>
#include <algorithm>

void sortVector(std::vector<int>& nums) {
    std::sort(nums.begin(), nums.end());
}""",
    },
    "cpp_class": {
        "pattern": r"c\+\+.*class|cpp.*class|cplus.*class",
        "code": """class Point {
private:
    double x, y;
public:
    Point(double x = 0, double y = 0) : x(x), y(y) {}
    double getX() const { return x; }
    double getY() const { return y; }
    double distanceTo(const Point& other) const {
        double dx = x - other.x;
        double dy = y - other.y;
        return std::sqrt(dx * dx + dy * dy);
    }
};""",
    },
    "cpp_binary_search": {
        "pattern": r"c\+\+.*binary.*search|cpp.*binary.*search",
        "code": """#include <vector>

int binarySearch(const std::vector<int>& arr, int target) {
    int lo = 0, hi = arr.size() - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] == target) return mid;
        else if (arr[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}""",
    },
    "cpp_linked_list": {
        "pattern": r"c\+\+.*linked.*list|cpp.*linked.*list",
        "code": """struct ListNode {
    int val;
    ListNode* next;
    ListNode(int x) : val(x), next(nullptr) {}
};

class LinkedList {
private:
    ListNode* head;
public:
    LinkedList() : head(nullptr) {}
    void append(int val) {
        if (!head) { head = new ListNode(val); return; }
        ListNode* cur = head;
        while (cur->next) cur = cur->next;
        cur->next = new ListNode(val);
    }
};""",
    },
    "cpp_template_function": {
        "pattern": r"c\+\+.*template|cpp.*template|cplus.*template|generic.*c\+\+",
        "code": """template <typename T>
T findMax(const std::vector<T>& vec) {
    if (vec.empty()) throw std::runtime_error("Empty vector");
    T maxVal = vec[0];
    for (size_t i = 1; i < vec.size(); i++) {
        if (vec[i] > maxVal) maxVal = vec[i];
    }
    return maxVal;
}""",
    },
    "cpp_smart_pointer": {
        "pattern": r"c\+\+.*smart.*pointer|cpp.*shared_ptr|unique_ptr|cplus.*pointer",
        "code": """#include <memory>

class Resource {
public:
    void doWork() { /* ... */ }
};

void useResource() {
    auto ptr = std::make_unique<Resource>();
    ptr->doWork();

    auto shared = std::make_shared<Resource>();
    shared->doWork();
}""",
    },
    "cpp_map": {
        "pattern": r"c\+\+.*map|cpp.*map|cplus.*unordered.*map",
        "code": """#include <map>
#include <string>

std::map<std::string, int> wordCount(const std::string& text) {
    std::map<std::string, int> counts;
    std::string word;
    for (char c : text) {
        if (c == ' ') {
            if (!word.empty()) {
                counts[word]++;
                word.clear();
            }
        } else {
            word += c;
        }
    }
    if (!word.empty()) counts[word]++;
    return counts;
}""",
    },
    "cpp_move_semantics": {
        "pattern": r"c\+\+.*move|cpp.*move|std::move|cplus.*rvalue|c\+\+.*&&",
        "code": """#include <string>
#include <utility>

class Buffer {
private:
    char* data;
    size_t size;
public:
    // Constructor
    Buffer(size_t sz) : size(sz), data(new char[sz]) {}

    // Move constructor
    Buffer(Buffer&& other) noexcept
        : data(other.data), size(other.size) {
        other.data = nullptr;
        other.size = 0;
    }

    // Move assignment
    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data;
            data = other.data;
            size = other.size;
            other.data = nullptr;
            other.size = 0;
        }
        return *this;
    }

    ~Buffer() { delete[] data; }
};""",
    },
    "cpp_vector_ops": {
        "pattern": r"c\+\+.*vector.*push|cpp.*vector.*erase|vector.*operations",
        "code": """#include <vector>
#include <algorithm>

void vectorOps(std::vector<int>& nums) {
    nums.push_back(42);
    auto it = std::find(nums.begin(), nums.end(), 42);
    if (it != nums.end()) nums.erase(it);
    std::sort(nums.begin(), nums.end());
}""",
    },
    "cpp_raii_file": {
        "pattern": r"c\+\+.*raii|cpp.*raii|raii.*file|file.*guard",
        "code": """class FileGuard {
    FILE* f;
public:
    FileGuard(const char* path, const char* mode) : f(fopen(path, mode)) {}
    ~FileGuard() { if (f) fclose(f); }
    FILE* get() const { return f; }
    // Prevent copy
    FileGuard(const FileGuard&) = delete;
    FileGuard& operator=(const FileGuard&) = delete;
};""",
    },
    "cpp_unique_ptr_deleter": {
        "pattern": r"c\+\+.*unique.*deleter|cpp.*custom.*deleter|raii.*deleter",
        "code": """auto ptr = std::unique_ptr<FILE, decltype(&fclose)>(fopen(path, "r"), fclose);""",
    },
}


# ============================================================
# GO TEMPLATES
# ============================================================

GO_TEMPLATES = {
    "go_fibonacci": {
        "pattern": r"go\s+fib|golang.*fib|go.*fibonacci",
        "code": """func fibonacci(n int) int {
    if n <= 1 {
        return n
    }
    a, b := 0, 1
    for i := 2; i <= n; i++ {
        a, b = b, a+b
    }
    return b
}""",
    },
    "go_struct": {
        "pattern": r"go\s+struct|golang.*struct|go.*struct.*example",
        "code": """type Person struct {
    Name string
    Age  int
}

func NewPerson(name string, age int) *Person {
    return &Person{Name: name, Age: age}
}

func (p *Person) Greet() string {
    return fmt.Sprintf("Hi, I'm %s, %d years old", p.Name, p.Age)
}""",
    },
    "go_interface": {
        "pattern": r"go\s+interface|golang.*interface|go.*interface.*example",
        "code": """type Shape interface {
    Area() float64
    Perimeter() float64
}

type Circle struct {
    Radius float64
}

func (c Circle) Area() float64 {
    return math.Pi * c.Radius * c.Radius
}

func (c Circle) Perimeter() float64 {
    return 2 * math.Pi * c.Radius
}""",
    },
    "go_goroutine": {
        "pattern": r"go\s+goroutine|golang.*goroutine|go.*concurrent|go.*channel",
        "code": """func worker(id int, jobs <-chan int, results chan<- int) {
    for j := range jobs {
        fmt.Printf("Worker %d processing job %d\\n", id, j)
        time.Sleep(time.Second)
        results <- j * 2
    }
}

func main() {
    jobs := make(chan int, 100)
    results := make(chan int, 100)

    for w := 1; w <= 3; w++ {
        go worker(w, jobs, results)
    }

    for j := 1; j <= 9; j++ {
        jobs <- j
    }
    close(jobs)

    for a := 1; a <= 9; a++ {
        <-results
    }
}""",
    },
    "go_http_server": {
        "pattern": r"go.*http.*server|golang.*server|go.*web.*server|golang.*http",
        "code": """package main

import (
    "encoding/json"
    "fmt"
    "net/http"
)

type Response struct {
    Message string `json:"message"`
    Status  int    `json:"status"`
}

func helloHandler(w http.ResponseWriter, r *http.Request) {
    resp := Response{Message: "Hello, World!", Status: 200}
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(resp)
}

func main() {
    http.HandleFunc("/api/hello", helloHandler)
    fmt.Println("Server running on :8080")
    http.ListenAndServe(":8080", nil)
}""",
    },
    "go_error_handling": {
        "pattern": r"go.*error.*handl|golang.*error|go.*error.*return",
        "code": """import (
    "fmt"
    "strconv"
)

func parseAge(input string) (int, error) {
    age, err := strconv.Atoi(input)
    if err != nil {
        return 0, fmt.Errorf("invalid age: %w", err)
    }
    if age < 0 || age > 150 {
        return 0, fmt.Errorf("age out of range: %d", age)
    }
    return age, nil
}""",
    },
    "go_map_reduce": {
        "pattern": r"go.*map.*reduce|golang.*map.*reduce|go.*slice.*operation",
        "code": """func Map(nums []int, fn func(int) int) []int {
    result := make([]int, len(nums))
    for i, n := range nums {
        result[i] = fn(n)
    }
    return result
}

func Filter(nums []int, fn func(int) bool) []int {
    var result []int
    for _, n := range nums {
        if fn(n) {
            result = append(result, n)
        }
    }
    return result
}

func Reduce(nums []int, fn func(int, int) int, init int) int {
    result := init
    for _, n := range nums {
        result = fn(result, n)
    }
    return result
}""",
    },
    "go_json_marshal": {
        "pattern": r"go.*json|golang.*json|go.*marshal|go.*unmarshal",
        "code": """import (
    "encoding/json"
    "fmt"
)

type Config struct {
    Host    string   `json:"host"`
    Port    int      `json:"port"`
    Debug   bool     `json:"debug,omitempty"`
    Tags    []string `json:"tags,omitempty"`
}

func loadConfig(data []byte) (*Config, error) {
    var cfg Config
    if err := json.Unmarshal(data, &cfg); err != nil {
        return nil, fmt.Errorf("parse error: %w", err)
    }
    return &cfg, nil
}

func saveConfig(cfg *Config) ([]byte, error) {
    return json.MarshalIndent(cfg, "", "  ")
}""",
    },
    "go_error_handling": {
        "pattern": r"go.*error.*handle|golang.*error.*return|go.*fmt.*Errorf",
        "code": """func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, fmt.Errorf("cannot divide by zero")
    }
    return a / b, nil
}""",
    },
    "go_mutex": {
        "pattern": r"go.*mutex|golang.*mutex|sync.*Mutex",
        "code": """type SafeCounter struct {
    mu sync.Mutex
    v  map[string]int
}

func (c *SafeCounter) Inc(key string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.v[key]++
}

func (c *SafeCounter) Value(key string) int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.v[key]
}""",
    },
    "go_defer": {
        "pattern": r"go.*defer|golang.*defer|defer.*close",
        "code": """func readFile(path string) ([]byte, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer f.Close()
    return io.ReadAll(f)
}""",
    },
    "go_context": {
        "pattern": r"go.*context.*timeout|golang.*context|context.*WithTimeout",
        "code": """func fetchWithTimeout(url string) ([]byte, error) {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil { return nil, err }
    resp, err := http.DefaultClient.Do(req)
    if err != nil { return nil, err }
    defer resp.Body.Close()
    return io.ReadAll(resp.Body)
}""",
    },
}


# ============================================================
# C LANGUAGE TEMPLATES
# ============================================================

C_TEMPLATES = {
    "c_fibonacci": {
        "pattern": r"\bc\s+fib|clang.*fib|c\b.*fibonacci",
        "code": """int fibonacci(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        int temp = b;
        b = a + b;
        a = temp;
    }
    return b;
}""",
    },
    "c_linked_list": {
        "pattern": r"\bc\s+linked.*list|clang.*linked.*list",
        "code": """typedef struct Node {
    int data;
    struct Node* next;
} Node;

Node* createNode(int data) {
    Node* node = (Node*)malloc(sizeof(Node));
    node->data = data;
    node->next = NULL;
    return node;
}

void append(Node** head, int data) {
    Node* node = createNode(data);
    if (*head == NULL) { *head = node; return; }
    Node* cur = *head;
    while (cur->next) cur = cur->next;
    cur->next = node;
}""",
    },
    "c_binary_search": {
        "pattern": r"\bc\s+binary.*search|clang.*binary.*search",
        "code": """int binary_search(int arr[], int n, int target) {
    int lo = 0, hi = n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] == target) return mid;
        else if (arr[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}""",
    },
    "c_file_io": {
        "pattern": r"\bc\s+file.*io|clang.*file.*io|c\b.*fopen|c\b.*fread",
        "code": """#include <stdio.h>

void writeFile(const char* filename, const char* content) {
    FILE* f = fopen(filename, "w");
    if (f) {
        fprintf(f, "%s", content);
        fclose(f);
    }
}

char* readFile(const char* filename) {
    FILE* f = fopen(filename, "r");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    rewind(f);
    char* buffer = malloc(size + 1);
    fread(buffer, 1, size, f);
    buffer[size] = '\\0';
    fclose(f);
    return buffer;
}""",
    },
}


# ============================================================
# TEMPLATE MATCHING ENGINE
# ============================================================

# ============================================================
# DEBUGGING TEMPLATES
# ============================================================

DEBUG_TEMPLATES = {
    "fix_sum_list": {
        "pattern": r"sum.*list|total.*list|fix.*sum_list",
        "code": """def sum_list(nums):
    total = 0
    for n in nums:
        total += n  # Fixed: was == instead of +=
    return total""",
    },
    "fix_is_even": {
        "pattern": r"is.*even|check.*even|fix.*is_even",
        "code": """def is_even(n):
    return n % 2 == 0  # Fixed: was == 1 instead of == 0""",
    },
    "fix_reverse_string": {
        "pattern": r"fix.*reverse|reverse.*missing.*return",
        "code": """def reverse_string(s):
    result = ''
    for c in s:
        result = c + result
    return result  # Fixed: added missing return""",
    },
    "fix_binary_search_offbyone": {
        "pattern": r"fix.*binary.*search|binary.*search.*off.*by.*one",
        "code": """def binary_search(arr, target):
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1  # Fixed: was lo = mid (infinite loop)
        else:
            hi = mid
    return -1""",
    },
    "fix_recursive_fib": {
        "pattern": r"fix.*recursive.*fib|fibonacci.*exponential|fibonacci.*slow",
        "code": """def fibonacci(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
    return memo[n]""",
    },
}

# ============================================================
# GIT KNOWLEDGE TEMPLATES
# ============================================================

GIT_TEMPLATES = {
    "git_status": {
        "pattern": r"git.*status|show.*status|current.*git",
        "code": "git status - Shows the current status of your working tree including staged, unstaged, and untracked files.",
    },
    "git_branch": {
        "pattern": r"git.*branch|create.*branch|new.*branch|checkout.*-b|switch.*-c",
        "code": "git checkout -b feature  OR  git switch -c feature  - Creates a new branch called 'feature' and switches to it.",
    },
    "git_reset": {
        "pattern": r"undo.*commit|reset.*commit|revert.*commit|last.*commit",
        "code": "git reset --soft HEAD~1  - Undo last commit but keep changes staged.\ngit reset HEAD~1  - Undo last commit and unstage changes.\ngit reset --hard HEAD~1  - Undo last commit and discard changes.",
    },
    "git_log": {
        "pattern": r"git.*log|show.*history|commit.*history",
        "code": "git log --oneline --graph  - Show commit history as compact graph.",
    },
    "git_merge": {
        "pattern": r"git.*merge|merge.*branch",
        "code": "git merge feature  - Merge the 'feature' branch into current branch.",
    },
    "git_stash": {
        "pattern": r"git.*stash|stash.*changes",
        "code": "git stash  - Stash current changes.\ngit stash pop  - Apply and remove stash.",
    },
    "git_diff": {
        "pattern": r"git.*diff|show.*changes|view.*diff",
        "code": "git diff  - Show unstaged changes.\ngit diff --staged  - Show staged changes.",
    },
}

# ============================================================
# TOOL USE TEMPLATES
# ============================================================

TOOL_TEMPLATES = {
    "read_file_lines": {
        "pattern": r"read.*file.*lines|count.*lines|how.*many.*lines",
        "code": "def count_lines(path):\n    with open(path) as f:\n        return len(f.readlines())",
    },
    "search_python_class": {
        "pattern": r"search.*class|find.*class|grep.*class|files.*contain.*class",
        "code": "grep -r 'class ' --include='*.py' .  - Search for 'class' in all Python files.",
    },
    "python_version": {
        "pattern": r"python.*version|python.*--version|version.*python",
        "code": "python --version  - Shows the Python version.",
    },
    "list_files": {
        "pattern": r"list.*files|show.*files|ls.*directory|dir.*content",
        "code": "ls -la  - List all files in current directory with details.",
    },
    "disk_usage": {
        "pattern": r"disk.*usage|space.*used|storage.*info",
        "code": "df -h  - Show disk usage.\ndu -sh .  - Show current directory size.",
    },
}


# ============================================================
# TEMPLATE MATCHING ENGINE
# ============================================================

# Order matters: check language-specific templates FIRST
ALL_LANGUAGES = {
    'debug': DEBUG_TEMPLATES,  # Debugging patterns first
    'git': GIT_TEMPLATES,  # Git knowledge
    'tool': TOOL_TEMPLATES,  # Tool usage
    'javascript': JAVASCRIPT_TEMPLATES,
    'typescript': TYPESCRIPT_TEMPLATES,
    'rust': RUST_TEMPLATES,
    'cpp': CPP_TEMPLATES,
    'go': GO_TEMPLATES,
    'c': C_TEMPLATES,
    'python': PYTHON_TEMPLATES,  # Last: generic fallback
}


def match_template(user_input: str) -> dict:
    """Match user input to a code template (all languages).

    Returns:
        dict with 'matched', 'template_name', 'code', 'language'
    """
    text = user_input.lower()

    # Try each language in order
    for lang, templates in ALL_LANGUAGES.items():
        for name, template in templates.items():
            if re.search(template['pattern'], text):
                return {
                    'matched': True,
                    'template_name': name,
                    'code': template['code'],
                    'language': lang,
                }

    return {'matched': False, 'language': None}


def get_all_templates() -> dict:
    """Get all available templates grouped by language."""
    result = {}
    for lang, templates in ALL_LANGUAGES.items():
        result[lang] = {name: t['code'] for name, t in templates.items()}
    return result


def get_template_count() -> dict:
    """Get template count per language."""
    return {lang: len(templates) for lang, templates in ALL_LANGUAGES.items()}
