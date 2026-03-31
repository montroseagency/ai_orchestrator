# Section 08 Code Review Interview

## Auto-Fixes Applied

### CRITICAL: ExportReportModal — URL encoding + variable shadowing
- Renamed `format` state to `exportFormat` (was shadowing `date-fns/format`)
- Used `URLSearchParams` + `encodeURIComponent(clientId)` for safe URL construction

### CRITICAL: OverviewTab — unstable date computation
- Wrapped `today` and `defaultStart` in `useMemo([], [])` to stabilize query key across renders

### MAJOR: TimeCapacityTab — DATE_RANGE_OPTIONS moved to module-level constant
- Moved out of component body to prevent unnecessary array re-creation on every render

### MAJOR: MarketingPlanTab — code block detection
- Replaced unreliable `node` presence heuristic with `!className && !includes('\n')` inline check
- Destructured and discarded `node` to avoid ESLint `no-unused-vars` warnings

### MAJOR: Error UI added to all tabs
- User confirmed: add basic error UI
- Added `isError` check in OverviewTab, MarketingPlanTab, TimeCapacityTab
- Each renders `<InlineError>` with a descriptive message on query failure

### MINOR: Misleading test name fixed
- `'agentType="developer" — same task list without "Project Milestones"... false'`
  → `'agentType="developer" — shows "Project Milestones" section'`

## User Decisions

- Error UI: **Yes, add basic error UI** — user confirmed adding InlineError to failing query states
