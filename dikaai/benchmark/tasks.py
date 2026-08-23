"""
DikaAI Benchmark Tasks - Coding challenges for evaluation.

Categories:
    python     - Python coding tasks
    javascript - JavaScript coding tasks
    debugging  - Find and fix bugs
    algorithms - Algorithm problems
    git        - Git operations
    tool_use   - Tool usage tasks
"""

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class BenchmarkTask:
    """A single benchmark task."""
    id: str
    category: str
    difficulty: str  # easy, medium, hard
    instruction: str
    test_code: str = ""
    expected_output: str = ""
    validate_fn: Optional[Callable] = None
    hints: list = field(default_factory=list)

    def evaluate(self, response: str, engine=None) -> dict:
        """Evaluate a response against this task."""
        result = {
            'task_id': self.id,
            'category': self.category,
            'difficulty': self.difficulty,
            'response': response,
            'passed': False,
            'metrics': {},
        }

        # 1. Check if response contains code
        has_code = ('```' in response or 'def ' in response or
                    'function ' in response or 'class ' in response or
                    'import ' in response)
        result['metrics']['has_code'] = has_code

        # 2. Check syntax (if Python)
        if self.category == 'python':
            code = self._extract_code(response)
            syntax_ok = self._check_python_syntax(code)
            result['metrics']['syntax_valid'] = syntax_ok
            if not syntax_ok:
                return result

        # 3. Run test code if provided
        if self.test_code:
            test_passed = self._run_test(response)
            result['metrics']['test_passed'] = test_passed
            result['passed'] = test_passed
        elif has_code:
            # If no test, consider it passed if it has valid code
            result['passed'] = True
            result['metrics']['test_passed'] = None
        else:
            # No code in response
            result['passed'] = False
            result['metrics']['test_passed'] = False

        # 4. Custom validation (takes priority over has_code check)
        if self.validate_fn:
            custom = self.validate_fn(response)
            result['metrics']['custom_validation'] = custom
            result['passed'] = custom  # validate_fn is the source of truth

        return result

    def _extract_code(self, response: str) -> str:
        """Extract code from response."""
        import re
        # Try markdown code blocks
        blocks = re.findall(r'```(?:python|py)?\n(.*?)```', response, re.DOTALL)
        if blocks:
            return blocks[0]
        # Try to find function definitions
        lines = response.split('\n')
        code_lines = []
        in_code = False
        for line in lines:
            if any(kw in line for kw in ['def ', 'import ', 'class ', 'function ', 'const ', 'let ', 'var ']):
                in_code = True
            if in_code:
                code_lines.append(line)
        return '\n'.join(code_lines) if code_lines else response

    def _check_python_syntax(self, code: str) -> bool:
        """Check if Python code has valid syntax."""
        if not code or not code.strip():
            return False
        try:
            compile(code, '<benchmark>', 'exec')
            return True
        except SyntaxError:
            return False

    def _run_test(self, response: str) -> bool:
        """Run test code against the response."""
        import subprocess
        import tempfile
        import os

        code = self._extract_code(response)
        if not code:
            return False

        full_code = code + '\n\n' + self.test_code

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            tmp = f.name

        try:
            result = subprocess.run(
                ['python', tmp],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return False
            if self.expected_output:
                return self.expected_output.strip() in result.stdout.strip()
            return True
        except Exception:
            return False
        finally:
            os.unlink(tmp)


# ============================================================
# TASK DEFINITIONS
# ============================================================

PYTHON_TASKS = [
    BenchmarkTask(
        id="py-001", category="python", difficulty="easy",
        instruction="Write a Python function `fibonacci(n)` that returns the nth Fibonacci number.",
        test_code="assert fibonacci(0) == 0\nassert fibonacci(1) == 1\nassert fibonacci(5) == 5\nassert fibonacci(10) == 55\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="py-002", category="python", difficulty="easy",
        instruction="Write a Python function `is_palindrome(s)` that checks if a string is a palindrome (case-insensitive).",
        test_code="assert is_palindrome('Racecar') == True\nassert is_palindrome('hello') == False\nassert is_palindrome('A man a plan a canal Panama'.replace(' ', '').lower()) == True\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="py-003", category="python", difficulty="easy",
        instruction="Write a Python function `count_vowels(s)` that counts the number of vowels in a string.",
        test_code="assert count_vowels('hello') == 2\nassert count_vowels('AEIOU') == 5\nassert count_vowels('bcdfg') == 0\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="py-004", category="python", difficulty="medium",
        instruction="Write a Python function `flatten(lst)` that flattens a nested list. Example: flatten([1, [2, 3], [4, [5]]]) should return [1, 2, 3, 4, 5].",
        test_code="assert flatten([1, [2, 3], [4, [5]]]) == [1, 2, 3, 4, 5]\nassert flatten([]) == []\nassert flatten([1, 2, 3]) == [1, 2, 3]\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="py-005", category="python", difficulty="medium",
        instruction="Write a Python function `merge_sort(arr)` that implements merge sort.",
        test_code="assert merge_sort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]\nassert merge_sort([]) == []\nassert merge_sort([1]) == [1]\nassert merge_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="py-006", category="python", difficulty="medium",
        instruction="Write a Python class `Stack` with methods `push(item)`, `pop()`, `peek()`, `is_empty()`, and `size()`.",
        test_code="s = Stack()\nassert s.is_empty() == True\ns.push(1)\ns.push(2)\nassert s.size() == 2\nassert s.peek() == 2\nassert s.pop() == 2\nassert s.pop() == 1\nassert s.is_empty() == True\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="py-007", category="python", difficulty="hard",
        instruction="Write a Python function `lcs(s1, s2)` that finds the length of the longest common subsequence of two strings.",
        test_code="assert lcs('abcde', 'ace') == 3\nassert lcs('abc', 'abc') == 3\nassert lcs('abc', 'def') == 0\nassert lcs('abcdef', 'acf') == 3\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="py-008", category="python", difficulty="hard",
        instruction="Write a Python function `binary_search(arr, target)` that returns the index of target in sorted array, or -1 if not found.",
        test_code="assert binary_search([1, 2, 3, 4, 5], 3) == 2\nassert binary_search([1, 2, 3, 4, 5], 6) == -1\nassert binary_search([], 1) == -1\nassert binary_search([1], 1) == 0\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="py-009", category="python", difficulty="easy",
        instruction="Write a Python function `factorial(n)` that returns the factorial of n.",
        test_code="assert factorial(0) == 1\nassert factorial(1) == 1\nassert factorial(5) == 120\nassert factorial(10) == 3628800\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="py-010", category="python", difficulty="medium",
        instruction="Write a Python function `bubble_sort(arr)` that sorts a list using bubble sort algorithm.",
        test_code="assert bubble_sort([3, 1, 4, 1, 5, 9]) == [1, 1, 3, 4, 5, 9]\nassert bubble_sort([]) == []\nassert bubble_sort([1]) == [1]\nprint('PASS')",
        expected_output="PASS",
    ),
]

DEBUG_TASKS = [
    BenchmarkTask(
        id="dbg-001", category="debugging", difficulty="easy",
        instruction="Fix this Python function that should return the sum of a list:\n```python\ndef sum_list(nums):\n    total = 0\n    for n in nums:\n        total == n  # Bug here\n    return total\n```",
        test_code="assert sum_list([1, 2, 3]) == 6\nassert sum_list([]) == 0\nassert sum_list([10, -5, 5]) == 10\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="dbg-002", category="debugging", difficulty="easy",
        instruction="Fix this function that checks if a number is even:\n```python\ndef is_even(n):\n    return n % 2 == 1  # Bug here\n```",
        test_code="assert is_even(2) == True\nassert is_even(3) == False\nassert is_even(0) == True\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="dbg-003", category="debugging", difficulty="medium",
        instruction="Fix this binary search that has an off-by-one error:\n```python\ndef binary_search(arr, target):\n    lo, hi = 0, len(arr)\n    while lo < hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            lo = mid  # Bug: should be mid + 1\n        else:\n            hi = mid\n    return -1\n```",
        test_code="assert binary_search([1, 2, 3, 4, 5], 3) == 2\nassert binary_search([1, 2, 3, 4, 5], 5) == 4\nassert binary_search([1, 2, 3, 4, 5], 1) == 0\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="dbg-004", category="debugging", difficulty="medium",
        instruction="Fix this function that reverses a string - it's missing the return statement:\n```python\ndef reverse_string(s):\n    result = ''\n    for c in s:\n        result = c + result\n    # Bug: missing return\n```",
        test_code="assert reverse_string('hello') == 'olleh'\nassert reverse_string('') == ''\nassert reverse_string('a') == 'a'\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="dbg-005", category="debugging", difficulty="hard",
        instruction="Fix this recursive Fibonacci function that has exponential time complexity - make it efficient:\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```",
        test_code="import time\nstart = time.time()\nresult = fibonacci(30)\nelapsed = time.time() - start\nassert result == 832040\nassert elapsed < 1.0, f'Too slow: {elapsed}s'\nprint('PASS')",
        expected_output="PASS",
    ),
]

ALGORITHM_TASKS = [
    BenchmarkTask(
        id="algo-001", category="algorithms", difficulty="easy",
        instruction="Write a function `two_sum(nums, target)` that returns indices of two numbers that add up to target.",
        test_code="result = two_sum([2, 7, 11, 15], 9)\nassert sorted(result) == [0, 1]\nresult = two_sum([3, 2, 4], 6)\nassert sorted(result) == [1, 2]\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="algo-002", category="algorithms", difficulty="medium",
        instruction="Write a function `valid_parentheses(s)` that checks if a string of brackets is valid.",
        test_code="assert valid_parentheses('()[]{}') == True\nassert valid_parentheses('(]') == False\nassert valid_parentheses('([)]') == False\nassert valid_parentheses('{[]}') == True\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="algo-003", category="algorithms", difficulty="medium",
        instruction="Write a function `max_subarray(nums)` that finds the contiguous subarray with the largest sum (Kadane's algorithm).",
        test_code="assert max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6\nassert max_subarray([1]) == 1\nassert max_subarray([5, 4, -1, 7, 8]) == 23\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="algo-004", category="algorithms", difficulty="hard",
        instruction="Write a function `edit_distance(s1, s2)` that computes the minimum edit distance between two strings.",
        test_code="assert edit_distance('kitten', 'sitting') == 3\nassert edit_distance('', '') == 0\nassert edit_distance('abc', 'abc') == 0\nassert edit_distance('abc', 'ac') == 1\nprint('PASS')",
        expected_output="PASS",
    ),
    BenchmarkTask(
        id="algo-005", category="algorithms", difficulty="hard",
        instruction="Write a function `knapsack(weights, values, capacity)` that solves the 0/1 knapsack problem.",
        test_code="assert knapsack([2, 3, 4, 5], [3, 4, 5, 6], 5) == 7\nassert knapsack([1, 1, 1], [1, 1, 1], 2) == 2\nassert knapsack([], [], 10) == 0\nprint('PASS')",
        expected_output="PASS",
    ),
]

GIT_TASKS = [
    BenchmarkTask(
        id="git-001", category="git", difficulty="easy",
        instruction="What command shows the current git status?",
        validate_fn=lambda r: any(w in r.lower() for w in ['git status', 'status']),
    ),
    BenchmarkTask(
        id="git-002", category="git", difficulty="easy",
        instruction="How do you create a new git branch called 'feature' and switch to it?",
        validate_fn=lambda r: any(w in r for w in ['git checkout -b feature', 'git switch -c feature', 'git branch feature']),
    ),
    BenchmarkTask(
        id="git-003", category="git", difficulty="medium",
        instruction="How do you undo the last commit but keep the changes in your working directory?",
        validate_fn=lambda r: 'git reset --soft HEAD~1' in r or 'git reset HEAD~1' in r or 'git reset --mixed HEAD~1' in r,
    ),
]

TOOL_USE_TASKS = [
    BenchmarkTask(
        id="tool-001", category="tool_use", difficulty="easy",
        instruction="Read the file config.py and tell me how many lines it has.",
        validate_fn=lambda r: any(w in r for w in ['lines', 'line', 'Line']),
    ),
    BenchmarkTask(
        id="tool-002", category="tool_use", difficulty="easy",
        instruction="Search for all Python files that contain 'class' keyword.",
        validate_fn=lambda r: any(w in r.lower() for w in ['found', 'match', 'result', '.py']),
    ),
    BenchmarkTask(
        id="tool-003", category="tool_use", difficulty="medium",
        instruction="Run 'python --version' and tell me the Python version.",
        validate_fn=lambda r: 'python' in r.lower() or '3.' in r,
    ),
]

# ============================================================
# JAVASCRIPT TASKS
# ============================================================

JS_TASKS = [
    BenchmarkTask(
        id="js-001", category="javascript", difficulty="easy",
        instruction="Write a JavaScript function `fibonacci(n)` that returns the nth Fibonacci number.",
        validate_fn=lambda r: any(kw in r for kw in ['function fibonacci', 'const fibonacci', 'fibonacci']),
    ),
    BenchmarkTask(
        id="js-002", category="javascript", difficulty="easy",
        instruction="Write a JavaScript function `reverseString(s)` that reverses a string.",
        validate_fn=lambda r: any(kw in r for kw in ['function reverseString', 'reverseString', 'split', 'reverse']),
    ),
    BenchmarkTask(
        id="js-003", category="javascript", difficulty="easy",
        instruction="Write a JavaScript function `isPalindrome(s)` to check if a string is a palindrome.",
        validate_fn=lambda r: any(kw in r for kw in ['function isPalindrome', 'isPalindrome', 'toLowerCase']),
    ),
    BenchmarkTask(
        id="js-004", category="javascript", difficulty="medium",
        instruction="Write a JavaScript function `binarySearch(arr, target)` that performs binary search.",
        validate_fn=lambda r: any(kw in r for kw in ['function binarySearch', 'binarySearch', 'Math.floor']),
    ),
    BenchmarkTask(
        id="js-005", category="javascript", difficulty="medium",
        instruction="Write a JavaScript function `twoSum(nums, target)` that finds two numbers adding to target.",
        validate_fn=lambda r: any(kw in r for kw in ['function twoSum', 'twoSum', 'seen']),
    ),
    BenchmarkTask(
        id="js-006", category="javascript", difficulty="medium",
        instruction="Write a JavaScript `debounce(fn, delay)` function.",
        validate_fn=lambda r: any(kw in r for kw in ['function debounce', 'debounce', 'setTimeout', 'clearTimeout']),
    ),
    BenchmarkTask(
        id="js-007", category="javascript", difficulty="medium",
        instruction="Write a JavaScript `memoize(fn)` function for caching results.",
        validate_fn=lambda r: any(kw in r for kw in ['function memoize', 'memoize', 'Map', 'cache']),
    ),
    BenchmarkTask(
        id="js-008", category="javascript", difficulty="medium",
        instruction="Write a JavaScript `validParentheses(s)` function.",
        validate_fn=lambda r: any(kw in r for kw in ['function validParentheses', 'validParentheses', 'stack']),
    ),
    BenchmarkTask(
        id="js-009", category="javascript", difficulty="medium",
        instruction="Write a JavaScript `deepClone(obj)` function.",
        validate_fn=lambda r: any(kw in r for kw in ['function deepClone', 'deepClone', 'typeof', 'Array.isArray']),
    ),
    BenchmarkTask(
        id="js-010", category="javascript", difficulty="medium",
        instruction="Write a JavaScript `flatten(arr)` function to flatten nested arrays.",
        validate_fn=lambda r: any(kw in r for kw in ['function flatten', 'flatten', 'reduce', 'Array.isArray']),
    ),
    # Advanced JS tasks
    BenchmarkTask(
        id="js-011", category="javascript", difficulty="medium",
        instruction="Write a JavaScript `throttle(fn, limit)` function that limits function calls.",
        validate_fn=lambda r: any(kw in r for kw in ['function throttle', 'throttle', 'Date.now', 'lastCall']),
    ),
    BenchmarkTask(
        id="js-012", category="javascript", difficulty="medium",
        instruction="Write a JavaScript `curry(fn)` function that curries a function.",
        validate_fn=lambda r: any(kw in r for kw in ['function curry', 'curry', 'length']),
    ),
    BenchmarkTask(
        id="js-013", category="javascript", difficulty="hard",
        instruction="Write a JavaScript `mergeSort(arr)` function using merge sort algorithm.",
        validate_fn=lambda r: any(kw in r for kw in ['function mergeSort', 'mergeSort', 'merge', 'slice']),
    ),
    BenchmarkTask(
        id="js-014", category="javascript", difficulty="hard",
        instruction="Write a JavaScript `lru_cache(capacity)` class with get and put methods.",
        validate_fn=lambda r: any(kw in r for kw in ['class', 'LRU', 'get', 'put', 'Map', 'capacity']),
    ),
    BenchmarkTask(
        id="js-015", category="javascript", difficulty="medium",
        instruction="Write a JavaScript `groupBy(arr, keyFn)` function that groups array elements.",
        validate_fn=lambda r: any(kw in r for kw in ['function groupBy', 'groupBy', 'reduce']),
    ),
    BenchmarkTask(
        id="js-016", category="javascript", difficulty="hard",
        instruction="Write a JavaScript async `retry(fn, retries, delay)` function with exponential backoff.",
        validate_fn=lambda r: any(kw in r for kw in ['function retry', 'retry', 'async', 'await', 'delay']),
    ),
    BenchmarkTask(
        id="js-017", category="javascript", difficulty="medium",
        instruction="Write a JavaScript `pipe(...fns)` function that composes functions left to right.",
        validate_fn=lambda r: any(kw in r for kw in ['function pipe', 'pipe', 'reduce', 'acc']),
    ),
    BenchmarkTask(
        id="js-018", category="javascript", difficulty="hard",
        instruction="Write a JavaScript `EventEmitter` class with on, emit, and off methods.",
        validate_fn=lambda r: any(kw in r for kw in ['class EventEmitter', 'EventEmitter', 'on', 'emit', 'off']),
    ),
    BenchmarkTask(
        id="js-019", category="javascript", difficulty="medium",
        instruction="Write a JavaScript `chunk(arr, size)` function that splits array into chunks.",
        validate_fn=lambda r: any(kw in r for kw in ['function chunk', 'chunk', 'slice']),
    ),
    BenchmarkTask(
        id="js-020", category="javascript", difficulty="hard",
        instruction="Write a JavaScript `debouncedFn` with cancel and flush methods.",
        validate_fn=lambda r: any(kw in r for kw in ['cancel', 'flush', 'debounce', 'timeout']),
    ),
]

# ============================================================
# RUST TASKS
# ============================================================

RUST_TASKS = [
    BenchmarkTask(
        id="rs-001", category="rust", difficulty="easy",
        instruction="Write a Rust function `fibonacci(n: u32) -> u64`.",
        validate_fn=lambda r: 'fn fibonacci' in r or 'fibonacci' in r,
    ),
    BenchmarkTask(
        id="rs-002", category="rust", difficulty="easy",
        instruction="Write a Rust struct `Point` with `new()` and `distance()` methods.",
        validate_fn=lambda r: 'struct Point' in r and ('fn new' in r or 'fn distance' in r),
    ),
    BenchmarkTask(
        id="rs-003", category="rust", difficulty="medium",
        instruction="Write a Rust `trait Drawable` with `draw()` and `area()` methods, and implement it for a `Circle` struct.",
        validate_fn=lambda r: 'trait Drawable' in r and 'impl Drawable for' in r,
    ),
    BenchmarkTask(
        id="rs-004", category="rust", difficulty="medium",
        instruction="Write a Rust `binary_search` function that returns `Option<usize>`.",
        validate_fn=lambda r: 'fn binary_search' in r and 'Option' in r,
    ),
    BenchmarkTask(
        id="rs-005", category="rust", difficulty="medium",
        instruction="Write a Rust function `divide(a: f64, b: f64) -> Result<f64, String>`.",
        validate_fn=lambda r: 'fn divide' in r and 'Result' in r,
    ),
    BenchmarkTask(
        id="rs-006", category="rust", difficulty="medium",
        instruction="Write Rust code using `HashMap` to count word occurrences.",
        validate_fn=lambda r: 'HashMap' in r and ('word_count' in r or 'entry' in r),
    ),
    BenchmarkTask(
        id="rs-007", category="rust", difficulty="medium",
        instruction="Write a Rust `enum TrafficLight` with a `wait_time()` method using `match`.",
        validate_fn=lambda r: 'enum TrafficLight' in r and 'match' in r,
    ),
    BenchmarkTask(
        id="rs-008", category="rust", difficulty="easy",
        instruction="Write Rust code to filter even numbers and square them using iterator chain.",
        validate_fn=lambda r: '.iter()' in r and ('filter' in r or 'map' in r),
    ),
    # Advanced Rust tasks
    BenchmarkTask(
        id="rs-009", category="rust", difficulty="hard",
        instruction="Write a Rust `sort_vec(vec: &mut Vec<i32>)` function using quicksort with mutable references.",
        validate_fn=lambda r: 'fn sort_vec' in r and ('&mut' in r or 'mut' in r),
    ),
    BenchmarkTask(
        id="rs-010", category="rust", difficulty="hard",
        instruction="Write a Rust generic `max_value<T: PartialOrd>(a: T, b: T) -> T` function.",
        validate_fn=lambda r: 'fn max_value' in r and ('PartialOrd' in r or 'Ord' in r),
    ),
    BenchmarkTask(
        id="rs-011", category="rust", difficulty="medium",
        instruction="Write a Rust `impl Drop` for a custom `Database` struct that prints on drop.",
        validate_fn=lambda r: 'impl Drop' in r and 'fn drop' in r,
    ),
    BenchmarkTask(
        id="rs-012", category="rust", difficulty="medium",
        instruction="Write a Rust function using `Option` and `map`/`and_then` chaining.",
        validate_fn=lambda r: 'Option' in r and ('map' in r or 'and_then' in r),
    ),
    BenchmarkTask(
        id="rs-013", category="rust", difficulty="hard",
        instruction="Write a Rust `thread::spawn` example that creates a thread and joins it.",
        validate_fn=lambda r: 'thread::spawn' in r and ('join' in r or 'handle' in r),
    ),
    BenchmarkTask(
        id="rs-014", category="rust", difficulty="medium",
        instruction="Write a Rust `impl Display` for a `Point` struct.",
        validate_fn=lambda r: 'impl fmt::Display' in r or ('impl Display' in r and 'fn fmt' in r),
    ),
    BenchmarkTask(
        id="rs-015", category="rust", difficulty="hard",
        instruction="Write Rust code using `Vec::iter().enumerate()` to find index of max element.",
        validate_fn=lambda r: 'enumerate' in r and ('max_by' in r or 'max()' in r or 'iter()' in r),
    ),
]

# ============================================================
# C++ TASKS
# ============================================================

CPP_TASKS = [
    BenchmarkTask(
        id="cpp-001", category="cpp", difficulty="easy",
        instruction="Write a C++ function `long long fibonacci(int n)` that returns the nth Fibonacci number.",
        validate_fn=lambda r: any(kw in r for kw in ['fibonacci', 'long long']),
    ),
    BenchmarkTask(
        id="cpp-002", category="cpp", difficulty="easy",
        instruction="Write a C++ class `Point` with constructor and `distanceTo` method.",
        validate_fn=lambda r: 'class Point' in r and ('distanceTo' in r or 'distance'),
    ),
    BenchmarkTask(
        id="cpp-003", category="cpp", difficulty="medium",
        instruction="Write a C++ template function `findMax`.",
        validate_fn=lambda r: 'template' in r and 'findMax' in r,
    ),
    BenchmarkTask(
        id="cpp-004", category="cpp", difficulty="medium",
        instruction="Write C++ code using `std::sort` with a lambda comparator.",
        validate_fn=lambda r: 'sort' in r and ('lambda' in r or '[]' in r),
    ),
    BenchmarkTask(
        id="cpp-005", category="cpp", difficulty="medium",
        instruction="Write C++ smart pointer usage with `make_unique` and `make_shared`.",
        validate_fn=lambda r: 'make_unique' in r or 'make_shared' in r or 'unique_ptr' in r,
    ),
    # Advanced C++ tasks
    BenchmarkTask(
        id="cpp-006", category="cpp", difficulty="hard",
        instruction="Write C++ `std::vector` usage with `push_back`, `erase`, and `std::find`.",
        validate_fn=lambda r: 'vector' in r and ('push_back' in r or 'erase' in r or 'find' in r),
    ),
    BenchmarkTask(
        id="cpp-007", category="cpp", difficulty="medium",
        instruction="Write C++ `std::map` usage to count word occurrences.",
        validate_fn=lambda r: 'map' in r and ('count' in r or 'insert' in r or 'operator[]' in r),
    ),
    BenchmarkTask(
        id="cpp-008", category="cpp", difficulty="hard",
        instruction="Write C++ RAII pattern with a `FileGuard` class that opens and closes a file.",
        validate_fn=lambda r: 'class FileGuard' in r and ('open' in r or 'close' in r or '~FileGuard' in r),
    ),
    BenchmarkTask(
        id="cpp-009", category="cpp", difficulty="medium",
        instruction="Write C++ `std::unique_ptr` with a custom deleter.",
        validate_fn=lambda r: 'unique_ptr' in r and ('deleter' in r or 'delete' in r or 'lambda' in r),
    ),
    BenchmarkTask(
        id="cpp-010", category="cpp", difficulty="hard",
        instruction="Write C++ move constructor and move assignment operator for a `Buffer` class.",
        validate_fn=lambda r: 'Buffer' in r and ('move' in r or '&&' in r or 'noexcept' in r),
    ),
]

# ============================================================
# GO TASKS
# ============================================================

GO_TASKS = [
    BenchmarkTask(
        id="go-001", category="go", difficulty="easy",
        instruction="Write a Go function `fibonacci(n int) int`.",
        validate_fn=lambda r: 'func fibonacci' in r,
    ),
    BenchmarkTask(
        id="go-002", category="go", difficulty="easy",
        instruction="Write a Go struct `Person` with a `Greet()` method.",
        validate_fn=lambda r: 'type Person struct' in r and 'func (p' in r,
    ),
    BenchmarkTask(
        id="go-003", category="go", difficulty="medium",
        instruction="Write a Go interface `Shape` with `Area()` and implement it for `Circle`.",
        validate_fn=lambda r: 'type Shape interface' in r and 'func (c' in r,
    ),
    BenchmarkTask(
        id="go-004", category="go", difficulty="medium",
        instruction="Write a Go goroutine worker function.",
        validate_fn=lambda r: 'func worker' in r and ('<-chan' in r or 'chan' in r),
    ),
    BenchmarkTask(
        id="go-005", category="go", difficulty="medium",
        instruction="Write a Go HTTP handler with JSON response.",
        validate_fn=lambda r: 'http.HandleFunc' in r or 'json.NewEncoder' in r or 'func' in r,
    ),
    # Advanced Go tasks
    BenchmarkTask(
        id="go-006", category="go", difficulty="hard",
        instruction="Write a Go function using `select` with multiple channels.",
        validate_fn=lambda r: 'select' in r and ('case' in r or 'chan' in r),
    ),
    BenchmarkTask(
        id="go-007", category="go", difficulty="medium",
        instruction="Write a Go function that returns an error with `fmt.Errorf`.",
        validate_fn=lambda r: 'error' in r and ('fmt.Errorf' in r or 'return nil' in r),
    ),
    BenchmarkTask(
        id="go-008", category="go", difficulty="hard",
        instruction="Write a Go `sync.Mutex` example to protect shared state.",
        validate_fn=lambda r: 'Mutex' in r and ('Lock' in r or 'Unlock' in r),
    ),
    BenchmarkTask(
        id="go-009", category="go", difficulty="medium",
        instruction="Write a Go function using `defer` to close a file.",
        validate_fn=lambda r: 'defer' in r and ('Close' in r or 'close' in r),
    ),
    BenchmarkTask(
        id="go-010", category="go", difficulty="hard",
        instruction="Write a Go function using `context.Context` with timeout.",
        validate_fn=lambda r: 'context' in r and ('WithTimeout' in r or 'WithCancel' in r or 'Done()' in r),
    ),
]

# ============================================================
# ALL TASKS
# ============================================================

ALL_TASKS = (PYTHON_TASKS + JS_TASKS + RUST_TASKS + CPP_TASKS + GO_TASKS +
             DEBUG_TASKS + ALGORITHM_TASKS + GIT_TASKS + TOOL_USE_TASKS)


def get_tasks(category: str = None, difficulty: str = None) -> list:
    """Get benchmark tasks filtered by category/difficulty."""
    tasks = ALL_TASKS
    if category:
        tasks = [t for t in tasks if t.category == category]
    if difficulty:
        tasks = [t for t in tasks if t.difficulty == difficulty]
    return tasks


def get_categories() -> dict:
    """Get task counts per category."""
    cats = {}
    for t in ALL_TASKS:
        cats[t.category] = cats.get(t.category, 0) + 1
    return cats
