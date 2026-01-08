"""Hall of Fame API routes for Fantasy League History Tracker.

This module provides endpoints for:
- Listing all champions by year
- Championship count leaderboard
- Dynasty/repeat champion tracking
"""

from typing import List, Optional
from collections import defaultdict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.db.models import Owner, Team, Season, League


router = APIRouter(prefix="/api/hall-of-fame", tags=["hall-of-fame"])


# ============= Pydantic Models =============

class ChampionOwner(BaseModel):
    """Owner info for championship display."""
    id: int
    name: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ChampionSeason(BaseModel):
    """Championship season details."""
    year: int
    league_id: int
    league_name: str
    platform: str
    team_name: str
    record: str  # e.g., "12-2"
    points_for: float
    champion: ChampionOwner
    runner_up: Optional[ChampionOwner] = None


class ChampionshipCount(BaseModel):
    """Championship count for leaderboard."""
    owner: ChampionOwner
    championships: int
    years: List[int]
    leagues: List[str]


class DynastyStreak(BaseModel):
    """Dynasty/consecutive championship streak."""
    owner: ChampionOwner
    streak: int
    start_year: int
    end_year: int
    league_name: str


class HallOfFameResponse(BaseModel):
    """Complete Hall of Fame data."""
    champions_by_year: List[ChampionSeason]
    championship_leaderboard: List[ChampionshipCount]
    dynasties: List[DynastyStreak]
    total_seasons: int
    unique_champions: int


# ============= Helper Functions =============

def calculate_dynasties(champions: List[dict]) -> List[dict]:
    """Calculate consecutive championship streaks.

    A dynasty is when an owner wins back-to-back championships
    in the same league.
    """
    # Group by league and owner
    league_owner_years = defaultdict(lambda: defaultdict(list))

    for champ in champions:
        league_id = champ["league_id"]
        owner_id = champ["owner_id"]
        league_owner_years[league_id][owner_id].append({
            "year": champ["year"],
            "league_name": champ["league_name"],
            "owner": champ["owner"],
        })

    dynasties = []

    for league_id, owners in league_owner_years.items():
        for owner_id, years_data in owners.items():
            # Sort by year
            years_data.sort(key=lambda x: x["year"])

            # Find consecutive streaks
            if len(years_data) < 2:
                continue

            streak_start = 0
            for i in range(1, len(years_data)):
                if years_data[i]["year"] != years_data[i-1]["year"] + 1:
                    # Streak broken
                    if i - streak_start >= 2:
                        dynasties.append({
                            "owner": years_data[streak_start]["owner"],
                            "streak": i - streak_start,
                            "start_year": years_data[streak_start]["year"],
                            "end_year": years_data[i-1]["year"],
                            "league_name": years_data[streak_start]["league_name"],
                        })
                    streak_start = i

            # Check final streak
            if len(years_data) - streak_start >= 2:
                dynasties.append({
                    "owner": years_data[streak_start]["owner"],
                    "streak": len(years_data) - streak_start,
                    "start_year": years_data[streak_start]["year"],
                    "end_year": years_data[-1]["year"],
                    "league_name": years_data[streak_start]["league_name"],
                })

    # Sort by streak length descending
    dynasties.sort(key=lambda x: x["streak"], reverse=True)

    return dynasties


# ============= API Endpoints =============

@router.get("", response_model=HallOfFameResponse)
async def get_hall_of_fame(db: Session = Depends(get_db)):
    """Get complete Hall of Fame data.

    Returns:
    - Champions by year (sorted by year descending)
    - Championship count leaderboard
    - Dynasty streaks (consecutive championships in same league)
    - Summary statistics
    """
    # Get all seasons with champions
    seasons = db.query(Season).options(
        joinedload(Season.league),
    ).filter(
        Season.champion_team_id.isnot(None)
    ).order_by(Season.year.desc()).all()

    champions_by_year = []
    champion_data = []  # For dynasty calculation
    championship_counts = defaultdict(lambda: {"count": 0, "years": [], "leagues": set(), "owner": None})

    for season in seasons:
        league = season.league

        # Get champion team with owner
        champ_team = db.query(Team).options(
            joinedload(Team.owner)
        ).filter(Team.id == season.champion_team_id).first()

        if not champ_team or not champ_team.owner:
            continue

        champion_owner = ChampionOwner(
            id=champ_team.owner.id,
            name=champ_team.owner.name,
            display_name=champ_team.owner.display_name,
            avatar_url=champ_team.owner.avatar_url,
        )

        # Get runner-up if exists
        runner_up_owner = None
        if season.runner_up_team_id:
            runner_up_team = db.query(Team).options(
                joinedload(Team.owner)
            ).filter(Team.id == season.runner_up_team_id).first()

            if runner_up_team and runner_up_team.owner:
                runner_up_owner = ChampionOwner(
                    id=runner_up_team.owner.id,
                    name=runner_up_team.owner.name,
                    display_name=runner_up_team.owner.display_name,
                    avatar_url=runner_up_team.owner.avatar_url,
                )

        # Build record string
        record = f"{champ_team.wins}-{champ_team.losses}"
        if champ_team.ties > 0:
            record += f"-{champ_team.ties}"

        champions_by_year.append(ChampionSeason(
            year=season.year,
            league_id=league.id,
            league_name=league.name,
            platform=league.platform.value,
            team_name=champ_team.name,
            record=record,
            points_for=champ_team.points_for,
            champion=champion_owner,
            runner_up=runner_up_owner,
        ))

        # Track for dynasty calculation
        champion_data.append({
            "year": season.year,
            "league_id": league.id,
            "league_name": league.name,
            "owner_id": champ_team.owner.id,
            "owner": champion_owner,
        })

        # Track championship counts
        owner_id = champ_team.owner.id
        championship_counts[owner_id]["count"] += 1
        championship_counts[owner_id]["years"].append(season.year)
        championship_counts[owner_id]["leagues"].add(league.name)
        championship_counts[owner_id]["owner"] = champion_owner

    # Build championship leaderboard
    championship_leaderboard = []
    for owner_id, data in championship_counts.items():
        championship_leaderboard.append(ChampionshipCount(
            owner=data["owner"],
            championships=data["count"],
            years=sorted(data["years"], reverse=True),
            leagues=list(data["leagues"]),
        ))

    # Sort by championship count descending
    championship_leaderboard.sort(key=lambda x: x.championships, reverse=True)

    # Calculate dynasties
    dynasty_data = calculate_dynasties(champion_data)
    dynasties = [
        DynastyStreak(
            owner=d["owner"],
            streak=d["streak"],
            start_year=d["start_year"],
            end_year=d["end_year"],
            league_name=d["league_name"],
        )
        for d in dynasty_data
    ]

    # Calculate summary stats
    unique_champion_ids = set(championship_counts.keys())

    return HallOfFameResponse(
        champions_by_year=champions_by_year,
        championship_leaderboard=championship_leaderboard,
        dynasties=dynasties,
        total_seasons=len(champions_by_year),
        unique_champions=len(unique_champion_ids),
    )


@router.get("/leaderboard", response_model=List[ChampionshipCount])
async def get_championship_leaderboard(db: Session = Depends(get_db)):
    """Get just the championship leaderboard.

    Returns owners sorted by championship count.
    """
    # Get all champion teams grouped by owner
    championship_counts = defaultdict(lambda: {"count": 0, "years": [], "leagues": set(), "owner": None})

    seasons = db.query(Season).options(
        joinedload(Season.league),
    ).filter(
        Season.champion_team_id.isnot(None)
    ).all()

    for season in seasons:
        champ_team = db.query(Team).options(
            joinedload(Team.owner)
        ).filter(Team.id == season.champion_team_id).first()

        if not champ_team or not champ_team.owner:
            continue

        owner_id = champ_team.owner.id
        championship_counts[owner_id]["count"] += 1
        championship_counts[owner_id]["years"].append(season.year)
        championship_counts[owner_id]["leagues"].add(season.league.name)
        championship_counts[owner_id]["owner"] = ChampionOwner(
            id=champ_team.owner.id,
            name=champ_team.owner.name,
            display_name=champ_team.owner.display_name,
            avatar_url=champ_team.owner.avatar_url,
        )

    # Build and sort leaderboard
    leaderboard = [
        ChampionshipCount(
            owner=data["owner"],
            championships=data["count"],
            years=sorted(data["years"], reverse=True),
            leagues=list(data["leagues"]),
        )
        for data in championship_counts.values()
    ]

    leaderboard.sort(key=lambda x: x.championships, reverse=True)

    return leaderboard
