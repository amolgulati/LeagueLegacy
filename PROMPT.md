# Ralph Agent Instructions

## Project Context
Fantasy League History Tracker - unifies Yahoo Fantasy and Sleeper data with rich statistics and ESPN-inspired UI.

## Your Task

1. Read `PRD.md` for bugs and features (prioritized by P0 > P1 > P2)
2. Read `progress.txt` for learnings and patterns
3. Read `CLAUDE.md` for project structure and commands
4. Pick ONE item: highest priority bug/feature with status "Open" or "In Progress"
5. Implement it completely, meeting all acceptance criteria
6. Run tests: `cd backend && pytest` and `cd frontend && npm run build`
7. Commit: `git add -A && git commit -m "fix: [ID] - [Title]"` or `feat: [ID] - [Title]`
8. Update `PRD.md`: change status to "FIXED" or "COMPLETE"
9. Append learnings to `progress.txt`

## Priority Order

1. **P0 - Critical**: Blocking bugs, data loss issues
2. **P1 - High**: Core functionality, major features
3. **P2 - Medium**: Improvements, tech debt
4. **P3 - Low**: Nice-to-haves

## Progress Format

APPEND to progress.txt after each item:
```
## [Date] - [ID]: [Title]
**Status:** FIXED/COMPLETE
**Files Changed:**
- file1.py - description
- file2.tsx - description
**Learnings:**
- Pattern or gotcha discovered
```

## Stop Condition

If no items have status "Open" or "In Progress", output:
<promise>COMPLETE</promise>

Otherwise, complete ONE item and exit normally.

## Key References

- `CLAUDE.md` - Project structure, commands, gotchas
- `ENDPOINTS.md` - API documentation
- `HISTORY.md` - Completed work archive
