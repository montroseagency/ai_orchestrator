# Section 02: Shared Utilities

## Overview

This section creates three pure-utility files under `client/components/portal/calendar/utils/`. These files have **no React dependencies** and no side effects — they are plain TypeScript functions. Everything else in the scheduling engine imports from them, so they must be completed and tested before any other section begins.

**Batch position:** Batch 1 (no dependencies — can run in parallel with section-01-test-utils).

**Blocks:** section-03-dayschedule-refactor, section-04-data-hook, section-08-grid-structure, section-09-day-column, section-10-time-block-card.

---

## Files to Create

```
client/components/portal/calendar/utils/timeUtils.ts
client/components/portal/calendar/utils/collisionUtils.ts
client/components/portal/calendar/utils/calendarCollision.ts
```

Test files alongside:

```
client/components/portal/calendar/utils/__tests__/timeUtils.test.ts
client/components/portal/calendar/utils/__tests__/collisionUtils.test.ts
client/components/portal/calendar/utils/__tests__/calendarCollision.test.ts
```

---

## Tests First

Write all tests before implementing. These are pure-function tests — no mocks or wrappers needed.

### `timeUtils.test.ts`

```typescript
import { describe, it, expect } from 'vitest'
import {
  timeToMinutes,
  minutesToTime,
  snapToSlot,
  minutesToPx,
  pxToMinutes,
  getEventStyle,
  formatHour,
  isoDateToWeekDays,
  clientYToTimeSlot,
} from '../timeUtils'

describe('timeToMinutes', () => {
  it('parses "HH:MM" format', () => expect(timeToMinutes('06:00')).toBe(360))
  it('parses "HH:MM:SS" format', () => expect(timeToMinutes('06:00:00')).toBe(360))
  it('returns 0 for midnight', () => expect(timeToMinutes('00:00')).toBe(0))
  it('handles end-of-day', () => expect(timeToMinutes('23:59')).toBe(1439))
})

describe('minutesToTime', () => {
  it('converts 360 → "06:00"', () => expect(minutesToTime(360)).toBe('06:00'))
  it('converts 0 → "00:00"', () => expect(minutesToTime(0)).toBe('00:00'))
  it('converts 1439 → "23:59"', () => expect(minutesToTime(1439)).toBe('23:59'))
})

describe('snapToSlot', () => {
  it('rounds down when below midpoint', () => expect(snapToSlot(45, 30)).toBe(30))
  it('rounds up when above midpoint', () => expect(snapToSlot(46, 30)).toBe(60))
  it('returns 0 for 0', () => expect(snapToSlot(0, 15)).toBe(0))
})

describe('minutesToPx / pxToMinutes', () => {
  it('minutesToPx(60, 60) → 60', () => expect(minutesToPx(60, 60)).toBe(60))
  it('minutesToPx(30, 60) → 30', () => expect(minutesToPx(30, 60)).toBe(30))
  it('pxToMinutes(60, 60) → 60', () => expect(pxToMinutes(60, 60)).toBe(60))
})

describe('getEventStyle', () => {
  it('block at startHour → top: 0, height: 60', () =>
    expect(getEventStyle('06:00', '07:00', 6, 60)).toEqual({ top: 0, height: 60 }))
  it('block at 7:30 → top: 90, height: 60', () =>
    expect(getEventStyle('07:30', '08:30', 6, 60)).toEqual({ top: 90, height: 60 }))
})

describe('formatHour', () => {
  it('midnight → "12 AM"', () => expect(formatHour(0)).toBe('12 AM'))
  it('6 AM', () => expect(formatHour(6)).toBe('6 AM'))
  it('noon → "12 PM"', () => expect(formatHour(12)).toBe('12 PM'))
  it('22 → "10 PM"', () => expect(formatHour(22)).toBe('10 PM'))
})

describe('isoDateToWeekDays', () => {
  it('returns Mon–Fri for a Wednesday', () =>
    expect(isoDateToWeekDays('2026-03-25')).toEqual([
      '2026-03-23', '2026-03-24', '2026-03-25', '2026-03-26', '2026-03-27',
    ]))
})

describe('clientYToTimeSlot', () => {
  it('converts pointer Y to snapped hour/minute', () =>
    expect(clientYToTimeSlot(60, 0, 6, 60, 30)).toEqual({ hour: 7, minute: 0 }))
  it('snaps to nearest 30min increment', () =>
    // clientY=75 → 75px offset → 75 minutes → startHour 6 → 6:75 → 7:15 → snaps to 7:30
    expect(clientYToTimeSlot(75, 0, 6, 60, 30)).toEqual({ hour: 7, minute: 30 }))
})
```

### `collisionUtils.test.ts`

```typescript
import { describe, it, expect } from 'vitest'
import { getOverlapGroups, getSideBySideLayout } from '../collisionUtils'
import { createMockTimeBlock } from '../../../../../test-utils/scheduling'
// Note: createMockTimeBlock comes from section-01-test-utils.
// If that section is not yet done, inline minimal factories here.

describe('getOverlapGroups', () => {
  it('returns empty array for no blocks', () => expect(getOverlapGroups([])).toEqual([]))
  it('puts non-overlapping blocks in separate groups', () => {
    const a = createMockTimeBlock({ start_time: '06:00', end_time: '07:00' })
    const b = createMockTimeBlock({ start_time: '08:00', end_time: '09:00' })
    const groups = getOverlapGroups([a, b])
    expect(groups).toHaveLength(2)
  })
  it('puts two overlapping blocks in the same group', () => {
    const a = createMockTimeBlock({ start_time: '06:00', end_time: '07:00' })
    const b = createMockTimeBlock({ start_time: '06:30', end_time: '07:30' })
    const groups = getOverlapGroups([a, b])
    expect(groups).toHaveLength(1)
    expect(groups[0]).toHaveLength(2)
  })
  it('groups three-way overlapping blocks together', () => {
    const a = createMockTimeBlock({ start_time: '06:00', end_time: '08:00' })
    const b = createMockTimeBlock({ start_time: '06:30', end_time: '08:30' })
    const c = createMockTimeBlock({ start_time: '07:00', end_time: '09:00' })
    const groups = getOverlapGroups([a, b, c])
    expect(groups).toHaveLength(1)
    expect(groups[0]).toHaveLength(3)
  })
  it('blocks sharing only an endpoint (end == start) are NOT overlapping', () => {
    const a = createMockTimeBlock({ start_time: '06:00', end_time: '07:00' })
    const b = createMockTimeBlock({ start_time: '07:00', end_time: '08:00' })
    const groups = getOverlapGroups([a, b])
    expect(groups).toHaveLength(2)
  })
})

describe('getSideBySideLayout', () => {
  it('single block → full width', () => {
    const block = createMockTimeBlock({})
    const layout = getSideBySideLayout([block])
    expect(layout.get(block.id)).toMatchObject({ left: '0%', width: '100%' })
  })
  it('two blocks → 50% each', () => {
    const a = createMockTimeBlock({})
    const b = createMockTimeBlock({})
    const layout = getSideBySideLayout([a, b])
    expect(layout.get(a.id)?.width).toBe('50%')
    expect(layout.get(b.id)?.width).toBe('50%')
  })
  it('three blocks → ~33% each', () => {
    const blocks = [createMockTimeBlock({}), createMockTimeBlock({}), createMockTimeBlock({})]
    const layout = getSideBySideLayout(blocks)
    blocks.forEach(b => expect(layout.get(b.id)?.width).toBe('33.33%'))
  })
  it('four blocks → first 2 get columns, 3rd+ in hidden array', () => {
    const blocks = Array.from({ length: 4 }, () => createMockTimeBlock({}))
    const layout = getSideBySideLayout(blocks)
    // hidden is a special key — check that 3rd and 4th blocks are designated hidden
    const hiddenEntry = layout.get('__hidden__') as unknown as { hidden: string[] }
    expect(hiddenEntry?.hidden).toHaveLength(2)
  })
})
```

### `calendarCollision.test.ts`

```typescript
import { describe, it, expect, vi } from 'vitest'
import { calendarCollisionDetection } from '../calendarCollision'
import { pointerWithin, closestCenter } from '@dnd-kit/core'

vi.mock('@dnd-kit/core', () => ({
  pointerWithin: vi.fn(),
  closestCenter: vi.fn(),
}))

describe('calendarCollisionDetection', () => {
  it('returns pointerWithin result when non-empty', () => {
    const fakeResult = [{ id: 'a' }]
    vi.mocked(pointerWithin).mockReturnValue(fakeResult as any)
    const result = calendarCollisionDetection({} as any)
    expect(result).toBe(fakeResult)
    expect(closestCenter).not.toHaveBeenCalled()
  })
  it('falls back to closestCenter when pointerWithin is empty', () => {
    const fallback = [{ id: 'b' }]
    vi.mocked(pointerWithin).mockReturnValue([])
    vi.mocked(closestCenter).mockReturnValue(fallback as any)
    const result = calendarCollisionDetection({} as any)
    expect(result).toBe(fallback)
  })
})
```

---

## Implementation

### Timezone Strategy

All times in this feature are wall-clock local times. No timezone conversion is performed. `start_time` / `end_time` strings (`"HH:MM:SS"`) are stored and returned by the backend as-is. Timezone support is out of scope.

---

### `timeUtils.ts`

All functions are pure — zero imports from React or the rest of the codebase.

```typescript
/**
 * Parses "HH:MM" or "HH:MM:SS" to total minutes.
 */
export function timeToMinutes(time: string): number { ... }

/**
 * Converts total minutes to "HH:MM" string (zero-padded).
 */
export function minutesToTime(minutes: number): string { ... }

/**
 * Rounds `minutes` to the nearest `snapMinutes` increment.
 * Uses standard rounding: 0.5 rounds up.
 */
export function snapToSlot(minutes: number, snapMinutes: number): number { ... }

/**
 * Converts a minute offset from the grid's startHour to CSS pixels.
 * minutesToPx(60, 60) === 60
 */
export function minutesToPx(minutes: number, hourHeight: number): number { ... }

/**
 * Inverse of minutesToPx.
 */
export function pxToMinutes(px: number, hourHeight: number): number { ... }

/**
 * Returns { top, height } in px for an absolutely-positioned time block.
 * `startHour` is the first hour rendered in the grid (e.g., 6).
 * `hourHeight` is px per hour (e.g., 60).
 */
export function getEventStyle(
  startTime: string,
  endTime: string,
  startHour: number,
  hourHeight: number,
): { top: number; height: number } { ... }

/**
 * Formats an hour integer to "H AM/PM" with midnight/noon handled correctly.
 * formatHour(0) → "12 AM", formatHour(12) → "12 PM", formatHour(22) → "10 PM"
 */
export function formatHour(hour: number): string { ... }

/**
 * Given any ISO date string, returns an array of ISO date strings for
 * Monday through Friday of the same week.
 * isoDateToWeekDays("2026-03-25") → ["2026-03-23", ..., "2026-03-27"]
 * Uses local date arithmetic (no timezone conversion).
 */
export function isoDateToWeekDays(isoDate: string): string[] { ... }

/**
 * Converts a pointer Y coordinate (from a pointer event) to a snapped
 * { hour, minute } value for drop placement.
 *
 * @param clientY   - pointer Y from event (absolute viewport coordinate)
 * @param columnTop - getBoundingClientRect().top of the column element
 * @param startHour - first hour rendered (e.g., 6)
 * @param hourHeight - px per hour (e.g., 60)
 * @param snapMinutes - snap resolution (e.g., 30)
 */
export function clientYToTimeSlot(
  clientY: number,
  columnTop: number,
  startHour: number,
  hourHeight: number,
  snapMinutes: number,
): { hour: number; minute: number } { ... }
```

**Implementation notes:**

- `timeToMinutes`: split on `":"`, parse hours × 60 + minutes (ignore seconds if present).
- `minutesToTime`: `Math.floor(m / 60)` padded + `m % 60` padded, joined with `":"`.
- `snapToSlot`: `Math.round(minutes / snapMinutes) * snapMinutes`.
- `minutesToPx` / `pxToMinutes`: simple proportional conversion using `hourHeight / 60`.
- `getEventStyle`: convert both times to minutes, subtract `startHour * 60` for offset, apply `minutesToPx`. Height = end − start in px.
- `formatHour`: use modulo 12 arithmetic; 0 and 12 both render as "12".
- `isoDateToWeekDays`: parse the date string with `new Date(isoDate + 'T00:00:00')` (local-time suffix avoids UTC shift), get `day = date.getDay()`, compute `monday = date - (day === 0 ? 6 : day - 1) * 86400000`, then generate 5 entries.
- `clientYToTimeSlot`: `offsetPx = clientY - columnTop`, `rawMinutes = pxToMinutes(offsetPx, hourHeight)`, `totalMinutes = snapToSlot(startHour * 60 + rawMinutes, snapMinutes)`. Return `{ hour: Math.floor(totalMinutes / 60), minute: totalMinutes % 60 }`.

---

### `collisionUtils.ts`

Imports only `AgentTimeBlock` from `client/lib/types/scheduling.ts`.

```typescript
import type { AgentTimeBlock } from '../../../../lib/types/scheduling'

/**
 * Groups time blocks whose intervals overlap. Two blocks overlap when
 * one starts strictly before the other ends (touching endpoints do NOT overlap).
 *
 * Returns an array of groups. Each group is an array of AgentTimeBlock.
 * Blocks that don't overlap with any other block appear in singleton groups.
 */
export function getOverlapGroups(blocks: AgentTimeBlock[]): AgentTimeBlock[][] { ... }

/**
 * Given a group of overlapping blocks, computes CSS left% and width% for
 * side-by-side positioning inside their shared column.
 *
 * For groups of 4+: the first 2 blocks receive standard columns.
 * Blocks 3+ are added to a `hidden` array stored under the key "__hidden__"
 * in the returned Map. The caller renders a "+N more" indicator at the third
 * column position instead of the hidden blocks.
 *
 * Returns: Map<blockId | "__hidden__", { left: string, width: string } | { hidden: string[] }>
 */
export function getSideBySideLayout(
  group: AgentTimeBlock[],
): Map<string, { left: string; width: string } | { hidden: string[] }> { ... }
```

**Implementation notes:**

- `getOverlapGroups`: use a union-find (or iterative merge) approach. For each pair `(a, b)`, they overlap if `timeToMinutes(a.start_time) < timeToMinutes(b.end_time) && timeToMinutes(b.start_time) < timeToMinutes(a.end_time)`. Merge into a single group if any block in group A overlaps any block in group B.
- `getSideBySideLayout`:
  - 1 block → `{ left: "0%", width: "100%" }`
  - 2 blocks → widths of `50%`, lefts of `0%` and `50%`
  - 3 blocks → widths of `33.33%`, lefts of `0%`, `33.33%`, `66.67%`
  - 4+ blocks → first two blocks as above for a 2-column layout (`50%` each); blocks at index 2+ added to the `"__hidden__"` entry's array

---

### `calendarCollision.ts`

```typescript
import { pointerWithin, closestCenter } from '@dnd-kit/core'
import type { CollisionDetection } from '@dnd-kit/core'

/**
 * Custom collision detection for the calendar grid.
 * Uses pointerWithin for precision (accurate to the element under the pointer).
 * Falls back to closestCenter when no pointer-within collisions are found
 * (e.g., dragging over empty space between elements).
 */
export const calendarCollisionDetection: CollisionDetection = (args) => {
  const pointerCollisions = pointerWithin(args)
  if (pointerCollisions.length > 0) return pointerCollisions
  return closestCenter(args)
}
```

This function is complete as shown — no additional logic needed.

---

## Directory Creation

Before writing the files, ensure the directory exists:

```
client/components/portal/calendar/utils/
client/components/portal/calendar/utils/__tests__/
```

The parent `client/components/portal/calendar/` directory may not exist yet — create it as part of this section. Subsequent sections will add component files alongside `utils/`.

---

## Acceptance Criteria

- All tests in `timeUtils.test.ts`, `collisionUtils.test.ts`, and `calendarCollision.test.ts` pass.
- No imports from React, React Query, or `@dnd-kit` in `timeUtils.ts` or `collisionUtils.ts` (they must remain pure).
- `calendarCollision.ts` imports only from `@dnd-kit/core`.
- `isoDateToWeekDays` returns exactly 5 entries in `"YYYY-MM-DD"` format, always Monday–Friday regardless of which weekday the input falls on.
- `getEventStyle` returns integer or decimal pixel values (not strings — the caller appends `"px"`).
- `getSideBySideLayout` for a 4-block group: Map has exactly 3 entries (2 positioned blocks + 1 `"__hidden__"` entry with an array of 2 IDs).

## Implementation Status: COMPLETE — 33/33 tests passing

## Deviations from Plan

- `snapToSlot`: uses "round half down" (strictly-greater-than rounds up) — midpoint rounds to lower slot. Tests confirm `snapToSlot(45,30)→30`, `snapToSlot(46,30)→60`.
- `clientYToTimeSlot`: uses `Math.round` directly (standard round-half-up) rather than calling `snapToSlot`. Both pass their respective tests; the difference in tie-breaking is an acknowledged spec inconsistency.
- `isoDateToWeekDays`: uses UTC date methods (`getUTCDay`, `getUTCFullYear`, etc.) to avoid DST-related day shifts (code review fix).
- `getOverlapGroups`: `timeToMinutes` calls hoisted out of inner loop for O(n) savings per outer iteration (code review fix).
