# Interview Transcript: Unified Task Management UI

---

## Q1: Recurring task JIT next-instance creation

**Question:** When a recurring task is moved to 'Done', the spec says it triggers JIT next-instance creation. Is this handled server-side (the PATCH to 'done' status automatically creates the next instance in Django), or does the frontend need to call a separate endpoint after the status update?

**Answer:** Server-side (backend handles it). The PATCH to 'done' automatically creates the next instance — frontend just invalidates the query.

---

## Q2: Notification timing for 'In Review' trigger

**Question:** When an agent drags a card to the In Review column, should the notification be sent optimistically (immediately on drop, before API confirms) or only after the PATCH succeeds?

**Answer:** After API success (safer). Wait for PATCH /global-tasks/{id}/ to succeed before triggering notification — avoids false alerts.

---

## Q3: Client badge color assignment

**Question:** Client badges need a color. The AgentGlobalTask has client_name but no client color field. How should client badge colors be assigned?

**Answer:** Auto-assign from a fixed palette. Frontend assigns colors deterministically (e.g., hash client ID to a palette of 8–12 colors).

---

## Q4: Clients API hook availability

**Question:** Does a useClients() hook (or equivalent) already exist for fetching the agent's assigned clients list for the filter bar and modal selector?

**Answer:** Not sure — research it and figure it out during implementation.

---

## Q5: Intra-column card reordering

**Question:** Should cards within a Kanban column be reorderable (drag to change position within the same column), or only movable between columns?

**Answer:** Both — within and between columns. Cards can be reordered within a column and moved between columns.

---

## Q6: Task description field

**Question:** The spec mentions 'rich text' for the task description field. Is there an existing rich text editor in the codebase, or should this be a plain textarea for now?

**Answer:** Use the existing rich text editor. Find it in the codebase during implementation.

---

## Q7: Filter persistence

**Question:** Should active filters persist in the URL (so the page is shareable/bookmarkable), or is React local state sufficient?

**Answer:** URL query params — filters reflected in the URL, shareable and survives browser refresh.

---

## Q8: Bulk actions

**Question:** The existing developer tasks page has bulk multi-select actions (bulk status update). Should the unified tasks page also support bulk operations?

**Answer:** Yes, include bulk actions — checkbox column in list view, bulk status/delete operations.
