# Section 11: Portal Calendar Page

## Overview

This section replaces the existing placeholder at `client/app/dashboard/agent/marketing/management/calendar/page.tsx` with a fully wired Next.js page component that mounts the `SchedulingEngine` and handles URL-based state initialization. It is the final entry point for the entire scheduling feature and depends on `section-05-scheduling-engine` being complete.

## Dependency

**Requires:** `section-05-scheduling-engine` — `SchedulingEngine` component must exist and accept `agentType` and `initialDate` props before this page can be implemented.

**Does not affect:** Any other section. This is a leaf in the dependency graph.

---

## File to Modify

**`client/app/dashboard/agent/marketing/management/calendar/page.tsx`**

This is the only file that needs to change. The developer calendar at `client/app/dashboard/agent/developer/calendar/page.tsx` is a separate, unrelated component (month-view developer calendar using `useDeveloperCalendar`) and must **not** be modified.

Current content is a placeholder:
```tsx
import Link from 'next/link';

export default function CalendarPage() {
  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold text-primary">Calendar</h1>
      <p className="mt-2 text-sm text-secondary">
        This section is being built and will be available soon.
      </p>
      <Link href="/dashboard/agent/marketing/management/" ...>
        Back to Command Centre
      </Link>
    </div>
  );
}
```

Replace it entirely with the new implementation described below.

---

## Tests First

**File:** `client/app/dashboard/agent/marketing/management/calendar/page.test.tsx`

Write these tests before implementing the page. The test file lives alongside the page component.

```typescript
// Stub signatures — implement test bodies based on the assertions listed below

describe('CalendarPage', () => {
  it('renders SchedulingEngine without crashing', ...)
  it('passes agentType="marketing" to SchedulingEngine', ...)
  it('initializes selectedDate from ?date= query param', ...)
  it('defaults selectedDate to today when ?date= is absent', ...)
})
```

**Test assertions (implement each):**

1. **Renders without crashing:** Render `<CalendarPage />` inside a `renderWithQuery()` wrapper (from `client/test-utils/scheduling.tsx`) with mocked Next.js navigation. Assert the component mounts without throwing. Mock `SchedulingEngine` as a stub that renders `<div data-testid="scheduling-engine" />`.

2. **`?date=` param initializes `selectedDate`:** Mock `useSearchParams` to return `{ get: (k) => k === 'date' ? '2026-03-28' : null }`. Render the page. Assert `SchedulingEngine` receives `initialDate="2026-03-28"`.

3. **Missing `?date` defaults to today:** Mock `useSearchParams` to return `{ get: () => null }`. Render the page. Assert `SchedulingEngine` receives `initialDate` equal to `new Date().toISOString().split('T')[0]` (today's ISO date string).

4. **`agentType` prop is "marketing":** Assert `SchedulingEngine` receives `agentType="marketing"` regardless of query params. Since there is currently only one concrete page file (marketing), the agent type is a static string derived from the route's position in the file system.

**Mocking Next.js navigation in tests:**

```typescript
vi.mock('next/navigation', () => ({
  useSearchParams: vi.fn(),
  useRouter: vi.fn(() => ({ push: vi.fn() })),
  useParams: vi.fn(() => ({ type: 'marketing' })),
}))
```

---

## Implementation

The page is a minimal `'use client'` component. It has no server-side data fetching. All data ownership lives in `useSchedulingEngine` inside the `SchedulingEngine` component.

**Responsibilities of this page:**
1. Read `?date=` from search params to determine the initial selected date.
2. Fall back to today's ISO date string if `?date=` is absent or invalid.
3. Render `<SchedulingEngine agentType="marketing" initialDate={initialDate} />`.
4. Nothing else — no layout wrappers, no extra query calls, no navigation logic.

**Key design decisions:**
- `'use client'` is required because `useSearchParams` (from `next/navigation`) only runs on the client.
- The page does not use `useParams` to derive `agentType` dynamically — the file is statically located under `marketing/` so `agentType` is the literal string `"marketing"`. The plan describes a dynamic `[type]` route, but the actual file system has concrete `marketing/` and `developer/` subdirectories, not a `[type]` param. Wire `agentType="marketing"` directly.
- Date validation: if `dateParam` is present but does not match `YYYY-MM-DD` format (a 10-character ISO date string), fall back to today. A simple length/format guard is sufficient — no full date parsing needed.

**Component signature:**

```tsx
'use client';

import { useSearchParams } from 'next/navigation';
import { SchedulingEngine } from '@/components/portal/calendar/SchedulingEngine';

export default function CalendarPage() {
  // read ?date= param
  // compute initialDate (param or today)
  // render SchedulingEngine
}
```

**Import path for `SchedulingEngine`:** `@/components/portal/calendar/SchedulingEngine` — matches the component directory established in `section-05-scheduling-engine`.

**Today's date computation:**

```typescript
const today = new Date().toISOString().split('T')[0]; // "YYYY-MM-DD"
```

Use this as the fallback when `?date=` is absent.

---

## Acceptance Criteria

- [ ] Existing placeholder is fully replaced — no "being built" text remains.
- [ ] Page renders `SchedulingEngine` as its sole content element.
- [ ] `?date=2026-03-28` in the URL causes `SchedulingEngine` to receive `initialDate="2026-03-28"`.
- [ ] Navigating to the page with no `?date=` param causes `initialDate` to equal today's ISO date.
- [ ] `agentType="marketing"` is always passed to `SchedulingEngine`.
- [ ] All four tests pass.
- [ ] No TypeScript errors (`tsc --noEmit` passes in `client/`).
- [ ] The existing developer calendar page (`client/app/dashboard/agent/developer/calendar/page.tsx`) is unchanged.
