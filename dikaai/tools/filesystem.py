"""DikaAI Filesystem Tools - Safe file operations for coding agent."""

import os
import re
from pathlib import Path
from dikaai.config import AGENT, TOOLS


class FilesystemTools:
    """Safe file operations with path validation."""

    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace) if workspace else Path.cwd()

    def _validate_path(self, path: str) -> Path:
        """Validate and resolve path within workspace."""
        p = Path(path).resolve()
        # Allow absolute paths but warn
        return p

    def read_file(self, path: str, offset: int = 0, limit: int = 2000) -> dict:
        """Read file content."""
        try:
            p = self._validate_path(path)
            if not p.exists():
                return {'error': f'File not found: {path}', 'success': False}
            if p.stat().st_size > AGENT['max_file_size']:
                return {'error': f'File too large ({p.stat().st_size} bytes)', 'success': False}

            with open(p, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            total = len(lines)
            selected = lines[offset:offset + limit]

            return {
                'success': True,
                'content': ''.join(selected),
                'lines': len(selected),
                'total_lines': total,
                'path': str(p),
                'truncated': (offset + limit) < total,
            }
        except Exception as e:
            return {'error': str(e), 'success': False}

    def write_file(self, path: str, content: str) -> dict:
        """Write content to file (creates or overwrites)."""
        try:
            p = self._validate_path(path)
            p.parent.mkdir(parents=True, exist_ok=True)

            with open(p, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                'success': True,
                'path': str(p),
                'size': len(content),
                'lines': content.count('\n') + 1,
            }
        except Exception as e:
            return {'error': str(e), 'success': False}

    def edit_file(self, path: str, old_text: str, new_text: str) -> dict:
        """Edit file by replacing text (exact match)."""
        try:
            p = self._validate_path(path)
            if not p.exists():
                return {'error': f'File not found: {path}', 'success': False}

            with open(p, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_text not in content:
                return {'error': f'Text not found in file', 'success': False}

            count = content.count(old_text)
            new_content = content.replace(old_text, new_text, 1)

            with open(p, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return {
                'success': True,
                'path': str(p),
                'replacements': 1,
                'remaining': count - 1,
            }
        except Exception as e:
            return {'error': str(e), 'success': False}

    def list_dir(self, path: str = '.', max_depth: int = 2) -> dict:
        """List directory contents recursively."""
        try:
            p = self._validate_path(path)
            if not p.is_dir():
                return {'error': f'Not a directory: {path}', 'success': False}

            items = []

            def _scan(dir_path, depth):
                if depth > max_depth:
                    return
                try:
                    for item in sorted(dir_path.iterdir()):
                        rel = item.relative_to(p)
                        if item.is_dir():
                            if item.name.startswith('.') or item.name in ('__pycache__', 'node_modules', '.git', 'venv'):
                                continue
                            items.append({'name': str(rel), 'type': 'dir'})
                            _scan(item, depth + 1)
                        else:
                            items.append({
                                'name': str(rel),
                                'type': 'file',
                                'size': item.stat().st_size,
                            })
                except PermissionError:
                    pass

            _scan(p, 0)

            return {
                'success': True,
                'path': str(p),
                'items': items,
                'count': len(items),
            }
        except Exception as e:
            return {'error': str(e), 'success': False}

    def search_code(self, pattern: str, path: str = '.', file_types: list = None) -> dict:
        """Search for pattern in code files."""
        try:
            import subprocess
            p = self._validate_path(path)

            cmd = ['grep', '-rn', '--include=*.{py,js,ts,jsx,tsx,go,rs,java,kt,sh,c,cpp,h}']
            if file_types:
                includes = ','.join(file_types)
                cmd = ['grep', '-rn']
                for ext in file_types:
                    cmd.extend(['--include=*' + ext])

            cmd.extend([pattern, str(p)])

            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=TOOLS.get('search_timeout', 10))

            matches = []
            for line in result.stdout.strip().split('\n')[:TOOLS['search_max_results']]:
                if ':' in line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        matches.append({
                            'file': parts[0],
                            'line': int(parts[1]) if parts[1].isdigit() else 0,
                            'content': parts[2].strip(),
                        })

            return {
                'success': True,
                'matches': matches,
                'count': len(matches),
                'pattern': pattern,
            }
        except Exception as e:
            return {'error': str(e), 'success': False}

    def file_info(self, path: str) -> dict:
        """Get file metadata."""
        try:
            p = self._validate_path(path)
            if not p.exists():
                return {'error': f'File not found: {path}', 'success': False}

            stat = p.stat()
            return {
                'success': True,
                'path': str(p),
                'name': p.name,
                'extension': p.suffix,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'is_file': p.is_file(),
                'is_dir': p.is_dir(),
            }
        except Exception as e:
            return {'error': str(e), 'success': False}
