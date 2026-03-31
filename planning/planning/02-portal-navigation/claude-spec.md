# Complete Specification: Portal Isolation & Contextual Navigation

_Synthesized from initial spec + research + interview — 2026-03-28_

---

## Overview

Build an isolated management portal at `dashboard/agent/marketing/management/*` with a self-contained contextual sidebar, breadcrumb navigation, and smooth portal entry animation. This is the UI shell (Command Centre) that will later contain unified task management, calendar, and CRM features.

---

## Architecture Decisions

### Sidebar Suppression Strategy

**Approach B chosen:** `dashboard/layout.tsx` is portal-aware.

- Modify `client/app/dashboard/layout.tsx` to detect `pathname.includes('/management/')` and conditionally skip rendering the global `<Sidebar>` component for those routes.
- `management/layout.tsx` renders its own `ManagementSidebar` completely independently — no reference to the global sidebar.
- This cleanly separates concerns: the management layout tree owns its entire chrome.

### Breadcrumbs

Reuse the existing `client/components/dashboard/breadcrumb.tsx` component. Extend its `pathLabels` dictionary to include management portal segments:
- `management` → "Command Centre"
- `tasks` → "Tasks"
- `calendar` → "Calendar"
- `clients` → "Clients"
- `notes` → "Notes"

No new breadcrumb component needed.

### Transitions

Use `management/template.tsx` with a simple entry-only animation (200ms opacity + Y-translate fade-in), matching `--transition-default`. Framer Motion if already in the project, otherwise plain CSS animation. No exit animation — stable over fragile internal-API approaches.

### Sidebar Collapse State

`ManagementSidebar` maintains its own independent collapse state in `localStorage['management-sidebar-collapsed']` — separate from `localStorage['sidebar-collapsed']` used by the global sidebar.

### Portal Entry Points

Two entry points:
1. **Sidebar link:** Update the "Command Center" href in `sidebar.tsx` marketing nav from `/dashboard/agent/marketing/schedule/` to `/dashboard/agent/marketing/management/`.
2. **Direct URL access:** The layout structure itself ensures direct navigation to any `/management/*` URL renders the portal correctly. No additional auth guards needed for this split (portal is within the authenticated dashboard tree).

### Mobile Sidebar

`ManagementSidebar` uses the same mobile pattern as the global sidebar: hamburger toggle button + full-height overlay drawer with `translateX` transitions. Consistent UX across the app.

### Overview Page

`management/page.tsx` follows the ads-manager portal overview pattern: portal header with title/description, and a structured overview of available sections. Mirrors the level of polish in `ads-manager/`.

---

## Route Structure

```
/dashboard/agent/marketing/management/           → Portal overview (page.tsx)
/dashboard/agent/marketing/management/tasks/     → Unified task manager (placeholder)
/dashboard/agent/marketing/management/calendar/  → Scheduling calendar (placeholder)
/dashboard/agent/marketing/management/clients/   → Client CRM hub (placeholder)
/dashboard/agent/marketing/management/clients/[id]/ → Client detail (placeholder stub)
/dashboard/agent/marketing/management/notes/     → Notes (placeholder)
```

---

## Files to Create

```
client/app/dashboard/agent/marketing/management/
├── layout.tsx           ← ManagementLayout: renders ManagementSidebar + BreadcrumbNav + children
├── template.tsx         ← Entry animation wrapper (200ms fade-in)
├── page.tsx             ← Portal overview (ads-manager pattern)
├── tasks/
│   └── page.tsx         ← Placeholder
├── calendar/
│   └── page.tsx         ← Placeholder
├── clients/
│   ├── page.tsx         ← Placeholder
│   └── [id]/
│       └── page.tsx     ← Placeholder
└── notes/
    └── page.tsx         ← Placeholder

client/components/dashboard/
└── ManagementSidebar.tsx    ← Contextual sidebar for portal
```

---

## Files to Modify

```
client/app/dashboard/layout.tsx
  → Add isInPortal detection (pathname.includes('/management/'))
  → Conditionally skip rendering <Sidebar> when in portal

client/components/dashboard/sidebar.tsx
  → Update "Command Center" href to /dashboard/agent/marketing/management/

client/components/dashboard/breadcrumb.tsx
  → Extend pathLabels with management portal segment labels
```

---

## ManagementLayout Specification

```tsx
// management/layout.tsx
// Renders:
//   <ManagementSidebar />    — contextual sidebar
//   <main>
//     <BreadcrumbNav />      — reuses existing breadcrumb.tsx
//     {children}             — page content
//   </main>
// Notes:
//   - Same topbar as main dashboard (provided by parent layout)
//   - ManagementSidebar is a Client Component
//   - Layout itself can be a Server Component
```

---

## ManagementSidebar Specification

### Visual Structure
- **Header:** "Command Centre" title (Poppins 600 / `font-display font-semibold`)
- **"Return to Dashboard" button:** Always visible at top, outline style (`border-2 border-gray-300 text-gray-700`), navigates to `/dashboard/agent/marketing/`
- **Nav items:**
  - Overview → `/management/`
  - Tasks → `/management/tasks/`
  - Calendar → `/management/calendar/`
  - Clients → `/management/clients/`
  - Notes → `/management/notes/`
- **Active state:** `bg-accent-light border-l-2 border-accent text-accent` (same as global sidebar)
- **Footer:** Collapse toggle button

### Dimensions & Tokens
- Expanded: `w-60` (240px = `--sidebar-expanded`)
- Collapsed: `w-16` (64px = `--sidebar-collapsed`)
- Background: `var(--color-surface)` #FFFFFF
- Border right: `1px solid var(--color-border)` #E4E4E7
- Nav item hover: `var(--color-surface-subtle)` #FAFAFA
- Transition: `var(--transition-default)` 200ms ease-in-out

### State
- `isCollapsed`: stored in `localStorage['management-sidebar-collapsed']`
- `isMobileOpen`: local useState for mobile drawer

### Mobile Behaviour
- Desktop: always visible, toggleable between 64px / 240px
- Mobile (`md:hidden` breakpoint): hidden by default, toggled via hamburger button in topbar area
- Mobile open: full-height drawer, fixed position, z-index overlay with backdrop

### Active State Logic
```typescript
const isActive = (href: string) =>
  href === '/management/' ? pathname === href : pathname.startsWith(href);
```

---

## `dashboard/layout.tsx` Changes

```typescript
// Add at top of client component body:
const isInPortal = pathname.includes('/management/');

// Modify sidebar rendering:
{!isInPortal && <Sidebar ... />}

// Modify main content margin:
// Current: className based on collapsed state
// New: when isInPortal, margin is driven by ManagementSidebar (handled in management/layout.tsx)
//      when !isInPortal, margin driven by global sidebar collapse state (unchanged)
```

---

## Template (Entry Animation)

```tsx
// management/template.tsx
// Client Component
// Wraps children with:
//   initial: { opacity: 0, y: 8 }
//   animate: { opacity: 1, y: 0 }
//   duration: 200ms ease-out
// OR: CSS class 'animate-portal-enter' if Framer Motion not in project
```

Confirm whether `framer-motion` is in `client/package.json` during implementation. If not, use a CSS keyframe approach.

---

## Breadcrumb Integration

Extend `pathLabels` in `breadcrumb.tsx`:
```typescript
management: 'Command Centre',
tasks: 'Tasks',
calendar: 'Calendar',
clients: 'Clients',
notes: 'Notes',
```

The breadcrumb component already handles path splitting, segment filtering, and non-linked last segment — no structural changes needed.

For the `clients/[id]` route, the breadcrumb will show the segment as the raw `[id]` value initially. A future enhancement (BreadcrumbContext with dynamic label injection) is out of scope for this split.

---

## Portal Overview Page

`management/page.tsx` follows the ads-manager portal overview pattern:
- Portal header: title "Command Centre" + subtitle description
- Section cards or list of available areas (Tasks, Calendar, Clients, Notes) with icons and brief descriptions
- Each card links to the respective portal sub-route
- Placeholder content, no real data — visual shell only

---

## Placeholder Pages

All sub-pages (`tasks/`, `calendar/`, `clients/`, `clients/[id]/`, `notes/`) render a minimal placeholder:
- Page title
- "Coming soon" or "This feature is in development" message
- Link back to portal overview

These will be replaced in subsequent splits (03, 04, 06).

---

## Acceptance Criteria (from spec + interview)

1. Navigating to `/dashboard/agent/marketing/management/` shows portal with contextual ManagementSidebar — global sidebar is NOT visible
2. Direct URL navigation to any `/management/*` route correctly renders portal layout
3. "Return to Main Dashboard" button navigates to `/dashboard/agent/marketing/`
4. Breadcrumbs show correct trail for every portal page (e.g., "Main Dashboard > Command Centre > Tasks")
5. Each breadcrumb segment is clickable and navigates correctly; current page is non-clickable
6. Portal entry animates in (200ms fade-in) — no layout flash
7. Exiting portal (Return to Dashboard) shows main dashboard with global sidebar correctly restored
8. `ManagementSidebar` collapses/expands independently from global sidebar
9. Mobile: ManagementSidebar collapses to hamburger + overlay drawer (matches global sidebar pattern)
10. Existing main dashboard sidebar continues to work unchanged for all non-management routes
11. "Command Center" sidebar link now routes to `/dashboard/agent/marketing/management/`
12. Portal pages render placeholder content (real content added in later splits)
13. Uses existing design tokens — no new colors or fonts introduced

---

## Out of Scope (this split)

- Task management UI (Split 03)
- Calendar/scheduling functionality (Split 04)
- Client CRM detail views (Split 06)
- Dashboard KPI widget (Split 05)
- Notes page functionality (future)
- BreadcrumbContext dynamic label injection for `clients/[id]`
- Testing framework setup (no test infrastructure currently exists)
