# Section 01 — Code Review Interview

## Auto-fixes Applied

### 1. Trailing slash removed from href
**Finding:** href `/dashboard/agent/marketing/management/` has a trailing slash inconsistent with other nav items. More critically, it would break the `isActive` check in `NavGroup`: `pathname.startsWith(href + '/')` becomes `startsWith('/management//')` — a double slash that never matches any sub-route, so the "Command Center" link would never highlight as active when on sub-pages like `/management/tasks`.

**Fix:** Changed to `/dashboard/agent/marketing/management` (no trailing slash). Updated test assertion to match.

### 2. Added canary comment to regression test
**Finding:** Test 2 asserts the developer Command Center href unchanged. Without a comment, a future reader might update the developer href intentionally and be confused by the failure.

**Fix:** Added comment explaining this is a canary guard.

### 3. Added vitest globals to tsconfig
**Finding:** `globals: true` in vitest.config means `describe`, `it`, `expect` are injected as globals, but TypeScript doesn't know about them without `"types": ["vitest/globals"]` in tsconfig.

**Fix:** Added to `client/tsconfig.json` compilerOptions.

## Items Let Go
- `waitFor` vs `findBy` style inconsistency — both are correct patterns, no functional difference.
- `@testing-library/user-event` installed but unused — needed imminently for later sections.
