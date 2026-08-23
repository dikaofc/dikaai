"""DikaAI Terminal Tools - Safe command execution."""

import subprocess
import os
from core.config import AGENT


class TerminalTools:
    """Execute shell commands safely."""

    def __init__(self, workspace: str = None):
        self.workspace = workspace or os.getcwd()

    def run_command(self, command: str, timeout: int = None) -> dict:
        """Run a shell command with safety checks."""
        timeout = timeout or AGENT['timeout_seconds']

        # Safety: block dangerous commands
        cmd_lower = command.lower().strip()
        for blocked in AGENT['blocked_commands']:
            if blocked in cmd_lower:
                return {
                    'success': False,
                    'error': f'Blocked dangerous command: {blocked}',
                    'stdout': '',
                    'stderr': 'Command blocked for safety',
                    'returncode': -1,
                }

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'},
            )

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout[-5000:] if result.stdout else '',  # Limit output
                'stderr': result.stderr[-2000:] if result.stderr else '',
                'returncode': result.returncode,
                'command': command,
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Command timed out after {timeout}s',
                'stdout': '',
                'stderr': f'Timeout: {command}',
                'returncode': -1,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': str(e),
                'returncode': -1,
            }

    def run_python(self, code: str, timeout: int = None) -> dict:
        """Run Python code safely."""
        timeout = timeout or AGENT['timeout_seconds']

        # Write to temp file and execute
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                ['python', tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace,
            )

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout[-5000:] if result.stdout else '',
                'stderr': result.stderr[-2000:] if result.stderr else '',
                'returncode': result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Python timed out after {timeout}s',
                'stdout': '',
                'stderr': 'Timeout',
                'returncode': -1,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': str(e),
                'returncode': -1,
            }
        finally:
            os.unlink(tmp_path)

    def run_file(self, file_path: str, timeout: int = None) -> dict:
        """Run a script file."""
        p = os.path.join(self.workspace, file_path)
        if not os.path.exists(p):
            return {'success': False, 'error': f'File not found: {file_path}'}

        ext = os.path.splitext(p)[1]
        cmd_map = {
            '.py': ['python', p],
            '.js': ['node', p],
            '.sh': ['bash', p],
            '.go': ['go', 'run', p],
        }

        cmd = cmd_map.get(ext)
        if not cmd:
            return {'success': False, 'error': f'Unsupported file type: {ext}'}

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or AGENT['timeout_seconds'],
                cwd=self.workspace,
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout[-5000:],
                'stderr': result.stderr[-2000:],
                'returncode': result.returncode,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
