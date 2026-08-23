"""DikaAI v2 Configuration"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MEMORY_DIR = DATA_DIR / "memory"
CODEX_DIR = DATA_DIR / "codex"
BENCHMARK_DIR = DATA_DIR / "benchmarks"

# Create dirs
for d in [DATA_DIR, MEMORY_DIR, CODEX_DIR, BENCHMARK_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Model routing thresholds
ROUTER = {
    'chat_max_tokens': 256,
    'code_max_tokens': 512,
    'reason_max_tokens': 1024,
    'temperature_chat': 0.7,
    'temperature_code': 0.3,
    'temperature_reason': 0.5,
}

# Agent settings
AGENT = {
    'max_retries': 5,
    'max_file_size': 1_000_000,  # 1MB
    'allowed_extensions': ['.py', '.js', '.ts', '.jsx', '.tsx', '.java',
                           '.kt', '.go', '.rs', '.c', '.cpp', '.h',
                           '.sh', '.bash', '.sql', '.json', '.yaml',
                           '.yml', '.toml', '.md', '.txt', '.html', '.css'],
    'blocked_commands': ['rm -rf /', 'mkfs', 'dd if=', ':(){ :|:& };:'],
    'timeout_seconds': 30,
}

# Tool settings
TOOLS = {
    'search_max_results': 20,
    'file_read_max_lines': 2000,
    'git_diff_max_lines': 500,
}

# RAG settings
RAG = {
    'chunk_size': 500,
    'chunk_overlap': 50,
    'embedding_dim': 128,
    'top_k': 5,
    'similarity_threshold': 0.3,
}

# Coding memory settings
MEMORY = {
    'short_term_limit': 20,      # Last N messages
    'long_term_limit': 1000,     # Max experiences
    'coding_memory_limit': 500,  # Max coding patterns
    'experience_threshold': 0.7, # Min confidence to save
}

# Supported languages for coding agent
LANGUAGES = {
    'python': {'ext': '.py', 'run': 'python {file}', 'test': 'python -m pytest {file} -v'},
    'javascript': {'ext': '.js', 'run': 'node {file}', 'test': 'npm test'},
    'typescript': {'ext': '.ts', 'run': 'npx ts-node {file}', 'test': 'npx jest'},
    'go': {'ext': '.go', 'run': 'go run {file}', 'test': 'go test ./...'},
    'rust': {'ext': '.rs', 'run': 'cargo run', 'test': 'cargo test'},
    'java': {'ext': '.java', 'run': 'javac {file} && java {class}', 'test': 'mvn test'},
    'kotlin': {'ext': '.kt', 'run': 'kotlinc {file} -include-runtime -d {file}.jar && java -jar {file}.jar', 'test': 'gradle test'},
    'shell': {'ext': '.sh', 'run': 'bash {file}', 'test': None},
    'c': {'ext': '.c', 'run': 'gcc {file} -o {file}.out && ./{file}.out', 'test': None},
    'cpp': {'ext': '.cpp', 'run': 'g++ {file} -o {file}.out && ./{file}.out', 'test': None},
}

# Benchmark categories
BENCHMARKS = {
    'python': 100, 'javascript': 100, 'go': 50,
    'rust': 50, 'java': 50, 'kotlin': 50,
    'shell': 100, 'debugging': 100, 'algorithms': 100,
    'git': 100,
}
