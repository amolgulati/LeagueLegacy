"""Yahoo Fantasy service for importing and storing fantasy football data.

This service handles:
- Fetching data from Yahoo Fantasy API
- Mapping Yahoo data to database models
- Storing/updating data in the database
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session

from app.db.models import League, Season, Team, Owner, Matchup, Trade, Platform
from app.services.yahoo_client import YahooClient, YahooToken


class YahooService:
    """Service for importing Yahoo Fantasy football data into the database."""

    def __init__(self, db: Session, client: Optional[YahooClient] = None):
        """Initialize the Yahoo service.

        Args:
            db: SQLAlchemy database session.
            client: Optional YahooClient instance (creates new one if not provided).
        """
        self.db = db
        self.client = client or YahooClient()

    def set_token(self, token: YahooToken) -> None:
        """Set the OAuth token on the client.

        Args:
            token: YahooToken to use for API requests.
        """
        self.client.set_token(token)

    def set_token_from_dict(self, token_data: dict) -> None:
        """Set the OAuth token from a dictionary.

        Args:
            token_data: Dictionary containing token fields.
        """
        self.client.set_token_from_dict(token_data)

    async def import_league(self, league_key: str) -> League:
        """Import or update a league from Yahoo.

        Args:
            league_key: The Yahoo league key (e.g., "449.l.123456").

        Returns:
            The created or updated League model.
        """
        # Fetch league data from Yahoo
        league_data = await self.client.get_league(league_key)

        # Extract league_id from the league_key (format: "449.l.123456")
        platform_league_id = league_data.get("league_key", league_key)

        # Check if league already exists
        league = (
            self.db.query(League)
            .filter(
                League.platform == Platform.YAHOO,
                League.platform_league_id == platform_league_id,
            )
            .first()
        )

        if not league:
            league = League(
                platform=Platform.YAHOO,
                platform_league_id=platform_league_id,
            )
            self.db.add(league)

        # Update league properties
        league.name = league_data.get("name", "Unknown League")
        league.team_count = league_data.get("num_teams")
        league.scoring_type = league_data.get("scoring_type", "head")

        self.db.commit()
        self.db.refresh(league)

        return league

    async def import_season(
        self, league_key: str, year: Optional[int] = None
    ) -> Season:
        """Import or update a season from Yahoo.

        Args:
            league_key: The Yahoo league key.
            year: Optional year override (fetches from API if not provided).

        Returns:
            The created or updated Season model.
        """
        # Ensure league exists
        league = await self.import_league(league_key)

        # Fetch league data to get season info
        league_data = await self.client.get_league(league_key)
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
        season.regular_season_weeks = league_data.get("end_week", 14)
        season.is_complete = league_data.get("is_finished", False)

        self.db.commit()
        self.db.refresh(season)

        return season

    async def import_standings(self, league_key: str) -> List[Team]:
        """Import standings (teams and owners) from Yahoo.

        Args:
            league_key: The Yahoo league key.

        Returns:
            List of created/updated Team models.
        """
        # Ensure season exists
        season = await self.import_season(league_key)

        # Fetch standings
        standings = await self.client.get_standings(league_key)

        teams = []

        for team_data in standings:
            manager = team_data.get("manager", {})
            yahoo_user_id = manager.get("guid", "") or manager.get("manager_id", "")

            if not yahoo_user_id:
                continue

            # Find or create owner by Yahoo user ID
            owner = (
                self.db.query(Owner)
                .filter(Owner.yahoo_user_id == yahoo_user_id)
                .first()
            )

            if not owner:
                owner = Owner(
                    name=manager.get("nickname", "Unknown"),
                    display_name=manager.get("nickname"),
                    yahoo_user_id=yahoo_user_id,
                    avatar_url=manager.get("image_url"),
                )
                self.db.add(owner)
                self.db.flush()  # Get owner ID without committing
            else:
                # Update owner info if changed
                owner.display_name = manager.get("nickname") or owner.display_name
                if manager.get("image_url"):
                    owner.avatar_url = manager.get("image_url")

            # Find or create team
            team_key = team_data.get("team_key", "")
            team = (
                self.db.query(Team)
                .filter(
                    Team.season_id == season.id,
                    Team.platform_team_id == team_key,
                )
                .first()
            )

            if not team:
                team = Team(
                    season_id=season.id,
                    owner_id=owner.id,
                    name=team_data.get("name", f"Team {team_data.get('team_id', '')}"),
                    platform_team_id=team_key,
                )
                self.db.add(team)
            else:
                team.owner_id = owner.id
                team.name = team_data.get("name", team.name)

            # Update team stats
            team.wins = team_data.get("wins", 0)
            team.losses = team_data.get("losses", 0)
            team.ties = team_data.get("ties", 0)
            team.points_for = team_data.get("points_for", 0.0)
            team.points_against = team_data.get("points_against", 0.0)
            team.regular_season_rank = team_data.get("rank")

            # Determine playoff status based on rank and playoff seed
            playoff_seed = team_data.get("playoff_seed")
            if playoff_seed is not None:
                team.made_playoffs = True

            teams.append(team)

        self.db.commit()

        # Refresh all teams
        for team in teams:
            self.db.refresh(team)

        return teams

    async def import_matchups(
        self, league_key: str, start_week: int = 1, end_week: int = 17
    ) -> List[Matchup]:
        """Import all matchups for a season from Yahoo.

        Args:
            league_key: The Yahoo league key.
            start_week: First week to import.
            end_week: Last week to import.

        Returns:
            List of created/updated Matchup models.
        """
        # Ensure teams exist
        teams = await self.import_standings(league_key)
        season = teams[0].season if teams else await self.import_season(league_key)

        # Build team lookup by team_key (platform_team_id)
        team_lookup = {t.platform_team_id: t for t in teams if t.platform_team_id}

        # Fetch all matchups
        all_matchups_data = await self.client.get_all_matchups_for_season(
            league_key, start_week, end_week
        )

        matchups = []

        for week, week_matchups in all_matchups_data.items():
            for matchup_data in week_matchups:
                teams_in_matchup = matchup_data.get("teams", [])
                if len(teams_in_matchup) != 2:
                    continue  # Skip incomplete matchups

                t1, t2 = teams_in_matchup
                team_1 = team_lookup.get(t1.get("team_key"))
                team_2 = team_lookup.get(t2.get("team_key"))

                if not team_1 or not team_2:
                    continue

                score_1 = t1.get("points", 0.0)
                score_2 = t2.get("points", 0.0)

                # Determine winner
                is_tied = matchup_data.get("is_tied", False)
                winner_key = matchup_data.get("winner_team_key")

                if is_tied:
                    winner_id = None
                elif winner_key:
                    winner_team = team_lookup.get(winner_key)
                    winner_id = winner_team.id if winner_team else None
                elif score_1 > score_2:
                    winner_id = team_1.id
                elif score_2 > score_1:
                    winner_id = team_2.id
                else:
                    winner_id = None
                    is_tied = True

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
                matchup.is_tie = is_tied
                matchup.is_playoff = matchup_data.get("is_playoffs", False)
                matchup.is_consolation = matchup_data.get("is_consolation", False)

                matchups.append(matchup)

        self.db.commit()

        # Refresh all matchups
        for matchup in matchups:
            self.db.refresh(matchup)

        return matchups

    async def import_trades(self, league_key: str) -> List[Trade]:
        """Import all trades for a season from Yahoo.

        Args:
            league_key: The Yahoo league key.

        Returns:
            List of created/updated Trade models.
        """
        # Ensure teams exist
        teams = await self.import_standings(league_key)
        season = teams[0].season if teams else await self.import_season(league_key)

        # Build team lookup by team_key
        team_lookup = {t.platform_team_id: t for t in teams if t.platform_team_id}

        # Fetch all trades
        trades_data = await self.client.get_trades(league_key)

        trades = []

        for trade_data in trades_data:
            transaction_id = trade_data.get("transaction_id", "")

            if not transaction_id:
                continue

            # Check if trade already exists
            trade = (
                self.db.query(Trade)
                .filter(Trade.platform_trade_id == transaction_id)
                .first()
            )

            if not trade:
                # Parse trade timestamp
                timestamp = trade_data.get("timestamp", 0)
                trade_date = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()

                trade = Trade(
                    season_id=season.id,
                    platform_trade_id=transaction_id,
                    trade_date=trade_date,
                    status=trade_data.get("status", "completed"),
                )
                self.db.add(trade)
                self.db.flush()

            # Build assets exchanged data from players
            assets: Dict[str, Dict[str, List[str]]] = {}
            players = trade_data.get("players", [])

            for player in players:
                player_name = player.get("name", player.get("player_key", "Unknown"))
                dest_key = player.get("destination_team_key", "")
                source_key = player.get("source_team_key", "")

                # Track what each team received
                if dest_key:
                    if dest_key not in assets:
                        assets[dest_key] = {"received": [], "sent": []}
                    assets[dest_key]["received"].append(player_name)

                # Track what each team sent
                if source_key:
                    if source_key not in assets:
                        assets[source_key] = {"received": [], "sent": []}
                    assets[source_key]["sent"].append(player_name)

            trade.assets_exchanged = json.dumps(assets)

            # Link teams involved in trade
            trader_key = trade_data.get("trader_team_key", "")
            tradee_key = trade_data.get("tradee_team_key", "")

            trade.teams = []
            for team_key in [trader_key, tradee_key]:
                if team_key:
                    team = team_lookup.get(team_key)
                    if team and team not in trade.teams:
                        trade.teams.append(team)

            trades.append(trade)

        self.db.commit()

        # Refresh all trades
        for trade in trades:
            self.db.refresh(trade)

        return trades

    async def import_full_league(
        self, league_key: str, start_week: int = 1, end_week: int = 17
    ) -> dict:
        """Import all data for a league from Yahoo.

        This is the main entry point for importing a complete league,
        including league info, standings, matchups, and trades.

        Args:
            league_key: The Yahoo league key.
            start_week: First week of matchups to import.
            end_week: Last week of matchups to import.

        Returns:
            Dictionary with counts of imported entities.
        """
        league = await self.import_league(league_key)
        season = await self.import_season(league_key)
        teams = await self.import_standings(league_key)
        matchups = await self.import_matchups(league_key, start_week, end_week)
        trades = await self.import_trades(league_key)

        return {
            "league_id": league.id,
            "league_name": league.name,
            "season_year": season.year,
            "teams_imported": len(teams),
            "matchups_imported": len(matchups),
            "trades_imported": len(trades),
        }

    async def get_user_leagues(self, game_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all leagues for the authenticated user.

        Args:
            game_key: Optional game key to filter by season.

        Returns:
            List of league data dictionaries.
        """
        return await self.client.get_user_leagues(game_key)
