"""Tests for Sleeper API integration.

Tests cover:
- SleeperClient API calls
- SleeperService database operations
- API endpoint functionality
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import League, Season, Team, Owner, Matchup, Trade, Platform
from app.services.sleeper_client import SleeperClient
from app.services.sleeper_service import SleeperService


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
    ):
        """Test importing trades."""
        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league.return_value = mock_league_data
        mock_client.get_users.return_value = mock_users_data
        mock_client.get_rosters.return_value = mock_rosters_data
        # Return only trade transactions
        mock_client.get_all_trades_for_season.return_value = [
            t for t in mock_transactions_data if t.get("type") == "trade"
        ]

        service = SleeperService(db_session, mock_client)
        trades = await service.import_trades("123456789", total_weeks=1)

        assert len(trades) == 1
        trade = trades[0]
        assert trade.platform_trade_id == "trade_001"
        assert trade.status == "completed"
        assert len(trade.teams) == 2

        # Check assets_exchanged was stored
        assets = json.loads(trade.assets_exchanged)
        assert "1" in assets or "2" in assets

    @pytest.mark.asyncio
    async def test_import_full_league(
        self,
        db_session: Session,
        mock_league_data,
        mock_users_data,
        mock_rosters_data,
        mock_matchups_data,
        mock_transactions_data,
    ):
        """Test full league import."""
        mock_client = AsyncMock(spec=SleeperClient)
        mock_client.get_league.return_value = mock_league_data
        mock_client.get_users.return_value = mock_users_data
        mock_client.get_rosters.return_value = mock_rosters_data
        mock_client.get_all_matchups_for_season.return_value = {1: mock_matchups_data}
        mock_client.get_all_trades_for_season.return_value = [
            t for t in mock_transactions_data if t.get("type") == "trade"
        ]

        service = SleeperService(db_session, mock_client)
        result = await service.import_full_league("123456789", total_weeks=1)

        assert result["league_name"] == "Test Fantasy League"
        assert result["season_year"] == 2023
        assert result["teams_imported"] == 2
        assert result["matchups_imported"] == 1
        assert result["trades_imported"] == 1


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
