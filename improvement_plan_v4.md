# Fantasy League History - Improvement Plan v4

## Overview
5 stories to add an ESPN Retro theme (early 2000s NFL Primetime / NFL2K aesthetic) with a toggleable theme system.

## Files to Create/Update
- `scripts/ralph/prd.json` - Add IMP-016 through IMP-020
- `scripts/ralph/progress.txt` - Reset to track new stories

---

## prd.json Content

```json
{
  "branchName": "ralph/improvements-v4",
  "userStories": [
    {
      "id": "IMP-016",
      "title": "Theme Infrastructure Setup",
      "acceptanceCriteria": [
        "ThemeContext created with provider that manages theme state (dark, light, espn-retro)",
        "Theme toggle in App.tsx cycles through all 3 themes instead of just dark/light",
        "Theme preference persists in localStorage",
        "CSS variables expanded to cover all colors used in app (~20-25 variables)",
        "useTheme hook available for components to access current theme",
        "typecheck passes"
      ],
      "priority": 1,
      "passes": false
    },
    {
      "id": "IMP-017",
      "title": "ESPN Retro Color Palette Design",
      "acceptanceCriteria": [
        "ESPN retro theme colors defined: primary red (#CC0000), gold accents (#FFD700), deep black backgrounds",
        "All CSS variables have values for espn-retro theme in index.css",
        "Color scheme has sufficient contrast for accessibility (4.5:1 minimum)",
        "Theme visually evokes early 2000s ESPN/NFL Primetime aesthetic",
        "typecheck passes"
      ],
      "priority": 2,
      "passes": false
    },
    {
      "id": "IMP-018",
      "title": "Update Core Components for Theming",
      "acceptanceCriteria": [
        "Dashboard.tsx uses CSS variables instead of hardcoded Tailwind colors",
        "OwnerProfileCard.tsx avatar gradients are theme-aware",
        "ImportModal.tsx and ImportedLeagues.tsx use theme variables",
        "LoadingStates.tsx skeleton colors respect current theme",
        "Navigation and header respect current theme",
        "typecheck passes"
      ],
      "priority": 3,
      "passes": false
    },
    {
      "id": "IMP-019",
      "title": "Update Data Visualization for Theming",
      "acceptanceCriteria": [
        "TradeTimeline.tsx chart colors come from theme (not hardcoded hex)",
        "HallOfFame.tsx trophy SVG gradients are theme-aware",
        "Records.tsx medal and stat colors use theme variables",
        "TradeNetwork.tsx visualization respects theme",
        "All pages render correctly in all 3 themes",
        "typecheck passes"
      ],
      "priority": 4,
      "passes": false
    },
    {
      "id": "IMP-020",
      "title": "Theme Polish and Typography",
      "acceptanceCriteria": [
        "Smooth transitions when switching themes (300ms)",
        "ESPN retro theme has bolder typography feel where appropriate",
        "Theme toggle has visual indicator showing current theme",
        "No flash of wrong theme on page load",
        "All 3 themes tested on all major pages",
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

### IMP-016: Theme Infrastructure Setup
**Priority: 1 | Foundation for multi-theme support**

Current state has a dark/light toggle but it's not extensible. This story creates proper infrastructure.

**Files to Create:**
- `frontend/src/contexts/ThemeContext.tsx`
- `frontend/src/hooks/useTheme.ts` (or export from context)
- `frontend/src/constants/themes.ts`

**Files to Modify:**
- `frontend/src/App.tsx` - Use ThemeProvider, update toggle UI
- `frontend/src/index.css` - Expand CSS variable definitions

**Key Implementation Notes:**
- Theme type: `'dark' | 'light' | 'espn-retro'`
- ThemeProvider wraps app and manages state
- CSS variables for: bg-primary, bg-secondary, bg-card, text-primary, text-secondary, text-muted, border-color, accent-primary, accent-secondary, etc.
- Toggle cycles: dark → light → espn-retro → dark

---

### IMP-017: ESPN Retro Color Palette Design
**Priority: 2 | Define the retro aesthetic**

**Files to Modify:**
- `frontend/src/constants/themes.ts`
- `frontend/src/index.css`
- `frontend/tailwind.config.js` (optional, for custom colors)

**ESPN Retro Palette:**
```css
/* ESPN Retro Theme */
html.espn-retro {
  --bg-primary: #0a0a0a;        /* Deep black */
  --bg-secondary: #1a1a1a;      /* Dark charcoal */
  --bg-card: #242424;           /* Card background */
  --text-primary: #ffffff;       /* Bright white */
  --text-secondary: #cccccc;     /* Light gray */
  --accent-primary: #CC0000;     /* ESPN Red */
  --accent-secondary: #FFD700;   /* Gold */
  --accent-tertiary: #FF6600;    /* Orange highlight */
  --border-color: #333333;       /* Dark border */
  --success: #00CC00;            /* Scoreboard green */
  --warning: #FFCC00;            /* Yellow alert */
}
```

**Inspiration:**
- NFL Primetime bold graphics
- ESPN Bottom Line ticker
- NFL2K scorebug UI
- High contrast, punchy colors

---

### IMP-018: Update Core Components for Theming
**Priority: 3 | Make UI theme-aware**

**Files to Modify:**
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/Owners.tsx`
- `frontend/src/components/OwnerProfileCard.tsx`
- `frontend/src/components/ImportModal.tsx`
- `frontend/src/components/ImportedLeagues.tsx`
- `frontend/src/components/LoadingStates.tsx`

**Key Changes:**
- Replace `bg-slate-800` with `bg-[var(--bg-secondary)]`
- Replace `text-slate-400` with `text-[var(--text-secondary)]`
- Replace `border-slate-700` with `border-[var(--border-color)]`
- Make avatar gradient generation theme-aware (use theme colors)

---

### IMP-019: Update Data Visualization for Theming
**Priority: 4 | Charts and graphics**

**Files to Modify:**
- `frontend/src/components/TradeTimeline.tsx`
- `frontend/src/components/TradeNetwork.tsx`
- `frontend/src/pages/HallOfFame.tsx`
- `frontend/src/pages/Records.tsx`
- `frontend/src/pages/Seasons.tsx`
- `frontend/src/pages/HeadToHead.tsx`

**Key Challenges:**
- Recharts colors are defined in JS, need to use `useTheme()` hook
- SVG gradients in HallOfFame need dynamic fill colors
- Medal colors in Records should match theme accents

---

### IMP-020: Theme Polish and Typography
**Priority: 5 | Final touches**

**Files to Modify:**
- `frontend/src/index.css`
- `frontend/src/App.tsx`
- Various components as needed

**Key Implementation Notes:**
- Add `transition-colors duration-300` to themed elements
- Theme toggle should show icon/label for current theme
- Consider slightly bolder font weights for ESPN theme
- Test all pages in all themes for visual consistency

---

## Execution Order

1. **IMP-016** (Infrastructure) - Must come first, foundation for everything
2. **IMP-017** (Color Palette) - Define colors before using them
3. **IMP-018** (Core Components) - Update main UI elements
4. **IMP-019** (Data Viz) - Update charts and graphics
5. **IMP-020** (Polish) - Final touches and testing

---

## Verification

After each story:
1. Run `cd frontend && npm run lint && npm run build` - no errors
2. Manual test: Toggle through all 3 themes
3. Check all major pages render correctly in each theme
4. Verify no white flash on page load
