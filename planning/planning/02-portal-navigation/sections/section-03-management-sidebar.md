# Section 03: `ManagementSidebar.tsx`

## Overview

New Client Component serving as the contextual sidebar for the management portal. Same dimensions and design tokens as the global sidebar, with portal-specific nav items and a "Return to Dashboard" exit button.

**File created:** `client/components/dashboard/ManagementSidebar.tsx`

**Dependencies:** None. Section 05 (portal layout) imports this component.

---

## Tests First

See `client/components/dashboard/ManagementSidebar.test.tsx` — 18 tests covering nav items, active states, collapse toggle, localStorage persistence, and mobile drawer.

---

## Implementation

### Component Structure

`ManagementSidebar` is a `'use client'` component. Uses `usePathname()` via the `useIsActive` hook and `useState`/`useEffect` for collapse state.

### Nav Items

Five items defined in `NAV_ITEMS` const array:
- Overview: `/dashboard/agent/marketing/management` (exact match)
- Tasks: `/dashboard/agent/marketing/management/tasks` (startsWith)
- Calendar: `/dashboard/agent/marketing/management/calendar` (startsWith)
- Clients: `/dashboard/agent/marketing/management/clients` (startsWith)
- Notes: `/dashboard/agent/marketing/management/notes` (startsWith)

Active items get `nav-item-active bg-accent-light text-accent border-l-2 border-accent` classes. `aria-current="page"` set on active link.

### "Return to Dashboard" Button

Uses `<Link href="/dashboard/agent/marketing/">` with `border border-border` styling (existing Button component not used — Link is more semantically correct for navigation).

### Header

"Command Centre" (British spelling) in `font-display font-semibold`.

### Collapse / Expand

- Expanded: `w-60`, Collapsed: `w-16`
- Toggle button: `aria-expanded` (reflects collapsed state) + `aria-controls` pointing to nav element id
- State key: `localStorage['management-sidebar-collapsed']` (independent from global sidebar)
- Hydrated from localStorage on mount via `useEffect`
- `transition-all duration-200`

### Mobile Behaviour

- Desktop sidebar: `hidden md:flex`
- Mobile hamburger: fixed at `top-4 left-4`, `aria-label="Open menu"`
- Mobile drawer: `role="dialog"`, `aria-modal="true"`, full-height overlay
- Backdrop: `data-testid="mobile-backdrop"` for test queryability
- Focus trap: Tab/Shift+Tab cycles through focusable elements in drawer

---

## Actual Implementation Notes

- `NavLink` is an internal sub-component that calls `useIsActive` (which calls `usePathname`)
- Focus trap implemented via `useRef` + `useEffect` on `isMobileOpen`
- Code review: Approved without changes

**Test file:** `client/components/dashboard/ManagementSidebar.test.tsx` — 18 tests, all pass
