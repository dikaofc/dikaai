"""
DikaAI Coding Dataset - Training data for code generation.

Contains:
    - Python Q&A pairs (instruction → code)
    - Debugging pairs (error → fix)
    - Code completion pairs (context → next line)
    - Algorithm solutions (problem → code)
"""

import random
import json
from pathlib import Path


# ============================================================
# CODING Q&A PAIRS (instruction → code)
# ============================================================

CODING_QA = [
    # Basic Python
    {
        "instruction": "Write a Python function to check if a number is prime",
        "code": "def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True",
        "language": "python",
        "difficulty": "easy",
    },
    {
        "instruction": "Write a Python function to reverse a string",
        "code": "def reverse_string(s):\n    return s[::-1]",
        "language": "python",
        "difficulty": "easy",
    },
    {
        "instruction": "Write a Python function to count vowels in a string",
        "code": "def count_vowels(s):\n    return sum(1 for c in s.lower() if c in 'aeiou')",
        "language": "python",
        "difficulty": "easy",
    },
    {
        "instruction": "Write a Python function to find the largest element in a list",
        "code": "def find_largest(lst):\n    if not lst:\n        return None\n    largest = lst[0]\n    for item in lst[1:]:\n        if item > largest:\n            largest = item\n    return largest",
        "language": "python",
        "difficulty": "easy",
    },
    {
        "instruction": "Write a Python function to check if a string is a palindrome",
        "code": "def is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]",
        "language": "python",
        "difficulty": "easy",
    },
    {
        "instruction": "Write a Python function to calculate factorial",
        "code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
        "language": "python",
        "difficulty": "easy",
    },
    {
        "instruction": "Write a Python function to flatten a nested list",
        "code": "def flatten(lst):\n    result = []\n    for item in lst:\n        if isinstance(item, list):\n            result.extend(flatten(item))\n        else:\n            result.append(item)\n    return result",
        "language": "python",
        "difficulty": "medium",
    },
    {
        "instruction": "Write a Python function to remove duplicates from a list",
        "code": "def remove_duplicates(lst):\n    seen = set()\n    result = []\n    for item in lst:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result",
        "language": "python",
        "difficulty": "easy",
    },
    {
        "instruction": "Write a Python function to merge two sorted lists",
        "code": "def merge_sorted(a, b):\n    result = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            result.append(a[i])\n            i += 1\n        else:\n            result.append(b[j])\n            j += 1\n    result.extend(a[i:])\n    result.extend(b[j:])\n    return result",
        "language": "python",
        "difficulty": "medium",
    },
    {
        "instruction": "Write a Python function to find all pairs that sum to a target",
        "code": "def two_sum(nums, target):\n    seen = {}\n    result = []\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            result.append((seen[complement], i))\n        seen[num] = i\n    return result",
        "language": "python",
        "difficulty": "medium",
    },
    # Data structures
    {
        "instruction": "Write a Python class for a Stack",
        "code": "class Stack:\n    def __init__(self):\n        self.items = []\n    def push(self, item):\n        self.items.append(item)\n    def pop(self):\n        if not self.is_empty():\n            return self.items.pop()\n        return None\n    def peek(self):\n        if not self.is_empty():\n            return self.items[-1]\n        return None\n    def is_empty(self):\n        return len(self.items) == 0\n    def size(self):\n        return len(self.items)",
        "language": "python",
        "difficulty": "easy",
    },
    {
        "instruction": "Write a Python class for a Queue",
        "code": "class Queue:\n    def __init__(self):\n        self.items = []\n    def enqueue(self, item):\n        self.items.insert(0, item)\n    def dequeue(self):\n        if not self.is_empty():\n            return self.items.pop()\n        return None\n    def is_empty(self):\n        return len(self.items) == 0\n    def size(self):\n        return len(self.items)",
        "language": "python",
        "difficulty": "easy",
    },
    {
        "instruction": "Write a Python class for a Linked List",
        "code": "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\nclass LinkedList:\n    def __init__(self):\n        self.head = None\n    def append(self, data):\n        if not self.head:\n            self.head = Node(data)\n            return\n        current = self.head\n        while current.next:\n            current = current.next\n        current.next = Node(data)\n    def display(self):\n        elements = []\n        current = self.head\n        while current:\n            elements.append(current.data)\n            current = current.next\n        return elements",
        "language": "python",
        "difficulty": "medium",
    },
    # Algorithms
    {
        "instruction": "Write a Python function for binary search",
        "code": "def binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1",
        "language": "python",
        "difficulty": "medium",
    },
    {
        "instruction": "Write a Python function for bubble sort",
        "code": "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr",
        "language": "python",
        "difficulty": "easy",
    },
    {
        "instruction": "Write a Python function for quicksort",
        "code": "def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)",
        "language": "python",
        "difficulty": "medium",
    },
    {
        "instruction": "Write a Python function to find the longest common subsequence",
        "code": "def lcs(s1, s2):\n    m, n = len(s1), len(s2)\n    dp = [[0] * (n + 1) for _ in range(m + 1)]\n    for i in range(1, m + 1):\n        for j in range(1, n + 1):\n            if s1[i-1] == s2[j-1]:\n                dp[i][j] = dp[i-1][j-1] + 1\n            else:\n                dp[i][j] = max(dp[i-1][j], dp[i][j-1])\n    return dp[m][n]",
        "language": "python",
        "difficulty": "hard",
    },
    {
        "instruction": "Write a Python function for memoized fibonacci",
        "code": "def fibonacci(n, memo={}):\n    if n in memo:\n        return memo[n]\n    if n <= 1:\n        return n\n    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)\n    return memo[n]",
        "language": "python",
        "difficulty": "medium",
    },
    # String operations
    {
        "instruction": "Write a Python function to check if two strings are anagrams",
        "code": "def are_anagrams(s1, s2):\n    return sorted(s1.lower()) == sorted(s2.lower())",
        "language": "python",
        "difficulty": "easy",
    },
    {
        "instruction": "Write a Python function to find all anagrams in a list",
        "code": "def find_anagrams(words):\n    anagram_map = {}\n    for word in words:\n        key = tuple(sorted(word.lower()))\n        if key not in anagram_map:\n            anagram_map[key] = []\n        anagram_map[key].append(word)\n    return [group for group in anagram_map.values() if len(group) > 1]",
        "language": "python",
        "difficulty": "medium",
    },
    {
        "instruction": "Write a Python function to compress a string",
        "code": "def compress_string(s):\n    if not s:\n        return ''\n    result = []\n    count = 1\n    for i in range(1, len(s)):\n        if s[i] == s[i-1]:\n            count += 1\n        else:\n            result.append(s[i-1] + (str(count) if count > 1 else ''))\n            count = 1\n    result.append(s[-1] + (str(count) if count > 1 else ''))\n    compressed = ''.join(result)\n    return compressed if len(compressed) < len(s) else s",
        "language": "python",
        "difficulty": "medium",
    },
    # File operations
    {
        "instruction": "Write a Python function to read a file and count word frequency",
        "code": "def word_frequency(filepath):\n    freq = {}\n    with open(filepath, 'r') as f:\n        for line in f:\n            for word in line.split():\n                word = word.lower().strip('.,!?;:')\n                freq[word] = freq.get(word, 0) + 1\n    return sorted(freq.items(), key=lambda x: x[1], reverse=True)",
        "language": "python",
        "difficulty": "easy",
    },
    # Decorators and advanced
    {
        "instruction": "Write a Python decorator for timing function execution",
        "code": "import time\n\ndef timer(func):\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        result = func(*args, **kwargs)\n        elapsed = time.time() - start\n        print(f'{func.__name__} took {elapsed:.4f}s')\n        return result\n    return wrapper",
        "language": "python",
        "difficulty": "medium",
    },
    {
        "instruction": "Write a Python decorator for caching (memoization)",
        "code": "def memoize(func):\n    cache = {}\n    def wrapper(*args):\n        if args not in cache:\n            cache[args] = func(*args)\n        return cache[args]\n    return wrapper",
        "language": "python",
        "difficulty": "medium",
    },
    # Database
    {
        "instruction": "Write a Python function to create a SQLite table",
        "code": "import sqlite3\n\ndef create_table(db_path, table_name, columns):\n    conn = sqlite3.connect(db_path)\n    col_defs = ', '.join(f'{name} {dtype}' for name, dtype in columns.items())\n    conn.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({col_defs})')\n    conn.commit()\n    conn.close()",
        "language": "python",
        "difficulty": "easy",
    },
    # API
    {
        "instruction": "Write a Python function to make an HTTP GET request",
        "code": "import urllib.request\nimport json\n\ndef http_get(url, headers=None):\n    req = urllib.request.Request(url, headers=headers or {})\n    with urllib.request.urlopen(req, timeout=10) as resp:\n        return json.loads(resp.read().decode('utf-8'))",
        "language": "python",
        "difficulty": "easy",
    },
    # Testing
    {
        "instruction": "Write a Python unit test for a factorial function",
        "code": "import unittest\n\ndef factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\nclass TestFactorial(unittest.TestCase):\n    def test_base(self):\n        self.assertEqual(factorial(0), 1)\n        self.assertEqual(factorial(1), 1)\n    def test_positive(self):\n        self.assertEqual(factorial(5), 120)\n        self.assertEqual(factorial(10), 3628800)\n    def test_negative(self):\n        with self.assertRaises(RecursionError):\n            factorial(-1)\n\nif __name__ == '__main__':\n    unittest.main()",
        "language": "python",
        "difficulty": "medium",
    },
]

# ============================================================
# DEBUGGING PAIRS (error → fix)
# ============================================================

DEBUGGING_PAIRS = [
    {
        "error": "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
        "bad_code": "result = 5 + 'hello'",
        "fix": "result = 5 + int('hello')  # or result = str(5) + 'hello'",
        "explanation": "Cannot add int and str directly. Convert one to match the other.",
    },
    {
        "error": "IndexError: list index out of range",
        "bad_code": "lst = [1, 2, 3]\nprint(lst[5])",
        "fix": "lst = [1, 2, 3]\nif len(lst) > 5:\n    print(lst[5])\nelse:\n    print('Index out of range')",
        "explanation": "Check list length before accessing index.",
    },
    {
        "error": "ModuleNotFoundError: No module named 'requests'",
        "bad_code": "import requests",
        "fix": "import subprocess\nsubprocess.run(['pip', 'install', 'requests'])\nimport requests",
        "explanation": "Install missing module before importing.",
    },
    {
        "error": "SyntaxError: invalid syntax",
        "bad_code": "def greet(name)\n    print(f'Hello {name}')",
        "fix": "def greet(name):\n    print(f'Hello {name}')",
        "explanation": "Missing colon after function definition.",
    },
    {
        "error": "IndentationError: expected an indented block",
        "bad_code": "if True:\nprint('hello')",
        "fix": "if True:\n    print('hello')",
        "explanation": "Code inside if block must be indented.",
    },
    {
        "error": "KeyError: 'name'",
        "bad_code": "data = {'age': 25}\nprint(data['name'])",
        "fix": "data = {'age': 25}\nprint(data.get('name', 'Unknown'))",
        "explanation": "Use .get() with default value for safe dict access.",
    },
    {
        "error": "AttributeError: 'NoneType' object has no attribute 'split'",
        "bad_code": "result = None\nwords = result.split(' ')",
        "fix": "result = None\nif result:\n    words = result.split(' ')",
        "explanation": "Check for None before calling methods.",
    },
    {
        "error": "ZeroDivisionError: division by zero",
        "bad_code": "def divide(a, b):\n    return a / b",
        "fix": "def divide(a, b):\n    if b == 0:\n        raise ValueError('Cannot divide by zero')\n    return a / b",
        "explanation": "Check for zero divisor before dividing.",
    },
    {
        "error": "RecursionError: maximum recursion depth exceeded",
        "bad_code": "def factorial(n):\n    return n * factorial(n - 1)",
        "fix": "def factorial(n, memo={}):\n    if n in memo:\n        return memo[n]\n    if n <= 1:\n        return 1\n    memo[n] = n * factorial(n - 1, memo)\n    return memo[n]",
        "explanation": "Add base case and memoization to prevent infinite recursion.",
    },
    {
        "error": "FileNotFoundError: [Errno 2] No such file or directory",
        "bad_code": "with open('data.txt') as f:\n    content = f.read()",
        "fix": "import os\nif os.path.exists('data.txt'):\n    with open('data.txt') as f:\n        content = f.read()\nelse:\n    content = ''",
        "explanation": "Check if file exists before opening.",
    },
]


class CodingDataset:
    """Manages coding training data."""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir or 'data/datasets')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.coding_qa = CODING_QA
        self.debugging_pairs = DEBUGGING_PAIRS

    def get_training_pairs(self, category: str = "all", max_pairs: int = 500) -> list:
        """Get training pairs as (input, target) format.

        Args:
            category: 'qa', 'debug', or 'all'
            max_pairs: Maximum pairs to return

        Returns:
            List of {'input': str, 'target': str, 'type': str}
        """
        pairs = []

        if category in ('qa', 'all'):
            for item in self.coding_qa:
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
        for item in self.coding_qa:
            texts.append(item['instruction'])
            texts.append(item['code'])
        for item in self.debugging_pairs:
            texts.append(f"Fix: {item['error']}")
            texts.append(item['fix'])
            texts.append(item['explanation'])
        return texts

    def get_stats(self) -> dict:
        return {
            'coding_qa': len(self.coding_qa),
            'debugging_pairs': len(self.debugging_pairs),
            'total': len(self.coding_qa) + len(self.debugging_pairs),
        }
