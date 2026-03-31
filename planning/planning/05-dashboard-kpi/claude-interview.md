# Interview Transcript: Dashboard KPI Redesign

## Q1: Where does this KPI dashboard live in the routing, and how does it relate to the existing CommandCenter?

**Answer:** New dashboard home route (e.g. `/agent/dashboard`). CommandCenter stays at its existing route for now. The KPI dashboard is a new top-level landing page for the agent.

---

## Q2: In the KPI widget, what does 'category' refer to?

**Answer:** Use `block_type` label (e.g., "Deep Work", "Creative", "Client Calls") — the `AgentTimeBlock.block_type` mapped through the existing `BLOCK_TYPE_LABELS` constant already available in the codebase.

---

## Q3: What should the 'Open in Portal →' deep-link URL look like?

**Answer:** `/management/calendar/?date={date}&block={id}` — pass both the date (YYYY-MM-DD) and the active block's ID as query parameters so the calendar page can highlight/scroll to the specific block.

---

## Q4: For the Today's Tasks panel, how should global tasks and cross-client tasks be combined?

**Answer:** Merged flat list, sorted by status then time. All tasks in one list: In Progress first, then To-Do, then Done (greyed out). Client badge distinguishes origin between global and cross-client tasks.

---

## Q5: What should happen when a recurring task is checked off?

**Answer:** Just mark done — backend handles JIT generation automatically via the PATCH `/global-tasks/{id}/` endpoint with `status: done`. No separate JIT endpoint call needed from the frontend.

---

## Q6: Should the read-only schedule panel use DaySchedule or a new component?

**Answer:** Build a new lightweight `ReadOnlySchedule` component from scratch — no DnD code, no modal code, just grid + blocks + NowIndicator. This keeps the existing `DaySchedule.tsx` untouched for the portal.
