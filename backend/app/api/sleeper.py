"""Sleeper API routes for importing fantasy football data."""

from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.sleeper_service import SleeperService

router = APIRouter(prefix="/api/sleeper", tags=["sleeper"])


class ImportLeagueRequest(BaseModel):
    """Request model for importing a league."""

    league_id: str


class ImportLeagueResponse(BaseModel):
    """Response model for league import."""

    league_id: int
    league_name: str
    season_year: int
    teams_imported: int
    matchups_imported: int
    trades_imported: int


class LeagueInfoResponse(BaseModel):
    """Response model for league info."""

    league_id: str
    name: str
    season: str
    total_rosters: int
    status: str
    scoring_type: Optional[str] = None


class UserResponse(BaseModel):
    """Response model for a Sleeper user."""

    user_id: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class RosterResponse(BaseModel):
    """Response model for a Sleeper roster."""

    roster_id: int
    owner_id: Optional[str] = None
    wins: int
    losses: int
    ties: int
    points_for: float


class MatchupResponse(BaseModel):
    """Response model for a matchup."""

    matchup_id: int
    roster_id: int
    points: Optional[float]


class TradeResponse(BaseModel):
    """Response model for a trade."""

    transaction_id: str
    roster_ids: List[int]
    week: int
    status: str
    adds: Optional[Dict[str, Any]] = None
    drops: Optional[Dict[str, Any]] = None


@router.post("/import", response_model=ImportLeagueResponse)
async def import_league(request: ImportLeagueRequest, db: Session = Depends(get_db)):
    """Import all data for a Sleeper league.

    This endpoint fetches and stores:
    - League information
    - Users and rosters (as owners and teams)
    - All matchups for the season
    - All trades for the season
    """
    try:
        service = SleeperService(db)
        result = await service.import_full_league(request.league_id)
        return ImportLeagueResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/league/{league_id}", response_model=LeagueInfoResponse)
async def get_league_info(league_id: str):
    """Fetch league information from Sleeper API (without storing)."""
    from app.services.sleeper_client import SleeperClient

    try:
        client = SleeperClient()
        data = await client.get_league(league_id)

        # Determine scoring type
        scoring_settings = data.get("scoring_settings", {})
        if scoring_settings.get("rec", 0) == 1:
            scoring_type = "PPR"
        elif scoring_settings.get("rec", 0) == 0.5:
            scoring_type = "Half PPR"
        else:
            scoring_type = "Standard"

        return LeagueInfoResponse(
            league_id=data.get("league_id", league_id),
            name=data.get("name", "Unknown"),
            season=data.get("season", ""),
            total_rosters=data.get("total_rosters", 0),
            status=data.get("status", "unknown"),
            scoring_type=scoring_type,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/league/{league_id}/users", response_model=List[UserResponse])
async def get_league_users(league_id: str):
    """Fetch all users in a Sleeper league (without storing)."""
    from app.services.sleeper_client import SleeperClient

    try:
        client = SleeperClient()
        users = await client.get_users(league_id)

        return [
            UserResponse(
                user_id=u.get("user_id", ""),
                username=u.get("username"),
                display_name=u.get("display_name"),
                avatar_url=SleeperClient.get_avatar_url(u.get("avatar")),
            )
            for u in users
            if u.get("user_id")
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/league/{league_id}/rosters", response_model=List[RosterResponse])
async def get_league_rosters(league_id: str):
    """Fetch all rosters in a Sleeper league (without storing)."""
    from app.services.sleeper_client import SleeperClient

    try:
        client = SleeperClient()
        rosters = await client.get_rosters(league_id)

        return [
            RosterResponse(
                roster_id=r.get("roster_id", 0),
                owner_id=r.get("owner_id"),
                wins=r.get("settings", {}).get("wins", 0),
                losses=r.get("settings", {}).get("losses", 0),
                ties=r.get("settings", {}).get("ties", 0),
                points_for=r.get("settings", {}).get("fpts", 0)
                + r.get("settings", {}).get("fpts_decimal", 0) / 100,
            )
            for r in rosters
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/league/{league_id}/matchups/{week}", response_model=List[MatchupResponse])
async def get_league_matchups(league_id: str, week: int):
    """Fetch matchups for a specific week (without storing)."""
    from app.services.sleeper_client import SleeperClient

    try:
        client = SleeperClient()
        matchups = await client.get_matchups(league_id, week)

        return [
            MatchupResponse(
                matchup_id=m.get("matchup_id", 0),
                roster_id=m.get("roster_id", 0),
                points=m.get("points"),
            )
            for m in matchups
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/league/{league_id}/trades/{week}", response_model=List[TradeResponse])
async def get_league_trades(league_id: str, week: int):
    """Fetch trades for a specific week (without storing)."""
    from app.services.sleeper_client import SleeperClient

    try:
        client = SleeperClient()
        transactions = await client.get_transactions(league_id, week)

        # Filter to only trades
        trades = [
            t for t in transactions
            if t.get("type") == "trade" and t.get("status") == "complete"
        ]

        return [
            TradeResponse(
                transaction_id=t.get("transaction_id", ""),
                roster_ids=t.get("roster_ids", []),
                week=week,
                status=t.get("status", ""),
                adds=t.get("adds"),
                drops=t.get("drops"),
            )
            for t in trades
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
