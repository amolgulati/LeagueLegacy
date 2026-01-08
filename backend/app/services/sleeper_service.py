"""Sleeper service for importing and storing fantasy football data.

This service handles:
- Fetching data from Sleeper API
- Mapping Sleeper data to database models
- Storing/updating data in the database
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import League, Season, Team, Owner, Matchup, Trade, Platform
from app.services.sleeper_client import SleeperClient
from app.services.player_cache import PlayerCache


class SleeperService:
    """Service for importing Sleeper fantasy football data into the database."""

    def __init__(
        self,
        db: Session,
        client: Optional[SleeperClient] = None,
        player_cache: Optional[PlayerCache] = None,
    ):
        """Initialize the Sleeper service.

        Args:
            db: SQLAlchemy database session.
            client: Optional SleeperClient instance (creates new one if not provided).
            player_cache: Optional PlayerCache for resolving player IDs to names.
        """
        self.db = db
        self.client = client or SleeperClient()
        # Create player cache if not provided (will use same client)
        self._player_cache = player_cache or PlayerCache(self.client)

    async def _ensure_player_cache(self) -> None:
        """Ensure player cache is loaded before resolving player names."""
        if not self._player_cache.is_loaded():
            await self._player_cache.fetch_players()

    def _resolve_player_id(self, player_id: str) -> str:
        """Resolve a player ID to player name.

        Args:
            player_id: The Sleeper player ID.

        Returns:
            Player name if found, otherwise the original ID.
        """
        return self._player_cache.get_player_name(player_id)

    async def import_league(self, league_id: str) -> League:
        """Import or update a league from Sleeper.

        Args:
            league_id: The Sleeper league ID.

        Returns:
            The created or updated League model.
        """
        # Fetch league data from Sleeper
        league_data = await self.client.get_league(league_id)

        # Check if league already exists
        league = (
            self.db.query(League)
            .filter(
                League.platform == Platform.SLEEPER,
                League.platform_league_id == league_id,
            )
            .first()
        )

        if not league:
            league = League(
                platform=Platform.SLEEPER,
                platform_league_id=league_id,
            )
            self.db.add(league)

        # Update league properties
        league.name = league_data.get("name", "Unknown League")
        league.team_count = league_data.get("total_rosters")

        # Determine scoring type from settings
        scoring_settings = league_data.get("scoring_settings", {})
        if scoring_settings.get("rec", 0) == 1:
            league.scoring_type = "PPR"
        elif scoring_settings.get("rec", 0) == 0.5:
            league.scoring_type = "Half PPR"
        else:
            league.scoring_type = "Standard"

        self.db.commit()
        self.db.refresh(league)

        return league

    async def import_season(
        self, league_id: str, year: Optional[int] = None, league: Optional[League] = None
    ) -> Season:
        """Import or update a season from Sleeper.

        Args:
            league_id: The Sleeper league ID (for this specific season).
            year: Optional year override (fetches from API if not provided).
            league: Optional League model to use. If not provided, creates/fetches
                    one based on league_id. Pass this when importing historical
                    seasons that should all belong to the same League record.

        Returns:
            The created or updated Season model.
        """
        # Ensure league exists (use provided league or create/fetch one)
        if league is None:
            league = await self.import_league(league_id)

        # Fetch league data to get season info
        league_data = await self.client.get_league(league_id)
        season_year = year or int(league_data.get("season", datetime.now().year))

        # Check if season already exists
        season = (
            self.db.query(Season)
            .filter(Season.league_id == league.id, Season.year == season_year)
            .first()
        )

        if not season:
            season = Season(league_id=league.id, year=season_year)
            self.db.add(season)

        # Update season settings from league data
        settings = league_data.get("settings", {})
        season.regular_season_weeks = settings.get("playoff_week_start", 14) - 1
        season.playoff_weeks = settings.get("playoff_round_type_playoff", 1)
        season.playoff_team_count = settings.get("playoff_teams", 6)
        season.is_complete = league_data.get("status") == "complete"

        self.db.commit()
        self.db.refresh(season)

        return season

    async def import_users_and_rosters(
        self, league_id: str, league: Optional[League] = None
    ) -> list[Team]:
        """Import users and rosters from Sleeper, creating owners and teams.

        Args:
            league_id: The Sleeper league ID.
            league: Optional League model to use for the season.

        Returns:
            List of created/updated Team models.
        """
        # Ensure season exists
        season = await self.import_season(league_id, league=league)

        # Fetch users and rosters
        users = await self.client.get_users(league_id)
        rosters = await self.client.get_rosters(league_id)

        # Build user lookup by user_id
        user_lookup = {u["user_id"]: u for u in users if u.get("user_id")}

        teams = []

        for roster in rosters:
            owner_id = roster.get("owner_id")
            if not owner_id:
                continue

            user = user_lookup.get(owner_id, {})

            # Find or create owner by Sleeper user ID
            owner = (
                self.db.query(Owner)
                .filter(Owner.sleeper_user_id == owner_id)
                .first()
            )

            if not owner:
                owner = Owner(
                    name=user.get("display_name") or user.get("username") or "Unknown",
                    display_name=user.get("display_name"),
                    sleeper_user_id=owner_id,
                    avatar_url=SleeperClient.get_avatar_url(user.get("avatar")),
                )
                self.db.add(owner)
                self.db.flush()  # Get owner ID without committing
            else:
                # Update owner info if changed
                owner.display_name = user.get("display_name") or owner.display_name
                avatar_url = SleeperClient.get_avatar_url(user.get("avatar"))
                if avatar_url:
                    owner.avatar_url = avatar_url

            # Find or create team for this roster
            roster_id = roster.get("roster_id")
            team = (
                self.db.query(Team)
                .filter(
                    Team.season_id == season.id,
                    Team.platform_team_id == str(roster_id),
                )
                .first()
            )

            if not team:
                team = Team(
                    season_id=season.id,
                    owner_id=owner.id,
                    name=user.get("display_name") or user.get("username") or f"Team {roster_id}",
                    platform_team_id=str(roster_id),
                )
                self.db.add(team)
            else:
                team.owner_id = owner.id

            # Update team stats from roster settings
            roster_settings = roster.get("settings", {})
            team.wins = roster_settings.get("wins", 0)
            team.losses = roster_settings.get("losses", 0)
            team.ties = roster_settings.get("ties", 0)

            # Calculate points (Sleeper stores as integer cents for precision)
            fpts = roster_settings.get("fpts", 0)
            fpts_decimal = roster_settings.get("fpts_decimal", 0)
            team.points_for = fpts + (fpts_decimal / 100)

            fpts_against = roster_settings.get("fpts_against", 0)
            fpts_against_decimal = roster_settings.get("fpts_against_decimal", 0)
            team.points_against = fpts_against + (fpts_against_decimal / 100)

            teams.append(team)

        self.db.commit()

        # Refresh all teams to get updated data
        for team in teams:
            self.db.refresh(team)

        return teams

    async def import_matchups(
        self, league_id: str, total_weeks: int = 18, league: Optional[League] = None
    ) -> list[Matchup]:
        """Import all matchups for a season from Sleeper.

        Args:
            league_id: The Sleeper league ID.
            total_weeks: Total number of weeks to import.
            league: Optional League model to use for the season.

        Returns:
            List of created/updated Matchup models.
        """
        # Ensure teams exist
        teams = await self.import_users_and_rosters(league_id, league=league)
        season = teams[0].season if teams else await self.import_season(league_id, league=league)

        # Build team lookup by roster_id (platform_team_id)
        team_lookup = {t.platform_team_id: t for t in teams}

        # Get league settings for playoff week
        league_data = await self.client.get_league(league_id)
        settings = league_data.get("settings", {})
        playoff_week_start = settings.get("playoff_week_start", 15)

        # Fetch all matchups
        all_matchups_data = await self.client.get_all_matchups_for_season(
            league_id, total_weeks
        )

        matchups = []

        for week, week_matchups in all_matchups_data.items():
            # Group matchups by matchup_id
            matchup_groups: dict[int, list[dict]] = {}
            for m in week_matchups:
                matchup_id = m.get("matchup_id")
                if matchup_id is not None:
                    if matchup_id not in matchup_groups:
                        matchup_groups[matchup_id] = []
                    matchup_groups[matchup_id].append(m)

            # Process each matchup pair
            for matchup_id, participants in matchup_groups.items():
                if len(participants) != 2:
                    continue  # Skip incomplete matchups (e.g., bye weeks)

                p1, p2 = participants
                roster_id_1 = str(p1.get("roster_id"))
                roster_id_2 = str(p2.get("roster_id"))

                team_1 = team_lookup.get(roster_id_1)
                team_2 = team_lookup.get(roster_id_2)

                if not team_1 or not team_2:
                    continue

                score_1 = p1.get("points") or 0.0
                score_2 = p2.get("points") or 0.0

                # Determine winner
                if score_1 > score_2:
                    winner_id = team_1.id
                    is_tie = False
                elif score_2 > score_1:
                    winner_id = team_2.id
                    is_tie = False
                else:
                    winner_id = None
                    is_tie = True

                # Check if this is a playoff game
                is_playoff = week >= playoff_week_start

                # Check if matchup already exists
                matchup = (
                    self.db.query(Matchup)
                    .filter(
                        Matchup.season_id == season.id,
                        Matchup.week == week,
                        Matchup.home_team_id == team_1.id,
                        Matchup.away_team_id == team_2.id,
                    )
                    .first()
                )

                if not matchup:
                    matchup = Matchup(
                        season_id=season.id,
                        week=week,
                        home_team_id=team_1.id,
                        away_team_id=team_2.id,
                    )
                    self.db.add(matchup)

                matchup.home_score = score_1
                matchup.away_score = score_2
                matchup.winner_team_id = winner_id
                matchup.is_tie = is_tie
                matchup.is_playoff = is_playoff

                matchups.append(matchup)

        self.db.commit()

        # Refresh all matchups
        for matchup in matchups:
            self.db.refresh(matchup)

        return matchups

    async def import_trades(
        self, league_id: str, total_weeks: int = 18, league: Optional[League] = None
    ) -> list[Trade]:
        """Import all trades for a season from Sleeper.

        Args:
            league_id: The Sleeper league ID.
            total_weeks: Total number of weeks to check for trades.
            league: Optional League model to use for the season.

        Returns:
            List of created/updated Trade models.
        """
        # Ensure teams exist
        teams = await self.import_users_and_rosters(league_id, league=league)
        season = teams[0].season if teams else await self.import_season(league_id, league=league)

        # Build team lookup by roster_id
        team_lookup = {int(t.platform_team_id): t for t in teams if t.platform_team_id}

        # Fetch all trades
        trades_data = await self.client.get_all_trades_for_season(league_id, total_weeks)

        # Load player cache for resolving player names
        await self._ensure_player_cache()

        trades = []

        for trade_data in trades_data:
            transaction_id = trade_data.get("transaction_id")

            # Check if trade already exists
            trade = (
                self.db.query(Trade)
                .filter(Trade.platform_trade_id == transaction_id)
                .first()
            )

            if not trade:
                # Parse trade timestamp
                created_ts = trade_data.get("created", 0)
                trade_date = datetime.fromtimestamp(created_ts / 1000)

                trade = Trade(
                    season_id=season.id,
                    platform_trade_id=transaction_id,
                    trade_date=trade_date,
                    week=trade_data.get("week"),
                    status="completed",
                )
                self.db.add(trade)
                self.db.flush()

            # Build assets exchanged data with resolved player names
            assets: dict[str, dict[str, list[str]]] = {}
            adds = trade_data.get("adds") or {}
            drops = trade_data.get("drops") or {}
            draft_picks = trade_data.get("draft_picks") or []

            for player_id, roster_id in adds.items():
                roster_key = str(roster_id)
                if roster_key not in assets:
                    assets[roster_key] = {"received": [], "sent": []}
                # Resolve player ID to name
                player_name = self._resolve_player_id(str(player_id))
                assets[roster_key]["received"].append(player_name)

            for player_id, roster_id in drops.items():
                roster_key = str(roster_id)
                if roster_key not in assets:
                    assets[roster_key] = {"received": [], "sent": []}
                # Resolve player ID to name
                player_name = self._resolve_player_id(str(player_id))
                assets[roster_key]["sent"].append(player_name)

            # Handle draft picks
            for pick in draft_picks:
                owner_id = pick.get("owner_id")
                previous_owner_id = pick.get("previous_owner_id")
                pick_info = f"{pick.get('season')} Round {pick.get('round')}"

                if owner_id:
                    key = str(owner_id)
                    if key not in assets:
                        assets[key] = {"received": [], "sent": []}
                    assets[key]["received"].append(f"Pick: {pick_info}")

                if previous_owner_id:
                    key = str(previous_owner_id)
                    if key not in assets:
                        assets[key] = {"received": [], "sent": []}
                    assets[key]["sent"].append(f"Pick: {pick_info}")

            trade.assets_exchanged = json.dumps(assets)

            # Link teams involved in trade
            roster_ids = trade_data.get("roster_ids", [])
            trade.teams = []
            for roster_id in roster_ids:
                team = team_lookup.get(roster_id)
                if team and team not in trade.teams:
                    trade.teams.append(team)

            trades.append(trade)

        self.db.commit()

        # Refresh all trades
        for trade in trades:
            self.db.refresh(trade)

        return trades

    async def detect_and_set_champion(
        self, league_id: str, season: Season, teams: list[Team]
    ) -> tuple[Optional[int], Optional[int]]:
        """Detect the playoff champion and runner-up and set them on the season.

        Fetches the winners bracket from Sleeper API, identifies the championship
        game, and updates the Season record with champion_team_id and runner_up_team_id.

        Args:
            league_id: The Sleeper league ID (for this specific season).
            season: The Season model to update.
            teams: List of Team models for this season (for roster_id to team_id mapping).

        Returns:
            Tuple of (champion_team_id, runner_up_team_id), either may be None if
            the championship has not been completed yet.
        """
        # Fetch the winners bracket
        bracket = await self.client.get_winners_bracket(league_id)

        if not bracket:
            return (None, None)

        # Get champion and runner-up roster IDs from bracket
        champion_roster_id = SleeperClient.get_champion_roster_id(bracket)
        runner_up_roster_id = SleeperClient.get_runner_up_roster_id(bracket)

        # Build team lookup by roster_id (platform_team_id)
        team_lookup = {t.platform_team_id: t for t in teams}

        # Map roster IDs to team IDs
        champion_team_id = None
        runner_up_team_id = None

        if champion_roster_id is not None:
            champion_team = team_lookup.get(str(champion_roster_id))
            if champion_team:
                champion_team_id = champion_team.id

        if runner_up_roster_id is not None:
            runner_up_team = team_lookup.get(str(runner_up_roster_id))
            if runner_up_team:
                runner_up_team_id = runner_up_team.id

        # Update the season with champion/runner-up
        if champion_team_id is not None:
            season.champion_team_id = champion_team_id
        if runner_up_team_id is not None:
            season.runner_up_team_id = runner_up_team_id

        self.db.commit()
        self.db.refresh(season)

        return (champion_team_id, runner_up_team_id)

    async def import_single_season(
        self, league_id: str, total_weeks: int = 18, league: Optional[League] = None
    ) -> dict:
        """Import data for a single season from Sleeper.

        Args:
            league_id: The Sleeper league ID for a specific season.
            total_weeks: Total number of weeks in the season.
            league: Optional League model. If provided, all data for this season
                    will be linked to this League record (used for historical imports).

        Returns:
            Dictionary with counts of imported entities for this season.
        """
        season = await self.import_season(league_id, league=league)
        teams = await self.import_users_and_rosters(league_id, league=league)
        matchups = await self.import_matchups(league_id, total_weeks, league=league)
        trades = await self.import_trades(league_id, total_weeks, league=league)

        # Detect and set champion/runner-up from playoff bracket
        champion_team_id, runner_up_team_id = await self.detect_and_set_champion(
            league_id, season, teams
        )

        return {
            "season_year": season.year,
            "teams_imported": len(teams),
            "matchups_imported": len(matchups),
            "trades_imported": len(trades),
            "champion_team_id": champion_team_id,
            "runner_up_team_id": runner_up_team_id,
        }

    async def import_full_league(
        self, league_id: str, total_weeks: int = 18
    ) -> dict:
        """Import all data for a league from Sleeper, including all historical seasons.

        This is the main entry point for importing a complete league,
        including league info, users, rosters, matchups, and trades
        for ALL historical seasons (not just the current one).

        Uses the league history chain to traverse previous_league_id links
        and import data from each historical season.

        Args:
            league_id: The Sleeper league ID (typically the most recent season).
            total_weeks: Total number of weeks in each season.

        Returns:
            Dictionary with counts of imported entities across all seasons.
        """
        # Get the chain of all historical league IDs (newest to oldest)
        league_ids = await self.client.get_league_history_chain(league_id)

        # Import the league record (uses first/current league ID)
        league = await self.import_league(league_id)

        # Track totals across all seasons
        total_teams = 0
        total_matchups = 0
        total_trades = 0
        seasons_imported: list[dict] = []

        # Import each historical season (all linked to the same League record)
        for historical_league_id in league_ids:
            season_result = await self.import_single_season(
                historical_league_id, total_weeks, league=league
            )
            total_teams += season_result["teams_imported"]
            total_matchups += season_result["matchups_imported"]
            total_trades += season_result["trades_imported"]
            seasons_imported.append(season_result)

        return {
            "league_id": league.id,
            "league_name": league.name,
            "seasons_imported": len(seasons_imported),
            "seasons": seasons_imported,
            "teams_imported": total_teams,
            "matchups_imported": total_matchups,
            "trades_imported": total_trades,
        }
