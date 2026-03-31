# Section 02 — CurrentTaskKpi

## Overview

Implement the primary KPI widget for the read-only agent dashboard. `CurrentTaskKpi` is a full-width card that shows the currently active time block, a real-time animated progress bar, time remaining, and a deep-link button into the CommandCenter portal. It also handles three distinct empty states.

This section depends on **section-01-test-utils** (which ensures `createMockTimeBlock()`, `renderWithQuery()`, and the `staleTime: 55_000` change are already in place). Sections 03, 04, and 05 are parallel peers. Section 06 assembles everything into the page.

---

## Files to Create

| File | Action |
|------|--------|
| `client/components/agent/dashboard/CurrentTaskKpi.tsx` | Create |
| `client/components/agent/dashboard/__tests__/CurrentTaskKpi.test.tsx` | Create |

The `client/components/agent/dashboard/` directory is new — create it. The `__tests__/` subdirectory is also new.

---

## Dependencies and Imports

### Existing utilities your component must use

**`timeToMinutes(time: string): number`**
- Location: `client/components/portal/calendar/utils/timeUtils.ts`
- Parses `"HH:MM"` or `"HH:MM:SS"` to total minutes since midnight.
- Use this for all time comparisons. Do NOT inline equivalent arithmetic.

**`BLOCK_TYPE_LABELS`** and **`BLOCK_TYPE_COLORS`**
- Location: `client/lib/types/scheduling.ts`
- `BLOCK_TYPE_LABELS: Record<BlockType, string>` — e.g., `{ deep_work: 'Deep Work', reactive: 'Reactive & Routine', ... }`
- `BLOCK_TYPE_COLORS: Record<BlockType, string>` — e.g., `{ deep_work: '#6366F1', ... }`

**`AgentTimeBlock`** type
- Location: `client/lib/types/scheduling.ts`
- Relevant fields: `id`, `title`, `client_name`, `block_type`, `start_time` (HH:MM:SS), `end_time` (HH:MM:SS), `date` (YYYY-MM-DD)

### Test utilities (from section-01)

- `createMockTimeBlock(overrides?)` — `client/test-utils/scheduling.tsx`
- `renderWithQuery(ui, options?)` — `client/test-utils/scheduling.tsx`

---

## Props Interface

```typescript
interface CurrentTaskKpiProps {
  timeBlocks: AgentTimeBlock[];
  agentType: string; // used to construct deep-link URLs
}
```

The component is **stateless with respect to data** — it receives `timeBlocks` from the parent page which calls `useCommandCenter()`. The only internal state is a `now: Date` that drives the progress timer.

---

## Active Block Detection Logic

This is a derived value — compute it inline or with `useMemo` every render when `now` or `timeBlocks` changes.

1. Convert `now` to minutes-since-midnight: `const nowMinutes = now.getHours() * 60 + now.getMinutes()`
2. Walk `timeBlocks` to find every block where `timeToMinutes(block.start_time) <= nowMinutes < timeToMinutes(block.end_time)`
3. If multiple blocks match (overlap), pick the one with the latest `start_time` (most recently started)
4. If no block matches, find the next upcoming block: `timeToMinutes(block.start_time) > nowMinutes`, take the one with the earliest `start_time`

The detection uses only `now.getHours()` and `now.getMinutes()` (no seconds), consistent with `timeToMinutes` which ignores seconds.

---

## Timer

```typescript
const [now, setNow] = useState(() => new Date());

useEffect(() => {
  const id = setInterval(() => setNow(new Date()), 60_000);
  return () => clearInterval(id);
}, []);
```

The interval fires every 60 seconds. Because `setInterval` is cleared on unmount, there is no memory leak. Tests must verify the cleanup using `vi.useFakeTimers()` and checking that `clearInterval` is called on unmount.

---

## Progress Calculation

Given an active block:

```typescript
const startMin = timeToMinutes(block.start_time);
const endMin   = timeToMinutes(block.end_time);
const progress = Math.min(100, Math.max(0, ((nowMinutes - startMin) / (endMin - startMin)) * 100));
const scaleX   = progress / 100; // 0.0 to 1.0
const remaining = Math.floor(endMin - nowMinutes);
```

- `remaining < 1` → display `"Ending soon"` instead of `"0 min remaining"`
- All other values → display `"{remaining} min remaining"`

---

## Progress Bar Element

The progress bar fill uses `transform: scaleX()` — NOT `width`. This is GPU-composited and does not trigger layout.

```tsx
<div
  role="progressbar"
  aria-valuenow={progress}
  aria-valuemin={0}
  aria-valuemax={100}
  style={{ transform: `scaleX(${scaleX})`, transformOrigin: 'left' }}
  className="h-2 bg-accent transition-transform duration-[800ms] ease-[cubic-bezier(0.4,0,0.2,1)]"
/>
```

Wrap the fill in a container div with `overflow-hidden` and `relative` positioning so the scaled fill does not bleed outside.

The `role="progressbar"` and ARIA attributes are required for screen reader accessibility.

---

## Display Elements (Active Block)

When an active block is found, render the following in the card:

- **Title**: `block.title` — large, bold (`text-xl font-bold` or larger)
- **Client badge**: `block.client_name` (omit if empty string)
- **Category badge**: `BLOCK_TYPE_LABELS[block.block_type]`
- **Time range**: `"{formattedStart} – {formattedEnd}"` in 12-hour format
  - Use a local inline formatter for `HH:MM:SS` → `"H:MM AM/PM"`. The existing `formatHour()` from `timeUtils.ts` handles whole hours only; you will need to handle minutes too (e.g., `"9:30 AM"`).
- **Progress bar**: as described above
- **Time remaining**: `"{N} min remaining"` or `"Ending soon"`
- **Deep-link button**: `"Open in Portal →"` as a Next.js `<Link>` with:
  ```
  href="/dashboard/agent/{agentType}/management/calendar/?date={block.date}&block={block.id}"
  ```

---

## Empty States

Three mutually exclusive states when no active block exists:

**State 1 — Free time** (no active block, but a future block exists today):
```tsx
// Render: "Free until {nextBlock.start_time formatted}. Next: {nextBlock.title}"
// Plus a portal link
```

**State 2 — Day ended / no tasks** (no active block and no future blocks):
```tsx
// Render: "No tasks scheduled for today."
// Plus a portal link to the calendar
```

**State 3 — Active block** (render full widget as described above).

For the portal link in empty states, link to `/dashboard/agent/{agentType}/management/calendar/` (no query params needed).

---

## Visual Design

The card must match the `Ui-Ux-Pro-Max` design language:

- Full-width card: `bg-surface border-2 border-accent shadow-lg rounded-2xl p-6`
- When active: add `ring-2 ring-accent/20`
- More prominent shadow than the stat cards below it
- Use `client/components/ui/card.tsx` for the outer container if available, or a plain `div` with the classes above

---

## React.memo

Wrap the export in `React.memo`:

```typescript
export const CurrentTaskKpi = React.memo(function CurrentTaskKpi(props: CurrentTaskKpiProps) {
  // ...
});
```

The parent page re-renders every 60s on query refetch. `memo` prevents cascade re-renders when `timeBlocks` data is unchanged.

---

## Test File: `CurrentTaskKpi.test.tsx`

**Setup for all tests:**

```typescript
// Mock the useScheduling module (not needed — component receives props, not hook calls)
// Use vi.useFakeTimers() for timer tests
// Use createMockTimeBlock() to build test data
// Use renderWithQuery() to wrap renders (component uses no queries, but consistent pattern)
```

For time-based tests, control `now` by mocking `Date`: use `vi.setSystemTime(new Date(2026, 2, 25, 9, 30, 0))` (March 25 2026, 09:30:00 local).

### Test stubs to implement

```typescript
describe('CurrentTaskKpi — Active Block Detection', () => {
  it('renders block title when now falls within a time block range')
  it('renders client badge with block.client_name')
  it('renders category badge with BLOCK_TYPE_LABELS[block.block_type]')
  it('renders the block whose range contains now, not a past or future block')
  it('when blocks overlap, renders the block with the latest start_time')
})

describe('CurrentTaskKpi — Progress Calculation', () => {
  it('progress bar has transform scaleX(0.5) when now is at 50% of block duration')
  it('progress bar has transform scaleX(0) when now equals block start')
  it('progress bar has transform scaleX(1) when now equals or exceeds block end')
  it('progress does not go below 0 or above 1 (scaleX is clamped)')
})

describe('CurrentTaskKpi — Time Remaining', () => {
  it('renders "30 min remaining" when 30 minutes remain')
  it('renders "Ending soon" when less than 1 minute remains')
  it('applies floor — renders "29 min remaining" when 29.9 minutes remain')
})

describe('CurrentTaskKpi — Empty States', () => {
  it('renders "No tasks scheduled for today" when timeBlocks is empty')
  it('renders portal link when timeBlocks is empty')
  it('renders "Free until" message when now falls between two blocks')
  it('renders next block title in "Free until" state')
  it('renders portal link when in "Free until" state')
  it('renders "No tasks scheduled" when now is after all blocks')
})

describe('CurrentTaskKpi — Timer', () => {
  it('re-renders with updated progress after advancing fake timers by 60s')
  it('clears setInterval on unmount (no memory leak)')
})

describe('CurrentTaskKpi — Deep-link', () => {
  it('"Open in Portal" href contains date={block.date} and block={block.id}')
})

describe('CurrentTaskKpi — Accessibility', () => {
  it('progress bar element has role="progressbar"')
  it('progress bar has aria-valuenow, aria-valuemin=0, aria-valuemax=100')
})
```

### Notes on fake timer tests

```typescript
// Pattern for timer test:
beforeEach(() => { vi.useFakeTimers(); vi.setSystemTime(new Date(2026, 2, 25, 9, 30, 0)); });
afterEach(() => { vi.useRealTimers(); });

it('re-renders with updated progress after advancing fake timers by 60s', async () => {
  // render with a block covering 9:00–10:00
  // check initial progress reflects 9:30 (50%)
  // act(() => { vi.advanceTimersByTime(60_000); })
  // check updated progress reflects 9:31 (≈51.67%)
});

it('clears setInterval on unmount', () => {
  const clearSpy = vi.spyOn(global, 'clearInterval');
  const { unmount } = renderWithQuery(<CurrentTaskKpi ... />);
  unmount();
  expect(clearSpy).toHaveBeenCalled();
});
```

---

## Acceptance Criteria for This Section

1. Component renders the active block's title, client badge, category badge, and formatted time range
2. Progress bar uses `transform: scaleX()` (not `width`) with CSS transition
3. Progress is clamped to 0–100 (scaleX 0–1)
4. Time remaining shows correct floor value; "Ending soon" when < 1 minute
5. All three empty states render correct messages and portal links
6. `setInterval` fires every 60s and updates `now` state; is cleared on unmount
7. Deep-link `href` includes correct `date` and `block` query params
8. Progress bar element has `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
9. Component is exported as `React.memo`
10. All test stubs above pass
