# Fantasy League History - Improvement Plan v3

## Overview
5 small, self-contained improvement stories for Ralph Wiggum to complete in single context windows.

## Files to Create/Update
- `scripts/ralph/prd.json` - Replace userStories with new IMP-011 through IMP-015
- `scripts/ralph/progress.txt` - Reset to track new stories

---

## prd.json Content

```json
{
  "branchName": "ralph/improvements-v3",
  "userStories": [
    {
      "id": "IMP-011",
      "title": "Enable Yahoo League Import Frontend",
      "acceptanceCriteria": [
        "YahooAuthModal component handles OAuth login flow with Yahoo redirect",
        "YahooImportModal component allows entering league key and triggering import",
        "Dashboard 'Import from Yahoo' button opens auth/import flow instead of 'Coming soon'",
        "Imported Yahoo leagues appear in ImportedLeagues list with re-import/delete support",
        "typecheck passes"
      ],
      "priority": 1,
      "passes": false
    },
    {
      "id": "IMP-012",
      "title": "Environment Configuration Setup",
      "acceptanceCriteria": [
        "backend/.env.example documents YAHOO_CLIENT_ID, YAHOO_CLIENT_SECRET, YAHOO_REDIRECT_URI, FRONTEND_URL, CORS_ORIGINS",
        "frontend/.env.example documents VITE_API_URL",
        "CORS origins in main.py read from CORS_ORIGINS env var with localhost:5173 default",
        "README.md updated with environment setup instructions",
        "typecheck passes"
      ],
      "priority": 2,
      "passes": false
    },
    {
      "id": "IMP-013",
      "title": "Loading State Improvements",
      "acceptanceCriteria": [
        "Seasons page shows skeleton loader while fetching data",
        "Records page shows skeleton loader while fetching data",
        "HallOfFame page shows skeleton loader while fetching data",
        "No white flash on initial page load for any of these pages",
        "typecheck passes"
      ],
      "priority": 3,
      "passes": false
    },
    {
      "id": "IMP-014",
      "title": "Add React Error Boundary",
      "acceptanceCriteria": [
        "ErrorBoundary component catches rendering errors in child components",
        "Error state shows user-friendly message with 'Try Again' button",
        "App.tsx wraps main content with ErrorBoundary",
        "Error details logged to console for debugging",
        "typecheck passes"
      ],
      "priority": 4,
      "passes": false
    },
    {
      "id": "IMP-015",
      "title": "API Documentation",
      "acceptanceCriteria": [
        "ENDPOINTS.md file exists in project root",
        "All API endpoints documented with method, path, and description",
        "Endpoints grouped by category (sleeper, yahoo, owners, history, trades, etc.)",
        "Key endpoints include example request/response",
        "typecheck passes"
      ],
      "priority": 5,
      "passes": false
    }
  ]
}
```

---

## Story Details

### IMP-011: Enable Yahoo League Import Frontend
**Priority: 1 | Backend complete, needs frontend UI**

The Yahoo backend is fully implemented (OAuth2, import services, 18 API endpoints, 50 tests). This story builds the missing frontend.

**Files to Create:**
- `frontend/src/components/YahooAuthModal.tsx`
- `frontend/src/components/YahooImportModal.tsx`
- `frontend/src/api/yahoo.ts`

**Files to Modify:**
- `frontend/src/pages/Dashboard.tsx` - Enable Yahoo section, add handlers

**Key Implementation Notes:**
- OAuth flow: Call `/api/yahoo/auth/url` → redirect to Yahoo → callback returns to frontend
- Use session ID stored in localStorage for token management
- Import flow similar to Sleeper: enter league key → call `/api/yahoo/import`
- Backend endpoints already exist and are tested

---

### IMP-012: Environment Configuration Setup
**Priority: 2 | Foundation for Yahoo setup**

**Files to Create:**
- `backend/.env.example`
- `frontend/.env.example`

**Files to Modify:**
- `backend/app/main.py` - Make CORS configurable
- `README.md` - Add environment setup section

**Key Implementation Notes:**
- `CORS_ORIGINS` env var, comma-separated, defaults to `http://localhost:5173`
- Use `os.getenv()` with sensible defaults
- Document all Yahoo OAuth variables

---

### IMP-013: Loading State Improvements
**Priority: 3 | UX polish**

**Files to Modify:**
- `frontend/src/pages/Seasons.tsx`
- `frontend/src/pages/Records.tsx`
- `frontend/src/pages/HallOfFame.tsx`

**Key Implementation Notes:**
- Use existing `LoadingStates.tsx` skeleton components
- Add `loading` state to each page's data fetch
- Show skeleton during fetch, content after

---

### IMP-014: Add React Error Boundary
**Priority: 4 | Error resilience**

**Files to Create:**
- `frontend/src/components/ErrorBoundary.tsx`

**Files to Modify:**
- `frontend/src/App.tsx` - Wrap routes with ErrorBoundary

**Key Implementation Notes:**
- Class component (React error boundaries require this)
- `getDerivedStateFromError` to catch errors
- Retry button resets error state

---

### IMP-015: API Documentation
**Priority: 5 | Documentation**

**Files to Create:**
- `ENDPOINTS.md`

**Key Implementation Notes:**
- Can reference FastAPI auto-docs at `/docs`
- Group by router (sleeper, yahoo, owners, history, trades, leagues, seasons, records, hall-of-fame)
- ~44 endpoints total

---

## Execution Order

1. **IMP-012** (Env Config) - Needed for Yahoo OAuth credentials
2. **IMP-011** (Yahoo Import) - Main feature
3. **IMP-013** (Loading States) - Quick UX win
4. **IMP-014** (Error Boundary) - Safety net
5. **IMP-015** (API Docs) - Documentation polish

---

## Verification

After each story:
1. Run `cd backend && pytest` - all tests pass
2. Run `cd frontend && npm run lint && npm run build` - no errors
3. Manual test: Start servers and verify functionality
