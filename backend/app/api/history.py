"""League history API routes for Fantasy League History Tracker.

This module provides endpoints for:
- Listing all owners with career statistics
- Getting full history for a specific owner
- Listing all seasons with champions
- Getting head-to-head rivalry statistics between two owners
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.db.models import Owner, Team, Season, League, Matchup


router = APIRouter(prefix="/api/history", tags=["history"])


# ============= Pydantic Models =============

class OwnerBrief(BaseModel):
    """Brief owner info."""
    id: int
    name: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class OwnerWithStats(BaseModel):
    """Owner with career statistics."""
    id: int
    name: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    total_wins: int
    total_losses: int
    total_ties: int
    total_points: float
    seasons_played: int
    playoff_appearances: int
    championships: int
    win_percentage: float

    class Config:
        from_attributes = True


class SeasonTeamStats(BaseModel):
    """Stats for a team in a specific season."""
    year: int
    league_name: str
    team_name: str
    wins: int
    losses: int
    ties: int
    points_for: float
    regular_season_rank: Optional[int] = None
    final_rank: Optional[int] = None
    made_playoffs: bool
    is_champion: bool


class CareerStats(BaseModel):
    """Aggregated career statistics."""
    total_wins: int
    total_losses: int
    total_ties: int
    total_points: float
    seasons_played: int
    playoff_appearances: int
    championships: int
    win_percentage: float
    matchups_won: int
    matchups_lost: int
    matchups_tied: int
    avg_points_per_season: float


class OwnerHistoryResponse(BaseModel):
    """Full history response for an owner."""
    owner: OwnerBrief
    career_stats: CareerStats
    seasons: List[SeasonTeamStats]


class SeasonChampion(BaseModel):
    """Champion info for a season."""
    id: int
    name: str


class SeasonResponse(BaseModel):
    """Season info with champion."""
    id: int
    year: int
    league_id: int
    league_name: str
    platform: str
    is_complete: bool
    champion: Optional[SeasonChampion] = None
    runner_up: Optional[SeasonChampion] = None
    team_count: Optional[int] = None


class MatchupDetail(BaseModel):
    """Individual matchup details for head-to-head."""
    year: int
    week: int
    owner1_score: float
    owner2_score: float
    winner_id: Optional[int] = None
    is_playoff: bool
    is_championship: bool


class HeadToHeadResponse(BaseModel):
    """Head-to-head rivalry statistics."""
    owner1: OwnerBrief
    owner2: OwnerBrief
    total_matchups: int
    owner1_wins: int
    owner2_wins: int
    ties: int
    owner1_avg_score: Optional[float] = None
    owner2_avg_score: Optional[float] = None
    playoff_matchups: int
    owner1_playoff_wins: int
    owner2_playoff_wins: int
    matchups: List[MatchupDetail]


# ============= Helper Functions =============

def calculate_owner_stats(teams: List[Team]) -> dict:
    """Calculate aggregated statistics from a list of teams."""
    total_wins = sum(team.wins for team in teams)
    total_losses = sum(team.losses for team in teams)
    total_ties = sum(team.ties for team in teams)
    total_points = sum(team.points_for for team in teams)
    seasons_played = len(teams)
    playoff_appearances = sum(1 for team in teams if team.made_playoffs)
    championships = sum(1 for team in teams if team.final_rank == 1)

    total_games = total_wins + total_losses + total_ties
    win_percentage = (total_wins / total_games * 100) if total_games > 0 else 0.0

    return {
        "total_wins": total_wins,
        "total_losses": total_losses,
        "total_ties": total_ties,
        "total_points": round(total_points, 2),
        "seasons_played": seasons_played,
        "playoff_appearances": playoff_appearances,
        "championships": championships,
        "win_percentage": round(win_percentage, 2),
    }


def get_matchup_stats_for_owner(db: Session, owner_id: int) -> dict:
    """Get matchup win/loss/tie counts for an owner."""
    # Get all team IDs for this owner
    team_ids = db.query(Team.id).filter(Team.owner_id == owner_id).all()
    team_id_list = [t[0] for t in team_ids]

    if not team_id_list:
        return {"matchups_won": 0, "matchups_lost": 0, "matchups_tied": 0}

    # Count wins (where this owner's team won)
    wins = db.query(func.count(Matchup.id)).filter(
        Matchup.winner_team_id.in_(team_id_list)
    ).scalar() or 0

    # Count ties
    ties = db.query(func.count(Matchup.id)).filter(
        and_(
            Matchup.is_tie == True,
            or_(
                Matchup.home_team_id.in_(team_id_list),
                Matchup.away_team_id.in_(team_id_list)
            )
        )
    ).scalar() or 0

    # Count total matchups
    total = db.query(func.count(Matchup.id)).filter(
        or_(
            Matchup.home_team_id.in_(team_id_list),
            Matchup.away_team_id.in_(team_id_list)
        )
    ).scalar() or 0

    losses = total - wins - ties

    return {
        "matchups_won": wins,
        "matchups_lost": losses,
        "matchups_tied": ties,
    }


# ============= API Endpoints =============

@router.get("/owners", response_model=List[OwnerWithStats])
async def list_owners_with_stats(db: Session = Depends(get_db)):
    """List all owners with their career statistics.

    Returns owners sorted by total wins (descending).
    Includes career stats aggregated across all seasons and platforms.
    """
    owners = db.query(Owner).options(joinedload(Owner.teams)).all()

    result = []
    for owner in owners:
        stats = calculate_owner_stats(owner.teams)
        result.append(OwnerWithStats(
            id=owner.id,
            name=owner.name,
            display_name=owner.display_name,
            avatar_url=owner.avatar_url,
            **stats
        ))

    # Sort by total wins descending
    result.sort(key=lambda x: x.total_wins, reverse=True)

    return result


@router.get("/owners/{owner_id}", response_model=OwnerHistoryResponse)
async def get_owner_history(owner_id: int, db: Session = Depends(get_db)):
    """Get full history for a specific owner.

    Returns:
    - Owner info
    - Career statistics (including matchup wins/losses)
    - Season-by-season breakdown (sorted by year descending)

    Raises:
        404: If owner not found
    """
    owner = db.query(Owner).options(
        joinedload(Owner.teams).joinedload(Team.season).joinedload(Season.league)
    ).filter(Owner.id == owner_id).first()

    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Owner with ID {owner_id} not found"
        )

    # Calculate career stats
    base_stats = calculate_owner_stats(owner.teams)
    matchup_stats = get_matchup_stats_for_owner(db, owner_id)

    avg_points = (base_stats["total_points"] / base_stats["seasons_played"]
                  if base_stats["seasons_played"] > 0 else 0.0)

    career_stats = CareerStats(
        **base_stats,
        **matchup_stats,
        avg_points_per_season=round(avg_points, 2),
    )

    # Build season-by-season breakdown
    seasons = []
    for team in owner.teams:
        season = team.season
        league = season.league
        is_champion = team.final_rank == 1

        seasons.append(SeasonTeamStats(
            year=season.year,
            league_name=league.name,
            team_name=team.name,
            wins=team.wins,
            losses=team.losses,
            ties=team.ties,
            points_for=team.points_for,
            regular_season_rank=team.regular_season_rank,
            final_rank=team.final_rank,
            made_playoffs=team.made_playoffs,
            is_champion=is_champion,
        ))

    # Sort by year descending
    seasons.sort(key=lambda x: x.year, reverse=True)

    return OwnerHistoryResponse(
        owner=OwnerBrief(
            id=owner.id,
            name=owner.name,
            display_name=owner.display_name,
            avatar_url=owner.avatar_url,
        ),
        career_stats=career_stats,
        seasons=seasons,
    )


@router.get("/seasons", response_model=List[SeasonResponse])
async def list_seasons(
    league_id: Optional[int] = Query(None, description="Filter by league ID"),
    db: Session = Depends(get_db)
):
    """List all seasons with their champions.

    Returns seasons sorted by year (descending).
    Optional filter by league_id to see seasons for a specific league.
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

        # Get champion info if available
        champion = None
        if season.champion_team_id:
            champ_team = db.query(Team).options(
                joinedload(Team.owner)
            ).filter(Team.id == season.champion_team_id).first()
            if champ_team and champ_team.owner:
                champion = SeasonChampion(
                    id=champ_team.owner.id,
                    name=champ_team.owner.name,
                )

        # Get runner-up info if available
        runner_up = None
        if season.runner_up_team_id:
            runner_up_team = db.query(Team).options(
                joinedload(Team.owner)
            ).filter(Team.id == season.runner_up_team_id).first()
            if runner_up_team and runner_up_team.owner:
                runner_up = SeasonChampion(
                    id=runner_up_team.owner.id,
                    name=runner_up_team.owner.name,
                )

        result.append(SeasonResponse(
            id=season.id,
            year=season.year,
            league_id=league.id,
            league_name=league.name,
            platform=league.platform.value,
            is_complete=season.is_complete,
            champion=champion,
            runner_up=runner_up,
            team_count=league.team_count,
        ))

    return result


@router.get("/head-to-head/{owner1_id}/{owner2_id}", response_model=HeadToHeadResponse)
async def get_head_to_head(
    owner1_id: int,
    owner2_id: int,
    db: Session = Depends(get_db)
):
    """Get head-to-head rivalry statistics between two owners.

    Returns:
    - Win/loss/tie record between the two owners
    - Average scores
    - Playoff matchup stats
    - List of all historical matchups

    Raises:
        404: If either owner not found
    """
    owner1 = db.query(Owner).filter(Owner.id == owner1_id).first()
    owner2 = db.query(Owner).filter(Owner.id == owner2_id).first()

    if not owner1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Owner with ID {owner1_id} not found"
        )
    if not owner2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Owner with ID {owner2_id} not found"
        )

    # Get all team IDs for each owner
    team1_ids = [t.id for t in db.query(Team).filter(Team.owner_id == owner1_id).all()]
    team2_ids = [t.id for t in db.query(Team).filter(Team.owner_id == owner2_id).all()]

    # Find all matchups between these two owners
    matchups = db.query(Matchup).options(
        joinedload(Matchup.season)
    ).filter(
        or_(
            and_(
                Matchup.home_team_id.in_(team1_ids),
                Matchup.away_team_id.in_(team2_ids)
            ),
            and_(
                Matchup.home_team_id.in_(team2_ids),
                Matchup.away_team_id.in_(team1_ids)
            )
        )
    ).all()

    # Calculate statistics
    owner1_wins = 0
    owner2_wins = 0
    ties = 0
    owner1_scores = []
    owner2_scores = []
    playoff_matchups = 0
    owner1_playoff_wins = 0
    owner2_playoff_wins = 0
    matchup_details = []

    for matchup in matchups:
        # Determine which score belongs to which owner
        if matchup.home_team_id in team1_ids:
            owner1_score = matchup.home_score
            owner2_score = matchup.away_score
        else:
            owner1_score = matchup.away_score
            owner2_score = matchup.home_score

        owner1_scores.append(owner1_score)
        owner2_scores.append(owner2_score)

        # Determine winner
        winner_id = None
        if matchup.is_tie:
            ties += 1
        elif owner1_score > owner2_score:
            owner1_wins += 1
            winner_id = owner1_id
            if matchup.is_playoff:
                owner1_playoff_wins += 1
        else:
            owner2_wins += 1
            winner_id = owner2_id
            if matchup.is_playoff:
                owner2_playoff_wins += 1

        if matchup.is_playoff:
            playoff_matchups += 1

        matchup_details.append(MatchupDetail(
            year=matchup.season.year,
            week=matchup.week,
            owner1_score=owner1_score,
            owner2_score=owner2_score,
            winner_id=winner_id,
            is_playoff=matchup.is_playoff,
            is_championship=matchup.is_championship,
        ))

    # Sort matchups by year and week (most recent first)
    matchup_details.sort(key=lambda x: (x.year, x.week), reverse=True)

    return HeadToHeadResponse(
        owner1=OwnerBrief(
            id=owner1.id,
            name=owner1.name,
            display_name=owner1.display_name,
            avatar_url=owner1.avatar_url,
        ),
        owner2=OwnerBrief(
            id=owner2.id,
            name=owner2.name,
            display_name=owner2.display_name,
            avatar_url=owner2.avatar_url,
        ),
        total_matchups=len(matchups),
        owner1_wins=owner1_wins,
        owner2_wins=owner2_wins,
        ties=ties,
        owner1_avg_score=round(sum(owner1_scores) / len(owner1_scores), 2) if owner1_scores else None,
        owner2_avg_score=round(sum(owner2_scores) / len(owner2_scores), 2) if owner2_scores else None,
        playoff_matchups=playoff_matchups,
        owner1_playoff_wins=owner1_playoff_wins,
        owner2_playoff_wins=owner2_playoff_wins,
        matchups=matchup_details,
    )
