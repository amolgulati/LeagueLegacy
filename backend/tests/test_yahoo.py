"""Tests for Yahoo Fantasy API integration.

Tests cover:
- YahooClient OAuth2 authentication flow
- YahooClient API methods
- YahooService database import
- Yahoo API endpoints
"""

import json
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from httpx import Response, HTTPStatusError, Request

from app.services.yahoo_client import (
    YahooClient,
    YahooToken,
    YahooAuthError,
    YahooAPIError,
)
from app.services.yahoo_service import YahooService
from app.db.models import League, Season, Team, Owner, Matchup, Trade, Platform


# ============= Fixtures =============

@pytest.fixture
def yahoo_client():
    """Create a YahooClient instance for testing."""
    return YahooClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
    )


@pytest.fixture
def mock_token():
    """Create a mock OAuth token."""
    return YahooToken(
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_type="bearer",
        expires_in=3600,
        expires_at=time.time() + 3600,
    )


@pytest.fixture
def expired_token():
    """Create an expired OAuth token."""
    return YahooToken(
        access_token="expired_access_token",
        refresh_token="test_refresh_token",
        token_type="bearer",
        expires_in=3600,
        expires_at=time.time() - 100,  # Expired
    )


@pytest.fixture
def mock_league_response():
    """Mock Yahoo league API response."""
    return {
        "fantasy_content": {
            "league": [
                {
                    "league_key": "449.l.123456",
                    "league_id": "123456",
                    "name": "Test League",
                    "num_teams": 12,
                    "scoring_type": "head",
                    "season": "2024",
                    "current_week": 10,
                    "start_week": 1,
                    "end_week": 17,
                    "is_finished": 0,
                }
            ]
        }
    }


@pytest.fixture
def mock_standings_response():
    """Mock Yahoo standings API response."""
    return {
        "fantasy_content": {
            "league": [
                {},
                {
                    "standings": [
                        {
                            "teams": {
                                "0": {
                                    "team": [
                                        {
                                            "team_key": "449.l.123456.t.1",
                                            "team_id": "1",
                                            "name": "Team One",
                                            "managers": [
                                                {
                                                    "manager": {
                                                        "manager_id": "1",
                                                        "guid": "user_guid_1",
                                                        "nickname": "Player One",
                                                        "image_url": "https://example.com/avatar1.png",
                                                    }
                                                }
                                            ],
                                            "team_standings": {
                                                "rank": 1,
                                                "points_for": 1500.5,
                                                "points_against": 1200.3,
                                                "outcome_totals": {
                                                    "wins": 8,
                                                    "losses": 2,
                                                    "ties": 0,
                                                },
                                                "playoff_seed": 1,
                                            },
                                        }
                                    ]
                                },
                                "1": {
                                    "team": [
                                        {
                                            "team_key": "449.l.123456.t.2",
                                            "team_id": "2",
                                            "name": "Team Two",
                                            "managers": [
                                                {
                                                    "manager": {
                                                        "manager_id": "2",
                                                        "guid": "user_guid_2",
                                                        "nickname": "Player Two",
                                                    }
                                                }
                                            ],
                                            "team_standings": {
                                                "rank": 2,
                                                "points_for": 1400.2,
                                                "points_against": 1300.1,
                                                "outcome_totals": {
                                                    "wins": 7,
                                                    "losses": 3,
                                                    "ties": 0,
                                                },
                                            },
                                        }
                                    ]
                                },
                            }
                        }
                    ]
                },
            ]
        }
    }


@pytest.fixture
def mock_matchups_response():
    """Mock Yahoo matchups/scoreboard API response."""
    return {
        "fantasy_content": {
            "league": [
                {},
                {
                    "scoreboard": {
                        "0": {
                            "matchups": {
                                "0": {
                                    "matchup": [
                                        {
                                            "week": 1,
                                            "is_playoffs": "0",
                                            "is_consolation": "0",
                                            "is_tied": "0",
                                            "winner_team_key": "449.l.123456.t.1",
                                        },
                                        {
                                            "0": {
                                                "teams": {
                                                    "0": {
                                                        "team": [
                                                            {
                                                                "team_key": "449.l.123456.t.1",
                                                                "team_id": "1",
                                                                "name": "Team One",
                                                                "team_points": {
                                                                    "total": 150.5,
                                                                },
                                                            }
                                                        ]
                                                    },
                                                    "1": {
                                                        "team": [
                                                            {
                                                                "team_key": "449.l.123456.t.2",
                                                                "team_id": "2",
                                                                "name": "Team Two",
                                                                "team_points": {
                                                                    "total": 120.3,
                                                                },
                                                            }
                                                        ]
                                                    },
                                                }
                                            }
                                        },
                                    ]
                                }
                            }
                        }
                    }
                },
            ]
        }
    }


@pytest.fixture
def mock_trades_response():
    """Mock Yahoo trades/transactions API response."""
    return {
        "fantasy_content": {
            "league": [
                {},
                {
                    "transactions": {
                        "0": {
                            "transaction": [
                                {
                                    "transaction_key": "449.l.123456.tr.1",
                                    "type": "trade",
                                    "status": "successful",
                                    "timestamp": 1699000000,
                                    "trader_team_key": "449.l.123456.t.1",
                                    "tradee_team_key": "449.l.123456.t.2",
                                },
                                {
                                    "players": {
                                        "0": {
                                            "player": [
                                                {
                                                    "player_key": "449.p.12345",
                                                    "player_id": "12345",
                                                    "name": {"full": "Test Player"},
                                                },
                                                {
                                                    "transaction_data": {
                                                        "source_team_key": "449.l.123456.t.1",
                                                        "destination_team_key": "449.l.123456.t.2",
                                                        "source_type": "team",
                                                        "destination_type": "team",
                                                    }
                                                },
                                            ]
                                        }
                                    }
                                },
                            ]
                        }
                    }
                },
            ]
        }
    }


# ============= YahooToken Tests =============

class TestYahooToken:
    """Tests for YahooToken class."""

    def test_token_not_expired(self, mock_token):
        """Test token is not expired when expires_at is in the future."""
        assert not mock_token.is_expired()

    def test_token_expired(self, expired_token):
        """Test token is expired when expires_at is in the past."""
        assert expired_token.is_expired()

    def test_token_to_dict(self, mock_token):
        """Test token serialization to dictionary."""
        token_dict = mock_token.to_dict()

        assert token_dict["access_token"] == "test_access_token"
        assert token_dict["refresh_token"] == "test_refresh_token"
        assert token_dict["token_type"] == "bearer"
        assert token_dict["expires_in"] == 3600

    def test_token_from_dict(self):
        """Test token deserialization from dictionary."""
        token_dict = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "token_type": "bearer",
            "expires_in": 7200,
            "expires_at": time.time() + 7200,
        }

        token = YahooToken.from_dict(token_dict)

        assert token.access_token == "new_access_token"
        assert token.refresh_token == "new_refresh_token"
        assert token.expires_in == 7200


# ============= YahooClient Tests =============

class TestYahooClient:
    """Tests for YahooClient class."""

    def test_client_initialization(self, yahoo_client):
        """Test client initializes with provided credentials."""
        assert yahoo_client.client_id == "test_client_id"
        assert yahoo_client.client_secret == "test_client_secret"
        assert not yahoo_client.is_authenticated

    def test_client_from_environment(self):
        """Test client reads credentials from environment."""
        with patch.dict("os.environ", {
            "YAHOO_CLIENT_ID": "env_client_id",
            "YAHOO_CLIENT_SECRET": "env_client_secret",
        }):
            client = YahooClient()
            assert client.client_id == "env_client_id"
            assert client.client_secret == "env_client_secret"

    def test_get_authorization_url(self, yahoo_client):
        """Test authorization URL generation."""
        url = yahoo_client.get_authorization_url(state="test_state")

        assert "api.login.yahoo.com/oauth2/request_auth" in url
        assert "client_id=test_client_id" in url
        assert "response_type=code" in url
        assert "state=test_state" in url

    def test_set_token(self, yahoo_client, mock_token):
        """Test setting token directly."""
        yahoo_client.set_token(mock_token)

        assert yahoo_client.is_authenticated
        assert yahoo_client.get_token() == mock_token

    def test_set_token_from_dict(self, yahoo_client):
        """Test setting token from dictionary."""
        token_dict = {
            "access_token": "dict_access_token",
            "refresh_token": "dict_refresh_token",
            "token_type": "bearer",
            "expires_in": 3600,
            "expires_at": time.time() + 3600,
        }

        yahoo_client.set_token_from_dict(token_dict)

        assert yahoo_client.is_authenticated
        assert yahoo_client.get_token().access_token == "dict_access_token"

    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self, yahoo_client):
        """Test token exchange from authorization code."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "exchanged_access_token",
            "refresh_token": "exchanged_refresh_token",
            "token_type": "bearer",
            "expires_in": 3600,
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            token = await yahoo_client.exchange_code_for_token("auth_code")

            assert token.access_token == "exchanged_access_token"
            assert yahoo_client.is_authenticated

    @pytest.mark.asyncio
    async def test_exchange_code_failure(self, yahoo_client):
        """Test token exchange failure raises YahooAuthError."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid code"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(YahooAuthError) as exc_info:
                await yahoo_client.exchange_code_for_token("invalid_code")

            assert "Token exchange failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refresh_access_token(self, yahoo_client, mock_token):
        """Test refreshing access token."""
        yahoo_client.set_token(mock_token)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "refreshed_access_token",
            "refresh_token": "new_refresh_token",
            "token_type": "bearer",
            "expires_in": 3600,
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            new_token = await yahoo_client.refresh_access_token()

            assert new_token.access_token == "refreshed_access_token"

    @pytest.mark.asyncio
    async def test_refresh_without_token_raises_error(self, yahoo_client):
        """Test refresh without token raises YahooAuthError."""
        with pytest.raises(YahooAuthError) as exc_info:
            await yahoo_client.refresh_access_token()

        assert "No refresh token available" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_league(self, yahoo_client, mock_token, mock_league_response):
        """Test fetching league information."""
        yahoo_client.set_token(mock_token)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_league_response

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            league = await yahoo_client.get_league("449.l.123456")

            assert league["league_key"] == "449.l.123456"
            assert league["name"] == "Test League"
            assert league["num_teams"] == 12

    @pytest.mark.asyncio
    async def test_get_standings(self, yahoo_client, mock_token, mock_standings_response):
        """Test fetching league standings."""
        yahoo_client.set_token(mock_token)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_standings_response

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            standings = await yahoo_client.get_standings("449.l.123456")

            assert len(standings) == 2
            assert standings[0]["name"] == "Team One"
            assert standings[0]["wins"] == 8
            assert standings[0]["rank"] == 1

    @pytest.mark.asyncio
    async def test_get_matchups(self, yahoo_client, mock_token, mock_matchups_response):
        """Test fetching matchups."""
        yahoo_client.set_token(mock_token)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_matchups_response

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            matchups = await yahoo_client.get_matchups("449.l.123456", week=1)

            assert len(matchups) == 1
            assert matchups[0]["week"] == 1
            assert len(matchups[0]["teams"]) == 2

    @pytest.mark.asyncio
    async def test_get_trades(self, yahoo_client, mock_token, mock_trades_response):
        """Test fetching trades."""
        yahoo_client.set_token(mock_token)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_trades_response

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            trades = await yahoo_client.get_trades("449.l.123456")

            assert len(trades) == 1
            assert trades[0]["transaction_id"] == "449.l.123456.tr.1"

    @pytest.mark.asyncio
    async def test_api_error_without_auth(self, yahoo_client):
        """Test API call without authentication raises error."""
        with pytest.raises(YahooAuthError):
            await yahoo_client.get_league("449.l.123456")


# ============= YahooService Tests =============

class TestYahooService:
    """Tests for YahooService class."""

    @pytest.fixture
    def yahoo_service(self, db_session, yahoo_client, mock_token):
        """Create a YahooService instance for testing."""
        yahoo_client.set_token(mock_token)
        return YahooService(db_session, yahoo_client)

    @pytest.mark.asyncio
    async def test_import_league(self, yahoo_service, mock_league_response):
        """Test importing a league from Yahoo."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_league_response

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            league = await yahoo_service.import_league("449.l.123456")

            assert league.name == "Test League"
            assert league.platform == Platform.YAHOO
            assert league.platform_league_id == "449.l.123456"
            assert league.team_count == 12

    @pytest.mark.asyncio
    async def test_import_season(self, yahoo_service, mock_league_response):
        """Test importing a season from Yahoo."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_league_response

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            season = await yahoo_service.import_season("449.l.123456")

            assert season.year == 2024
            assert season.league is not None

    @pytest.mark.asyncio
    async def test_import_standings(
        self, yahoo_service, mock_league_response, mock_standings_response
    ):
        """Test importing standings from Yahoo."""
        def mock_get_response(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200

            url = args[0] if args else kwargs.get("url", "")
            if "standings" in url:
                mock_response.json.return_value = mock_standings_response
            else:
                mock_response.json.return_value = mock_league_response

            return mock_response

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = mock_get_response

            teams = await yahoo_service.import_standings("449.l.123456")

            assert len(teams) == 2
            assert teams[0].name == "Team One"
            assert teams[0].wins == 8
            assert teams[0].owner is not None
            assert teams[0].owner.yahoo_user_id == "user_guid_1"

    @pytest.mark.asyncio
    async def test_import_creates_owners(
        self, yahoo_service, mock_league_response, mock_standings_response
    ):
        """Test that importing creates owner records."""
        def mock_get_response(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200

            url = args[0] if args else kwargs.get("url", "")
            if "standings" in url:
                mock_response.json.return_value = mock_standings_response
            else:
                mock_response.json.return_value = mock_league_response

            return mock_response

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = mock_get_response

            teams = await yahoo_service.import_standings("449.l.123456")

            # Check owners were created
            owners = yahoo_service.db.query(Owner).all()
            assert len(owners) == 2
            assert any(o.yahoo_user_id == "user_guid_1" for o in owners)
            assert any(o.yahoo_user_id == "user_guid_2" for o in owners)


# ============= API Endpoint Tests =============

class TestYahooAPIEndpoints:
    """Tests for Yahoo API endpoints."""

    def test_get_auth_url(self, test_client):
        """Test getting OAuth2 authorization URL."""
        response = test_client.get("/api/yahoo/auth/url?state=test_state")

        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "state" in data
        assert data["state"] == "test_state"

    def test_auth_status_not_authenticated(self, test_client):
        """Test auth status when not authenticated."""
        response = test_client.get("/api/yahoo/auth/status?session_id=test_session")

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False

    def test_set_token(self, test_client):
        """Test setting token directly."""
        token_data = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "bearer",
            "expires_in": 3600,
        }

        response = test_client.post(
            "/api/yahoo/auth/set-token?session_id=test_session",
            json=token_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True

    def test_get_league_not_authenticated(self, test_client):
        """Test getting league info when not authenticated."""
        response = test_client.get(
            "/api/yahoo/league/449.l.123456?session_id=unauth_session"
        )

        assert response.status_code == 401

    def test_logout(self, test_client):
        """Test logout clears token."""
        # First set a token
        token_data = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }
        test_client.post(
            "/api/yahoo/auth/set-token?session_id=logout_session",
            json=token_data,
        )

        # Then logout
        response = test_client.delete(
            "/api/yahoo/auth/logout?session_id=logout_session"
        )

        assert response.status_code == 200

        # Verify logged out
        status_response = test_client.get(
            "/api/yahoo/auth/status?session_id=logout_session"
        )
        assert status_response.json()["authenticated"] is False

    def test_import_league_not_authenticated(self, test_client):
        """Test import league when not authenticated."""
        response = test_client.post(
            "/api/yahoo/import?session_id=unauth_import",
            json={"league_key": "449.l.123456"},
        )

        assert response.status_code == 401
