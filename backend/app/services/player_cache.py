"""Player cache for Sleeper player database.

This module provides a caching layer for the Sleeper player database,
which is a large (~30MB) JSON file containing all NFL players. The cache
stores the data locally to avoid repeated API calls.
"""

import json
import os
import time
from typing import Any, Optional

from app.services.sleeper_client import SleeperClient


class PlayerCache:
    """File-based cache for Sleeper player database.

    The cache stores player data in a JSON file with a timestamp.
    Data is refreshed when the cache is older than the specified TTL.

    Attributes:
        client: SleeperClient instance for fetching player data.
        cache_dir: Directory to store the cache file.
        ttl_hours: Time-to-live in hours for cached data.
        cache_file: Full path to the cache file.
    """

    CACHE_FILENAME = "sleeper_players.json"

    def __init__(
        self,
        client: SleeperClient,
        cache_dir: Optional[str] = None,
        ttl_hours: float = 24.0,
    ):
        """Initialize the player cache.

        Args:
            client: SleeperClient instance for fetching player data.
            cache_dir: Directory to store cache file. Defaults to ~/.fantasy-league-history/
            ttl_hours: Time-to-live in hours for cached data. Default is 24 hours.
        """
        self.client = client
        self.ttl_hours = ttl_hours

        # Set default cache directory if not provided
        if cache_dir is None:
            home = os.path.expanduser("~")
            cache_dir = os.path.join(home, ".fantasy-league-history")

        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, self.CACHE_FILENAME)

        # In-memory cache of player data
        self._players: dict[str, Any] = {}
        # Flag to track if cache has been explicitly loaded (for testing)
        self._loaded: bool = False

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)

    def _is_cache_valid(self) -> bool:
        """Check if the cache file exists and is not expired.

        Returns:
            True if cache is valid, False otherwise.
        """
        if not os.path.exists(self.cache_file):
            return False

        try:
            with open(self.cache_file, "r") as f:
                cached_data = json.load(f)

            timestamp = cached_data.get("timestamp", 0)
            age_hours = (time.time() - timestamp) / 3600

            return age_hours < self.ttl_hours
        except (json.JSONDecodeError, IOError, KeyError):
            return False

    def _load_from_cache(self) -> dict[str, Any]:
        """Load player data from cache file.

        Returns:
            Player data dictionary.

        Raises:
            IOError: If cache file cannot be read.
            json.JSONDecodeError: If cache file is not valid JSON.
        """
        with open(self.cache_file, "r") as f:
            cached_data = json.load(f)
        return cached_data["data"]

    def _save_to_cache(self, players: dict[str, Any]) -> None:
        """Save player data to cache file.

        Args:
            players: Player data dictionary to cache.
        """
        self._ensure_cache_dir()

        cache_data = {
            "timestamp": time.time(),
            "data": players,
        }

        with open(self.cache_file, "w") as f:
            json.dump(cache_data, f)

    async def fetch_players(self, force_refresh: bool = False) -> dict[str, Any]:
        """Fetch player data, using cache if available and not expired.

        Args:
            force_refresh: If True, ignore cache and fetch from API.

        Returns:
            Dictionary mapping player_id to player data.
        """
        # Return in-memory cache if available and not forcing refresh
        if self._loaded and not force_refresh:
            return self._players

        if self._players and not force_refresh:
            return self._players

        # Try to load from file cache if not forcing refresh
        if not force_refresh and self._is_cache_valid():
            self._players = self._load_from_cache()
            self._loaded = True
            return self._players

        # Fetch from API
        self._players = await self.client.get_players()
        self._loaded = True

        # Save to cache file
        self._save_to_cache(self._players)

        return self._players

    def get_player(self, player_id: str) -> Optional[dict[str, Any]]:
        """Get full player data by ID.

        Args:
            player_id: The Sleeper player ID.

        Returns:
            Player data dictionary, or None if not found.
        """
        return self._players.get(player_id)

    def get_player_name(self, player_id: str) -> str:
        """Get player's display name by ID.

        Tries full_name first, then falls back to first_name + last_name.
        If player is not found, returns "Player {id}".

        Args:
            player_id: The Sleeper player ID.

        Returns:
            Player's name, or a placeholder if not found.
        """
        player = self._players.get(player_id)

        if player is None:
            return f"Player {player_id}"

        # Try full_name first
        full_name = player.get("full_name")
        if full_name:
            return full_name

        # Fall back to first_name + last_name
        first_name = player.get("first_name", "")
        last_name = player.get("last_name", "")

        if first_name or last_name:
            return f"{first_name} {last_name}".strip()

        return f"Player {player_id}"

    def is_loaded(self) -> bool:
        """Check if player data is loaded in memory.

        Returns:
            True if player data is available or has been explicitly marked loaded.
        """
        return self._loaded or bool(self._players)

    def player_count(self) -> int:
        """Get the number of players in the cache.

        Returns:
            Number of players.
        """
        return len(self._players)
