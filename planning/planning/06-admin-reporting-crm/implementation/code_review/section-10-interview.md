# Code Review Interview: section-10-admin-category-page

## Pre-interview: Already-Fixed Findings

Before the interview, the implementation was checked against the review. Most findings were already addressed:

- ✅ Dual state → `useMutation` with `onMutate`/`onError`/`onSettled` already used
- ✅ Loading/error states already rendered
- ✅ `TaskCategoryItem` already extracted to `@/lib/types/categories`
- ✅ `role="dialog"` not present in `<form>`
- ✅ `handleDragEnd` guards `oldIndex === -1`
- ✅ `handleConfirmDelete` shows `toast.success('Category deleted')`
- ✅ `categoryIds` memoized with `useMemo`
- ✅ Labels have `htmlFor`/`id` wiring
- ✅ `DEFAULT_FORM` uses `{ ...EMPTY_FORM }` factory pattern

---

## Interview Decisions

### Q1: Replace reorder error test call-count heuristic with `toast.error` assertion?

**Answer:** Yes — use `toast.error` assertion (auto-fix)

**Applied:** Replaced `mockGet.mock.calls.length > initialCallCount` check with `expect(toast.error).toHaveBeenCalled()`.

---

### Q2: Add failure-path tests for POST and PATCH?

**Answer:** Yes — add failure tests

**Applied:** Added two new tests:
- `modal submit shows error toast on POST failure` — mocks `mockPost` to reject, asserts `toast.error` called
- `active toggle shows error toast on PATCH failure` — mocks `mockPatch` to reject, asserts `toast.error` called

---

## Auto-fixes Applied (No User Input Needed)

### Fix: Remove duplicate `export default` from `ConfirmationModal`

`client/components/common/confirmation-modal.tsx` had both a named export (`export function ConfirmationModal`) and a default re-export (`export default ConfirmationModal`). Removed the default export — named export only. Callers use `{ ConfirmationModal }` import.

---

## Let Go (No Action)

- **`useEffect` deps include `isOpen`:** Early return `if (!isOpen) return` prevents incorrect state changes. `isOpen` is needed so reopening the modal with the same `editTarget` re-populates the form. Not a real bug.
- **Row preview badge redundant with color swatch:** Design choice — the preview badge shows name + color together, which is useful for admin context.

---

## Final Test Count: 12 tests, all passing
