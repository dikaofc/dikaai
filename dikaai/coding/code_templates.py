"""
DikaAI Code Templates - Pre-built code patterns for instant code generation.

Instead of relying solely on the tiny LSTM model, use template matching
for code tasks. The model can learn patterns from templates over time.
"""

import re


# ============================================================
# PYTHON CODE TEMPLATES
# ============================================================

PYTHON_TEMPLATES = {
    # Basic functions
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
        "pattern": r"class.*stack|stack.*class",
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
        "pattern": r"class.*queue|queue.*class",
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
    "binary_tree": {
        "pattern": r"binary.?tree|pohon.*biner",
        "code": """class TreeNode:
    def __init__(self, val=0):
        self.val = val
        self.left = None
        self.right = None

def insert(root, val):
    if not root:
        return TreeNode(val)
    if val < root.val:
        root.left = insert(root.left, val)
    else:
        root.right = insert(root.right, val)
    return root

def inorder(root):
    if not root:
        return []
    return inorder(root.left) + [root.val] + inorder(root.right)""",
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
}


def match_template(user_input: str) -> dict:
    """Match user input to a code template.

    Returns:
        dict with 'matched', 'template_name', 'code' or None
    """
    text = user_input.lower()

    for name, template in PYTHON_TEMPLATES.items():
        if re.search(template['pattern'], text):
            return {
                'matched': True,
                'template_name': name,
                'code': template['code'],
            }

    return {'matched': False}


def get_all_templates() -> dict:
    """Get all available templates."""
    return {name: t['code'] for name, t in PYTHON_TEMPLATES.items()}
