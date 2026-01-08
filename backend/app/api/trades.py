"""Trade analytics API routes for Fantasy League History Tracker.

This module provides endpoints for:
- Listing all trades with filters (owner, season, league)
- Getting trades for a specific owner
- Trade frequency calculations
- Most common trade partners
- Win rate before/after trades analysis
- Overall trade statistics
"""

from typing import List, Optional
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.db.models import Owner, Team, Season, League, Trade, Matchup, trade_teams


router = APIRouter(prefix="/api/trades", tags=["trades"])


# ============= Pydantic Models =============

class OwnerBrief(BaseModel):
    """Brief owner info."""
    id: int
    name: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class TeamBrief(BaseModel):
    """Brief team info for trade display."""
    id: int
    name: str
    owner: OwnerBrief


class TradeResponse(BaseModel):
    """Trade info with participating teams."""
    id: int
    week: Optional[int] = None
    trade_date: str
    season_id: int
    season_year: int
    league_id: int
    league_name: str
    assets_exchanged: Optional[str] = None
    status: str
    teams: List[TeamBrief]


class TradesListResponse(BaseModel):
    """Paginated list of trades."""
    trades: List[TradeResponse]
    total: int
    limit: int
    offset: int


class TradePartner(BaseModel):
    """Trade partner info with trade count."""
    owner: OwnerBrief
    trade_count: int


class TradeFrequency(BaseModel):
    """Trade frequency statistics."""
    trades_per_season: float
    seasons_played: int
    total_trades: int


class WinRateAnalysis(BaseModel):
    """Win rate before and after trades analysis."""
    win_rate_before_trades: Optional[float] = None
    win_rate_after_trades: Optional[float] = None
    win_rate_change: Optional[float] = None
    games_before: int = 0
    games_after: int = 0
    wins_before: int = 0
    wins_after: int = 0


class OwnerTradesResponse(BaseModel):
    """Full trade info for an owner."""
    owner: OwnerBrief
    trades: List[TradeResponse]
    total_trades: int
    trade_frequency: TradeFrequency
    trade_partners: List[TradePartner]
    win_rate_analysis: WinRateAnalysis


class TraderStats(BaseModel):
    """Stats for a trader."""
    owner: OwnerBrief
    trade_count: int


class SeasonTradeStats(BaseModel):
    """Trade stats for a season."""
    season_id: int
    year: int
    league_name: str
    trade_count: int


class OverallTradeStats(BaseModel):
    """Overall trade statistics."""
    total_trades: int
    most_active_traders: List[TraderStats]
    trades_by_season: List[SeasonTradeStats]
    avg_trades_per_season: float


# ============= Helper Functions =============

def trade_to_response(trade: Trade) -> TradeResponse:
    """Convert a Trade model to TradeResponse."""
    season = trade.season
    league = season.league

    teams = []
    for team in trade.teams:
        teams.append(TeamBrief(
            id=team.id,
            name=team.name,
            owner=OwnerBrief(
                id=team.owner.id,
                name=team.owner.name,
                display_name=team.owner.display_name,
                avatar_url=team.owner.avatar_url,
            )
        ))

    return TradeResponse(
        id=trade.id,
        week=trade.week,
        trade_date=trade.trade_date.isoformat(),
        season_id=season.id,
        season_year=season.year,
        league_id=league.id,
        league_name=league.name,
        assets_exchanged=trade.assets_exchanged,
        status=trade.status,
        teams=teams,
    )


def calculate_trade_frequency(owner_id: int, trades: List[Trade], db: Session) -> TradeFrequency:
    """Calculate trade frequency for an owner."""
    # Count unique seasons the owner has participated in
    seasons_count = db.query(func.count(func.distinct(Team.season_id))).filter(
        Team.owner_id == owner_id
    ).scalar() or 0

    total = len(trades)
    trades_per_season = round(total / seasons_count, 2) if seasons_count > 0 else 0.0

    return TradeFrequency(
        trades_per_season=trades_per_season,
        seasons_played=seasons_count,
        total_trades=total,
    )


def calculate_trade_partners(owner_id: int, trades: List[Trade]) -> List[TradePartner]:
    """Calculate most common trade partners for an owner."""
    partner_counts = defaultdict(int)
    partner_info = {}

    for trade in trades:
        for team in trade.teams:
            if team.owner_id != owner_id:
                partner_counts[team.owner_id] += 1
                partner_info[team.owner_id] = team.owner

    # Sort by trade count descending
    sorted_partners = sorted(partner_counts.items(), key=lambda x: x[1], reverse=True)

    result = []
    for partner_id, count in sorted_partners:
        owner = partner_info[partner_id]
        result.append(TradePartner(
            owner=OwnerBrief(
                id=owner.id,
                name=owner.name,
                display_name=owner.display_name,
                avatar_url=owner.avatar_url,
            ),
            trade_count=count,
        ))

    return result


def calculate_win_rate_analysis(owner_id: int, trades: List[Trade], db: Session) -> WinRateAnalysis:
    """Calculate win rate before and after first trade for an owner."""
    if not trades:
        return WinRateAnalysis()

    # Find the earliest trade by (season_year, week)
    earliest_trade = None
    earliest_key = None
    for trade in trades:
        year = trade.season.year
        week = trade.week or 0
        key = (year, week)
        if earliest_key is None or key < earliest_key:
            earliest_key = key
            earliest_trade = trade

    if earliest_trade is None:
        return WinRateAnalysis()

    earliest_year = earliest_trade.season.year
    earliest_week = earliest_trade.week or 0

    # Get all team IDs for this owner
    team_ids = [t.id for t in db.query(Team.id).filter(Team.owner_id == owner_id).all()]

    if not team_ids:
        return WinRateAnalysis()

    # Get all matchups for this owner with season info
    matchups = db.query(Matchup).options(
        joinedload(Matchup.season)
    ).filter(
        or_(
            Matchup.home_team_id.in_(team_ids),
            Matchup.away_team_id.in_(team_ids)
        )
    ).all()

    wins_before = 0
    losses_before = 0
    wins_after = 0
    losses_after = 0

    for matchup in matchups:
        year = matchup.season.year
        week = matchup.week

        # Determine if this matchup is before or after the first trade
        is_before = (year < earliest_year) or (year == earliest_year and week < earliest_week)

        # Determine if owner won
        if matchup.home_team_id in team_ids:
            won = matchup.winner_team_id == matchup.home_team_id
        else:
            won = matchup.winner_team_id == matchup.away_team_id

        # Skip ties
        if matchup.is_tie:
            continue

        if is_before:
            if won:
                wins_before += 1
            else:
                losses_before += 1
        else:
            if won:
                wins_after += 1
            else:
                losses_after += 1

    games_before = wins_before + losses_before
    games_after = wins_after + losses_after

    win_rate_before = round((wins_before / games_before) * 100, 1) if games_before > 0 else None
    win_rate_after = round((wins_after / games_after) * 100, 1) if games_after > 0 else None

    win_rate_change = None
    if win_rate_before is not None and win_rate_after is not None:
        win_rate_change = round(win_rate_after - win_rate_before, 1)

    return WinRateAnalysis(
        win_rate_before_trades=win_rate_before,
        win_rate_after_trades=win_rate_after,
        win_rate_change=win_rate_change,
        games_before=games_before,
        games_after=games_after,
        wins_before=wins_before,
        wins_after=wins_after,
    )


def get_trades_for_owner(owner_id: int, db: Session) -> List[Trade]:
    """Get all trades involving an owner."""
    # Get team IDs for this owner
    team_ids = [t.id for t in db.query(Team.id).filter(Team.owner_id == owner_id).all()]

    if not team_ids:
        return []

    # Find trades that involve any of these teams
    trades = db.query(Trade).options(
        joinedload(Trade.teams).joinedload(Team.owner),
        joinedload(Trade.season).joinedload(Season.league),
    ).filter(
        Trade.teams.any(Team.id.in_(team_ids))
    ).order_by(Trade.trade_date.desc()).all()

    return trades


# ============= API Endpoints =============

@router.get("", response_model=TradesListResponse)
async def list_all_trades(
    owner_id: Optional[int] = Query(None, description="Filter by owner ID"),
    season_id: Optional[int] = Query(None, description="Filter by season ID"),
    league_id: Optional[int] = Query(None, description="Filter by league ID"),
    limit: int = Query(50, ge=1, le=100, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """List all trades with optional filters.

    Filters:
    - owner_id: Only trades involving this owner
    - season_id: Only trades from this season
    - league_id: Only trades from this league

    Pagination:
    - limit: Max 100 per page (default 50)
    - offset: Skip N results (default 0)
    """
    query = db.query(Trade).options(
        joinedload(Trade.teams).joinedload(Team.owner),
        joinedload(Trade.season).joinedload(Season.league),
    )

    # Apply filters
    if owner_id is not None:
        team_ids = [t.id for t in db.query(Team.id).filter(Team.owner_id == owner_id).all()]
        if team_ids:
            query = query.filter(Trade.teams.any(Team.id.in_(team_ids)))
        else:
            # No teams means no trades for this owner
            return TradesListResponse(trades=[], total=0, limit=limit, offset=offset)

    if season_id is not None:
        query = query.filter(Trade.season_id == season_id)

    if league_id is not None:
        query = query.join(Season).filter(Season.league_id == league_id)

    # Get total count before pagination
    total = query.count()

    # Apply pagination and ordering
    trades = query.order_by(Trade.trade_date.desc()).offset(offset).limit(limit).all()

    trade_responses = [trade_to_response(trade) for trade in trades]

    return TradesListResponse(
        trades=trade_responses,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/owners/{owner_id}", response_model=OwnerTradesResponse)
async def get_owner_trades(owner_id: int, db: Session = Depends(get_db)):
    """Get all trades for a specific owner with analytics.

    Returns:
    - All trades involving this owner
    - Trade frequency (trades per season)
    - Most common trade partners
    - Win rate before/after trades analysis

    Raises:
        404: If owner not found
    """
    owner = db.query(Owner).filter(Owner.id == owner_id).first()

    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Owner with ID {owner_id} not found"
        )

    # Get trades for this owner
    trades = get_trades_for_owner(owner_id, db)

    # Calculate analytics
    trade_frequency = calculate_trade_frequency(owner_id, trades, db)
    trade_partners = calculate_trade_partners(owner_id, trades)
    win_rate_analysis = calculate_win_rate_analysis(owner_id, trades, db)

    trade_responses = [trade_to_response(trade) for trade in trades]

    return OwnerTradesResponse(
        owner=OwnerBrief(
            id=owner.id,
            name=owner.name,
            display_name=owner.display_name,
            avatar_url=owner.avatar_url,
        ),
        trades=trade_responses,
        total_trades=len(trades),
        trade_frequency=trade_frequency,
        trade_partners=trade_partners,
        win_rate_analysis=win_rate_analysis,
    )


@router.get("/stats", response_model=OverallTradeStats)
async def get_trade_stats(db: Session = Depends(get_db)):
    """Get overall trade statistics.

    Returns:
    - Total trades across all seasons
    - Most active traders
    - Trade counts by season
    - Average trades per season
    """
    # Total trades
    total_trades = db.query(func.count(Trade.id)).scalar() or 0

    if total_trades == 0:
        return OverallTradeStats(
            total_trades=0,
            most_active_traders=[],
            trades_by_season=[],
            avg_trades_per_season=0.0,
        )

    # Count trades per owner
    # Need to join through trade_teams association table
    owner_trade_counts = defaultdict(int)
    owners_dict = {}

    trades = db.query(Trade).options(
        joinedload(Trade.teams).joinedload(Team.owner),
        joinedload(Trade.season).joinedload(Season.league),
    ).all()

    for trade in trades:
        for team in trade.teams:
            owner_trade_counts[team.owner_id] += 1
            owners_dict[team.owner_id] = team.owner

    # Sort by trade count
    sorted_traders = sorted(owner_trade_counts.items(), key=lambda x: x[1], reverse=True)

    most_active_traders = []
    for owner_id, count in sorted_traders[:10]:  # Top 10
        owner = owners_dict[owner_id]
        most_active_traders.append(TraderStats(
            owner=OwnerBrief(
                id=owner.id,
                name=owner.name,
                display_name=owner.display_name,
                avatar_url=owner.avatar_url,
            ),
            trade_count=count,
        ))

    # Count trades by season
    season_trade_counts = defaultdict(int)
    season_info = {}

    for trade in trades:
        season = trade.season
        season_trade_counts[season.id] += 1
        season_info[season.id] = (season.year, season.league.name)

    trades_by_season = []
    for season_id, count in sorted(season_trade_counts.items(), key=lambda x: season_info[x[0]][0], reverse=True):
        year, league_name = season_info[season_id]
        trades_by_season.append(SeasonTradeStats(
            season_id=season_id,
            year=year,
            league_name=league_name,
            trade_count=count,
        ))

    # Average trades per season
    num_seasons = len(season_trade_counts)
    avg_trades_per_season = round(total_trades / num_seasons, 2) if num_seasons > 0 else 0.0

    return OverallTradeStats(
        total_trades=total_trades,
        most_active_traders=most_active_traders,
        trades_by_season=trades_by_season,
        avg_trades_per_season=avg_trades_per_season,
    )
