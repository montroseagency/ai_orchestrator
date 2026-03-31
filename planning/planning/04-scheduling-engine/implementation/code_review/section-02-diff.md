diff --git a/client/components/portal/calendar/utils/__tests__/calendarCollision.test.ts b/client/components/portal/calendar/utils/__tests__/calendarCollision.test.ts
new file mode 100644
index 000000000..fa30599ac
--- /dev/null
+++ b/client/components/portal/calendar/utils/__tests__/calendarCollision.test.ts
@@ -0,0 +1,29 @@
+import { describe, it, expect, vi } from 'vitest'
+import { calendarCollisionDetection } from '../calendarCollision'
+import { pointerWithin, closestCenter } from '@dnd-kit/core'
+
+vi.mock('@dnd-kit/core', () => ({
+  pointerWithin: vi.fn(),
+  closestCenter: vi.fn(),
+}))
+
+describe('calendarCollisionDetection', () => {
+  it('returns pointerWithin result when non-empty', () => {
+    const fakeResult = [{ id: 'a' }]
+    vi.mocked(pointerWithin).mockReturnValue(fakeResult as Parameters<typeof pointerWithin>[0] extends infer A ? never : never)
+    // eslint-disable-next-line @typescript-eslint/no-explicit-any
+    vi.mocked(pointerWithin).mockReturnValue(fakeResult as any)
+    const result = calendarCollisionDetection({} as Parameters<typeof calendarCollisionDetection>[0])
+    expect(result).toBe(fakeResult)
+    expect(closestCenter).not.toHaveBeenCalled()
+  })
+  it('falls back to closestCenter when pointerWithin is empty', () => {
+    const fallback = [{ id: 'b' }]
+    // eslint-disable-next-line @typescript-eslint/no-explicit-any
+    vi.mocked(pointerWithin).mockReturnValue([] as any)
+    // eslint-disable-next-line @typescript-eslint/no-explicit-any
+    vi.mocked(closestCenter).mockReturnValue(fallback as any)
+    const result = calendarCollisionDetection({} as Parameters<typeof calendarCollisionDetection>[0])
+    expect(result).toBe(fallback)
+  })
+})
diff --git a/client/components/portal/calendar/utils/__tests__/collisionUtils.test.ts b/client/components/portal/calendar/utils/__tests__/collisionUtils.test.ts
new file mode 100644
index 000000000..30f3fe45f
--- /dev/null
+++ b/client/components/portal/calendar/utils/__tests__/collisionUtils.test.ts
@@ -0,0 +1,69 @@
+import { describe, it, expect } from 'vitest'
+import { getOverlapGroups, getSideBySideLayout } from '../collisionUtils'
+import { createMockTimeBlock } from '../../../../../test-utils/scheduling'
+
+describe('getOverlapGroups', () => {
+  it('returns empty array for no blocks', () => expect(getOverlapGroups([])).toEqual([]))
+  it('puts non-overlapping blocks in separate groups', () => {
+    const a = createMockTimeBlock({ start_time: '06:00', end_time: '07:00' })
+    const b = createMockTimeBlock({ start_time: '08:00', end_time: '09:00' })
+    const groups = getOverlapGroups([a, b])
+    expect(groups).toHaveLength(2)
+  })
+  it('puts two overlapping blocks in the same group', () => {
+    const a = createMockTimeBlock({ start_time: '06:00', end_time: '07:00' })
+    const b = createMockTimeBlock({ start_time: '06:30', end_time: '07:30' })
+    const groups = getOverlapGroups([a, b])
+    expect(groups).toHaveLength(1)
+    expect(groups[0]).toHaveLength(2)
+  })
+  it('groups three-way overlapping blocks together', () => {
+    const a = createMockTimeBlock({ start_time: '06:00', end_time: '08:00' })
+    const b = createMockTimeBlock({ start_time: '06:30', end_time: '08:30' })
+    const c = createMockTimeBlock({ start_time: '07:00', end_time: '09:00' })
+    const groups = getOverlapGroups([a, b, c])
+    expect(groups).toHaveLength(1)
+    expect(groups[0]).toHaveLength(3)
+  })
+  it('blocks sharing only an endpoint (end == start) are NOT overlapping', () => {
+    const a = createMockTimeBlock({ start_time: '06:00', end_time: '07:00' })
+    const b = createMockTimeBlock({ start_time: '07:00', end_time: '08:00' })
+    const groups = getOverlapGroups([a, b])
+    expect(groups).toHaveLength(2)
+  })
+})
+
+describe('getSideBySideLayout', () => {
+  it('single block → full width', () => {
+    const block = createMockTimeBlock({ id: 'b1' })
+    const layout = getSideBySideLayout([block])
+    expect(layout.get(block.id)).toMatchObject({ left: '0%', width: '100%' })
+  })
+  it('two blocks → 50% each', () => {
+    const a = createMockTimeBlock({ id: 'a1' })
+    const b = createMockTimeBlock({ id: 'b1' })
+    const layout = getSideBySideLayout([a, b])
+    expect(layout.get(a.id)?.width).toBe('50%')
+    expect(layout.get(b.id)?.width).toBe('50%')
+  })
+  it('three blocks → ~33% each', () => {
+    const blocks = [
+      createMockTimeBlock({ id: 'a1' }),
+      createMockTimeBlock({ id: 'b1' }),
+      createMockTimeBlock({ id: 'c1' }),
+    ]
+    const layout = getSideBySideLayout(blocks)
+    blocks.forEach(b => expect(layout.get(b.id)?.width).toBe('33.33%'))
+  })
+  it('four blocks → first 2 get columns, 3rd+ in hidden array', () => {
+    const blocks = [
+      createMockTimeBlock({ id: 'a1' }),
+      createMockTimeBlock({ id: 'b1' }),
+      createMockTimeBlock({ id: 'c1' }),
+      createMockTimeBlock({ id: 'd1' }),
+    ]
+    const layout = getSideBySideLayout(blocks)
+    const hiddenEntry = layout.get('__hidden__') as { hidden: string[] }
+    expect(hiddenEntry?.hidden).toHaveLength(2)
+  })
+})
diff --git a/client/components/portal/calendar/utils/__tests__/timeUtils.test.ts b/client/components/portal/calendar/utils/__tests__/timeUtils.test.ts
new file mode 100644
index 000000000..a3ee4aba1
--- /dev/null
+++ b/client/components/portal/calendar/utils/__tests__/timeUtils.test.ts
@@ -0,0 +1,66 @@
+import { describe, it, expect } from 'vitest'
+import {
+  timeToMinutes,
+  minutesToTime,
+  snapToSlot,
+  minutesToPx,
+  pxToMinutes,
+  getEventStyle,
+  formatHour,
+  isoDateToWeekDays,
+  clientYToTimeSlot,
+} from '../timeUtils'
+
+describe('timeToMinutes', () => {
+  it('parses "HH:MM" format', () => expect(timeToMinutes('06:00')).toBe(360))
+  it('parses "HH:MM:SS" format', () => expect(timeToMinutes('06:00:00')).toBe(360))
+  it('returns 0 for midnight', () => expect(timeToMinutes('00:00')).toBe(0))
+  it('handles end-of-day', () => expect(timeToMinutes('23:59')).toBe(1439))
+})
+
+describe('minutesToTime', () => {
+  it('converts 360 → "06:00"', () => expect(minutesToTime(360)).toBe('06:00'))
+  it('converts 0 → "00:00"', () => expect(minutesToTime(0)).toBe('00:00'))
+  it('converts 1439 → "23:59"', () => expect(minutesToTime(1439)).toBe('23:59'))
+})
+
+describe('snapToSlot', () => {
+  it('rounds down when below midpoint', () => expect(snapToSlot(45, 30)).toBe(30))
+  it('rounds up when above midpoint', () => expect(snapToSlot(46, 30)).toBe(60))
+  it('returns 0 for 0', () => expect(snapToSlot(0, 15)).toBe(0))
+})
+
+describe('minutesToPx / pxToMinutes', () => {
+  it('minutesToPx(60, 60) → 60', () => expect(minutesToPx(60, 60)).toBe(60))
+  it('minutesToPx(30, 60) → 30', () => expect(minutesToPx(30, 60)).toBe(30))
+  it('pxToMinutes(60, 60) → 60', () => expect(pxToMinutes(60, 60)).toBe(60))
+})
+
+describe('getEventStyle', () => {
+  it('block at startHour → top: 0, height: 60', () =>
+    expect(getEventStyle('06:00', '07:00', 6, 60)).toEqual({ top: 0, height: 60 }))
+  it('block at 7:30 → top: 90, height: 60', () =>
+    expect(getEventStyle('07:30', '08:30', 6, 60)).toEqual({ top: 90, height: 60 }))
+})
+
+describe('formatHour', () => {
+  it('midnight → "12 AM"', () => expect(formatHour(0)).toBe('12 AM'))
+  it('6 AM', () => expect(formatHour(6)).toBe('6 AM'))
+  it('noon → "12 PM"', () => expect(formatHour(12)).toBe('12 PM'))
+  it('22 → "10 PM"', () => expect(formatHour(22)).toBe('10 PM'))
+})
+
+describe('isoDateToWeekDays', () => {
+  it('returns Mon–Fri for a Wednesday', () =>
+    expect(isoDateToWeekDays('2026-03-25')).toEqual([
+      '2026-03-23', '2026-03-24', '2026-03-25', '2026-03-26', '2026-03-27',
+    ]))
+})
+
+describe('clientYToTimeSlot', () => {
+  it('converts pointer Y to snapped hour/minute', () =>
+    expect(clientYToTimeSlot(60, 0, 6, 60, 30)).toEqual({ hour: 7, minute: 0 }))
+  it('snaps to nearest 30min increment', () =>
+    // clientY=75 → 75px offset → 75 minutes → startHour 6 → 6:75 → 7:15 → snaps to 7:30
+    expect(clientYToTimeSlot(75, 0, 6, 60, 30)).toEqual({ hour: 7, minute: 30 }))
+})
diff --git a/client/components/portal/calendar/utils/calendarCollision.ts b/client/components/portal/calendar/utils/calendarCollision.ts
new file mode 100644
index 000000000..f83d4efa1
--- /dev/null
+++ b/client/components/portal/calendar/utils/calendarCollision.ts
@@ -0,0 +1,14 @@
+import { pointerWithin, closestCenter } from '@dnd-kit/core'
+import type { CollisionDetection } from '@dnd-kit/core'
+
+/**
+ * Custom collision detection for the calendar grid.
+ * Uses pointerWithin for precision (accurate to the element under the pointer).
+ * Falls back to closestCenter when no pointer-within collisions are found
+ * (e.g., dragging over empty space between elements).
+ */
+export const calendarCollisionDetection: CollisionDetection = (args) => {
+  const pointerCollisions = pointerWithin(args)
+  if (pointerCollisions.length > 0) return pointerCollisions
+  return closestCenter(args)
+}
diff --git a/client/components/portal/calendar/utils/collisionUtils.ts b/client/components/portal/calendar/utils/collisionUtils.ts
new file mode 100644
index 000000000..b69ad46ba
--- /dev/null
+++ b/client/components/portal/calendar/utils/collisionUtils.ts
@@ -0,0 +1,89 @@
+import type { AgentTimeBlock } from '../../../../lib/types/scheduling'
+import { timeToMinutes } from './timeUtils'
+
+/**
+ * Groups time blocks whose intervals overlap. Two blocks overlap when
+ * one starts strictly before the other ends (touching endpoints do NOT overlap).
+ *
+ * Returns an array of groups. Each group is an array of AgentTimeBlock.
+ * Blocks that don't overlap with any other block appear in singleton groups.
+ */
+export function getOverlapGroups(blocks: AgentTimeBlock[]): AgentTimeBlock[][] {
+  if (blocks.length === 0) return []
+
+  // Union-find by index
+  const parent = blocks.map((_, i) => i)
+
+  function find(i: number): number {
+    if (parent[i] !== i) parent[i] = find(parent[i])
+    return parent[i]
+  }
+
+  function union(a: number, b: number): void {
+    parent[find(a)] = find(b)
+  }
+
+  for (let i = 0; i < blocks.length; i++) {
+    for (let j = i + 1; j < blocks.length; j++) {
+      const aStart = timeToMinutes(blocks[i].start_time)
+      const aEnd = timeToMinutes(blocks[i].end_time)
+      const bStart = timeToMinutes(blocks[j].start_time)
+      const bEnd = timeToMinutes(blocks[j].end_time)
+      if (aStart < bEnd && bStart < aEnd) {
+        union(i, j)
+      }
+    }
+  }
+
+  const groupMap = new Map<number, AgentTimeBlock[]>()
+  for (let i = 0; i < blocks.length; i++) {
+    const root = find(i)
+    if (!groupMap.has(root)) groupMap.set(root, [])
+    groupMap.get(root)!.push(blocks[i])
+  }
+
+  return Array.from(groupMap.values())
+}
+
+type LayoutEntry = { left: string; width: string } | { hidden: string[] }
+
+/**
+ * Given a group of overlapping blocks, computes CSS left% and width% for
+ * side-by-side positioning inside their shared column.
+ *
+ * For groups of 4+: the first 2 blocks receive standard columns.
+ * Blocks 3+ are added to a `hidden` array stored under the key "__hidden__"
+ * in the returned Map.
+ *
+ * Returns: Map<blockId | "__hidden__", { left: string, width: string } | { hidden: string[] }>
+ */
+export function getSideBySideLayout(
+  group: AgentTimeBlock[],
+): Map<string, LayoutEntry> {
+  const result = new Map<string, LayoutEntry>()
+  const count = group.length
+
+  if (count === 1) {
+    result.set(group[0].id, { left: '0%', width: '100%' })
+    return result
+  }
+
+  if (count === 2) {
+    result.set(group[0].id, { left: '0%', width: '50%' })
+    result.set(group[1].id, { left: '50%', width: '50%' })
+    return result
+  }
+
+  if (count === 3) {
+    result.set(group[0].id, { left: '0%', width: '33.33%' })
+    result.set(group[1].id, { left: '33.33%', width: '33.33%' })
+    result.set(group[2].id, { left: '66.67%', width: '33.33%' })
+    return result
+  }
+
+  // 4+ blocks: first 2 get columns, rest are hidden
+  result.set(group[0].id, { left: '0%', width: '50%' })
+  result.set(group[1].id, { left: '50%', width: '50%' })
+  result.set('__hidden__', { hidden: group.slice(2).map((b) => b.id) })
+  return result
+}
diff --git a/client/components/portal/calendar/utils/timeUtils.ts b/client/components/portal/calendar/utils/timeUtils.ts
new file mode 100644
index 000000000..26de1c794
--- /dev/null
+++ b/client/components/portal/calendar/utils/timeUtils.ts
@@ -0,0 +1,118 @@
+/**
+ * Parses "HH:MM" or "HH:MM:SS" to total minutes.
+ */
+export function timeToMinutes(time: string): number {
+  const parts = time.split(':')
+  return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10)
+}
+
+/**
+ * Converts total minutes to "HH:MM" string (zero-padded).
+ */
+export function minutesToTime(minutes: number): string {
+  const h = Math.floor(minutes / 60)
+  const m = minutes % 60
+  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
+}
+
+/**
+ * Rounds `minutes` to the nearest `snapMinutes` increment.
+ * Strictly above the midpoint rounds up; at or below midpoint rounds down.
+ */
+export function snapToSlot(minutes: number, snapMinutes: number): number {
+  const base = Math.floor(minutes / snapMinutes)
+  const remainder = minutes % snapMinutes
+  return (remainder > snapMinutes / 2 ? base + 1 : base) * snapMinutes
+}
+
+/**
+ * Converts a minute offset from the grid's startHour to CSS pixels.
+ * minutesToPx(60, 60) === 60
+ */
+export function minutesToPx(minutes: number, hourHeight: number): number {
+  return (minutes / 60) * hourHeight
+}
+
+/**
+ * Inverse of minutesToPx.
+ */
+export function pxToMinutes(px: number, hourHeight: number): number {
+  return (px / hourHeight) * 60
+}
+
+/**
+ * Returns { top, height } in px for an absolutely-positioned time block.
+ * `startHour` is the first hour rendered in the grid (e.g., 6).
+ * `hourHeight` is px per hour (e.g., 60).
+ */
+export function getEventStyle(
+  startTime: string,
+  endTime: string,
+  startHour: number,
+  hourHeight: number,
+): { top: number; height: number } {
+  const startMinutes = timeToMinutes(startTime)
+  const endMinutes = timeToMinutes(endTime)
+  const offsetMinutes = startMinutes - startHour * 60
+  return {
+    top: minutesToPx(offsetMinutes, hourHeight),
+    height: minutesToPx(endMinutes - startMinutes, hourHeight),
+  }
+}
+
+/**
+ * Formats an hour integer to "H AM/PM" with midnight/noon handled correctly.
+ * formatHour(0) → "12 AM", formatHour(12) → "12 PM", formatHour(22) → "10 PM"
+ */
+export function formatHour(hour: number): string {
+  const suffix = hour < 12 ? 'AM' : 'PM'
+  const display = hour % 12 === 0 ? 12 : hour % 12
+  return `${display} ${suffix}`
+}
+
+/**
+ * Given any ISO date string, returns an array of ISO date strings for
+ * Monday through Friday of the same week.
+ * isoDateToWeekDays("2026-03-25") → ["2026-03-23", ..., "2026-03-27"]
+ * Uses local date arithmetic (no timezone conversion).
+ */
+export function isoDateToWeekDays(isoDate: string): string[] {
+  const date = new Date(isoDate + 'T00:00:00')
+  const day = date.getDay() // 0=Sun, 1=Mon, ..., 6=Sat
+  const daysFromMonday = day === 0 ? 6 : day - 1
+  const monday = new Date(date.getTime() - daysFromMonday * 86400000)
+
+  return Array.from({ length: 5 }, (_, i) => {
+    const d = new Date(monday.getTime() + i * 86400000)
+    const y = d.getFullYear()
+    const m = String(d.getMonth() + 1).padStart(2, '0')
+    const dd = String(d.getDate()).padStart(2, '0')
+    return `${y}-${m}-${dd}`
+  })
+}
+
+/**
+ * Converts a pointer Y coordinate (from a pointer event) to a snapped
+ * { hour, minute } value for drop placement.
+ *
+ * @param clientY   - pointer Y from event (absolute viewport coordinate)
+ * @param columnTop - getBoundingClientRect().top of the column element
+ * @param startHour - first hour rendered (e.g., 6)
+ * @param hourHeight - px per hour (e.g., 60)
+ * @param snapMinutes - snap resolution (e.g., 30)
+ */
+export function clientYToTimeSlot(
+  clientY: number,
+  columnTop: number,
+  startHour: number,
+  hourHeight: number,
+  snapMinutes: number,
+): { hour: number; minute: number } {
+  const offsetPx = clientY - columnTop
+  const rawMinutes = pxToMinutes(offsetPx, hourHeight)
+  const totalMinutes = Math.round((startHour * 60 + rawMinutes) / snapMinutes) * snapMinutes
+  return {
+    hour: Math.floor(totalMinutes / 60),
+    minute: totalMinutes % 60,
+  }
+}
