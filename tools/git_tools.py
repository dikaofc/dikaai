"""DikaAI Git Tools - Version control operations."""

import subprocess
import os


class GitTools:
    """Git operations for coding agent."""

    def __init__(self, workspace: str = None):
        self.workspace = workspace or os.getcwd()

    def _run(self, *args) -> dict:
        """Run git command."""
        try:
            result = subprocess.run(
                ['git'] + list(args),
                capture_output=True,
                text=True,
                timeout=15,
                cwd=self.workspace,
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def status(self) -> dict:
        """Get git status."""
        return self._run('status', '--short')

    def diff(self, file_path: str = None) -> dict:
        """Get git diff."""
        args = ['diff']
        if file_path:
            args.append(file_path)
        return self._run(*args)

    def log(self, count: int = 10) -> dict:
        """Get recent commits."""
        return self._run('log', f'--oneline', f'-{count}')

    def commit(self, message: str, add_all: bool = False) -> dict:
        """Create a commit."""
        if add_all:
            self._run('add', '-A')
        return self._run('commit', '-m', message)

    def branch(self) -> dict:
        """List branches."""
        return self._run('branch', '-a')

    def checkout(self, branch: str) -> dict:
        """Switch branch."""
        return self._run('checkout', branch)

    def create_branch(self, name: str) -> dict:
        """Create new branch."""
        return self._run('checkout', '-b', name)

    def stash(self) -> dict:
        """Stash changes."""
        return self._run('stash')

    def stash_pop(self) -> dict:
        """Pop stash."""
        return self._run('stash', 'pop')

    def pull(self) -> dict:
        """Pull from remote."""
        return self._run('pull')

    def push(self, branch: str = 'main') -> dict:
        """Push to remote."""
        return self._run('push', 'origin', branch)

    def remote_url(self) -> dict:
        """Get remote URL."""
        return self._run('remote', 'get-url', 'origin')

    def file_history(self, file_path: str, count: int = 5) -> dict:
        """Get file history."""
        return self._run('log', f'-{count}', '--oneline', '--', file_path)

    def blame(self, file_path: str) -> dict:
        """Git blame a file."""
        return self._run('blame', '--line-porcelain', file_path)
