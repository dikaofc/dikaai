"""DikaAI Tool Sandbox & Permissions

Controls what tools can do:
  - Permission levels (READ, WRITE, EXECUTE, NETWORK, DELETE, ADMIN)
  - Path guards (prevent access outside workspace)
  - Command validation (block dangerous commands)
  - Sandbox for code execution
"""
import os
import re
from enum import IntEnum
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path


class Permission(IntEnum):
    """Permission levels (higher includes lower)."""
    NONE = 0
    READ = 1       # Read files, list dirs
    WRITE = 2      # Create/edit files
    EXECUTE = 3    # Run commands
    NETWORK = 4    # HTTP requests
    DELETE = 5     # Delete files
    ADMIN = 6      # System-level operations


class ToolRequest:
    """A request to use a tool."""
    def __init__(self, tool: str, action: str, path: str = "",
                 command: str = "", permission: Permission = Permission.READ):
        self.tool = tool
        self.action = action
        self.path = path
        self.command = command
        self.permission = permission


class ToolSandbox:
    """Controls tool access with permissions and guards."""

    # Dangerous commands that should never be executed
    BLOCKED_COMMANDS = {
        'rm -rf /', 'rm -rf /*', 'dd if=', 'mkfs', ':(){', 'fork',
        'shutdown', 'reboot', 'halt', 'poweroff', 'init 0', 'init 6',
        'chmod -R 777 /', 'chown -R', 'wget', 'curl.*|.*sh',
        'eval', 'exec', 'nc -', 'ncat', 'socat',
    }

    # Commands that need special permission
    NETWORK_COMMANDS = {'curl', 'wget', 'ping', 'ssh', 'scp', 'rsync', 'nc'}

    DELETE_PATTERNS = ['rm ', 'rmdir', 'unlink', 'shred']

    def __init__(self, workspace: str = None, permission_level: Permission = Permission.EXECUTE):
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.permission_level = permission_level
        self._allowed_paths: List[str] = [str(self.workspace)]
        self._blocked_paths: List[str] = ['/etc', '/usr', '/bin', '/sbin', '/boot', '/sys', '/proc']
        self._audit_log: List[Dict] = []

    def check_permission(self, request: ToolRequest) -> Tuple[bool, str]:
        """Check if a tool request is allowed.

        Returns: (allowed, reason)
        """
        # Check permission level
        if request.permission > self.permission_level:
            reason = f"Insufficient permissions: need {request.permission.name}, have {self.permission_level.name}"
            self._audit(request, False, reason)
            return False, reason

        # Check path guards
        if request.path:
            allowed, reason = self._check_path(request.path)
            if not allowed:
                self._audit(request, False, reason)
                return False, reason

        # Check command guards
        if request.command:
            allowed, reason = self._check_command(request.command)
            if not allowed:
                self._audit(request, False, reason)
                return False, reason

        self._audit(request, True, "allowed")
        return True, "allowed"

    def _check_path(self, path: str) -> Tuple[bool, str]:
        """Check if a path is safe to access."""
        try:
            resolved = Path(path).resolve()
        except Exception:
            return False, f"Invalid path: {path}"

        # Check blocked paths
        for blocked in self._blocked_paths:
            if str(resolved).startswith(blocked):
                return False, f"Access denied: {path} is in blocked area ({blocked})"

        # For read: must be under workspace or allowed paths
        # For write/delete: must be strictly under workspace
        for allowed in self._allowed_paths:
            if str(resolved).startswith(allowed):
                return True, "ok"

        return False, f"Access denied: {path} is outside allowed workspace"

    def _check_command(self, command: str) -> Tuple[bool, str]:
        """Check if a command is safe to execute."""
        cmd_lower = command.lower().strip()

        # Check blocked commands
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in cmd_lower:
                return False, f"Blocked command pattern: {blocked}"

        # Check network commands
        first_word = cmd_lower.split()[0] if cmd_lower.split() else ''
        if first_word in self.NETWORK_COMMANDS:
            if self.permission_level < Permission.NETWORK:
                return False, f"Network commands require NETWORK permission"

        # Check delete commands
        for pattern in self.DELETE_PATTERNS:
            if pattern in cmd_lower:
                if self.permission_level < Permission.DELETE:
                    return False, f"Delete commands require DELETE permission"
                # Extra check: don't allow deleting outside workspace
                parts = cmd_lower.split()
                for part in parts:
                    if part.startswith('/') and not any(part.startswith(a) for a in self._allowed_paths):
                        return False, f"Cannot delete outside workspace: {part}"

        # Check for pipe to shell
        if '| sh' in cmd_lower or '| bash' in cmd_lower:
            return False, "Piping to shell is blocked"

        # Check for background execution of dangerous stuff
        if '&amp;' in cmd_lower or 'nohup' in cmd_lower:
            if self.permission_level < Permission.ADMIN:
                return False, "Background execution requires ADMIN permission"

        return True, "ok"

    def _audit(self, request: ToolRequest, allowed: bool, reason: str):
        """Log tool access for audit trail."""
        import time
        self._audit_log.append({
            'tool': request.tool,
            'action': request.action,
            'path': request.path,
            'command': request.command[:100],
            'permission': request.permission.name,
            'allowed': allowed,
            'reason': reason,
            'timestamp': time.time(),
        })
        # Keep last 200 entries
        if len(self._audit_log) > 200:
            self._audit_log = self._audit_log[-200:]

    def add_allowed_path(self, path: str):
        """Add an allowed path."""
        self._allowed_paths.append(str(Path(path).resolve()))

    def add_blocked_path(self, path: str):
        """Add a blocked path."""
        self._blocked_paths.append(str(Path(path).resolve()))

    def get_audit_log(self, limit: int = 20) -> List[Dict]:
        """Get recent audit log entries."""
        return self._audit_log[-limit:]

    def get_stats(self) -> Dict:
        blocked = sum(1 for e in self._audit_log if not e['allowed'])
        return {
            'permission_level': self.permission_level.name,
            'allowed_paths': len(self._allowed_paths),
            'blocked_paths': len(self._blocked_paths),
            'total_requests': len(self._audit_log),
            'blocked_requests': blocked,
            'allowed_requests': len(self._audit_log) - blocked,
        }
