# Ralph Agent Instructions

## Project Context
Building a Fantasy League History Tracker that unifies data from Yahoo Fantasy and Sleeper into one place with rich statistics and an eye-catching UI.

## Your Task

1. Read `scripts/ralph/prd.json` for the task list
2. Read `scripts/ralph/progress.txt` for learnings and patterns
3. Ensure you're on the correct branch (`ralph/fantasy-league-history`)
4. Pick the highest priority story where `passes: false`
5. Implement that ONE story completely
6. Verify the acceptance criteria are met
7. Commit with message: `feat: [ID] - [Title]`
8. Update prd.json: set `passes: true` for completed story
9. Append learnings to progress.txt

## Tech Stack
- Backend: Python with FastAPI
- Frontend: React with Vite and Tailwind CSS
- Database: SQLite with SQLAlchemy
- Charts: Recharts for visualizations

## Progress Format

APPEND to progress.txt after each story:
```
## [Date] - [Story ID]
- What was implemented
- Files changed
- **Learnings:**
  - Patterns discovered
  - Gotchas encountered
```

## Stop Condition

If ALL stories have `passes: true`, reply with:
<promise>COMPLETE</promise>

Otherwise, end normally after completing one story.

---

## Completed Stories

### FLH-002: Create SQLite database schema ✅
**Completed:** 2025-01-07

**Implementation:**
- Created SQLAlchemy models: Owner, League, Season, Team, Matchup, Trade
- Owner model supports cross-platform mapping with unique yahoo_user_id and sleeper_user_id
- Platform enum (YAHOO, SLEEPER) for league platform identification
- Trade-Team many-to-many relationship via association table
- Database initializes automatically on app startup via FastAPI lifespan handler

**Files Created:**
- `backend/app/db/__init__.py` - Module exports
- `backend/app/db/database.py` - Engine, session factory, init_db()
- `backend/app/db/models.py` - All 6 data models
- `backend/tests/__init__.py` - Test module
- `backend/tests/conftest.py` - Pytest fixtures
- `backend/tests/test_models.py` - 14 comprehensive tests

**Tests:** All 14 tests passing


### FLH-003: Build Sleeper API integration ✅
**Completed:** 2025-01-07

**Implementation:**
- Created SleeperClient HTTP client for Sleeper API (no auth required)
- Created SleeperService for importing data to database
- Added FastAPI routes under /api/sleeper prefix
- Full import pipeline: league -> season -> users/rosters -> matchups -> trades

**Files Created:**
- `backend/app/services/__init__.py` - Services module exports
- `backend/app/services/sleeper_client.py` - HTTP client for Sleeper API
- `backend/app/services/sleeper_service.py` - Database import service
- `backend/app/api/sleeper.py` - FastAPI routes
- `backend/tests/test_sleeper.py` - 24 comprehensive tests

**API Endpoints:**
- POST `/api/sleeper/import` - Import full league data to database
- GET `/api/sleeper/league/{id}` - Fetch league info
- GET `/api/sleeper/league/{id}/users` - Fetch users
- GET `/api/sleeper/league/{id}/rosters` - Fetch rosters
- GET `/api/sleeper/league/{id}/matchups/{week}` - Fetch matchups
- GET `/api/sleeper/league/{id}/trades/{week}` - Fetch trades

**Tests:** All 38 tests passing (14 models + 24 sleeper)


### FLH-004: Build Yahoo Fantasy API integration ✅
**Completed:** 2025-01-07

**Implementation:**
- Created YahooClient HTTP client with full OAuth2 authentication support
- Created YahooService for importing data to database
- Added FastAPI routes under /api/yahoo prefix
- Full import pipeline: oauth -> league -> standings -> matchups -> trades

**Files Created:**
- `backend/app/services/yahoo_client.py` - HTTP client with OAuth2 for Yahoo API
- `backend/app/services/yahoo_service.py` - Database import service
- `backend/app/api/yahoo.py` - FastAPI routes

**API Endpoints:**
- GET `/api/yahoo/auth/url` - Get OAuth2 authorization URL
- POST `/api/yahoo/auth/token` - Exchange code for access token
- POST `/api/yahoo/auth/set-token` - Set token directly
- GET `/api/yahoo/auth/status` - Check authentication status
- POST `/api/yahoo/auth/refresh` - Refresh access token
- DELETE `/api/yahoo/auth/logout` - Clear stored token
- GET `/api/yahoo/leagues` - Get user's leagues
- GET `/api/yahoo/league/{key}` - Fetch league info
- GET `/api/yahoo/league/{key}/standings` - Fetch standings
- GET `/api/yahoo/league/{key}/matchups` - Fetch matchups
- GET `/api/yahoo/league/{key}/trades` - Fetch trades
- POST `/api/yahoo/import` - Import full league data to database

**Tests:** All 66 tests passing (14 models + 24 sleeper + 28 yahoo)


### FLH-005: Create owner mapping system ✅
**Completed:** 2025-01-08

**Implementation:**
- Created owner mapping API with full CRUD operations
- UI component for linking Yahoo and Sleeper users as same owner
- Merge functionality to combine two separate owner records
- Stats aggregation across platforms via GET /api/owners/{id}/stats

**Files Created:**
- `backend/app/api/owners.py` - Owner mapping API endpoints
- `backend/tests/test_owners.py` - 19 comprehensive tests
- `frontend/src/types/owner.ts` - TypeScript types
- `frontend/src/api/owners.ts` - API client
- `frontend/src/components/OwnerMapping.tsx` - Main UI component

**API Endpoints:**
- GET `/api/owners` - List all owners
- GET `/api/owners/unmapped` - Get owners not mapped to both platforms
- GET `/api/owners/{id}` - Get owner by ID
- GET `/api/owners/{id}/stats` - Get aggregated career stats
- POST `/api/owners/mapping` - Create new owner with mappings
- PUT `/api/owners/{id}/mapping` - Update owner mappings
- POST `/api/owners/merge` - Merge two owners
- DELETE `/api/owners/{id}/mapping/{platform}` - Unlink a platform

**Tests:** All 85 tests passing (14 models + 24 sleeper + 28 yahoo + 19 owners)


### FLH-006: Build league history API endpoints ✅
**Completed:** 2025-01-08

**Implementation:**
- Created league history API with comprehensive endpoints
- Career stats aggregation across all seasons and platforms
- Full owner history with season-by-season breakdown
- Head-to-head rivalry statistics with matchup history

**Files Created:**
- `backend/app/api/history.py` - League history API endpoints
- `backend/tests/test_history.py` - 16 comprehensive tests

**API Endpoints:**
- GET `/api/history/owners` - List all owners with career stats (sorted by wins)
- GET `/api/history/owners/{id}` - Full history for one owner with season breakdown
- GET `/api/history/seasons` - List all seasons with champions (filterable by league)
- GET `/api/history/head-to-head/{owner1}/{owner2}` - Rivalry stats between two owners

**Features:**
- Win percentage calculations
- Playoff and championship tracking
- Cross-season head-to-head aggregation
- Average scores in matchups
- Matchup detail history

**Tests:** All 101 tests passing (14 models + 24 sleeper + 28 yahoo + 19 owners + 16 history)


### FLH-007: Build trade analytics API ✅
**Completed:** 2025-01-08

**Implementation:**
- Created trade analytics API with comprehensive endpoints
- Trade filtering by owner, season, and league with pagination
- Full trade analytics per owner: frequency, partners, win rate analysis
- Overall trade statistics including most active traders

**Files Created:**
- `backend/app/api/trades.py` - Trade analytics API endpoints
- `backend/tests/test_trades.py` - 17 comprehensive tests

**API Endpoints:**
- GET `/api/trades` - List all trades with filters (owner_id, season_id, league_id) and pagination
- GET `/api/trades/owners/{id}` - Get all trades for an owner with full analytics
- GET `/api/trades/stats` - Overall trade statistics

**Analytics Features:**
- Trade frequency per owner (trades per season calculation)
- Most common trade partners (sorted by trade count)
- Win rate before/after first trade analysis
- Trade counts by season and overall statistics
- Most active traders leaderboard

**Tests:** All 118 tests passing (14 models + 24 sleeper + 28 yahoo + 19 owners + 16 history + 17 trades)


### FLH-008: Create frontend dashboard layout ✅
**Completed:** 2025-01-08

**Implementation:**
- Created 4-tab navigation: Dashboard, Owners, Seasons, Trades
- Responsive design with mobile bottom navigation and hamburger menu
- Dark mode toggle with localStorage persistence (default: dark)
- League branding with trophy icon and configurable league name

**Files Created:**
- `frontend/src/pages/Dashboard.tsx` - Landing page with quick stats
- `frontend/src/pages/Owners.tsx` - Owner stats table
- `frontend/src/pages/Seasons.tsx` - Season list with champions
- `frontend/src/pages/Trades.tsx` - Trade list with analytics

**Files Modified:**
- `frontend/src/App.tsx` - New tabbed layout with dark mode
- `frontend/src/index.css` - Dark/light mode CSS support
- `frontend/index.html` - Updated page title

**Features:**
- Desktop horizontal tabs with icons
- Mobile bottom navigation bar
- Mobile hamburger menu dropdown
- Dark mode toggle (sun/moon icons)
- Sticky header with backdrop blur
- Dashboard quick stats cards
- Getting started guide for new users

**Acceptance Criteria Met:**
- ✅ Navigation with tabs: Dashboard, Owners, Seasons, Trades
- ✅ Responsive design works on mobile
- ✅ Dark mode support with persistence
- ✅ League branding/name displayed

**Tests:** Frontend builds successfully, all 118 backend tests passing


### FLH-009: Build owner profile cards ✅
**Completed:** 2025-01-08

**Implementation:**
- Created OwnerProfileCard component with visually appealing design
- Gradient avatars generated from owner name (or custom avatar if provided)
- Card/list view toggle on Owners page
- Responsive 4-column grid layout

**Files Created:**
- `frontend/src/components/OwnerProfileCard.tsx` - Profile card component

**Files Modified:**
- `frontend/src/pages/Owners.tsx` - Added card/list view toggle
- `frontend/src/types/owner.ts` - Added OwnerWithStats type

**Features:**
- Gradient avatars with owner initial (8 color combinations)
- Career record (W-L-T) prominently displayed
- Championships with trophy icons and "CHAMP" banner ribbon
- Playoff appearances and seasons played
- Win percentage display
- Rank badges (gold/silver/bronze for top 3)
- Hover effects with scale and shadow transitions

**Acceptance Criteria Met:**
- ✅ Display owner name and avatar
- ✅ Show career record (W-L)
- ✅ Show championships count
- ✅ Show playoff appearances
- ✅ Visually appealing card design

**Tests:** Frontend builds successfully, all 118 backend tests passing


### FLH-010: Build head-to-head rivalry view ✅
**Completed:** 2025-01-09

**Implementation:**
- Created HeadToHead page component with owner selection dropdowns
- Utilizes existing `/api/history/head-to-head/{owner1}/{owner2}` API endpoint
- Added "Rivalries" tab to main navigation
- Full rivalry comparison with historical matchup list

**Files Created:**
- `frontend/src/pages/HeadToHead.tsx` - Main rivalry comparison page

**Files Modified:**
- `frontend/src/types/owner.ts` - Added OwnerBrief, MatchupDetail, HeadToHeadResponse types
- `frontend/src/App.tsx` - Added Rivalries tab to navigation

**Features:**
- Owner selection dropdowns with swap button
- Owner comparison cards showing wins and average scores
- "LEADING" badge for owner with more wins
- Summary stats: total matchups, ties, playoff matchups, playoff record
- Historical matchup list with scrollable container (max-h-96)
- Playoff matchups highlighted with purple styling
- Championship matchups highlighted with gold styling and trophy icon
- Winner/Loser (W/L) indicators on each matchup row
- Responsive design for mobile and desktop

**Acceptance Criteria Met:**
- ✅ Select two owners to compare
- ✅ Show all-time record between them
- ✅ Show average score in matchups
- ✅ List all historical matchups
- ✅ Highlight playoff matchups

**Tests:** Frontend builds successfully, all 118 backend tests passing
