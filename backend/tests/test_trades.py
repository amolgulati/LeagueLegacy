"""Tests for trade analytics API endpoints."""

import pytest
from datetime import datetime, timedelta
from app.db.models import Owner, League, Season, Team, Trade, Matchup, Platform


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


def create_test_trade(db_session, season, teams, week=5, assets=None,
                      trade_date=None, status="completed"):
    """Create a test trade between teams."""
    if trade_date is None:
        trade_date = datetime.utcnow()

    trade = Trade(
        season_id=season.id,
        trade_date=trade_date,
        week=week,
        assets_exchanged=assets or '{"team1": ["PlayerA"], "team2": ["PlayerB"]}',
        status=status,
    )
    db_session.add(trade)
    db_session.flush()

    # Link teams to trade
    for team in teams:
        trade.teams.append(team)

    db_session.flush()
    return trade


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

class TestListAllTrades:
    """Test GET /api/trades - list all trades with filters."""

    def test_list_trades_empty(self, test_client):
        """Test listing trades when none exist."""
        response = test_client.get("/api/trades")
        assert response.status_code == 200
        data = response.json()
        assert data["trades"] == []
        assert data["total"] == 0

    def test_list_trades_basic(self, test_client, db_session):
        """Test listing all trades."""
        owner1 = create_test_owner(db_session, "Owner1", sleeper_id="s_t1")
        owner2 = create_test_owner(db_session, "Owner2", sleeper_id="s_t2")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Team1")
        team2 = create_test_team(db_session, season, owner2, "Team2")

        trade = create_test_trade(db_session, season, [team1, team2], week=5)
        db_session.commit()

        response = test_client.get("/api/trades")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        assert len(data["trades"]) == 1

        trade_data = data["trades"][0]
        assert trade_data["week"] == 5
        assert trade_data["season_year"] == 2023
        assert len(trade_data["teams"]) == 2

    def test_list_trades_filter_by_owner(self, test_client, db_session):
        """Test filtering trades by owner_id."""
        owner1 = create_test_owner(db_session, "Owner1", sleeper_id="s_fo1")
        owner2 = create_test_owner(db_session, "Owner2", sleeper_id="s_fo2")
        owner3 = create_test_owner(db_session, "Owner3", sleeper_id="s_fo3")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Team1")
        team2 = create_test_team(db_session, season, owner2, "Team2")
        team3 = create_test_team(db_session, season, owner3, "Team3")

        # Trade 1: owner1 <-> owner2
        create_test_trade(db_session, season, [team1, team2], week=5)
        # Trade 2: owner2 <-> owner3
        create_test_trade(db_session, season, [team2, team3], week=6)
        db_session.commit()

        # Filter by owner1 - should return 1 trade
        response = test_client.get(f"/api/trades?owner_id={owner1.id}")
        assert response.status_code == 200
        assert response.json()["total"] == 1

        # Filter by owner2 - should return 2 trades
        response = test_client.get(f"/api/trades?owner_id={owner2.id}")
        assert response.status_code == 200
        assert response.json()["total"] == 2

    def test_list_trades_filter_by_season(self, test_client, db_session):
        """Test filtering trades by season_id."""
        owner1 = create_test_owner(db_session, "Owner1", sleeper_id="s_fs1")
        owner2 = create_test_owner(db_session, "Owner2", sleeper_id="s_fs2")
        league = create_test_league(db_session)

        season2022 = create_test_season(db_session, league, 2022)
        season2023 = create_test_season(db_session, league, 2023)

        team1_2022 = create_test_team(db_session, season2022, owner1, "Team1 2022")
        team2_2022 = create_test_team(db_session, season2022, owner2, "Team2 2022")
        team1_2023 = create_test_team(db_session, season2023, owner1, "Team1 2023")
        team2_2023 = create_test_team(db_session, season2023, owner2, "Team2 2023")

        create_test_trade(db_session, season2022, [team1_2022, team2_2022], week=5)
        create_test_trade(db_session, season2023, [team1_2023, team2_2023], week=5)
        db_session.commit()

        response = test_client.get(f"/api/trades?season_id={season2023.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["trades"][0]["season_year"] == 2023

    def test_list_trades_filter_by_league(self, test_client, db_session):
        """Test filtering trades by league_id."""
        owner1 = create_test_owner(db_session, "Owner1", sleeper_id="s_fl1")
        owner2 = create_test_owner(db_session, "Owner2", sleeper_id="s_fl2")

        league1 = create_test_league(db_session, "League 1", league_id="lg1")
        league2 = create_test_league(db_session, "League 2", league_id="lg2")

        season1 = create_test_season(db_session, league1, 2023)
        season2 = create_test_season(db_session, league2, 2023)

        team1 = create_test_team(db_session, season1, owner1, "Team1")
        team2 = create_test_team(db_session, season1, owner2, "Team2")
        team3 = create_test_team(db_session, season2, owner1, "Team3")
        team4 = create_test_team(db_session, season2, owner2, "Team4")

        create_test_trade(db_session, season1, [team1, team2], week=5)
        create_test_trade(db_session, season2, [team3, team4], week=5)
        db_session.commit()

        response = test_client.get(f"/api/trades?league_id={league1.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["trades"][0]["league_name"] == "League 1"

    def test_list_trades_pagination(self, test_client, db_session):
        """Test trades pagination with limit and offset."""
        owner1 = create_test_owner(db_session, "Owner1", sleeper_id="s_pg1")
        owner2 = create_test_owner(db_session, "Owner2", sleeper_id="s_pg2")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Team1")
        team2 = create_test_team(db_session, season, owner2, "Team2")

        # Create 5 trades
        for week in range(1, 6):
            create_test_trade(db_session, season, [team1, team2], week=week)
        db_session.commit()

        # Get first 2
        response = test_client.get("/api/trades?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["trades"]) == 2

        # Get next 2
        response = test_client.get("/api/trades?limit=2&offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) == 2


class TestGetOwnerTrades:
    """Test GET /api/trades/owners/{id} - trades for an owner."""

    def test_get_owner_trades_empty(self, test_client, db_session):
        """Test getting trades for owner with none."""
        owner = create_test_owner(db_session, "No Trades", sleeper_id="s_nt")
        db_session.commit()

        response = test_client.get(f"/api/trades/owners/{owner.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["trades"] == []
        assert data["total_trades"] == 0

    def test_get_owner_trades_basic(self, test_client, db_session):
        """Test getting trades for an owner."""
        owner1 = create_test_owner(db_session, "Trader", sleeper_id="s_otr")
        owner2 = create_test_owner(db_session, "Partner", sleeper_id="s_ptr")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Team1")
        team2 = create_test_team(db_session, season, owner2, "Team2")

        create_test_trade(db_session, season, [team1, team2], week=3)
        create_test_trade(db_session, season, [team1, team2], week=7)
        db_session.commit()

        response = test_client.get(f"/api/trades/owners/{owner1.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["total_trades"] == 2
        assert len(data["trades"]) == 2
        assert data["owner"]["id"] == owner1.id

    def test_get_owner_trades_not_found(self, test_client):
        """Test 404 for non-existent owner."""
        response = test_client.get("/api/trades/owners/9999")
        assert response.status_code == 404


class TestTradeFrequency:
    """Test trade frequency per owner calculations."""

    def test_trade_frequency_included_in_response(self, test_client, db_session):
        """Test that trade frequency is included in owner trades response."""
        owner1 = create_test_owner(db_session, "Trader", sleeper_id="s_freq1")
        owner2 = create_test_owner(db_session, "Partner", sleeper_id="s_freq2")
        league = create_test_league(db_session)

        season2022 = create_test_season(db_session, league, 2022)
        season2023 = create_test_season(db_session, league, 2023)

        team1_2022 = create_test_team(db_session, season2022, owner1, "Team1 2022")
        team2_2022 = create_test_team(db_session, season2022, owner2, "Team2 2022")
        team1_2023 = create_test_team(db_session, season2023, owner1, "Team1 2023")
        team2_2023 = create_test_team(db_session, season2023, owner2, "Team2 2023")

        # 2 trades in 2022
        create_test_trade(db_session, season2022, [team1_2022, team2_2022], week=3)
        create_test_trade(db_session, season2022, [team1_2022, team2_2022], week=7)
        # 3 trades in 2023
        create_test_trade(db_session, season2023, [team1_2023, team2_2023], week=2)
        create_test_trade(db_session, season2023, [team1_2023, team2_2023], week=5)
        create_test_trade(db_session, season2023, [team1_2023, team2_2023], week=9)
        db_session.commit()

        response = test_client.get(f"/api/trades/owners/{owner1.id}")
        assert response.status_code == 200

        data = response.json()
        assert "trade_frequency" in data
        assert data["total_trades"] == 5
        assert data["trade_frequency"]["trades_per_season"] == 2.5  # 5 trades / 2 seasons
        assert data["trade_frequency"]["seasons_played"] == 2


class TestMostCommonTradePartners:
    """Test most common trade partners calculations."""

    def test_trade_partners_included_in_response(self, test_client, db_session):
        """Test that trade partners are included in owner trades response."""
        owner1 = create_test_owner(db_session, "Main Trader", sleeper_id="s_mp1")
        owner2 = create_test_owner(db_session, "Partner A", sleeper_id="s_mp2")
        owner3 = create_test_owner(db_session, "Partner B", sleeper_id="s_mp3")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Team1")
        team2 = create_test_team(db_session, season, owner2, "Team2")
        team3 = create_test_team(db_session, season, owner3, "Team3")

        # 3 trades with owner2, 1 trade with owner3
        create_test_trade(db_session, season, [team1, team2], week=1)
        create_test_trade(db_session, season, [team1, team2], week=3)
        create_test_trade(db_session, season, [team1, team2], week=5)
        create_test_trade(db_session, season, [team1, team3], week=7)
        db_session.commit()

        response = test_client.get(f"/api/trades/owners/{owner1.id}")
        assert response.status_code == 200

        data = response.json()
        assert "trade_partners" in data

        # Owner2 should be top partner with 3 trades
        partners = data["trade_partners"]
        assert len(partners) == 2
        assert partners[0]["owner"]["name"] == "Partner A"
        assert partners[0]["trade_count"] == 3
        assert partners[1]["owner"]["name"] == "Partner B"
        assert partners[1]["trade_count"] == 1


class TestWinRateBeforeAfterTrades:
    """Test win rate before/after trades calculations."""

    def test_win_rate_before_after_trades(self, test_client, db_session):
        """Test calculating win rate before and after trades."""
        owner1 = create_test_owner(db_session, "Trader", sleeper_id="s_wr1")
        owner2 = create_test_owner(db_session, "Opponent", sleeper_id="s_wr2")
        owner3 = create_test_owner(db_session, "Partner", sleeper_id="s_wr3")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Team1")
        team2 = create_test_team(db_session, season, owner2, "Team2")
        team3 = create_test_team(db_session, season, owner3, "Team3")

        # Weeks 1-4: Owner1 goes 1-3 (loses most)
        create_test_matchup(db_session, season, team1, team2, 1, 90, 100)  # Loss
        create_test_matchup(db_session, season, team1, team2, 2, 80, 100)  # Loss
        create_test_matchup(db_session, season, team1, team2, 3, 85, 100)  # Loss
        create_test_matchup(db_session, season, team1, team2, 4, 110, 100) # Win

        # Trade happens in week 5
        create_test_trade(db_session, season, [team1, team3], week=5)

        # Weeks 6-9: Owner1 goes 3-1 (wins most)
        create_test_matchup(db_session, season, team1, team2, 6, 120, 100) # Win
        create_test_matchup(db_session, season, team1, team2, 7, 115, 100) # Win
        create_test_matchup(db_session, season, team1, team2, 8, 110, 100) # Win
        create_test_matchup(db_session, season, team1, team2, 9, 90, 100)  # Loss

        db_session.commit()

        response = test_client.get(f"/api/trades/owners/{owner1.id}")
        assert response.status_code == 200

        data = response.json()
        assert "win_rate_analysis" in data

        analysis = data["win_rate_analysis"]
        # Before trade: 1 win, 3 losses = 25%
        assert analysis["win_rate_before_trades"] == 25.0
        # After trade: 3 wins, 1 loss = 75%
        assert analysis["win_rate_after_trades"] == 75.0
        # Change should be positive
        assert analysis["win_rate_change"] == 50.0

    def test_win_rate_no_trades(self, test_client, db_session):
        """Test win rate analysis with no trades."""
        owner = create_test_owner(db_session, "No Trades", sleeper_id="s_ntr")
        db_session.commit()

        response = test_client.get(f"/api/trades/owners/{owner.id}")
        assert response.status_code == 200

        data = response.json()
        assert "win_rate_analysis" in data
        assert data["win_rate_analysis"]["win_rate_before_trades"] is None
        assert data["win_rate_analysis"]["win_rate_after_trades"] is None

    def test_win_rate_multiple_trades(self, test_client, db_session):
        """Test win rate analysis with multiple trades."""
        owner1 = create_test_owner(db_session, "Trader", sleeper_id="s_mtr1")
        owner2 = create_test_owner(db_session, "Opponent", sleeper_id="s_mtr2")
        owner3 = create_test_owner(db_session, "Partner", sleeper_id="s_mtr3")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Team1")
        team2 = create_test_team(db_session, season, owner2, "Team2")
        team3 = create_test_team(db_session, season, owner3, "Team3")

        # Week 1: Loss
        create_test_matchup(db_session, season, team1, team2, 1, 90, 100)
        # Trade at week 2
        create_test_trade(db_session, season, [team1, team3], week=2)
        # Week 3: Win
        create_test_matchup(db_session, season, team1, team2, 3, 110, 100)
        # Trade at week 4
        create_test_trade(db_session, season, [team1, team3], week=4)
        # Weeks 5-6: Win, Win
        create_test_matchup(db_session, season, team1, team2, 5, 115, 100)
        create_test_matchup(db_session, season, team1, team2, 6, 120, 100)

        db_session.commit()

        response = test_client.get(f"/api/trades/owners/{owner1.id}")
        assert response.status_code == 200

        data = response.json()
        # Uses FIRST trade as dividing point
        # Before week 2: 0-1 = 0%
        # After week 2: 3-0 = 100%
        analysis = data["win_rate_analysis"]
        assert analysis["win_rate_before_trades"] == 0.0
        assert analysis["win_rate_after_trades"] == 100.0


class TestTradeStats:
    """Test GET /api/trades/stats - overall trade statistics."""

    def test_trade_stats_empty(self, test_client):
        """Test stats when no trades exist."""
        response = test_client.get("/api/trades/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_trades"] == 0
        assert data["most_active_traders"] == []

    def test_trade_stats_most_active_traders(self, test_client, db_session):
        """Test most active traders in stats."""
        owner1 = create_test_owner(db_session, "Big Trader", sleeper_id="s_bt1")
        owner2 = create_test_owner(db_session, "Medium Trader", sleeper_id="s_bt2")
        owner3 = create_test_owner(db_session, "Small Trader", sleeper_id="s_bt3")
        league = create_test_league(db_session)
        season = create_test_season(db_session, league, 2023)

        team1 = create_test_team(db_session, season, owner1, "Team1")
        team2 = create_test_team(db_session, season, owner2, "Team2")
        team3 = create_test_team(db_session, season, owner3, "Team3")

        # Owner1 involved in 4 trades
        create_test_trade(db_session, season, [team1, team2], week=1)
        create_test_trade(db_session, season, [team1, team2], week=2)
        create_test_trade(db_session, season, [team1, team3], week=3)
        create_test_trade(db_session, season, [team1, team3], week=4)
        # Owner2 involved in 3 trades (2 above + 1 more)
        create_test_trade(db_session, season, [team2, team3], week=5)
        db_session.commit()

        response = test_client.get("/api/trades/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["total_trades"] == 5

        traders = data["most_active_traders"]
        assert len(traders) >= 3
        # Owner1 should be first with 4 trades
        assert traders[0]["owner"]["name"] == "Big Trader"
        assert traders[0]["trade_count"] == 4

    def test_trade_stats_by_season(self, test_client, db_session):
        """Test trade stats per season."""
        owner1 = create_test_owner(db_session, "Owner1", sleeper_id="s_ss1")
        owner2 = create_test_owner(db_session, "Owner2", sleeper_id="s_ss2")
        league = create_test_league(db_session)

        season2022 = create_test_season(db_session, league, 2022)
        season2023 = create_test_season(db_session, league, 2023)

        team1_2022 = create_test_team(db_session, season2022, owner1, "Team1 2022")
        team2_2022 = create_test_team(db_session, season2022, owner2, "Team2 2022")
        team1_2023 = create_test_team(db_session, season2023, owner1, "Team1 2023")
        team2_2023 = create_test_team(db_session, season2023, owner2, "Team2 2023")

        # 2 trades in 2022
        create_test_trade(db_session, season2022, [team1_2022, team2_2022], week=3)
        create_test_trade(db_session, season2022, [team1_2022, team2_2022], week=7)
        # 5 trades in 2023
        for week in range(1, 6):
            create_test_trade(db_session, season2023, [team1_2023, team2_2023], week=week)
        db_session.commit()

        response = test_client.get("/api/trades/stats")
        assert response.status_code == 200

        data = response.json()
        assert "trades_by_season" in data

        season_stats = {s["year"]: s["trade_count"] for s in data["trades_by_season"]}
        assert season_stats[2022] == 2
        assert season_stats[2023] == 5
