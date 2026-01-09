"""Tests for owner mapping system and API endpoints."""

import pytest
from datetime import datetime
from app.db.models import Owner, League, Season, Team, Platform


class TestOwnerMappingModels:
    """Test owner mapping at the model level."""

    def test_create_owner_with_sleeper_id(self, db_session):
        """Test creating an owner with Sleeper user ID."""
        owner = Owner(
            name="John Doe",
            display_name="JohnnyD",
            sleeper_user_id="sleeper_123",
        )
        db_session.add(owner)
        db_session.commit()

        assert owner.id is not None
        assert owner.sleeper_user_id == "sleeper_123"
        assert owner.yahoo_user_id is None

    def test_create_owner_with_yahoo_id(self, db_session):
        """Test creating an owner with Yahoo user ID."""
        owner = Owner(
            name="Jane Doe",
            display_name="JaneD",
            yahoo_user_id="yahoo_456",
        )
        db_session.add(owner)
        db_session.commit()

        assert owner.id is not None
        assert owner.yahoo_user_id == "yahoo_456"
        assert owner.sleeper_user_id is None

    def test_map_owner_to_both_platforms(self, db_session):
        """Test mapping an owner to both Yahoo and Sleeper."""
        owner = Owner(
            name="Multi Platform User",
            sleeper_user_id="sleeper_789",
        )
        db_session.add(owner)
        db_session.commit()

        # Now link to Yahoo
        owner.yahoo_user_id = "yahoo_789"
        db_session.commit()

        # Refresh and verify
        db_session.refresh(owner)
        assert owner.sleeper_user_id == "sleeper_789"
        assert owner.yahoo_user_id == "yahoo_789"

    def test_unique_sleeper_user_id(self, db_session):
        """Test that Sleeper user ID must be unique."""
        owner1 = Owner(name="Owner 1", sleeper_user_id="sleeper_unique")
        db_session.add(owner1)
        db_session.commit()

        # Try to create another owner with same Sleeper ID
        owner2 = Owner(name="Owner 2", sleeper_user_id="sleeper_unique")
        db_session.add(owner2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_unique_yahoo_user_id(self, db_session):
        """Test that Yahoo user ID must be unique."""
        owner1 = Owner(name="Owner 1", yahoo_user_id="yahoo_unique")
        db_session.add(owner1)
        db_session.commit()

        owner2 = Owner(name="Owner 2", yahoo_user_id="yahoo_unique")
        db_session.add(owner2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


class TestOwnerStatsAggregation:
    """Test that stats aggregate correctly across platforms."""

    def _create_league_with_teams(self, db_session, platform, owner, year):
        """Helper to create a league with a team for the owner."""
        league = League(
            name=f"Test League {platform.value}",
            platform=platform,
            platform_league_id=f"{platform.value}_{year}",
            team_count=10,
        )
        db_session.add(league)
        db_session.flush()

        season = Season(
            league_id=league.id,
            year=year,
            regular_season_weeks=14,
            playoff_weeks=3,
        )
        db_session.add(season)
        db_session.flush()

        team = Team(
            season_id=season.id,
            owner_id=owner.id,
            name=f"{owner.name}'s Team",
            platform_team_id=f"team_{year}",
            wins=10,
            losses=4,
            ties=0,
            points_for=1500.0,
            points_against=1300.0,
            made_playoffs=True,
        )
        db_session.add(team)
        db_session.commit()

        return league, season, team

    def test_aggregate_stats_single_platform(self, db_session):
        """Test aggregating stats for owner on single platform."""
        owner = Owner(
            name="Single Platform User",
            sleeper_user_id="sleeper_agg1",
        )
        db_session.add(owner)
        db_session.commit()

        # Create two seasons
        self._create_league_with_teams(db_session, Platform.SLEEPER, owner, 2022)
        self._create_league_with_teams(db_session, Platform.SLEEPER, owner, 2023)

        # Aggregate stats through teams relationship
        total_wins = sum(team.wins for team in owner.teams)
        total_losses = sum(team.losses for team in owner.teams)
        total_points = sum(team.points_for for team in owner.teams)

        assert total_wins == 20  # 10 + 10
        assert total_losses == 8  # 4 + 4
        assert total_points == 3000.0  # 1500 + 1500

    def test_aggregate_stats_cross_platform(self, db_session):
        """Test aggregating stats for owner across both platforms."""
        owner = Owner(
            name="Cross Platform User",
            sleeper_user_id="sleeper_cross",
            yahoo_user_id="yahoo_cross",
        )
        db_session.add(owner)
        db_session.commit()

        # Create season on Sleeper
        self._create_league_with_teams(db_session, Platform.SLEEPER, owner, 2022)

        # Create season on Yahoo
        self._create_league_with_teams(db_session, Platform.YAHOO, owner, 2023)

        # Aggregate stats through teams relationship
        total_wins = sum(team.wins for team in owner.teams)
        playoff_appearances = sum(1 for team in owner.teams if team.made_playoffs)

        assert total_wins == 20
        assert playoff_appearances == 2
        assert len(owner.teams) == 2


class TestOwnerMappingAPI:
    """Test owner mapping API endpoints."""

    def test_list_owners(self, test_client, db_session):
        """Test GET /api/owners returns all owners."""
        # Create some owners
        owner1 = Owner(name="Owner 1", sleeper_user_id="s1")
        owner2 = Owner(name="Owner 2", yahoo_user_id="y2")
        db_session.add_all([owner1, owner2])
        db_session.commit()

        response = test_client.get("/api/owners")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert any(o["name"] == "Owner 1" for o in data)
        assert any(o["name"] == "Owner 2" for o in data)

    def test_get_owner_by_id(self, test_client, db_session):
        """Test GET /api/owners/{id} returns owner with stats."""
        owner = Owner(name="Test Owner", sleeper_user_id="s_test")
        db_session.add(owner)
        db_session.commit()

        response = test_client.get(f"/api/owners/{owner.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == owner.id
        assert data["name"] == "Test Owner"
        assert data["sleeper_user_id"] == "s_test"

    def test_get_owner_not_found(self, test_client):
        """Test GET /api/owners/{id} returns 404 for non-existent owner."""
        response = test_client.get("/api/owners/9999")
        assert response.status_code == 404

    def test_create_owner_mapping(self, test_client, db_session):
        """Test POST /api/owners/mapping to create new owner with mappings."""
        response = test_client.post(
            "/api/owners/mapping",
            json={
                "name": "New Owner",
                "display_name": "NewOwner",
                "sleeper_user_id": "sleeper_new",
                "yahoo_user_id": "yahoo_new",
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "New Owner"
        assert data["sleeper_user_id"] == "sleeper_new"
        assert data["yahoo_user_id"] == "yahoo_new"

    def test_update_owner_mapping(self, test_client, db_session):
        """Test PUT /api/owners/{id}/mapping to link platforms."""
        # Create owner with only Sleeper
        owner = Owner(name="Link Test", sleeper_user_id="s_link")
        db_session.add(owner)
        db_session.commit()

        # Now link Yahoo
        response = test_client.put(
            f"/api/owners/{owner.id}/mapping",
            json={"yahoo_user_id": "y_link"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["sleeper_user_id"] == "s_link"
        assert data["yahoo_user_id"] == "y_link"

    def test_merge_owners(self, test_client, db_session):
        """Test POST /api/owners/merge to merge two owners into one."""
        # Create two separate owners (one for each platform)
        sleeper_owner = Owner(
            name="Sleeper Only",
            sleeper_user_id="s_merge",
        )
        yahoo_owner = Owner(
            name="Yahoo Only",
            yahoo_user_id="y_merge",
        )
        db_session.add_all([sleeper_owner, yahoo_owner])
        db_session.commit()

        # Create teams for each owner
        league = League(
            name="Test League",
            platform=Platform.SLEEPER,
            platform_league_id="merge_league",
        )
        db_session.add(league)
        db_session.flush()

        season = Season(league_id=league.id, year=2023)
        db_session.add(season)
        db_session.flush()

        team1 = Team(
            season_id=season.id,
            owner_id=sleeper_owner.id,
            name="Sleeper Team",
            wins=8,
            losses=6,
        )
        db_session.add(team1)
        db_session.commit()

        # Merge owners: keep sleeper_owner, merge yahoo into it
        response = test_client.post(
            "/api/owners/merge",
            json={
                "primary_owner_id": sleeper_owner.id,
                "secondary_owner_id": yahoo_owner.id,
            },
        )
        assert response.status_code == 200

        data = response.json()
        # Primary owner should now have both platform IDs
        assert data["sleeper_user_id"] == "s_merge"
        assert data["yahoo_user_id"] == "y_merge"

    def test_get_unmapped_users(self, test_client, db_session):
        """Test GET /api/owners/unmapped returns owners without full mapping."""
        # Owner with only Sleeper
        owner1 = Owner(name="Sleeper Only", sleeper_user_id="s_only")
        # Owner with both
        owner2 = Owner(name="Both Platforms", sleeper_user_id="s_both", yahoo_user_id="y_both")
        # Owner with only Yahoo
        owner3 = Owner(name="Yahoo Only", yahoo_user_id="y_only")
        db_session.add_all([owner1, owner2, owner3])
        db_session.commit()

        response = test_client.get("/api/owners/unmapped")
        assert response.status_code == 200

        data = response.json()
        # Should return owners without full mapping (owner1 and owner3)
        assert len(data) == 2
        unmapped_names = [o["name"] for o in data]
        assert "Sleeper Only" in unmapped_names
        assert "Yahoo Only" in unmapped_names
        assert "Both Platforms" not in unmapped_names

    def test_get_owner_career_stats(self, test_client, db_session):
        """Test GET /api/owners/{id}/stats returns aggregated career stats."""
        owner = Owner(name="Career Stats Test", sleeper_user_id="s_career")
        db_session.add(owner)
        db_session.commit()

        # Create leagues and teams
        league = League(
            name="Test League",
            platform=Platform.SLEEPER,
            platform_league_id="career_league",
        )
        db_session.add(league)
        db_session.flush()

        # Season 1
        season1 = Season(league_id=league.id, year=2022)
        db_session.add(season1)
        db_session.flush()

        team1 = Team(
            season_id=season1.id,
            owner_id=owner.id,
            name="Team 2022",
            wins=10,
            losses=4,
            points_for=1600.0,
            made_playoffs=True,
            final_rank=1,  # Champion
        )
        db_session.add(team1)

        # Season 2
        season2 = Season(league_id=league.id, year=2023)
        db_session.add(season2)
        db_session.flush()

        team2 = Team(
            season_id=season2.id,
            owner_id=owner.id,
            name="Team 2023",
            wins=8,
            losses=6,
            points_for=1400.0,
            made_playoffs=True,
            final_rank=3,
        )
        db_session.add(team2)
        db_session.commit()

        response = test_client.get(f"/api/owners/{owner.id}/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["total_wins"] == 18
        assert data["total_losses"] == 10
        assert data["total_points"] == 3000.0
        assert data["playoff_appearances"] == 2
        assert data["championships"] == 1  # Only 2022 had final_rank=1
        assert data["seasons_played"] == 2


class TestOwnerMappingValidation:
    """Test validation for owner mapping operations."""

    def test_cannot_map_already_mapped_sleeper_id(self, test_client, db_session):
        """Test that Sleeper ID already mapped to another owner is rejected."""
        owner1 = Owner(name="Owner 1", sleeper_user_id="s_taken")
        owner2 = Owner(name="Owner 2")
        db_session.add_all([owner1, owner2])
        db_session.commit()

        response = test_client.put(
            f"/api/owners/{owner2.id}/mapping",
            json={"sleeper_user_id": "s_taken"},
        )
        assert response.status_code == 400
        assert "already mapped" in response.json()["detail"].lower()

    def test_cannot_map_already_mapped_yahoo_id(self, test_client, db_session):
        """Test that Yahoo ID already mapped to another owner is rejected."""
        owner1 = Owner(name="Owner 1", yahoo_user_id="y_taken")
        owner2 = Owner(name="Owner 2")
        db_session.add_all([owner1, owner2])
        db_session.commit()

        response = test_client.put(
            f"/api/owners/{owner2.id}/mapping",
            json={"yahoo_user_id": "y_taken"},
        )
        assert response.status_code == 400
        assert "already mapped" in response.json()["detail"].lower()

    def test_merge_requires_different_owners(self, test_client, db_session):
        """Test that merge requires two different owners."""
        owner = Owner(name="Self Merge", sleeper_user_id="s_self")
        db_session.add(owner)
        db_session.commit()

        response = test_client.post(
            "/api/owners/merge",
            json={
                "primary_owner_id": owner.id,
                "secondary_owner_id": owner.id,
            },
        )
        assert response.status_code == 400

    def test_unlink_platform(self, test_client, db_session):
        """Test unlinking a platform from an owner."""
        owner = Owner(
            name="Unlink Test",
            sleeper_user_id="s_unlink",
            yahoo_user_id="y_unlink",
        )
        db_session.add(owner)
        db_session.commit()

        # Unlink Sleeper
        response = test_client.delete(
            f"/api/owners/{owner.id}/mapping/sleeper"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["sleeper_user_id"] is None
        assert data["yahoo_user_id"] == "y_unlink"
