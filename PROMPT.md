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

## References

- **HISTORY.md** - All completed stories (FLH-002 through IMP-015)
- **CLAUDE.md** - Project structure, commands, and common gotchas
- **ENDPOINTS.md** - API documentation

---

## Completed Stories This Session

### IMP-019: Update Data Visualization for Theming ✅
**Completed:** 2026-01-08

**Acceptance Criteria Met:**
- ✅ TradeTimeline.tsx chart colors come from theme (not hardcoded hex)
- ✅ HallOfFame.tsx trophy SVG gradients are theme-aware
- ✅ Records.tsx medal and stat colors use theme variables
- ✅ TradeNetwork.tsx visualization respects theme
- ✅ All pages render correctly in all 3 themes
- ✅ typecheck passes

**Files Changed:**
- `frontend/src/components/TradeTimeline.tsx` - Theme-aware chart colors (getThemeColors, getChartThemeStyles)
- `frontend/src/components/TradeNetwork.tsx` - Theme-aware charts and owner avatars
- `frontend/src/pages/HallOfFame.tsx` - Theme-aware trophy gradients (useId for unique IDs), medals, leaderboards
- `frontend/src/pages/Records.tsx` - Theme-aware medals and record cards

**Next Story:** IMP-022 (Fix Owners Tab Championships Display)

---

### IMP-020: Theme Polish and Typography ✅
**Completed:** 2026-01-08

**Acceptance Criteria Met:**
- ✅ Smooth transitions when switching themes (300ms)
- ✅ ESPN retro theme has bolder typography feel where appropriate
- ✅ Theme toggle has visual indicator showing current theme
- ✅ No flash of wrong theme on page load
- ✅ All 3 themes tested on all major pages
- ✅ typecheck passes

**Files Changed:**
- `frontend/src/index.css` - Theme transitions (300ms), ESPN retro typography (uppercase, bold, letter-spacing)
- `frontend/src/App.tsx` - Enhanced theme toggle with visual indicator label
- `frontend/index.html` - Blocking theme script to prevent flash, initial background colors

---

### IMP-018: Update Core Components for Theming ✅
**Completed:** 2026-01-08 (Previous iteration)

**Acceptance Criteria Met:**
- ✅ Dashboard.tsx uses CSS variables instead of hardcoded Tailwind colors
- ✅ OwnerProfileCard.tsx avatar gradients are theme-aware
- ✅ ImportModal.tsx and ImportedLeagues.tsx use theme variables
- ✅ LoadingStates.tsx skeleton colors respect current theme
- ✅ Navigation and header respect current theme
- ✅ typecheck passes

---

### IMP-022: Fix Owners Tab Championships Display ✅
**Completed:** 2026-01-08

**Acceptance Criteria Met:**
- ✅ Championships count on Owners tab matches Hall of Fame tab
- ✅ Use same data source (Season.champion_team_id) as Hall of Fame for consistency
- ✅ Owner profile cards show correct championship trophy count
- ✅ typecheck passes

**Files Changed:**
- `backend/tests/test_history.py` - Fixed 2 tests to use champion_team_id instead of final_rank

**Notes:**
- Backend was already correct - both Owners API and Hall of Fame API use `Season.champion_team_id`
- The tests were outdated and expected championships from `final_rank=1` instead of `champion_team_id`
- All 204 backend tests now pass

---

### IMP-023: Track 2nd and 3rd Place Finishes ✅
**Completed:** 2026-01-08

**Acceptance Criteria Met:**
- ✅ Season model has third_place_team_id field (runner_up already exists)
- ✅ Owner stats include runner_up_finishes and third_place_finishes counts
- ✅ Hall of Fame shows runner-up leaderboard (silver medals)
- ✅ Hall of Fame shows 3rd place leaderboard (bronze medals)
- ✅ Owner profile cards display 2nd/3rd place trophy counts
- ✅ Records page shows Most Runner-Up Finishes and Most Third Place Finishes
- ✅ typecheck passes (build succeeded)
- ✅ All 207 backend tests pass (3 new tests added)

**Files Changed:**
- `backend/app/db/models.py` - Added third_place_team_id to Season model
- `backend/app/api/history.py` - Updated calculate_owner_stats, OwnerWithStats, CareerStats
- `backend/app/api/hall_of_fame.py` - Added PlacementCount model, runner_up_leaderboard, third_place_leaderboard
- `backend/app/api/records.py` - Added PlacementRecord model, get_placement_records helper, placement records
- `backend/tests/test_history.py` - Added TestPodiumFinishes class with 3 tests
- `frontend/src/types/owner.ts` - Added runner_up_finishes, third_place_finishes to OwnerWithStats
- `frontend/src/components/OwnerProfileCard.tsx` - Podium stats (1st/2nd/3rd) with trophy icons
- `frontend/src/pages/HallOfFame.tsx` - PlacementCount type, PlacementLeaderboardRow, runner-up/third-place sections
- `frontend/src/pages/Records.tsx` - PlacementRecord type, PlacementRecordCard, placement record displays

---

## ALL STORIES COMPLETE ✅

All 7 stories in prd.json have `passes: true`:
- IMP-016: Theme Infrastructure Setup ✅
- IMP-017: ESPN Retro Color Palette Design ✅
- IMP-018: Update Core Components for Theming ✅
- IMP-019: Update Data Visualization for Theming ✅
- IMP-020: Theme Polish and Typography ✅
- IMP-022: Fix Owners Tab Championships Display ✅
- IMP-023: Track 2nd and 3rd Place Finishes ✅
