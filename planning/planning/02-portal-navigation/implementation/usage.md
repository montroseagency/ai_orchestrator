# Portal Isolation & Contextual Navigation — Usage Guide

## What Was Built

A fully isolated management portal for marketing agents, accessed via **Command Centre** in the sidebar.

---

## How to Navigate

1. Log in as a marketing agent
2. Click **Command Centre** in the left sidebar → navigates to `/dashboard/agent/marketing/management`
3. The global sidebar disappears; the portal's own **ManagementSidebar** takes over
4. Navigate between Tasks, Calendar, Clients, Notes using the portal sidebar
5. Click **Return to Dashboard** to exit the portal

---

## Route Map

| URL | Component | Description |
|-----|-----------|-------------|
| `/dashboard/agent/marketing/management` | `management/page.tsx` | Portal overview with section cards |
| `/dashboard/agent/marketing/management/tasks` | `tasks/page.tsx` | Tasks placeholder |
| `/dashboard/agent/marketing/management/calendar` | `calendar/page.tsx` | Calendar placeholder |
| `/dashboard/agent/marketing/management/clients` | `clients/page.tsx` | Clients placeholder |
| `/dashboard/agent/marketing/management/clients/[id]` | `clients/[id]/page.tsx` | Client detail stub |
| `/dashboard/agent/marketing/management/notes` | `notes/page.tsx` | Notes placeholder |

---

## Key Files

| File | Purpose |
|------|---------|
| `client/components/dashboard/sidebar.tsx` | Gateway link (Command Centre href updated) |
| `client/app/dashboard/layout.tsx` | Portal detection (`isInPortal`), suppresses global sidebar |
| `client/components/dashboard/ManagementSidebar.tsx` | Portal-specific sidebar with 5 nav items |
| `client/components/dashboard/breadcrumb.tsx` | Labels for portal segments |
| `client/app/dashboard/agent/marketing/management/layout.tsx` | Portal layout wrapper |
| `client/app/dashboard/agent/marketing/management/template.tsx` | Per-page entry animation |
| `client/components/common/error-boundary.tsx` | `PortalErrorBoundary` class component |

---

## Test Infrastructure

Vitest + React Testing Library added to `client/`. Run tests:

```bash
cd client
npm test -- --run      # single run
npm test               # watch mode
```

**7 test files, 58 tests total** — all pass.

---

## Commits

| Hash | Section |
|------|---------|
| `c532bf38c` | Section 01: Gateway link |
| `1ce13e749` | Section 02: Portal detection |
| `04c3e7c71` | Section 03: ManagementSidebar |
| `bde6ec5d4` | Section 04: Breadcrumb labels |
| `e5dc80cda` | Fix: code review fixes (sections 02+03) |
| `26ca7160b` | Section 05: Portal layout |
| `717f3e1fa` | Section 06: Portal pages |
| `91a8c003c` | Section 07: Entry animation |
