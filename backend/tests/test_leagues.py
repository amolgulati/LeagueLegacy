"""Tests for the Leagues API endpoints."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.models import League, Season, Team, Matchup, Trade, Owner, Platform


@pytest.fixture
def test_owner(db_session: Session) -> Owner:
    """Create a test owner."""
    owner = Owner(name="Test Owner", display_name="Test Display")
    db_session.add(owner)
    db_session.commit()
    db_session.refresh(owner)
    return owner


@pytest.fixture
def test_league(db_session: Session) -> League:
    """Create a test league."""
    league = League(
        name="Test League",
        platform=Platform.SLEEPER,
        platform_league_id="123456789",
        team_count=12,
        scoring_type="PPR"
    )
    db_session.add(league)
    db_session.commit()
    db_session.refresh(league)
    return league


@pytest.fixture
def test_league_with_data(db_session: Session, test_owner: Owner) -> League:
    """Create a test league with seasons, teams, matchups, and trades."""
    # Create league
    league = League(
        name="Test League With Data",
        platform=Platform.SLEEPER,
        platform_league_id="987654321",
        team_count=10,
        scoring_type="Half PPR"
    )
    db_session.add(league)
    db_session.commit()
    db_session.refresh(league)

    # Create a season
    season = Season(
        league_id=league.id,
        year=2024,
        regular_season_weeks=14,
        playoff_weeks=3,
        is_complete=True
    )
    db_session.add(season)
    db_session.commit()
    db_session.refresh(season)

    # Create teams
    team1 = Team(
        season_id=season.id,
        owner_id=test_owner.id,
        name="Team 1",
        platform_team_id="t1",
        wins=10,
        losses=4,
        points_for=1500.5,
        made_playoffs=True
    )
    team2 = Team(
        season_id=season.id,
        owner_id=test_owner.id,
        name="Team 2",
        platform_team_id="t2",
        wins=8,
        losses=6,
        points_for=1400.0,
        made_playoffs=True
    )
    db_session.add_all([team1, team2])
    db_session.commit()
    db_session.refresh(team1)
    db_session.refresh(team2)

    # Set champion
    season.champion_team_id = team1.id
    season.runner_up_team_id = team2.id
    db_session.commit()

    # Create matchup
    matchup = Matchup(
        season_id=season.id,
        week=1,
        home_team_id=team1.id,
        away_team_id=team2.id,
        home_score=120.5,
        away_score=110.3,
        winner_team_id=team1.id
    )
    db_session.add(matchup)
    db_session.commit()

    # Create trade
    trade = Trade(
        season_id=season.id,
        trade_date=datetime.utcnow(),
        week=5,
        status="completed",
        assets_exchanged='{"1": ["Player A"], "2": ["Player B"]}'
    )
    trade.teams.append(team1)
    trade.teams.append(team2)
    db_session.add(trade)
    db_session.commit()

    db_session.refresh(league)
    return league


class TestGetLeagues:
    """Tests for GET /api/leagues endpoint."""

    def test_get_leagues_empty(self, test_client: TestClient):
        """Test getting leagues when none exist."""
        response = test_client.get("/api/leagues")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_leagues_single(self, test_client: TestClient, test_league: League):
        """Test getting a single league."""
        response = test_client.get("/api/leagues")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test League"
        assert data[0]["platform"] == "sleeper"
        assert data[0]["platform_league_id"] == "123456789"
        assert data[0]["team_count"] == 12
        assert data[0]["scoring_type"] == "PPR"
        assert data[0]["seasons_count"] == 0
        assert data[0]["total_teams"] == 0
        assert data[0]["total_matchups"] == 0
        assert data[0]["total_trades"] == 0

    def test_get_leagues_with_data(self, test_client: TestClient, test_league_with_data: League, test_owner: Owner):
        """Test getting league with full data."""
        response = test_client.get("/api/leagues")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        league = data[0]
        assert league["name"] == "Test League With Data"
        assert league["seasons_count"] == 1
        assert league["total_teams"] == 2
        assert league["total_matchups"] == 1
        assert league["total_trades"] == 1
        assert league["latest_season_year"] == 2024

        # Check season details
        assert len(league["seasons"]) == 1
        assert league["seasons"][0]["year"] == 2024
        assert league["seasons"][0]["champion_name"] == "Test Display"  # display_name of test_owner


class TestGetLeague:
    """Tests for GET /api/leagues/{id} endpoint."""

    def test_get_league_not_found(self, test_client: TestClient):
        """Test getting non-existent league."""
        response = test_client.get("/api/leagues/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "League not found"

    def test_get_league_by_id(self, test_client: TestClient, test_league_with_data: League):
        """Test getting league by ID."""
        response = test_client.get(f"/api/leagues/{test_league_with_data.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_league_with_data.id
        assert data["name"] == "Test League With Data"
        assert data["seasons_count"] == 1


class TestDeleteLeague:
    """Tests for DELETE /api/leagues/{id} endpoint."""

    def test_delete_league_not_found(self, test_client: TestClient):
        """Test deleting non-existent league."""
        response = test_client.delete("/api/leagues/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "League not found"

    def test_delete_empty_league(self, test_client: TestClient, test_league: League):
        """Test deleting league with no data."""
        league_id = test_league.id
        response = test_client.delete(f"/api/leagues/{league_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Test League" in data["message"]
        assert data["deleted_seasons"] == 0
        assert data["deleted_teams"] == 0
        assert data["deleted_matchups"] == 0
        assert data["deleted_trades"] == 0

        # Verify league is deleted via API
        response = test_client.get(f"/api/leagues/{league_id}")
        assert response.status_code == 404

    def test_delete_league_with_data(self, test_client: TestClient, db_session: Session):
        """Test deleting league with all associated data."""
        # Create test data directly (without using fixtures that set champion/runner-up)
        owner = Owner(name="Test Owner Delete", display_name="Test Display Delete")
        db_session.add(owner)
        db_session.commit()

        league = League(
            name="League To Delete",
            platform=Platform.SLEEPER,
            platform_league_id="delete_test_123"
        )
        db_session.add(league)
        db_session.commit()

        season = Season(league_id=league.id, year=2024, is_complete=True)
        db_session.add(season)
        db_session.commit()

        team1 = Team(season_id=season.id, owner_id=owner.id, name="Team 1")
        team2 = Team(season_id=season.id, owner_id=owner.id, name="Team 2")
        db_session.add_all([team1, team2])
        db_session.commit()

        matchup = Matchup(
            season_id=season.id, week=1,
            home_team_id=team1.id, away_team_id=team2.id,
            home_score=100, away_score=90
        )
        db_session.add(matchup)
        db_session.commit()

        trade = Trade(
            season_id=season.id, trade_date=datetime.utcnow(), week=5, status="completed"
        )
        trade.teams.append(team1)
        trade.teams.append(team2)
        db_session.add(trade)
        db_session.commit()

        league_id = league.id

        # Delete via API
        response = test_client.delete(f"/api/leagues/{league_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted_seasons"] == 1
        assert data["deleted_teams"] == 2
        assert data["deleted_matchups"] == 1
        assert data["deleted_trades"] == 1

        # Verify league is deleted via API
        response = test_client.get(f"/api/leagues/{league_id}")
        assert response.status_code == 404

    def test_delete_league_preserves_owners(self, test_client: TestClient, db_session: Session):
        """Test that deleting a league preserves owner records."""
        # Create test data directly
        owner = Owner(name="Persistent Owner", display_name="Persistent Display")
        db_session.add(owner)
        db_session.commit()

        league = League(
            name="League To Delete 2",
            platform=Platform.SLEEPER,
            platform_league_id="delete_preserve_123"
        )
        db_session.add(league)
        db_session.commit()

        season = Season(league_id=league.id, year=2024, is_complete=True)
        db_session.add(season)
        db_session.commit()

        team = Team(season_id=season.id, owner_id=owner.id, name="Team")
        db_session.add(team)
        db_session.commit()

        league_id = league.id

        # Delete league
        response = test_client.delete(f"/api/leagues/{league_id}")
        assert response.status_code == 200

        # Verify owner still exists via API (owners endpoint)
        response = test_client.get("/api/owners")
        assert response.status_code == 200
        owners = response.json()
        owner_names = [o["name"] for o in owners]
        assert "Persistent Owner" in owner_names


class TestLeagueIntegration:
    """Integration tests for league management."""

    def test_multiple_leagues(self, test_client: TestClient, db_session: Session, test_owner: Owner):
        """Test managing multiple leagues."""
        # Create multiple leagues
        leagues_data = [
            ("League 1", Platform.SLEEPER, "111"),
            ("League 2", Platform.YAHOO, "222"),
            ("League 3", Platform.SLEEPER, "333"),
        ]

        created_leagues = []
        for name, platform, platform_id in leagues_data:
            league = League(
                name=name,
                platform=platform,
                platform_league_id=platform_id
            )
            db_session.add(league)
            db_session.commit()
            db_session.refresh(league)
            created_leagues.append(league)

        # Get all leagues
        response = test_client.get("/api/leagues")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Delete middle league
        response = test_client.delete(f"/api/leagues/{created_leagues[1].id}")
        assert response.status_code == 200

        # Verify only 2 leagues remain
        response = test_client.get("/api/leagues")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        remaining_names = [l["name"] for l in data]
        assert "League 1" in remaining_names
        assert "League 3" in remaining_names
        assert "League 2" not in remaining_names
