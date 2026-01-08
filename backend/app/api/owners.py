"""Owner mapping API routes for Fantasy League History Tracker.

This module provides endpoints for:
- Listing and viewing owners
- Creating and updating owner platform mappings
- Merging owners from different platforms
- Viewing aggregated career statistics
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Owner, Team


router = APIRouter(prefix="/api/owners", tags=["owners"])


# ============= Pydantic Models =============

class OwnerResponse(BaseModel):
    """Response model for an owner."""
    id: int
    name: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    sleeper_user_id: Optional[str] = None
    yahoo_user_id: Optional[str] = None

    class Config:
        from_attributes = True


class CreateOwnerMappingRequest(BaseModel):
    """Request model for creating a new owner with platform mappings."""
    name: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    sleeper_user_id: Optional[str] = None
    yahoo_user_id: Optional[str] = None


class UpdateOwnerMappingRequest(BaseModel):
    """Request model for updating owner platform mappings."""
    sleeper_user_id: Optional[str] = None
    yahoo_user_id: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class MergeOwnersRequest(BaseModel):
    """Request model for merging two owners."""
    primary_owner_id: int
    secondary_owner_id: int


class OwnerStatsResponse(BaseModel):
    """Response model for owner career statistics."""
    id: int
    name: str
    total_wins: int
    total_losses: int
    total_ties: int
    total_points: float
    seasons_played: int
    playoff_appearances: int
    championships: int
    avg_regular_season_rank: Optional[float] = None


# ============= API Endpoints =============

@router.get("", response_model=List[OwnerResponse])
async def list_owners(db: Session = Depends(get_db)):
    """List all owners in the system.

    Returns all owners with their platform mappings.
    """
    owners = db.query(Owner).order_by(Owner.name).all()
    return owners


@router.get("/unmapped", response_model=List[OwnerResponse])
async def get_unmapped_owners(db: Session = Depends(get_db)):
    """Get owners that are not mapped to both platforms.

    Returns owners that have only one platform ID set (or neither).
    These owners may need to be merged or linked.
    """
    owners = db.query(Owner).filter(
        or_(
            Owner.sleeper_user_id.is_(None),
            Owner.yahoo_user_id.is_(None)
        )
    ).order_by(Owner.name).all()
    return owners


@router.get("/{owner_id}", response_model=OwnerResponse)
async def get_owner(owner_id: int, db: Session = Depends(get_db)):
    """Get a specific owner by ID.

    Args:
        owner_id: The database ID of the owner

    Returns:
        Owner details including platform mappings

    Raises:
        404: If owner not found
    """
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Owner with ID {owner_id} not found"
        )
    return owner


@router.get("/{owner_id}/stats", response_model=OwnerStatsResponse)
async def get_owner_stats(owner_id: int, db: Session = Depends(get_db)):
    """Get aggregated career statistics for an owner.

    Calculates stats across all seasons and platforms.

    Args:
        owner_id: The database ID of the owner

    Returns:
        Aggregated career statistics

    Raises:
        404: If owner not found
    """
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Owner with ID {owner_id} not found"
        )

    # Get all teams for this owner
    teams = db.query(Team).filter(Team.owner_id == owner_id).all()

    # Calculate aggregated stats
    total_wins = sum(team.wins for team in teams)
    total_losses = sum(team.losses for team in teams)
    total_ties = sum(team.ties for team in teams)
    total_points = sum(team.points_for for team in teams)
    seasons_played = len(teams)
    playoff_appearances = sum(1 for team in teams if team.made_playoffs)
    championships = sum(1 for team in teams if team.final_rank == 1)

    # Calculate average regular season rank (exclude None values)
    ranks = [team.regular_season_rank for team in teams if team.regular_season_rank is not None]
    avg_rank = sum(ranks) / len(ranks) if ranks else None

    return OwnerStatsResponse(
        id=owner.id,
        name=owner.name,
        total_wins=total_wins,
        total_losses=total_losses,
        total_ties=total_ties,
        total_points=round(total_points, 2),
        seasons_played=seasons_played,
        playoff_appearances=playoff_appearances,
        championships=championships,
        avg_regular_season_rank=round(avg_rank, 2) if avg_rank else None,
    )


@router.post("/mapping", response_model=OwnerResponse, status_code=status.HTTP_201_CREATED)
async def create_owner_mapping(
    request: CreateOwnerMappingRequest,
    db: Session = Depends(get_db)
):
    """Create a new owner with platform mappings.

    Args:
        request: Owner details including name and optional platform IDs

    Returns:
        The created owner

    Raises:
        400: If a platform ID is already in use by another owner
    """
    # Check for existing platform mappings
    if request.sleeper_user_id:
        existing = db.query(Owner).filter(
            Owner.sleeper_user_id == request.sleeper_user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sleeper user ID '{request.sleeper_user_id}' is already mapped to owner '{existing.name}'"
            )

    if request.yahoo_user_id:
        existing = db.query(Owner).filter(
            Owner.yahoo_user_id == request.yahoo_user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Yahoo user ID '{request.yahoo_user_id}' is already mapped to owner '{existing.name}'"
            )

    owner = Owner(
        name=request.name,
        display_name=request.display_name,
        avatar_url=request.avatar_url,
        sleeper_user_id=request.sleeper_user_id,
        yahoo_user_id=request.yahoo_user_id,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)

    return owner


@router.put("/{owner_id}/mapping", response_model=OwnerResponse)
async def update_owner_mapping(
    owner_id: int,
    request: UpdateOwnerMappingRequest,
    db: Session = Depends(get_db)
):
    """Update platform mappings for an existing owner.

    Links the owner to additional platforms (Yahoo and/or Sleeper).

    Args:
        owner_id: The database ID of the owner
        request: Platform IDs to add/update

    Returns:
        The updated owner

    Raises:
        404: If owner not found
        400: If platform ID is already mapped to another owner
    """
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Owner with ID {owner_id} not found"
        )

    # Check and update Sleeper mapping
    if request.sleeper_user_id is not None:
        existing = db.query(Owner).filter(
            Owner.sleeper_user_id == request.sleeper_user_id,
            Owner.id != owner_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sleeper user ID '{request.sleeper_user_id}' is already mapped to owner '{existing.name}'"
            )
        owner.sleeper_user_id = request.sleeper_user_id

    # Check and update Yahoo mapping
    if request.yahoo_user_id is not None:
        existing = db.query(Owner).filter(
            Owner.yahoo_user_id == request.yahoo_user_id,
            Owner.id != owner_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Yahoo user ID '{request.yahoo_user_id}' is already mapped to owner '{existing.name}'"
            )
        owner.yahoo_user_id = request.yahoo_user_id

    # Update optional fields
    if request.display_name is not None:
        owner.display_name = request.display_name
    if request.avatar_url is not None:
        owner.avatar_url = request.avatar_url

    db.commit()
    db.refresh(owner)

    return owner


@router.delete("/{owner_id}/mapping/{platform}", response_model=OwnerResponse)
async def unlink_platform(
    owner_id: int,
    platform: str,
    db: Session = Depends(get_db)
):
    """Unlink a platform from an owner.

    Removes the association between an owner and a platform account.

    Args:
        owner_id: The database ID of the owner
        platform: The platform to unlink ('sleeper' or 'yahoo')

    Returns:
        The updated owner

    Raises:
        404: If owner not found
        400: If invalid platform specified
    """
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Owner with ID {owner_id} not found"
        )

    platform_lower = platform.lower()
    if platform_lower == "sleeper":
        owner.sleeper_user_id = None
    elif platform_lower == "yahoo":
        owner.yahoo_user_id = None
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform '{platform}'. Must be 'sleeper' or 'yahoo'"
        )

    db.commit()
    db.refresh(owner)

    return owner


@router.post("/merge", response_model=OwnerResponse)
async def merge_owners(
    request: MergeOwnersRequest,
    db: Session = Depends(get_db)
):
    """Merge two owners into one.

    Combines platform mappings from secondary owner into primary owner.
    Transfers all teams from secondary owner to primary.
    Deletes the secondary owner after merging.

    Args:
        request: IDs of the primary (keep) and secondary (merge into) owners

    Returns:
        The merged primary owner

    Raises:
        400: If trying to merge owner with itself
        404: If either owner not found
    """
    if request.primary_owner_id == request.secondary_owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot merge owner with itself"
        )

    primary = db.query(Owner).filter(Owner.id == request.primary_owner_id).first()
    secondary = db.query(Owner).filter(Owner.id == request.secondary_owner_id).first()

    if not primary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Primary owner with ID {request.primary_owner_id} not found"
        )
    if not secondary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Secondary owner with ID {request.secondary_owner_id} not found"
        )

    # Store values to merge before clearing unique constraints
    sleeper_id_to_merge = secondary.sleeper_user_id if not primary.sleeper_user_id else None
    yahoo_id_to_merge = secondary.yahoo_user_id if not primary.yahoo_user_id else None
    display_name_to_merge = secondary.display_name if not primary.display_name else None
    avatar_url_to_merge = secondary.avatar_url if not primary.avatar_url else None

    # Transfer all teams from secondary to primary
    for team in secondary.teams:
        team.owner_id = primary.id

    # Clear unique fields on secondary before deletion to avoid constraint violations
    secondary.sleeper_user_id = None
    secondary.yahoo_user_id = None
    db.flush()  # Flush the changes to secondary

    # Now safely update primary with merged values
    if sleeper_id_to_merge:
        primary.sleeper_user_id = sleeper_id_to_merge
    if yahoo_id_to_merge:
        primary.yahoo_user_id = yahoo_id_to_merge
    if display_name_to_merge:
        primary.display_name = display_name_to_merge
    if avatar_url_to_merge:
        primary.avatar_url = avatar_url_to_merge

    # Delete secondary owner
    db.delete(secondary)
    db.commit()
    db.refresh(primary)

    return primary
