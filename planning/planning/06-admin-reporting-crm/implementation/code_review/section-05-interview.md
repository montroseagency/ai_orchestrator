# Code Review Interview: section-05-approval-queue-api

## Interview Decisions

### Q: Add LimitOffsetPagination to list_approvals?
**User answer:** Add LimitOffsetPagination (Recommended)
**Action:** Applied — `list_approvals` now uses `LimitOffsetPagination`. Tests updated to access `response.data['results']`.

---

## Auto-Fixes Applied

1. **Fragile datetime string in ordering test** — Changed `'2020-01-01T00:00:00Z'` to `datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)` in `test_list_ordered_by_updated_at_asc`.

2. **Duplicate ValueError semantics in `reject_task`** — Removed the blank-feedback `ValueError` from `reject_task`. Validation is now only at the view layer (`reject_task_view`), keeping `ValueError` exclusive to state-conflict errors.

3. **`select_for_update()` without `select_related`** — Added `.select_for_update(of=('self',)).select_related('agent__user', 'client')` to both `approve_task` and `reject_task`. The `of=('self',)` is required to avoid PostgreSQL `FOR UPDATE cannot be applied to nullable outer join` error.

4. **Local `import uuid` inside test method** — Moved to top-level imports in `tests.py`.

5. **Comment header "Section 06 (plan 05)"** — Fixed to "Section 05".

---

## Items Let Go

- `ApprovalService` class grouping — cosmetic, not worth restructuring now
- `IsAdminUser` duplication check — would require codebase audit; low risk as-is
- `ApprovalTaskSerializer` in views file — acceptable for self-contained module
- Notification-failure test — nice-to-have, tracked for section-13
