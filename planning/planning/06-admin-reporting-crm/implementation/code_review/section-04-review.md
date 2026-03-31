# Code Review: Section 04 — Marketing Plan API

**Reviewer:** Senior Django/Python Code Review
**Date:** 2026-03-30
**Files changed:**
- `server/api/serializers/marketing_core.py`
- `server/api/views/agent/marketing_plan_views.py`
- `server/api/urls.py`
- `server/api/tests.py`

---

## Summary

The implementation is largely correct and well-structured. The happy path for both GET and POST works as specified: active-pillar filtering is correctly done via `Prefetch`, the `get_or_create` pattern on POST is sound, and the query structure stays within the ≤3 round-trip budget for the GET path. Several issues range from a latent race condition on POST, to a fragile auth guard, to a missing `name` default in `get_or_create` that could cause a DB-level integrity error in some schema configurations. Test coverage is good overall but has a gap on the integer-validation assertion logic.

---

## Issues Found

### Critical

#### C-1: `get_or_create` missing required `name` field — potential IntegrityError on plan creation

**File:** `marketing_plan_views.py`, line 299
**Code:**
```python
plan, _ = MarketingPlan.objects.get_or_create(
    client=client,
    defaults={'created_by': request.user},
)
```

`MarketingPlan` has a `name` field (confirmed by test fixture `_make_plan` using `name='Plan04'`). If `name` has `blank=False` and no DB default, the `INSERT` path of `get_or_create` will raise an `IntegrityError` or `django.db.utils.IntegrityError` depending on the DB backend, surfacing as an unhandled 500.

**Fix:** Add a `name` default to `defaults`, e.g.:
```python
defaults={
    'created_by': request.user,
    'name': 'Marketing Plan',
},
```
Or, if `name` has a model-level default, document that assumption explicitly in a comment.

---

### Major

#### M-1: Race condition on POST — double-save pattern not atomic

**File:** `marketing_plan_views.py`, lines 299–304
**Code:**
```python
plan, _ = MarketingPlan.objects.get_or_create(
    client=client,
    defaults={'created_by': request.user},
)
plan.strategy_notes = strategy_notes
plan.save(update_fields=['strategy_notes', 'updated_at'])
```

Under concurrent POST requests for the same `client_id`, two threads can both pass the `get_or_create` lookup (one gets `created=True`, the other gets the newly created object) and then both call `save()`. This is a TOCTOU race. The second save silently overwrites the first.

While low-probability in practice (admin-only endpoint, single client), the spec explicitly calls out `get_or_create`, so this is the intended pattern — but a `update_or_create` combining both operations is safer:
```python
plan, _ = MarketingPlan.objects.update_or_create(
    client=client,
    defaults={
        'strategy_notes': strategy_notes,
        # only set created_by on insert; update_or_create doesn't support create_defaults
        # until Django 4.2 — see M-1 note below
    },
)
```
For Django < 4.2, the split pattern is acceptable but should be wrapped in `select_for_update()`:
```python
with transaction.atomic():
    plan, _ = MarketingPlan.objects.select_for_update().get_or_create(...)
    plan.strategy_notes = strategy_notes
    plan.save(update_fields=['strategy_notes', 'updated_at'])
```

#### M-2: POST re-fetch query is wasteful and returns stale `updated_at`

**File:** `marketing_plan_views.py`, lines 307–315
After `plan.save()`, the code does a full re-fetch with `prefetch_related` to get pillars and audiences. But because `strategy_notes` was just set and `updated_at` is a `auto_now` field (typical pattern), the `plan` object in memory already has the correct `strategy_notes`. The re-fetch is needed only for pillars and audiences.

More importantly: if `updated_at` is set by the DB via `auto_now=True`, the in-memory object's `updated_at` is stale after `.save()`. The re-fetch correctly resolves this — but the comment `# Re-fetch with prefetch for serialization` doesn't make the reason explicit. A developer might remove it thinking it's redundant.

This is also an extra round-trip that pushes the POST path to **4 queries** (client lookup, get_or_create SELECT, UPDATE, re-fetch SELECT), violating the ≤3 spec requirement if it applies to POST as well.

**Recommendation:** Clarify in the spec whether the ≤3 limit applies to POST. If so, use `prefetch_related_objects([plan], ...)` after save to avoid the re-fetch SELECT, or accept that POST is allowed >3 queries.

#### M-3: `_get_agent` call after role check — unnecessary failure path

**File:** `marketing_plan_views.py`, lines 250–253
```python
if request.user.role != 'agent' or not hasattr(request.user, 'agent_profile'):
    return Response({'detail': 'Forbidden.'}, status=403)

agent = _get_agent(request)
```

`_get_agent` is an internal helper imported from `scheduling_views`. If it raises or returns `None` under any condition (e.g., `Agent.DoesNotExist`), this will produce an unhandled exception rather than a clean 403. The `hasattr` guard partially mitigates this, but `_get_agent`'s exact contract is opaque here — it's imported from a different view module without documentation of its failure modes.

**Fix:** Either inline the agent lookup with explicit error handling, or document `_get_agent`'s contract and wrap the call:
```python
try:
    agent = _get_agent(request)
except Exception:
    return Response({'detail': 'Forbidden.'}, status=403)
```

---

### Minor

#### m-1: `strategy_notes=None` (missing key) returns 400 with misleading message

**File:** `marketing_plan_views.py`, lines 290–295
```python
strategy_notes = request.data.get('strategy_notes')
if not isinstance(strategy_notes, str):
    return Response(
        {'strategy_notes': 'This field is required and must be a string.'},
        status=400,
    )
```

When `strategy_notes` is omitted from the request body, `request.data.get('strategy_notes')` returns `None`, which correctly fails the `isinstance` check. However, the error message says "required and must be a string" in a single message, making it impossible for the client to distinguish between "field missing" and "field wrong type". Consider splitting:
```python
if 'strategy_notes' not in request.data:
    return Response({'strategy_notes': 'This field is required.'}, status=400)
if not isinstance(request.data['strategy_notes'], str):
    return Response({'strategy_notes': 'This field must be a string.'}, status=400)
```

#### m-2: `_is_agent_assigned_to_client` only checks two departments

**File:** `marketing_plan_views.py`, lines 230–236
```python
def _is_agent_assigned_to_client(agent, client):
    if agent.department == 'marketing':
        return client.marketing_agent_id == agent.pk
    elif agent.department == 'website':
        return client.website_agent_id == agent.pk
    return False
```

If a new agent department is added in the future (e.g., `'seo'`, `'content'`), agents in that department will silently get a 403 regardless of actual assignment. The fallback `return False` is safe but not self-documenting. A comment noting this is intentionally restrictive would help.

#### m-3: GET view allows agents of any department to attempt access

The assignment check gates on department, but an agent with `department='website'` but `client.website_agent_id == agent.pk` would succeed. This is probably correct, but the spec says "agent must be assigned to client" without specifying which assignment field. If marketing-plan data should only be viewable by the marketing agent (not website agent), the check is too broad.

#### m-4: `MarketingPlanDetailSerializer` is fully read-only but inherits writable base

**File:** `serializers/marketing_core.py`, lines 9–21
All fields are in `read_only_fields`, which is correct. However, since this serializer is never used for writes, using `serializers.Serializer` with explicit fields would be more explicit and prevent accidental use in a write context. This is a style concern, not a bug.

#### m-5: `updated_at` not tested in POST response

The POST test assertions check `strategy_notes` but never assert that `updated_at` is present in the response. Since the serializer includes it, a regression that drops `updated_at` from serializer fields would not be caught.

---

### Nitpick

#### n-1: `active_pillars_qs` duplicated in both views

The queryset `ContentPillar.objects.filter(is_active=True)` is written identically in both `AgentClientMarketingPlanView.get` and `AdminClientMarketingPlanView.post`. Extract to a module-level constant or helper:
```python
_ACTIVE_PILLARS_QS = ContentPillar.objects.filter(is_active=True)
```

#### n-2: Test `test_admin_post_validates_strategy_notes_is_string` may not test the right thing

**File:** `tests.py`, line 161
```python
response = self.admin_api.post(self._admin_url(), {'strategy_notes': 12345}, format='json')
self.assertEqual(response.status_code, 400)
```

When `format='json'`, DRF/JSON serialization converts the integer `12345` to a JSON number. The view then receives `request.data['strategy_notes'] = 12345` (Python `int`), which correctly fails `isinstance(strategy_notes, str)`. This works as intended. However, the test does not assert on the response body (`response.data`), so the error message is never verified. Add:
```python
self.assertIn('strategy_notes', response.data)
```

#### n-3: `test_agent_get_returns_403_for_non_agent_user` uses `assertIn` for status code

**File:** `tests.py`, line 139
```python
self.assertIn(response.status_code, [401, 403])
```

This is appropriately permissive (DRF may return 401 when unauthenticated vs. 403 when authenticated but unauthorized). However, since `client_api` uses `force_authenticate`, the user IS authenticated — so a 403 is the only correct response here, and a 401 would indicate a bug. Use `assertEqual(response.status_code, 403)` for precision.

---

## Positive Observations

1. **Correct Prefetch usage.** Active-pillar filtering via `Prefetch('pillars', queryset=ContentPillar.objects.filter(is_active=True))` is exactly right — it avoids N+1 queries and applies the filter at the SQL level, not in Python post-processing.

2. **Query budget met for GET.** The GET path is 3 round-trips: client lookup (`get_object_or_404`), plan fetch with `prefetch_related` (1 SELECT for plan + batched prefetch SELECTs). This is within spec.

3. **Serializer design is clean.** `MarketingPlanDetailSerializer` correctly documents that pillar filtering is the view's responsibility. The `read_only_fields` declaration is consistent and prevents accidental mutation.

4. **404 on missing plan is correct.** Returning 404 (not an empty plan) when no `MarketingPlan` exists is the right semantic: the resource does not exist, not a plan with empty data.

5. **Test coverage is comprehensive.** Active/inactive pillar filtering, missing plan 404, unassigned agent 403, empty string strategy_notes, and get_or_create idempotency are all explicitly tested. The test fixture setup is clean and readable.

6. **`update_fields` on save.** Using `save(update_fields=['strategy_notes', 'updated_at'])` is good practice — it prevents clobbering unloaded fields on partial updates.

7. **URL pattern placement is logical.** Agent and admin endpoints are in the correct URL namespaces and follow the existing convention established by section 03.

---

## Recommendation

**Approve with required fixes before merge.**

The two items that must be resolved before shipping:

1. **C-1** — Add `name` (or other required fields) to `get_or_create` defaults to prevent a potential 500 on first plan creation.
2. **M-1** — Either wrap `get_or_create` + `save` in `transaction.atomic()` with `select_for_update()`, or migrate to `update_or_create` (Django 4.2+ supports `create_defaults` to set `created_by` only on insert).

M-2 (re-fetch round-trip) should be clarified against the spec: if the ≤3 query limit applies to POST, the re-fetch must be replaced with `prefetch_related_objects`. If POST is exempt, add a comment acknowledging the extra trip is intentional.

All other issues are minor polish and can be addressed in a follow-up.
