# Task: Generate a 10-Story Improvement Plan for Fantasy League History Tracker

## Context
This is a Fantasy League History Tracker app that imports data from Sleeper and Yahoo Fantasy leagues. Ralph (an AI orchestrator) built the initial version, but there are gaps and bugs that need fixing.

## Current Issues to Address

### 1. Sleeper Import - Missing Historical Seasons
- Currently only imports the current/2025 season
- Need to import ALL historical seasons (2024, and any prior years)
- Sleeper API provides `previous_league_id` to traverse league history

### 2. Sleeper Import - No Champion Detection
- 2025 season is complete but no champion is recorded
- Need to detect playoff bracket winner from matchups
- Champion should be stored in the Season record

### 3. Sleeper Import - Player IDs Not Resolved
- Trades show player IDs (numbers) instead of player names
- Sleeper has a player database endpoint to resolve IDs to names
- Need to fetch and cache player names, display them in trades

### 4. Yahoo Fantasy Import - Not Implemented
- Backend has placeholder routes but no actual Yahoo API integration
- Need OAuth2 flow for Yahoo authentication
- Need to import: leagues, standings, matchups, trades

### 5. UI/UX Gaps
- Import modal needs loading states and better error handling
- No way to see import history or re-import leagues
- Dashboard should show which leagues are imported

## Your Task

Generate a `prd.json` file with exactly 10 user stories that will fix these issues. Each story must:

1. Be completable in a single coding session (< 30 min of AI work)
2. Have specific, testable acceptance criteria
3. Include "typecheck passes" or "tests pass" in criteria where applicable
4. Be ordered by dependency (foundational work first)

## Output Format

Output ONLY valid JSON in this exact format:
```json
{
  "branchName": "ralph/improvements-v2",
  "userStories": [
    {
      "id": "IMP-001",
      "title": "Short descriptive title",
      "acceptanceCriteria": [
        "Specific criterion 1",
        "Specific criterion 2",
        "typecheck passes"
      ],
      "priority": 1,
      "passes": false
    }
  ]
}
```

## Technical Context

- Backend: Python/FastAPI in `backend/`
- Frontend: React/Vite/Tailwind in `frontend/`
- Database: SQLite with SQLAlchemy
- Sleeper API: Public, no auth needed
- Yahoo API: Requires OAuth2 (use yahoo-oauth or similar)

## Prioritization Guidance

1. Fix Sleeper historical import first (most value, no auth needed)
2. Fix player name resolution (improves existing data)
3. Add champion detection (completes the data model)
4. Then Yahoo integration (more complex, requires OAuth)
5. UI improvements last (polish after core works)

Generate the 10 stories now.
