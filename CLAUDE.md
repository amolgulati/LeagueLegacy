# Fantasy League History Tracker

## Project Structure

```
fantasy-league-history/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes (sleeper, yahoo, owners, history, trades, records, etc.)
│   │   ├── services/          # Service layer (sleeper_client, sleeper_service, player_cache, etc.)
│   │   ├── db/                # Database layer (models, database config)
│   │   └── main.py            # FastAPI application entry point
│   ├── tests/                 # Test suite (204 tests)
│   └── requirements.txt       # Python dependencies
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── pages/             # Page components (Dashboard, Owners, Seasons, Trades, etc.)
│   │   ├── components/        # Reusable components (ErrorBoundary, ImportModal, etc.)
│   │   ├── api/               # API client functions
│   │   ├── types/             # TypeScript types
│   │   ├── hooks/             # Custom React hooks
│   │   └── App.tsx            # Main React component
│   └── package.json           # NPM configuration
├── scripts/ralph/             # Ralph orchestrator files
│   ├── progress.txt           # Progress tracking log
│   └── prd.json               # Product requirements
├── fantasy_league.db          # SQLite database
├── PROMPT.md                  # Ralph task instructions
├── HISTORY.md                 # Completed story documentation
├── ENDPOINTS.md               # API documentation
└── README.md                  # Getting started guide
```

## Commands

```bash
# Backend
cd backend && uvicorn app.main:app --reload    # Start backend dev server (port 8000)
cd backend && pytest                            # Run all tests
cd backend && pytest -v                         # Run tests with verbose output

# Frontend
cd frontend && npm install                      # Install dependencies
cd frontend && npm run dev                      # Start dev server (port 5173)
cd frontend && npm run build                    # Production build
cd frontend && npm run lint                     # Run ESLint
```

## Tech Stack

**Backend:**
- FastAPI 0.115.0 - Web framework
- SQLAlchemy 2.0.25 - ORM
- Pydantic 2.5.3 - Data validation
- httpx 0.27.0 - HTTP client (for API calls)
- pytest 8.0.0+ - Testing framework

**Frontend:**
- React 19.2.0 - UI framework
- Vite 7.2.4 - Build tool
- TypeScript 5.9.3 - Type safety
- Tailwind CSS 3.4.19 - Styling
- Recharts 3.6.0 - Charts

**Database:**
- SQLite with SQLAlchemy ORM
- 8 models: Owner, League, Season, Team, Matchup, Trade, Roster, Player

## Common Gotchas

1. **Sleeper vs Yahoo Auth**: Sleeper API is completely unauthenticated. Yahoo requires OAuth2 with tokens stored in `~/.fantasy-league-history/yahoo_tokens.json`.

2. **PlayerCache Singleton**: The `PlayerCache` class caches Sleeper player data to avoid repeated API calls. Default TTL is 24 hours. Cache file at `~/.fantasy-league-history/sleeper_players.json`.

3. **Owner Mapping**: Owners can have both `sleeper_user_id` and `yahoo_user_id`. The owner mapping system links identities across platforms to a single Owner record.

4. **CORS Configuration**: CORS origins read from `CORS_ORIGINS` env var (comma-separated). Defaults to `http://localhost:5173`.

5. **Backend Tests**: Use pytest fixtures with in-memory SQLite database. See `backend/tests/conftest.py` for fixtures.

6. **React Error Boundaries**: Must use class components - React hooks cannot catch render errors. See `frontend/src/components/ErrorBoundary.tsx`.

7. **Skeleton Loaders**: Use `animationDelay` for staggered entrance effects. Background colors should match content for smooth transitions.

8. **Environment Files**: Copy `.env.example` to `.env` in both backend and frontend directories. Required for Yahoo OAuth.

## API Documentation

- Interactive Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Static documentation: See `ENDPOINTS.md`

## Database Location

SQLite database file: `fantasy_league.db` in project root.

To reset: Delete the file and restart the backend (tables auto-create on startup).
