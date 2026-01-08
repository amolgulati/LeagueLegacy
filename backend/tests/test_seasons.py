"""Tests for seasons API endpoints."""

import pytest
from datetime import datetime

from app.db.models import Owner, League, Season, Team, Matchup, Trade, Platform


class TestSeasonsAPI:
    """Test cases for /api/seasons endpoints."""

    @pytest.fixture
    def sample_data(self, db_session):
        """Create sample data for testing."""
        # Create owners
        owner1 = Owner(name="Champion Owner", sleeper_user_id="champ123")
        owner2 = Owner(name="Runner Up", sleeper_user_id="runner456")
        owner3 = Owner(name="Third Place", sleeper_user_id="third789")
        owner4 = Owner(name="Fourth Place", sleeper_user_id="fourth101")
        db_session.add_all([owner1, owner2, owner3, owner4])
        db_session.flush()

        # Create league
        league = League(
            name="Test League",
            platform=Platform.SLEEPER,
            platform_league_id="league123",
            team_count=4,
        )
        db_session.add(league)
        db_session.flush()

        # Create season
        season = Season(
            league_id=league.id,
            year=2023,
            regular_season_weeks=14,
            playoff_weeks=3,
            playoff_team_count=4,
            is_complete=True,
        )
        db_session.add(season)
        db_session.flush()

        # Create teams
        team1 = Team(
            season_id=season.id,
            owner_id=owner1.id,
            name="Champion Team",
            wins=12,
            losses=2,
            ties=0,
            points_for=1500.5,
            points_against=1100.0,
            regular_season_rank=1,
            final_rank=1,
            made_playoffs=True,
        )
        team2 = Team(
            season_id=season.id,
            owner_id=owner2.id,
            name="Runner Up Team",
            wins=10,
            losses=4,
            ties=0,
            points_for=1400.0,
            points_against=1150.0,
            regular_season_rank=2,
            final_rank=2,
            made_playoffs=True,
        )
        team3 = Team(
            season_id=season.id,
            owner_id=owner3.id,
            name="Third Place Team",
            wins=8,
            losses=6,
            ties=0,
            points_for=1300.0,
            points_against=1200.0,
            regular_season_rank=3,
            final_rank=3,
            made_playoffs=True,
        )
        team4 = Team(
            season_id=season.id,
            owner_id=owner4.id,
            name="Fourth Place Team",
            wins=6,
            losses=8,
            ties=0,
            points_for=1200.0,
            points_against=1250.0,
            regular_season_rank=4,
            final_rank=4,
            made_playoffs=True,
        )
        db_session.add_all([team1, team2, team3, team4])
        db_session.flush()

        # Update season with champion and runner-up
        season.champion_team_id = team1.id
        season.runner_up_team_id = team2.id

        # Create playoff matchups (week 15, 16, 17)
        # Semifinals (week 15)
        semi1 = Matchup(
            season_id=season.id,
            week=15,
            home_team_id=team1.id,
            away_team_id=team4.id,
            home_score=140.5,
            away_score=110.0,
            is_playoff=True,
            winner_team_id=team1.id,
        )
        semi2 = Matchup(
            season_id=season.id,
            week=15,
            home_team_id=team2.id,
            away_team_id=team3.id,
            home_score=135.0,
            away_score=125.0,
            is_playoff=True,
            winner_team_id=team2.id,
        )
        # Third place game (week 16)
        third_place = Matchup(
            season_id=season.id,
            week=16,
            home_team_id=team3.id,
            away_team_id=team4.id,
            home_score=120.0,
            away_score=115.0,
            is_playoff=True,
            is_consolation=True,
            winner_team_id=team3.id,
        )
        # Championship (week 16)
        championship = Matchup(
            season_id=season.id,
            week=16,
            home_team_id=team1.id,
            away_team_id=team2.id,
            home_score=155.0,
            away_score=145.0,
            is_playoff=True,
            is_championship=True,
            winner_team_id=team1.id,
        )
        db_session.add_all([semi1, semi2, third_place, championship])

        # Create a trade
        trade = Trade(
            season_id=season.id,
            trade_date=datetime(2023, 10, 15),
            week=7,
            assets_exchanged='{"team1": ["Player A"], "team2": ["Player B"]}',
            status="completed",
        )
        trade.teams.extend([team1, team2])
        db_session.add(trade)

        db_session.commit()

        return {
            "owners": [owner1, owner2, owner3, owner4],
            "league": league,
            "season": season,
            "teams": [team1, team2, team3, team4],
        }

    def test_get_season_detail(self, test_client, sample_data):
        """Test GET /api/seasons/{id} returns full season details."""
        season = sample_data["season"]

        response = test_client.get(f"/api/seasons/{season.id}")
        assert response.status_code == 200

        data = response.json()

        # Check basic season info
        assert data["id"] == season.id
        assert data["year"] == 2023
        assert data["league_name"] == "Test League"
        assert data["platform"] == "SLEEPER"
        assert data["is_complete"] is True
        assert data["regular_season_weeks"] == 14
        assert data["playoff_weeks"] == 3
        assert data["playoff_team_count"] == 4

    def test_get_season_detail_standings(self, test_client, sample_data):
        """Test GET /api/seasons/{id} returns final standings."""
        season = sample_data["season"]

        response = test_client.get(f"/api/seasons/{season.id}")
        assert response.status_code == 200

        data = response.json()

        # Check standings
        standings = data["standings"]
        assert len(standings) == 4

        # Check order (by final_rank)
        assert standings[0]["owner_name"] == "Champion Owner"
        assert standings[0]["final_rank"] == 1
        assert standings[0]["wins"] == 12
        assert standings[0]["losses"] == 2

        assert standings[1]["owner_name"] == "Runner Up"
        assert standings[1]["final_rank"] == 2

        assert standings[2]["owner_name"] == "Third Place"
        assert standings[3]["owner_name"] == "Fourth Place"

    def test_get_season_detail_champion(self, test_client, sample_data):
        """Test GET /api/seasons/{id} includes champion info."""
        season = sample_data["season"]

        response = test_client.get(f"/api/seasons/{season.id}")
        assert response.status_code == 200

        data = response.json()

        assert data["champion"]["name"] == "Champion Owner"
        assert data["runner_up"]["name"] == "Runner Up"

    def test_get_season_detail_playoff_bracket(self, test_client, sample_data):
        """Test GET /api/seasons/{id} includes playoff bracket."""
        season = sample_data["season"]

        response = test_client.get(f"/api/seasons/{season.id}")
        assert response.status_code == 200

        data = response.json()

        # Check playoff bracket
        bracket = data["playoff_bracket"]
        assert len(bracket) == 4  # 2 semis, 1 third place, 1 championship

        # Check championship game
        championship = next(m for m in bracket if m["is_championship"])
        assert championship["winner_owner_name"] == "Champion Owner"
        assert championship["home_score"] == 155.0
        assert championship["away_score"] == 145.0

    def test_get_season_detail_trades(self, test_client, sample_data):
        """Test GET /api/seasons/{id} includes notable trades."""
        season = sample_data["season"]

        response = test_client.get(f"/api/seasons/{season.id}")
        assert response.status_code == 200

        data = response.json()

        # Check trades
        trades = data["trades"]
        assert len(trades) == 1
        assert trades[0]["week"] == 7
        assert len(trades[0]["teams"]) == 2

    def test_get_season_detail_not_found(self, test_client, db_session):
        """Test GET /api/seasons/{id} returns 404 for non-existent season."""
        response = test_client.get("/api/seasons/99999")
        assert response.status_code == 404

    def test_list_seasons(self, test_client, sample_data):
        """Test GET /api/seasons returns list of all seasons."""
        response = test_client.get("/api/seasons")
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 1

        # Find our test season
        test_season = next((s for s in data if s["id"] == sample_data["season"].id), None)
        assert test_season is not None
        assert test_season["year"] == 2023
        assert test_season["champion_name"] == "Champion Owner"

    def test_list_seasons_by_league(self, test_client, sample_data):
        """Test GET /api/seasons?league_id={id} filters by league."""
        league = sample_data["league"]

        response = test_client.get(f"/api/seasons?league_id={league.id}")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["league_id"] == league.id
