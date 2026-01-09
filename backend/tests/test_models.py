"""Tests for database models."""

from datetime import datetime
import pytest
from app.db.models import Owner, League, Season, Team, Matchup, Trade, Platform


class TestOwnerModel:
    """Tests for the Owner model."""

    def test_create_owner(self, db_session):
        """Test creating a basic owner."""
        owner = Owner(name="John Doe")
        db_session.add(owner)
        db_session.commit()

        assert owner.id is not None
        assert owner.name == "John Doe"
        assert owner.created_at is not None

    def test_owner_with_platform_ids(self, db_session):
        """Test owner with Yahoo and Sleeper IDs."""
        owner = Owner(
            name="Jane Smith",
            yahoo_user_id="yahoo_123",
            sleeper_user_id="sleeper_456",
        )
        db_session.add(owner)
        db_session.commit()

        retrieved = db_session.query(Owner).filter_by(name="Jane Smith").first()
        assert retrieved.yahoo_user_id == "yahoo_123"
        assert retrieved.sleeper_user_id == "sleeper_456"

    def test_owner_persists_across_seasons(self, db_session):
        """Test that an owner can have teams across multiple seasons."""
        # Create owner
        owner = Owner(name="Multi-Season Owner")
        db_session.add(owner)

        # Create league and two seasons
        league = League(
            name="Test League",
            platform=Platform.SLEEPER,
            platform_league_id="league_123",
        )
        db_session.add(league)
        db_session.commit()

        season_2022 = Season(league_id=league.id, year=2022)
        season_2023 = Season(league_id=league.id, year=2023)
        db_session.add_all([season_2022, season_2023])
        db_session.commit()

        # Create teams for same owner in different seasons
        team_2022 = Team(
            season_id=season_2022.id,
            owner_id=owner.id,
            name="Team 2022",
        )
        team_2023 = Team(
            season_id=season_2023.id,
            owner_id=owner.id,
            name="Team 2023",
        )
        db_session.add_all([team_2022, team_2023])
        db_session.commit()

        # Verify owner has both teams
        db_session.refresh(owner)
        assert len(owner.teams) == 2
        assert {t.name for t in owner.teams} == {"Team 2022", "Team 2023"}

    def test_owner_unique_platform_ids(self, db_session):
        """Test that platform IDs are unique."""
        owner1 = Owner(name="Owner 1", yahoo_user_id="same_id")
        db_session.add(owner1)
        db_session.commit()

        owner2 = Owner(name="Owner 2", yahoo_user_id="same_id")
        db_session.add(owner2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


class TestLeagueModel:
    """Tests for the League model."""

    def test_create_yahoo_league(self, db_session):
        """Test creating a Yahoo league."""
        league = League(
            name="Yahoo Test League",
            platform=Platform.YAHOO,
            platform_league_id="yahoo_league_123",
            team_count=12,
            scoring_type="PPR",
        )
        db_session.add(league)
        db_session.commit()

        assert league.id is not None
        assert league.platform == Platform.YAHOO
        assert league.team_count == 12

    def test_create_sleeper_league(self, db_session):
        """Test creating a Sleeper league."""
        league = League(
            name="Sleeper Test League",
            platform=Platform.SLEEPER,
            platform_league_id="sleeper_league_456",
        )
        db_session.add(league)
        db_session.commit()

        assert league.platform == Platform.SLEEPER


class TestSeasonModel:
    """Tests for the Season model."""

    def test_create_season(self, db_session):
        """Test creating a season."""
        league = League(
            name="Test League",
            platform=Platform.SLEEPER,
            platform_league_id="league_123",
        )
        db_session.add(league)
        db_session.commit()

        season = Season(
            league_id=league.id,
            year=2023,
            regular_season_weeks=14,
            playoff_weeks=3,
            playoff_team_count=6,
        )
        db_session.add(season)
        db_session.commit()

        assert season.id is not None
        assert season.year == 2023
        assert season.is_complete is False

    def test_season_with_champion(self, db_session):
        """Test setting a season champion."""
        league = League(
            name="Test League",
            platform=Platform.SLEEPER,
            platform_league_id="league_123",
        )
        db_session.add(league)
        db_session.commit()

        season = Season(league_id=league.id, year=2023)
        db_session.add(season)
        db_session.commit()

        owner = Owner(name="Champion Owner")
        db_session.add(owner)
        db_session.commit()

        team = Team(season_id=season.id, owner_id=owner.id, name="Champion Team")
        db_session.add(team)
        db_session.commit()

        season.champion_team_id = team.id
        season.is_complete = True
        db_session.commit()

        assert season.champion_team_id == team.id
        assert season.is_complete is True


class TestTeamModel:
    """Tests for the Team model."""

    def test_create_team(self, db_session):
        """Test creating a team."""
        league = League(
            name="Test League",
            platform=Platform.SLEEPER,
            platform_league_id="league_123",
        )
        db_session.add(league)
        db_session.commit()

        season = Season(league_id=league.id, year=2023)
        db_session.add(season)
        db_session.commit()

        owner = Owner(name="Test Owner")
        db_session.add(owner)
        db_session.commit()

        team = Team(
            season_id=season.id,
            owner_id=owner.id,
            name="My Fantasy Team",
            wins=10,
            losses=4,
            points_for=1850.5,
            points_against=1700.25,
            made_playoffs=True,
        )
        db_session.add(team)
        db_session.commit()

        assert team.id is not None
        assert team.wins == 10
        assert team.losses == 4
        assert team.points_for == 1850.5
        assert team.made_playoffs is True

    def test_team_relationships(self, db_session):
        """Test team's relationships with season and owner."""
        league = League(
            name="Test League",
            platform=Platform.YAHOO,
            platform_league_id="league_123",
        )
        db_session.add(league)
        db_session.commit()

        season = Season(league_id=league.id, year=2023)
        db_session.add(season)
        db_session.commit()

        owner = Owner(name="Test Owner")
        db_session.add(owner)
        db_session.commit()

        team = Team(season_id=season.id, owner_id=owner.id, name="Test Team")
        db_session.add(team)
        db_session.commit()

        # Verify relationships
        assert team.season == season
        assert team.owner == owner
        assert team in season.teams
        assert team in owner.teams


class TestMatchupModel:
    """Tests for the Matchup model."""

    def test_create_matchup(self, db_session):
        """Test creating a matchup."""
        # Setup
        league = League(
            name="Test League",
            platform=Platform.SLEEPER,
            platform_league_id="league_123",
        )
        db_session.add(league)
        db_session.commit()

        season = Season(league_id=league.id, year=2023)
        db_session.add(season)
        db_session.commit()

        owner1 = Owner(name="Owner 1")
        owner2 = Owner(name="Owner 2")
        db_session.add_all([owner1, owner2])
        db_session.commit()

        home_team = Team(season_id=season.id, owner_id=owner1.id, name="Home Team")
        away_team = Team(season_id=season.id, owner_id=owner2.id, name="Away Team")
        db_session.add_all([home_team, away_team])
        db_session.commit()

        # Create matchup
        matchup = Matchup(
            season_id=season.id,
            week=1,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            home_score=125.5,
            away_score=110.3,
            winner_team_id=home_team.id,
        )
        db_session.add(matchup)
        db_session.commit()

        assert matchup.id is not None
        assert matchup.week == 1
        assert matchup.home_score == 125.5
        assert matchup.winner_team_id == home_team.id

    def test_playoff_matchup(self, db_session):
        """Test creating a playoff matchup."""
        league = League(
            name="Test League",
            platform=Platform.SLEEPER,
            platform_league_id="league_123",
        )
        db_session.add(league)
        db_session.commit()

        season = Season(league_id=league.id, year=2023)
        db_session.add(season)
        db_session.commit()

        owner1 = Owner(name="Owner 1")
        owner2 = Owner(name="Owner 2")
        db_session.add_all([owner1, owner2])
        db_session.commit()

        team1 = Team(season_id=season.id, owner_id=owner1.id, name="Team 1")
        team2 = Team(season_id=season.id, owner_id=owner2.id, name="Team 2")
        db_session.add_all([team1, team2])
        db_session.commit()

        # Championship matchup
        matchup = Matchup(
            season_id=season.id,
            week=16,
            home_team_id=team1.id,
            away_team_id=team2.id,
            home_score=150.0,
            away_score=140.0,
            is_playoff=True,
            is_championship=True,
            winner_team_id=team1.id,
        )
        db_session.add(matchup)
        db_session.commit()

        assert matchup.is_playoff is True
        assert matchup.is_championship is True


class TestTradeModel:
    """Tests for the Trade model."""

    def test_create_trade(self, db_session):
        """Test creating a trade."""
        league = League(
            name="Test League",
            platform=Platform.SLEEPER,
            platform_league_id="league_123",
        )
        db_session.add(league)
        db_session.commit()

        season = Season(league_id=league.id, year=2023)
        db_session.add(season)
        db_session.commit()

        owner1 = Owner(name="Owner 1")
        owner2 = Owner(name="Owner 2")
        db_session.add_all([owner1, owner2])
        db_session.commit()

        team1 = Team(season_id=season.id, owner_id=owner1.id, name="Team 1")
        team2 = Team(season_id=season.id, owner_id=owner2.id, name="Team 2")
        db_session.add_all([team1, team2])
        db_session.commit()

        trade = Trade(
            season_id=season.id,
            trade_date=datetime.utcnow(),
            week=5,
            assets_exchanged='{"team1": ["Player A"], "team2": ["Player B", "2024 1st"]}',
            status="completed",
        )
        trade.teams.append(team1)
        trade.teams.append(team2)
        db_session.add(trade)
        db_session.commit()

        assert trade.id is not None
        assert len(trade.teams) == 2
        assert trade.status == "completed"


class TestCrossPlatformOwner:
    """Tests for owner mapping across platforms."""

    def test_owner_linked_to_both_platforms(self, db_session):
        """Test an owner with accounts on both Yahoo and Sleeper."""
        owner = Owner(
            name="Cross-Platform User",
            yahoo_user_id="yahoo_user_789",
            sleeper_user_id="sleeper_user_789",
        )
        db_session.add(owner)
        db_session.commit()

        # Create Yahoo league and season
        yahoo_league = League(
            name="Yahoo League",
            platform=Platform.YAHOO,
            platform_league_id="yahoo_123",
        )
        db_session.add(yahoo_league)
        db_session.commit()

        yahoo_season = Season(league_id=yahoo_league.id, year=2022)
        db_session.add(yahoo_season)
        db_session.commit()

        # Create Sleeper league and season
        sleeper_league = League(
            name="Sleeper League",
            platform=Platform.SLEEPER,
            platform_league_id="sleeper_456",
        )
        db_session.add(sleeper_league)
        db_session.commit()

        sleeper_season = Season(league_id=sleeper_league.id, year=2023)
        db_session.add(sleeper_season)
        db_session.commit()

        # Create teams on both platforms for same owner
        yahoo_team = Team(
            season_id=yahoo_season.id,
            owner_id=owner.id,
            name="Yahoo Team Name",
            wins=8,
            losses=6,
        )
        sleeper_team = Team(
            season_id=sleeper_season.id,
            owner_id=owner.id,
            name="Sleeper Team Name",
            wins=10,
            losses=4,
        )
        db_session.add_all([yahoo_team, sleeper_team])
        db_session.commit()

        # Verify owner has teams from both platforms
        db_session.refresh(owner)
        assert len(owner.teams) == 2

        # Calculate aggregate stats
        total_wins = sum(t.wins for t in owner.teams)
        total_losses = sum(t.losses for t in owner.teams)
        assert total_wins == 18  # 8 + 10
        assert total_losses == 10  # 6 + 4
