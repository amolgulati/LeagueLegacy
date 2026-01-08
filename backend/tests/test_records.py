"""Tests for league records API endpoints."""

import pytest
from datetime import datetime
from app.db.models import Owner, League, Season, Team, Matchup, Trade, Platform


# ==================== Helper Functions ====================

def create_test_league(db_session, name="Test League", platform=Platform.SLEEPER, league_id="test_league_1"):
    """Create a test league."""
    league = League(
        name=name,
        platform=platform,
        platform_league_id=league_id,
        team_count=10,
        scoring_type="PPR",
    )
    db_session.add(league)
    db_session.flush()
    return league


def create_test_season(db_session, league, year, is_complete=True):
    """Create a test season."""
    season = Season(
        league_id=league.id,
        year=year,
        regular_season_weeks=14,
        playoff_weeks=3,
        playoff_team_count=6,
        is_complete=is_complete,
    )
    db_session.add(season)
    db_session.flush()
    return season


def create_test_owner(db_session, name, sleeper_id=None, yahoo_id=None):
    """Create a test owner."""
    owner = Owner(
        name=name,
        display_name=name,
        sleeper_user_id=sleeper_id,
        yahoo_user_id=yahoo_id,
    )
    db_session.add(owner)
    db_session.flush()
    return owner


def create_test_team(db_session, season, owner, name="Test Team", wins=8, losses=6,
                     points_for=1500.0, made_playoffs=True, final_rank=None,
                     regular_season_rank=None, longest_win_streak=0):
    """Create a test team."""
    team = Team(
        season_id=season.id,
        owner_id=owner.id,
        name=name,
        wins=wins,
        losses=losses,
        ties=0,
        points_for=points_for,
        points_against=1400.0,
        made_playoffs=made_playoffs,
        final_rank=final_rank,
        regular_season_rank=regular_season_rank,
        longest_win_streak=longest_win_streak,
    )
    db_session.add(team)
    db_session.flush()
    return team


def create_test_matchup(db_session, season, home_team, away_team, week,
                        home_score=100.0, away_score=90.0,
                        is_playoff=False, is_championship=False):
    """Create a test matchup."""
    winner_id = home_team.id if home_score > away_score else (
        away_team.id if away_score > home_score else None
    )
    matchup = Matchup(
        season_id=season.id,
        week=week,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        home_score=home_score,
        away_score=away_score,
        is_playoff=is_playoff,
        is_championship=is_championship,
        winner_team_id=winner_id,
        is_tie=home_score == away_score,
    )
    db_session.add(matchup)
    db_session.flush()
    return matchup


def create_test_trade(db_session, season, teams, week=1):
    """Create a test trade between teams."""
    trade = Trade(
        season_id=season.id,
        trade_date=datetime(season.year, 10, 1),
        week=week,
        status="completed",
    )
    db_session.add(trade)
    db_session.flush()

    # Associate teams with the trade
    for team in teams:
        trade.teams.append(team)

    db_session.flush()
    return trade


# ==================== Test Classes ====================

class TestHighestSingleWeekScore:
    """Test highest single-week score record."""

    def test_highest_single_week_score(self, test_client, db_session):
        """Test getting highest single-week score."""
        owner1 = create_test_owner(db_session, "John Doe", sleeper_id="s_high_1")
        owner2 = create_test_owner(db_session, "Jane Doe", sleeper_id="s_high_2")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Team A")
        team2 = create_test_team(db_session, season, owner2, "Team B")

        # Create matchups with different scores
        create_test_matchup(db_session, season, team1, team2, 1, 180.5, 120.0)  # John scores 180.5
        create_test_matchup(db_session, season, team2, team1, 2, 150.0, 165.3)  # John scores 165.3

        db_session.commit()

        response = test_client.get("/api/records")
        assert response.status_code == 200

        data = response.json()
        assert "highest_single_week_score" in data
        record = data["highest_single_week_score"]
        assert record["score"] == 180.5
        assert record["owner_name"] == "John Doe"
        assert record["year"] == 2023
        assert record["week"] == 1

    def test_highest_score_across_seasons(self, test_client, db_session):
        """Test highest score considering all seasons."""
        owner = create_test_owner(db_session, "Record Breaker", sleeper_id="s_record")
        league = create_test_league(db_session)

        season_2022 = create_test_season(db_session, league, 2022)
        team_2022 = create_test_team(db_session, season_2022, owner, "Team 2022")

        season_2023 = create_test_season(db_session, league, 2023)
        team_2023 = create_test_team(db_session, season_2023, owner, "Team 2023")

        owner2 = create_test_owner(db_session, "Opponent", sleeper_id="s_opp")
        opp_2022 = create_test_team(db_session, season_2022, owner2, "Opp 2022")
        opp_2023 = create_test_team(db_session, season_2023, owner2, "Opp 2023")

        create_test_matchup(db_session, season_2022, team_2022, opp_2022, 1, 150.0, 100.0)
        create_test_matchup(db_session, season_2023, team_2023, opp_2023, 1, 200.0, 100.0)  # Higher

        db_session.commit()

        response = test_client.get("/api/records")
        assert response.status_code == 200

        data = response.json()
        record = data["highest_single_week_score"]
        assert record["score"] == 200.0
        assert record["year"] == 2023


class TestMostPointsInSeason:
    """Test most points in a season record."""

    def test_most_points_in_season(self, test_client, db_session):
        """Test getting most points in a season."""
        owner1 = create_test_owner(db_session, "High Scorer", sleeper_id="s_pts_1")
        owner2 = create_test_owner(db_session, "Low Scorer", sleeper_id="s_pts_2")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        create_test_team(db_session, season, owner1, "High Team", points_for=2500.5)
        create_test_team(db_session, season, owner2, "Low Team", points_for=1800.0)

        db_session.commit()

        response = test_client.get("/api/records")
        assert response.status_code == 200

        data = response.json()
        assert "most_points_in_season" in data
        record = data["most_points_in_season"]
        assert record["points"] == 2500.5
        assert record["owner_name"] == "High Scorer"
        assert record["year"] == 2023

    def test_most_points_across_multiple_seasons(self, test_client, db_session):
        """Test most points considering multiple seasons."""
        owner = create_test_owner(db_session, "Scorer", sleeper_id="s_multi_pts")
        league = create_test_league(db_session)

        season_2022 = create_test_season(db_session, league, 2022)
        create_test_team(db_session, season_2022, owner, "Team 2022", points_for=2200.0)

        season_2023 = create_test_season(db_session, league, 2023)
        create_test_team(db_session, season_2023, owner, "Team 2023", points_for=2800.0)  # Higher

        db_session.commit()

        response = test_client.get("/api/records")
        assert response.status_code == 200

        data = response.json()
        record = data["most_points_in_season"]
        assert record["points"] == 2800.0
        assert record["year"] == 2023


class TestLongestWinStreak:
    """Test longest win streak record."""

    def test_longest_win_streak(self, test_client, db_session):
        """Test getting longest win streak."""
        owner1 = create_test_owner(db_session, "Streak Master", sleeper_id="s_streak_1")
        owner2 = create_test_owner(db_session, "No Streak", sleeper_id="s_streak_2")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        create_test_team(db_session, season, owner1, "Hot Team", longest_win_streak=8)
        create_test_team(db_session, season, owner2, "Cold Team", longest_win_streak=3)

        db_session.commit()

        response = test_client.get("/api/records")
        assert response.status_code == 200

        data = response.json()
        assert "longest_win_streak" in data
        record = data["longest_win_streak"]
        assert record["streak"] == 8
        assert record["owner_name"] == "Streak Master"
        assert record["year"] == 2023


class TestMostTradesInSeason:
    """Test most trades in a season record."""

    def test_most_trades_in_season(self, test_client, db_session):
        """Test getting most trades in a season by an owner."""
        owner1 = create_test_owner(db_session, "Trade Happy", sleeper_id="s_trade_1")
        owner2 = create_test_owner(db_session, "Trade Partner", sleeper_id="s_trade_2")
        owner3 = create_test_owner(db_session, "Quiet Owner", sleeper_id="s_trade_3")

        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Trade Team")
        team2 = create_test_team(db_session, season, owner2, "Partner Team")
        team3 = create_test_team(db_session, season, owner3, "Quiet Team")

        # Create trades: owner1 involved in 5 trades, owner2 in 3, owner3 in 1
        create_test_trade(db_session, season, [team1, team2], week=1)
        create_test_trade(db_session, season, [team1, team2], week=2)
        create_test_trade(db_session, season, [team1, team3], week=3)
        create_test_trade(db_session, season, [team1, team2], week=4)
        create_test_trade(db_session, season, [team1, team3], week=5)

        db_session.commit()

        response = test_client.get("/api/records")
        assert response.status_code == 200

        data = response.json()
        assert "most_trades_in_season" in data
        record = data["most_trades_in_season"]
        assert record["trade_count"] == 5
        assert record["owner_name"] == "Trade Happy"
        assert record["year"] == 2023


class TestRecordsEmptyDatabase:
    """Test records endpoint with empty database."""

    def test_empty_database_returns_nulls(self, test_client):
        """Test that empty database returns null for all records."""
        response = test_client.get("/api/records")
        assert response.status_code == 200

        data = response.json()
        assert data["highest_single_week_score"] is None
        assert data["most_points_in_season"] is None
        assert data["longest_win_streak"] is None
        assert data["most_trades_in_season"] is None


class TestRecordsMultipleRecords:
    """Test that all records are returned together."""

    def test_all_records_returned(self, test_client, db_session):
        """Test that endpoint returns all record types."""
        owner = create_test_owner(db_session, "All Records", sleeper_id="s_all")
        owner2 = create_test_owner(db_session, "Partner", sleeper_id="s_partner")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner, "Record Team",
                                  points_for=2500.0, longest_win_streak=6)
        team2 = create_test_team(db_session, season, owner2, "Partner Team",
                                  points_for=1800.0, longest_win_streak=2)

        create_test_matchup(db_session, season, team1, team2, 1, 180.0, 120.0)
        create_test_trade(db_session, season, [team1, team2], week=1)

        db_session.commit()

        response = test_client.get("/api/records")
        assert response.status_code == 200

        data = response.json()

        # All records should be present
        assert "highest_single_week_score" in data
        assert "most_points_in_season" in data
        assert "longest_win_streak" in data
        assert "most_trades_in_season" in data

        # Verify they have the expected structure
        assert data["highest_single_week_score"]["owner_name"] == "All Records"
        assert data["most_points_in_season"]["owner_name"] == "All Records"
        assert data["longest_win_streak"]["owner_name"] == "All Records"


class TestTopRecords:
    """Test top N records functionality."""

    def test_top_weekly_scores(self, test_client, db_session):
        """Test getting top N weekly scores."""
        owner1 = create_test_owner(db_session, "Owner A", sleeper_id="s_top_a")
        owner2 = create_test_owner(db_session, "Owner B", sleeper_id="s_top_b")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Team A")
        team2 = create_test_team(db_session, season, owner2, "Team B")

        # Create matchups with various scores
        create_test_matchup(db_session, season, team1, team2, 1, 200.0, 180.0)
        create_test_matchup(db_session, season, team2, team1, 2, 175.0, 170.0)
        create_test_matchup(db_session, season, team1, team2, 3, 190.0, 150.0)
        create_test_matchup(db_session, season, team2, team1, 4, 185.0, 160.0)

        db_session.commit()

        response = test_client.get("/api/records")
        assert response.status_code == 200

        data = response.json()

        # Should have top scores list
        assert "top_weekly_scores" in data
        top_scores = data["top_weekly_scores"]

        # Should be sorted descending
        assert len(top_scores) >= 3
        assert top_scores[0]["score"] >= top_scores[1]["score"]
