# Section 05 — ReadOnlySchedule

## Overview

Implement `ReadOnlySchedule.tsx`, a self-contained vertical hour-by-hour timeline that renders an agent's time blocks for the day. This is a pure display component — no drag-and-drop, no click handlers, no modals. It uses the same positioning math as `DaySchedule.tsx` but with none of its interactive complexity.

This component is implemented in parallel with sections 02, 03, and 04. It depends on section 01 (test utilities) and is consumed by section 06 (the dashboard page).

---

## Dependencies

- **section-01-test-utils** must be complete before running tests. Specifically:
  - `createMockTimeBlock()` from `client/test-utils/scheduling.tsx`
  - `renderWithQuery()` from `client/test-utils/scheduling.tsx`

- **Existing imports** (do not modify these files):
  - `BLOCK_TYPE_LABELS`, `BLOCK_TYPE_COLORS`, `AgentTimeBlock` from `client/lib/types/scheduling.ts`
  - `timeToMinutes()` (or equivalent) from the existing time utilities — the same helper used by `DaySchedule.tsx` and `CurrentTaskKpi.tsx`

---

## Files to Create

| File | Action |
|------|--------|
| `client/components/agent/dashboard/ReadOnlySchedule.tsx` | Create |
| `client/components/agent/dashboard/__tests__/ReadOnlySchedule.test.tsx` | Create |

Do not modify `client/components/agent/scheduling/DaySchedule.tsx` or any other existing file.

---

## Tests First

**File**: `client/components/agent/dashboard/__tests__/ReadOnlySchedule.test.tsx`

All tests use `vi.useFakeTimers()` (set before each test) and `vi.useRealTimers()` (restored after each). Use `createMockTimeBlock()` from `client/test-utils/scheduling.tsx` to build fixture data. Use `renderWithQuery()` to wrap the component.

### Block Rendering

```typescript
// Test: given a time block, renders the block's title in the DOM
// Test: given a time block, renders the block's client_name
```

### Block Positioning Math

The positioning formula is:
- `top = ((startMin - startHour * 60) / 60) * hourHeight` (in px)
- `height = ((endMin - startMin) / 60) * hourHeight` (in px)

With defaults `startHour=8`, `hourHeight=50`:

```typescript
// Test: a block starting at 9:00 (540 min total, 60 min past startHour=8)
//   → top = (60 / 60) * 50 = 50px
//   Check: block element has inline style `top: 50px`

// Test: a 60-minute block (e.g. 9:00–10:00)
//   → height = (60 / 60) * 50 = 50px
//   Check: block element has inline style `height: 50px`

// Test: a block's left border color matches BLOCK_TYPE_COLORS[block.block_type]
//   Check: block element has inline style `borderLeftColor: <expected color>`
//   (Use a block type that has a known color in BLOCK_TYPE_COLORS)
```

### Hour Grid

```typescript
// Test: hour labels "8 AM" through "8 PM" render when startHour=8, endHour=20
//   Check: screen contains text "8 AM", "9 AM", ..., "8 PM"

// Test: formatHour(8) → "8 AM" label renders in the grid
//   (The hour label format is "H AM/PM" — no leading zero, e.g. "8 AM" not "08 AM")
```

### Active Block Highlight

The active block detection uses the same logic as `CurrentTaskKpi`: walk `timeBlocks` to find the block where `startMinutes <= nowMinutes < endMinutes`. If multiple overlap, use the one with the latest `start_time`.

```typescript
// Test: the block whose range contains `now` has the highlight class `ring-accent` (or equivalent)
//   Check: block element has a class containing "ring" or "ring-accent"

// Test: a block in the past does not have the highlight class
//   Set up two blocks: one past, one active
//   Check: past block element does NOT have the highlight class
```

### NowIndicator

The `NowIndicator` is an inline sub-component — a thin `border-t-2 border-red-500` horizontal line positioned absolutely at:

```
top = ((nowMinutes - startHour * 60) / 60) * hourHeight
```

```typescript
// Test: NowIndicator is present in the DOM when now is within [startHour, endHour]
//   Check: an element with role or data attribute that identifies it as the now indicator exists

// Test: NowIndicator's top style matches expected position
//   e.g., now = 9:00 (540 min), startHour=8 (480 min), hourHeight=50
//   → top = ((540 - 480) / 60) * 50 = 50px
//   Check: indicator element has inline style `top: 50px`

// Test: NowIndicator is NOT rendered when now is before startHour
//   e.g., now = 7:00 → indicator should not be in the DOM

// Test: NowIndicator is NOT rendered when now is after endHour
//   e.g., now = 21:00 → indicator should not be in the DOM

// Test: advancing fake timers by 60s updates NowIndicator position
//   Use vi.advanceTimersByTime(60_000) and check new top value
```

### No Interactivity

```typescript
// Test: time block elements do not have onClick handlers
//   Check: block element does not have an onClick prop (or that clicking does nothing)

// Test: time block elements are not focusable
//   Check: block element does NOT have tabIndex attribute
//   Check: block element does NOT have role="button"
```

### Auto-Scroll on Mount

The container `ref` is used to set `scrollTop` on mount so the current hour is visible. This fires in a `useEffect` with the container ref.

```typescript
// Test: scrollTop on the container is set to a non-zero value on mount
//   when now is within the visible [startHour, endHour] range
//   Use Object.defineProperty to mock scrollTop on the container element
//   or spy on the ref's scrollTop setter
```

### Footer Link

```typescript
// Test: "Edit Schedule in Portal →" link has correct href
//   href should contain `/management/calendar/`
//   href should contain `date=` with today's date in YYYY-MM-DD format
//   Example href: `/dashboard/agent/marketing/management/calendar/?date=2026-03-29`
```

---

## Implementation

**File**: `client/components/agent/dashboard/ReadOnlySchedule.tsx`

### Props Interface

```typescript
interface ReadOnlyScheduleProps {
  timeBlocks: AgentTimeBlock[];
  date: string;           // YYYY-MM-DD — used for the portal footer link
  agentType: string;      // e.g. "marketing" — used to construct the portal link
  startHour?: number;     // default: 8
  endHour?: number;       // default: 20
  hourHeight?: number;    // default: 50 (px per hour)
}
```

### Component Structure

The component renders:

1. **Outer container**: `position: relative`, `overflow-y: auto`, `max-height: 600px`. Attach a `ref` to this element for auto-scroll.

2. **Hour label column** (left side): one label per hour from `startHour` to `endHour`. Use a helper `formatHour(h: number): string` that returns "8 AM", "9 AM", ..., "12 PM", "1 PM", etc. Each label is positioned absolutely at `top = ((h - startHour) * hourHeight)`.

3. **Grid lines**: thin horizontal `border-t border-border` lines at each hour boundary, spanning the full width, positioned at the same `top` as each hour label.

4. **Time block cards**: positioned absolutely using the formula above. Each block renders:
   - `rounded-lg border-l-4` with `borderLeftColor: BLOCK_TYPE_COLORS[block.block_type]`
   - Background: a light tint (e.g., `bg-surface/80`)
   - Title in small bold text
   - Client name in smaller muted text
   - Active block gets an additional `ring-2 ring-accent/20` class
   - No `onClick`, no `tabIndex`, no `role="button"`

5. **`NowIndicator`** (inline sub-component): owns its own `now` state via `useState(new Date())` and a `setInterval` every 60 seconds to update it. Renders only when `nowMinutes` is within `[startHour * 60, endHour * 60]`. Styled as `position: absolute; left: 0; right: 0; border-top: 2px solid red`.

6. **Footer**: `<a>` or Next.js `<Link>` → "Edit Schedule in Portal →" pointing to `/dashboard/agent/{agentType}/management/calendar/?date={date}`.

### Active Block Detection (derived value)

Use `useMemo` to detect the active block, same logic as `CurrentTaskKpi`:

```typescript
// Stub:
const activeBlockId = useMemo(() => {
  // Convert now to minutes-since-midnight
  // Walk timeBlocks to find blocks where startMin <= nowMin < endMin
  // If multiple overlap, return the id of the one with the latest start_time
  // Return null if none
}, [timeBlocks, now]);
```

### Auto-Scroll on Mount

```typescript
// useEffect stub:
useEffect(() => {
  // If containerRef.current exists and nowMinutes is within range,
  // set containerRef.current.scrollTop to position the current hour
  // roughly in the upper third of the visible area
  // scrollTop = max(0, (nowMinutes - startHour * 60 - 60) / 60 * hourHeight)
}, []); // empty dep array — only on mount
```

### NowIndicator Sub-Component

```typescript
// Inline sub-component stub (not exported):
function NowIndicator({ startHour, endHour, hourHeight }: NowIndicatorProps) {
  // Local state: now = new Date()
  // setInterval every 60s to update now
  // Clear interval on unmount
  // Compute nowMinutes, return null if outside range
  // Return a div with position:absolute, top computed from formula, border-t-2 border-red-500
}
```

### `formatHour` Helper

```typescript
// Not exported — used only within this file
function formatHour(h: number): string {
  // 0–11 → "12 AM" / "1 AM" ... "11 AM"
  // 12 → "12 PM"
  // 13–23 → "1 PM" ... "11 PM"
}
```

### Performance

Wrap the component in `React.memo`. The `NowIndicator` sub-component does not need memo since it is a lightweight local state holder with no parent prop changes that would re-render it independently.

---

## Key Design Decisions

**Why a separate component instead of adding a `readOnly` prop to `DaySchedule`?**
`DaySchedule.tsx` is ~544 lines of DnD, modal, and editing logic. A `readOnly` prop would scatter conditionals throughout its body. `ReadOnlySchedule` achieves the same display with ~100 lines, zero coupling to `@dnd-kit`, and no risk of accidentally breaking the interactive `CommandCenter` portal.

**Why does `NowIndicator` own its own timer instead of receiving `now` as a prop?**
The parent (`ReadOnlySchedule`) does not need to re-render every 60s — only the indicator line needs to move. Keeping the timer inside `NowIndicator` prevents the entire schedule (including all absolutely-positioned blocks) from re-rendering on each tick.

**Why `scaleX` isn't needed here (unlike `CurrentTaskKpi`)?**
`ReadOnlySchedule` doesn't have a progress bar — it has absolute positioning. Block positions are static relative to the data, not animated. Only the `NowIndicator` moves, and a simple top-position update is sufficient (no GPU compositor concern at this frequency).

**Why `overflow-y: auto` with `max-height: 600px`?**
A full 8 AM–8 PM range at 50px/hour = 600px. This is the exact visible area. The `max-height` cap ensures the component doesn't grow unbounded in short layouts, while `overflow-y: auto` makes the scrollbar appear only when content overflows (e.g., if `endHour` is extended).

---

## Acceptance Criteria

- [x] `ReadOnlySchedule.tsx` renders all provided time blocks at correct vertical positions
- [x] Block `top` and `height` match the formula: `((min - startHour*60) / 60) * hourHeight`
- [x] Left border color of each block matches `BLOCK_TYPE_COLORS[block.block_type]`
- [x] Hour labels from `startHour` to `endHour` render in "H AM/PM" format
- [x] Active block (range contains `now`) has a highlight ring class
- [x] Blocks in the past or future do not have the highlight class
- [x] `NowIndicator` is visible and at correct `top` when `now` is within `[startHour, endHour]`
- [x] `NowIndicator` is absent from the DOM when `now` is outside the visible range
- [x] `NowIndicator` position updates after 60s (via fake timer test)
- [x] No block element has `onClick`, `tabIndex`, or `role="button"`
- [x] Container auto-scrolls to approximately the current hour on mount
- [x] Footer link href contains `/management/calendar` and `date={date}` in `YYYY-MM-DD` format
- [x] All `ReadOnlySchedule.test.tsx` tests pass (22 tests)

## Implementation Status

**COMPLETE.** All changes applied and 22 tests pass (415 total, 1 pre-existing failure in unrelated file).

### Deviations from Plan

- `getEventStyle` from `timeUtils` reused for block top/height calculation (instead of inline formula)
- `formatHour` from `timeUtils` reused (instead of local helper)
- Parent gains its own 60s interval (same as NowIndicator) so `activeBlockId` re-evaluates across block boundaries — not in original plan but needed for correctness
- `useEffect` auto-scroll uses `[startHour, endHour, hourHeight]` deps (not `[]`) and reads `new Date()` internally to avoid stale closure
- NowIndicator boundary uses `>= endHour * 60` (exclusive end) for consistency with active-block detection
