# Section 06: CalendarHeader and Navigation

## Overview

This section implements `CalendarHeader.tsx`, the top navigation bar of the scheduling calendar. It provides the Day/Week view toggle, previous/next navigation arrows, a date picker, a human-readable date display string, and bidirectional sync with the URL query param `?date=`.

**Batch position:** Batch 3 (parallel with sections 07, 08, 10, 12 — after section 04 completes).

**Dependencies:**
- `section-04-data-hook` — provides `viewMode`, `setViewMode`, `selectedDate`, `setSelectedDate` from `useSchedulingEngine`
- `section-02-shared-utils` — provides `isoDateToWeekDays` and `formatHour` (not directly used here, but the week day range label requires ISO date arithmetic consistent with that utility)

**Blocks:** `section-05-scheduling-engine` (CalendarHeader is composed inside SchedulingEngine)

---

## File to Create

```
client/components/portal/calendar/CalendarHeader.tsx
```

---

## Tests First

File: `client/components/portal/calendar/CalendarHeader.test.tsx`

Use `renderWithQuery` from `client/test-utils/scheduling.tsx` (section 01). Mock `useSchedulingEngine` with `mockUseSchedulingEngine()`. Mock `next/navigation` (`useSearchParams`, `useRouter`) using `vi.mock('next/navigation', ...)`.

### Test stubs

```typescript
describe('CalendarHeader', () => {
  it('renders "Day" and "Week" toggle buttons')
  // Verify both buttons are present in the DOM.

  it('clicking "Week" calls setViewMode("week")')
  // Click the "Week" button; assert the mock setViewMode was called with "week".

  it('clicking "Day" calls setViewMode("day")')
  // Click the "Day" button; assert setViewMode was called with "day".

  it('clicking "Week" writes "week" to localStorage key scheduler_view_mode')
  // After click, assert localStorage.getItem('scheduler_view_mode') === 'week'.

  it('clicking "Day" writes "day" to localStorage key scheduler_view_mode')

  it('◀ button calls setSelectedDate with the previous day in Day view')
  // When viewMode="day" and selectedDate="2026-03-25", clicking ◀
  // must call setSelectedDate("2026-03-24").

  it('▶ button calls setSelectedDate with the next day in Day view')
  // When viewMode="day" and selectedDate="2026-03-25", clicking ▶
  // must call setSelectedDate("2026-03-26").

  it('◀ button calls setSelectedDate with 7 days back in Week view')
  // When viewMode="week" and selectedDate="2026-03-25", clicking ◀
  // must call setSelectedDate("2026-03-18").

  it('▶ button calls setSelectedDate with 7 days forward in Week view')
  // When viewMode="week" and selectedDate="2026-03-25", clicking ▶
  // must call setSelectedDate("2026-04-01").

  it('date picker input change calls setSelectedDate with the new value')
  // Simulate changing <input type="date"> to "2026-04-01";
  // assert setSelectedDate("2026-04-01") was called.

  it('Day view shows a single formatted date label')
  // When viewMode="day" and selectedDate="2026-03-28",
  // the header shows "March 28, 2026" (or equivalent locale format).

  it('Week view shows a Mon–Fri range label')
  // When viewMode="week" and selectedDate="2026-03-25" (a Wednesday),
  // the header shows something like "Mar 23 – 27, 2026".

  it('on mount reads scheduler_view_mode from localStorage and applies it')
  // Seed localStorage.setItem('scheduler_view_mode', 'week') before render;
  // assert setViewMode('week') is called (or that the "Week" button appears active).

  it('URL param ?date= is updated when setSelectedDate is called')
  // After a ▶ click, assert router.push or router.replace was called
  // with a URL containing ?date=<newDate>.
})
```

---

## Implementation Details

### Props interface

```typescript
interface CalendarHeaderProps {
  viewMode: 'day' | 'week'
  setViewMode: (mode: 'day' | 'week') => void
  selectedDate: string          // ISO date string "YYYY-MM-DD"
  setSelectedDate: (date: string) => void
}
```

Props are passed down from `SchedulingEngine`, which gets them from `useSchedulingEngine`.

### localStorage persistence

On mount, read `localStorage.getItem('scheduler_view_mode')` and call `setViewMode` if the stored value is `'day'` or `'week'`. This runs once via `useEffect([], [])`. On every `setViewMode` call, also write to `localStorage`.

Encapsulate with a small helper to avoid repetition:

```typescript
function persistViewMode(mode: 'day' | 'week') {
  localStorage.setItem('scheduler_view_mode', mode)
}
```

### URL query param sync

Use `useSearchParams()` and `useRouter()` from `next/navigation`.

On mount, if `?date=` is present in search params, call `setSelectedDate` with that value (initialization is actually handled by the portal page — see section 11 — but CalendarHeader is responsible for keeping the URL in sync on subsequent navigation).

Whenever `selectedDate` changes (track via `useEffect([selectedDate])`), call `router.replace` with the updated `?date=` param to keep the URL current without adding browser history entries.

```typescript
// Pseudo-code only — do not write full implementation
useEffect(() => {
  const params = new URLSearchParams(searchParams.toString())
  params.set('date', selectedDate)
  router.replace(`?${params.toString()}`)
}, [selectedDate])
```

### Date arithmetic for navigation

The `◀` and `▶` buttons compute the new date purely from the ISO date string and the current `viewMode`. Use standard `Date` arithmetic:

```typescript
function offsetDate(isoDate: string, days: number): string {
  // Parse isoDate, add/subtract days, return ISO date string "YYYY-MM-DD"
  // Use UTC dates to avoid DST-related off-by-one errors
}
```

- Day view: offset by `±1`
- Week view: offset by `±7`

### Date display string

- **Day view:** Format `selectedDate` as `"March 28, 2026"`. Use `new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })` or equivalent.
- **Week view:** Derive the Mon–Fri range for the week containing `selectedDate` using the same logic as `isoDateToWeekDays` from `timeUtils.ts`. Show the first (Monday) and last (Friday) dates as `"Mar 23 – 27, 2026"`. If month or year differs between the two ends, include both months/years in the label.

### Segmented control (Day/Week toggle)

Two adjacent buttons styled as a pill toggle. The active mode button has a filled/highlighted background. Clicking the inactive button calls `setViewMode` and `persistViewMode`.

Accessible: add `aria-pressed` to reflect active state, or wrap in a `role="group"` with `aria-label="View mode"`.

### Navigation arrows

Plain `<button>` elements labeled `◀` and `▶` (or accessible equivalents with `aria-label="Previous"` / `aria-label="Next"`). On click, call `setSelectedDate(offsetDate(selectedDate, ±step))`.

### Date picker

```tsx
<input
  type="date"
  value={selectedDate}
  onChange={(e) => setSelectedDate(e.target.value)}
  aria-label="Select date"
/>
```

Style the date picker to match the portal design language. It can be visually hidden behind a calendar icon button if the native picker appearance is unsatisfactory — but the underlying `<input type="date">` must remain accessible.

### Layout structure

```
[Title: "Calendar"]   [◀]  [date display string]  [▶]   [date picker 📅]   [Day | Week toggle]
```

The header is a `<header>` element with `display: flex`, `align-items: center`, `gap`. Use existing design tokens: `--color-border` for the bottom border, `--color-surface-subtle` for the background if needed.

---

## Design Notes

- The component is presentational: it receives all data and callbacks as props and does not call `useSchedulingEngine` directly. This makes testing straightforward.
- The only side effects are `localStorage` reads/writes and `router.replace` for URL sync — both isolated in `useEffect`.
- No spinner or loading state needed in the header itself.
- The "Calendar" title is static text.

---

## Acceptance Criteria

1. Clicking Day/Week toggle updates `viewMode` and writes to `localStorage`.
2. Navigation arrows advance/retreat by the correct step for the active view.
3. Date picker change immediately calls `setSelectedDate`.
4. Day view label shows a single full date; Week view shows the Mon–Fri span.
5. `?date=` URL param stays in sync with `selectedDate` after every navigation.
6. On mount, localStorage value for `scheduler_view_mode` is applied.
7. All 11 tests listed above pass.
