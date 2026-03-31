

<!-- PROJECT_CONFIG
runtime: typescript-npm
test_command: cd client && npm test -- --run
END_PROJECT_CONFIG -->

<!-- SECTION_MANIFEST
section-01-test-utils
section-02-current-task-kpi
section-03-dashboard-stats
section-04-dashboard-task-list
section-05-readonly-schedule
section-06-dashboard-page
END_MANIFEST -->

# Implementation Sections Index: Agent Dashboard KPI

## Overview

Six sections implement the read-only agent dashboard. The first section establishes the data layer and test utilities that all components depend on. Sections 02–05 implement the four dashboard components in parallel. Section 06 assembles the page and integration tests.

## Dependency Graph

| Section | Depends On | Blocks | Parallelizable |
|---------|------------|--------|----------------|
| section-01-test-utils | — | 02, 03, 04, 05 | Yes |
| section-02-current-task-kpi | 01 | 06 | Yes |
| section-03-dashboard-stats | 01 | 06 | Yes |
| section-04-dashboard-task-list | 01 | 06 | Yes |
| section-05-readonly-schedule | 01 | 06 | Yes |
| section-06-dashboard-page | 02, 03, 04, 05 | — | No |

## Execution Order

1. `section-01-test-utils` (no dependencies — foundation)
2. `section-02-current-task-kpi`, `section-03-dashboard-stats`, `section-04-dashboard-task-list`, `section-05-readonly-schedule` (parallel after 01)
3. `section-06-dashboard-page` (requires all of 02–05)

## Section Summaries

### section-01-test-utils
Update `useCommandCenter` in `client/lib/hooks/useScheduling.ts` to add `staleTime: 55_000`. Verify/extend `client/test-utils/scheduling.tsx` to include `createMockTimeBlock()`, `createMockGlobalTask()`, and `renderWithQuery()`. Add `makeMockCommandCenterData()` helper. Add staleTime/refetchInterval config tests. These utilities are prerequisites for all component test suites.

### section-02-current-task-kpi
Implement `client/components/agent/dashboard/CurrentTaskKpi.tsx` — the primary KPI widget showing the currently active time block with animated progress bar, time remaining, deep-link button, and three empty states (active/free/no tasks). Implement `client/components/agent/dashboard/__tests__/CurrentTaskKpi.test.tsx` covering active block detection, progress calculation, empty states, 60s timer, deep-link href, and ARIA attributes.

### section-03-dashboard-stats
Implement `client/components/agent/dashboard/DashboardStatsRow.tsx` — a row of four read-only stat cards mapping `CommandCenterStats` fields to "Active Tasks", "Done Today", "Hours Blocked", "Active Clients". Implement `client/components/agent/dashboard/__tests__/DashboardStatsRow.test.tsx` covering all four values, all four labels, and zero-value edge cases.

### section-04-dashboard-task-list
Implement `client/components/agent/dashboard/DashboardTaskList.tsx` — merged global + client task list with status-group sorting, optimistic checkbox mutations (cache-based), rollback on error, cross-client tasks as display-only, and portal footer link. Implement `client/components/agent/dashboard/__tests__/DashboardTaskList.test.tsx` covering merge/render, sort order, checkbox behavior, optimistic update, rollback, and empty state.

### section-05-readonly-schedule
Implement `client/components/agent/dashboard/ReadOnlySchedule.tsx` — a vertical hour-by-hour timeline with absolutely-positioned blocks, NowIndicator sub-component, active block highlight, auto-scroll on mount, and portal footer link. No click handlers, no DnD. Implement `client/components/agent/dashboard/__tests__/ReadOnlySchedule.test.tsx` covering block positioning math, hour grid labels, NowIndicator position/visibility, no-interactivity assertions, and auto-scroll.

### section-06-dashboard-page
Implement `client/components/agent/dashboard/index.ts` barrel export. Implement `client/app/dashboard/agent/marketing/page.tsx` (update or create the dashboard route page) as `AgentDashboardPage` — calls `useCommandCenter()`, handles loading/error/loaded states, distributes data to the four child components, applies the two-column layout (KPI full-width, stats row, task list + schedule side-by-side). Implement integration tests covering loading skeleton, error state, loaded state (all four sections present), and mobile layout ordering.
