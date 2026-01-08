"""Tests for Sleeper API integration.

Tests cover:
- SleeperClient API calls
- SleeperService database operations
- API endpoint functionality
- Player cache functionality
"""

import json
import os
import tempfile
import time
from datetime import datetime
from typing import Optional
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import League, Season, Team, Owner, Matchup, Trade, Platform
from app.services.sleeper_client import SleeperClient
from app.services.sleeper_service import SleeperService
from app.services.player_cache import PlayerCache


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_league_data():
    """Sample Sleeper league data."""
    return {
        "league_id": "123456789",
        "name": "Test Fantasy League",
        "season": "2023",
        "total_rosters": 10,
        "status": "complete",
        "scoring_settings": {"rec": 1},  # PPR
        "settings": {
            "playoff_week_start": 15,
            "playoff_teams": 6,
        },
    }


@pytest.fixture
def mock_users_data():
    """Sample Sleeper users data."""
    return [
        {
            "user_id": "user_001",
            "username": "testuser1",
            "display_name": "Test User 1",
            "avatar": "avatar123",
        },
        {
            "user_id": "user_002",
            "username": "testuser2",
            "display_name": "Test User 2",
            "avatar": "avatar456",
        },
    ]


@pytest.fixture
def mock_rosters_data():
    """Sample Sleeper rosters data."""
    return [
        {
            "roster_id": 1,
            "owner_id": "user_001",
            "settings": {
                "wins": 10,
                "losses": 4,
                "ties": 0,
                "fpts": 1500,
                "fpts_decimal": 50,
                "fpts_against": 1400,
                "fpts_against_decimal": 25,
            },
        },
        {
            "roster_id": 2,
            "owner_id": "user_002",
            "settings": {
                "wins": 8,
                "losses": 6,
                "ties": 0,
                "fpts": 1400,
                "fpts_decimal": 75,
                "fpts_against": 1350,
                "fpts_against_decimal": 0,
            },
        },
    ]


@pytest.fixture
def mock_matchups_data():
    """Sample Sleeper matchups data."""
    return [
        {
            "roster_id": 1,
            "matchup_id": 1,
            "points": 125.5,
        },
        {
            "roster_id": 2,
            "matchup_id": 1,
            "points": 110.25,
        },
    ]


@pytest.fixture
def mock_transactions_data():
    """Sample Sleeper transactions data."""
    return [
        {
            "transaction_id": "trade_001",
            "type": "trade",
            "status": "complete",
            "roster_ids": [1, 2],
            "adds": {"player_123": 1, "player_456": 2},
            "drops": {"player_123": 2, "player_456": 1},
            "draft_picks": [],
            "created": 1700000000000,  # Timestamp in ms
        },
        {
            "transaction_id": "waiver_001",
            "type": "waiver",
            "status": "complete",
            "roster_ids": [1],
        },
    ]


@pytest.fixture
def mock_player_data():
    """Sample Sleeper player database."""
    return {
        "player_123": {
            "player_id": "player_123",
            "full_name": "Patrick Mahomes",
            "first_name": "Patrick",
            "last_name": "Mahomes",
            "position": "QB",
            "team": "KC",
        },
        "player_456": {
            "player_id": "player_456",
            "full_name": "Travis Kelce",
            "first_name": "Travis",
            "last_name": "Kelce",
            "position": "TE",
            "team": "KC",
        },
        "player_789": {
            "player_id": "player_789",
            "full_name": "Justin Jefferson",
            "first_name": "Justin",
            "last_name": "Jefferson",
            "position": "WR",
            "team": "MIN",
        },
    }


def create_mock_player_cache(mock_client: AsyncMock, player_data: dict) -> PlayerCache:
    """Create a PlayerCache with pre-loaded player data for testing.

    This avoids API calls and file operations during tests.
    """
    cache = PlayerCache(mock_client, cache_dir="/tmp/test_cache", ttl_hours=24)
    # Pre-populate the in-memory cache and mark as loaded
    cache._players = player_data
    cache._loaded = True
    return cache


# ============================================================================
# SleeperClient Tests
# ============================================================================


class TestSleeperClient:
    """Tests for the SleeperClient class."""

    def test_avatar_url_generation(self):
        """Test avatar URL generation."""
        url = SleeperClient.get_avatar_url("abc123")
        assert url == "https://sleepercdn.com/avatars/abc123"

    def test_avatar_url_none(self):
        """Test avatar URL with None returns None."""
        url = SleeperClient.get_avatar_url(None)
        assert url is None

    @pytest.mark.asyncio
    async def test_get_league(self, mock_league_data):
        """Test fetching league info."""
        client = SleeperClient()

        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_league_data
            result = await client.get_league("123456789")

            mock_get.assert_called_once_with("/league/123456789")
            assert result["name"] == "Test Fantasy League"
            assert result["total_rosters"] == 10

    @pytest.mark.asyncio
    async def test_get_users(self, mock_users_data):
        """Test fetching users."""
        client = SleeperClient()

        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_users_data
            result = await client.get_users("123456789")

            mock_get.assert_called_once_with("/league/123456789/users")
            assert len(result) == 2
            assert result[0]["username"] == "testuser1"

    @pytest.mark.asyncio
    async def test_get_rosters(self, mock_rosters_data):
        """Test fetching rosters."""
        client = SleeperClient()

        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_rosters_data
            result = await client.get_rosters("123456789")

            mock_get.assert_called_once_with("/league/123456789/rosters")
            assert len(result) == 2
            assert result[0]["settings"]["wins"] == 10

    @pytest.mark.asyncio
    async def test_get_matchups(self, mock_matchups_data):
        """Test fetching matchups."""
        client = SleeperClient()

        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_matchups_data
            result = await client.get_matchups("123456789", 1)

            mock_get.assert_called_once_with("/league/123456789/matchups/1")
            assert len(result) == 2
            assert result[0]["points"] == 125.5

    @pytest.mark.asyncio
    async def test_get_transactions(self, mock_transactions_data):
        """Test fetching transactions."""
        client = SleeperClient()

        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_transactions_data
            result = await client.get_transactions("123456789", 1)

            mock_get.assert_called_once_with("/league/123456789/transactions/1")
            assert len(result) == 2

    def test_get_previous_league_id(self):
        """Test extracting previous_league_id from league data."""
        client = SleeperClient()

        # League with previous league
        league_with_prev = {
            "league_id": "123456789",
            "name": "Test League",
            "season": "2023",
            "previous_league_id": "987654321",
        }
        assert client.get_previous_league_id(league_with_prev) == "987654321"

        # League without previous league (first season)
        league_no_prev = {
            "league_id": "123456789",
            "name": "Test League",
            "season": "2020",
            "previous_league_id": None,
        }
        assert client.get_previous_league_id(league_no_prev) is None

        # League without previous_league_id key at all
        league_no_key = {
            "league_id": "123456789",
            "name": "Test League",
            "season": "2020",
        }
        assert client.get_previous_league_id(league_no_key) is None

    @pytest.mark.asyncio
    async def test_get_league_history_chain_single_season(self):
        """Test chain traversal with single season (no history)."""
        client = SleeperClient()

        # Single season league with no previous_league_id
        mock_league = {
            "league_id": "123456789",
            "name": "Test League",
            "season": "2023",
            "previous_league_id": None,
        }

        with patch.object(client, "get_league", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_league
            chain = await client.get_league_history_chain("123456789")

            mock_get.assert_called_once_with("123456789")
            assert chain == ["123456789"]

    @pytest.mark.asyncio
    async def test_get_league_history_chain_multiple_seasons(self):
        """Test chain traversal with multiple historical seasons."""
        client = SleeperClient()

        # Three seasons: 2023 -> 2022 -> 2021
        league_2023 = {
            "league_id": "league_2023",
            "name": "Test League",
            "season": "2023",
            "previous_league_id": "league_2022",
        }
        league_2022 = {
            "league_id": "league_2022",
            "name": "Test League",
            "season": "2022",
            "previous_league_id": "league_2021",
        }
        league_2021 = {
            "league_id": "league_2021",
            "name": "Test League",
            "season": "2021",
            "previous_league_id": None,  # First season
        }

        with patch.object(client, "get_league", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [league_2023, league_2022, league_2021]
            chain = await client.get_league_history_chain("league_2023")

            assert mock_get.call_count == 3
            assert chain == ["league_2023", "league_2022", "league_2021"]

    @pytest.mark.asyncio
    async def test_get_league_history_chain_long_history(self):
        """Test chain traversal with many historical seasons."""
        client = SleeperClient()

        # Five seasons of history: 2024 -> 2023 -> 2022 -> 2021 -> 2020
        leagues = []
        for year in range(2024, 2019, -1):  # 2024, 2023, 2022, 2021, 2020
            prev_id = f"league_{year - 1}" if year > 2020 else None
            leagues.append({
                "league_id": f"league_{year}",
                "name": "Test League",
                "season": str(year),
                "previous_league_id": prev_id,
            })

        with patch.object(client, "get_league", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = leagues
            chain = await client.get_league_history_chain("league_2024")

            assert mock_get.call_count == 5
            expected = [f"league_{year}" for year in range(2024, 2019, -1)]
            assert chain == expected


# ============================================================================
# Multi-Season Historical Import Fixtures
# ============================================================================


def make_league_data(league_id: str, year: str, prev_id: Optional[str] = None) -> dict:
    """Helper to create league data for a specific year."""
    return {
        "league_id": league_id,
        "name": "Test Fantasy League",
        "season": year,
        "total_rosters": 10,
        "status": "complete",
        "scoring_settings": {"rec": 1},
        "settings": {
            "playoff_week_start": 15,
            "playoff_teams": 6,
        },
        "previous_league_id": prev_id,
    }


def make_users_data() -> list[dict]:
    """Helper to create users data."""
    return [
        {
            "user_id": "user_001",
            "username": "testuser1",
            "display_name": "Test User 1",
            "avatar": "avatar123",
        },
        {
            "user_id": "user_002",
            "username": "testuser2",
            "display_name": "Test User 2",
            "avatar": "avatar456",
        },
    ]


def make_rosters_data(year: int) -> list[dict]:
    """Helper to create rosters data with year-specific stats."""
    base_wins = 10 if year == 2023 else (8 if year == 2022 else 6)
    return [
        {
            "roster_id": 1,
            "owner_id": "user_001",
            "settings": {
                "wins": base_wins,
                "losses": 14 - base_wins,
                "ties": 0,
                "fpts": 1500 + (year - 2020) * 10,
                "fpts_decimal": 50,
                "fpts_against": 1400,
                "fpts_against_decimal": 25,
            },
        },
        {
            "roster_id": 2,
            "owner_id": "user_002",
            "settings": {
                "wins": base_wins - 2,
                "losses": 14 - base_wins + 2,
                "ties": 0,
                "fpts": 1400 + (year - 2020) * 10,
                "fpts_decimal": 75,
                "fpts_against": 1350,
                "fpts_against_decimal": 0,
            },
        },
    ]


def make_matchups_data(year: int) -> list[dict]:
    """Helper to create matchups data with year-specific scores."""
    return [
        {
            "roster_id": 1,
            "matchup_id": 1,
            "points": 125.5 + (year - 2020),
        },
        {
            "roster_id": 2,
            "matchup_id": 1,
            "points": 110.25 + (year - 2020),
        },
    ]


# ============================================================================
# SleeperService Tests
# ============================================================================


class TestSleeperService:
    """Tests for the SleeperService class."""

    @pytest.mark.asyncio
    async def test_import_league(self, db_session: Session, mock_league_data):
        """Test importing a league."""
        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league.return_value = mock_league_data

        service = SleeperService(db_session, mock_client)
        league = await service.import_league("123456789")

        assert league.name == "Test Fantasy League"
        assert league.platform == Platform.SLEEPER
        assert league.platform_league_id == "123456789"
        assert league.team_count == 10
        assert league.scoring_type == "PPR"

    @pytest.mark.asyncio
    async def test_import_league_updates_existing(
        self, db_session: Session, mock_league_data
    ):
        """Test that importing an existing league updates it."""
        # Create existing league
        existing = League(
            name="Old Name",
            platform=Platform.SLEEPER,
            platform_league_id="123456789",
        )
        db_session.add(existing)
        db_session.commit()
        existing_id = existing.id

        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league.return_value = mock_league_data

        service = SleeperService(db_session, mock_client)
        league = await service.import_league("123456789")

        assert league.id == existing_id  # Same league, not a new one
        assert league.name == "Test Fantasy League"  # Updated name

    @pytest.mark.asyncio
    async def test_import_season(
        self, db_session: Session, mock_league_data
    ):
        """Test importing a season."""
        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league.return_value = mock_league_data

        service = SleeperService(db_session, mock_client)
        season = await service.import_season("123456789")

        assert season.year == 2023
        assert season.is_complete is True
        assert season.regular_season_weeks == 14  # playoff_week_start - 1

    @pytest.mark.asyncio
    async def test_import_users_and_rosters(
        self, db_session: Session, mock_league_data, mock_users_data, mock_rosters_data
    ):
        """Test importing users and rosters as owners and teams."""
        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league.return_value = mock_league_data
        mock_client.get_users.return_value = mock_users_data
        mock_client.get_rosters.return_value = mock_rosters_data

        service = SleeperService(db_session, mock_client)
        teams = await service.import_users_and_rosters("123456789")

        assert len(teams) == 2

        # Check first team
        team1 = next(t for t in teams if t.platform_team_id == "1")
        assert team1.wins == 10
        assert team1.losses == 4
        assert team1.points_for == 1500.50  # fpts + fpts_decimal/100

        # Check owner was created
        owner = team1.owner
        assert owner.sleeper_user_id == "user_001"
        assert owner.display_name == "Test User 1"
        assert "sleepercdn.com" in owner.avatar_url

    @pytest.mark.asyncio
    async def test_import_matchups(
        self,
        db_session: Session,
        mock_league_data,
        mock_users_data,
        mock_rosters_data,
        mock_matchups_data,
    ):
        """Test importing matchups."""
        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league.return_value = mock_league_data
        mock_client.get_users.return_value = mock_users_data
        mock_client.get_rosters.return_value = mock_rosters_data
        mock_client.get_all_matchups_for_season.return_value = {
            1: mock_matchups_data,
        }

        service = SleeperService(db_session, mock_client)
        matchups = await service.import_matchups("123456789", total_weeks=1)

        assert len(matchups) == 1
        matchup = matchups[0]
        assert matchup.week == 1
        assert matchup.home_score == 125.5
        assert matchup.away_score == 110.25
        assert matchup.is_tie is False
        # Winner should be team with 125.5 points
        assert matchup.winner_team_id == matchup.home_team_id

    @pytest.mark.asyncio
    async def test_import_trades(
        self,
        db_session: Session,
        mock_league_data,
        mock_users_data,
        mock_rosters_data,
        mock_transactions_data,
        mock_player_data,
    ):
        """Test importing trades with player name resolution."""
        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league.return_value = mock_league_data
        mock_client.get_users.return_value = mock_users_data
        mock_client.get_rosters.return_value = mock_rosters_data
        # Return only trade transactions
        mock_client.get_all_trades_for_season.return_value = [
            t for t in mock_transactions_data if t.get("type") == "trade"
        ]

        # Create mock player cache with pre-populated data
        player_cache = create_mock_player_cache(mock_client, mock_player_data)

        service = SleeperService(db_session, mock_client, player_cache=player_cache)
        trades = await service.import_trades("123456789", total_weeks=1)

        assert len(trades) == 1
        trade = trades[0]
        assert trade.platform_trade_id == "trade_001"
        assert trade.status == "completed"
        assert len(trade.teams) == 2

        # Check assets_exchanged was stored with player names (not IDs)
        assets = json.loads(trade.assets_exchanged)
        assert "1" in assets or "2" in assets

        # Verify player names are resolved
        for roster_id, asset_data in assets.items():
            received = asset_data.get("received", [])
            sent = asset_data.get("sent", [])
            # Check that player names are resolved, not raw IDs
            for player_name in received + sent:
                # Should not contain raw player IDs like "player_123"
                # Instead should have "Patrick Mahomes" or "Travis Kelce"
                assert "Patrick Mahomes" in player_name or "Travis Kelce" in player_name

    @pytest.mark.asyncio
    async def test_import_full_league_single_season(
        self,
        db_session: Session,
        mock_league_data,
        mock_users_data,
        mock_rosters_data,
        mock_matchups_data,
        mock_transactions_data,
        mock_player_data,
    ):
        """Test full league import with a single season (no history)."""
        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league.return_value = mock_league_data
        mock_client.get_users.return_value = mock_users_data
        mock_client.get_rosters.return_value = mock_rosters_data
        mock_client.get_all_matchups_for_season.return_value = {1: mock_matchups_data}
        mock_client.get_all_trades_for_season.return_value = [
            t for t in mock_transactions_data if t.get("type") == "trade"
        ]
        # Single season - no previous league
        mock_client.get_league_history_chain.return_value = ["123456789"]

        # Create mock player cache
        player_cache = create_mock_player_cache(mock_client, mock_player_data)

        service = SleeperService(db_session, mock_client, player_cache=player_cache)
        result = await service.import_full_league("123456789", total_weeks=1)

        assert result["league_name"] == "Test Fantasy League"
        assert result["seasons_imported"] == 1
        assert result["seasons"][0]["season_year"] == 2023
        assert result["teams_imported"] == 2
        assert result["matchups_imported"] == 1
        assert result["trades_imported"] == 1

    @pytest.mark.asyncio
    async def test_import_full_league_multiple_seasons(
        self,
        db_session: Session,
    ):
        """Test full league import with multiple historical seasons."""
        # Create mock data for 3 seasons: 2023 -> 2022 -> 2021
        league_2023 = make_league_data("league_2023", "2023", "league_2022")
        league_2022 = make_league_data("league_2022", "2022", "league_2021")
        league_2021 = make_league_data("league_2021", "2021", None)

        users = make_users_data()

        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league_history_chain.return_value = [
            "league_2023", "league_2022", "league_2021"
        ]

        # Return different league data based on league_id
        def get_league_side_effect(league_id: str):
            if league_id == "league_2023":
                return league_2023
            elif league_id == "league_2022":
                return league_2022
            else:
                return league_2021

        mock_client.get_league.side_effect = get_league_side_effect
        mock_client.get_users.return_value = users

        # Return year-specific rosters based on the league_id
        def get_rosters_side_effect(league_id: str):
            year = int(league_id.split("_")[1])
            return make_rosters_data(year)

        mock_client.get_rosters.side_effect = get_rosters_side_effect

        # Return year-specific matchups
        def get_matchups_side_effect(league_id: str, total_weeks: int):
            year = int(league_id.split("_")[1])
            return {1: make_matchups_data(year)}

        mock_client.get_all_matchups_for_season.side_effect = get_matchups_side_effect
        mock_client.get_all_trades_for_season.return_value = []

        # Create mock player cache (empty since no trades)
        player_cache = create_mock_player_cache(mock_client, {})

        service = SleeperService(db_session, mock_client, player_cache=player_cache)
        result = await service.import_full_league("league_2023", total_weeks=1)

        # Verify all seasons were imported
        assert result["seasons_imported"] == 3
        assert result["league_name"] == "Test Fantasy League"

        # Verify totals across all seasons
        assert result["teams_imported"] == 6  # 2 teams x 3 seasons
        assert result["matchups_imported"] == 3  # 1 matchup x 3 seasons

        # Verify each season was imported with correct year
        season_years = [s["season_year"] for s in result["seasons"]]
        assert 2023 in season_years
        assert 2022 in season_years
        assert 2021 in season_years

        # Verify database has the right number of seasons
        seasons = db_session.query(Season).all()
        assert len(seasons) == 3

        # Verify only ONE league record (not 3)
        leagues = db_session.query(League).all()
        assert len(leagues) == 1
        assert leagues[0].name == "Test Fantasy League"

    @pytest.mark.asyncio
    async def test_import_full_league_idempotent(
        self,
        db_session: Session,
    ):
        """Test that re-importing the same league doesn't create duplicates."""
        # Single season for simplicity
        league_data = make_league_data("league_2023", "2023", None)
        users = make_users_data()
        rosters = make_rosters_data(2023)
        matchups = make_matchups_data(2023)

        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league_history_chain.return_value = ["league_2023"]
        mock_client.get_league.return_value = league_data
        mock_client.get_users.return_value = users
        mock_client.get_rosters.return_value = rosters
        mock_client.get_all_matchups_for_season.return_value = {1: matchups}
        mock_client.get_all_trades_for_season.return_value = []

        # Create mock player cache (empty since no trades)
        player_cache = create_mock_player_cache(mock_client, {})

        service = SleeperService(db_session, mock_client, player_cache=player_cache)

        # First import
        result1 = await service.import_full_league("league_2023", total_weeks=1)

        # Record counts after first import
        leagues_count_1 = db_session.query(League).count()
        seasons_count_1 = db_session.query(Season).count()
        teams_count_1 = db_session.query(Team).count()
        matchups_count_1 = db_session.query(Matchup).count()
        owners_count_1 = db_session.query(Owner).count()

        # Second import (same league)
        result2 = await service.import_full_league("league_2023", total_weeks=1)

        # Record counts after second import should be identical
        leagues_count_2 = db_session.query(League).count()
        seasons_count_2 = db_session.query(Season).count()
        teams_count_2 = db_session.query(Team).count()
        matchups_count_2 = db_session.query(Matchup).count()
        owners_count_2 = db_session.query(Owner).count()

        # Verify no duplicates were created
        assert leagues_count_1 == leagues_count_2 == 1
        assert seasons_count_1 == seasons_count_2 == 1
        assert teams_count_1 == teams_count_2 == 2
        assert matchups_count_1 == matchups_count_2 == 1
        assert owners_count_1 == owners_count_2 == 2

        # Both imports should return same data
        assert result1["seasons_imported"] == result2["seasons_imported"]
        assert result1["teams_imported"] == result2["teams_imported"]

    @pytest.mark.asyncio
    async def test_import_full_league_multiple_seasons_idempotent(
        self,
        db_session: Session,
    ):
        """Test that re-importing multiple seasons doesn't create duplicates."""
        # Create mock data for 2 seasons: 2023 -> 2022
        league_2023 = make_league_data("league_2023", "2023", "league_2022")
        league_2022 = make_league_data("league_2022", "2022", None)

        users = make_users_data()

        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league_history_chain.return_value = ["league_2023", "league_2022"]

        def get_league_side_effect(league_id: str):
            if league_id == "league_2023":
                return league_2023
            return league_2022

        mock_client.get_league.side_effect = get_league_side_effect
        mock_client.get_users.return_value = users

        def get_rosters_side_effect(league_id: str):
            year = int(league_id.split("_")[1])
            return make_rosters_data(year)

        mock_client.get_rosters.side_effect = get_rosters_side_effect

        def get_matchups_side_effect(league_id: str, total_weeks: int):
            year = int(league_id.split("_")[1])
            return {1: make_matchups_data(year)}

        mock_client.get_all_matchups_for_season.side_effect = get_matchups_side_effect
        mock_client.get_all_trades_for_season.return_value = []

        # Create mock player cache (empty since no trades)
        player_cache = create_mock_player_cache(mock_client, {})

        service = SleeperService(db_session, mock_client, player_cache=player_cache)

        # First import
        await service.import_full_league("league_2023", total_weeks=1)

        # Record counts after first import
        leagues_count_1 = db_session.query(League).count()
        seasons_count_1 = db_session.query(Season).count()
        teams_count_1 = db_session.query(Team).count()
        owners_count_1 = db_session.query(Owner).count()

        # Second import (should not create duplicates)
        await service.import_full_league("league_2023", total_weeks=1)

        # Record counts should be unchanged
        leagues_count_2 = db_session.query(League).count()
        seasons_count_2 = db_session.query(Season).count()
        teams_count_2 = db_session.query(Team).count()
        owners_count_2 = db_session.query(Owner).count()

        assert leagues_count_1 == leagues_count_2 == 1  # Only ONE league
        assert seasons_count_1 == seasons_count_2 == 2  # 2 seasons
        assert teams_count_1 == teams_count_2 == 4  # 2 teams x 2 seasons
        assert owners_count_1 == owners_count_2 == 2  # Only 2 unique owners


# ============================================================================
# API Endpoint Tests
# ============================================================================


class TestSleeperEndpoints:
    """Tests for Sleeper API endpoints."""

    def test_get_league_info(self, test_client: TestClient, mock_league_data):
        """Test GET /api/sleeper/league/{league_id}."""
        with patch(
            "app.services.sleeper_client.SleeperClient.get_league",
            new_callable=AsyncMock,
            return_value=mock_league_data,
        ):
            response = test_client.get("/api/sleeper/league/123456789")

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Fantasy League"
            assert data["scoring_type"] == "PPR"

    def test_get_league_users(self, test_client: TestClient, mock_users_data):
        """Test GET /api/sleeper/league/{league_id}/users."""
        with patch(
            "app.services.sleeper_client.SleeperClient.get_users",
            new_callable=AsyncMock,
            return_value=mock_users_data,
        ):
            response = test_client.get("/api/sleeper/league/123456789/users")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["user_id"] == "user_001"

    def test_get_league_rosters(self, test_client: TestClient, mock_rosters_data):
        """Test GET /api/sleeper/league/{league_id}/rosters."""
        with patch(
            "app.services.sleeper_client.SleeperClient.get_rosters",
            new_callable=AsyncMock,
            return_value=mock_rosters_data,
        ):
            response = test_client.get("/api/sleeper/league/123456789/rosters")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["wins"] == 10

    def test_get_league_matchups(self, test_client: TestClient, mock_matchups_data):
        """Test GET /api/sleeper/league/{league_id}/matchups/{week}."""
        with patch(
            "app.services.sleeper_client.SleeperClient.get_matchups",
            new_callable=AsyncMock,
            return_value=mock_matchups_data,
        ):
            response = test_client.get("/api/sleeper/league/123456789/matchups/1")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["points"] == 125.5

    def test_get_league_trades(self, test_client: TestClient, mock_transactions_data):
        """Test GET /api/sleeper/league/{league_id}/trades/{week}."""
        with patch(
            "app.services.sleeper_client.SleeperClient.get_transactions",
            new_callable=AsyncMock,
            return_value=mock_transactions_data,
        ):
            response = test_client.get("/api/sleeper/league/123456789/trades/1")

            assert response.status_code == 200
            data = response.json()
            # Should only return trades, not waivers
            assert len(data) == 1
            assert data[0]["transaction_id"] == "trade_001"

    def test_import_league(
        self,
        test_client: TestClient,
        mock_league_data,
        mock_users_data,
        mock_rosters_data,
        mock_matchups_data,
        mock_transactions_data,
    ):
        """Test POST /api/sleeper/import."""
        with patch.object(
            SleeperService,
            "import_full_league",
            new_callable=AsyncMock,
            return_value={
                "league_id": 1,
                "league_name": "Test Fantasy League",
                "season_year": 2023,
                "teams_imported": 2,
                "matchups_imported": 14,
                "trades_imported": 5,
            },
        ):
            response = test_client.post(
                "/api/sleeper/import",
                json={"league_id": "123456789"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["league_name"] == "Test Fantasy League"
            assert data["teams_imported"] == 2


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_import_roster_without_owner(
        self, db_session: Session, mock_league_data, mock_users_data
    ):
        """Test importing roster without an owner_id."""
        roster_without_owner = [
            {
                "roster_id": 1,
                "owner_id": None,  # No owner
                "settings": {"wins": 0, "losses": 0, "ties": 0, "fpts": 0},
            }
        ]

        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league.return_value = mock_league_data
        mock_client.get_users.return_value = mock_users_data
        mock_client.get_rosters.return_value = roster_without_owner

        service = SleeperService(db_session, mock_client)
        teams = await service.import_users_and_rosters("123456789")

        # Should skip rosters without owner_id
        assert len(teams) == 0

    @pytest.mark.asyncio
    async def test_import_matchup_with_tie(
        self,
        db_session: Session,
        mock_league_data,
        mock_users_data,
        mock_rosters_data,
    ):
        """Test importing a tied matchup."""
        tied_matchup = [
            {"roster_id": 1, "matchup_id": 1, "points": 100.0},
            {"roster_id": 2, "matchup_id": 1, "points": 100.0},
        ]

        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league.return_value = mock_league_data
        mock_client.get_users.return_value = mock_users_data
        mock_client.get_rosters.return_value = mock_rosters_data
        mock_client.get_all_matchups_for_season.return_value = {1: tied_matchup}

        service = SleeperService(db_session, mock_client)
        matchups = await service.import_matchups("123456789", total_weeks=1)

        assert len(matchups) == 1
        assert matchups[0].is_tie is True
        assert matchups[0].winner_team_id is None

    def test_scoring_type_half_ppr(self, db_session: Session):
        """Test scoring type detection for Half PPR."""
        half_ppr_league = {
            "league_id": "123",
            "name": "Half PPR League",
            "season": "2023",
            "total_rosters": 10,
            "status": "complete",
            "scoring_settings": {"rec": 0.5},  # Half PPR
            "settings": {},
        }

        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league.return_value = half_ppr_league

        service = SleeperService(db_session, mock_client)

        import asyncio
        league = asyncio.get_event_loop().run_until_complete(
            service.import_league("123")
        )

        assert league.scoring_type == "Half PPR"

    def test_scoring_type_standard(self, db_session: Session):
        """Test scoring type detection for Standard."""
        standard_league = {
            "league_id": "123",
            "name": "Standard League",
            "season": "2023",
            "total_rosters": 10,
            "status": "complete",
            "scoring_settings": {"rec": 0},  # Standard
            "settings": {},
        }

        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league.return_value = standard_league

        service = SleeperService(db_session, mock_client)

        import asyncio
        league = asyncio.get_event_loop().run_until_complete(
            service.import_league("123")
        )

        assert league.scoring_type == "Standard"


# ============================================================================
# Player Cache Test Fixtures
# ============================================================================


@pytest.fixture
def mock_players_data():
    """Sample Sleeper players data (subset of actual response)."""
    return {
        "4046": {
            "player_id": "4046",
            "full_name": "Davante Adams",
            "first_name": "Davante",
            "last_name": "Adams",
            "team": "LV",
            "position": "WR",
            "status": "Active",
        },
        "4981": {
            "player_id": "4981",
            "full_name": "Tyreek Hill",
            "first_name": "Tyreek",
            "last_name": "Hill",
            "team": "MIA",
            "position": "WR",
            "status": "Active",
        },
        "6794": {
            "player_id": "6794",
            "full_name": "Justin Jefferson",
            "first_name": "Justin",
            "last_name": "Jefferson",
            "team": "MIN",
            "position": "WR",
            "status": "Active",
        },
        "9999": {
            "player_id": "9999",
            "full_name": None,  # Some players may have null names
            "first_name": "Unknown",
            "last_name": "Player",
            "team": None,
            "position": "DEF",
        },
    }


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ============================================================================
# Player Cache Tests
# ============================================================================


class TestPlayerCache:
    """Tests for the PlayerCache class."""

    @pytest.mark.asyncio
    async def test_fetch_players_from_api(self, mock_players_data, temp_cache_dir):
        """Test fetching players from Sleeper API."""
        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_players.return_value = mock_players_data

        cache = PlayerCache(
            client=mock_client,
            cache_dir=temp_cache_dir,
            ttl_hours=24,
        )

        players = await cache.fetch_players()

        mock_client.get_players.assert_called_once()
        assert len(players) == 4
        assert "4046" in players
        assert players["4046"]["full_name"] == "Davante Adams"

    @pytest.mark.asyncio
    async def test_players_cached_to_file(self, mock_players_data, temp_cache_dir):
        """Test that players are cached to a file after fetching."""
        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_players.return_value = mock_players_data

        cache = PlayerCache(
            client=mock_client,
            cache_dir=temp_cache_dir,
            ttl_hours=24,
        )

        await cache.fetch_players()

        # Verify cache file was created
        cache_file = os.path.join(temp_cache_dir, "sleeper_players.json")
        assert os.path.exists(cache_file)

        # Verify cache contents
        with open(cache_file, "r") as f:
            cached_data = json.load(f)
        assert "data" in cached_data
        assert "timestamp" in cached_data
        assert cached_data["data"]["4046"]["full_name"] == "Davante Adams"

    @pytest.mark.asyncio
    async def test_players_loaded_from_cache(self, mock_players_data, temp_cache_dir):
        """Test that players are loaded from cache when not expired."""
        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_players.return_value = mock_players_data

        cache = PlayerCache(
            client=mock_client,
            cache_dir=temp_cache_dir,
            ttl_hours=24,
        )

        # First fetch - hits API
        await cache.fetch_players()
        assert mock_client.get_players.call_count == 1

        # Second fetch - should use cache
        cache2 = PlayerCache(
            client=mock_client,
            cache_dir=temp_cache_dir,
            ttl_hours=24,
        )
        players = await cache2.fetch_players()
        # Should still be 1, no additional API call
        assert mock_client.get_players.call_count == 1
        assert players["4046"]["full_name"] == "Davante Adams"

    @pytest.mark.asyncio
    async def test_cache_expires_after_ttl(self, mock_players_data, temp_cache_dir):
        """Test that cache is refreshed after TTL expires."""
        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_players.return_value = mock_players_data

        cache = PlayerCache(
            client=mock_client,
            cache_dir=temp_cache_dir,
            ttl_hours=0,  # 0 hours = immediately expired
        )

        # First fetch
        await cache.fetch_players()
        assert mock_client.get_players.call_count == 1

        # Modify cache file timestamp to be in the past
        cache_file = os.path.join(temp_cache_dir, "sleeper_players.json")
        with open(cache_file, "r") as f:
            cached_data = json.load(f)
        cached_data["timestamp"] = time.time() - 3600  # 1 hour ago
        with open(cache_file, "w") as f:
            json.dump(cached_data, f)

        # Second fetch - should hit API since TTL is 0
        cache2 = PlayerCache(
            client=mock_client,
            cache_dir=temp_cache_dir,
            ttl_hours=0,
        )
        await cache2.fetch_players()
        assert mock_client.get_players.call_count == 2

    def test_get_player_name(self, mock_players_data, temp_cache_dir):
        """Test looking up player name by ID."""
        mock_client = MagicMock(spec=SleeperClient)

        cache = PlayerCache(
            client=mock_client,
            cache_dir=temp_cache_dir,
            ttl_hours=24,
        )

        # Manually set the cached players
        cache._players = mock_players_data

        assert cache.get_player_name("4046") == "Davante Adams"
        assert cache.get_player_name("4981") == "Tyreek Hill"
        assert cache.get_player_name("6794") == "Justin Jefferson"

    def test_get_player_name_fallback(self, mock_players_data, temp_cache_dir):
        """Test player name lookup with fallback to first/last name."""
        mock_client = MagicMock(spec=SleeperClient)

        cache = PlayerCache(
            client=mock_client,
            cache_dir=temp_cache_dir,
            ttl_hours=24,
        )

        cache._players = mock_players_data

        # Player with null full_name should fallback to first/last
        assert cache.get_player_name("9999") == "Unknown Player"

    def test_get_player_name_unknown(self, temp_cache_dir):
        """Test player name lookup for unknown player ID."""
        mock_client = MagicMock(spec=SleeperClient)

        cache = PlayerCache(
            client=mock_client,
            cache_dir=temp_cache_dir,
            ttl_hours=24,
        )

        cache._players = {}

        # Unknown player should return the ID itself
        assert cache.get_player_name("999999") == "Player 999999"

    @pytest.mark.asyncio
    async def test_force_refresh(self, mock_players_data, temp_cache_dir):
        """Test force refresh ignores cache and fetches from API."""
        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_players.return_value = mock_players_data

        cache = PlayerCache(
            client=mock_client,
            cache_dir=temp_cache_dir,
            ttl_hours=24,
        )

        # First fetch
        await cache.fetch_players()
        assert mock_client.get_players.call_count == 1

        # Force refresh - should hit API again
        await cache.fetch_players(force_refresh=True)
        assert mock_client.get_players.call_count == 2

    def test_get_player_info(self, mock_players_data, temp_cache_dir):
        """Test getting full player info by ID."""
        mock_client = MagicMock(spec=SleeperClient)

        cache = PlayerCache(
            client=mock_client,
            cache_dir=temp_cache_dir,
            ttl_hours=24,
        )

        cache._players = mock_players_data

        player = cache.get_player("4046")
        assert player is not None
        assert player["full_name"] == "Davante Adams"
        assert player["team"] == "LV"
        assert player["position"] == "WR"

        # Unknown player should return None
        assert cache.get_player("999999") is None


# ============================================================================
# SleeperClient get_players Tests
# ============================================================================


class TestSleeperClientPlayers:
    """Tests for SleeperClient.get_players method."""

    @pytest.mark.asyncio
    async def test_get_players(self, mock_players_data):
        """Test fetching all NFL players from Sleeper API."""
        client = SleeperClient()

        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_players_data
            result = await client.get_players()

            mock_get.assert_called_once_with("/players/nfl")
            assert len(result) == 4
            assert result["4046"]["full_name"] == "Davante Adams"
