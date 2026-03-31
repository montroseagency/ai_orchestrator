# Section 01: Backend Migrations

## Overview

This section adds three schema changes to existing Django models and updates two serializers. No new models are created. No data migrations are needed — existing rows receive empty string defaults automatically. This section has no dependencies and can be implemented immediately.

**Estimated scope:** 3 migration files, 2 serializer edits, 5 tests.

---

## Background

### Models being changed

**`AgentGlobalTask`** — `server/api/models/agent_scheduling.py` (line 133)
The task model already has a 4-state `Status` enum: `todo`, `in_progress`, `in_review`, `done`. The approval reject workflow needs to persist admin feedback on the task so the agent can read it. Currently there is no field for this. The field must be cleared when the agent re-submits.

**`MarketingPlan`** — `server/api/models/marketing_core.py` (line 34)
The model exists as a `OneToOneField(Client)` with `ContentPillar` (via `pillars`) and `AudiencePersona` (via `audiences`) related sets. It does not currently have a free-form strategy document field. The Marketing Plan tab (built in section 08) needs this field to render strategy markdown.

**`AgentTimeBlock`** — `server/api/models/agent_scheduling.py` (line 63)
The model has `client = ForeignKey('Client', ...)` (line 96) and `date = DateField(db_index=True)` (line 88). The client report aggregation (section 03) filters by `client=clientId` AND `date__range=...` in combination. Currently there is only a single-column index on `date`. A composite `(client, date)` index enables the query planner to satisfy both filter columns from a single index scan rather than scanning all rows.

### Serializers being changed

**`AgentGlobalTaskReadSerializer`** — `server/api/serializers/agent_scheduling.py` (line 118)
This is the GET serializer used for list/detail responses. `review_feedback` must be readable by agents so they can see rejection notes. It must be **read-only** in this serializer (agents read feedback, they do not write it — that is done by the admin approval endpoint in section 05).

**`AgentGlobalTaskWriteSerializer`** — `server/api/serializers/agent_scheduling.py` (line 150)
This is the POST/PATCH serializer. `review_feedback` must NOT appear in this serializer — agents cannot set feedback themselves.

**`MarketingPlanSerializer`** — `server/api/serializers/marketing_core.py` (line 53)
The existing serializer exposes `id`, `client`, `name`, `timezone`, `is_active`, `created_by`, `created_at`, `updated_at`, `pillars`, and `audiences`. Add `strategy_notes` to the `fields` list. It is writable (admins set it via the section 04 endpoint).

**Note:** There is also a basic `AgentGlobalTaskSerializer` at line 57 of `agent_scheduling.py` (the older write serializer used in some views). Check whether it also needs `review_feedback` added — if it is used in any agent-facing GET response, add it as `read_only=True`. If it is purely a write serializer, leave it as-is.

---

## Tests to Write First

Create `server/api/tests/test_migrations_01.py` with a `pytest-django` test class. Run with: `cd server && pytest api/tests/test_migrations_01.py -v`

### Test stubs

```python
# server/api/tests/test_migrations_01.py

import pytest
from django.test import TestCase

class TestAgentGlobalTaskReviewFeedback(TestCase):

    def test_review_feedback_field_exists_on_model(self):
        """AgentGlobalTask has a review_feedback attribute."""

    def test_review_feedback_default_is_empty_string(self):
        """Newly created AgentGlobalTask has review_feedback=''."""

    def test_review_feedback_in_read_serializer(self):
        """AgentGlobalTaskReadSerializer includes review_feedback as a read-only field."""

    def test_review_feedback_not_in_write_serializer(self):
        """AgentGlobalTaskWriteSerializer does not expose review_feedback."""


class TestMarketingPlanStrategyNotes(TestCase):

    def test_strategy_notes_field_exists_on_model(self):
        """MarketingPlan has a strategy_notes attribute."""

    def test_strategy_notes_default_is_empty_string(self):
        """Newly created MarketingPlan has strategy_notes=''."""

    def test_strategy_notes_in_serializer(self):
        """MarketingPlanSerializer includes strategy_notes in its fields."""


class TestAgentTimeBlockClientDateIndex(TestCase):

    def test_client_date_filter_returns_correct_results(self):
        """
        AgentTimeBlock filtered by client= and date__range= returns only
        matching records. Creates 3 time blocks: 2 for client A in range,
        1 for client B in range. Asserts queryset count == 2.
        """
```

---

## What to Build

### 1. Migration: `review_feedback` on `AgentGlobalTask`

**File:** `server/api/migrations/0075_agentglobaltask_review_feedback.py`

Add `review_feedback = models.TextField(blank=True, default='')` to `AgentGlobalTask`.

Use `migrations.AddField` with:
- `model_name='agentglobaltask'`
- `name='review_feedback'`
- `field=models.TextField(blank=True, default='')`

Dependencies: `[('api', '0074_recurringtasktemplate')]`

### 2. Migration: `strategy_notes` on `MarketingPlan`

**File:** `server/api/migrations/0076_marketingplan_strategy_notes.py`

Add `strategy_notes = models.TextField(blank=True, default='')` to `MarketingPlan`.

Use `migrations.AddField` with:
- `model_name='marketingplan'`
- `name='strategy_notes'`
- `field=models.TextField(blank=True, default='')`

Dependencies: `[('api', '0075_agentglobaltask_review_feedback')]`

### 3. Migration: composite index on `AgentTimeBlock`

**File:** `server/api/migrations/0077_agentimeblock_client_date_index.py`

Add `Index(fields=['client', 'date'])` to `AgentTimeBlock.Meta.indexes`.

Use `migrations.AddIndex` with:
- `model_name='agenttimeblock'`
- `index=models.Index(fields=['client', 'date'], name='api_agenttime_client_date_idx')`

Dependencies: `[('api', '0076_marketingplan_strategy_notes')]`

### 4. Serializer update: `AgentGlobalTaskReadSerializer`

**File:** `server/api/serializers/agent_scheduling.py`

In `AgentGlobalTaskReadSerializer.Meta.fields` (line 129), add `'review_feedback'` to the fields list. Since `read_only_fields = fields` is already set on this serializer, the field will automatically be read-only — no extra configuration needed.

### 5. Serializer update: `MarketingPlanSerializer`

**File:** `server/api/serializers/marketing_core.py`

In `MarketingPlanSerializer.Meta.fields` (line 59), add `'strategy_notes'` to the fields list. Place it after `'is_active'` and before `'created_by'` for logical grouping. It is writable by default (admin-facing write uses this serializer in section 04).

---

## Model field signatures (for reference)

```python
# AgentGlobalTask — add after existing fields, before class Meta
review_feedback = models.TextField(blank=True, default='')

# MarketingPlan — add after is_active, before created_by
strategy_notes = models.TextField(blank=True, default='')
```

---

## Verification

After applying migrations, confirm:

```bash
cd server
python manage.py migrate --check    # should show no pending migrations
python manage.py shell -c "
from api.models.agent_scheduling import AgentGlobalTask
from api.models.marketing_core import MarketingPlan
print(hasattr(AgentGlobalTask, 'review_feedback'))   # True
print(hasattr(MarketingPlan, 'strategy_notes'))       # True
"
```

Check the composite index exists in the database:
```bash
python manage.py dbshell
# SQLite: .schema api_agenttimeblock
# Postgres: \d api_agenttimeblock
# Look for index on (client_id, date)
```

---

## Dependencies

This section has no upstream dependencies. Sections that depend on this section completing:

- **Section 03** (Client Report API) — needs `review_feedback` in the serializer
- **Section 04** (Marketing Plan API) — needs `strategy_notes` on `MarketingPlan`
- **Section 05** (Approval Queue API) — needs `review_feedback` field to store rejection notes
- **Section 11** (Agent Re-submission) — needs `review_feedback` to be clearable
