
# Project Manifest: Agency Command Centre

## Project Overview

Redesign the agency management platform from a flat-architecture interface into an isolated portal system with contextual navigation, unified task management, interactive time-blocking calendar, and automated admin-agent reporting. Built on the existing Django + Next.js stack, refactoring current components rather than replacing them.

## Key Decisions

- **Scope:** Marketing portal + shared backend core (developer portal extensible later)
- **Stack:** Full stack — Django models/migrations/APIs + Next.js frontend
- **Strategy:** Refactor & evolve existing components (CommandCenter.tsx, DaySchedule.tsx, etc.)
- **Notifications:** Operational notification-realtime service, integrate approval triggers
- **Admin:** Integrate reporting into existing admin dashboard structure
- **Categories:** Admin-configurable task category taxonomy via settings UI
- **Calendar:** Full drag-and-drop on both Day and Week views

## Dependency Graph

```
Split 01 (Backend) ──┬──→ Split 03 (Task UI) ─────────→ Split 06 (Admin/CRM)
                     │                                      ↑
Split 02 (Portal) ───┤                                      │
                     │                                      │
                     └──→ Split 04 (Calendar) → Split 05 (Dashboard) ──┘
```

## Execution Order

| Wave | Splits | Can Parallelize |
|------|--------|-----------------|
| 1 | 01-backend-restructuring + 02-portal-navigation | Yes |
| 2 | 03-unified-task-management + 04-scheduling-engine | Yes |
| 3 | 05-dashboard-kpi | No |
| 4 | 06-admin-reporting-crm | No |

**Critical Path:** 01 → 04 → 05 → 06

<!-- SPLIT_MANIFEST
- id: 01-backend-restructuring
  title: "Backend Task Model & API Restructuring"
  depends_on: []
  description: "Refactor Django models for unified task system: client tagging as metadata, admin-configurable categories, recurring tasks as task property with JIT generation. New API endpoints and migrations."

- id: 02-portal-navigation
  title: "Portal Isolation & Contextual Navigation"
  depends_on: []
  description: "Create isolated management portal route structure, contextual sidebar that swaps on portal entry, breadcrumb navigation, and Return to Dashboard button."

- id: 03-unified-task-management
  title: "Unified Task Management UI"
  depends_on: [01-backend-restructuring, 02-portal-navigation]
  description: "Merge Kanban and List views into single Tasks page with view toggle. Client tag filter bar, task creation modal with category picker and recurrence rule builder, approval workflow columns."

- id: 04-scheduling-engine
  title: "Interactive Scheduling Engine"
  depends_on: [01-backend-restructuring, 02-portal-navigation]
  description: "Split-view calendar with unscheduled backlog pane and hourly grid. Full DnD from backlog to grid, resize handles, All-Day header, Week view with cross-day DnD, bi-directional API sync."

- id: 05-dashboard-kpi
  title: "Main Dashboard Redesign & Current Task KPI"
  depends_on: [04-scheduling-engine]
  description: "Redesign main dashboard as read-only overview with Current Task KPI widget (chronological sync, progress bar, deep-link), progressive interactivity checkboxes, and read-only schedule view."

- id: 06-admin-reporting-crm
  title: "Admin Reporting & Client CRM Hub"
  depends_on: [03-unified-task-management, 04-scheduling-engine, 05-dashboard-kpi]
  description: "Enhanced Clients Page as CRM hub with task aggregation, auto Days Worked tracking. Admin approval queue, approve/reject workflow, category management settings, automated client report export."
-->

## Split Details

### 01-backend-restructuring
**Backend Task Model & API Restructuring**

- Dependencies: None (foundation)
- Risk: Medium
- Plan sections: §4.1, §4.3, §6.1-6.3 from requirements

Key deliverables:
- Refactor `AgentGlobalTask` model: add `client` FK, recurrence fields
- Create `TaskCategory` model (admin CRUD)
- JIT recurring task generation on completion
- Updated serializers and API endpoints
- Database migrations
- Backward-compatible changes

### 02-portal-navigation
**Portal Isolation & Contextual Navigation**

- Dependencies: None (parallel with 01)
- Risk: Low
- Plan sections: §2.1-2.2 from requirements

Key deliverables:
- Route: `dashboard/agent/marketing/management/*`
- `ManagementLayout` with contextual sidebar (Tasks, Calendar, Clients, Notes)
- `BreadcrumbNav` component
- "Return to Main Dashboard" button
- Sidebar portal-mode detection in existing `sidebar.tsx`

### 03-unified-task-management
**Unified Task Management UI**

- Dependencies: 01, 02
- Risk: High
- Plan sections: §4.1-4.3, §6.2, §7.2 from requirements

Key deliverables:
- Unified Tasks page with Kanban ↔ List view toggle
- Horizontal client tag filter bar (color-coded, controlled vocabulary)
- Task creation/edit modal: client selector, category picker, recurrence toggle + rule builder
- Approval workflow columns: To-Do → In Progress → In Review → Done
- "In Review" state triggers notification to admin via notification-realtime service

### 04-scheduling-engine
**Interactive Scheduling Engine**

- Dependencies: 01, 02
- Risk: Highest
- Plan sections: §5.1-5.3 from requirements

Key deliverables:
- Refactor `DaySchedule.tsx` → split-view (backlog pane + hourly grid)
- Drag from backlog → grid: ghosting, snap-to-slot, default 60min duration
- Resize handles on time blocks (expand/contract)
- "All-Day" header for multi-day/time-agnostic tasks
- `WeekView` with full cross-day DnD
- Day/Week toggle
- Bi-directional sync to API
- Multi-day task partial scheduling logic

### 05-dashboard-kpi
**Main Dashboard Redesign & Current Task KPI**

- Dependencies: 04
- Risk: Medium
- Plan sections: §3.1-3.2 from requirements

Key deliverables:
- Read-only main dashboard redesign
- "Current Task" KPI widget: chronological sync, progress bar, time remaining, deep-link to portal task, empty state
- Progressive interactivity: task checkboxes for quick completion
- Read-only daily schedule view (mirrors calendar)
- Analytics summary cards

### 06-admin-reporting-crm
**Admin Reporting & Client CRM Hub**

- Dependencies: 03, 04, 05
- Risk: Medium
- Plan sections: §7.1-7.3 from requirements

Key deliverables:
- Enhanced Clients Page: task aggregation by client tag, marketing plan tab, time tracking
- Auto "Days Worked" calculation from time block data
- Admin approval queue in existing admin dashboard
- Approve/reject workflow with mandatory feedback notes
- Admin category management settings page
- Automated client report export (tasks, time, milestones by client/period)
