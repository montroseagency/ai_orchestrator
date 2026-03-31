# Opus Review

**Model:** claude-opus-4
**Generated:** 2026-03-27T00:00:00Z

---

## Plan Review: Split 01 -- Backend Task Model & API Restructuring

### Critical Issues

**1. The `recurring_source` FK on AgentGlobalTask is not addressed.**

The existing `AgentGlobalTask` model at line 139 of `/home/ubuntu/Montrroase_website/server/api/models/agent_scheduling.py` has a `recurring_source` FK pointing to `RecurringTaskTemplate`. The plan adds `recurrence_parent` (a self-FK) but never mentions what happens to the existing `recurring_source` field. Migration D removes the `RecurringTaskTemplate` model, but if the `recurring_source` FK is not dropped first (or simultaneously), the migration will fail because the FK target table is being deleted. This field must be explicitly listed in the cleanup migration alongside the old `task_category` CharField.

**2. Department value mismatch will break category filtering.**

The plan's Risk Area #5 flags this but does not resolve it. The `TaskCategory.department` field uses choices `marketing/developer/both`, but the actual `Agent.department` field at line 47 of `/home/ubuntu/Montrroase_website/server/api/models/users.py` stores `'marketing'` or `'website'` (not `'developer'`). The plan's Section 7 says to filter by `request.user.agent_profile.department`, but a `website` agent would never match `developer` categories. The plan needs an explicit mapping (e.g., `website` -> `developer`) in the queryset filter or the department choices on `TaskCategory` need to use `marketing/website/both` to match reality.

**3. The `command_center` and `cross_client_tasks` views are not updated.**

These are standalone function-based views (lines 283-458 of `/home/ubuntu/Montrroase_website/server/api/views/agent/scheduling_views.py`) that directly reference `task_category` (the old CharField), use `AgentGlobalTaskSerializer` (which will be split into read/write), and access `ScheduledTaskLink.task` via the GenericFK pattern (`link.task` at line 323). The plan does not mention updating these views at all. After the changes ship, `command_center` will break because:
- It uses the old `AgentGlobalTaskSerializer` name
- `_serialize_global_task` reads `task.task_category` (the old CharField, which gets removed in Migration D)
- The `ScheduledTaskLink` loop uses `link.task` which was a GenericFK accessor and will no longer exist after the GFK fields are removed

**4. The `ScheduledTaskLink` unique constraint is not updated.**

The current model has `unique_together = ['content_type', 'object_id', 'agent']` (line 194). When the GenericFK fields are removed, this constraint becomes invalid. The plan's Section 3 does not mention creating a replacement constraint (e.g., `unique_together = ['task', 'agent']` or whatever the new uniqueness rule should be).

### Significant Issues

**5. `ScheduledTaskLink.task` field name collision.**

The existing model already has `task = GenericForeignKey('content_type', 'object_id')` at line 182. The plan wants to add a new `task` FK field. While GenericForeignKey is not a real database column, Django will complain about the attribute name collision if both exist on the model simultaneously. The new FK should use a different name during the transition period (e.g., `linked_task`) or the plan needs to explicitly state that the GFK attribute will be removed in the same schema migration that adds the FK, which contradicts the stated multi-step approach.

**6. Existing index `(agent, task_category)` on the old CharField is not cleaned up.**

Line 155 of the model shows an index on the old `task_category` CharField. When that field is dropped in Migration D, the index should be explicitly dropped too. Django may handle this automatically when the field is removed, but it should be called out to avoid migration ordering surprises.

**7. The `IsAdmin` permission check may be wrong.**

Section 6 says `IsAdmin` checks `request.user.role == 'admin'`. Looking at the existing `IsAnyAgent` (line 35 of scheduling_views.py), it checks `request.user.role != 'agent'`. The User model at line 11 of users.py shows `ROLE_CHOICES = [('admin', 'Admin'), ('client', 'Client'), ('agent', 'Agent')]`. This looks correct, but the plan should note that admin users will NOT have an `agent_profile`, so any view that calls `_get_agent(request)` will crash if an admin user hits agent-facing endpoints. The `/complete/` action needs to handle the case where an admin (not an agent) is approving a reviewed task.

**8. JIT generation has a race condition risk.**

Section 5 describes the JIT function firing when a task reaches `done`. If two requests hit `/complete/` simultaneously (e.g., double-click), two next instances could be created. The plan should mention using `select_for_update()` or a unique constraint on `(recurrence_parent, recurrence_instance_number)` to prevent duplicate instance creation.

### Minor Issues and Missing Considerations

**9. `MarketingTask` and `ProjectTask` are not being migrated or deprecated.**

The plan says `AgentGlobalTask` is the "unified" model, and Migration B only converts `RecurringTaskTemplate` records where `target_type='global'`. But `RecurringTaskTemplate` also generates `MarketingTask` and `ProjectTask` records (lines 65-124 of scheduling_tasks.py). Those templates with `target_type='marketing_task'` or `'project_task'` are silently dropped. The plan should explicitly acknowledge this data loss and confirm it is acceptable.

**10. The `apply_to_all_clients` and `day_of_month` fields from RecurringTaskTemplate have no equivalent.**

The new recurrence fields on `AgentGlobalTask` do not include `apply_to_all_clients` or `day_of_month`. The plan's `recurrence_frequency: monthly` does not specify which day of the month to recur on. The `dateutil.rrule` approach in Section 5 uses `dtstart=task.scheduled_date` which implicitly uses the day-of-month from the scheduled date, but this is not documented and could confuse implementers.

**11. Frontend has 24 files importing from scheduling types/API.**

The plan's Sections 9-10 only cover `client/lib/types/scheduling.ts` and `client/lib/api/scheduling.ts`. There are 24 files that import from these modules (including `RecurringTaskManager.tsx`, `TaskCategoryBadge.tsx`, `CrossClientTaskList.tsx`, and multiple page components). These will all break at compile time when types like `TaskCategory` (string union) and `RecurringTaskTemplate` are removed. The plan should at minimum list the downstream components that need updating, or confirm that those are handled in a later split.

**12. The `TASK_CATEGORY_LABELS` and `TASK_CATEGORY_COLORS` frontend constants will break.**

These are `Record<TaskCategory, string>` typed objects at lines 357-387 of scheduling.ts. When `TaskCategory` changes from a string union to a `TaskCategoryItem` interface, all these constants and the `TaskCategoryBadge.tsx` component need rewriting. This is a substantial amount of frontend work not scoped in Sections 9-10.

**13. Celery Beat schedule location.**

Section 8 says to check `server/config/celery.py` for the Beat schedule. The actual location is `/home/ubuntu/Montrroase_website/server/server/settings.py` at line 326. The `generate-recurring-tasks` entry is at line 383. The plan should reference the correct file.

**14. Two `CELERY_BEAT_SCHEDULE` definitions exist.**

There is one at `/home/ubuntu/Montrroase_website/server/settings.py` (line 5) and another at `/home/ubuntu/Montrroase_website/server/server/settings.py` (line 326). Depending on which `settings.py` is the active one, the cleanup might miss the other.

**15. The `_serialize_global_task` helper function returns `'client_name': ''` and `'client_id': None`.**

After this restructuring, global tasks CAN have a client. This helper (line 111 of scheduling_views.py) hardcodes empty client data. It needs updating to reflect the new `client` FK on `AgentGlobalTask`.

**16. No mention of the `order` field or drag-and-drop behavior with `in_review` status.**

If the frontend uses the `order` field for kanban-style drag-and-drop, adding `in_review` as a new column/status means the UI needs to know about it. This is potentially a later-split concern but the plan does not clarify.

### Summary

The most dangerous issues are #1 (migration will fail due to FK to a deleted model), #3 (two major views will break silently), and #2 (department filtering will never match). These should be resolved before implementation begins.
