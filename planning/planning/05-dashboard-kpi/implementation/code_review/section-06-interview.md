# Code Review Interview: section-06-dashboard-page

## Interview Decision

No user interview required — all findings fall into auto-fix or let-go categories.

---

## Auto-Fixes Applied

### CRITICAL
1. **`data!` non-null assertions** — Combined `if (isLoading || !data)` guard instead of separate `isLoading` and `isError` returns. TypeScript now narrows `data` to defined in the success branch; all `!` operators removed.

### IMPORTANT
2. **`todayStr` midnight flip** — Stabilized with `useMemo(() => new Date().toISOString().slice(0, 10), [])`.
3. **Raw `<button>` for Retry** — Replaced with project `Button` component from `@/components/ui/button`.
4. **`as any` casts in tests** — Introduced `makeQueryReturn()` helper typed with `Partial<ReturnType<typeof useCommandCenter>>` to avoid cast suppression.
5. **Missing `isFetching` test** — Added test asserting the pulse indicator is present when `isFetching: true`.

### MINOR
6. **`agentType` outside component** — Moved to module-level constant.
7. **`aria-live` on fetching indicator** — Added `aria-live="polite"` and descriptive text for screen readers.

## Let Go
- `agentType` union typing: child props accept `string`; no union type defined in shared types.
- Test file location: consistent with all other dashboard component tests in `__tests__/`.
- Skeleton stat count: acceptable drift risk given implementation is complete.
