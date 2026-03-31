# Deep Project Interview Transcript

## Requirements File
`command_centre_plan.md` — Architectural Blueprint for Next-Generation Agency Command Centers

## Interview Questions & Answers

### Q1: Department Scope
**Q:** The plan focuses on marketing agents, but your codebase has parallel structures for both marketing AND developer agents. Should we build the Command Centre for both departments or start with marketing only?
**A:** Marketing + shared core — Build shared task/scheduling infrastructure, but only the marketing portal UI. Developer portal added later with minimal effort.

### Q2: Backend Scope
**Q:** The plan requires database restructuring (recurring tasks as task property, category taxonomy overhaul, client tagging). Should we include Django backend changes (models, migrations, APIs) or focus on frontend only?
**A:** Full stack — Django models, migrations, serializers, API endpoints AND Next.js frontend. Frontend without backend is building on sand.

### Q3: Existing Code Strategy
**Q:** Your codebase already has CommandCenter.tsx, DaySchedule.tsx, WeeklyPlanView.tsx, RecurringTaskManager.tsx with drag-and-drop. What should happen to these?
**A:** Refactor & evolve — Keep existing components as base, refactor them into the new architecture. Preserves working DnD logic and patterns.

### Q4: Notification Service
**Q:** For the notification service (services/notification-realtime/) — is it working and ready to use for the admin approval workflow?
**A:** It's operational — can send approval triggers through it.

### Q5: Admin Dashboard Integration
**Q:** Does the admin dashboard already have a structure we should integrate into, or is the admin reporting a new build?
**A:** Integrate into existing — Admin dashboard exists with Overview, Clients, Agents, Performance. Add approval queue and reporting into that structure.

### Q6: Category Taxonomy
**Q:** Should task categories be hardcoded or configurable by admins through a settings UI?
**A:** Admin-configurable — Admins can create/edit/delete categories via a settings page. More flexible, matches the plan's vision.

### Q7: Calendar Week View
**Q:** The plan calls for Day View AND Week View with drag-and-drop on both. How ambitious should the week view be?
**A:** Full week DnD — Both day and week views with full drag-and-drop from backlog. Complete vision.

## Existing Codebase Context

### Current Infrastructure (to refactor, not replace):
- `CommandCenter.tsx` — Main hub with stats and agenda
- `DaySchedule.tsx` — Hourly calendar with @dnd-kit drag-and-drop
- `WeeklyPlanView.tsx` — Weekly planning view
- `RecurringTaskManager.tsx` / `RecurringBlockManager.tsx` — Recurring task templates
- `CrossClientTaskList.tsx` — Cross-client task display
- `TaskCategoryBadge.tsx` — Category visualization
- `sidebar.tsx` — Role-based navigation (marketing/developer/admin/client)
- Full scheduling API (`/lib/api/scheduling.ts`) with hooks (`/lib/hooks/useScheduling.ts`)
- Types in `/lib/types/scheduling.ts` — AgentGlobalTask, AgentTimeBlock, CrossClientTask, etc.
- @dnd-kit library already in use

### Key Decisions:
1. Shared backend infrastructure, marketing-specific portal UI
2. Django backend changes required (models, migrations, APIs)
3. Evolve existing components rather than replace
4. Notification service ready for approval workflow integration
5. Integrate admin reporting into existing admin dashboard
6. Admin-configurable category taxonomy
7. Full drag-and-drop on both day and week calendar views
