# Section 03: Client Report API

## Overview

Build a dedicated Django read endpoint that aggregates `AgentTimeBlock` and `AgentGlobalTask` data for a specific client over a requested date range. This is the data source for the Time & Capacity tab (Section 08) and the export endpoint (Section 07). Centralising the aggregation here avoids duplicating query logic on the frontend and keeps the computation queryable.

**Depends on:** `section-01-backend-migrations` — Migration 3 adds the `(client, date)` composite index on `AgentTimeBlock` that this view relies on for performance. The `review_feedback` field added in Migration 1 does not affect this section directly, but the serializer update in Section 01 (adding `review_feedback` to `AgentGlobalTaskReadSerializer`) is a prerequisite for the `tasks` list in the response.

**Sections that depend on this one:** `section-07-export-api`, `section-08-client-detail-hub`

---

## Files to Create / Modify

| File | Change |
|---|---|
| `server/api/agent/client_report_views.py` | **Create** — new `ClientReportView` class-based view |
| `server/api/urls.py` | Register two new `path()` entries under the `agent/` prefix |
| `server/api/tests/test_client_report_api.py` | **Create** — backend tests (write first) |

> Note: `server/api/agent/` may not exist yet. Create `__init__.py` alongside `client_report_views.py` if the directory is new.

---

## Tests First

Tests live in `server/api/tests/test_client_report_api.py`. Write and run these tests against stubs before implementing the view logic.

```python
# server/api/tests/test_client_report_api.py
import pytest
from django.utils import timezone
from datetime import date, timedelta


# --- Authorization ---

def test_client_report_returns_403_if_agent_not_assigned_to_client(api_client, agent_user, other_client):
    """GET /agent/clients/{id}/report/ must return 403 when the requesting agent
    is not assigned to the given client."""

def test_client_report_returns_404_if_client_does_not_exist(api_client, agent_user):
    """GET /agent/clients/{random_uuid}/report/ must return 404."""

def test_client_report_returns_403_for_unauthenticated_requests(api_client, assigned_client):
    """Endpoint must return 403 (not 200 or 401) for unauthenticated requests."""


# --- Aggregation correctness ---

def test_days_worked_counts_distinct_dates(api_client, agent_user, assigned_client, db):
    """3 time blocks on 2 distinct dates → days_worked=2 in summary."""

def test_total_hours_sums_duration_minutes_divided_by_60(api_client, agent_user, assigned_client, db):
    """Two time blocks of 90 mins each → total_hours=3.0."""

def test_weekly_breakdown_groups_by_iso_week(api_client, agent_user, assigned_client, db):
    """Time blocks in week 1 and week 2 appear in separate weekly_breakdown entries."""

def test_category_breakdown_groups_hours_by_task_category(api_client, agent_user, assigned_client, db):
    """Time blocks linked to tasks in two different categories → two entries in
    category_breakdown, each with correct hours and task_count."""

def test_tasks_list_filtered_to_date_range(api_client, agent_user, assigned_client, db):
    """Tasks with completed_at or created_at outside the requested range must
    not appear in the tasks list."""

def test_tasks_list_capped_at_200_records(api_client, agent_user, assigned_client, db):
    """When more than 200 tasks exist in the range, the response returns exactly 200."""

def test_unique_categories_contains_category_names_from_tasks_in_range(api_client, agent_user, assigned_client, db):
    """summary.unique_categories lists the distinct category names from tasks
    within the date range."""

def test_monthly_summary_groups_by_calendar_month(api_client, agent_user, assigned_client, db):
    """Time blocks spanning two calendar months appear in two monthly_summary entries."""


# --- Date range defaults ---

def test_default_date_range_is_last_90_days(api_client, agent_user, assigned_client, db):
    """With no query params, period.start = today - 90 days, period.end = today."""

def test_only_end_date_provided_defaults_start_to_90_days_before(api_client, agent_user, assigned_client, db):
    """?end_date=2026-03-29 → start_date=2025-12-29 (90 days prior)."""

def test_only_start_date_provided_defaults_end_to_today(api_client, agent_user, assigned_client, db):
    """?start_date=2026-01-01 → end_date=today."""


# --- Performance ---

def test_report_query_count_is_bounded(api_client, agent_user, assigned_client, django_assert_num_queries, db):
    """Report endpoint must complete in ≤ 6 database queries regardless of data volume
    (assert with django_assert_num_queries)."""
```

Fixture notes:
- `agent_user` — an authenticated `User` with `role='agent'` and an `Agent` profile assigned to `assigned_client`.
- `assigned_client` — a `Client` linked to `agent_user`'s `Agent` profile (via `marketing_agent` or `website_agent`).
- `other_client` — a `Client` NOT assigned to `agent_user`.
- Create `AgentTimeBlock` instances using Django ORM or a factory (e.g. `pytest-factoryboy`) with explicit `client`, `agent`, `date`, `start_time`, and `end_time` values so aggregation math is deterministic.

---

## Implementation

### Endpoint Contract

```
GET /agent/clients/{id}/report/
Query params: start_date (YYYY-MM-DD, optional), end_date (YYYY-MM-DD, optional)
Auth: IsAuthenticated; requesting agent must be assigned to the client
Default range: last 90 days from today
```

Response shape:

```json
{
  "client": { "id": "...", "name": "...", "company": "..." },
  "period": { "start": "2025-12-29", "end": "2026-03-29" },
  "summary": {
    "total_tasks": 42,
    "completed_tasks": 30,
    "in_progress_tasks": 8,
    "total_hours": 120.5,
    "days_worked": 45,
    "unique_categories": ["Copywriting", "Strategy"]
  },
  "category_breakdown": [
    { "category": "Copywriting", "hours": 80.0, "task_count": 25 }
  ],
  "weekly_breakdown": [
    { "week_start": "2026-03-23", "hours": 12.5, "tasks_completed": 3 }
  ],
  "monthly_summary": [
    { "month": "2026-03", "days": 15, "hours": 60.0, "tasks_completed": 18 }
  ],
  "tasks": [
    {
      "id": "...", "title": "...", "status": "done",
      "category": "Copywriting", "hours_spent": 2.5, "completed_at": "2026-03-15"
    }
  ]
}
```

### File: `server/api/agent/client_report_views.py`

Create this file. The view should be a `APIView` subclass (or function-based view with `@api_view`). Follow the same permission and agent-resolution pattern already used in `server/api/views/agent/scheduling_views.py` — reuse `IsAnyAgent` (import it from there or copy the class) and `_get_agent(request)`.

```python
from datetime import date, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncWeek, TruncMonth
from django.shortcuts import get_object_or_404
from django.utils import timezone

from api.models import AgentTimeBlock, AgentGlobalTask, Client
# Import IsAnyAgent and _get_agent from scheduling_views or define inline


class ClientReportView(APIView):
    """Aggregate time and task data for a single client over a date range.

    Auth: IsAuthenticated + agent must be assigned to the requested client.
    Returns 403 if agent is not assigned; 404 if client does not exist.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        """Return aggregated report data for client_id.

        Steps:
        1. Resolve start_date / end_date from query params (apply defaults).
        2. Fetch the client; verify the requesting agent is assigned to it (return 403 if not).
        3. Filter AgentTimeBlock by client=client_id and date__range=(start, end).
        4. Compute summary stats, category_breakdown, weekly_breakdown, monthly_summary.
        5. Fetch tasks with created_at or completed_at in range; cap at 200.
        6. Return assembled response dict.
        """
```

### Authorization Check

The agent assignment check must verify that the requesting agent is actually assigned to the client. Replicate the logic from `_get_agent_client_ids` in `scheduling_views.py`:

```python
def _is_agent_assigned_to_client(agent, client):
    """Return True if the agent is assigned to the client (marketing or website)."""
    if agent.department == 'marketing':
        return client.marketing_agent_id == agent.pk
    elif agent.department == 'website':
        return client.website_agent_id == agent.pk
    return False
```

Return `Response({'detail': 'Forbidden.'}, status=403)` if the check fails.

### Date Range Parsing

```python
def _parse_date_range(request):
    """Parse start_date / end_date from query params. Apply defaults:
    - No params → (today - 90d, today)
    - Only end_date → (end_date - 90d, end_date)
    - Only start_date → (start_date, today)
    Returns (start_date, end_date) as date objects.
    Raises ValidationError (400) if a provided date string is not valid YYYY-MM-DD.
    """
```

### Aggregation Queries

All time-block queries must filter on both `client=client_id` and `date__range=(start_date, end_date)`. Use the following ORM patterns:

**`days_worked`:**
```python
AgentTimeBlock.objects.filter(
    client=client, date__range=(start_date, end_date)
).dates('date', 'day').count()
```

**`total_hours`:**
```python
result = AgentTimeBlock.objects.filter(
    client=client, date__range=(start_date, end_date)
).aggregate(total_minutes=Sum('duration_minutes'))
total_hours = (result['total_minutes'] or 0) / 60
```

> `duration_minutes` on `AgentTimeBlock` is a `@property` — it cannot be used in ORM `Sum()` directly. Instead, compute `duration_minutes` as an annotated expression: `ExpressionWrapper((end_time - start_time in minutes), output_field=IntegerField())`, or pre-calculate in Python after a `.values()` fetch. The simplest approach that avoids N+1: fetch all matching blocks with `.values('date', 'start_time', 'end_time', 'client_task__task_category_ref__name')` and aggregate in Python.

**`weekly_breakdown`:**
```python
from django.db.models.functions import TruncWeek

AgentTimeBlock.objects.filter(
    client=client, date__range=(start_date, end_date)
).annotate(week=TruncWeek('date'))
.values('week')
.annotate(total_minutes=Sum(...))
.order_by('week')
```

**`monthly_summary`:**
Same pattern using `TruncMonth('date')` instead of `TruncWeek`.

**`category_breakdown`:**
Join time blocks to their linked tasks and then to categories. Since `AgentTimeBlock` does not have a direct category FK, join via the tasks linked to each time block through `AgentGlobalTask.time_block` (the `time_block` FK on `AgentGlobalTask` points back to a `AgentTimeBlock`). Group by `task_category_ref__name`.

```python
AgentGlobalTask.objects.filter(
    client=client,
    time_block__date__range=(start_date, end_date),
    time_block__isnull=False,
).select_related('task_category_ref', 'time_block')
.values('task_category_ref__name')
.annotate(task_count=Count('id'))
# hours per category: sum the time block durations linked to tasks in each category
```

Because `duration_minutes` is a property (not a DB column), fetch the time block start/end times and compute in Python rather than in the ORM.

**`tasks` list:**
```python
AgentGlobalTask.objects.filter(
    client=client,
).filter(
    Q(created_at__date__range=(start_date, end_date)) |
    Q(completed_at__date__range=(start_date, end_date))
).select_related('task_category_ref', 'time_block')
.order_by('-completed_at', '-created_at')[:200]
```

For each task, compute `hours_spent` by summing `time_block.duration_minutes / 60` if `time_block` is set, else `0`.

### URL Registration

Add to `server/api/urls.py` (in the `# Agent endpoints` block):

```python
from api.agent.client_report_views import ClientReportView

# inside urlpatterns:
path('agent/clients/<uuid:client_id>/report/', ClientReportView.as_view(), name='agent_client_report'),
```

The export variant (`/agent/clients/{id}/report/export/`) is registered by Section 07, not here.

---

## Key Technical Decisions

| Decision | Choice | Reason |
|---|---|---|
| `duration_minutes` is a `@property` | Aggregate in Python, not ORM `Sum()` | The property computes from `start_time`/`end_time`; not a DB column |
| Task date filter | `created_at OR completed_at` in range | Captures tasks started or finished in the period |
| Tasks cap | `[:200]` slice | Keeps JSON response size bounded; export endpoint returns full dataset |
| Authorization | Inline check against `marketing_agent_id` / `website_agent_id` | Consistent with `_get_agent_client_ids` pattern already in codebase |
| Date defaults | Python-level, not Django queryset | Simple; avoids over-engineering |

---

## Acceptance Criteria

- [x] `GET /agent/clients/{id}/report/` returns 200 with the full response shape for an assigned agent.
- [x] Returns 403 when the requesting agent is not assigned to the client.
- [x] Returns 404 when the client UUID does not exist.
- [x] `summary.days_worked` counts distinct dates (not block count).
- [x] `summary.total_hours` is a float (minutes / 60), not an integer.
- [x] `weekly_breakdown` entries are ordered chronologically by `week_start`.
- [x] `monthly_summary` entries are ordered chronologically by `month`.
- [x] `tasks` list is capped at 200 items.
- [x] Default date range (no params) spans today − 90 days to today.
- [x] All backend tests pass (15 tests in `ClientReportViewSection03Test` class in `server/api/tests.py`).
- [x] Query count is bounded (≤ 6 DB queries for a standard request).

---

## Implementation Notes (Actual vs Planned)

### File paths (deviations from plan)
| Planned | Actual | Reason |
|---|---|---|
| `server/api/agent/client_report_views.py` | `server/api/views/agent/client_report_views.py` | Existing convention — all agent views live in `views/agent/`; `api/agent/` directory doesn't exist |
| `server/api/tests/test_client_report_api.py` | `server/api/tests.py` (class `ClientReportViewSection03Test`) | `tests/` directory would shadow existing `tests.py` module; tests added as a new class |

### Aggregation approach
`duration_minutes` is a `@property` — aggregation done entirely in Python after a `.values()` fetch. Helper function `_block_duration_minutes(block_date, start_time, end_time)` takes the actual block date (not `date.today()`) for DST correctness.

### Scope decision
The report aggregates ALL agents' time blocks for the client (full client view), not scoped to the requesting agent. This was confirmed with the user.

### Extra validation added (from code review)
`_parse_date_range` validates `start_date <= end_date` when both params are provided, returning 400.

### Tests: 15 pass
Authorization (3), aggregation correctness (6), date range defaults (3), performance bound (1), tasks cap (1), categories (1).
