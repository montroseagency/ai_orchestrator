<!-- PROJECT_CONFIG
runtime: typescript-npm
test_command: npm test
END_PROJECT_CONFIG -->

<!-- SECTION_MANIFEST
section-01-gateway-link
section-02-portal-detection
section-03-management-sidebar
section-04-breadcrumb-extension
section-05-portal-layout
section-06-portal-pages
section-07-entry-animation
END_MANIFEST -->

# Implementation Sections Index

Portal Isolation & Contextual Navigation — 7 sections, 3 batches

---

## Dependency Graph

| Section | Depends On | Blocks | Parallelizable |
|---------|------------|--------|----------------|
| section-01-gateway-link | — | — | Yes |
| section-02-portal-detection | — | section-05 | Yes |
| section-03-management-sidebar | — | section-05 | Yes |
| section-04-breadcrumb-extension | — | section-06 | Yes |
| section-05-portal-layout | 02, 03 | 06, 07 | No |
| section-06-portal-pages | 04, 05 | — | Yes |
| section-07-entry-animation | 05 | — | Yes |

---

## Execution Order

**Batch 1 (parallel):** sections 01, 02, 03, 04 — no dependencies, all independent
**Batch 2:** section 05 — requires 02 (portal detection) AND 03 (ManagementSidebar)
**Batch 3 (parallel):** sections 06, 07 — run together after 05 completes

---

## Section Summaries

### section-01-gateway-link
Single `href` change in `sidebar.tsx`: update "Command Center" link from `/dashboard/agent/marketing/schedule/` to `/dashboard/agent/marketing/management/`. Standalone, zero-risk, immediately testable. Includes test stub verifying only this href changed.

### section-02-portal-detection
Add `isInPortal` boolean to `dashboard/layout.tsx` using `pathname.startsWith('/dashboard/agent/marketing/management/')`. When true: suppress global `<Sidebar>` and remove sidebar-offset left-margin from the main content wrapper. All non-management routes remain untouched. Includes unit test stubs for all edge-case paths (false-positive guard for `management-reports/`).

### section-03-management-sidebar
New Client Component `client/components/dashboard/ManagementSidebar.tsx`. Renders: "Command Centre" header, "Return to Dashboard" button (uses existing `<Button variant="outline">` if available), five nav items with `usePathname`-driven active state (`startsWith` for sub-routes, exact for Overview), collapse/expand toggle with `localStorage['management-sidebar-collapsed']` persistence, mobile drawer pattern mirroring global sidebar. Full WCAG 2.1 AA: `aria-expanded`, `aria-controls`, `role="dialog"`, focus trap. Uses existing design tokens — no new CSS variables.

### section-04-breadcrumb-extension
Minimal change to `client/components/dashboard/breadcrumb.tsx`: add portal segment entries to the `pathLabels` map (`management → "Command Centre"`, `tasks → "Tasks"`, `calendar → "Calendar"`, `clients → "Clients"`, `notes → "Notes"`). No structural changes to the component. Includes test stubs verifying each mapping and the full breadcrumb trail for representative portal paths.

### section-05-portal-layout
New files: `client/app/dashboard/agent/marketing/management/layout.tsx` (Server Component wrapping `<ManagementSidebar>` + `<Breadcrumb>` + `{children}`; includes React Error Boundary for portal page failures; applies `pt-[var(--topbar-height)]` offset; flex layout mirroring `dashboard/layout.tsx` structure). Depends on sections 02 and 03 being complete. Includes unit test stubs for layout rendering ManagementSidebar, Breadcrumb, children, and error boundary catch.

### section-06-portal-pages
New page files under `management/`: `page.tsx` (polished overview with section cards linking to each sub-route, modelled on ads-manager portal), `tasks/page.tsx`, `calendar/page.tsx`, `clients/page.tsx`, `notes/page.tsx` (clean placeholder stubs with title + back-to-overview link), and `clients/[id]/page.tsx` (displays `params.id` to validate dynamic routing). Depends on section 05 (layout) and section 04 (breadcrumb labels). Includes unit test stubs for each page.

### section-07-entry-animation
New file: `client/app/dashboard/agent/marketing/management/template.tsx` (Client Component). Uses `framer-motion` `motion.div` with `initial={{ opacity: 0, y: 8 }}`, `animate={{ opacity: 1, y: 0 }}`, `transition={{ duration: 0.2, ease: 'easeOut' }}` (confirmed: `framer-motion@11` is in `client/package.json`). Wraps `{children}` — animates page content only, not the persistent sidebar. Depends on section 05 (layout must exist for template to slot in). Includes test stubs: template renders children, wrapper has animation props on mount.
