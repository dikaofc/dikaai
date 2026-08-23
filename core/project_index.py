"""DikaAI Project Index - Understands repository structure.

Index: files, symbols, functions, classes, imports, dependencies, configs.
"""

import os
import re
from pathlib import Path
from collections import defaultdict


class ProjectIndex:
    """Indexes a project for intelligent code navigation."""

    def __init__(self, root: str = None):
        self.root = Path(root) if root else Path.cwd()
        self.files = {}
        self.symbols = defaultdict(list)  # name -> [{file, line, type}]
        self.dependencies = defaultdict(set)  # file -> {imports}
        self.configs = []
        self.tests = []
        self.architecture = {}
        self.indexed = False

    def index(self, max_files: int = 500) -> dict:
        """Index entire project."""
        count = 0
        for file_path in self._scan_files():
            if count >= max_files:
                break
            try:
                self._index_file(file_path)
                count += 1
            except Exception:
                pass

        # Detect architecture
        self._detect_architecture()
        self.indexed = True

        return {
            'files': len(self.files),
            'symbols': len(self.symbols),
            'configs': len(self.configs),
            'tests': len(self.tests),
        }

    def _scan_files(self):
        """Scan for indexable files."""
        skip_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv',
                     'build', 'dist', '.idea', '.vscode', 'data', 'model_checkpoints'}

        extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs',
                      '.java', '.kt', '.sh', '.c', '.cpp', '.h', '.sql',
                      '.json', '.yaml', '.yml', '.toml', '.md', '.txt'}

        config_names = {'package.json', 'requirements.txt', 'Cargo.toml',
                       'go.mod', 'pom.xml', 'build.gradle', '.env',
                       'config.py', 'config.js', 'config.ts', 'settings.py',
                       'vercel.json', 'docker-compose.yml', 'Dockerfile',
                       '.gitignore', 'Makefile', 'CMakeLists.txt'}

        for root, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                fpath = Path(root) / fname
                if fname in config_names:
                    self.configs.append(str(fpath.relative_to(self.root)))
                elif fpath.suffix in extensions:
                    yield fpath

    def _index_file(self, file_path: Path):
        """Index a single file."""
        rel = str(file_path.relative_to(self.root))
        try:
            content = file_path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            return

        lines = content.split('\n')
        ext = file_path.suffix

        # Store file info
        self.files[rel] = {
            'path': rel,
            'extension': ext,
            'size': len(content),
            'lines': len(lines),
        }

        # Detect test files
        if 'test' in file_path.name.lower() or file_path.name.startswith('test_'):
            self.tests.append(rel)

        # Extract symbols based on language
        if ext == '.py':
            self._index_python(rel, lines)
        elif ext in ('.js', '.ts', '.jsx', '.tsx'):
            self._index_javascript(rel, lines)
        elif ext == '.go':
            self._index_go(rel, lines)

        # Extract imports
        self._extract_imports(rel, lines)

    def _index_python(self, file: str, lines: list):
        """Index Python symbols."""
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Functions
            match = re.match(r'def\s+(\w+)\s*\(', stripped)
            if match:
                self.symbols[match.group(1)].append({
                    'file': file, 'line': i + 1, 'type': 'function'
                })
            # Classes
            match = re.match(r'class\s+(\w+)', stripped)
            if match:
                self.symbols[match.group(1)].append({
                    'file': file, 'line': i + 1, 'type': 'class'
                })
            # Methods (inside class)
            match = re.match(r'\s+def\s+(\w+)\s*\(', line)
            if match and not match.group(1).startswith('_'):
                self.symbols[match.group(1)].append({
                    'file': file, 'line': i + 1, 'type': 'method'
                })

    def _index_javascript(self, file: str, lines: list):
        """Index JavaScript/TypeScript symbols."""
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Functions
            match = re.search(r'(?:function|const|let|var)\s+(\w+)\s*(?:=\s*(?:async\s*)?\(|=\s*function)', stripped)
            if match:
                self.symbols[match.group(1)].append({
                    'file': file, 'line': i + 1, 'type': 'function'
                })
            # Classes
            match = re.match(r'class\s+(\w+)', stripped)
            if match:
                self.symbols[match.group(1)].append({
                    'file': file, 'line': i + 1, 'type': 'class'
                })

    def _index_go(self, file: str, lines: list):
        """Index Go symbols."""
        for i, line in enumerate(lines):
            stripped = line.strip()
            match = re.match(r'func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(', stripped)
            if match:
                self.symbols[match.group(1)].append({
                    'file': file, 'line': i + 1, 'type': 'function'
                })

    def _extract_imports(self, file: str, lines: list):
        """Extract import statements."""
        imports = set()
        for line in lines:
            stripped = line.strip()
            # Python imports
            match = re.match(r'(?:from|import)\s+([\w.]+)', stripped)
            if match:
                imports.add(match.group(1))
            # JS imports
            match = re.match(r"import\s+.*from\s+['\"]([^'\"]+)['\"]", stripped)
            if match:
                imports.add(match.group(1))
            # Go imports
            match = re.match(r'"([^"]+)"', stripped)
            if match:
                imports.add(match.group(1))

        if imports:
            self.dependencies[file] = imports

    def _detect_architecture(self):
        """Detect project architecture pattern."""
        arch = {
            'type': 'unknown',
            'language': '',
            'framework': '',
            'structure': [],
        }

        # Detect main language
        ext_counts = defaultdict(int)
        for f in self.files:
            ext = self.files[f]['extension']
            ext_counts[ext] += 1

        if ext_counts:
            main_ext = max(ext_counts, key=ext_counts.get)
            lang_map = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                       '.go': 'go', '.rs': 'rust', '.java': 'java', '.kt': 'kotlin'}
            arch['language'] = lang_map.get(main_ext, main_ext)

        # Detect framework
        config_content = ' '.join(self.configs)
        if 'requirements.txt' in self.configs:
            try:
                req = (self.root / 'requirements.txt').read_text()
                if 'django' in req: arch['framework'] = 'django'
                elif 'flask' in req: arch['framework'] = 'flask'
                elif 'fastapi' in req: arch['framework'] = 'fastapi'
            except Exception:
                pass
        if 'package.json' in self.configs:
            try:
                pkg = (self.root / 'package.json').read_text()
                if 'react' in pkg: arch['framework'] = 'react'
                elif 'next' in pkg: arch['framework'] = 'nextjs'
                elif 'vue' in pkg: arch['framework'] = 'vue'
            except Exception:
                pass

        # Detect pattern
        dir_names = set()
        for f in self.files:
            parts = Path(f).parts
            if len(parts) > 1:
                dir_names.add(parts[0])

        if 'src' in dir_names and 'tests' in dir_names:
            arch['type'] = 'src-tests'
        elif 'api' in dir_names:
            arch['type'] = 'api'
        elif 'app' in dir_names:
            arch['type'] = 'app'

        self.architecture = arch

    def find_file(self, name: str) -> list:
        """Find files by name (partial match)."""
        results = []
        name_lower = name.lower()
        for f in self.files:
            if name_lower in f.lower():
                results.append(f)
        return results

    def find_symbol(self, name: str) -> list:
        """Find symbol by name."""
        return self.symbols.get(name, [])

    def get_context(self, query: str = "") -> str:
        """Get project context as string."""
        lines = ["PROJECT INDEX:"]

        if self.architecture:
            lines.append(f"  Type: {self.architecture.get('type', 'unknown')}")
            lines.append(f"  Language: {self.architecture.get('language', 'unknown')}")
            lines.append(f"  Framework: {self.architecture.get('framework', 'none')}")

        lines.append(f"  Files: {len(self.files)}")
        lines.append(f"  Symbols: {len(self.symbols)}")
        lines.append(f"  Configs: {len(self.configs)}")
        lines.append(f"  Tests: {len(self.tests)}")

        if self.configs:
            lines.append(f"\n  Configs: {', '.join(self.configs[:10])}")

        if self.tests:
            lines.append(f"  Tests: {', '.join(self.tests[:10])}")

        return '\n'.join(lines)

    def get_file_tree(self, max_depth: int = 3) -> str:
        """Get file tree."""
        lines = []
        for root, dirs, files in os.walk(self.root):
            depth = root.replace(str(self.root), '').count(os.sep)
            if depth >= max_depth:
                continue
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            indent = '  ' * depth
            lines.append(f"{indent}{os.path.basename(root)}/")
            for f in sorted(files)[:10]:
                lines.append(f"{indent}  {f}")
        return '\n'.join(lines)
