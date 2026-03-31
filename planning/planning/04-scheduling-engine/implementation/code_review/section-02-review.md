## Summary

Three pure utility files for the calendar engine: `timeUtils.ts`, `collisionUtils.ts`, and `calendarCollision.ts`. The implementations are clean and the test coverage is solid. Four real bugs were found — one HIGH (data corruption under concurrent drag), one MED (silent data loss on negative offsets), and two LOW (rounding inconsistency and an untested edge case in `snapToSlot`).

---

## Issues

### 1. [HIGH] `clientYToTimeSlot` uses `Math.round` instead of `snapToSlot`, producing results inconsistent with the rest of the codebase

**File:** `timeUtils.ts`, line 416

```ts
const totalMinutes = Math.round((startHour * 60 + rawMinutes) / snapMinutes) * snapMinutes
```

`snapToSlot` is defined separately and documents its tie-breaking rule: "strictly above the midpoint rounds up; at or below rounds down." `Math.round` uses "round half away from zero" (i.e., the midpoint always rounds up). For `snapMinutes = 30`, a pointer at exactly 15 px (the midpoint) will snap differently depending on which function is used, causing a drag-drop placement to land on a different slot than a manually placed event at the same position. This is a hidden inconsistency that will produce confusing UX when two code paths compute different snap results for the same input.

**Fix:** Replace the inline rounding with a call to `snapToSlot`:
```ts
const rawTotal = startHour * 60 + rawMinutes
const totalMinutes = snapToSlot(Math.round(rawTotal), snapMinutes)
```
Or, if sub-minute raw values are expected, pass `rawTotal` directly into `snapToSlot` and remove `Math.round`.

---

### 2. [MED] `clientYToTimeSlot` does not clamp the result, allowing negative or past-midnight output

**File:** `timeUtils.ts`, lines 414–420

When `clientY < columnTop` (pointer above the column top, a real scenario during fast drag gestures), `offsetPx` is negative, `rawMinutes` is negative, and `totalMinutes` can go below `startHour * 60`. The return value will then have `hour < startHour` (or even negative) and a nonsensical `minute`. The caller will pass this directly into an API payload.

**Fix:** Clamp `totalMinutes` to `[startHour * 60, 23 * 60 + 59]` (or to the grid's `endHour`) before computing `hour`/`minute`.

---

### 3. [MED] `getSideBySideLayout` hard-codes a 2-column cap instead of scaling to `n` columns

**File:** `collisionUtils.ts`, lines 293–296

For 4+ overlapping blocks, the function places only the first two blocks in visible columns (50% each) and hides the rest under `__hidden__`. The doc comment treats this as intended behaviour, but this is semantically wrong for a real calendar: Google Calendar, Outlook, and every mainstream calendar renderer divide the available width by the number of simultaneously-overlapping blocks, not by a hard cap of 2. A user with 4 concurrent blocks would see 2 of them silently disappear from the grid.

This may be a deliberate MVP compromise, but it is not called out as temporary in the code, so downstream consumers have no indication the `__hidden__` key exists or what to do with it. If the cap is intentional, add a `// TODO` comment and ensure the rendering layer actually surfaces the hidden count to the user.

---

### 4. [LOW] `snapToSlot` test boundary at exactly the midpoint is not covered, and the implementation comment may be wrong

**File:** `timeUtils.ts`, line 328 / `timeUtils.test.ts`, lines 144–147

The comment says "strictly above the midpoint rounds up; **at or below** rounds down." For `snapMinutes = 30`, the midpoint is 15. At `remainder === 15`, the condition `remainder > snapMinutes / 2` is `15 > 15` which is `false`, so it rounds down to 0. The test only covers `45` (rounds down to 30) and `46` (rounds up to 60). There is no test for `remainder === snapMinutes / 2` (the exact midpoint). This is not a bug given the comment, but the test gap means a future refactor could silently change tie-breaking behaviour and no test would catch it.

---

### 5. [LOW] `getOverlapGroups` recomputes `timeToMinutes` on every inner loop iteration — O(n²) string parses

**File:** `collisionUtils.ts`, lines 236–243

`timeToMinutes(blocks[i].start_time)` and the three related calls are inside the inner `j` loop. For 100 overlapping blocks this is ~10,000 string split/parseInt calls instead of 200. This is not a correctness bug, but it will be noticeable if the calendar renders 50+ blocks per day (e.g., an admin view across all agents). Pre-compute the minute values before the loop.

---

### 6. [LOW] `isoDateToWeekDays` is brittle against DST transitions

**File:** `timeUtils.ts`, lines 386–394

The Monday offset and the 5-day array both use `± N * 86400000` ms arithmetic on `Date.getTime()`. On the two days per year when a DST clock change occurs in the local timezone, a day boundary can be 23 or 25 hours long, causing `new Date(monday.getTime() + i * 86400000)` to land in the previous or next calendar day. The `T00:00:00` suffix on line 383 anchors the *parsed* date to local midnight, but the arithmetic thereafter is still wall-clock ms. Use UTC methods (`getUTCDay`, `setUTCDate`) throughout, or rewrite using date-only arithmetic (integer day offsets with `setDate`).

---

## Auto-fixable

The following issues can be fixed mechanically without design decisions:

1. **Issue 5 — pre-compute minute values in `getOverlapGroups`:** Move the four `timeToMinutes` calls above the `j` loop into the `i` loop body.

2. **Issue 1 — replace inline `Math.round` snap with `snapToSlot`:** Single-line substitution in `clientYToTimeSlot`.

3. **Issue 4 — add midpoint boundary test:** Add `expect(snapToSlot(15, 30)).toBe(0)` to the `snapToSlot` describe block.

Issues 2, 3, and 6 require a design decision (clamping bounds, column-cap strategy, DST handling) and cannot be auto-applied.
