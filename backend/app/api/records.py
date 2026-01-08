"""League records API routes for Fantasy League History Tracker.

This module provides endpoints for:
- Highest single-week score (all-time)
- Most points in a season
- Longest win streak
- Most trades in a season
All records show owner name and year.
"""

from typing import Optional, List
from collections import defaultdict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, desc
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.db.models import Owner, Team, Season, Matchup, Trade, trade_teams


router = APIRouter(prefix="/api/records", tags=["records"])


# ============= Pydantic Models =============

class WeeklyScoreRecord(BaseModel):
    """Single-week score record."""
    score: float
    owner_id: int
    owner_name: str
    team_name: str
    year: int
    week: int
    opponent_name: Optional[str] = None


class SeasonPointsRecord(BaseModel):
    """Most points in a season record."""
    points: float
    owner_id: int
    owner_name: str
    team_name: str
    year: int


class WinStreakRecord(BaseModel):
    """Longest win streak record."""
    streak: int
    owner_id: int
    owner_name: str
    team_name: str
    year: int


class SeasonTradesRecord(BaseModel):
    """Most trades in a season record."""
    trade_count: int
    owner_id: int
    owner_name: str
    year: int


class AllRecordsResponse(BaseModel):
    """All league records."""
    highest_single_week_score: Optional[WeeklyScoreRecord] = None
    most_points_in_season: Optional[SeasonPointsRecord] = None
    longest_win_streak: Optional[WinStreakRecord] = None
    most_trades_in_season: Optional[SeasonTradesRecord] = None
    top_weekly_scores: List[WeeklyScoreRecord] = []
    top_season_points: List[SeasonPointsRecord] = []
    top_win_streaks: List[WinStreakRecord] = []


# ============= Helper Functions =============

def get_highest_weekly_scores(db: Session, limit: int = 10) -> List[WeeklyScoreRecord]:
    """Get the highest single-week scores across all matchups."""
    # Get all matchups with their teams, owners, and seasons
    matchups = db.query(Matchup).options(
        joinedload(Matchup.season),
        joinedload(Matchup.home_team).joinedload(Team.owner),
        joinedload(Matchup.away_team).joinedload(Team.owner),
    ).all()

    if not matchups:
        return []

    # Build list of all individual scores
    scores = []
    for matchup in matchups:
        season = matchup.season
        home_team = matchup.home_team
        away_team = matchup.away_team

        if home_team and home_team.owner:
            scores.append({
                "score": matchup.home_score,
                "owner_id": home_team.owner.id,
                "owner_name": home_team.owner.name,
                "team_name": home_team.name,
                "year": season.year,
                "week": matchup.week,
                "opponent_name": away_team.name if away_team else None,
            })

        if away_team and away_team.owner:
            scores.append({
                "score": matchup.away_score,
                "owner_id": away_team.owner.id,
                "owner_name": away_team.owner.name,
                "team_name": away_team.name,
                "year": season.year,
                "week": matchup.week,
                "opponent_name": home_team.name if home_team else None,
            })

    # Sort by score descending and take top N
    scores.sort(key=lambda x: x["score"], reverse=True)
    return [WeeklyScoreRecord(**s) for s in scores[:limit]]


def get_top_season_points(db: Session, limit: int = 10) -> List[SeasonPointsRecord]:
    """Get the highest season point totals."""
    teams = db.query(Team).options(
        joinedload(Team.owner),
        joinedload(Team.season),
    ).order_by(desc(Team.points_for)).limit(limit).all()

    return [
        SeasonPointsRecord(
            points=team.points_for,
            owner_id=team.owner.id,
            owner_name=team.owner.name,
            team_name=team.name,
            year=team.season.year,
        )
        for team in teams if team.owner
    ]


def get_top_win_streaks(db: Session, limit: int = 10) -> List[WinStreakRecord]:
    """Get the longest win streaks."""
    teams = db.query(Team).options(
        joinedload(Team.owner),
        joinedload(Team.season),
    ).filter(Team.longest_win_streak > 0).order_by(
        desc(Team.longest_win_streak)
    ).limit(limit).all()

    return [
        WinStreakRecord(
            streak=team.longest_win_streak,
            owner_id=team.owner.id,
            owner_name=team.owner.name,
            team_name=team.name,
            year=team.season.year,
        )
        for team in teams if team.owner
    ]


def get_most_trades_in_season(db: Session) -> Optional[SeasonTradesRecord]:
    """Get the owner with most trades in a single season."""
    # Get all trades with their teams and seasons
    trades = db.query(Trade).options(
        joinedload(Trade.season),
        joinedload(Trade.teams).joinedload(Team.owner),
    ).filter(Trade.status == "completed").all()

    if not trades:
        return None

    # Count trades per owner per season
    owner_season_trades = defaultdict(lambda: defaultdict(int))
    owner_info = {}

    for trade in trades:
        season_year = trade.season.year
        for team in trade.teams:
            if team.owner:
                owner_id = team.owner.id
                owner_season_trades[owner_id][season_year] += 1
                owner_info[owner_id] = team.owner.name

    # Find the max
    max_trades = 0
    max_owner_id = None
    max_year = None

    for owner_id, season_counts in owner_season_trades.items():
        for year, count in season_counts.items():
            if count > max_trades:
                max_trades = count
                max_owner_id = owner_id
                max_year = year

    if max_owner_id is None:
        return None

    return SeasonTradesRecord(
        trade_count=max_trades,
        owner_id=max_owner_id,
        owner_name=owner_info[max_owner_id],
        year=max_year,
    )


# ============= API Endpoints =============

@router.get("", response_model=AllRecordsResponse)
async def get_all_records(db: Session = Depends(get_db)):
    """Get all league records.

    Returns:
    - Highest single-week score (all-time)
    - Most points in a season
    - Longest win streak
    - Most trades in a season by an owner
    - Top N lists for weekly scores, season points, and win streaks

    Each record includes owner name and year.
    """
    # Get top weekly scores
    top_weekly_scores = get_highest_weekly_scores(db, limit=10)
    highest_single_week = top_weekly_scores[0] if top_weekly_scores else None

    # Get top season points
    top_season_points = get_top_season_points(db, limit=10)
    most_points_in_season = top_season_points[0] if top_season_points else None

    # Get top win streaks
    top_win_streaks = get_top_win_streaks(db, limit=10)
    longest_win_streak = top_win_streaks[0] if top_win_streaks else None

    # Get most trades in a season
    most_trades = get_most_trades_in_season(db)

    return AllRecordsResponse(
        highest_single_week_score=highest_single_week,
        most_points_in_season=most_points_in_season,
        longest_win_streak=longest_win_streak,
        most_trades_in_season=most_trades,
        top_weekly_scores=top_weekly_scores,
        top_season_points=top_season_points,
        top_win_streaks=top_win_streaks,
    )
