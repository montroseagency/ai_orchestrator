# Section 06: Category Management API

## Overview

This section adds a dedicated admin viewset for full `TaskCategory` CRUD with bulk reorder, and ensures the existing agent-facing category endpoint is correctly restricted to active categories only.

**No migration dependency.** This section is parallelizable and can be implemented independently of all other sections in this split.

**Blocks:** `section-10-admin-category-page` (the frontend page depends on these endpoints).

---

## Background and Current State

`TaskCategory` already exists. The relevant parts of the current codebase:

- **Model:** `server/api/models/agent_scheduling.py` — `TaskCategory` has `id` (UUID), `name`, `slug` (auto-generated, read-only), `color`, `icon`, `department`, `requires_review`, `is_active`, `sort_order`, `created_by`, `created_at`, `updated_at`.
- **Serializer:** `server/api/serializers/agent_scheduling.py` — `TaskCategorySerializer` exposes all fields; `slug`, `created_at`, `updated_at` are read-only.
- **Agent viewset:** `AgentTaskCategoryViewSet` in `server/api/views/agent/scheduling_views.py` — already filters `is_active=True`. No change needed here.
- **Admin viewset:** `AdminTaskCategoryViewSet` in the same file — already a `ModelViewSet` with `perform_destroy` doing a soft-delete (`is_active=False`). **However**, it is missing the `reorder` custom action and uses `TaskCategorySerializer` (which includes all fields including `created_by`, `requires_review`, etc.). A dedicated `TaskCategoryAdminSerializer` should be used instead.
- **URL registration:** `server/api/urls.py` — both viewsets already registered at `agent/schedule/task-categories` and `admin/task-categories`.

**Implemented in-place:** `AdminTaskCategoryViewSet` was enhanced directly in `scheduling_views.py` (no new file). `TaskCategoryAdminSerializer` was added to `serializers/agent_scheduling.py`. This avoided changing URL registrations and kept the diff minimal.

---

## What to Build

### 1. `TaskCategoryAdminSerializer`

Add to `server/api/serializers/agent_scheduling.py`:

```python
class TaskCategoryAdminSerializer(serializers.ModelSerializer):
    """Admin-facing serializer for TaskCategory.

    Exposes the fields needed by the admin category management page.
    slug is auto-generated (read-only). created_by, requires_review,
    created_at, updated_at are excluded from the admin edit surface.
    """
    class Meta:
        model = TaskCategory
        fields = ['id', 'name', 'slug', 'color', 'icon', 'department', 'sort_order', 'is_active']
        read_only_fields = ['id', 'slug']
```

### 2. `AdminTaskCategoryViewSet` — add `reorder` action

Update the existing `AdminTaskCategoryViewSet` in `server/api/views/agent/scheduling_views.py`:

- Switch to `TaskCategoryAdminSerializer`
- Add a `reorder` custom router action
- Keep the existing `perform_destroy` soft-delete logic
- Keep the existing `perform_create` that sets `created_by`

Stub signatures:

```python
class AdminTaskCategoryViewSet(viewsets.ModelViewSet):
    """Admin-facing: full CRUD + bulk reorder for task categories.

    GET    /admin/task-categories/          → list all (including inactive)
    POST   /admin/task-categories/          → create new
    PATCH  /admin/task-categories/{id}/     → update fields
    DELETE /admin/task-categories/{id}/     → soft-delete (is_active=False)
    PATCH  /admin/task-categories/reorder/  → bulk update sort_order
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = TaskCategoryAdminSerializer
    queryset = TaskCategory.objects.all().order_by('sort_order', 'name')

    def perform_create(self, serializer):
        """Set created_by to the requesting admin user."""

    def perform_destroy(self, instance):
        """Soft-delete: set is_active=False, do not remove the record."""

    @action(detail=False, methods=['patch'], url_path='reorder')
    def reorder(self, request):
        """Bulk-update sort_order for all categories in a single transaction.

        Body: { "ordered_ids": ["uuid1", "uuid2", ...] }

        Sets sort_order=0 for the first ID, sort_order=1 for the second, etc.
        Uses transaction.atomic() to wrap all updates.
        Returns 200 with the updated category list on success.
        Returns 400 if ordered_ids is missing, not a list, or contains unknown IDs.
        """
```

**Reorder implementation notes:**
- Accept `{ ordered_ids: list[str] }` in the request body.
- Validate that `ordered_ids` is a non-empty list. Return HTTP 400 if missing or wrong type.
- Fetch all `TaskCategory` objects whose IDs are in `ordered_ids`. Return HTTP 400 if any ID is unknown.
- Inside `transaction.atomic()`, loop over `ordered_ids` and call `TaskCategory.objects.filter(id=cat_id).update(sort_order=index)` for each position. Do not use a bulk `update()` on a queryset with a single `.update()` call — do it per-ID so each gets a distinct `sort_order`.
- Return the full updated category list (all categories, not just the reordered ones) serialized with `TaskCategoryAdminSerializer`.

### 3. Agent-facing viewset — verify `is_active=True` filter

The existing `AgentTaskCategoryViewSet.get_queryset()` already filters `is_active=True`. Confirm this is in place and add a test. No code change should be needed, but if the filter is missing it must be added here.

---

## Endpoints Summary

| Method | URL | Auth | Behavior |
|--------|-----|------|----------|
| GET | `/admin/task-categories/` | IsAdmin | List all categories (including inactive), ordered by `sort_order, name` |
| POST | `/admin/task-categories/` | IsAdmin | Create new category; `slug` auto-generated from `name`; `created_by` set from request user |
| PATCH | `/admin/task-categories/{id}/` | IsAdmin | Update `name`, `color`, `icon`, `department`, `is_active`, `sort_order` |
| DELETE | `/admin/task-categories/{id}/` | IsAdmin | Soft-delete: sets `is_active=False`, record remains in DB |
| PATCH | `/admin/task-categories/reorder/` | IsAdmin | Bulk `sort_order` update: body `{ ordered_ids: [...] }` |
| GET | `/agent/schedule/task-categories/` | IsAnyAgent | List active (`is_active=True`) categories filtered by agent's department |

**Note on slug uniqueness:** The `name` field has `unique=True` on the model. Duplicate name validation is handled by Django's model validation — the serializer will surface this as a 400 with a `name` field error. No additional uniqueness check is needed in the view.

---

## Tests to Write First

File: `server/api/tests.py` (extend the existing `TaskCategoryViewSetSection07Test` class, or add a new `TaskCategoryAdminSection06Test` class alongside it).

### Backend tests (pytest / APITestCase)

```python
# Fixture setup needed:
# - admin user (role='admin' or is_staff=True, matching IsAdmin permission check)
# - agent user with department set
# - 3+ TaskCategory instances with varying is_active and sort_order values
```

**GET `/admin/task-categories/`:**
- Returns all categories including those with `is_active=False`
- Response includes `id`, `name`, `slug`, `color`, `icon`, `department`, `sort_order`, `is_active`
- Returns 403 for non-admin (agent) users

**POST `/admin/task-categories/`:**
- Creates a new category; response includes auto-generated `slug`
- Returns 400 if `name` is missing or blank
- Returns 400 on duplicate name (slug collision handled by model uniqueness)

**PATCH `/admin/task-categories/{id}/`:**
- Updates category fields and returns updated data
- Returns 400 for invalid field values (e.g., color not a valid hex string — if validated)
- Returns 403 for non-admin users

**DELETE `/admin/task-categories/{id}/`:**
- Sets `is_active=False` on the instance; record still exists in DB
- Returns 204; subsequent GET of the same ID still returns the record (now with `is_active=False`)
- Returns 403 for non-admin users

**PATCH `/admin/task-categories/reorder/`:**
- Provide `ordered_ids` with N category IDs; verify each gets `sort_order` = its index in the list
- All updates happen (verify all N categories have updated `sort_order`)
- Returns 400 if `ordered_ids` is missing from body
- Returns 400 if `ordered_ids` contains an unknown UUID
- Returns 403 for non-admin users

**GET `/agent/schedule/task-categories/`:**
- Returns only `is_active=True` categories (inactive categories not in response)
- Returns 403 for unauthenticated requests

### Frontend mock factory (for `section-10-admin-category-page` and `section-13-tests`)

Add to `client/test-utils/scheduling.tsx`:

```typescript
export function createMockTaskCategory(overrides?: Partial<TaskCategoryItem>): TaskCategoryItem {
    /**
     * Returns a TaskCategoryItem with sensible defaults.
     * Override any field by passing partial values.
     */
}
```

The `TaskCategoryItem` TypeScript type should be defined in the frontend API types file (wherever agent scheduling types live) with fields: `id`, `name`, `slug`, `color`, `icon`, `department`, `sort_order`, `is_active`.

---

## Files to Create or Modify

| File | Action | Notes |
|------|--------|-------|
| `server/api/serializers/agent_scheduling.py` | Modify | Add `TaskCategoryAdminSerializer` class |
| `server/api/views/agent/scheduling_views.py` | Modify | Update `AdminTaskCategoryViewSet`: use new serializer, add `reorder` action |
| `server/api/tests.py` | Modify | Add/extend category management tests |
| `client/test-utils/scheduling.tsx` | Modify | Add `createMockTaskCategory` mock factory |

**Optional (if team prefers clean file separation):**
- `server/api/admin/category_views.py` — move `AdminTaskCategoryViewSet` here, import into `urls.py`

If the viewset is moved to a new file, update the import in `server/api/urls.py` (line ~163 where `AdminTaskCategoryViewSet` is currently imported from `scheduling_views`).

---

## Key Constraints

- **Soft-delete only.** `TaskCategory` records referenced by existing `AgentGlobalTask.task_category_ref` (FK with `SET_NULL`) must never be hard-deleted. Deleting sets `is_active=False`; the record stays. This already exists in `perform_destroy` — preserve it.
- **Agent endpoint must stay `is_active=True` filtered.** Deactivated categories must not appear in agent task creation forms or filter bars. The existing filter in `AgentTaskCategoryViewSet.get_queryset()` handles this — do not remove it.
- **Reorder is atomic.** All `sort_order` updates for a single reorder request must succeed or all must fail. Use `transaction.atomic()`.
- **`TaskCategoryAdminSerializer` exposes `id`, `name`, `slug`, `color`, `icon`, `department`, `sort_order`, `is_active` only.** The `created_by`, `requires_review`, `created_at`, `updated_at` fields from the base `TaskCategorySerializer` are not needed in the admin CRUD surface.
