"""Yahoo Fantasy API routes for OAuth2 authentication and data import."""

import logging
import os
import re
import time
import traceback
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import get_db
from app.services.yahoo_client import YahooClient, YahooToken, YahooAuthError, YahooAPIError
from app.services.yahoo_service import YahooService
from app.services.yahoo_token_cache import get_token_cache, YahooTokenCache

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/api/yahoo", tags=["yahoo"])

# In-memory fallback store (used when file cache fails or for testing)
_token_store: Dict[str, YahooToken] = {}

# Get the token cache instance
def _get_token_cache() -> YahooTokenCache:
    """Get the token cache instance for persistent storage."""
    return get_token_cache()


def _get_token(session_id: str) -> Optional[YahooToken]:
    """Get token from cache or in-memory store.

    First checks file-based cache, then falls back to in-memory store.
    """
    # Try file cache first
    cache = _get_token_cache()
    token = cache.get_token(session_id)
    if token:
        return token

    # Fall back to in-memory store
    return _token_store.get(session_id)


def _set_token(token: YahooToken, session_id: str) -> None:
    """Store token in both file cache and in-memory store."""
    # Store in file cache
    cache = _get_token_cache()
    cache.set_token(token, session_id)

    # Also store in memory for fast access
    _token_store[session_id] = token


def _delete_token(session_id: str) -> bool:
    """Delete token from both file cache and in-memory store."""
    cache = _get_token_cache()
    deleted_from_cache = cache.delete_token(session_id)

    deleted_from_memory = session_id in _token_store
    if deleted_from_memory:
        del _token_store[session_id]

    return deleted_from_cache or deleted_from_memory


# ============= Request/Response Models =============

class AuthUrlResponse(BaseModel):
    """Response containing OAuth2 authorization URL."""
    authorization_url: str
    state: Optional[str] = None


class TokenExchangeRequest(BaseModel):
    """Request to exchange authorization code for token."""
    authorization_code: str
    state: Optional[str] = None


class TokenResponse(BaseModel):
    """Response containing OAuth2 token info."""
    access_token: str
    token_type: str
    expires_in: int
    authenticated: bool


class SetTokenRequest(BaseModel):
    """Request to set token directly."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    expires_at: Optional[float] = None


class ImportLeagueRequest(BaseModel):
    """Request model for importing a league."""
    league_key: str
    start_week: int = 1
    end_week: int = 17


class ImportLeagueResponse(BaseModel):
    """Response model for league import."""
    league_id: int
    league_name: str
    season_year: int
    teams_imported: int
    matchups_imported: int
    trades_imported: int
    champion_team_id: Optional[int] = None
    champion_name: Optional[str] = None


class ImportHistoricalRequest(BaseModel):
    """Request model for importing historical leagues."""
    game_keys: Optional[List[str]] = None


class ImportHistoricalResponse(BaseModel):
    """Response model for historical league import."""
    leagues_imported: int
    seasons_imported: int
    results: List[dict]


class LeagueInfoResponse(BaseModel):
    """Response model for league info."""
    league_key: str
    league_id: str
    name: str
    num_teams: int
    scoring_type: str
    season: str
    current_week: int
    is_finished: bool


class TeamStandingResponse(BaseModel):
    """Response model for team standings."""
    team_key: str
    team_id: str
    name: str
    manager_name: Optional[str] = None
    wins: int
    losses: int
    ties: int
    points_for: float
    points_against: float
    rank: int


class MatchupTeamResponse(BaseModel):
    """Response model for a team in a matchup."""
    team_key: str
    name: str
    points: float


class MatchupResponse(BaseModel):
    """Response model for a matchup."""
    week: int
    is_playoffs: bool
    is_consolation: bool
    teams: List[MatchupTeamResponse]
    winner_team_key: Optional[str] = None
    is_tied: bool


class TradePlayerResponse(BaseModel):
    """Response model for a player in a trade."""
    player_key: str
    name: str
    source_team_key: str
    destination_team_key: str


class TradeResponse(BaseModel):
    """Response model for a trade."""
    transaction_id: str
    status: str
    timestamp: int
    trader_team_key: str
    tradee_team_key: str
    players: List[TradePlayerResponse]


class UserLeagueResponse(BaseModel):
    """Response model for user's leagues."""
    league_key: str
    name: str
    season: str
    num_teams: int
    scoring_type: str
    is_finished: bool


# ============= Helper Functions =============

def get_authenticated_client(session_id: str = "default") -> YahooClient:
    """Get an authenticated Yahoo client.

    Args:
        session_id: Session identifier for token lookup.

    Returns:
        YahooClient with valid token.

    Raises:
        HTTPException: If not authenticated.
    """
    token = _get_token(session_id)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please complete OAuth flow first."
        )

    client = YahooClient()
    client.set_token(token)
    return client


def get_redirect_uri() -> str:
    """Get the OAuth2 redirect URI from environment or use default.

    Returns:
        Redirect URI string.
    """
    return os.environ.get(
        "YAHOO_REDIRECT_URI",
        "http://localhost:8000/api/yahoo/auth/callback"
    )


def validate_league_key(league_key: str) -> bool:
    """Validate Yahoo league key format.

    Valid formats:
    - 449.l.123456 (game_key.l.league_id)

    Args:
        league_key: The league key to validate.

    Returns:
        True if valid, False otherwise.
    """
    # Pattern: game_key.l.league_id (e.g., "449.l.123456")
    pattern = r"^\d+\.l\.\d+$"
    return bool(re.match(pattern, league_key))


# ============= OAuth2 Authentication Routes =============

@router.get("/auth/url", response_model=AuthUrlResponse)
async def get_authorization_url(
    state: Optional[str] = Query(None, description="CSRF protection state parameter"),
    redirect_uri: Optional[str] = Query(None, description="Custom redirect URI")
):
    """Get the OAuth2 authorization URL for user consent.

    The user should visit this URL to authorize the application
    to access their Yahoo Fantasy data.

    If redirect_uri is not provided, uses YAHOO_REDIRECT_URI env var
    or defaults to http://localhost:8000/api/yahoo/auth/callback
    """
    uri = redirect_uri or get_redirect_uri()
    client = YahooClient(redirect_uri=uri)
    auth_url = client.get_authorization_url(state)

    return AuthUrlResponse(authorization_url=auth_url, state=state)


@router.get("/auth/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code from Yahoo"),
    state: Optional[str] = Query(None, description="State parameter for CSRF validation"),
    session_id: str = Query("default", description="Session identifier")
):
    """OAuth2 callback endpoint for browser redirect flow.

    This endpoint is called by Yahoo after user authorization.
    It exchanges the code for tokens and stores them.

    After successful authentication, redirects to the frontend.
    """
    redirect_uri = get_redirect_uri()
    client = YahooClient(redirect_uri=redirect_uri)

    try:
        token = await client.exchange_code_for_token(code)
        _set_token(token, session_id)

        # Redirect to frontend with success indicator
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}?yahoo_auth=success&session_id={session_id}",
            status_code=302
        )
    except YahooAuthError as e:
        # Redirect to frontend with error
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}?yahoo_auth=error&message={str(e)}",
            status_code=302
        )


@router.post("/auth/token", response_model=TokenResponse)
async def exchange_token(
    request: TokenExchangeRequest,
    session_id: str = Query("default", description="Session identifier"),
    redirect_uri: Optional[str] = Query(None, description="Redirect URI used in auth flow")
):
    """Exchange authorization code for access token.

    After the user authorizes at the authorization URL,
    they receive a code that should be submitted here.
    """
    uri = redirect_uri or get_redirect_uri()
    client = YahooClient(redirect_uri=uri)

    try:
        token = await client.exchange_code_for_token(request.authorization_code)
        _set_token(token, session_id)

        return TokenResponse(
            access_token=token.access_token[:20] + "...",  # Truncate for security
            token_type=token.token_type,
            expires_in=token.expires_in,
            authenticated=True,
        )
    except YahooAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/auth/set-token", response_model=TokenResponse)
async def set_token(
    request: SetTokenRequest,
    session_id: str = Query("default", description="Session identifier")
):
    """Set OAuth token directly (for tokens obtained externally).

    This endpoint allows setting a token that was obtained through
    another method (e.g., existing YFPY configuration).
    """
    expires_at = request.expires_at or (time.time() + request.expires_in)

    token = YahooToken(
        access_token=request.access_token,
        refresh_token=request.refresh_token,
        token_type=request.token_type,
        expires_in=request.expires_in,
        expires_at=expires_at,
    )
    _set_token(token, session_id)

    return TokenResponse(
        access_token=token.access_token[:20] + "...",
        token_type=token.token_type,
        expires_in=token.expires_in,
        authenticated=True,
    )


@router.get("/auth/status")
async def get_auth_status(
    session_id: str = Query("default", description="Session identifier")
):
    """Check authentication status."""
    token = _get_token(session_id)

    if not token:
        return {"authenticated": False, "message": "No token found"}

    if token.is_expired():
        return {"authenticated": False, "message": "Token expired"}

    return {
        "authenticated": True,
        "token_type": token.token_type,
        "expires_in": int(token.expires_at - time.time()),
    }


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    session_id: str = Query("default", description="Session identifier")
):
    """Refresh the access token."""
    token = _get_token(session_id)

    if not token:
        raise HTTPException(status_code=401, detail="No token to refresh")

    client = YahooClient()
    client.set_token(token)

    try:
        new_token = await client.refresh_access_token()
        _set_token(new_token, session_id)

        return TokenResponse(
            access_token=new_token.access_token[:20] + "...",
            token_type=new_token.token_type,
            expires_in=new_token.expires_in,
            authenticated=True,
        )
    except YahooAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.delete("/auth/logout")
async def logout(
    session_id: str = Query("default", description="Session identifier")
):
    """Clear the stored token (logout)."""
    _delete_token(session_id)
    return {"message": "Logged out successfully"}


# ============= League Data Routes =============

@router.get("/leagues", response_model=List[UserLeagueResponse])
async def get_user_leagues(
    game_key: Optional[str] = Query(None, description="Game key for specific season"),
    session_id: str = Query("default", description="Session identifier")
):
    """Get all leagues for the authenticated user."""
    logger.info(f"Fetching user leagues for session_id={session_id}, game_key={game_key}")

    try:
        client = get_authenticated_client(session_id)
    except HTTPException as e:
        logger.warning(f"Authentication failed for get_user_leagues: {e.detail}")
        raise

    try:
        leagues = await client.get_user_leagues(game_key)
        logger.info(f"Found {len(leagues)} leagues for user")

        return [
            UserLeagueResponse(
                league_key=league.get("league_key", ""),
                name=league.get("name", "Unknown"),
                season=league.get("season", ""),
                num_teams=league.get("num_teams", 0),
                scoring_type=league.get("scoring_type", ""),
                is_finished=league.get("is_finished", False),
            )
            for league in leagues
        ]
    except YahooAPIError as e:
        logger.error(f"Yahoo API error fetching leagues: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch leagues from Yahoo: {str(e)}"
        )
    except YahooAuthError as e:
        logger.error(f"Yahoo auth error fetching leagues: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication error: {str(e)}. Please login to Yahoo again."
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching leagues: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}. Check server logs for details."
        )


@router.get("/league/{league_key:path}", response_model=LeagueInfoResponse)
async def get_league_info(
    league_key: str,
    session_id: str = Query("default", description="Session identifier")
):
    """Fetch league information from Yahoo API (without storing)."""
    client = get_authenticated_client(session_id)

    try:
        data = await client.get_league(league_key)

        return LeagueInfoResponse(
            league_key=data.get("league_key", league_key),
            league_id=data.get("league_id", ""),
            name=data.get("name", "Unknown"),
            num_teams=data.get("num_teams", 0),
            scoring_type=data.get("scoring_type", ""),
            season=data.get("season", ""),
            current_week=data.get("current_week", 1),
            is_finished=data.get("is_finished", False),
        )
    except YahooAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except YahooAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/league/{league_key:path}/standings", response_model=List[TeamStandingResponse])
async def get_league_standings(
    league_key: str,
    session_id: str = Query("default", description="Session identifier")
):
    """Fetch standings for a Yahoo league (without storing)."""
    client = get_authenticated_client(session_id)

    try:
        standings = await client.get_standings(league_key)

        return [
            TeamStandingResponse(
                team_key=team.get("team_key", ""),
                team_id=team.get("team_id", ""),
                name=team.get("name", ""),
                manager_name=team.get("manager", {}).get("nickname"),
                wins=team.get("wins", 0),
                losses=team.get("losses", 0),
                ties=team.get("ties", 0),
                points_for=team.get("points_for", 0.0),
                points_against=team.get("points_against", 0.0),
                rank=team.get("rank", 0),
            )
            for team in standings
        ]
    except YahooAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except YahooAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/league/{league_key:path}/matchups", response_model=List[MatchupResponse])
async def get_league_matchups(
    league_key: str,
    week: Optional[int] = Query(None, description="Specific week number"),
    session_id: str = Query("default", description="Session identifier")
):
    """Fetch matchups for a Yahoo league (without storing)."""
    client = get_authenticated_client(session_id)

    try:
        matchups = await client.get_matchups(league_key, week)

        return [
            MatchupResponse(
                week=m.get("week", 0),
                is_playoffs=m.get("is_playoffs", False),
                is_consolation=m.get("is_consolation", False),
                teams=[
                    MatchupTeamResponse(
                        team_key=t.get("team_key", ""),
                        name=t.get("name", ""),
                        points=t.get("points", 0.0),
                    )
                    for t in m.get("teams", [])
                ],
                winner_team_key=m.get("winner_team_key"),
                is_tied=m.get("is_tied", False),
            )
            for m in matchups
        ]
    except YahooAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except YahooAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/league/{league_key:path}/trades", response_model=List[TradeResponse])
async def get_league_trades(
    league_key: str,
    session_id: str = Query("default", description="Session identifier")
):
    """Fetch trades for a Yahoo league (without storing)."""
    client = get_authenticated_client(session_id)

    try:
        trades = await client.get_trades(league_key)

        return [
            TradeResponse(
                transaction_id=t.get("transaction_id", ""),
                status=t.get("status", ""),
                timestamp=t.get("timestamp", 0),
                trader_team_key=t.get("trader_team_key", ""),
                tradee_team_key=t.get("tradee_team_key", ""),
                players=[
                    TradePlayerResponse(
                        player_key=p.get("player_key", ""),
                        name=p.get("name", ""),
                        source_team_key=p.get("source_team_key", ""),
                        destination_team_key=p.get("destination_team_key", ""),
                    )
                    for p in t.get("players", [])
                ],
            )
            for t in trades
        ]
    except YahooAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except YahooAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ============= Database Import Routes =============

@router.post("/import", response_model=ImportLeagueResponse)
async def import_league(
    request: ImportLeagueRequest,
    db: Session = Depends(get_db),
    session_id: str = Query("default", description="Session identifier")
):
    """Import all data for a Yahoo league into the database.

    This endpoint fetches and stores:
    - League information
    - Standings (teams and owners)
    - All matchups for the season
    - All trades for the season
    - Champion detection for completed seasons
    """
    logger.info(f"Starting Yahoo import for league_key={request.league_key}, session_id={session_id}")

    # Validate league key format
    if not validate_league_key(request.league_key):
        logger.warning(f"Invalid league key format: {request.league_key}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid league key format: '{request.league_key}'. Expected format: '449.l.123456' (game_key.l.league_id)"
        )

    # Get authenticated client (may raise 401)
    try:
        client = get_authenticated_client(session_id)
        logger.info(f"Successfully authenticated for session_id={session_id}")
    except HTTPException:
        logger.warning(f"Authentication failed for session_id={session_id}")
        raise

    try:
        service = YahooService(db, client)
        result = await service.import_full_league_with_champion(
            request.league_key,
            request.start_week,
            request.end_week,
        )
        logger.info(f"Successfully imported league: {result.get('league_name', 'Unknown')}")
        return ImportLeagueResponse(**result)

    except YahooAPIError as e:
        logger.error(f"Yahoo API error during import: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=400,
            detail=f"Yahoo API error: {str(e)}. Check that you have access to this league."
        )

    except YahooAuthError as e:
        logger.error(f"Yahoo authentication error during import: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication error: {str(e)}. Please try logging in to Yahoo again."
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error during import: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error while saving league data. Please try again."
        )

    except Exception as e:
        logger.error(f"Unexpected error during Yahoo import: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}. Check server logs for details."
        )


@router.post("/import/all", response_model=ImportHistoricalResponse)
async def import_all_leagues(
    request: Optional[ImportHistoricalRequest] = None,
    db: Session = Depends(get_db),
    session_id: str = Query("default", description="Session identifier")
):
    """Import all leagues from the user's Yahoo Fantasy history.

    This endpoint fetches leagues from multiple NFL seasons and imports:
    - All leagues the user has access to
    - Standings (teams and owners) for each league
    - All matchups for each season
    - All trades for each season
    - Champion detection for completed seasons

    By default, imports leagues from the past 6 seasons (2024-2019).
    Pass custom game_keys to import from specific seasons.
    """
    logger.info(f"Starting historical Yahoo import for session_id={session_id}")

    try:
        client = get_authenticated_client(session_id)
    except HTTPException:
        logger.warning(f"Authentication failed for session_id={session_id}")
        raise

    try:
        service = YahooService(db, client)
        game_keys = request.game_keys if request else None
        results = await service.import_historical_leagues(game_keys)

        # Count successful imports
        leagues_imported = sum(1 for r in results if "league_id" in r)
        seasons_imported = leagues_imported  # Each league is one season in Yahoo

        logger.info(f"Successfully imported {leagues_imported} leagues")
        return ImportHistoricalResponse(
            leagues_imported=leagues_imported,
            seasons_imported=seasons_imported,
            results=results,
        )

    except YahooAPIError as e:
        logger.error(f"Yahoo API error during historical import: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=400,
            detail=f"Yahoo API error: {str(e)}. Check your Yahoo connection."
        )

    except YahooAuthError as e:
        logger.error(f"Yahoo authentication error during historical import: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication error: {str(e)}. Please try logging in to Yahoo again."
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error during historical import: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error while saving league data. Please try again."
        )

    except Exception as e:
        logger.error(f"Unexpected error during historical Yahoo import: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}. Check server logs for details."
        )
