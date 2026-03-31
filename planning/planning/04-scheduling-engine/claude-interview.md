# Interview Transcript: Interactive Scheduling Engine

## Q1: What's the correct filter for 'unscheduled' tasks in the backlog?

**Options presented:**
- scheduled_date = selected date AND time_block = null
- time_block = null (any date — global pool)
- Both, in sections

**Answer:** Both, in sections.
- Section 1: Tasks where scheduled_date = selected date AND time_block = null
- Section 2: Overdue / undated tasks (no scheduled_date, or scheduled_date in the past, with no time_block)

---

## Q2: How are multi-day tasks modeled?

**Options presented:**
- New concept — add span_start_date / span_end_date fields
- Use scheduled_date + estimated_minutes only
- Out of scope for this split

**Answer:** Use scheduled_date + estimated_minutes only.
No date range fields needed. "Multi-day" means the task has a large `estimated_minutes` value but is scheduled to a single date. If a task spans multiple days conceptually, it appears in each relevant day's backlog via recurrence, not via a date range. This keeps the data model simple.

---

## Q3: Should the new Management Calendar replace or coexist with the old /schedule?

**Options presented:**
- Both coexist
- New replaces old
- Soft replace

**Answer:** Both coexist — old /schedule stays, new /management/calendar is the portal version.
No regression risk. The old CommandCenter is heavily used and has many features beyond scheduling (stats, focus timer, quick tasks). The new portal calendar is a standalone, purpose-built scheduling interface.

---

## Q4: Should HOUR_HEIGHT be changed globally or only in the new component?

**Options presented:**
- New component only
- Update globally

**Answer:** Refactor to Configurable Props.
Rather than choosing "old" or "new," refactor DaySchedule to accept layout configuration as props:
- `hourHeight` (default: 50px for backward compat)
- `startHour` / `endHour` (defaults: 0 / 24 for backward compat)
- The new portal calendar passes 60px, 6, 22
- The old CommandCenter passes nothing (gets defaults = unchanged behavior)

---

## Q5: For collision behavior — should drops be blocked, warned, or resolved?

**Options presented:**
- Block the drop
- Allow with warning toast
- (User free-text: Resolve)

**Answer:** Collision Resolution — implement Side-by-Side.
The user recommends a "premium" approach where drops are never simply blocked or warned. Instead:

**Side-by-Side (selected):** Allow the drop. Both tasks share the time slot, visually split into columns (like Google Calendar). Neither block is displaced. This signals a conflict without breaking the user's flow.

**Displacement (not selected for now):** Auto-slide the displaced block down to the next free slot. This is a power feature but requires conflict-cascade logic — left for a future iteration.

---

## Q6: Realtime sync — polling or WebSocket?

**Options presented:**
- Polling only
- Wire up existing WebSocket service

**Answer:** Wire up existing WebSocket service.
Use the existing `services/realtime/` service for live multi-tab sync. Calendar mutations should broadcast to connected clients so changes appear instantly across tabs/devices.

---

## Q7: In week view, should the backlog show all week tasks or selected day only?

**Options presented:**
- Entire week, grouped by day
- Selected day only

**Answer:** Accordion Hybrid (Pro Recommendation).
Implement a Grouped Accordion with Auto-Expansion:
- The backlog groups tasks by day (Mon / Tue / Wed / Thu / Fri)
- Each day group is collapsible
- When the user clicks a day column in the calendar, that day's backlog section auto-expands and scrolls into view; other days collapse or dim
- A search bar at the top of the backlog enables cross-week task search
- This gives both the at-a-glance week overview and the focused per-day context

---

## Q8: Should the DaySchedule prop refactor break CommandCenter?

**Options presented:**
- Backwards compatible (old defaults preserved)
- Clean break

**Answer:** Backwards compatible — old defaults preserved.
DaySchedule gets new optional props with defaults that exactly match current behavior:
- `hourHeight` defaults to 50 (current value)
- `startHour` defaults to 0
- `endHour` defaults to 24
CommandCenter passes nothing and continues working as-is. The new portal calendar explicitly passes 60, 6, 22.
