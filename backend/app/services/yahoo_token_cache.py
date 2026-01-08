"""Yahoo OAuth2 token persistence with file-based caching.

Stores Yahoo OAuth2 tokens in a local file for persistence across server restarts.
Supports multiple sessions with separate token storage.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional, Any

from .yahoo_client import YahooToken


class YahooTokenCache:
    """File-based cache for Yahoo OAuth2 tokens.

    Stores tokens at ~/.fantasy-league-history/yahoo_tokens.json
    Each session_id gets its own token entry.
    """

    DEFAULT_CACHE_DIR = Path.home() / ".fantasy-league-history"
    DEFAULT_CACHE_FILE = "yahoo_tokens.json"

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the token cache.

        Args:
            cache_dir: Optional custom cache directory path.
        """
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.cache_file = self.cache_dir / self.DEFAULT_CACHE_FILE
        self._tokens: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_from_file(self) -> None:
        """Load tokens from cache file."""
        if self._loaded:
            return

        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                    self._tokens = data.get("tokens", {})
        except (json.JSONDecodeError, IOError):
            self._tokens = {}

        self._loaded = True

    def _save_to_file(self) -> None:
        """Save tokens to cache file."""
        self._ensure_cache_dir()

        data = {
            "tokens": self._tokens,
            "updated_at": time.time(),
        }

        # Write atomically using temp file
        temp_file = self.cache_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            temp_file.rename(self.cache_file)
        except IOError:
            if temp_file.exists():
                temp_file.unlink()
            raise

    def get_token(self, session_id: str = "default") -> Optional[YahooToken]:
        """Get a token for a session.

        Args:
            session_id: Session identifier (default: "default").

        Returns:
            YahooToken if found and valid, None otherwise.
        """
        self._load_from_file()

        token_data = self._tokens.get(session_id)
        if not token_data:
            return None

        try:
            return YahooToken.from_dict(token_data)
        except (KeyError, TypeError):
            return None

    def set_token(self, token: YahooToken, session_id: str = "default") -> None:
        """Store a token for a session.

        Args:
            token: YahooToken to store.
            session_id: Session identifier (default: "default").
        """
        self._load_from_file()

        self._tokens[session_id] = token.to_dict()
        self._save_to_file()

    def delete_token(self, session_id: str = "default") -> bool:
        """Delete a token for a session.

        Args:
            session_id: Session identifier (default: "default").

        Returns:
            True if token was deleted, False if not found.
        """
        self._load_from_file()

        if session_id in self._tokens:
            del self._tokens[session_id]
            self._save_to_file()
            return True
        return False

    def has_token(self, session_id: str = "default") -> bool:
        """Check if a session has a stored token.

        Args:
            session_id: Session identifier (default: "default").

        Returns:
            True if token exists for session.
        """
        self._load_from_file()
        return session_id in self._tokens

    def get_all_sessions(self) -> list:
        """Get list of all session IDs with stored tokens.

        Returns:
            List of session ID strings.
        """
        self._load_from_file()
        return list(self._tokens.keys())

    def clear_all(self) -> None:
        """Clear all stored tokens."""
        self._tokens = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        self._loaded = True

    def is_loaded(self) -> bool:
        """Check if cache has been loaded from file.

        Returns:
            True if cache data has been loaded.
        """
        return self._loaded


# Global singleton instance
_token_cache: Optional[YahooTokenCache] = None


def get_token_cache() -> YahooTokenCache:
    """Get the global token cache instance.

    Returns:
        YahooTokenCache singleton.
    """
    global _token_cache
    if _token_cache is None:
        _token_cache = YahooTokenCache()
    return _token_cache
