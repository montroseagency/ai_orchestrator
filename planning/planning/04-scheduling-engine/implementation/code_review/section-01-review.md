# Code Review: Section 01 — Scheduling Test Utilities

**Files reviewed:**
- `client/test-utils/scheduling.tsx`
- `client/test-utils/scheduling.test.ts`

---

## Summary

Solid foundation overall. The factory functions are well-structured, the `renderWithQuery` helper correctly isolates QueryClient state between tests, and the `SchedulingEngineMock` type is explicit and complete. A few real issues stand out: stale `vi.fn()` instances are recreated on every call to `mockUseSchedulingEngine`, which is correct for isolation but makes the type annotation misleading; the "fresh client" test doesn't actually verify freshness; and the `import React from 'react'` in the `.ts` test file is unused. The diff also accidentally includes the entire `server/venv/` deletion — that should not be part of this PR.

---

## Issues

**1. [HIGH] Unrelated venv deletion included in the diff**
The diff contains thousands of lines deleting `server/venv/lib/python3.10/site-packages/` (Django, IPython, and other packages). This is clearly not related to the scheduling test utilities. If committed as-is, it could strip the tracked venv from git history and cause CI/environment issues for other contributors. The `server/venv/` directory should be in `.gitignore` and never committed.

**2. [MED] `renderWithQuery` "fresh client" test proves nothing**
```ts
// scheduling.test.ts line 91-96
const r1 = renderWithQuery(React.createElement('div'))
const r2 = renderWithQuery(React.createElement('div'))
expect(r1).not.toBe(r2)  // r1 and r2 are always different objects — this is trivially true
```
The test asserts that two render results are different objects, which is always true regardless of whether clients are shared. A meaningful test would verify that mutations to the cache in `r1` do not appear in `r2` — for example, by pre-populating `r1`'s QueryClient and asserting the key is absent in `r2`.

**3. [MED] `weekDays` in `mockUseSchedulingEngine` is a Mon–Fri slice but has no Sunday**
```ts
weekDays: ['2026-03-23', '2026-03-24', '2026-03-25', '2026-03-26', '2026-03-27'],
```
2026-03-23 is a Monday — fine for a 5-day week. However, if `useSchedulingEngine` in production ever returns a 7-day array (Mon–Sun), tests that rely on `weekDays.length` or index-based access will silently diverge from real behaviour. Document the 5-day assumption explicitly in a comment, or derive the default from the actual hook's return shape once it is implemented.

**4. [MED] `mockUseSchedulingEngine` creates new `vi.fn()` instances on every call**
This is correct for test isolation, but `ReturnType<typeof vi.fn>` loses all generic call-signature information. If a consumer needs to assert call arguments (e.g., `expect(mock.scheduleTask).toHaveBeenCalledWith(...)`) the type is fine at runtime but provides no compile-time parameter checking. Consider typing the functions more precisely once the hook signatures are known — e.g., `scheduleTask: vi.fn() as ReturnType<typeof vi.fn<[string, string], Promise<void>>>`.

**5. [LOW] Unused `import React from 'react'` in `scheduling.test.ts`**
```ts
// scheduling.test.ts line 7
import React from 'react'
```
`React` is used only via `React.createElement('div')` in the `renderWithQuery` tests. With the JSX transform enabled (Next.js default), this import is unnecessary and should be either removed or replaced with `import { createElement } from 'react'` for clarity. If the project's tsconfig does not have `"jsx": "react-jsx"`, this is harmless but still lint-triggering.

**6. [LOW] `createMockTimeBlock` independence test mutates a property after assertion**
```ts
// scheduling.test.ts lines 41-43
a.id = 'modified'
expect(b.id).toBe('block-1')
```
The mutation is intentional (proving shallow independence), but the test does not clean up or describe why it is mutating. This pattern is fine but worth a brief inline comment so future maintainers don't mistake it for a test setup error.

**7. [LOW] `selectedDate` and `weekDays` defaults are hardcoded to a specific date (2026-03-25)**
If test files import this mock and also assert against `new Date()` or `Date.now()`, time-sensitive comparisons will fail as the project ages. These are fine as static strings for structural tests, but make sure no consumer test ever compares them to "today". A comment noting they are static fixtures (not relative to the current date) would prevent confusion.

---

## Auto-fixable

The following can be fixed mechanically without design decisions:

- **Remove unused `import React`** from `scheduling.test.ts` (line 7) — or change `React.createElement('div')` to `<div />` with a `.tsx` extension on the test file.
- **Add `server/venv/` to `.gitignore`** if not already present — prevents the venv from being tracked and eliminates the noise in this diff.
- **Add a lint rule or vitest config comment** (`// @vitest-environment jsdom`) at the top of `scheduling.test.ts` if the project does not set this globally, to ensure the `render` calls in `renderWithQuery` tests run in a DOM environment.
