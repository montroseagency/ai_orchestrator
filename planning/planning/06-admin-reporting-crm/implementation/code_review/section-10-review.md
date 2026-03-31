# Code Review: section-10-admin-category-page

## Summary

The implementation is functionally solid with good separation of concerns, proper DnD integration, and reasonable test coverage. A few correctness gaps and patterns need attention.

---

## Critical
None identified.

---

## Important

### 1. Dual state for server data creates stale-state risk
`categories` is a manual shadow of the query cache. After mutations, `categories` briefly shows stale state. The `useEffect` sync is fragile. Recommendation: use `queryData ?? []` directly and use `useMutation` with `onMutate`/`onError` for optimistic reorder.

### 2. No loading or error state rendered
`isLoading` and `isError` from `useQuery` are unused. Page shows empty-state immediately on slow connections or errors.

### 3. `TaskCategoryItem` interface duplicated in test and page
Should be extracted to `client/lib/types/categories.ts`.

### 4. `useEffect` in `CategoryModal` depends on `isOpen` incorrectly
`isOpen` in dependency array causes unnecessary resets. Should depend only on `editTarget`.

### 5. Reorder error test is fragile
Uses call count heuristic instead of explicit assertion.

---

## Minor

- `role="dialog"` on `<form>` creates nested dialog in accessibility tree — remove it (Modal already handles this)
- `handleDragEnd` doesn't guard against `oldIndex === -1`
- `handleConfirmDelete` doesn't show success toast (inconsistent with other actions)
- `categoryIds` should be memoized with `useMemo`
- No test coverage for POST/PATCH failure paths

---

## Nitpicks

- Row preview badge is redundant with color swatch
- `DEFAULT_FORM` could use factory function for explicit reset intent
- `ConfirmationModal` has both named and default export — pick one
- Labels missing `htmlFor` / `id` wiring
