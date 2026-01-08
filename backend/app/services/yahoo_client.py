"""Yahoo Fantasy Sports API client with OAuth2 authentication.

Yahoo Fantasy Sports API documentation: https://developer.yahoo.com/fantasysports/guide/
Base URL: https://fantasysports.yahooapis.com/fantasy/v2/

OAuth2 flow:
1. User visits authorization URL and grants permission
2. User receives authorization code
3. Exchange code for access token + refresh token
4. Use access token for API requests
5. Refresh token when access token expires
"""

import json
import time
import os
from typing import Any, Optional, Dict, List
from dataclasses import dataclass
from urllib.parse import urlencode
import httpx


@dataclass
class YahooToken:
    """OAuth2 token data structure."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    expires_at: float  # Unix timestamp when token expires

    def is_expired(self) -> bool:
        """Check if the access token has expired (with 5-minute buffer)."""
        return time.time() >= (self.expires_at - 300)

    def to_dict(self) -> dict:
        """Convert token to dictionary for storage."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "YahooToken":
        """Create token from dictionary."""
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            token_type=data.get("token_type", "bearer"),
            expires_in=data.get("expires_in", 3600),
            expires_at=data.get("expires_at", time.time() + 3600),
        )


class YahooAuthError(Exception):
    """Exception raised for Yahoo OAuth2 authentication errors."""
    pass


class YahooAPIError(Exception):
    """Exception raised for Yahoo API request errors."""
    pass


class YahooClient:
    """HTTP client for the Yahoo Fantasy Sports API with OAuth2 authentication."""

    AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
    TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
    BASE_URL = "https://fantasysports.yahooapis.com/fantasy/v2"

    # NFL game key for 2024 season (updates yearly)
    NFL_GAME_KEY = "449"  # 2024 NFL season

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: str = "oob",
        timeout: float = 30.0,
    ):
        """Initialize the Yahoo Fantasy API client.

        Args:
            client_id: Yahoo app client ID (from environment if not provided).
            client_secret: Yahoo app client secret (from environment if not provided).
            redirect_uri: OAuth redirect URI (default "oob" for out-of-band).
            timeout: Request timeout in seconds.
        """
        self.client_id = client_id or os.environ.get("YAHOO_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("YAHOO_CLIENT_SECRET", "")
        self.redirect_uri = redirect_uri
        self.timeout = timeout
        self._token: Optional[YahooToken] = None

    @property
    def is_authenticated(self) -> bool:
        """Check if client has valid authentication."""
        return self._token is not None and not self._token.is_expired()

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate the OAuth2 authorization URL for user consent.

        Args:
            state: Optional state parameter for CSRF protection.

        Returns:
            URL for user to visit to authorize the application.
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
        }
        if state:
            params["state"] = state

        return f"{self.AUTH_URL}?{urlencode(params)}"

    async def exchange_code_for_token(self, authorization_code: str) -> YahooToken:
        """Exchange authorization code for access token.

        Args:
            authorization_code: Code received from OAuth callback.

        Returns:
            YahooToken with access and refresh tokens.

        Raises:
            YahooAuthError: If token exchange fails.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": self.redirect_uri,
                },
                auth=(self.client_id, self.client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise YahooAuthError(
                    f"Token exchange failed: {response.status_code} - {response.text}"
                )

            data = response.json()
            token = YahooToken(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                token_type=data.get("token_type", "bearer"),
                expires_in=data.get("expires_in", 3600),
                expires_at=time.time() + data.get("expires_in", 3600),
            )
            self._token = token
            return token

    async def refresh_access_token(self) -> YahooToken:
        """Refresh the access token using the refresh token.

        Returns:
            New YahooToken with fresh access token.

        Raises:
            YahooAuthError: If token refresh fails or no refresh token available.
        """
        if not self._token or not self._token.refresh_token:
            raise YahooAuthError("No refresh token available")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._token.refresh_token,
                },
                auth=(self.client_id, self.client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise YahooAuthError(
                    f"Token refresh failed: {response.status_code} - {response.text}"
                )

            data = response.json()
            self._token = YahooToken(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", self._token.refresh_token),
                token_type=data.get("token_type", "bearer"),
                expires_in=data.get("expires_in", 3600),
                expires_at=time.time() + data.get("expires_in", 3600),
            )
            return self._token

    def set_token(self, token: YahooToken) -> None:
        """Set the OAuth token directly (for loading from storage).

        Args:
            token: YahooToken to use for API requests.
        """
        self._token = token

    def set_token_from_dict(self, token_data: dict) -> None:
        """Set the OAuth token from a dictionary.

        Args:
            token_data: Dictionary containing token fields.
        """
        self._token = YahooToken.from_dict(token_data)

    def get_token(self) -> Optional[YahooToken]:
        """Get the current OAuth token.

        Returns:
            Current YahooToken or None if not authenticated.
        """
        return self._token

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid access token, refreshing if needed."""
        if not self._token:
            raise YahooAuthError("Not authenticated. Call exchange_code_for_token first.")

        if self._token.is_expired():
            await self.refresh_access_token()

    async def _get(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> Any:
        """Make an authenticated GET request to the Yahoo Fantasy API.

        Args:
            endpoint: API endpoint path (without base URL).
            params: Optional query parameters.

        Returns:
            JSON response data.

        Raises:
            YahooAPIError: If the request fails.
            YahooAuthError: If not authenticated.
        """
        await self._ensure_authenticated()

        url = f"{self.BASE_URL}{endpoint}"
        # Always request JSON format
        if params is None:
            params = {}
        params["format"] = "json"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url,
                params=params,
                headers={
                    "Authorization": f"Bearer {self._token.access_token}",
                    "Accept": "application/json",
                },
            )

            if response.status_code == 401:
                # Try refreshing token once
                await self.refresh_access_token()
                response = await client.get(
                    url,
                    params=params,
                    headers={
                        "Authorization": f"Bearer {self._token.access_token}",
                        "Accept": "application/json",
                    },
                )

            if response.status_code != 200:
                raise YahooAPIError(
                    f"API request failed: {response.status_code} - {response.text}"
                )

            return response.json()

    @staticmethod
    def _extract_value(data: Any) -> Any:
        """Extract value from Yahoo's nested response format.

        Yahoo API returns data in a nested format like:
        {"fantasy_content": {"league": [{"league_key": "..."}, {...}]}}

        This helper extracts the actual data.
        """
        if isinstance(data, dict) and "fantasy_content" in data:
            return data["fantasy_content"]
        return data

    # ============= League Methods =============

    async def get_user_leagues(self, game_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all leagues for the authenticated user.

        Args:
            game_key: Game key (default: current NFL season).

        Returns:
            List of league data dictionaries.
        """
        gk = game_key or self.NFL_GAME_KEY
        response = await self._get(f"/users;use_login=1/games;game_keys={gk}/leagues")
        content = self._extract_value(response)

        leagues = []
        try:
            # Navigate Yahoo's complex nested structure
            users = content.get("users", {})
            if "0" in users:
                user = users["0"]["user"]
                if isinstance(user, list):
                    for item in user:
                        if isinstance(item, dict) and "games" in item:
                            games = item["games"]
                            if "0" in games:
                                game = games["0"]["game"]
                                if isinstance(game, list):
                                    for g_item in game:
                                        if isinstance(g_item, dict) and "leagues" in g_item:
                                            league_data = g_item["leagues"]
                                            for key, value in league_data.items():
                                                if key.isdigit() and "league" in value:
                                                    leagues.append(
                                                        self._parse_league(value["league"])
                                                    )
        except (KeyError, IndexError, TypeError):
            pass  # Return empty list if structure doesn't match

        return leagues

    async def get_league(self, league_key: str) -> Dict[str, Any]:
        """Fetch league information by league key.

        Args:
            league_key: The Yahoo league key (e.g., "449.l.123456").

        Returns:
            League data dictionary containing:
            - league_key: str
            - name: str
            - num_teams: int
            - scoring_type: str
            - season: str (year)
            - current_week: int
        """
        response = await self._get(f"/league/{league_key}")
        content = self._extract_value(response)

        league_data = content.get("league", [])
        return self._parse_league(league_data)

    def _parse_league(self, league_data: Any) -> Dict[str, Any]:
        """Parse league data from Yahoo's response format."""
        if isinstance(league_data, list):
            # Merge all items in the list into one dict
            merged = {}
            for item in league_data:
                if isinstance(item, dict):
                    merged.update(item)
            league_data = merged

        return {
            "league_key": league_data.get("league_key", ""),
            "league_id": league_data.get("league_id", ""),
            "name": league_data.get("name", "Unknown League"),
            "num_teams": league_data.get("num_teams", 0),
            "scoring_type": league_data.get("scoring_type", ""),
            "season": league_data.get("season", ""),
            "current_week": league_data.get("current_week", 1),
            "start_week": league_data.get("start_week", 1),
            "end_week": league_data.get("end_week", 17),
            "is_finished": league_data.get("is_finished", 0) == 1,
        }

    async def get_standings(self, league_key: str) -> List[Dict[str, Any]]:
        """Fetch standings for a league.

        Args:
            league_key: The Yahoo league key.

        Returns:
            List of team standings with records and ranks.
        """
        response = await self._get(f"/league/{league_key}/standings")
        content = self._extract_value(response)

        standings = []
        try:
            league = content.get("league", [])
            for item in league:
                if isinstance(item, dict) and "standings" in item:
                    teams_data = item["standings"][0].get("teams", {})
                    for key, value in teams_data.items():
                        if key.isdigit() and "team" in value:
                            standings.append(self._parse_team(value["team"]))
        except (KeyError, IndexError, TypeError):
            pass

        return standings

    def _parse_team(self, team_data: Any) -> Dict[str, Any]:
        """Parse team data from Yahoo's response format."""
        if isinstance(team_data, list):
            merged = {}
            for item in team_data:
                if isinstance(item, dict):
                    merged.update(item)
            team_data = merged

        # Extract standings info
        standings = team_data.get("team_standings", {})
        outcome_totals = standings.get("outcome_totals", {})

        return {
            "team_key": team_data.get("team_key", ""),
            "team_id": team_data.get("team_id", ""),
            "name": team_data.get("name", ""),
            "manager": self._parse_manager(team_data.get("managers", [])),
            "wins": int(outcome_totals.get("wins", 0)),
            "losses": int(outcome_totals.get("losses", 0)),
            "ties": int(outcome_totals.get("ties", 0)),
            "points_for": float(standings.get("points_for", 0)),
            "points_against": float(standings.get("points_against", 0)),
            "rank": int(standings.get("rank", 0)),
            "playoff_seed": standings.get("playoff_seed"),
        }

    def _parse_manager(self, managers_data: Any) -> Dict[str, Any]:
        """Parse manager (owner) data from Yahoo's response format."""
        if not managers_data:
            return {}

        if isinstance(managers_data, list):
            for item in managers_data:
                if isinstance(item, dict) and "manager" in item:
                    manager = item["manager"]
                    return {
                        "manager_id": manager.get("manager_id", ""),
                        "guid": manager.get("guid", ""),
                        "nickname": manager.get("nickname", ""),
                        "image_url": manager.get("image_url"),
                    }
        return {}

    async def get_matchups(
        self, league_key: str, week: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch matchups (scoreboard) for a league.

        Args:
            league_key: The Yahoo league key.
            week: Specific week number (default: current week).

        Returns:
            List of matchup data dictionaries.
        """
        endpoint = f"/league/{league_key}/scoreboard"
        if week:
            endpoint += f";week={week}"

        response = await self._get(endpoint)
        content = self._extract_value(response)

        matchups = []
        try:
            league = content.get("league", [])
            for item in league:
                if isinstance(item, dict) and "scoreboard" in item:
                    scoreboard = item["scoreboard"]
                    if "0" in scoreboard and "matchups" in scoreboard["0"]:
                        matchups_data = scoreboard["0"]["matchups"]
                        for key, value in matchups_data.items():
                            if key.isdigit() and "matchup" in value:
                                matchups.append(self._parse_matchup(value["matchup"]))
        except (KeyError, IndexError, TypeError):
            pass

        return matchups

    def _parse_matchup(self, matchup_data: Any) -> Dict[str, Any]:
        """Parse matchup data from Yahoo's response format."""
        result = {
            "week": 0,
            "is_playoffs": False,
            "is_consolation": False,
            "teams": [],
            "winner_team_key": None,
            "is_tied": False,
        }

        if isinstance(matchup_data, list):
            for item in matchup_data:
                if isinstance(item, dict):
                    if "week" in item:
                        result["week"] = int(item["week"])
                    if "is_playoffs" in item:
                        result["is_playoffs"] = item["is_playoffs"] == "1"
                    if "is_consolation" in item:
                        result["is_consolation"] = item["is_consolation"] == "1"
                    if "is_tied" in item:
                        result["is_tied"] = item["is_tied"] == "1"
                    if "winner_team_key" in item:
                        result["winner_team_key"] = item["winner_team_key"]
                    if "0" in item and "teams" in item["0"]:
                        teams_data = item["0"]["teams"]
                        for key, value in teams_data.items():
                            if key.isdigit() and "team" in value:
                                result["teams"].append(
                                    self._parse_matchup_team(value["team"])
                                )

        return result

    def _parse_matchup_team(self, team_data: Any) -> Dict[str, Any]:
        """Parse team data from matchup response."""
        if isinstance(team_data, list):
            merged = {}
            for item in team_data:
                if isinstance(item, dict):
                    merged.update(item)
            team_data = merged

        team_points = team_data.get("team_points", {})

        return {
            "team_key": team_data.get("team_key", ""),
            "team_id": team_data.get("team_id", ""),
            "name": team_data.get("name", ""),
            "points": float(team_points.get("total", 0)),
        }

    async def get_all_matchups_for_season(
        self, league_key: str, start_week: int = 1, end_week: int = 17
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Fetch all matchups for an entire season.

        Args:
            league_key: The Yahoo league key.
            start_week: First week to fetch.
            end_week: Last week to fetch.

        Returns:
            Dictionary mapping week number to list of matchups.
        """
        all_matchups = {}
        for week in range(start_week, end_week + 1):
            matchups = await self.get_matchups(league_key, week)
            if matchups:
                all_matchups[week] = matchups
        return all_matchups

    async def get_transactions(
        self, league_key: str, transaction_type: str = "trade"
    ) -> List[Dict[str, Any]]:
        """Fetch transactions for a league.

        Args:
            league_key: The Yahoo league key.
            transaction_type: Type of transaction ("trade", "add", "drop", "commish").

        Returns:
            List of transaction data dictionaries.
        """
        response = await self._get(
            f"/league/{league_key}/transactions;type={transaction_type}"
        )
        content = self._extract_value(response)

        transactions = []
        try:
            league = content.get("league", [])
            for item in league:
                if isinstance(item, dict) and "transactions" in item:
                    trans_data = item["transactions"]
                    for key, value in trans_data.items():
                        if key.isdigit() and "transaction" in value:
                            transactions.append(
                                self._parse_transaction(value["transaction"])
                            )
        except (KeyError, IndexError, TypeError):
            pass

        return transactions

    def _parse_transaction(self, transaction_data: Any) -> Dict[str, Any]:
        """Parse transaction data from Yahoo's response format."""
        result = {
            "transaction_id": "",
            "type": "",
            "status": "",
            "timestamp": 0,
            "trader_team_key": "",
            "tradee_team_key": "",
            "players": [],
        }

        if isinstance(transaction_data, list):
            for item in transaction_data:
                if isinstance(item, dict):
                    if "transaction_key" in item:
                        result["transaction_id"] = item.get("transaction_key", "")
                    if "type" in item:
                        result["type"] = item.get("type", "")
                    if "status" in item:
                        result["status"] = item.get("status", "")
                    if "timestamp" in item:
                        result["timestamp"] = int(item.get("timestamp", 0))
                    if "trader_team_key" in item:
                        result["trader_team_key"] = item.get("trader_team_key", "")
                    if "tradee_team_key" in item:
                        result["tradee_team_key"] = item.get("tradee_team_key", "")
                    if "players" in item:
                        players_data = item["players"]
                        for key, value in players_data.items():
                            if key.isdigit() and "player" in value:
                                result["players"].append(
                                    self._parse_trade_player(value["player"])
                                )

        return result

    def _parse_trade_player(self, player_data: Any) -> Dict[str, Any]:
        """Parse player data from trade transaction."""
        if isinstance(player_data, list):
            merged = {}
            for item in player_data:
                if isinstance(item, dict):
                    merged.update(item)
            player_data = merged

        transaction_data = player_data.get("transaction_data", {})
        if isinstance(transaction_data, list):
            for item in transaction_data:
                if isinstance(item, dict):
                    transaction_data = item
                    break

        return {
            "player_key": player_data.get("player_key", ""),
            "player_id": player_data.get("player_id", ""),
            "name": player_data.get("name", {}).get("full", ""),
            "source_team_key": transaction_data.get("source_team_key", ""),
            "destination_team_key": transaction_data.get("destination_team_key", ""),
            "source_type": transaction_data.get("source_type", ""),
            "destination_type": transaction_data.get("destination_type", ""),
        }

    async def get_trades(self, league_key: str) -> List[Dict[str, Any]]:
        """Fetch all trades for a league (convenience method).

        Args:
            league_key: The Yahoo league key.

        Returns:
            List of trade transaction data.
        """
        return await self.get_transactions(league_key, "trade")

    # ============= Historical Data Methods =============

    async def get_historical_leagues(
        self, game_keys: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get leagues from multiple seasons.

        Args:
            game_keys: List of game keys for different seasons.

        Returns:
            List of league data from all specified seasons.
        """
        if not game_keys:
            # Default to recent NFL seasons
            game_keys = ["449", "423", "406", "399", "390"]  # 2024-2020

        all_leagues = []
        for game_key in game_keys:
            try:
                leagues = await self.get_user_leagues(game_key)
                all_leagues.extend(leagues)
            except YahooAPIError:
                continue  # Skip seasons with no data

        return all_leagues
