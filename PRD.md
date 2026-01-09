# Fantasy League History - Bug Fixes & Improvements PRD

## Overview
This document tracks critical bugs and feature improvements identified during Yahoo integration testing.

---

## Critical Bugs

### BUG-001: Yahoo Import Not Saving Teams/Matchups to Database
**Status:** PARTIALLY FIXED
**Priority:** P0 - Critical
**Reported:** 2026-01-08
**Updated:** 2026-01-08

**Description:**
When importing a Yahoo league (tested with 2023 season, league key `423.l.170384`), the import reports success but:
- 0 teams saved to database
- 0 matchups saved to database
- Only trades are being saved (8 trades imported)
- Season record is created with correct metadata but no associated data

**Root Cause #1 (FIXED):**
Database schema was out of sync with SQLAlchemy model. The `seasons` table was missing the `third_place_team_id` column that was added to the model. This caused all Season queries to fail silently, preventing teams and matchups from being saved.

**Fix Applied:**
```sql
ALTER TABLE seasons ADD COLUMN third_place_team_id INTEGER REFERENCES teams(id);
```

**Root Cause #2 (FIXED):**
Yahoo API response parsing in `_parse_team()` and `_parse_matchup_team()` wasn't handling nested list structure where team details are in a nested array.

**Fix Applied:**
Updated parsing to flatten nested lists in team data structure.

---

### BUG-001b: Yahoo Import - Matchups and Champion Detection Still Failing
**Status:** Open
**Priority:** P1 - High
**Reported:** 2026-01-08

**Description:**
After fixing the database schema and team parsing, Yahoo import now saves teams/records correctly, but:
- Matchups = 0 (not being saved despite API calls succeeding)
- Champion not being detected/recorded
- Only 8 trades imported (may be correct, but seems low - needs verification)

**Current State:**
- Teams import: WORKING
- Team records (W/L/PF/PA): WORKING
- Matchups import: NOT WORKING
- Champion detection: NOT WORKING
- Trades import: NEEDS VERIFICATION

**Files to Investigate:**
- `backend/app/services/yahoo_service.py` - `import_matchups()`, `detect_and_set_champion()`
- `backend/app/services/yahoo_client.py` - `get_matchups()`, `_parse_matchup()`

**Debug Steps:**
1. Add logging to `import_matchups()` to see if matchups are being fetched
2. Check if `_parse_matchup()` is correctly parsing the nested structure
3. Verify team_key lookup is working in matchup import
4. Check champion detection logic for playoff matchup identification

---

### BUG-002: Owner Merge Fails with Database Constraint Error
**Status:** FIXED
**Priority:** P0 - Critical
**Reported:** 2026-01-08
**Fixed:** 2026-01-08

**Description:**
When attempting to merge owners (e.g., merging "PinguinosMafia" into "Amish"), the operation fails with:
```
sqlite3.IntegrityError: NOT NULL constraint failed: teams.owner_id
```

**Root Cause:**
The merge function was iterating through `secondary.teams` relationship collection while modifying it. SQLAlchemy removes items from the collection when their foreign key changes, causing iteration issues.

**Fix Applied:**
Changed from iterating through relationship collection to using a bulk update query:
```python
db.query(Team).filter(Team.owner_id == secondary.id).update(
    {Team.owner_id: primary.id},
    synchronize_session='fetch'
)
```

**File Modified:**
- `backend/app/api/owners.py` - line 387-392

---

## Feature Improvements

### IMP-001: ESPN Theme - NFL 2K5 Broadcast Style Graphics
**Status:** In Progress
**Priority:** P1 - High
**Reported:** 2026-01-08
**Updated:** 2026-01-08

**Description:**
Transform the UI to match ESPN NFL 2K5 (2004) and SportsCenter broadcast graphics (2002-2006 era). This creates a dramatic sports-broadcast presentation style perfect for league history content.

**Current State:**
- Colors updated to ESPN palette (insufficient)
- Standard card/table layouts (needs replacement)

**Desired State:**
Full broadcast-style presentation with specific visual requirements below.

---

#### Color Palette (EXACT VALUES - REQUIRED)

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg-dark` | `#0D0D0D` | Pure black base |
| `--bg-burgundy` | `#2D0A0A` | Deep burgundy |
| `--bg-burgundy-mid` | `#4A1515` | Mid burgundy for gradients |
| `--bg-burgundy-light` | `#6B1F1F` | Lighter burgundy accent |
| `--metallic-light` | `#D4D4D4` | Score box gradient top |
| `--metallic-mid` | `#A8A8A8` | Score box gradient middle |
| `--metallic-dark` | `#6B6B6B` | Score box gradient bottom |
| `--accent-copper` | `#CD7F32` | Divider lines, borders |
| `--accent-orange` | `#E85D04` | Highlight accent |
| `--accent-red` | `#CC0000` | ESPN red |
| `--accent-gold` | `#FFD700` | Stat numbers, champions |
| `--record-badge-bg` | `#8B0000` | Record/W-L badge background |
| `--text-white` | `#FFFFFF` | Primary text |
| `--text-silver` | `#C0C0C0` | Secondary text, labels |
| `--text-gray` | `#888888` | Muted text |

---

#### Typography Requirements

| Element | Font Family | Weight | Transform | Color |
|---------|-------------|--------|-----------|-------|
| Owner/Team Names | Rockwell, Georgia, serif | Bold | UPPERCASE | White |
| Stat Values | Impact, Arial Black | Bold | - | Gold `#FFD700` |
| Stat Labels | Arial, Helvetica | Normal | - | Silver `#C0C0C0` |
| Section Headers | Rockwell, Georgia, serif | Bold | UPPERCASE | White |
| Record Badges | Impact, Arial Black | Bold | - | White on `#8B0000` |

---

#### Core Visual Elements

1. **Page Backgrounds**
   - Radial gradient: `#4A1515` → `#2D0A0A` → `#0D0D0D`
   - Never use flat colors or light backgrounds

2. **Card Headers**
   - Background: `#0D0D0D` (pure black)
   - Border-bottom: 3px solid `#CD7F32` (copper)
   - Owner/team name on left, record badge on right

3. **Score Boxes (Matchup Scores)**
   - Metallic gradient: `#D4D4D4` → `#A8A8A8` → `#6B6B6B`
   - Bevel effect with inset shadows
   - Winner variant: Gold gradient `#FFD700` → `#B8860B`

4. **Divider Lines**
   - Height: 3px
   - Copper/orange gradient with fade at edges

5. **Tables**
   - Header: Black background, 3px copper bottom border
   - Body: Burgundy gradient background
   - Alternating rows: Subtle darkening
   - Champion row: Gold left border + gold background tint

6. **Corners**
   - Sharp edges only (0-2px border-radius max)

---

#### Component Specifications

**Owner Card:**
- Black header with name (serif, ALL CAPS) + record badge
- Burgundy gradient body
- Stats: gold values, silver labels

**Matchup Card:**
- Score header with metallic boxes (gold for winner)
- Copper divider below scores
- Two-column stats panel with burgundy background

**Hall of Fame:**
- Gold border around section
- "HALL OF FAME" header in gold text
- Champion cards with trophy emoji + gold borders

**Standings Table:**
- Rank in gold, names in serif ALL CAPS
- Champion row highlighted with gold

**Navigation:**
- Dark burgundy gradient background
- Copper right border
- Active: gold text + gold left border
- Hover: copper left border

---

#### Anti-Patterns (DO NOT USE)

- Light/white backgrounds
- Flat solid colors (always use gradients)
- Rounded corners > 4px
- Sans-serif for owner/team names
- Thin/light font weights
- Blue accent colors
- Modern minimalist spacing
- Material Design patterns

---

#### Files to Create/Modify

**Modify:**
- `frontend/tailwind.config.js` - Add theme colors/fonts
- `frontend/src/index.css` - Update espn-retro theme styles
- `frontend/src/App.tsx` - Apply page background
- All existing page/component files - Apply theme classes

---

#### Implementation Checklist

- [ ] Tailwind config updated with ESPN color palette
- [ ] espn-retro theme CSS updated in index.css
- [ ] Page backgrounds use burgundy-to-black gradient
- [ ] Card headers are black with copper border
- [ ] All stat numbers display in gold (#FFD700)
- [ ] Owner/team names use serif font, ALL CAPS
- [ ] Record badges have dark red background
- [ ] Score boxes have metallic gradient + bevel
- [ ] Tables have copper header border
- [ ] No rounded corners > 4px
- [ ] Navigation styled with copper/gold accents
- [ ] Charts use gold/copper/red palette
- [ ] Hall of Fame has gold border treatment
- [ ] Champion rows highlighted with gold

---

#### Visual References

Based on:
- ESPN NFL 2K5 SportsCenter halftime box scores
- ESPN NFL 2K5 player stat cards
- Early 2000s ESPN broadcast graphics (NFL Primetime era)

Key characteristics: Deep burgundy backgrounds, metallic silver score boxes, copper accent lines, bold serif team names, gold stat numbers, dark red badges, information-dense layouts

---

## Technical Debt

### DEBT-001: Yahoo API Response Structure Varies by Season
**Status:** Partially Fixed
**Priority:** P2 - Medium

**Description:**
Yahoo API returns different nested structures for different seasons/endpoints. The `_parse_team` method was fixed to handle nested lists, but there may be other parsing edge cases.

**Recommendation:**
- Add comprehensive logging for API responses
- Create response validation/normalization layer
- Add integration tests with real API response fixtures

---

## Testing Checklist

### Yahoo Import
- [ ] Import 2024 season - verify teams, matchups, trades
- [ ] Import 2023 season - verify teams, matchups, trades
- [ ] Import older seasons (2020, 2019, etc.)
- [ ] Verify champion detection works
- [ ] Verify owner creation/mapping

### Owner Management
- [ ] Merge owners with teams from same platform
- [ ] Merge owners with teams from different platforms
- [ ] Verify team history preserved after merge

### Theme/UI
- [ ] ESPN theme matches broadcast style
- [ ] All pages render correctly with theme
- [ ] Charts/graphs styled appropriately

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-08 | 0.1 | Initial PRD created with BUG-001, BUG-002, IMP-001 |
