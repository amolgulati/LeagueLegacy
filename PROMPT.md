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
