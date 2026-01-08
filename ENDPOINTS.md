# Fantasy League History API Documentation

This document describes all available API endpoints for the Fantasy League History Tracker.

## Table of Contents

- [Sleeper API](#sleeper-api)
- [Yahoo Fantasy API](#yahoo-fantasy-api)
- [Owners API](#owners-api)
- [History API](#history-api)
- [Trades API](#trades-api)
- [Records API](#records-api)
- [Hall of Fame API](#hall-of-fame-api)
- [Seasons API](#seasons-api)
- [Leagues API](#leagues-api)

---

## Sleeper API

Base path: `/api/sleeper`

Import and fetch data from Sleeper fantasy football leagues.

### POST /api/sleeper/import

Import all data for a Sleeper league into the database.

**Request Body:**
```json
{
  "league_id": "123456789"
}
```

**Response:**
```json
{
  "league_id": 1,
  "league_name": "My Sleeper League",
  "seasons_imported": 3,
  "seasons": [
    {
      "season_year": 2024,
      "teams_imported": 12,
      "matchups_imported": 156,
      "trades_imported": 8,
      "champion_team_id": 5,
      "runner_up_team_id": 3
    }
  ],
  "teams_imported": 36,
  "matchups_imported": 468,
  "trades_imported": 24
}
```

### GET /api/sleeper/league/{league_id}

Fetch league information from Sleeper API (without storing).

**Response:**
```json
{
  "league_id": "123456789",
  "name": "My Sleeper League",
  "season": "2024",
  "total_rosters": 12,
  "status": "complete",
  "scoring_type": "PPR"
}
```

### GET /api/sleeper/league/{league_id}/users

Fetch all users in a Sleeper league (without storing).

**Response:**
```json
[
  {
    "user_id": "abc123",
    "username": "player1",
    "display_name": "John Doe",
    "avatar_url": "https://sleepercdn.com/avatars/..."
  }
]
```

### GET /api/sleeper/league/{league_id}/rosters

Fetch all rosters in a Sleeper league (without storing).

**Response:**
```json
[
  {
    "roster_id": 1,
    "owner_id": "abc123",
    "wins": 10,
    "losses": 4,
    "ties": 0,
    "points_for": 1523.45
  }
]
```

### GET /api/sleeper/league/{league_id}/matchups/{week}

Fetch matchups for a specific week (without storing).

**Response:**
```json
[
  {
    "matchup_id": 1,
    "roster_id": 1,
    "points": 125.5
  }
]
```

### GET /api/sleeper/league/{league_id}/trades/{week}

Fetch trades for a specific week (without storing).

**Response:**
```json
[
  {
    "transaction_id": "trans123",
    "roster_ids": [1, 3],
    "week": 5,
    "status": "complete",
    "adds": {"1234": 1},
    "drops": {"5678": 3}
  }
]
```

---

## Yahoo Fantasy API

Base path: `/api/yahoo`

OAuth2 authentication and data import for Yahoo Fantasy Football leagues.

### Authentication Endpoints

#### GET /api/yahoo/auth/url

Get the OAuth2 authorization URL for user consent.

**Query Parameters:**
- `state` (optional): CSRF protection state parameter
- `redirect_uri` (optional): Custom redirect URI

**Response:**
```json
{
  "authorization_url": "https://api.login.yahoo.com/oauth2/...",
  "state": "csrf_token"
}
```

#### GET /api/yahoo/auth/callback

OAuth2 callback endpoint for browser redirect flow. Redirects to frontend after authentication.

**Query Parameters:**
- `code` (required): Authorization code from Yahoo
- `state` (optional): State parameter for CSRF validation
- `session_id` (optional): Session identifier (default: "default")

#### POST /api/yahoo/auth/token

Exchange authorization code for access token.

**Request Body:**
```json
{
  "authorization_code": "auth_code_here",
  "state": "optional_state"
}
```

**Response:**
```json
{
  "access_token": "abcd1234567890...",
  "token_type": "bearer",
  "expires_in": 3600,
  "authenticated": true
}
```

#### POST /api/yahoo/auth/set-token

Set OAuth token directly (for tokens obtained externally).

**Request Body:**
```json
{
  "access_token": "access_token_here",
  "refresh_token": "refresh_token_here",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### GET /api/yahoo/auth/status

Check authentication status.

**Response (authenticated):**
```json
{
  "authenticated": true,
  "token_type": "bearer",
  "expires_in": 2500
}
```

**Response (not authenticated):**
```json
{
  "authenticated": false,
  "message": "No token found"
}
```

#### POST /api/yahoo/auth/refresh

Refresh the access token.

**Response:**
```json
{
  "access_token": "new_access_token...",
  "token_type": "bearer",
  "expires_in": 3600,
  "authenticated": true
}
```

#### DELETE /api/yahoo/auth/logout

Clear the stored token (logout).

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

### League Data Endpoints

#### GET /api/yahoo/leagues

Get all leagues for the authenticated user.

**Query Parameters:**
- `game_key` (optional): Game key for specific season (e.g., "449" for 2024)
- `session_id` (optional): Session identifier

**Response:**
```json
[
  {
    "league_key": "449.l.12345",
    "name": "My Yahoo League",
    "season": "2024",
    "num_teams": 12,
    "scoring_type": "head",
    "is_finished": true
  }
]
```

#### GET /api/yahoo/league/{league_key}

Fetch league information from Yahoo API (without storing).

**Response:**
```json
{
  "league_key": "449.l.12345",
  "league_id": "12345",
  "name": "My Yahoo League",
  "num_teams": 12,
  "scoring_type": "head",
  "season": "2024",
  "current_week": 17,
  "is_finished": true
}
```

#### GET /api/yahoo/league/{league_key}/standings

Fetch standings for a Yahoo league (without storing).

**Response:**
```json
[
  {
    "team_key": "449.l.12345.t.1",
    "team_id": "1",
    "name": "Team Name",
    "manager_name": "John",
    "wins": 11,
    "losses": 3,
    "ties": 0,
    "points_for": 1625.50,
    "points_against": 1420.25,
    "rank": 1
  }
]
```

#### GET /api/yahoo/league/{league_key}/matchups

Fetch matchups for a Yahoo league (without storing).

**Query Parameters:**
- `week` (optional): Specific week number

**Response:**
```json
[
  {
    "week": 1,
    "is_playoffs": false,
    "is_consolation": false,
    "teams": [
      {"team_key": "449.l.12345.t.1", "name": "Team A", "points": 125.5},
      {"team_key": "449.l.12345.t.2", "name": "Team B", "points": 110.3}
    ],
    "winner_team_key": "449.l.12345.t.1",
    "is_tied": false
  }
]
```

#### GET /api/yahoo/league/{league_key}/trades

Fetch trades for a Yahoo league (without storing).

**Response:**
```json
[
  {
    "transaction_id": "trans123",
    "status": "successful",
    "timestamp": 1699900000,
    "trader_team_key": "449.l.12345.t.1",
    "tradee_team_key": "449.l.12345.t.2",
    "players": [
      {
        "player_key": "449.p.1234",
        "name": "Patrick Mahomes",
        "source_team_key": "449.l.12345.t.1",
        "destination_team_key": "449.l.12345.t.2"
      }
    ]
  }
]
```

### Import Endpoints

#### POST /api/yahoo/import

Import all data for a Yahoo league into the database.

**Request Body:**
```json
{
  "league_key": "449.l.12345",
  "start_week": 1,
  "end_week": 17
}
```

**Response:**
```json
{
  "league_id": 1,
  "league_name": "My Yahoo League",
  "season_year": 2024,
  "teams_imported": 12,
  "matchups_imported": 156,
  "trades_imported": 5,
  "champion_team_id": 3,
  "champion_name": "John Doe"
}
```

#### POST /api/yahoo/import/all

Import all leagues from the user's Yahoo Fantasy history.

**Request Body (optional):**
```json
{
  "game_keys": ["449", "423", "406"]
}
```

**Response:**
```json
{
  "leagues_imported": 3,
  "seasons_imported": 3,
  "results": [
    {"league_id": 1, "league_name": "League 2024", "season_year": 2024},
    {"league_id": 2, "league_name": "League 2023", "season_year": 2023}
  ]
}
```

---

## Owners API

Base path: `/api/owners`

Manage fantasy league owners and cross-platform mappings.

### GET /api/owners

List all owners in the system.

**Response:**
```json
[
  {
    "id": 1,
    "name": "John Doe",
    "display_name": "Johnny",
    "avatar_url": "https://...",
    "sleeper_user_id": "abc123",
    "yahoo_user_id": "xyz789"
  }
]
```

### GET /api/owners/unmapped

Get owners that are not mapped to both platforms.

**Response:**
```json
[
  {
    "id": 2,
    "name": "Jane Smith",
    "display_name": null,
    "avatar_url": null,
    "sleeper_user_id": "def456",
    "yahoo_user_id": null
  }
]
```

### GET /api/owners/{owner_id}

Get a specific owner by ID.

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "display_name": "Johnny",
  "avatar_url": "https://...",
  "sleeper_user_id": "abc123",
  "yahoo_user_id": "xyz789"
}
```

### GET /api/owners/{owner_id}/stats

Get aggregated career statistics for an owner.

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "total_wins": 85,
  "total_losses": 42,
  "total_ties": 1,
  "total_points": 12500.75,
  "seasons_played": 8,
  "playoff_appearances": 6,
  "championships": 2,
  "avg_regular_season_rank": 3.5
}
```

### POST /api/owners/mapping

Create a new owner with platform mappings.

**Request Body:**
```json
{
  "name": "John Doe",
  "display_name": "Johnny",
  "avatar_url": "https://...",
  "sleeper_user_id": "abc123",
  "yahoo_user_id": "xyz789"
}
```

**Response:** Returns the created owner object.

### PUT /api/owners/{owner_id}/mapping

Update platform mappings for an existing owner.

**Request Body:**
```json
{
  "sleeper_user_id": "new_sleeper_id",
  "yahoo_user_id": "new_yahoo_id",
  "display_name": "New Display Name",
  "avatar_url": "https://new-avatar.png"
}
```

**Response:** Returns the updated owner object.

### DELETE /api/owners/{owner_id}/mapping/{platform}

Unlink a platform from an owner.

**Path Parameters:**
- `owner_id`: The database ID of the owner
- `platform`: Either "sleeper" or "yahoo"

**Response:** Returns the updated owner object.

### POST /api/owners/merge

Merge two owners into one.

**Request Body:**
```json
{
  "primary_owner_id": 1,
  "secondary_owner_id": 2
}
```

**Response:** Returns the merged primary owner object.

---

## History API

Base path: `/api/history`

Career statistics and historical data across all seasons.

### GET /api/history/owners

List all owners with their career statistics.

**Response:**
```json
[
  {
    "id": 1,
    "name": "John Doe",
    "display_name": "Johnny",
    "avatar_url": "https://...",
    "total_wins": 85,
    "total_losses": 42,
    "total_ties": 1,
    "total_points": 12500.75,
    "seasons_played": 8,
    "playoff_appearances": 6,
    "championships": 2,
    "win_percentage": 66.41
  }
]
```

### GET /api/history/owners/{owner_id}

Get full history for a specific owner.

**Response:**
```json
{
  "owner": {
    "id": 1,
    "name": "John Doe",
    "display_name": "Johnny",
    "avatar_url": "https://..."
  },
  "career_stats": {
    "total_wins": 85,
    "total_losses": 42,
    "total_ties": 1,
    "total_points": 12500.75,
    "seasons_played": 8,
    "playoff_appearances": 6,
    "championships": 2,
    "win_percentage": 66.41,
    "matchups_won": 85,
    "matchups_lost": 42,
    "matchups_tied": 1,
    "avg_points_per_season": 1562.59
  },
  "seasons": [
    {
      "year": 2024,
      "league_name": "My League",
      "team_name": "John's Team",
      "wins": 12,
      "losses": 2,
      "ties": 0,
      "points_for": 1650.25,
      "regular_season_rank": 1,
      "final_rank": 1,
      "made_playoffs": true,
      "is_champion": true
    }
  ]
}
```

### GET /api/history/seasons

List all seasons with their champions.

**Query Parameters:**
- `league_id` (optional): Filter by league ID

**Response:**
```json
[
  {
    "id": 1,
    "year": 2024,
    "league_id": 1,
    "league_name": "My League",
    "platform": "sleeper",
    "is_complete": true,
    "champion": {"id": 1, "name": "John Doe"},
    "runner_up": {"id": 2, "name": "Jane Smith"},
    "team_count": 12
  }
]
```

### GET /api/history/head-to-head/{owner1_id}/{owner2_id}

Get head-to-head rivalry statistics between two owners.

**Response:**
```json
{
  "owner1": {"id": 1, "name": "John Doe", "display_name": null, "avatar_url": null},
  "owner2": {"id": 2, "name": "Jane Smith", "display_name": null, "avatar_url": null},
  "total_matchups": 24,
  "owner1_wins": 14,
  "owner2_wins": 9,
  "ties": 1,
  "owner1_avg_score": 118.5,
  "owner2_avg_score": 112.3,
  "playoff_matchups": 3,
  "owner1_playoff_wins": 2,
  "owner2_playoff_wins": 1,
  "matchups": [
    {
      "year": 2024,
      "week": 5,
      "owner1_score": 125.5,
      "owner2_score": 118.2,
      "winner_id": 1,
      "is_playoff": false,
      "is_championship": false
    }
  ]
}
```

---

## Trades API

Base path: `/api/trades`

Trade analytics and history.

### GET /api/trades

List all trades with optional filters.

**Query Parameters:**
- `owner_id` (optional): Filter by owner ID
- `season_id` (optional): Filter by season ID
- `league_id` (optional): Filter by league ID
- `limit` (optional): Max results per page (default: 50, max: 100)
- `offset` (optional): Number of results to skip (default: 0)

**Response:**
```json
{
  "trades": [
    {
      "id": 1,
      "week": 5,
      "trade_date": "2024-10-15",
      "season_id": 1,
      "season_year": 2024,
      "league_id": 1,
      "league_name": "My League",
      "assets_exchanged": "{...}",
      "trade_details": [
        {
          "team_id": 1,
          "owner_name": "John Doe",
          "received": ["Patrick Mahomes", "Travis Kelce"],
          "sent": ["Josh Allen"]
        }
      ],
      "trade_summary": "John Doe receives Patrick Mahomes, Travis Kelce",
      "status": "completed",
      "teams": [
        {"id": 1, "name": "Team 1", "owner": {"id": 1, "name": "John Doe"}}
      ]
    }
  ],
  "total": 45,
  "limit": 50,
  "offset": 0
}
```

### GET /api/trades/owners/{owner_id}

Get all trades for a specific owner with analytics.

**Response:**
```json
{
  "owner": {"id": 1, "name": "John Doe", "display_name": null, "avatar_url": null},
  "trades": [...],
  "total_trades": 15,
  "trade_frequency": {
    "trades_per_season": 1.88,
    "seasons_played": 8,
    "total_trades": 15
  },
  "trade_partners": [
    {"owner": {"id": 2, "name": "Jane Smith"}, "trade_count": 5}
  ],
  "win_rate_analysis": {
    "win_rate_before_trades": 55.0,
    "win_rate_after_trades": 68.0,
    "win_rate_change": 13.0,
    "games_before": 20,
    "games_after": 50,
    "wins_before": 11,
    "wins_after": 34
  }
}
```

### GET /api/trades/stats

Get overall trade statistics.

**Response:**
```json
{
  "total_trades": 125,
  "most_active_traders": [
    {"owner": {"id": 1, "name": "John Doe"}, "trade_count": 25}
  ],
  "trades_by_season": [
    {"season_id": 1, "year": 2024, "league_name": "My League", "trade_count": 15}
  ],
  "avg_trades_per_season": 12.5
}
```

---

## Records API

Base path: `/api/records`

League records and all-time statistics.

### GET /api/records

Get all league records.

**Response:**
```json
{
  "highest_single_week_score": {
    "score": 195.5,
    "owner_id": 1,
    "owner_name": "John Doe",
    "team_name": "John's Team",
    "year": 2023,
    "week": 12,
    "opponent_name": "Jane's Team"
  },
  "most_points_in_season": {
    "points": 1850.75,
    "owner_id": 1,
    "owner_name": "John Doe",
    "team_name": "John's Team",
    "year": 2024
  },
  "longest_win_streak": {
    "streak": 12,
    "owner_id": 2,
    "owner_name": "Jane Smith",
    "team_name": "Jane's Team",
    "year": 2022
  },
  "most_trades_in_season": {
    "trade_count": 8,
    "owner_id": 3,
    "owner_name": "Bob Johnson",
    "year": 2023
  },
  "top_weekly_scores": [...],
  "top_season_points": [...],
  "top_win_streaks": [...]
}
```

---

## Hall of Fame API

Base path: `/api/hall-of-fame`

Championship history and dynasty tracking.

### GET /api/hall-of-fame

Get complete Hall of Fame data.

**Response:**
```json
{
  "champions_by_year": [
    {
      "year": 2024,
      "league_id": 1,
      "league_name": "My League",
      "platform": "sleeper",
      "team_name": "Champion Team",
      "record": "12-2",
      "points_for": 1650.25,
      "champion": {
        "id": 1,
        "name": "John Doe",
        "display_name": "Johnny",
        "avatar_url": "https://..."
      },
      "runner_up": {
        "id": 2,
        "name": "Jane Smith"
      }
    }
  ],
  "championship_leaderboard": [
    {
      "owner": {"id": 1, "name": "John Doe"},
      "championships": 3,
      "years": [2024, 2022, 2020],
      "leagues": ["My League"]
    }
  ],
  "dynasties": [
    {
      "owner": {"id": 1, "name": "John Doe"},
      "streak": 2,
      "start_year": 2022,
      "end_year": 2023,
      "league_name": "My League"
    }
  ],
  "total_seasons": 8,
  "unique_champions": 5
}
```

### GET /api/hall-of-fame/leaderboard

Get just the championship leaderboard.

**Response:**
```json
[
  {
    "owner": {"id": 1, "name": "John Doe"},
    "championships": 3,
    "years": [2024, 2022, 2020],
    "leagues": ["My League"]
  }
]
```

---

## Seasons API

Base path: `/api/seasons`

Season details with standings, playoffs, and trades.

### GET /api/seasons

List all seasons with basic info.

**Query Parameters:**
- `league_id` (optional): Filter by league ID

**Response:**
```json
[
  {
    "id": 1,
    "year": 2024,
    "league_id": 1,
    "league_name": "My League",
    "platform": "SLEEPER",
    "is_complete": true,
    "team_count": 12,
    "champion_id": 1,
    "champion_name": "John Doe",
    "runner_up_id": 2,
    "runner_up_name": "Jane Smith"
  }
]
```

### GET /api/seasons/{season_id}

Get detailed view of a specific season.

**Response:**
```json
{
  "id": 1,
  "year": 2024,
  "league_id": 1,
  "league_name": "My League",
  "platform": "SLEEPER",
  "is_complete": true,
  "regular_season_weeks": 14,
  "playoff_weeks": 3,
  "playoff_team_count": 6,
  "team_count": 12,
  "champion": {"id": 1, "name": "John Doe", "display_name": null, "avatar_url": null},
  "runner_up": {"id": 2, "name": "Jane Smith"},
  "standings": [
    {
      "team_id": 1,
      "team_name": "Champion Team",
      "owner_id": 1,
      "owner_name": "John Doe",
      "owner_display_name": "Johnny",
      "owner_avatar_url": null,
      "wins": 12,
      "losses": 2,
      "ties": 0,
      "points_for": 1650.25,
      "points_against": 1420.50,
      "regular_season_rank": 1,
      "final_rank": 1,
      "made_playoffs": true
    }
  ],
  "playoff_bracket": [
    {
      "id": 100,
      "week": 15,
      "home_team_id": 1,
      "home_team_name": "Team A",
      "home_owner_id": 1,
      "home_owner_name": "John Doe",
      "away_team_id": 4,
      "away_team_name": "Team D",
      "away_owner_id": 4,
      "away_owner_name": "Bob",
      "home_score": 125.5,
      "away_score": 110.2,
      "winner_team_id": 1,
      "winner_owner_name": "John Doe",
      "is_championship": false,
      "is_consolation": false,
      "is_tie": false
    }
  ],
  "trades": [
    {
      "id": 5,
      "week": 8,
      "trade_date": "2024-10-20",
      "assets_exchanged": "{...}",
      "teams": [
        {"id": 1, "name": "Team A", "owner_id": 1, "owner_name": "John Doe"},
        {"id": 3, "name": "Team C", "owner_id": 3, "owner_name": "Jane"}
      ]
    }
  ]
}
```

---

## Leagues API

Base path: `/api/leagues`

Manage imported leagues.

### GET /api/leagues

Get all imported leagues with summary statistics.

**Response:**
```json
[
  {
    "id": 1,
    "name": "My League",
    "platform": "sleeper",
    "platform_league_id": "123456789",
    "team_count": 12,
    "scoring_type": "PPR",
    "created_at": "2024-01-15T10:30:00",
    "seasons_count": 5,
    "seasons": [
      {"id": 1, "year": 2024, "champion_name": "John Doe"},
      {"id": 2, "year": 2023, "champion_name": "Jane Smith"}
    ],
    "latest_season_year": 2024,
    "total_teams": 60,
    "total_matchups": 780,
    "total_trades": 45
  }
]
```

### GET /api/leagues/{league_id}

Get a specific league by ID with full details.

**Response:** Same structure as individual item in GET /api/leagues response.

### DELETE /api/leagues/{league_id}

Delete a league and all its associated data.

**Response:**
```json
{
  "success": true,
  "message": "Successfully deleted league \"My League\"",
  "deleted_seasons": 5,
  "deleted_teams": 60,
  "deleted_matchups": 780,
  "deleted_trades": 45
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

**400 Bad Request:**
```json
{
  "detail": "Error message describing the issue"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Not authenticated. Please complete OAuth flow first."
}
```

**404 Not Found:**
```json
{
  "detail": "Resource with ID {id} not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error message"
}
```

---

## Interactive API Documentation

When running the backend server, you can access interactive API documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
