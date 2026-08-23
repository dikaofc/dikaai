"""
DikaAI Auth - API Token generation and validation.

Tokens are stored in Redis (Vercel) or local file (dev).
Format: dka_<random_32_chars>

Usage:
    from dikaai.auth import AuthManager
    auth = AuthManager()
    token = auth.create_token(name="my-app", scopes=["chat", "agent"])
    valid = auth.validate_token(token)
"""

import os
import json
import time
import hashlib
import secrets
from pathlib import Path


class AuthManager:
    """Manages API tokens for DikaAI public API."""

    def __init__(self):
        self.redis = None
        self._local_tokens_file = Path(__file__).parent.parent / "data" / "api_tokens.json"
        self._local_tokens_file.parent.mkdir(parents=True, exist_ok=True)

        # Try Redis first
        try:
            from dikaai.config import UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN, USE_REDIS
            if USE_REDIS:
                from dikaai.database import UpstashRedis
                self.redis = UpstashRedis(UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN)
        except Exception:
            pass

    def create_token(self, name: str = "default", scopes: list = None,
                     rate_limit: int = 60) -> dict:
        """Create a new API token.

        Args:
            name: Human-readable name for the token
            scopes: List of allowed scopes (chat, agent, tools, admin)
            rate_limit: Max requests per minute

        Returns:
            dict with token, name, scopes, created_at
        """
        token = f"dka_{''.join(secrets.token_hex(16).split())}"
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        data = {
            'hash': token_hash,
            'name': name,
            'scopes': scopes or ['chat', 'agent', 'tools'],
            'rate_limit': rate_limit,
            'created_at': time.time(),
            'last_used': 0,
            'total_requests': 0,
            'active': True,
        }

        if self.redis:
            self.redis.hset('dikaai:tokens', token_hash, json.dumps(data))
        else:
            self._save_local(token_hash, data)

        return {
            'token': token,
            'name': name,
            'scopes': data['scopes'],
            'rate_limit': rate_limit,
            'created_at': data['created_at'],
        }

    def validate_token(self, token: str, required_scope: str = None) -> dict:
        """Validate an API token.

        Args:
            token: The API token to validate
            required_scope: Optional scope to check

        Returns:
            dict with valid, token_data, error
        """
        if not token:
            return {'valid': False, 'error': 'No token provided'}

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        data = None
        if self.redis:
            raw = self.redis.hget('dikaai:tokens', token_hash)
            if raw:
                try:
                    data = json.loads(raw)
                except Exception:
                    pass
        else:
            data = self._load_local(token_hash)

        if not data:
            return {'valid': False, 'error': 'Invalid token'}

        if not data.get('active', True):
            return {'valid': False, 'error': 'Token revoked'}

        if required_scope and required_scope not in data.get('scopes', []):
            return {'valid': False, 'error': f'Missing scope: {required_scope}'}

        # Update usage
        data['last_used'] = time.time()
        data['total_requests'] = data.get('total_requests', 0) + 1
        if self.redis:
            self.redis.hset('dikaai:tokens', token_hash, json.dumps(data))
        else:
            self._save_local(token_hash, data)

        return {'valid': True, 'token_data': data}

    def revoke_token(self, token: str) -> bool:
        """Revoke an API token."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        if self.redis:
            raw = self.redis.hget('dikaai:tokens', token_hash)
            if raw:
                data = json.loads(raw)
                data['active'] = False
                self.redis.hset('dikaai:tokens', token_hash, json.dumps(data))
                return True
        else:
            data = self._load_local(token_hash)
            if data:
                data['active'] = False
                self._save_local(token_hash, data)
                return True
        return False

    def list_tokens(self) -> list:
        """List all tokens (without revealing actual tokens)."""
        tokens = []
        if self.redis:
            raw = self.redis.hget('dikaai:tokens', '*')
            # Redis doesn't support wildcard hget, use hgetall pattern
            pass
        else:
            if self._local_tokens_file.exists():
                try:
                    with open(self._local_tokens_file) as f:
                        store = json.load(f)
                    for h, data in store.items():
                        tokens.append({
                            'name': data.get('name', ''),
                            'scopes': data.get('scopes', []),
                            'active': data.get('active', True),
                            'created_at': data.get('created_at', 0),
                            'total_requests': data.get('total_requests', 0),
                        })
                except Exception:
                    pass
        return tokens

    def _save_local(self, token_hash: str, data: dict):
        """Save token to local file."""
        store = {}
        if self._local_tokens_file.exists():
            try:
                with open(self._local_tokens_file) as f:
                    store = json.load(f)
            except Exception:
                pass
        store[token_hash] = data
        with open(self._local_tokens_file, 'w') as f:
            json.dump(store, f, indent=2)

    def _load_local(self, token_hash: str) -> dict:
        """Load token from local file."""
        if not self._local_tokens_file.exists():
            return None
        try:
            with open(self._local_tokens_file) as f:
                store = json.load(f)
            return store.get(token_hash)
        except Exception:
            return None
