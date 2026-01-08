"""Tests for league history API endpoints."""

import pytest
from datetime import datetime
from app.db.models import Owner, League, Season, Team, Matchup, Platform


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


# ==================== Test Classes ====================

class TestListOwnersWithCareerStats:
    """Test GET /api/history/owners - list all owners with career stats."""

    def test_list_owners_empty(self, test_client):
        """Test listing owners when none exist."""
        response = test_client.get("/api/history/owners")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_owners_with_stats(self, test_client, db_session):
        """Test listing owners returns career stats."""
        # Create owner with two seasons of data
        owner = create_test_owner(db_session, "John Doe", sleeper_id="s1")
        league = create_test_league(db_session)

        season1 = create_test_season(db_session, league, 2022)
        champ_team = create_test_team(db_session, season1, owner, wins=10, losses=4,
                                       points_for=1600.0, made_playoffs=True, final_rank=1)
        # Set champion_team_id - this is the authoritative way to track championships
        season1.champion_team_id = champ_team.id

        season2 = create_test_season(db_session, league, 2023)
        create_test_team(db_session, season2, owner, wins=8, losses=6,
                         points_for=1400.0, made_playoffs=True, final_rank=3)

        db_session.commit()

        response = test_client.get("/api/history/owners")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1

        owner_data = data[0]
        assert owner_data["name"] == "John Doe"
        assert owner_data["total_wins"] == 18
        assert owner_data["total_losses"] == 10
        assert owner_data["total_points"] == 3000.0
        assert owner_data["championships"] == 1
        assert owner_data["playoff_appearances"] == 2
        assert owner_data["seasons_played"] == 2

    def test_list_owners_sorted_by_wins(self, test_client, db_session):
        """Test that owners are sorted by total wins descending."""
        owner1 = create_test_owner(db_session, "Loser", sleeper_id="s1")
        owner2 = create_test_owner(db_session, "Winner", sleeper_id="s2")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        create_test_team(db_session, season, owner1, wins=4, losses=10)
        create_test_team(db_session, season, owner2, wins=12, losses=2)

        db_session.commit()

        response = test_client.get("/api/history/owners")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Winner"
        assert data[1]["name"] == "Loser"


class TestGetOwnerHistory:
    """Test GET /api/history/owners/{id} - full history for one owner."""

    def test_get_owner_history(self, test_client, db_session):
        """Test getting full history for an owner."""
        owner = create_test_owner(db_session, "History Test", sleeper_id="s_hist")
        league = create_test_league(db_session, "Main League")

        season1 = create_test_season(db_session, league, 2022)
        team1 = create_test_team(db_session, season1, owner, "Team 2022",
                                  wins=10, losses=4, final_rank=1, regular_season_rank=2)
        # Set champion_team_id to track the championship
        season1.champion_team_id = team1.id

        season2 = create_test_season(db_session, league, 2023)
        team2 = create_test_team(db_session, season2, owner, "Team 2023",
                                  wins=8, losses=6, final_rank=3, regular_season_rank=4)

        db_session.commit()

        response = test_client.get(f"/api/history/owners/{owner.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["owner"]["id"] == owner.id
        assert data["owner"]["name"] == "History Test"

        # Check career stats
        assert data["career_stats"]["total_wins"] == 18
        assert data["career_stats"]["championships"] == 1

        # Check seasons
        assert len(data["seasons"]) == 2
        # Seasons should be sorted by year descending (most recent first)
        assert data["seasons"][0]["year"] == 2023
        assert data["seasons"][1]["year"] == 2022

    def test_get_owner_history_not_found(self, test_client):
        """Test 404 for non-existent owner."""
        response = test_client.get("/api/history/owners/9999")
        assert response.status_code == 404

    def test_owner_history_includes_matchup_count(self, test_client, db_session):
        """Test that owner history includes matchup statistics."""
        owner1 = create_test_owner(db_session, "Matchup Test", sleeper_id="s_match")
        owner2 = create_test_owner(db_session, "Opponent", sleeper_id="s_opp")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Team 1")
        team2 = create_test_team(db_session, season, owner2, "Team 2")

        # Create some matchups
        create_test_matchup(db_session, season, team1, team2, 1, 120.0, 100.0)
        create_test_matchup(db_session, season, team2, team1, 2, 90.0, 110.0)

        db_session.commit()

        response = test_client.get(f"/api/history/owners/{owner1.id}")
        assert response.status_code == 200

        data = response.json()
        # Should have matchup stats
        assert "matchups_won" in data["career_stats"]
        assert "matchups_lost" in data["career_stats"]


class TestListSeasons:
    """Test GET /api/history/seasons - list all seasons with champions."""

    def test_list_seasons_empty(self, test_client):
        """Test listing seasons when none exist."""
        response = test_client.get("/api/history/seasons")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_seasons_with_champions(self, test_client, db_session):
        """Test listing seasons shows champions."""
        owner = create_test_owner(db_session, "Champion", sleeper_id="s_champ")
        league = create_test_league(db_session, "Championship League")

        season = create_test_season(db_session, league, 2023)
        champ_team = create_test_team(db_session, season, owner, "Champion Team",
                                       wins=12, losses=2, final_rank=1)

        # Set season champion
        season.champion_team_id = champ_team.id
        db_session.commit()

        response = test_client.get("/api/history/seasons")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1

        season_data = data[0]
        assert season_data["year"] == 2023
        assert season_data["league_name"] == "Championship League"
        assert season_data["champion"]["name"] == "Champion"

    def test_list_seasons_sorted_by_year(self, test_client, db_session):
        """Test seasons are sorted by year descending."""
        league = create_test_league(db_session)
        create_test_season(db_session, league, 2021)
        create_test_season(db_session, league, 2023)
        create_test_season(db_session, league, 2022)
        db_session.commit()

        response = test_client.get("/api/history/seasons")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 3
        assert data[0]["year"] == 2023
        assert data[1]["year"] == 2022
        assert data[2]["year"] == 2021

    def test_list_seasons_filter_by_league(self, test_client, db_session):
        """Test filtering seasons by league ID."""
        league1 = create_test_league(db_session, "League 1", league_id="league_1")
        league2 = create_test_league(db_session, "League 2", league_id="league_2")

        create_test_season(db_session, league1, 2023)
        create_test_season(db_session, league2, 2023)
        db_session.commit()

        response = test_client.get(f"/api/history/seasons?league_id={league1.id}")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["league_name"] == "League 1"


class TestHeadToHead:
    """Test GET /api/history/head-to-head/{owner1}/{owner2} - rivalry stats."""

    def test_head_to_head_stats(self, test_client, db_session):
        """Test getting head-to-head stats between two owners."""
        owner1 = create_test_owner(db_session, "Owner A", sleeper_id="s_a")
        owner2 = create_test_owner(db_session, "Owner B", sleeper_id="s_b")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Team A")
        team2 = create_test_team(db_session, season, owner2, "Team B")

        # Create 5 matchups: owner1 wins 3, owner2 wins 2
        create_test_matchup(db_session, season, team1, team2, 1, 120.0, 100.0)  # Owner 1 wins
        create_test_matchup(db_session, season, team2, team1, 2, 110.0, 105.0)  # Owner 2 wins
        create_test_matchup(db_session, season, team1, team2, 3, 115.0, 95.0)   # Owner 1 wins
        create_test_matchup(db_session, season, team2, team1, 4, 125.0, 120.0)  # Owner 2 wins
        create_test_matchup(db_session, season, team1, team2, 5, 130.0, 110.0, is_playoff=True)  # Owner 1 wins (playoff)

        db_session.commit()

        response = test_client.get(f"/api/history/head-to-head/{owner1.id}/{owner2.id}")
        assert response.status_code == 200

        data = response.json()

        # Owner1 perspective
        assert data["owner1"]["id"] == owner1.id
        assert data["owner1"]["name"] == "Owner A"
        assert data["owner1_wins"] == 3
        assert data["owner1_avg_score"] == pytest.approx(118.0, rel=0.1)  # (120+105+115+120+130)/5

        # Owner2 perspective
        assert data["owner2"]["id"] == owner2.id
        assert data["owner2"]["name"] == "Owner B"
        assert data["owner2_wins"] == 2

        # Total matchups
        assert data["total_matchups"] == 5
        assert data["ties"] == 0

        # Playoff stats
        assert data["playoff_matchups"] == 1
        assert data["owner1_playoff_wins"] == 1

    def test_head_to_head_with_ties(self, test_client, db_session):
        """Test head-to-head with tied matchups."""
        owner1 = create_test_owner(db_session, "Owner A", sleeper_id="s_tie_a")
        owner2 = create_test_owner(db_session, "Owner B", sleeper_id="s_tie_b")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Team A")
        team2 = create_test_team(db_session, season, owner2, "Team B")

        # Create matchup with tie
        create_test_matchup(db_session, season, team1, team2, 1, 100.0, 100.0)
        db_session.commit()

        response = test_client.get(f"/api/history/head-to-head/{owner1.id}/{owner2.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["ties"] == 1
        assert data["owner1_wins"] == 0
        assert data["owner2_wins"] == 0

    def test_head_to_head_owner_not_found(self, test_client, db_session):
        """Test 404 when owner not found."""
        owner = create_test_owner(db_session, "Existing", sleeper_id="s_exist")
        db_session.commit()

        response = test_client.get(f"/api/history/head-to-head/{owner.id}/9999")
        assert response.status_code == 404

    def test_head_to_head_no_matchups(self, test_client, db_session):
        """Test head-to-head when owners have never played."""
        owner1 = create_test_owner(db_session, "Owner A", sleeper_id="s_no_a")
        owner2 = create_test_owner(db_session, "Owner B", sleeper_id="s_no_b")
        db_session.commit()

        response = test_client.get(f"/api/history/head-to-head/{owner1.id}/{owner2.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["total_matchups"] == 0
        assert data["owner1_wins"] == 0
        assert data["owner2_wins"] == 0

    def test_head_to_head_includes_all_matchups(self, test_client, db_session):
        """Test that head-to-head returns list of all matchups."""
        owner1 = create_test_owner(db_session, "Owner A", sleeper_id="s_list_a")
        owner2 = create_test_owner(db_session, "Owner B", sleeper_id="s_list_b")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Team A")
        team2 = create_test_team(db_session, season, owner2, "Team B")

        create_test_matchup(db_session, season, team1, team2, 1, 120.0, 100.0)
        create_test_matchup(db_session, season, team2, team1, 2, 90.0, 110.0)
        db_session.commit()

        response = test_client.get(f"/api/history/head-to-head/{owner1.id}/{owner2.id}")
        assert response.status_code == 200

        data = response.json()
        assert "matchups" in data
        assert len(data["matchups"]) == 2

        # Verify matchup data
        matchup = data["matchups"][0]
        assert "week" in matchup
        assert "year" in matchup
        assert "owner1_score" in matchup
        assert "owner2_score" in matchup
        assert "is_playoff" in matchup


class TestHeadToHeadCrossSeasons:
    """Test head-to-head stats across multiple seasons."""

    def test_head_to_head_multiple_seasons(self, test_client, db_session):
        """Test head-to-head aggregates across seasons."""
        owner1 = create_test_owner(db_session, "Owner A", sleeper_id="s_multi_a")
        owner2 = create_test_owner(db_session, "Owner B", sleeper_id="s_multi_b")
        league = create_test_league(db_session)

        # Season 2022
        season1 = create_test_season(db_session, league, 2022)
        team1_s1 = create_test_team(db_session, season1, owner1, "Team A 2022")
        team2_s1 = create_test_team(db_session, season1, owner2, "Team B 2022")
        create_test_matchup(db_session, season1, team1_s1, team2_s1, 1, 120.0, 100.0)

        # Season 2023
        season2 = create_test_season(db_session, league, 2023)
        team1_s2 = create_test_team(db_session, season2, owner1, "Team A 2023")
        team2_s2 = create_test_team(db_session, season2, owner2, "Team B 2023")
        create_test_matchup(db_session, season2, team1_s2, team2_s2, 1, 90.0, 110.0)

        db_session.commit()

        response = test_client.get(f"/api/history/head-to-head/{owner1.id}/{owner2.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["total_matchups"] == 2
        assert data["owner1_wins"] == 1
        assert data["owner2_wins"] == 1

        # Check matchups include year
        years = [m["year"] for m in data["matchups"]]
        assert 2022 in years
        assert 2023 in years


class TestPodiumFinishes:
    """Test 2nd and 3rd place tracking in career stats."""

    def test_owner_stats_include_runner_up_and_third_place(self, test_client, db_session):
        """Test that owner stats include runner_up_finishes and third_place_finishes."""
        owner = create_test_owner(db_session, "Podium Test", sleeper_id="s_podium")
        league = create_test_league(db_session)

        # Season 1 - owner gets 2nd place (runner-up)
        season1 = create_test_season(db_session, league, 2021)
        team1 = create_test_team(db_session, season1, owner, "Team 2021",
                                  wins=10, losses=4, made_playoffs=True)
        season1.runner_up_team_id = team1.id

        # Season 2 - owner gets 3rd place
        season2 = create_test_season(db_session, league, 2022)
        team2 = create_test_team(db_session, season2, owner, "Team 2022",
                                  wins=9, losses=5, made_playoffs=True)
        season2.third_place_team_id = team2.id

        # Season 3 - owner wins championship
        season3 = create_test_season(db_session, league, 2023)
        team3 = create_test_team(db_session, season3, owner, "Team 2023",
                                  wins=12, losses=2, made_playoffs=True)
        season3.champion_team_id = team3.id

        db_session.commit()

        response = test_client.get("/api/history/owners")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1

        owner_data = data[0]
        assert owner_data["name"] == "Podium Test"
        assert owner_data["championships"] == 1
        assert owner_data["runner_up_finishes"] == 1
        assert owner_data["third_place_finishes"] == 1
        assert owner_data["seasons_played"] == 3

    def test_owner_history_includes_runner_up_and_third_place(self, test_client, db_session):
        """Test that individual owner history includes 2nd/3rd place finishes."""
        owner = create_test_owner(db_session, "Career Test", sleeper_id="s_career")
        league = create_test_league(db_session)

        # Create multiple seasons with various finishes
        for year, placement in [(2020, "runner_up"), (2021, "third"), (2022, "runner_up"), (2023, "champion")]:
            season = create_test_season(db_session, league, year)
            team = create_test_team(db_session, season, owner, f"Team {year}",
                                     wins=10, losses=4, made_playoffs=True)
            if placement == "champion":
                season.champion_team_id = team.id
            elif placement == "runner_up":
                season.runner_up_team_id = team.id
            elif placement == "third":
                season.third_place_team_id = team.id

        db_session.commit()

        response = test_client.get(f"/api/history/owners/{owner.id}")
        assert response.status_code == 200

        data = response.json()
        career_stats = data["career_stats"]

        assert career_stats["championships"] == 1
        assert career_stats["runner_up_finishes"] == 2
        assert career_stats["third_place_finishes"] == 1

    def test_multiple_owners_placement_tracking(self, test_client, db_session):
        """Test tracking placements across multiple owners."""
        owner1 = create_test_owner(db_session, "Always Second", sleeper_id="s_second")
        owner2 = create_test_owner(db_session, "Always Third", sleeper_id="s_third")
        owner3 = create_test_owner(db_session, "Champion", sleeper_id="s_champ")
        league = create_test_league(db_session)

        # Create 3 seasons with consistent placements
        for year in [2021, 2022, 2023]:
            season = create_test_season(db_session, league, year)
            team1 = create_test_team(db_session, season, owner1, f"Team1 {year}")
            team2 = create_test_team(db_session, season, owner2, f"Team2 {year}")
            team3 = create_test_team(db_session, season, owner3, f"Team3 {year}")

            season.champion_team_id = team3.id
            season.runner_up_team_id = team1.id
            season.third_place_team_id = team2.id

        db_session.commit()

        response = test_client.get("/api/history/owners")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 3

        # Find each owner in the response
        owner1_data = next(o for o in data if o["name"] == "Always Second")
        owner2_data = next(o for o in data if o["name"] == "Always Third")
        owner3_data = next(o for o in data if o["name"] == "Champion")

        assert owner1_data["championships"] == 0
        assert owner1_data["runner_up_finishes"] == 3
        assert owner1_data["third_place_finishes"] == 0

        assert owner2_data["championships"] == 0
        assert owner2_data["runner_up_finishes"] == 0
        assert owner2_data["third_place_finishes"] == 3

        assert owner3_data["championships"] == 3
        assert owner3_data["runner_up_finishes"] == 0
        assert owner3_data["third_place_finishes"] == 0
