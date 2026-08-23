"""
DikaAI Needle-in-a-Haystack Benchmark - Test long-context retrieval.

Tests if DikaAI can find a specific piece of information
("needle") hidden in a large amount of text ("haystack").

Test sizes: 1K, 5K, 10K, 50K, 100K tokens
Needle positions: 10%, 25%, 50%, 75%, 90%
"""

import time
import random
import re
from dataclasses import dataclass


@dataclass
class NeedleHaystackResult:
    """Result of a single needle-in-haystack test."""
    context_size: int  # tokens
    needle_position: float  # 0.0-1.0
    found: bool
    response: str
    time_taken: float = 0.0


# The "needle" - a secret fact that must be retrieved
NEEDLE = "The secret code for DikaAI is DIKAAI-7291."

# Haystack filler - generic text to fill context
HAYSTACK_PARAGRAPHS = [
    "Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python is widely used in web development, data science, artificial intelligence, and automation.",
    "Machine learning is a subset of artificial intelligence that enables systems to learn from data. Common algorithms include linear regression, decision trees, random forests, and neural networks. Deep learning uses multi-layered neural networks to learn complex patterns.",
    "Web development involves building websites and web applications. Frontend technologies include HTML, CSS, and JavaScript. Backend technologies include Python, Node.js, and databases like PostgreSQL and MongoDB.",
    "Docker is a containerization platform that packages applications with their dependencies. Containers are lightweight, portable, and consistent across environments. Docker Compose manages multi-container applications.",
    "Git is a distributed version control system. It tracks changes in source code and enables collaboration. Common commands include clone, commit, push, pull, and branch. GitHub hosts Git repositories online.",
    "REST APIs use HTTP methods for communication. GET retrieves data, POST creates, PUT updates, and DELETE removes. Status codes indicate success (200) or errors (404, 500).",
    "Database design involves creating schemas, tables, and relationships. SQL databases use structured queries. NoSQL databases like MongoDB use flexible documents. Indexing improves query performance.",
    "Testing ensures code quality. Unit tests verify individual functions. Integration tests check component interactions. Test-driven development writes tests before code.",
    "Security best practices include input validation, parameterized queries, HTTPS, and authentication. OWASP lists common vulnerabilities like SQL injection and XSS.",
    "Linux is an open-source operating system. Common commands include ls, cd, grep, find, and chmod. Shell scripting automates tasks. Package managers install software.",
    "TypeScript adds static typing to JavaScript. It catches errors at compile time and improves code documentation. Interfaces define object shapes. Generics enable reusable components.",
    "React is a JavaScript library for building user interfaces. Components are reusable UI pieces. State management handles data flow. Hooks like useState and useEffect manage component lifecycle.",
    "Cloud computing provides on-demand resources. AWS, Azure, and GCP offer computing, storage, and networking services. Serverless functions run code without managing servers.",
    "Data structures organize information efficiently. Arrays provide fast access. Linked lists enable efficient insertion. Trees and graphs model hierarchical relationships.",
    "Algorithms solve problems step by step. Sorting algorithms arrange data. Search algorithms find elements. Dynamic programming optimizes recursive solutions.",
    "Networking connects computers. TCP/IP is the foundation protocol. HTTP runs on top of TCP. DNS translates domain names to IP addresses.",
    "DevOps bridges development and operations. CI/CD pipelines automate testing and deployment. Infrastructure as code manages servers programmatically.",
    "Mobile development creates apps for phones. Android uses Java/Kotlin. iOS uses Swift. Cross-platform frameworks include Flutter and React Native.",
    "Artificial intelligence simulates human intelligence. Natural language processing understands text. Computer vision interprets images. Robotics combines AI with physical systems.",
    "Blockchain is a distributed ledger technology. Cryptocurrencies use blockchain for transactions. Smart contracts execute automatically when conditions are met.",
    "Agile methodology promotes iterative development. Scrum organizes work in sprints. Kanban visualizes workflow. Daily standups coordinate team activities.",
    "Object-oriented programming uses classes and objects. Inheritance enables code reuse. Polymorphism allows flexible interfaces. Encapsulation hides internal details.",
    "Functional programming treats computation as mathematical functions. Pure functions have no side effects. Immutability prevents unintended changes. Higher-order functions take functions as arguments.",
    "APIs enable software communication. GraphQL provides flexible querying. gRPC offers high-performance RPC. WebSockets enable real-time bidirectional communication.",
    "Monitoring tracks system health. Metrics measure performance. Logs record events. Alerts notify of issues. Prometheus and Grafana are popular monitoring tools.",
]


def generate_haystack(target_tokens: int) -> str:
    """Generate haystack text of approximately target_tokens size."""
    paragraphs = []
    current_tokens = 0

    while current_tokens < target_tokens:
        para = random.choice(HAYSTACK_PARAGRAPHS)
        para_tokens = len(para.split())
        paragraphs.append(para)
        current_tokens += para_tokens

    return '\n\n'.join(paragraphs)


def insert_needle(haystack: str, needle: str, position: float) -> str:
    """Insert needle at a specific position in the haystack.

    Args:
        haystack: The background text
        needle: The secret information to hide
        position: Where to insert (0.0 = beginning, 1.0 = end)
    """
    paragraphs = haystack.split('\n\n')
    insert_idx = int(len(paragraphs) * position)
    insert_idx = max(0, min(insert_idx, len(paragraphs) - 1))

    paragraphs.insert(insert_idx, needle)
    return '\n\n'.join(paragraphs)


class NeedleHaystackBenchmark:
    """Run needle-in-a-haystack tests at various context sizes."""

    def __init__(self, engine=None):
        self.engine = engine

    @property
    def _engine(self):
        if self.engine is None:
            from dikaai.engine import Engine
            self.engine = Engine()
        return self.engine

    def run(self, sizes: list = None, positions: list = None) -> list:
        """Run needle-in-haystack tests.

        Args:
            sizes: List of context sizes in tokens [1000, 5000, 10000, 50000]
            positions: List of needle positions [0.1, 0.25, 0.5, 0.75, 0.9]

        Returns:
            List of NeedleHaystackResult
        """
        sizes = sizes or [1000, 5000, 10000, 50000]
        positions = positions or [0.1, 0.25, 0.5, 0.75, 0.9]
        results = []

        total = len(sizes) * len(positions)
        print(f"\n{'='*60}")
        print(f"  Needle-in-a-Haystack Benchmark")
        print(f"  {len(sizes)} sizes × {len(positions)} positions = {total} tests")
        print(f"{'='*60}\n")

        for size in sizes:
            for pos in positions:
                result = self._test_single(size, pos)
                results.append(result)

                status = "✅" if result.found else "❌"
                print(f"  {status} {size:>7,} tokens @ {pos:.0%} → {'FOUND' if result.found else 'MISSED'} ({result.time_taken:.1f}s)")

        print(f"\n{'='*60}")
        self._print_summary(results)
        print(f"{'='*60}\n")

        return results

    def _test_single(self, context_size: int, position: float) -> NeedleHaystackResult:
        """Run a single needle-in-haystack test."""
        start = time.time()

        # Generate haystack
        haystack = generate_haystack(context_size)

        # Insert needle
        text_with_needle = insert_needle(haystack, NEEDLE, position)

        # Ask the model
        query = f"Based on the following text, what is the secret code for DikaAI?\n\n{text_with_needle}\n\nWhat is the secret code?"

        try:
            result = self._engine.process(query)
            response = result.get('response', '')

            # Check if needle was found
            found = 'DIKAAI-7291' in response or 'dikaai-7291' in response.lower()

            return NeedleHaystackResult(
                context_size=context_size,
                needle_position=position,
                found=found,
                response=response,
                time_taken=time.time() - start,
            )
        except Exception as e:
            return NeedleHaystackResult(
                context_size=context_size,
                needle_position=position,
                found=False,
                response=f"Error: {e}",
                time_taken=time.time() - start,
            )

    def _print_summary(self, results: list):
        """Print summary of results."""
        total = len(results)
        found = sum(1 for r in results if r.found)

        print(f"\n  📊 Summary")
        print(f"  {'─'*40}")
        print(f"  Total tests : {total}")
        print(f"  Found       : {found}")
        print(f"  Missed      : {total - found}")
        print(f"  Accuracy    : {found/total*100:.1f}%")

        # Per-size breakdown
        print(f"\n  📏 By Context Size")
        print(f"  {'─'*40}")
        by_size = {}
        for r in results:
            if r.context_size not in by_size:
                by_size[r.context_size] = {'total': 0, 'found': 0}
            by_size[r.context_size]['total'] += 1
            if r.found:
                by_size[r.context_size]['found'] += 1

        for size in sorted(by_size.keys()):
            data = by_size[size]
            rate = data['found'] / data['total'] * 100
            bar = '█' * int(rate / 5) + '░' * (20 - int(rate / 5))
            print(f"  {size:>7,} tokens  {bar}  {rate:.0f}%")

        # Per-position breakdown
        print(f"\n  📍 By Needle Position")
        print(f"  {'─'*40}")
        by_pos = {}
        for r in results:
            pos_key = f"{r.needle_position:.0%}"
            if pos_key not in by_pos:
                by_pos[pos_key] = {'total': 0, 'found': 0}
            by_pos[pos_key]['total'] += 1
            if r.found:
                by_pos[pos_key]['found'] += 1

        for pos in sorted(by_pos.keys()):
            data = by_pos[pos]
            rate = data['found'] / data['total'] * 100
            bar = '█' * int(rate / 5) + '░' * (20 - int(rate / 5))
            print(f"  Position {pos:>4s}  {bar}  {rate:.0f}%")

        # Score
        if found / total >= 0.9:
            grade = 'A'
        elif found / total >= 0.7:
            grade = 'B'
        elif found / total >= 0.5:
            grade = 'C'
        elif found / total >= 0.3:
            grade = 'D'
        else:
            grade = 'F'

        print(f"\n  🏆 Long-Context Score: {found/total*100:.0f}% (Grade: {grade})")
