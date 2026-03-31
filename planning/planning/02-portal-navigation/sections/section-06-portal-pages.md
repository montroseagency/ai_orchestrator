# Section 06: Portal Pages

## Overview

Create all page files under the management portal route. The overview page links to all sections; the sub-pages are clean placeholder stubs.

**Files created:**
- `client/app/dashboard/agent/marketing/management/page.tsx`
- `client/app/dashboard/agent/marketing/management/tasks/page.tsx`
- `client/app/dashboard/agent/marketing/management/calendar/page.tsx`
- `client/app/dashboard/agent/marketing/management/clients/page.tsx`
- `client/app/dashboard/agent/marketing/management/clients/[id]/page.tsx`
- `client/app/dashboard/agent/marketing/management/notes/page.tsx`

**Dependencies:** Sections 04 ✓, 05 ✓

---

## Actual Implementation

### Overview page

Server Component. Structure: h1 "Command Centre" + description + 4 section cards (Tasks, Calendar, Clients, Notes). Each card uses a lucide icon, label, description text, and `<Link>` to the sub-route. Uses `bg-surface border border-border rounded-lg` card styling.

### Placeholder sub-pages (Tasks, Calendar, Clients, Notes)

Server Components. Each: `<h1>` with section name, placeholder message, back link to `/management/`.

### clients/[id]/page.tsx

Renders `params.id` as "Client ID: {id}" to confirm dynamic routing. Back link to `/management/clients/`.

Code review: Approved without changes.

**Test file:** `client/app/dashboard/agent/marketing/management/pages.test.tsx` — 10 tests, all pass
