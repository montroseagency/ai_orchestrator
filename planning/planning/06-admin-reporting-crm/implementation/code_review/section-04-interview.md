# Section 04 Code Review Interview — Marketing Plan API

## Review Summary
Reviewed by: code-reviewer subagent
Verdict: Approve with fixes

---

## Items Triaged

### C-1: `get_or_create` missing `name` field → IntegrityError
**Disposition: Let go (not an issue)**
MarketingPlan.name has `default="Marketing Plan"` — INSERT path of get_or_create will use the default. No IntegrityError possible.

### M-1: Race condition in POST (get_or_create + save not atomic)
**Disposition: Auto-fixed**
Wrapped `get_or_create` + `save` in `transaction.atomic()`. Also added `select_for_update()` on the get_or_create to prevent concurrent creates.

### M-2: POST does 4 round-trips (re-fetch after save adds extra SELECT)
**Disposition: Auto-fixed**
Replaced re-fetch queryset with `prefetch_related_objects([plan], ...)` which loads related data in-place without an extra SELECT for the plan itself.

### M-3: `_get_agent` failure modes opaque
**Disposition: Let go (already handled)**
We check `hasattr(request.user, 'agent_profile')` before calling `_get_agent` — it won't raise.

### Minor: `assertIn(status_code, [401, 403])` for authenticated non-agent user
**Disposition: Auto-fixed**
Changed to `assertEqual(403)` — `force_authenticate` means the user IS authenticated; our view returns 403 for wrong role.

### Minor: `test_admin_post_validates_strategy_notes_is_string` missing data assertion
**Disposition: Auto-fixed**
Added `assertIn('strategy_notes', response.data)` to verify error key is present.

### Nitpick: `active_pillars_qs` duplicated in both views
**Disposition: Auto-fixed**
Extracted to module-level constant `_ACTIVE_PILLARS_PREFETCH`.

---

## Applied Fixes
1. `transaction.atomic()` + `select_for_update()` on admin POST (M-1)
2. `prefetch_related_objects` instead of re-fetch (M-2)
3. `assertEqual(403)` for authenticated non-agent test
4. Added data assertion to strategy_notes type validation test
5. Module-level `_ACTIVE_PILLARS_PREFETCH` constant

---

## Final Test Result
Ran 10 tests — OK (all pass)
