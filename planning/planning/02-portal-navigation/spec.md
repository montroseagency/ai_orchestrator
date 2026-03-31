# Spec: Portal Isolation & Contextual Navigation

## Summary

Create an isolated management portal accessed via a gateway link from the main dashboard. The portal has its own contextual sidebar showing only workflow-relevant pages (Tasks, Calendar, Clients, Notes), breadcrumb navigation for spatial orientation, and a persistent "Return to Main Dashboard" button. This is the UI shell that contains all Command Centre features.

## Dependencies

None. Can be built in parallel with Split 01.

## Goals

1. **Portal isolation:** Route structure `dashboard/agent/marketing/management/*` acts as a self-contained workspace
2. **Contextual sidebar:** Sidebar dynamically swaps to show only Command Centre pages when inside the portal
3. **Breadcrumb navigation:** Users always know where they are and can jump to any parent level
4. **Clean portal exit:** Persistent "Return to Main Dashboard" button (not an ambiguous back arrow)

## Existing Code to Refactor

### Files to Modify
- `client/components/dashboard/sidebar.tsx` — Add portal-mode detection and contextual nav rendering
- `client/app/dashboard/agent/marketing/layout.tsx` — Wrap management routes in portal layout
- `client/app/dashboard/layout.tsx` — Detect portal vs main dashboard context

### New Files to Create
- `client/app/dashboard/agent/marketing/management/layout.tsx` — Portal layout wrapper
- `client/app/dashboard/agent/marketing/management/page.tsx` — Portal landing/overview
- `client/app/dashboard/agent/marketing/management/tasks/page.tsx` — Unified tasks (placeholder for Split 03)
- `client/app/dashboard/agent/marketing/management/calendar/page.tsx` — Calendar (placeholder for Split 04)
- `client/app/dashboard/agent/marketing/management/clients/page.tsx` — Clients (placeholder for Split 06)
- `client/app/dashboard/agent/marketing/management/notes/page.tsx` — Notes page
- `client/components/dashboard/BreadcrumbNav.tsx` — Breadcrumb component
- `client/components/dashboard/ManagementSidebar.tsx` — Contextual sidebar for portal

## Detailed Requirements

### Route Structure

```
dashboard/agent/marketing/management/           → Portal overview
dashboard/agent/marketing/management/tasks/     → Unified task page
dashboard/agent/marketing/management/calendar/  → Scheduling calendar
dashboard/agent/marketing/management/clients/   → Client CRM hub
dashboard/agent/marketing/management/clients/[id]/ → Client detail
dashboard/agent/marketing/management/notes/     → Notes
```

### Portal Layout (`ManagementLayout`)

The layout wraps all `/management/*` routes and provides:
1. **Contextual sidebar** replacing the global sidebar
2. **Breadcrumb bar** at the top of content area
3. **Same topbar** as main dashboard (user profile, notifications)
4. Smooth transition animation when entering/exiting portal

```tsx
// Pseudostructure
<ManagementLayout>
  <ManagementSidebar />       {/* Contextual sidebar */}
  <main>
    <BreadcrumbNav />          {/* Breadcrumb trail */}
    <div>{children}</div>      {/* Page content */}
  </main>
</ManagementLayout>
```

### Contextual Sidebar

The sidebar inside the portal shows ONLY:
- **Header:** "Command Centre" title with Montrose branding
- **"Return to Dashboard"** button — prominent, always visible at top
- **Nav items:**
  - Overview (portal landing)
  - Tasks (unified task manager)
  - Calendar (scheduling engine)
  - Clients (CRM hub)
  - Notes
- **Active state:** Uses existing `nav-item-active` CSS class (accent-light bg + left border)

Design tokens from globals.css:
- Sidebar width: `var(--sidebar-expanded)` = 240px / `var(--sidebar-collapsed)` = 64px
- Transitions: `var(--transition-default)` = 200ms
- Surface: `var(--color-surface)` / Border: `var(--color-border)`

### Breadcrumb Navigation

Component renders a trail based on the current route:
```
Main Dashboard > Command Centre > Tasks > [Task Name]
```

- Each breadcrumb segment is clickable and navigates to that route
- Current page (last segment) is non-clickable, shown in `text-muted` style
- Uses `>` or `/` as separator
- Positioned at top of content area, below topbar
- Font: `text-sm font-medium` with `text-secondary` color

### Gateway Link on Main Dashboard

The existing sidebar's "Command Center" link under marketing agent nav should route to `/dashboard/agent/marketing/management/` instead of the current `/dashboard/agent/marketing/schedule/`.

Current sidebar.tsx marketing nav structure:
```
Main: Command Center, Overview
```
Change "Command Center" href to point to the new management portal route.

### Portal Detection Logic

The sidebar needs to know if the user is inside the management portal:
```typescript
const isInPortal = pathname.includes('/management/');
```

If inside portal → render `ManagementSidebar`
If outside portal → render standard global sidebar

This can be handled in the parent layout or in `sidebar.tsx` itself.

## Design Specifications

### Colors & Styling (from existing design system)
- Sidebar bg: `var(--color-surface)` (#FFFFFF)
- Border right: `1px solid var(--color-border)` (#E4E4E7)
- Nav item hover: `var(--color-surface-subtle)` (#FAFAFA)
- Active nav: `var(--color-accent-light)` (#DBEAFE) bg + `2px solid var(--color-accent)` (#2563EB) left border
- "Return to Dashboard" button: Outline style, `border-2 border-gray-300 text-gray-700`
- Breadcrumb text: `text-sm text-secondary` (#52525B)
- Transition: `var(--transition-default)` 200ms ease-in-out

### Fonts
- Sidebar nav items: Inter 500 (font-sans, font-medium)
- Breadcrumb: Inter 400 (font-sans)
- Portal header: Poppins 600 (font-display, font-semibold)

## Out of Scope

- Task management UI (Split 03)
- Calendar/scheduling functionality (Split 04)
- Client CRM detail views (Split 06)
- Dashboard KPI widget (Split 05)
- Notes page functionality (future)

## Acceptance Criteria

1. Navigating to `/dashboard/agent/marketing/management/` shows portal with contextual sidebar
2. Global sidebar items are NOT visible inside the portal
3. "Return to Main Dashboard" button navigates back to main dashboard
4. Breadcrumbs show correct trail for every portal page
5. Each breadcrumb segment is clickable and navigates correctly
6. Portal entry/exit transitions smoothly (no layout flash)
7. Existing main dashboard sidebar continues to work unchanged
8. Portal pages render placeholder content (real content added in later splits)
9. Mobile responsive: sidebar collapses or becomes drawer on small screens
10. Uses existing design tokens — no new colors or fonts introduced
