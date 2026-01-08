"""Sleeper API client for fetching fantasy football data.

Sleeper API documentation: https://docs.sleeper.com/
Base URL: https://api.sleeper.app/v1
"""

from typing import Any, Optional
import httpx


class SleeperClient:
    """HTTP client for the Sleeper Fantasy Football API."""

    BASE_URL = "https://api.sleeper.app/v1"

    def __init__(self, timeout: float = 30.0):
        """Initialize the Sleeper API client.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout

    async def _get(self, endpoint: str) -> Any:
        """Make a GET request to the Sleeper API.

        Args:
            endpoint: API endpoint path (without base URL).

        Returns:
            JSON response data.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{self.BASE_URL}{endpoint}"
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_league(self, league_id: str) -> dict[str, Any]:
        """Fetch league information by league ID.

        Args:
            league_id: The Sleeper league ID.

        Returns:
            League data dictionary containing:
            - league_id: str
            - name: str
            - season: str (year)
            - total_rosters: int
            - scoring_settings: dict
            - status: str (e.g., "complete", "in_season")
            - settings: dict (contains playoff_week_start, etc.)
        """
        return await self._get(f"/league/{league_id}")

    async def get_users(self, league_id: str) -> list[dict[str, Any]]:
        """Fetch all users in a league.

        Args:
            league_id: The Sleeper league ID.

        Returns:
            List of user dictionaries containing:
            - user_id: str
            - username: str
            - display_name: str
            - avatar: str (avatar ID, not full URL)
        """
        return await self._get(f"/league/{league_id}/users")

    async def get_rosters(self, league_id: str) -> list[dict[str, Any]]:
        """Fetch all rosters in a league.

        Args:
            league_id: The Sleeper league ID.

        Returns:
            List of roster dictionaries containing:
            - roster_id: int
            - owner_id: str (user_id of owner)
            - settings: dict (wins, losses, ties, fpts, etc.)
            - players: list[str] (player IDs)
        """
        return await self._get(f"/league/{league_id}/rosters")

    async def get_matchups(self, league_id: str, week: int) -> list[dict[str, Any]]:
        """Fetch matchups for a specific week.

        Args:
            league_id: The Sleeper league ID.
            week: Week number (1-18 typically).

        Returns:
            List of matchup dictionaries containing:
            - roster_id: int
            - matchup_id: int (teams with same matchup_id play each other)
            - points: float (total points scored)
            - players: list[str]
            - starters: list[str]
        """
        return await self._get(f"/league/{league_id}/matchups/{week}")

    async def get_transactions(
        self, league_id: str, week: int
    ) -> list[dict[str, Any]]:
        """Fetch all transactions (trades, waivers, free agents) for a week.

        Args:
            league_id: The Sleeper league ID.
            week: Week number.

        Returns:
            List of transaction dictionaries containing:
            - transaction_id: str
            - type: str ("trade", "waiver", "free_agent")
            - status: str ("complete", "failed", etc.)
            - roster_ids: list[int] (rosters involved)
            - adds: dict (player_id -> roster_id)
            - drops: dict (player_id -> roster_id)
            - draft_picks: list (for trades involving picks)
            - created: int (timestamp in milliseconds)
        """
        return await self._get(f"/league/{league_id}/transactions/{week}")

    async def get_traded_picks(self, league_id: str) -> list[dict[str, Any]]:
        """Fetch all traded draft picks for a league.

        Args:
            league_id: The Sleeper league ID.

        Returns:
            List of traded pick dictionaries.
        """
        return await self._get(f"/league/{league_id}/traded_picks")

    async def get_user(self, username_or_id: str) -> Optional[dict[str, Any]]:
        """Fetch user information by username or user ID.

        Args:
            username_or_id: Username or user_id.

        Returns:
            User data dictionary or None if not found.
        """
        try:
            return await self._get(f"/user/{username_or_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def get_sport_state(self, sport: str = "nfl") -> dict[str, Any]:
        """Fetch current state of a sport (season, week, etc.).

        Args:
            sport: Sport identifier (default: "nfl").

        Returns:
            State dictionary containing:
            - season: str (year)
            - week: int
            - season_type: str ("regular", "post")
            - display_week: int
        """
        return await self._get(f"/state/{sport}")

    async def get_all_matchups_for_season(
        self, league_id: str, total_weeks: int = 18
    ) -> dict[int, list[dict[str, Any]]]:
        """Fetch all matchups for an entire season.

        Args:
            league_id: The Sleeper league ID.
            total_weeks: Total number of weeks in the season.

        Returns:
            Dictionary mapping week number to list of matchups.
        """
        all_matchups = {}
        for week in range(1, total_weeks + 1):
            matchups = await self.get_matchups(league_id, week)
            # Only include weeks that have matchup data
            if matchups:
                all_matchups[week] = matchups
        return all_matchups

    async def get_all_trades_for_season(
        self, league_id: str, total_weeks: int = 18
    ) -> list[dict[str, Any]]:
        """Fetch all trades for an entire season.

        Args:
            league_id: The Sleeper league ID.
            total_weeks: Total number of weeks to check.

        Returns:
            List of all trade transactions across all weeks.
        """
        all_trades = []
        for week in range(1, total_weeks + 1):
            transactions = await self.get_transactions(league_id, week)
            # Filter to only include completed trades
            trades = [
                t for t in transactions
                if t.get("type") == "trade" and t.get("status") == "complete"
            ]
            for trade in trades:
                trade["week"] = week  # Add week info to trade
            all_trades.extend(trades)
        return all_trades

    @staticmethod
    def get_avatar_url(avatar_id: Optional[str]) -> Optional[str]:
        """Convert avatar ID to full URL.

        Args:
            avatar_id: The avatar ID from user data.

        Returns:
            Full URL to avatar image or None.
        """
        if not avatar_id:
            return None
        return f"https://sleepercdn.com/avatars/{avatar_id}"

    @staticmethod
    def get_previous_league_id(league_data: dict[str, Any]) -> Optional[str]:
        """Extract the previous_league_id from league data.

        Sleeper leagues have a chain of previous_league_id fields that link
        to the same league from prior seasons.

        Args:
            league_data: League data dictionary from get_league().

        Returns:
            The previous league ID if it exists, None otherwise.
        """
        prev_id = league_data.get("previous_league_id")
        # Sleeper returns None or empty string if no previous league
        if not prev_id:
            return None
        return prev_id

    async def get_league_history_chain(self, league_id: str) -> list[str]:
        """Traverse the chain of previous_league_id to find all historical league IDs.

        Starting from the given league_id, follows the chain of previous_league_id
        references to find all historical seasons of this league.

        Args:
            league_id: The current (most recent) Sleeper league ID.

        Returns:
            List of league IDs from newest to oldest (current season first).
            For example: ["2023_league_id", "2022_league_id", "2021_league_id"]
        """
        chain: list[str] = []
        current_id: Optional[str] = league_id

        while current_id:
            chain.append(current_id)
            league_data = await self.get_league(current_id)
            current_id = self.get_previous_league_id(league_data)

        return chain

    async def get_players(self, sport: str = "nfl") -> dict[str, Any]:
        """Fetch all players for a sport from the Sleeper API.

        This endpoint returns a large (~30MB) dictionary of all players.
        The response is keyed by player_id.

        Args:
            sport: Sport identifier (default: "nfl").

        Returns:
            Dictionary mapping player_id to player data containing:
            - player_id: str
            - full_name: str (may be null)
            - first_name: str
            - last_name: str
            - team: str (NFL team abbreviation, may be null)
            - position: str (e.g., "WR", "RB", "QB")
            - status: str (e.g., "Active", "Injured Reserve")
            - And many other fields...
        """
        return await self._get(f"/players/{sport}")
