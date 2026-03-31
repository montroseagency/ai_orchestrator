# Section 04 — Marketing Plan API

## Overview

This section adds two focused HTTP endpoints for the `MarketingPlan` data:

- **Agent GET** — reads the client's marketing plan including free-form strategy notes, content pillars, and audience personas.
- **Admin POST** — creates the plan if it does not yet exist, or updates the `strategy_notes` field on an existing plan.

These endpoints feed the `MarketingPlanTab` inside `ClientDetailHub` (Section 08) and are consumed by the `useClientMarketingPlan` React Query hook.

### Dependency

This section requires **Section 01 (Backend Migrations)** to be complete first. The `strategy_notes` field must exist on `MarketingPlan` before the serializer or endpoints can expose it.

---

## Background

The `MarketingPlan` model lives in `server/api/models/marketing_core.py`. It has a `OneToOneField` to `Client` via `related_name="marketing_plan"`. Related models:

- `ContentPillar` — FK to `MarketingPlan` via `related_name="pillars"`. Fields relevant here: `id`, `name`, `description`, `target_percentage`, `color`, `weight`, `is_active`.
- `AudiencePersona` — FK to `MarketingPlan` via `related_name="audiences"`. Fields relevant here: `id`, `name`, `description`.

The existing `MarketingPlanSerializer` in `server/api/serializers/marketing_core.py` already nests `pillars` and `audiences` read-only, but does **not** include `strategy_notes` (because that field does not yet exist — it is added in Section 01).

The existing `MarketingPlanViewSet` in `server/api/views/marketing/plan_views.py` handles the general marketing plan CRUD. The new endpoints are **separate** from that viewset — they are client-scoped views registered under the `agent/` and `admin/` URL prefixes.

Authorization pattern (matching `scheduling_views.py`):
- Agent check: `request.user.role == 'agent'` and `hasattr(request.user, 'agent_profile')`
- Admin check: `request.user.role == 'admin'`
- Client ownership: verify the client is assigned to the requesting agent (check `Client.marketing_agent == agent` or `Client.website_agent == agent` depending on department, or via the `ClientServiceSettings` join)

---

## Tests First

### Backend Tests

Create `server/api/tests/test_marketing_plan_api.py`.

Write these tests before implementing the views:

**Agent GET — happy path and auth:**

```python
def test_agent_get_returns_strategy_notes_pillars_audiences_updated_at():
    """GET /agent/clients/{id}/marketing-plan/ returns all four fields."""

def test_agent_get_returns_404_if_no_marketing_plan_exists():
    """When the client has no MarketingPlan record, return 404."""

def test_agent_get_returns_403_if_agent_not_assigned_to_client():
    """Agent who does not own the client cannot read the plan."""

def test_agent_get_returns_403_for_non_agent_user():
    """A client-role user cannot access this endpoint."""
```

**Admin POST — happy path and auth:**

```python
def test_admin_post_creates_marketing_plan_if_none_exists():
    """POST with strategy_notes creates a new MarketingPlan for the client."""

def test_admin_post_updates_strategy_notes_on_existing_plan():
    """POST when plan already exists updates strategy_notes, does not duplicate."""

def test_admin_post_returns_403_for_non_admin_users():
    """Agent or client role cannot call the admin write endpoint."""

def test_admin_post_validates_strategy_notes_is_string():
    """Sending a non-string value (e.g. integer) returns 400."""

def test_admin_post_allows_empty_string_strategy_notes():
    """Clearing strategy_notes by posting empty string is valid."""
```

**Frontend mock factory** (needed by Section 08 and Section 13):

```typescript
// In client/test-utils/scheduling.tsx (or a new test-utils file)
function createMockMarketingPlan(overrides?: Partial<MarketingPlanDetailResponse>): MarketingPlanDetailResponse
```

The factory must produce the full shape described in the Response Shape section below.

---

## Implementation

### New File: `server/api/views/agent/marketing_plan_views.py`

Create this file. It contains two class-based views:

**`AgentClientMarketingPlanView`** — handles `GET /agent/clients/{client_id}/marketing-plan/`

```python
class AgentClientMarketingPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        """
        Returns the MarketingPlan for the given client.
        The requesting user must be an agent assigned to this client.
        Returns 404 if the client has no MarketingPlan.
        Returns 403 if the agent is not assigned to this client.
        """
```

Authorization logic inside `get()`:
1. Verify `request.user.role == 'agent'` and `request.user.agent_profile` exists; otherwise return 403.
2. Fetch the `Client` by `client_id` (404 if not found).
3. Verify the client is assigned to the requesting agent. Use the same logic as `_get_agent_client_ids` in `scheduling_views.py` — check `marketing_agent` or `website_agent` FK, or the `ClientServiceSettings` join.
4. Fetch `client.marketing_plan` — return 404 with `{"detail": "No marketing plan found for this client."}` if `RelatedObjectDoesNotExist`.
5. Serialize with `MarketingPlanDetailSerializer` and return.

**`AdminClientMarketingPlanView`** — handles `POST /admin/clients/{client_id}/marketing-plan/`

```python
class AdminClientMarketingPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, client_id):
        """
        Creates or updates the MarketingPlan's strategy_notes for the client.
        Admin only. Uses get_or_create so it is safe to call when no plan exists.
        """
```

Logic inside `post()`:
1. Verify `request.user.role == 'admin'`; return 403 otherwise.
2. Validate that `request.data.get('strategy_notes')` is present and is a string; return 400 with `{"strategy_notes": "This field is required and must be a string."}` if not.
3. Fetch the `Client` (404 if not found).
4. `plan, _ = MarketingPlan.objects.get_or_create(client=client, defaults={'created_by': request.user})`
5. `plan.strategy_notes = request.data['strategy_notes']`
6. `plan.save(update_fields=['strategy_notes', 'updated_at'])`
7. Return serialized plan using `MarketingPlanDetailSerializer` with HTTP 200.

---

### Serializer: `MarketingPlanDetailSerializer`

Add to `server/api/serializers/marketing_core.py`.

This serializer is read-only (used by both agent GET and admin POST response). It extends the existing nested structure with the new `strategy_notes` field:

```python
class MarketingPlanDetailSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for the CRM marketing plan tab.
    Includes strategy_notes (added in Section 01 migration),
    nested pillars (ContentPillarSerializer), and nested audiences (AudiencePersonaSerializer).
    """
    pillars = ContentPillarSerializer(many=True, read_only=True)
    audiences = AudiencePersonaSerializer(many=True, read_only=True)

    class Meta:
        model = MarketingPlan
        fields = ['strategy_notes', 'pillars', 'audiences', 'updated_at']
        read_only_fields = ['strategy_notes', 'pillars', 'audiences', 'updated_at']
```

`ContentPillarSerializer` and `AudiencePersonaSerializer` already exist in `marketing_core.py`. The `pillars` list must only include active pillars (`is_active=True`). Handle this by overriding `get_pillars` as a `SerializerMethodField` or by filtering in the view queryset via `prefetch_related(Prefetch('pillars', queryset=ContentPillar.objects.filter(is_active=True)))`.

---

### Response Shape

```json
{
  "strategy_notes": "## Q2 Strategy\n\nFocus on short-form video...",
  "pillars": [
    {
      "id": "uuid",
      "name": "Educational Content",
      "description": "How-to posts and tutorials",
      "target_percentage": 40.0,
      "color": "#6366F1",
      "weight": 3,
      "is_active": true
    }
  ],
  "audiences": [
    {
      "id": "uuid",
      "name": "Small Business Owners",
      "description": "Ages 30–50, decision makers..."
    }
  ],
  "updated_at": "2026-03-15T10:22:00Z"
}
```

---

### URL Registration

Register both views in `server/api/urls.py`.

Find the block where `admin/clients/<uuid:client_id>/` paths are defined (around line 478). Add alongside those:

```python
# Marketing plan API (Section 04)
path(
    'agent/clients/<uuid:client_id>/marketing-plan/',
    AgentClientMarketingPlanView.as_view(),
    name='agent_client_marketing_plan',
),
path(
    'admin/clients/<uuid:client_id>/marketing-plan/',
    AdminClientMarketingPlanView.as_view(),
    name='admin_client_marketing_plan',
),
```

Import the two new views at the top of `urls.py`:

```python
from .views.agent.marketing_plan_views import (
    AgentClientMarketingPlanView, AdminClientMarketingPlanView
)
```

---

## Files to Create or Modify

| File | Action | Description |
|------|--------|-------------|
| `server/api/views/agent/marketing_plan_views.py` | **Created** | Both view classes |
| `server/api/serializers/marketing_core.py` | **Modified** | Added `MarketingPlanDetailSerializer` |
| `server/api/urls.py` | **Modified** | Registered two new URL paths and import |
| `server/api/tests.py` | **Modified** | Tests as `MarketingPlanAPISection04Test` class (deviation: tests in monolith not separate file) |

---

## Implementation Notes (Actual)

- Tests live in `tests.py` as `MarketingPlanAPISection04Test` (consistent with section 03 decision)
- Admin POST uses `transaction.atomic()` + `select_for_update()` to prevent race conditions (code review fix)
- Uses `prefetch_related_objects([plan], ...)` instead of re-fetch after save to stay at 3 queries for POST too (code review fix)
- Module-level `_ACTIVE_PILLARS_PREFETCH` constant avoids code duplication between views
- 10 tests pass: agent GET (4), admin POST (5), active pillars filter (1)

---

## Implementation Notes

- The `get_or_create` in the admin POST must pass `created_by=request.user` in `defaults` only. If the plan already exists the `created_by` is preserved untouched.
- The `save(update_fields=['strategy_notes', 'updated_at'])` ensures `auto_now` on `updated_at` fires even with the explicit `update_fields` list — Django's `auto_now` fields update whenever `save()` is called regardless of `update_fields`.
- Do **not** allow agents to write `strategy_notes`. The GET endpoint is intentionally read-only for agents. The admin POST endpoint is the only write path.
- The existing `MarketingPlanViewSet` (registered at `marketing-plans/`) remains unchanged. The new views are additive.
- Pillar filtering (`is_active=True`) should be done at the queryset level (use `Prefetch`) rather than in the serializer, to avoid N+1 queries.
- Use `select_related('client')` when fetching the plan and `prefetch_related` for pillars and audiences. The combined query should hit at most 3 database round-trips: client lookup, plan fetch, prefetch pillars+audiences.
