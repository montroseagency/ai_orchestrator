# Implementation Plan: Portal Isolation & Contextual Navigation

_Plan for `planning/02-portal-navigation` — 2026-03-28_

---

## What We're Building

A self-contained management portal UI shell (the "Command Centre") accessed via a gateway link from the main marketing agent dashboard. The portal lives at `dashboard/agent/marketing/management/*` and provides:

1. **Portal isolation** — when inside `/management/`, the global sidebar disappears and is replaced by a contextual management sidebar
2. **Contextual sidebar** — shows only Command Centre pages (Overview, Tasks, Calendar, Clients, Notes) plus a prominent "Return to Main Dashboard" button
3. **Breadcrumb navigation** — auto-generated from the current URL, using the existing `breadcrumb.tsx` component extended with portal segment labels
4. **Smooth entry animation** — 200ms fade-in when entering the portal, via a `template.tsx` file
5. **Portal pages** — overview page modelled after the ads-manager portal, plus placeholder pages for Tasks, Calendar, Clients (including `[id]`), and Notes

This is the UI scaffold for Split 02. The placeholder pages will be filled with real functionality in Splits 03, 04, and 06. Nothing built here should need to be torn down — it is structural wiring.

---

## Why This Architecture

### Why `dashboard/layout.tsx` is portal-aware (not `sidebar.tsx`)

The global sidebar is rendered by `dashboard/layout.tsx`, which wraps the entire authenticated dashboard. Making `sidebar.tsx` responsible for detecting the portal would require it to conditionally render a completely different component — blurring the boundary between the global shell and the portal shell.

Instead, `dashboard/layout.tsx` checks whether the current path is inside `/management/` and, if so, simply does not render the global `<Sidebar>`. The portal then owns its own sidebar entirely through `management/layout.tsx`. This is a clean separation: the dashboard layout steps aside; the portal layout takes over.

### Why `management/layout.tsx` owns the portal chrome

Next.js App Router nested layouts compose naturally. By creating a `management/layout.tsx` that renders `ManagementSidebar` and wraps its children, every page under `/management/*` automatically gets portal chrome — no per-page boilerplate. The parent topbar (provided by `dashboard/layout.tsx`) persists because we are not replacing the root layout, only augmenting it at the management route level.

### Why reuse `breadcrumb.tsx`

An existing breadcrumb component already implements the exact pattern required: path splitting, segment filtering, a label map, and non-linked current-page styling. Creating a parallel `BreadcrumbNav.tsx` would duplicate this logic. Instead, extending the label map is a minimal, non-breaking change that adds portal segment support.

### Why entry-only animation via `template.tsx`

Next.js's `template.tsx` remounts on every navigation (unlike `layout.tsx`, which persists). This makes it the correct hook point for enter animations. The FrozenRouter approach for enter+exit animations depends on Next.js internal APIs that could break on any minor update — not worth the risk for a 200ms fade. The spec requirement is "smooth transition, no layout flash," which entry-only satisfies.

### Why independent sidebar collapse state

The global sidebar and the management sidebar serve different contexts. A user might prefer the management sidebar expanded while the global sidebar is collapsed, or vice versa. Sharing `localStorage` state would impose one user's preference across both contexts. Using a separate key (`management-sidebar-collapsed`) means each sidebar remembers its own last state.

---

## File Structure

### New Files

```
client/app/dashboard/agent/marketing/management/
├── layout.tsx           ← ManagementLayout: ManagementSidebar + main content area + breadcrumbs
├── template.tsx         ← Entry animation (Client Component)
├── page.tsx             ← Portal overview (ads-manager pattern)
├── tasks/
│   └── page.tsx         ← Placeholder
├── calendar/
│   └── page.tsx         ← Placeholder
├── clients/
│   ├── page.tsx         ← Placeholder
│   └── [id]/
│       └── page.tsx     ← Placeholder stub for client detail
└── notes/
    └── page.tsx         ← Placeholder

client/components/dashboard/
└── ManagementSidebar.tsx    ← Contextual sidebar (Client Component)
```

### Modified Files

```
client/app/dashboard/layout.tsx
  → Portal detection + conditional global sidebar suppression

client/components/dashboard/sidebar.tsx
  → "Command Center" href update

client/components/dashboard/breadcrumb.tsx
  → pathLabels extension
```

---

## Section 1: Portal Detection in `dashboard/layout.tsx`

`dashboard/layout.tsx` is a Client Component that already uses `usePathname()`. The change is minimal and additive.

A boolean `isInPortal` is derived from the pathname before the render. When true, the global `<Sidebar>` is not rendered. The main content area's responsive left-margin classes should also omit the sidebar-offset margin when in portal mode (the portal layout handles its own sidebar spacing).

The `isInPortal` check uses `pathname.startsWith('/dashboard/agent/marketing/management/')` — explicit and immune to false positives from future routes that might contain "management" elsewhere in their path (e.g., a hypothetical `/management-reports/` route).

The main content wrapper in `dashboard/layout.tsx` applies responsive sidebar-offset classes (typically `md:ml-60` when expanded, `md:ml-16` when collapsed). When `isInPortal` is true, these left-margin classes must be entirely omitted — the management layout provides its own sidebar and handles its own internal spacing. Leaving the margin in place would cause a double-offset layout where the management content is shifted right by the global sidebar's width despite the sidebar not being rendered.

This change must not affect any non-management routes. All existing behaviour (sidebar collapse state, chat widgets, provider nesting, guest route handling) remains untouched for non-portal paths.

---

## Section 2: `management/layout.tsx` — Portal Layout Wrapper

The management layout is the structural wrapper for all portal pages. It is responsible for:

1. Rendering `<ManagementSidebar>` — the contextual sidebar
2. Rendering a main content area containing:
   - The breadcrumb bar (using the existing `<Breadcrumb>` component from `breadcrumb.tsx`)
   - The `{children}` slot for page content
3. Providing the correct structural CSS so the content area sits to the right of the sidebar, matches the topbar height, and scrolls correctly

The layout does not need to be a Client Component unless it consumes client hooks. Prefer Server Component if possible; only convert to Client Component if rendering logic requires `usePathname` or state. (The sidebar and breadcrumb are already Client Components and handle their own hooks internally.)

The flex layout structure mirrors `dashboard/layout.tsx`: `flex h-screen` outer container, sidebar fixed on the left, main area fills remaining width with `overflow-y-auto`.

The management layout's main content area must account for the persisting topbar from `dashboard/layout.tsx`. Apply `pt-[var(--topbar-height)]` (or equivalent `pt-14` for 56px) to the content wrapper so page content sits below the topbar and is not obscured by it.

`management/layout.tsx` should wrap its `{children}` slot in a React Error Boundary so that render-time failures in any portal page are caught gracefully (displaying a portal-specific error state) rather than propagating up and crashing the outer dashboard shell.

---

## Section 3: `ManagementSidebar.tsx`

`ManagementSidebar` is a Client Component. It is visually and functionally analogous to the global `Sidebar` — same dimensions, same design tokens, same mobile drawer pattern — but with portal-specific nav items and an additional "Return to Dashboard" button.

### Nav Items

```
Overview      →  /dashboard/agent/marketing/management/
Tasks         →  /dashboard/agent/marketing/management/tasks/
Calendar      →  /dashboard/agent/marketing/management/calendar/
Clients       →  /dashboard/agent/marketing/management/clients/
Notes         →  /dashboard/agent/marketing/management/notes/
```

Active state uses `usePathname()` with a `startsWith` check for sub-routes (e.g., `clients/` is active for both `clients/` and `clients/[id]/`), and exact match for Overview.

### "Return to Dashboard" Button

Positioned at the top of the sidebar nav area, above the nav items. Uses `useRouter().push('/dashboard/agent/marketing/')` or a `<Link>` component. Before writing ad-hoc Tailwind classes, check whether the codebase has an existing `<Button variant="outline">` component — if so, use it for consistency. If not, apply `border-2 border-gray-300 text-gray-700 hover:bg-surface-subtle` directly. This is intentionally distinct from nav items — it is an exit action, not a navigation target within the portal.

### Header

Above the "Return" button: portal title "Command Centre" in `font-display font-semibold` (Poppins 600). Optionally includes a small Montrose branding mark (use existing brand assets if available, otherwise text only).

### Collapse / Expand

- Expanded: `w-60` (240px)
- Collapsed: `w-16` (64px), icon-only (hide labels, keep icons)
- Toggle button at the bottom of the sidebar
- State persisted to `localStorage['management-sidebar-collapsed']`
- `useEffect` on mount to hydrate from `localStorage`
- Transition: `transition-all duration-200` matching `--transition-default`

### Mobile Behaviour

Below the `md` breakpoint, the sidebar is hidden (`hidden md:flex`). A hamburger/menu toggle button is rendered in the topbar area — positioned at the top-left corner of the topbar on mobile, adjacent to the logo/brand mark, consistent with the global sidebar's toggle placement. Tapping it opens the sidebar as a full-height fixed overlay (`role="dialog"` with `aria-modal="true"`) with a semi-transparent backdrop. Tapping the backdrop or the toggle closes it. This mirrors the global sidebar's mobile drawer implementation.

### Accessibility

`ManagementSidebar` must meet basic WCAG 2.1 AA requirements for this interaction pattern:

- The collapse/expand toggle button must have `aria-expanded` (true/false) and `aria-controls` pointing to the sidebar's `id`
- All nav links and the "Return to Dashboard" button must be keyboard-reachable via Tab and activatable via Enter/Space
- Provide visible `:focus-visible` outlines on all interactive elements
- The mobile drawer must use `role="dialog"` with `aria-modal="true"` and trap focus inside while open — implement focus trapping consistent with the global sidebar's mobile drawer if one exists

---

## Section 4: Entry Animation — `management/template.tsx`

`template.tsx` in Next.js App Router remounts on every navigation within the portal. It wraps `{children}` with an animation that fires on mount.

If `framer-motion` is present in `client/package.json` (verify during implementation): use `motion.div` with `initial={{ opacity: 0, y: 8 }}`, `animate={{ opacity: 1, y: 0 }}`, `transition={{ duration: 0.2, ease: 'easeOut' }}`.

If `framer-motion` is not present: use a CSS keyframe class (`animate-portal-enter`) defined in `globals.css` or as a Tailwind `@keyframes` extension. Same effect: fade in from slight Y offset over 200ms.

The animation runs at the page content level, not the sidebar level (sidebar is in `layout.tsx` and persists across within-portal navigations). Only page content fades in on each route change.

---

## Section 5: Breadcrumb Extension

The existing `breadcrumb.tsx` component splits the pathname, filters segments, and maps them to labels via a `pathLabels` dictionary. The only change is adding portal segment entries to that dictionary:

- `management` → "Command Centre"
- `tasks` → "Tasks"
- `calendar` → "Calendar"
- `clients` → "Clients"
- `notes` → "Notes"

The component already handles the "Main Dashboard" root, non-linked last segment, and separator rendering. No structural changes are needed.

For `clients/[id]`, the dynamic segment will render as the raw ID value in the breadcrumb (since there is no data-fetching for this split). This is acceptable placeholder behaviour. Dynamic label injection is deferred to Split 06. When that split is scoped, it should evaluate three approaches and pick the one consistent with how the rest of the app handles shared page-level metadata:
1. A React Context provider in `management/layout.tsx` that portal pages can write client name into
2. A Zustand store slice (consistent with the existing `client/store/` pattern)
3. A dedicated breadcrumb data service / hook that fetches lazily

---

## Section 6: Portal Pages

### Overview Page (`management/page.tsx`)

Modelled after the ads-manager portal overview. Structure:
- Portal header section: "Command Centre" heading with a brief description of the portal's purpose
- Section cards or a list of available areas, each with an icon, name, brief description, and link to the sub-route
- Clean, polished placeholder — not a "coming soon" stub

The overview page communicates to the user what this workspace is for and provides direct navigation to each section without requiring them to use the sidebar.

### Placeholder Sub-Pages (`tasks/`, `calendar/`, `clients/`, `notes/`)

Each page displays:
- Page title (matching the nav item label)
- A short "coming soon in a future update" or "this section is being built" message
- A link back to the portal overview

These are pure stubs — no data, no state, no API calls. The goal is working navigation (breadcrumbs, active states, back button) without any feature implementation.

### `clients/[id]/page.tsx`

Same stub pattern as other placeholders. The route parameter `id` can be read and displayed (`params.id`) to confirm the dynamic routing works. This ensures the route structure is in place for Split 06 to build on.

---

## Section 7: Gateway Link Update

In `client/components/dashboard/sidebar.tsx`, find the marketing agent nav section where "Command Center" links to `/dashboard/agent/marketing/schedule/`. Update the `href` to `/dashboard/agent/marketing/management/`.

This is a single string change. No other modifications to `sidebar.tsx` are needed as part of this split (the portal detection logic lives in `dashboard/layout.tsx`, not here).

---

## Implementation Order

The sections have natural dependencies. Implement in this order to allow testing at each step:

1. **Section 7 first** — update the gateway link (one-line change, immediately testable in the browser)
2. **Section 1** — portal detection in `dashboard/layout.tsx` (suppresses global sidebar for `/management/*`)
3. **Section 3** — `ManagementSidebar.tsx` (needed by layout)
4. **Section 2** — `management/layout.tsx` (needs ManagementSidebar to exist)
5. **Section 5** — extend `breadcrumb.tsx` labels (needed by layout's breadcrumb rendering)
6. **Section 6** — portal pages (overview first, then placeholders)
7. **Section 4** — `management/template.tsx` (add animation last, after routing is confirmed working)

---

## Edge Cases and Considerations

### Main content margin when in portal

`dashboard/layout.tsx` applies a left margin to the main content area based on the sidebar's collapsed state (`md:ml-60` or `md:ml-16`). When `isInPortal` is true, this margin should be removed or set to zero — the management layout handles its own internal layout. Failing to do this would cause double-offset layout.

### Topbar and profile banner persist in portal

The topbar and profile-incomplete banner are rendered by `dashboard/layout.tsx` regardless of portal state. This is intentional — the spec says the portal uses "the same topbar as the main dashboard." No changes needed for topbar rendering.

### Chat widgets in portal

`dashboard/layout.tsx` renders chat widgets at the bottom of the screen for some roles. These should continue to render in the portal (or not, if the current role check already handles this). Do not add explicit portal-based suppression of chat widgets — let existing role/route logic decide.

### Direct URL navigation

Since `management/layout.tsx` provides the portal chrome automatically for all routes under `/management/*`, direct URL navigation works correctly without any special handling. A user bookmarking `/management/tasks/` will get the full portal layout on load.

### No auth guards needed

The management portal is inside the authenticated dashboard tree. The existing session check in `dashboard/layout.tsx` (or middleware) already protects all `/dashboard/*` routes. No additional guards needed for this split.

### Mobile hamburger trigger placement

The management sidebar's mobile hamburger button needs to be visible when the sidebar is closed. Options: (1) place it in the topbar area for mobile viewports, or (2) render it as a fixed floating button in the management layout. Option 1 is consistent with the global sidebar pattern and preferred.

---

## Testing Strategy

### Unit Tests

- `ManagementSidebar` collapse/expand toggle — assert `isCollapsed` state changes and the correct CSS class is applied
- `ManagementSidebar` active state logic — for each nav item, assert active class is applied when pathname matches, inactive when it doesn't; verify `startsWith` behaviour for `clients/` sub-routes
- `breadcrumb.tsx` label map extension — assert "management" maps to "Command Centre", other portal segments map correctly

### Integration / E2E Tests (Playwright)

- Navigate to `/dashboard/agent/marketing/` → global sidebar is visible, management sidebar is not
- Click the "Command Center" gateway link → lands on `/management/`, global sidebar gone, management sidebar present
- Navigate between all portal pages → breadcrumb updates correctly for each route
- Click "Return to Main Dashboard" → navigates back, global sidebar reappears
- Mobile viewport: sidebar collapses at `md` breakpoint, hamburger button triggers drawer open/close

### Visual Regression

Run visual regression snapshots on:
- Portal overview page (expanded sidebar)
- Portal overview page (collapsed sidebar)
- A placeholder sub-page (e.g., `/management/tasks/`)
- Mobile viewport with sidebar drawer open

---

## Design Token Checklist

All styling must use existing CSS custom properties. No new tokens introduced.

| Token | Value | Usage |
|-------|-------|-------|
| `--sidebar-expanded` | 240px | ManagementSidebar expanded width |
| `--sidebar-collapsed` | 64px | ManagementSidebar collapsed width |
| `--transition-default` | 200ms | Sidebar transition, entry animation |
| `--color-surface` | #FFFFFF | Sidebar background |
| `--color-border` | #E4E4E7 | Sidebar right border |
| `--color-surface-subtle` | #FAFAFA | Nav item hover |
| `--color-accent-light` | #DBEAFE | Active nav item background |
| `--color-accent` | #2563EB | Active nav item left border + text |
| `--color-text-secondary` | #52525B | Breadcrumb text |
| `--topbar-height` | 56px | Offset for content area top |
