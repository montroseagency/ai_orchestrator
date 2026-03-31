# TDD Plan: Portal Isolation & Contextual Navigation

_Companion to `claude-plan.md` — defines tests to write BEFORE implementing each section_

---

## Testing Setup Prerequisite

No testing framework exists in the project. Before writing any tests for this split, set up:
- **Vitest** + **React Testing Library** for unit/component tests
- **Playwright** for integration/E2E tests
- Configure test runner in `client/package.json`

If testing setup is deferred to a later sprint, the stubs below serve as a specification for future test authorship.

---

## Section 1: Portal Detection in `dashboard/layout.tsx`

**Test stubs (Vitest + RTL):**

```
// Test: isInPortal is true when pathname is '/dashboard/agent/marketing/management/'
// Test: isInPortal is true when pathname is '/dashboard/agent/marketing/management/tasks/'
// Test: isInPortal is true when pathname is '/dashboard/agent/marketing/management/clients/abc123/'
// Test: isInPortal is false when pathname is '/dashboard/agent/marketing/'
// Test: isInPortal is false when pathname is '/dashboard/agent/marketing/schedule/'
// Test: isInPortal is false when pathname is '/dashboard/agent/marketing/management-reports/' (false-positive guard)
// Test: global <Sidebar> is not rendered when isInPortal is true
// Test: global <Sidebar> is rendered when isInPortal is false
// Test: main content wrapper does NOT have sidebar-offset margin classes when isInPortal is true
// Test: main content wrapper has correct sidebar-offset margin class when isInPortal is false
```

---

## Section 2: `management/layout.tsx` — Portal Layout Wrapper

**Test stubs (Vitest + RTL):**

```
// Test: layout renders ManagementSidebar
// Test: layout renders Breadcrumb component
// Test: layout renders children inside the main content area
// Test: main content area has topbar-height top padding applied
// Test: error boundary catches render error in children and shows fallback UI (not a crash)
```

---

## Section 3: `ManagementSidebar.tsx`

**Test stubs (Vitest + RTL):**

```
// Test: all 5 nav items render (Overview, Tasks, Calendar, Clients, Notes)
// Test: "Return to Dashboard" button renders and links to /dashboard/agent/marketing/
// Test: "Command Centre" header text renders
// Test: Overview nav item has active class when pathname is exactly /management/
// Test: Overview nav item does NOT have active class when pathname is /management/tasks/
// Test: Tasks nav item has active class when pathname is /management/tasks/
// Test: Clients nav item has active class when pathname is /management/clients/
// Test: Clients nav item has active class when pathname is /management/clients/[id]/ (startsWith)
// Test: collapse toggle button has aria-expanded="false" when sidebar is expanded (collapsed: false)
// Test: collapse toggle button has aria-expanded="true" when sidebar is collapsed
// Test: collapse toggle button has aria-controls matching the sidebar element's id
// Test: clicking collapse toggle changes sidebar width class from w-60 to w-16
// Test: clicking collapse toggle again restores sidebar width class to w-60
// Test: collapse state is written to localStorage['management-sidebar-collapsed'] on toggle
// Test: collapse state is hydrated from localStorage['management-sidebar-collapsed'] on mount
// Test: all nav links and toggle button are keyboard-reachable (tab order test)
// Test: mobile drawer opens when hamburger button is clicked (below md breakpoint)
// Test: mobile drawer closes when backdrop is clicked
// Test: mobile drawer has role="dialog" and aria-modal="true"
// Test: focus is trapped inside mobile drawer when open
```

---

## Section 4: Entry Animation — `management/template.tsx`

**Test stubs (Vitest + RTL):**

```
// Test: template renders children
// Test: on mount, the wrapper element has the entry animation class or initial animation props
// (Note: animation timing is not testable in unit tests — verify visually in E2E)
```

---

## Section 5: Breadcrumb Extension

**Test stubs (Vitest + RTL):**

```
// Test: 'management' segment maps to label "Command Centre"
// Test: 'tasks' segment maps to label "Tasks"
// Test: 'calendar' segment maps to label "Calendar"
// Test: 'clients' segment maps to label "Clients"
// Test: 'notes' segment maps to label "Notes"
// Test: breadcrumb for /management/ shows: Main Dashboard > Command Centre (last segment non-linked)
// Test: breadcrumb for /management/tasks/ shows: Main Dashboard > Command Centre > Tasks
// Test: breadcrumb for /management/clients/abc123/ shows: Main Dashboard > Command Centre > Clients > abc123
// Test: "Main Dashboard" segment is clickable (has href)
// Test: "Command Centre" is clickable when not the last segment
// Test: last segment is not clickable (no href / rendered as span)
```

---

## Section 6: Portal Pages

**Test stubs (Vitest + RTL):**

```
// Test: overview page renders "Command Centre" heading
// Test: overview page renders navigation cards for all 5 sub-sections
// Test: each navigation card links to the correct /management/[section]/ route
// Test: tasks placeholder page renders page title
// Test: tasks placeholder page renders link back to /management/
// Test: calendar placeholder page renders page title
// Test: clients placeholder page renders page title
// Test: notes placeholder page renders page title
// Test: clients/[id] page renders the id parameter value
// Test: clients/[id] page renders link back to /management/clients/
```

---

## Section 7: Gateway Link Update

**Test stubs (Vitest + RTL):**

```
// Test: marketing agent "Command Center" nav item href is '/dashboard/agent/marketing/management/'
// Test: no other sidebar nav items were changed by this modification
```

---

## Integration / E2E Tests (Playwright)

```
// E2E: navigate to /dashboard/agent/marketing/ → global sidebar is visible, management sidebar absent
// E2E: click "Command Center" link → URL becomes /management/, management sidebar appears, global sidebar gone
// E2E: navigate to /management/tasks/ → breadcrumb shows "Main Dashboard > Command Centre > Tasks"
// E2E: click "Main Dashboard" breadcrumb → navigates back to /dashboard/
// E2E: click "Return to Main Dashboard" button → navigates to /dashboard/agent/marketing/, global sidebar reappears
// E2E: navigate directly to /management/tasks/ (no prior navigation) → portal renders correctly
// E2E: mobile viewport (375px) → sidebar not visible, hamburger button visible, clicking opens drawer
// E2E: mobile viewport → clicking backdrop closes sidebar drawer
// E2E: keyboard navigation → Tab through all sidebar items reaches all links and toggle button
```

---

## Visual Regression (Playwright snapshots)

```
// Snapshot: portal overview page, sidebar expanded, desktop viewport
// Snapshot: portal overview page, sidebar collapsed, desktop viewport
// Snapshot: /management/tasks/ placeholder page
// Snapshot: mobile viewport with sidebar drawer open
// Snapshot: main dashboard page (regression guard — global sidebar unchanged)
```
