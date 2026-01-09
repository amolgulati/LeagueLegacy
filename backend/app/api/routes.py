"""
API route definitions for the Fantasy League History Tracker.
Routes will be added as features are implemented.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")


@router.get("/ping")
async def ping():
    """Simple ping endpoint for testing."""
    return {"message": "pong"}
