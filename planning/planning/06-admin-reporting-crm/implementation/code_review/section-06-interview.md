# Code Review Interview: section-06-category-management-api

## Interview Decisions

### Q: Should reorder return the updated category list?
**User answer:** Return updated list (Recommended)
**Action:** Applied — `reorder` now returns `self.get_serializer(self.get_queryset(), many=True).data`.

---

## Auto-Fixes Applied

1. **Per-item key validation in `reorder`** — Added guard: each item must have `"id"` and `"sort_order"`; missing keys return 400 instead of KeyError 500.

2. **`sort_order` type validation** — Added `isinstance(item['sort_order'], int)` check; non-integer returns 400.

3. **N UPDATE queries → `bulk_update`** — Replaced N `filter().update()` calls with fetch-set-bulk_update pattern for a single DB round-trip.

4. **ID validation scoped to `self.get_queryset()`** — Future-proof against queryset narrowing.

5. **New test added** — `test_reorder_returns_400_on_missing_sort_order_key` pins the KeyError regression.

---

## Items Let Go

- `TaskCategorySerializer` created_by not read-only — out of scope for this section
- Class-level queryset pattern — DRF standard, not a real risk
