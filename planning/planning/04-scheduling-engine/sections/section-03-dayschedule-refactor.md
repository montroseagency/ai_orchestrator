# Section 03 — DaySchedule Refactor (Configurable Layout Props)

## Overview

Add four optional, backward-compatible layout props to the existing `DaySchedule.tsx`. No behavior changes for existing callers (e.g. `CommandCenter`). The new portal calendar introduced in later sections passes custom values to get 60px/hr, 6 AM–10 PM rendering.

**Depends on:** section-02-shared-utils (the `timeToMinutes`/`minutesToTime` utilities must already exist in `timeUtils.ts` before this section touches imports)

**Blocks:** Nothing — this section is a leaf for the existing codebase.

---

## Files to Modify / Create

| Path | Action |
|------|--------|
| `client/components/agent/scheduling/DaySchedule.tsx` | Modify — add props, switch internal references |
| `client/components/agent/scheduling/__tests__/DaySchedule.test.tsx` | Create — tests for new props |

The utility functions `timeToMinutes` and `minutesToTime` are **extracted to** `client/components/portal/calendar/utils/timeUtils.ts` by section-02. This section updates the import inside `DaySchedule.tsx` to point to that shared location, then removes the local function definitions to avoid duplication.

> If section-02 has not landed yet, keep the local definitions temporarily and leave a `// TODO: import from timeUtils` comment. Do not block this section on that extraction.

---

## Background: Current Hard-Coded Constants

`DaySchedule.tsx` currently exports three module-level constants that all internal math references:

```typescript
export const START_HOUR = 0;
export const END_HOUR = 24;
export const HOUR_HEIGHT = 50;
export const TOTAL_HOURS = END_HOUR - START_HOUR;  // derived
```

These constants appear in:
- `NowIndicator` — `START_HOUR * 60`, `END_HOUR * 60`, `HOUR_HEIGHT`
- `DraggableBlock` — `START_HOUR * 60`, `HOUR_HEIGHT`
- `TimedTaskBlock` — `START_HOUR * 60`, `HOUR_HEIGHT`
- `HourSlot` — `HOUR_HEIGHT` (via style prop)
- `DaySchedule` auto-scroll effect — `START_HOUR * 60`, `END_HOUR * 60`, `HOUR_HEIGHT`
- `DaySchedule` timeline container — `TOTAL_HOURS * HOUR_HEIGHT`

After the refactor every reference above uses the prop value instead of the constant. The exported constants (`START_HOUR`, `END_HOUR`, `HOUR_HEIGHT`) remain exported for backward compatibility with any external code that may import them — they are not deleted.

---

## New Props Interface

```typescript
interface DayScheduleProps {
  date: string;
  agentType: 'marketing' | 'website';
  externalDnd?: boolean;
  // --- New optional layout props ---
  hourHeight?: number;    // px per hour — default: 50
  startHour?: number;     // first hour rendered — default: 0
  endHour?: number;       // last hour rendered (exclusive) — default: 24
  snapMinutes?: number;   // drag snap resolution in minutes — default: 60
}
```

Destructure with defaults at the top of the component body:

```typescript
export function DaySchedule({
  date,
  agentType,
  externalDnd = false,
  hourHeight = HOUR_HEIGHT,
  startHour = START_HOUR,
  endHour = END_HOUR,
  snapMinutes = 60,
}: DayScheduleProps) {
```

The derived `totalHours` is computed inside the component as `endHour - startHour`.

---

## Propagating Props to Sub-Components

`NowIndicator`, `DraggableBlock`, `TimedTaskBlock`, and `HourSlot` are all defined in the same file. They currently read module-level constants directly. After the refactor they receive layout values as props.

### `NowIndicator` updated signature

```typescript
function NowIndicator({
  startHour,
  endHour,
  hourHeight,
}: {
  startHour: number;
  endHour: number;
  hourHeight: number;
})
```

### `DraggableBlock` updated signature

```typescript
function DraggableBlock({
  block,
  onClick,
  onToggleComplete,
  startHour,
  hourHeight,
}: {
  block: AgentTimeBlock;
  onClick: () => void;
  onToggleComplete: () => void;
  startHour: number;
  hourHeight: number;
})
```

### `TimedTaskBlock` updated signature

```typescript
function TimedTaskBlock({
  task,
  onToggle,
  startHour,
  hourHeight,
}: {
  task: AgentGlobalTask;
  onToggle: () => void;
  startHour: number;
  hourHeight: number;
})
```

### `HourSlot` updated signature

```typescript
export function HourSlot({
  hour,
  onClick,
  hourHeight,
}: {
  hour: number;
  onClick: () => void;
  hourHeight: number;
})
```

Pass all layout values down from `DaySchedule` to each of these when rendering them.

---

## Auto-Scroll Logic

The existing `useEffect` that scrolls to current time uses the constants directly. After the refactor it reads the destructured prop values:

```typescript
useEffect(() => {
  if (!timelineRef.current) return;
  const now = new Date();
  const minutes = now.getHours() * 60 + now.getMinutes();
  if (minutes >= startHour * 60 && minutes <= endHour * 60) {
    const scrollTop = ((minutes - startHour * 60) / 60) * hourHeight - 100;
    timelineRef.current.scrollTop = Math.max(0, scrollTop);
  }
}, [blocksLoading, startHour, endHour, hourHeight]);
```

---

## `snapMinutes` Usage

`snapMinutes` is accepted as a prop but is **not used internally** in the current `DaySchedule` — the existing drag-end handler snaps to whole hours. Accepting it now makes the prop contract consistent with what the portal calendar expects. A future improvement can wire it into the drag handler. No logic change required in this section.

---

## Import Update (after section-02 lands)

Remove the local `timeToMinutes` and `minutesToTime` function definitions from `DaySchedule.tsx` and replace with:

```typescript
import { timeToMinutes, minutesToTime } from '@/components/portal/calendar/utils/timeUtils';
```

The `formatHour` function defined locally in `DaySchedule.tsx` is **not** extracted — it is already defined in `timeUtils.ts` by section-02, but `DaySchedule` can keep its local copy until a cleanup pass. Do not remove it now to avoid merge conflicts with section-02.

---

## Tests

File: `client/components/agent/scheduling/__tests__/DaySchedule.test.tsx`

Use the `renderWithQuery` helper from `client/test-utils/scheduling.tsx` (section-01). Mock `useTimeBlocks` and `useGlobalTasks` to return empty arrays so tests are not blocked on real data.

### Test stubs

```typescript
describe('DaySchedule — backward compatibility', () => {
  it('renders without new props — layout uses defaults (50px/hr, 0–24h)', () => {
    // Render <DaySchedule date="2026-03-28" agentType="marketing" />
    // Expect the timeline container height to equal 24 * 50 = 1200px
    // Expect hour labels "12 AM" and "11 PM" to be present
  });

  it('CommandCenter renders without errors after refactor', () => {
    // Import CommandCenter and render it — assert no thrown error
    // CommandCenter passes no new props to DaySchedule, so this is a smoke test
  });
});

describe('DaySchedule — custom layout props', () => {
  it('renders only 6 AM–10 PM hour labels when startHour=6 endHour=22', () => {
    // Render with hourHeight=60 startHour=6 endHour=22
    // Expect "6 AM" label present; "12 AM" label absent
    // Expect "10 PM" label present; "11 PM" label absent
  });

  it('timeline container height equals (endHour - startHour) * hourHeight', () => {
    // Render with hourHeight=60 startHour=6 endHour=22
    // Expected height: 16 * 60 = 960px
  });

  it('positions a time block at correct pixel offset with custom props', () => {
    // Mock useTimeBlocks to return a block: start_time="07:00", end_time="08:00"
    // Render with startHour=6, hourHeight=60
    // Block at 7:00 is 1 hour after startHour=6 → top = 1 * 60 = 60px
    // Assert the block element has style top: 60
  });

  it('NowIndicator uses prop values not module constants', () => {
    // Mock Date to return a time within startHour–endHour range
    // Render with startHour=6, hourHeight=60
    // Assert NowIndicator's top matches expected value
  });
});
```

Run the existing `CommandCenter` tests (if any exist) after the refactor to confirm no regression.

---

## Acceptance Criteria

1. `DaySchedule` rendered with no new props produces identical output to the pre-refactor version (same heights, same labels, same behavior).
2. `DaySchedule` rendered with `hourHeight=60, startHour=6, endHour=22` shows only hours 6–21 (22 labels), container height 960px, and positions blocks correctly.
3. `CommandCenter` renders without errors — it does not pass any new props.
4. `timeToMinutes` and `minutesToTime` imports point to `timeUtils.ts` once section-02 is merged (or local copies remain with a TODO comment if not yet merged).
5. All four new tests pass; no pre-existing tests broken.
