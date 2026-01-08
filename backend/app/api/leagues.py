"""League management API routes.

Provides endpoints for:
- Listing imported leagues
- Re-importing league data
- Deleting leagues and all related data
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import League, Season, Team, Matchup, Trade, Platform, trade_teams

router = APIRouter(prefix="/api/leagues", tags=["leagues"])


class LeagueSeasonSummary(BaseModel):
    """Summary of a season in a league."""
    id: int
    year: int
    champion_name: Optional[str] = None


class LeagueResponse(BaseModel):
    """Response model for a league."""
    id: int
    name: str
    platform: str
    platform_league_id: str
    team_count: Optional[int] = None
    scoring_type: Optional[str] = None
    created_at: datetime
    seasons_count: int
    seasons: List[LeagueSeasonSummary]
    latest_season_year: Optional[int] = None
    total_teams: int
    total_matchups: int
    total_trades: int

    class Config:
        from_attributes = True


class DeleteLeagueResponse(BaseModel):
    """Response model for league deletion."""
    success: bool
    message: str
    deleted_seasons: int
    deleted_teams: int
    deleted_matchups: int
    deleted_trades: int


@router.get("", response_model=List[LeagueResponse])
async def get_leagues(db: Session = Depends(get_db)):
    """Get all imported leagues with summary statistics.

    Returns a list of all leagues with:
    - Basic league info (name, platform, scoring)
    - Import date (created_at)
    - Counts of seasons, teams, matchups, trades
    - List of seasons with champions
    """
    leagues = db.query(League).order_by(League.created_at.desc()).all()

    results = []
    for league in leagues:
        # Get season summaries with champion names
        seasons_data = []
        latest_year = None
        for season in sorted(league.seasons, key=lambda s: s.year, reverse=True):
            champion_name = None
            if season.champion_team_id:
                champion_team = db.query(Team).filter(Team.id == season.champion_team_id).first()
                if champion_team and champion_team.owner:
                    champion_name = champion_team.owner.display_name or champion_team.owner.name

            seasons_data.append(LeagueSeasonSummary(
                id=season.id,
                year=season.year,
                champion_name=champion_name
            ))

            if latest_year is None or season.year > latest_year:
                latest_year = season.year

        # Count totals
        season_ids = [s.id for s in league.seasons]
        total_teams = db.query(func.count(Team.id)).filter(Team.season_id.in_(season_ids)).scalar() if season_ids else 0
        total_matchups = db.query(func.count(Matchup.id)).filter(Matchup.season_id.in_(season_ids)).scalar() if season_ids else 0
        total_trades = db.query(func.count(Trade.id)).filter(Trade.season_id.in_(season_ids)).scalar() if season_ids else 0

        results.append(LeagueResponse(
            id=league.id,
            name=league.name,
            platform=league.platform.value,
            platform_league_id=league.platform_league_id,
            team_count=league.team_count,
            scoring_type=league.scoring_type,
            created_at=league.created_at,
            seasons_count=len(league.seasons),
            seasons=seasons_data,
            latest_season_year=latest_year,
            total_teams=total_teams,
            total_matchups=total_matchups,
            total_trades=total_trades
        ))

    return results


@router.get("/{league_id}", response_model=LeagueResponse)
async def get_league(league_id: int, db: Session = Depends(get_db)):
    """Get a specific league by ID with full details."""
    league = db.query(League).filter(League.id == league_id).first()

    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # Get season summaries with champion names
    seasons_data = []
    latest_year = None
    for season in sorted(league.seasons, key=lambda s: s.year, reverse=True):
        champion_name = None
        if season.champion_team_id:
            champion_team = db.query(Team).filter(Team.id == season.champion_team_id).first()
            if champion_team and champion_team.owner:
                champion_name = champion_team.owner.display_name or champion_team.owner.name

        seasons_data.append(LeagueSeasonSummary(
            id=season.id,
            year=season.year,
            champion_name=champion_name
        ))

        if latest_year is None or season.year > latest_year:
            latest_year = season.year

    # Count totals
    season_ids = [s.id for s in league.seasons]
    total_teams = db.query(func.count(Team.id)).filter(Team.season_id.in_(season_ids)).scalar() if season_ids else 0
    total_matchups = db.query(func.count(Matchup.id)).filter(Matchup.season_id.in_(season_ids)).scalar() if season_ids else 0
    total_trades = db.query(func.count(Trade.id)).filter(Trade.season_id.in_(season_ids)).scalar() if season_ids else 0

    return LeagueResponse(
        id=league.id,
        name=league.name,
        platform=league.platform.value,
        platform_league_id=league.platform_league_id,
        team_count=league.team_count,
        scoring_type=league.scoring_type,
        created_at=league.created_at,
        seasons_count=len(league.seasons),
        seasons=seasons_data,
        latest_season_year=latest_year,
        total_teams=total_teams,
        total_matchups=total_matchups,
        total_trades=total_trades
    )


@router.delete("/{league_id}", response_model=DeleteLeagueResponse)
async def delete_league(league_id: int, db: Session = Depends(get_db)):
    """Delete a league and all its associated data.

    This performs a cascade delete:
    1. Delete all trade_teams associations for trades in this league
    2. Delete all trades in all seasons of this league
    3. Delete all matchups in all seasons of this league
    4. Delete all teams in all seasons of this league
    5. Delete all seasons of this league
    6. Delete the league itself

    Note: Owners are NOT deleted as they may be linked to other leagues.
    """
    # Check if league exists (without loading relationships)
    league_data = db.query(League.id, League.name).filter(League.id == league_id).first()

    if not league_data:
        raise HTTPException(status_code=404, detail="League not found")

    league_name = league_data.name

    # Get all season IDs for this league (raw query, no relationship loading)
    season_rows = db.query(Season.id).filter(Season.league_id == league_id).all()
    season_ids = [r.id for r in season_rows]

    # Count items before deletion for response
    deleted_teams = 0
    deleted_matchups = 0
    deleted_trades = 0
    deleted_seasons = len(season_ids)

    if season_ids:
        # Clear FK references from seasons to teams first (champion, runner-up, regular season winner)
        db.query(Season).filter(Season.id.in_(season_ids)).update(
            {
                Season.champion_team_id: None,
                Season.runner_up_team_id: None,
                Season.regular_season_winner_id: None
            },
            synchronize_session=False
        )

        # Clear matchup winner_team_id FK references
        db.query(Matchup).filter(Matchup.season_id.in_(season_ids)).update(
            {Matchup.winner_team_id: None},
            synchronize_session=False
        )

        # Get trade IDs for deletion count
        trade_rows = db.query(Trade.id).filter(Trade.season_id.in_(season_ids)).all()
        trade_ids = [r.id for r in trade_rows]
        deleted_trades = len(trade_ids)

        # Delete trade_teams associations using raw SQL
        if trade_ids:
            db.execute(trade_teams.delete().where(trade_teams.c.trade_id.in_(trade_ids)))

        # Delete trades
        db.query(Trade).filter(Trade.season_id.in_(season_ids)).delete(synchronize_session=False)

        # Delete matchups
        deleted_matchups = db.query(Matchup).filter(Matchup.season_id.in_(season_ids)).delete(synchronize_session=False)

        # Delete teams
        deleted_teams = db.query(Team).filter(Team.season_id.in_(season_ids)).delete(synchronize_session=False)

        # Delete seasons
        db.query(Season).filter(Season.id.in_(season_ids)).delete(synchronize_session=False)

    # Delete the league itself using raw query
    db.query(League).filter(League.id == league_id).delete(synchronize_session=False)

    db.commit()

    return DeleteLeagueResponse(
        success=True,
        message=f'Successfully deleted league "{league_name}"',
        deleted_seasons=deleted_seasons,
        deleted_teams=deleted_teams,
        deleted_matchups=deleted_matchups,
        deleted_trades=deleted_trades
    )
