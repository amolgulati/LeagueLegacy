"""Seasons API routes for Fantasy League History Tracker.

This module provides endpoints for:
- Listing all seasons with basic info
- Getting detailed season view with standings, playoff bracket, and trades
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.db.models import Owner, Team, Season, League, Matchup, Trade


router = APIRouter(prefix="/api/seasons", tags=["seasons"])


# ============= Pydantic Models =============

class OwnerBrief(BaseModel):
    """Brief owner info."""
    id: int
    name: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class TeamStanding(BaseModel):
    """Team standing info for a season."""
    team_id: int
    team_name: str
    owner_id: int
    owner_name: str
    owner_display_name: Optional[str] = None
    owner_avatar_url: Optional[str] = None
    wins: int
    losses: int
    ties: int
    points_for: float
    points_against: float
    regular_season_rank: Optional[int] = None
    final_rank: Optional[int] = None
    made_playoffs: bool


class PlayoffMatchup(BaseModel):
    """Playoff matchup info."""
    id: int
    week: int
    home_team_id: int
    home_team_name: str
    home_owner_id: int
    home_owner_name: str
    away_team_id: int
    away_team_name: str
    away_owner_id: int
    away_owner_name: str
    home_score: float
    away_score: float
    winner_team_id: Optional[int] = None
    winner_owner_name: Optional[str] = None
    is_championship: bool
    is_consolation: bool
    is_tie: bool


class TradeTeamBrief(BaseModel):
    """Brief team info for trade display."""
    id: int
    name: str
    owner_id: int
    owner_name: str


class TradeSummary(BaseModel):
    """Trade summary for a season."""
    id: int
    week: Optional[int] = None
    trade_date: str
    assets_exchanged: Optional[str] = None
    teams: List[TradeTeamBrief]


class SeasonDetailResponse(BaseModel):
    """Full season detail response."""
    id: int
    year: int
    league_id: int
    league_name: str
    platform: str
    is_complete: bool
    regular_season_weeks: Optional[int] = None
    playoff_weeks: Optional[int] = None
    playoff_team_count: Optional[int] = None
    team_count: int
    champion: Optional[OwnerBrief] = None
    runner_up: Optional[OwnerBrief] = None
    standings: List[TeamStanding]
    playoff_bracket: List[PlayoffMatchup]
    trades: List[TradeSummary]


class SeasonListItem(BaseModel):
    """Season info for list view."""
    id: int
    year: int
    league_id: int
    league_name: str
    platform: str
    is_complete: bool
    team_count: int
    champion_id: Optional[int] = None
    champion_name: Optional[str] = None
    runner_up_id: Optional[int] = None
    runner_up_name: Optional[str] = None


# ============= API Endpoints =============

@router.get("", response_model=List[SeasonListItem])
async def list_seasons(
    league_id: Optional[int] = Query(None, description="Filter by league ID"),
    db: Session = Depends(get_db)
):
    """List all seasons with basic info.

    Returns seasons sorted by year (descending).
    Optional filter by league_id.
    """
    query = db.query(Season).options(
        joinedload(Season.league),
    )

    if league_id is not None:
        query = query.filter(Season.league_id == league_id)

    seasons = query.order_by(Season.year.desc()).all()

    result = []
    for season in seasons:
        league = season.league

        # Get champion info
        champion_id = None
        champion_name = None
        if season.champion_team_id:
            champ_team = db.query(Team).options(
                joinedload(Team.owner)
            ).filter(Team.id == season.champion_team_id).first()
            if champ_team and champ_team.owner:
                champion_id = champ_team.owner.id
                champion_name = champ_team.owner.name

        # Get runner-up info
        runner_up_id = None
        runner_up_name = None
        if season.runner_up_team_id:
            runner_team = db.query(Team).options(
                joinedload(Team.owner)
            ).filter(Team.id == season.runner_up_team_id).first()
            if runner_team and runner_team.owner:
                runner_up_id = runner_team.owner.id
                runner_up_name = runner_team.owner.name

        # Get team count
        team_count = db.query(Team).filter(Team.season_id == season.id).count()

        result.append(SeasonListItem(
            id=season.id,
            year=season.year,
            league_id=league.id,
            league_name=league.name,
            platform=league.platform.value.upper(),
            is_complete=season.is_complete,
            team_count=team_count,
            champion_id=champion_id,
            champion_name=champion_name,
            runner_up_id=runner_up_id,
            runner_up_name=runner_up_name,
        ))

    return result


@router.get("/{season_id}", response_model=SeasonDetailResponse)
async def get_season_detail(season_id: int, db: Session = Depends(get_db)):
    """Get detailed view of a specific season.

    Returns:
    - Season info and configuration
    - Final standings (all teams sorted by final_rank)
    - Playoff bracket (all playoff matchups)
    - Notable trades that season

    Raises:
        404: If season not found
    """
    season = db.query(Season).options(
        joinedload(Season.league),
    ).filter(Season.id == season_id).first()

    if not season:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Season with ID {season_id} not found"
        )

    league = season.league

    # Get champion info
    champion = None
    if season.champion_team_id:
        champ_team = db.query(Team).options(
            joinedload(Team.owner)
        ).filter(Team.id == season.champion_team_id).first()
        if champ_team and champ_team.owner:
            champion = OwnerBrief(
                id=champ_team.owner.id,
                name=champ_team.owner.name,
                display_name=champ_team.owner.display_name,
                avatar_url=champ_team.owner.avatar_url,
            )

    # Get runner-up info
    runner_up = None
    if season.runner_up_team_id:
        runner_team = db.query(Team).options(
            joinedload(Team.owner)
        ).filter(Team.id == season.runner_up_team_id).first()
        if runner_team and runner_team.owner:
            runner_up = OwnerBrief(
                id=runner_team.owner.id,
                name=runner_team.owner.name,
                display_name=runner_team.owner.display_name,
                avatar_url=runner_team.owner.avatar_url,
            )

    # Get all teams with standings, sorted by final_rank
    teams = db.query(Team).options(
        joinedload(Team.owner)
    ).filter(
        Team.season_id == season_id
    ).order_by(Team.final_rank.asc().nullslast()).all()

    standings = []
    for team in teams:
        standings.append(TeamStanding(
            team_id=team.id,
            team_name=team.name,
            owner_id=team.owner.id,
            owner_name=team.owner.name,
            owner_display_name=team.owner.display_name,
            owner_avatar_url=team.owner.avatar_url,
            wins=team.wins,
            losses=team.losses,
            ties=team.ties,
            points_for=team.points_for,
            points_against=team.points_against,
            regular_season_rank=team.regular_season_rank,
            final_rank=team.final_rank,
            made_playoffs=team.made_playoffs,
        ))

    # Get playoff matchups
    playoff_matchups = db.query(Matchup).options(
        joinedload(Matchup.home_team).joinedload(Team.owner),
        joinedload(Matchup.away_team).joinedload(Team.owner),
    ).filter(
        Matchup.season_id == season_id,
        Matchup.is_playoff == True,
    ).order_by(Matchup.week.asc()).all()

    playoff_bracket = []
    for matchup in playoff_matchups:
        # Determine winner owner name
        winner_owner_name = None
        if matchup.winner_team_id:
            if matchup.winner_team_id == matchup.home_team_id:
                winner_owner_name = matchup.home_team.owner.name
            else:
                winner_owner_name = matchup.away_team.owner.name

        playoff_bracket.append(PlayoffMatchup(
            id=matchup.id,
            week=matchup.week,
            home_team_id=matchup.home_team_id,
            home_team_name=matchup.home_team.name,
            home_owner_id=matchup.home_team.owner.id,
            home_owner_name=matchup.home_team.owner.name,
            away_team_id=matchup.away_team_id,
            away_team_name=matchup.away_team.name,
            away_owner_id=matchup.away_team.owner.id,
            away_owner_name=matchup.away_team.owner.name,
            home_score=matchup.home_score,
            away_score=matchup.away_score,
            winner_team_id=matchup.winner_team_id,
            winner_owner_name=winner_owner_name,
            is_championship=matchup.is_championship,
            is_consolation=matchup.is_consolation,
            is_tie=matchup.is_tie,
        ))

    # Get trades for this season
    trades_db = db.query(Trade).options(
        joinedload(Trade.teams).joinedload(Team.owner),
    ).filter(
        Trade.season_id == season_id
    ).order_by(Trade.trade_date.desc()).all()

    trades = []
    for trade in trades_db:
        trade_teams = []
        for team in trade.teams:
            trade_teams.append(TradeTeamBrief(
                id=team.id,
                name=team.name,
                owner_id=team.owner.id,
                owner_name=team.owner.name,
            ))

        trades.append(TradeSummary(
            id=trade.id,
            week=trade.week,
            trade_date=trade.trade_date.isoformat(),
            assets_exchanged=trade.assets_exchanged,
            teams=trade_teams,
        ))

    return SeasonDetailResponse(
        id=season.id,
        year=season.year,
        league_id=league.id,
        league_name=league.name,
        platform=league.platform.value.upper(),
        is_complete=season.is_complete,
        regular_season_weeks=season.regular_season_weeks,
        playoff_weeks=season.playoff_weeks,
        playoff_team_count=season.playoff_team_count,
        team_count=len(teams),
        champion=champion,
        runner_up=runner_up,
        standings=standings,
        playoff_bracket=playoff_bracket,
        trades=trades,
    )
