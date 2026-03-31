# Code Review: Section 03 — Client Report API

**Reviewer:** Senior Django/Python Code Review
**Date:** 2026-03-30
**Diff file:** `planning/06-admin-reporting-crm/implementation/code_review/section-03-diff.md`
**Spec:** `planning/06-admin-reporting-crm/sections/section-03-client-report-api.md`

---

## Summary

The implementation is largely correct and well-structured. The core architecture — Python-level aggregation over `.values()` fetches to avoid N+1, a clean separation of date parsing and assignment checking, and a single-pass aggregation loop — aligns with the spec's intent. Authorization and 404/403 handling are correct. Query count is bounded at 3 queries (auth + client lookup + time blocks + tasks), well within the ≤ 6 target.

However, there are three issues worth addressing before this ships:

1. **Critical:** `tb_duration` only covers time blocks within the selected date range, but tasks are fetched via a broader OR filter (`created_at OR completed_at` in range). A task whose `time_block` falls outside the date window (e.g. a task created in range but whose block was scheduled earlier) will silently report `hours_spent = 0`, producing misleading category and tasks-list hours. The spec links category hours to blocks via `AgentGlobalTask.time_block`, so this edge case needs explicit handling.

2. **Major:** The `_block_duration_minutes` helper uses `date.today()` as the base date for midnight-crossing detection. This is cosmetically correct (the math only uses the date as an anchor), but it is semantically confusing and fragile — if a time block value is ever stored as a naive `datetime` string on a different DST day, the comparison could produce off-by-one-hour bugs. The model's own `duration_minutes` property uses `self.date` as the anchor — the view's helper should mirror that exactly.

3. **Minor:** The `_parse_date_range` function does not validate that `start_date <= end_date` when both are explicitly provided. A request with `?start_date=2026-12-01&end_date=2026-01-01` will silently return an empty result set rather than a 400 error.

No security vulnerabilities were found. No N+1 queries were found.

---

## Issues Found

### Critical

#### C-01 — Category hours and task `hours_spent` can silently be zero for out-of-window time blocks

**File:** `server/api/views/agent/client_report_views.py`, lines 378–398, 453–462

**Problem:**
`tb_duration` is built exclusively from time blocks that match `date__range=(start_date, end_date)`:

```python
tb_duration = {
    b['id']: _block_duration_minutes(b['start_time'], b['end_time'])
    for b in time_blocks          # only blocks within the date window
}
```

Tasks are fetched with a broader filter:

```python
Q(created_at__date__range=(start_date, end_date))
| Q(completed_at__date__range=(start_date, end_date))
```

A task could have been created inside the range but its linked `time_block.date` falls outside (e.g. a recurring task created on day 1 of the range, but whose scheduled time block was from a prior period). In that case `task.time_block_id` is not in `tb_duration`, the dict `.get()` returns `0`, and the category hours and `hours_spent` fields are silently wrong.

**Impact:** Misleading data surfaced to the client in both `category_breakdown.hours` and `tasks[*].hours_spent`. The total_hours in the summary is unaffected (it sums all blocks in range, not via tasks), so the inconsistency would be visible if the frontend cross-checks.

**Fix options (choose one):**
- Restrict the task query to only include tasks whose `time_block__date` is also in range when a time block is present, OR
- Fetch any referenced time blocks that fall outside the window in a separate query (adds one query but stays within budget), OR
- Document the known limitation and return `null` for `hours_spent` when the block is not in the fetched set instead of silently returning `0`.

---

### Major

#### M-01 — `_block_duration_minutes` uses `date.today()` as the midnight-crossing anchor instead of `b['date']`

**File:** `server/api/views/agent/client_report_views.py`, lines 308–314

```python
def _block_duration_minutes(start_time, end_time):
    start = dt.combine(date.today(), start_time)
    end   = dt.combine(date.today(), end_time)
    if end < start:
        end += timedelta(days=1)
    ...
```

The model's own `duration_minutes` property uses `self.date` as the anchor (see `agent_scheduling.py` lines 125–131). The view uses `date.today()` instead. For pure duration computation this makes no mathematical difference — the date cancels out in the subtraction. But:

- It is semantically incorrect and misleading to any reader. The block's actual date is available in `b['date']` and should be used.
- If Django's TIME_ZONE is configured and the stored `TimeField` values are ever returned as time-zone-aware objects on a DST boundary, using today's wall-clock date instead of the block's actual date could produce an off-by-60-minute result for blocks near DST transitions.
- It diverges from the model's own implementation without explanation.

**Fix:** Pass `b['date']` into the helper and use it:

```python
def _block_duration_minutes(block_date, start_time, end_time):
    start = dt.combine(block_date, start_time)
    end   = dt.combine(block_date, end_time)
    ...
```

---

#### M-02 — Tests added to `server/api/tests.py` (monolith) instead of the spec's dedicated file

**Spec says:** `server/api/tests/test_client_report_api.py` (new file)
**Actual:** Tests appended to `server/api/tests.py`

This is a violation of the spec's TDD file layout. As `tests.py` grows it will become unmanageable. The spec explicitly calls for a separate file and references `pytest` fixtures (`agent_user`, `assigned_client`, `other_client`) — the implementation uses Django's `APITestCase` `setUp()` instead, which is a stylistic departure but acceptable. The file location issue is the real concern: future sections will each add more tests to the monolith instead of their own modules if this pattern is not corrected now.

**Fix:** Move the `ClientReportViewSection03Test` class to `server/api/tests/test_client_report_api.py` (creating the file and an `__init__.py` if needed).

---

#### M-03 — `agent` filter missing from the time blocks query

**File:** `server/api/views/agent/client_report_views.py`, lines 337–342

```python
time_blocks = list(
    AgentTimeBlock.objects.filter(
        client=client,
        date__range=(start_date, end_date),
    ).values('id', 'date', 'start_time', 'end_time')
)
```

The filter uses only `client` — not `agent`. If two agents are both assigned to the same client (one as `marketing_agent`, the other as `website_agent`), the report will aggregate time blocks from both agents, not just the requesting agent. The spec does not explicitly say "only the requesting agent's blocks", but the UI context (an agent viewing their own client report) implies agent-scoping. Without it, a marketing agent would see website agent hours added to their report.

**Recommendation:** Add `agent=agent` to the `AgentTimeBlock` filter. The same concern applies to the task query (line 345).

---

### Minor

#### m-01 — No validation that `start_date <= end_date`

**File:** `server/api/views/agent/client_report_views.py`, `_parse_date_range`

When both dates are provided explicitly, no check is made that `start_date <= end_date`. An inverted range silently returns empty aggregations (0 hours, 0 tasks) rather than a clear 400 error. This will confuse API consumers and produce blank UI panels with no error feedback.

**Fix:** After parsing both dates, add:

```python
if start_date > end_date:
    raise ValidationError({'detail': 'start_date must be on or before end_date.'})
```

---

#### m-02 — `total_hours` computation redundantly iterates `time_blocks` twice

**File:** Lines 365–369 and 378–381

`total_minutes` is computed by iterating `time_blocks` once (line 365), then `tb_duration` is built by iterating `time_blocks` again (line 378). These two passes can be merged into a single pass:

```python
tb_duration = {}
total_minutes = 0
for b in time_blocks:
    mins = _block_duration_minutes(b['date'], b['start_time'], b['end_time'])
    tb_duration[b['id']] = mins
    total_minutes += mins
```

This is a minor efficiency and clarity improvement — Python list iteration is fast, so it is not a performance bug, but it removes unnecessary duplication.

---

#### m-03 — `start_date > today` not guarded

If a caller passes a `start_date` in the future, `end_date` defaults to today (which is then less than `start_date`). This is caught by m-01's fix once implemented, but deserves a separate call-out because the "only start_date provided" branch currently produces a silently incorrect range.

---

#### m-04 — The `tasks_list_capped_at_200` test assertion is `assertLessEqual(len(...), 200)` not `assertEqual(len(...), 200)`

**File:** `server/api/tests.py`, line 165

The test creates 210 tasks and asserts `len(tasks) <= 200`. This will also pass if the endpoint returns only 10 tasks (e.g. if the query filter is too restrictive). A stricter assertion would be:

```python
self.assertEqual(len(response.data['tasks']), 200)
```

This ensures the cap applies exactly, not just "at most 200".

---

#### m-05 — `test_tasks_list_filtered_to_date_range` modifies `old_task` after creation

**File:** `server/api/tests.py`, lines 147–149

```python
old_task.completed_at = tz.now() - datetime.timedelta(days=91)
old_task.created_at = tz.now() - datetime.timedelta(days=91)
old_task.save()
```

`created_at` is declared as `default=timezone.now` (not `auto_now_add`), so setting it post-creation and calling `.save()` works. However, `updated_at` uses `auto_now=True`, so `.save()` will update `updated_at` to now, which is fine for this test. This pattern is acceptable but worth noting — if `created_at` is ever changed to `auto_now_add`, this test will silently stop working.

---

### Nitpick

#### n-01 — Import `from django.utils import timezone as tz` inside `setUp` and two test methods is inconsistent

The import is done inside `setUp` (and again inside individual test methods) rather than at the top of the test class or module. Move to module-level imports for consistency.

#### n-02 — `_parse_date_range` is a module-level function; consider making it a static method or standalone utility

The spec suggests a module-level function, so this matches the spec. No change needed — noted only because future contributors may not expect module-level helpers in a views file.

#### n-03 — Response uses `status=403` integer literal instead of `status.HTTP_403_FORBIDDEN`

**File:** Line 335

```python
return Response({'detail': 'Forbidden.'}, status=403)
```

DRF convention (and the rest of the codebase) uses `from rest_framework import status` and `status.HTTP_403_FORBIDDEN`. Minor style inconsistency.

---

## Positive Observations

1. **Python-level aggregation is the right call.** The spec correctly identified that `duration_minutes` is a `@property`, not a DB column, and the implementation correctly avoids ORM `Sum('duration_minutes')` (which would fail at runtime). Using `.values()` + Python loops is both correct and efficient.

2. **Zero N+1 risk.** The implementation fetches all time blocks and all tasks in two queries, then aggregates entirely in Python using `defaultdict`. No per-record database access occurs anywhere in the aggregation path.

3. **`_is_agent_assigned_to_client` is a clean, spec-faithful implementation.** It correctly checks both `marketing_agent_id` and `website_agent_id` using the PK comparison (not a queryset), which avoids any extra query.

4. **`_block_duration_minutes` correctly handles midnight-crossing blocks.** The `if end < start: end += timedelta(days=1)` guard mirrors the model's own `duration_minutes` property, which is the authoritative implementation.

5. **`_parse_date_range` covers all four input combinations** (both, start-only, end-only, neither) with a clear `ValidationError` on bad format. The docstring accurately describes the behaviour.

6. **Weekly and monthly breakdowns merge both block-keyed and task-keyed week/month sets** before sorting, so weeks with only completed tasks (and no blocks) still appear in the output. This is a subtle correctness detail the spec does not explicitly call out.

7. **Test coverage is comprehensive** for the happy paths. All spec acceptance criteria have a corresponding test. The `CaptureQueriesContext` performance test is a good addition that will catch regressions.

8. **URL pattern uses `<uuid:client_id>`** rather than `<str:>` or `<pk:>`, which means Django will return 404 automatically on malformed UUIDs without the view needing to catch a `ValueError`.

---

## Recommendation

**Approve with required changes before merge.**

The blocking items before this can ship:

1. **Fix C-01** — decide on a strategy for time blocks whose date falls outside the window but whose linked task is in range. The simplest fix is to add `time_block__date__range=(start_date, end_date)` to the category_breakdown sub-query and return `null` for `hours_spent` on tasks whose block is not in the fetched set.

2. **Fix M-01** — pass `b['date']` into `_block_duration_minutes` to match the model's own property.

3. **Fix M-02** — move the test file to `server/api/tests/test_client_report_api.py` per the spec.

4. **Fix M-03** — add `agent=agent` to both the time block and task queries to scope the report to the requesting agent's own work.

5. **Fix m-01** — add an `start_date > end_date` guard in `_parse_date_range`.

The remaining minor and nitpick items are optional clean-up that can be bundled into the same PR or deferred to a polish pass.
