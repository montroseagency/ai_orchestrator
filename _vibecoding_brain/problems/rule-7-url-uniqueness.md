## RULE-7: [BACKEND] URL Registration Uniqueness

**Why:** Two views were registered at the same path (`admin/agents/`). Django resolved first-match, making the second view completely unreachable — all POST/PATCH/DELETE requests returned 404. This was only caught at code review, not during implementation. Root cause: when adding a new view, the developer didn't check whether the path was already registered, and there was confusion between old and new URL convention.

**How to apply:** Before finalizing any URL registration:
1. Run `grep -n "path(" server/api/urls.py | grep "your-route-path"` and verify it appears exactly once
2. Scan `urls.py` for the full route string — check both direct `path()` calls and included routers
3. If changing an existing path, review git diff for shadowed registrations
4. Run `python manage.py check` to validate syntax (won't catch duplicates, but catches errors)
5. If using a router (e.g., DRF DefaultRouter), check that the basename doesn't conflict with manually registered paths

This applies to all new views, routers, and path modifications. When in doubt: grep first, then register.
