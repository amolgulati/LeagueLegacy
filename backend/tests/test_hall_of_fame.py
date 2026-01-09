"""Tests for Hall of Fame API endpoints."""

import pytest
from app.db.models import Owner, League, Season, Team, Platform


# ==================== Helper Functions ====================

def create_test_league(db_session, name="Test League", platform=Platform.SLEEPER, league_id="test_league_hof"):
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
                     regular_season_rank=None):
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
    )
    db_session.add(team)
    db_session.flush()
    return team


# ==================== Test Classes ====================

class TestHallOfFameEndpoint:
    """Test GET /api/hall-of-fame - complete Hall of Fame data."""

    def test_hall_of_fame_empty(self, test_client):
        """Test Hall of Fame when no champions exist."""
        response = test_client.get("/api/hall-of-fame")
        assert response.status_code == 200

        data = response.json()
        assert data["champions_by_year"] == []
        assert data["championship_leaderboard"] == []
        assert data["dynasties"] == []
        assert data["total_seasons"] == 0
        assert data["unique_champions"] == 0

    def test_hall_of_fame_single_champion(self, test_client, db_session):
        """Test Hall of Fame with a single champion."""
        owner = create_test_owner(db_session, "Champion King", sleeper_id="hof_s1")
        league = create_test_league(db_session, "Premier League")
        season = create_test_season(db_session, league, 2023)
        champ_team = create_test_team(db_session, season, owner, "Dynasty FC",
                                       wins=12, losses=2, points_for=1800.0, final_rank=1)

        season.champion_team_id = champ_team.id
        db_session.commit()

        response = test_client.get("/api/hall-of-fame")
        assert response.status_code == 200

        data = response.json()
        assert data["total_seasons"] == 1
        assert data["unique_champions"] == 1
        assert len(data["champions_by_year"]) == 1

        champion = data["champions_by_year"][0]
        assert champion["year"] == 2023
        assert champion["champion"]["name"] == "Champion King"
        assert champion["team_name"] == "Dynasty FC"
        assert champion["record"] == "12-2"
        assert champion["points_for"] == 1800.0

    def test_hall_of_fame_with_runner_up(self, test_client, db_session):
        """Test Hall of Fame includes runner-up info."""
        winner = create_test_owner(db_session, "Winner", sleeper_id="hof_winner")
        loser = create_test_owner(db_session, "Runner Up", sleeper_id="hof_loser")
        league = create_test_league(db_session, "Championship League")
        season = create_test_season(db_session, league, 2023)

        champ_team = create_test_team(db_session, season, winner, "Champions",
                                       wins=12, losses=2, final_rank=1)
        runner_up_team = create_test_team(db_session, season, loser, "Almost",
                                           wins=10, losses=4, final_rank=2)

        season.champion_team_id = champ_team.id
        season.runner_up_team_id = runner_up_team.id
        db_session.commit()

        response = test_client.get("/api/hall-of-fame")
        assert response.status_code == 200

        data = response.json()
        champion = data["champions_by_year"][0]
        assert champion["champion"]["name"] == "Winner"
        assert champion["runner_up"]["name"] == "Runner Up"

    def test_hall_of_fame_multiple_champions(self, test_client, db_session):
        """Test Hall of Fame with multiple champions across years."""
        owner1 = create_test_owner(db_session, "First Champ", sleeper_id="hof_c1")
        owner2 = create_test_owner(db_session, "Second Champ", sleeper_id="hof_c2")
        owner3 = create_test_owner(db_session, "Third Champ", sleeper_id="hof_c3")
        league = create_test_league(db_session)

        # 2021 - Owner 1
        season1 = create_test_season(db_session, league, 2021)
        team1 = create_test_team(db_session, season1, owner1, "Team 2021", final_rank=1)
        season1.champion_team_id = team1.id

        # 2022 - Owner 2
        season2 = create_test_season(db_session, league, 2022)
        team2 = create_test_team(db_session, season2, owner2, "Team 2022", final_rank=1)
        season2.champion_team_id = team2.id

        # 2023 - Owner 3
        season3 = create_test_season(db_session, league, 2023)
        team3 = create_test_team(db_session, season3, owner3, "Team 2023", final_rank=1)
        season3.champion_team_id = team3.id

        db_session.commit()

        response = test_client.get("/api/hall-of-fame")
        assert response.status_code == 200

        data = response.json()
        assert data["total_seasons"] == 3
        assert data["unique_champions"] == 3

        # Should be sorted by year descending
        assert data["champions_by_year"][0]["year"] == 2023
        assert data["champions_by_year"][1]["year"] == 2022
        assert data["champions_by_year"][2]["year"] == 2021


class TestChampionshipLeaderboard:
    """Test championship leaderboard functionality."""

    def test_leaderboard_sorted_by_championships(self, test_client, db_session):
        """Test that leaderboard is sorted by championship count."""
        dynasty_owner = create_test_owner(db_session, "Dynasty Owner", sleeper_id="hof_dyn")
        single_champ = create_test_owner(db_session, "Single Champ", sleeper_id="hof_single")
        league = create_test_league(db_session)

        # Dynasty owner wins 3 championships
        for year in [2021, 2022, 2023]:
            season = create_test_season(db_session, league, year)
            team = create_test_team(db_session, season, dynasty_owner, f"Dynasty {year}", final_rank=1)
            season.champion_team_id = team.id

        # Single champ wins 1
        season = create_test_season(db_session, league, 2020)
        team = create_test_team(db_session, season, single_champ, "One Time", final_rank=1)
        season.champion_team_id = team.id

        db_session.commit()

        response = test_client.get("/api/hall-of-fame")
        assert response.status_code == 200

        data = response.json()
        leaderboard = data["championship_leaderboard"]

        assert len(leaderboard) == 2
        assert leaderboard[0]["owner"]["name"] == "Dynasty Owner"
        assert leaderboard[0]["championships"] == 3
        assert leaderboard[1]["owner"]["name"] == "Single Champ"
        assert leaderboard[1]["championships"] == 1

    def test_leaderboard_includes_years(self, test_client, db_session):
        """Test that leaderboard includes championship years."""
        owner = create_test_owner(db_session, "Multi Champ", sleeper_id="hof_multi")
        league = create_test_league(db_session)

        for year in [2020, 2022, 2023]:
            season = create_test_season(db_session, league, year)
            team = create_test_team(db_session, season, owner, f"Champs {year}", final_rank=1)
            season.champion_team_id = team.id

        db_session.commit()

        response = test_client.get("/api/hall-of-fame")
        assert response.status_code == 200

        data = response.json()
        leaderboard = data["championship_leaderboard"]

        assert len(leaderboard) == 1
        assert leaderboard[0]["championships"] == 3
        # Years should be sorted descending
        assert leaderboard[0]["years"] == [2023, 2022, 2020]

    def test_dedicated_leaderboard_endpoint(self, test_client, db_session):
        """Test the dedicated leaderboard endpoint."""
        owner = create_test_owner(db_session, "Leaderboard Test", sleeper_id="hof_lead")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)
        team = create_test_team(db_session, season, owner, "Test Team", final_rank=1)
        season.champion_team_id = team.id
        db_session.commit()

        response = test_client.get("/api/hall-of-fame/leaderboard")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["owner"]["name"] == "Leaderboard Test"
        assert data[0]["championships"] == 1


class TestDynastyTracking:
    """Test dynasty (consecutive championship) tracking."""

    def test_dynasty_detection(self, test_client, db_session):
        """Test that consecutive championships are detected as dynasty."""
        dynasty_owner = create_test_owner(db_session, "Dynasty King", sleeper_id="hof_dk")
        league = create_test_league(db_session, "Dynasty League")

        # Win 3 consecutive championships
        for year in [2021, 2022, 2023]:
            season = create_test_season(db_session, league, year)
            team = create_test_team(db_session, season, dynasty_owner, f"Dynasty {year}", final_rank=1)
            season.champion_team_id = team.id

        db_session.commit()

        response = test_client.get("/api/hall-of-fame")
        assert response.status_code == 200

        data = response.json()
        dynasties = data["dynasties"]

        assert len(dynasties) == 1
        assert dynasties[0]["owner"]["name"] == "Dynasty King"
        assert dynasties[0]["streak"] == 3
        assert dynasties[0]["start_year"] == 2021
        assert dynasties[0]["end_year"] == 2023

    def test_no_dynasty_for_non_consecutive(self, test_client, db_session):
        """Test that non-consecutive wins don't count as dynasty."""
        owner = create_test_owner(db_session, "Gap Champ", sleeper_id="hof_gap")
        league = create_test_league(db_session)

        # Win in 2021 and 2023 (gap in 2022)
        for year in [2021, 2023]:
            season = create_test_season(db_session, league, year)
            team = create_test_team(db_session, season, owner, f"Team {year}", final_rank=1)
            season.champion_team_id = team.id

        db_session.commit()

        response = test_client.get("/api/hall-of-fame")
        assert response.status_code == 200

        data = response.json()
        assert len(data["dynasties"]) == 0

    def test_dynasty_only_counts_same_league(self, test_client, db_session):
        """Test that dynasties only count consecutive wins in same league."""
        owner = create_test_owner(db_session, "Multi League", sleeper_id="hof_ml")
        league1 = create_test_league(db_session, "League 1", league_id="hof_l1")
        league2 = create_test_league(db_session, "League 2", league_id="hof_l2")

        # Win in League 1 in 2022
        season1 = create_test_season(db_session, league1, 2022)
        team1 = create_test_team(db_session, season1, owner, "L1 Team", final_rank=1)
        season1.champion_team_id = team1.id

        # Win in League 2 in 2023 (different league, doesn't count as dynasty)
        season2 = create_test_season(db_session, league2, 2023)
        team2 = create_test_team(db_session, season2, owner, "L2 Team", final_rank=1)
        season2.champion_team_id = team2.id

        db_session.commit()

        response = test_client.get("/api/hall-of-fame")
        assert response.status_code == 200

        data = response.json()
        # No dynasty because wins are in different leagues
        assert len(data["dynasties"]) == 0


class TestHallOfFameWithTies:
    """Test Hall of Fame with tie records."""

    def test_champion_with_ties_in_record(self, test_client, db_session):
        """Test that champion record includes ties when present."""
        owner = create_test_owner(db_session, "Tie Champ", sleeper_id="hof_tie")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        # Create team with ties
        team = Team(
            season_id=season.id,
            owner_id=owner.id,
            name="Tie Team",
            wins=10,
            losses=3,
            ties=1,
            points_for=1600.0,
            made_playoffs=True,
            final_rank=1,
        )
        db_session.add(team)
        db_session.flush()

        season.champion_team_id = team.id
        db_session.commit()

        response = test_client.get("/api/hall-of-fame")
        assert response.status_code == 200

        data = response.json()
        champion = data["champions_by_year"][0]
        assert champion["record"] == "10-3-1"
