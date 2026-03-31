# Code Review: section-06-dashboard-page

## Summary
The page is a clean, well-scoped refactor that correctly replaces a monolithic client-selector–driven page with a composed KPI dashboard. The tests are well-structured and cover the important orchestration paths. Two non-nullable assertions on potentially-undefined data are the main issue that must be addressed before shipping.

---

## CRITICAL

### 1. Non-null assertions on `data` after the `isLoading`/`isError` guards do not eliminate `undefined` at runtime

```tsx
// line 490
<CurrentTaskKpi timeBlocks={data!.time_blocks} agentType={agentType} />
// line 505
<DashboardStatsRow stats={data!.stats} />
// line 541
globalTasks={data!.todays_global_tasks}
// line 542
clientTasks={data!.todays_client_tasks}
// line 550
timeBlocks={data!.time_blocks}
```

`useCommandCenter` is typed so that `data` can be `undefined` even when `isLoading` and `isError` are both `false` (e.g. a query that has not yet fetched, or a background refetch that briefly puts the query back into a non-loading-non-error state on remount). The `!` assertions suppress the TypeScript error but will produce a runtime `TypeError: Cannot read properties of undefined` in those edge cases.

**Fix:** Either narrow with an explicit guard before the return or provide a fallback:

```tsx
if (isLoading || !data) { /* skeleton */ }
```

This ensures `data` is always defined in the success branch, making the assertions unnecessary and the types sound.

---

## IMPORTANT

### 2. `todayStr` is computed at render time without memoization

```tsx
const todayStr = new Date().toISOString().slice(0, 10)
```

This is called on every re-render (including the `isFetching` pulse re-renders). For a page component this is low-cost, but the value will silently flip at midnight mid-session, potentially causing a prop mismatch on `ReadOnlySchedule` between what the schedule header shows and what the underlying query key uses.

**Fix:** Derive `todayStr` with `useMemo` and no dependencies (or compute once outside the component) so it is stable for the session lifetime.

### 3. The Retry button is a raw `<button>` rather than the project's `<Button>` component

```tsx
<button
  onClick={() => refetch()}
  className="px-4 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent/90 transition-colors"
>
  Retry
</button>
```

`CLAUDE.md` explicitly requires using `client/components/ui/button.tsx` for interactive controls. This one-off deviates from the design system and lacks the consistent focus ring, loading state, and disabled handling the shared component provides.

### 4. `agentType` is a hardcoded string constant but not typed

```tsx
const agentType = 'marketing'
```

There is no union type (`'marketing' | 'design' | ...`) guarding this prop. If `CurrentTaskKpi`, `DashboardTaskList`, and `ReadOnlySchedule` accept a typed `agentType` prop, this should either be narrowed to that union type locally or imported from a shared types file. As written, TypeScript will widen it to `string`, hiding any future enum drift.

### 5. Tests use `as any` casts on `mockUseCommandCenter.mockReturnValue`

```tsx
} as any)
```

This appears in every `beforeEach` block. Because the mock return type was already annotated by `vi.mocked(useCommandCenter)`, the `as any` suppresses useful type checking that would catch mismatches between mock shape and the real hook contract if the hook signature changes.

**Fix:** Define a typed helper that satisfies `UseQueryResult<CommandCenterData>` (even partially via `Partial`) and drop the `as any` casts.

### 6. Missing test: `isFetching` progress bar render

The tests cover `isLoading`, `isError`, and the loaded state, but there is no test verifying that the `isFetching` pulse bar renders (or is hidden) when `isFetching` is `true` / `false`. This is observable UI state driven by a distinct flag.

---

## MINOR / NITPICK

### 7. `agentType` constant placement

`const agentType = 'marketing'` is declared inside the component body. Since it never changes and is not reactive, it belongs outside the component or as a module-level constant to avoid a new reference on every render (negligible cost, but signals intent).

### 8. No `aria-live` region for the `isFetching` progress bar

The `h-0.5` pulse bar is marked `aria-hidden="true"`, which is correct since it carries no semantic meaning on its own. However, there is no `aria-live="polite"` region announcing to screen readers that the dashboard data is refreshing. This is a minor gap — a visually-hidden status message would complete the pattern.

### 9. Skeleton grid hardcodes 4 columns for stats row

```tsx
<div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
  <Skeleton ... />
  ...  {/* 4 items */}
</div>
```

If `DashboardStatsRow` ever changes the number of stats displayed, this skeleton count will be out of sync. Consider deriving the skeleton count from a shared constant.

### 10. `dashboard/__tests__/` test file path vs co-location pattern

The test is in `client/components/agent/dashboard/__tests__/` but it imports and tests `client/app/dashboard/agent/marketing/page.tsx`. Placing a page-level test under a components directory is slightly confusing. A test at `client/app/dashboard/agent/marketing/__tests__/page.test.tsx` would be more conventional for a Next.js project.

### 11. Semi-colon style inconsistency removed from page but retained in test imports

The old page used semicolons; the new page deliberately omits them (project style). The test file also omits them — consistent. No action needed, just confirming the style is intentional and uniform in this section.

---

## Verdict

**APPROVE WITH FIXES**

The two critical non-null assertion issues and the raw `<button>` deviation from the design system should be addressed. The rest of the findings are improvements that can be batched or handled in follow-up.
