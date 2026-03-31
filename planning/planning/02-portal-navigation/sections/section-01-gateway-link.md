# Section 01: Gateway Link Update

## Overview

Update a single `href` in the global sidebar so the "Command Center" nav item routes to the new management portal instead of the old schedule page. This is the entry point into the entire portal — without this change, users have no way to reach the portal via the normal navigation.

**File to modify:** `client/components/dashboard/sidebar.tsx`

**Dependencies:** None. This section is fully standalone.

---

## Tests First

Set up Vitest + React Testing Library if not already present (see Testing Setup below). Write these tests before making the change:

```
// Test: marketing agent "Command Center" nav item href is '/dashboard/agent/marketing/management'
// Test: no other sidebar nav items were changed by this modification
```

The second test is a regression guard — render the full sidebar and assert that all other `href` values are unchanged from baseline.

---

## Implementation

### What to Change

In `client/components/dashboard/sidebar.tsx`, find the marketing agent navigation section. There is a nav item labelled "Command Center" (note: US spelling, not "Command Centre"). Its `href` currently points to `/dashboard/agent/marketing/schedule`.

Change that single `href` value to:

```
/dashboard/agent/marketing/management
```

**Note:** No trailing slash — the `isActive` helper in `NavGroup` uses `pathname.startsWith(href + '/')` to highlight active state for sub-routes. A trailing slash on the href would cause a double-slash (`/management//tasks`) that never matches.

No other changes to `sidebar.tsx` are needed in this section. Portal detection logic lives in `dashboard/layout.tsx` (Section 02), not here.

### How to Find It

Search for `schedule` in `sidebar.tsx` to locate the exact line. The nav structure for the marketing agent looks like:

```
Main: Command Center, Overview
```

The "Command Center" entry is the one to update.

### Verification

After the change, clicking "Command Center" in the marketing agent sidebar should navigate to `/dashboard/agent/marketing/management`. At this point the route doesn't exist yet (Section 05 creates it), so the browser will show a 404 — that is expected. The link itself is correct.

---

## Testing Setup

No test framework was previously configured in the project. The following was added:

**Files created:**
- `client/vitest.config.ts` — Vitest config with jsdom environment, `@vitejs/plugin-react`, and `@/*` alias
- `client/vitest.setup.ts` — imports `@testing-library/jest-dom`

**Files modified:**
- `client/package.json` — added `"test": "vitest"` script; added devDependencies: `vitest@^4`, `@vitejs/plugin-react@^6`, `@testing-library/react@^16`, `@testing-library/jest-dom@^6`, `@testing-library/user-event@^14`, `jsdom@^29`
- `client/tsconfig.json` — added `"types": ["vitest/globals"]` so TypeScript recognises Vitest globals

**Test file:** `client/components/dashboard/sidebar.test.tsx` — 2 tests, both pass.

This infrastructure is a prerequisite for all subsequent sections' unit tests.
