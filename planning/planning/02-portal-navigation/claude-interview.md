# Interview Transcript: Portal Isolation & Contextual Navigation

_Step 8 interview — 2026-03-28_

---

## Q1: How should the global sidebar be suppressed inside the management portal?

**Question:** The global dashboard layout renders `<Sidebar>` unconditionally. Two approaches: (A) `sidebar.tsx` returns null when inside `/management/`, rendering `ManagementSidebar` instead. (B) Modify `dashboard/layout.tsx` to skip rendering `<Sidebar>` for management routes, with `management/layout.tsx` handling its own sidebar entirely.

**Answer:** B — `dashboard/layout.tsx` is portal-aware. Modify `dashboard/layout.tsx` to conditionally skip the global sidebar for `/management/` routes; the management layout handles its own sidebar completely independently.

---

## Q2: Reuse existing `breadcrumb.tsx` or create new `BreadcrumbNav.tsx`?

**Question:** Research found an existing `breadcrumb.tsx` component that auto-generates breadcrumbs from `usePathname()`. Should the portal reuse and extend it, or create a new dedicated `BreadcrumbNav.tsx` as specified in the spec?

**Answer:** Reuse existing `breadcrumb.tsx`. Extend its `pathLabels` map with management portal segments — less duplication, consistent style across the app.

---

## Q3: Portal entry/exit animation approach?

**Question:** Research shows two options: `template.tsx` + Framer Motion for entry-only animations (stable), or the FrozenRouter pattern for full enter + exit (uses Next.js internal APIs, fragile).

**Answer:** Entry-only animation (stable). Use `template.tsx` + 200ms fade-in on portal entry. No risk of breaking on Next.js updates.

---

## Q4: Should `ManagementSidebar` collapse state be shared with or independent from the global sidebar?

**Question:** Should it use the same `localStorage` key as the global sidebar (shared state) or track its own independent collapse state?

**Answer:** Independent collapse state. `ManagementSidebar` tracks its own expand/collapse separately from the global sidebar.

---

## Q5: What should the portal overview page (`management/page.tsx`) show?

**Question:** Options: (A) Simple title + nav cards grid, (B) Pure placeholder text, (C) Match the ads-manager portal pattern.

**Answer:** Match ads-manager portal pattern. Follow the existing ads-manager overview style as a reference baseline.

---

## Q6: Should `clients/[id]` dynamic route be created now or deferred to Split 06?

**Question:** The spec lists `clients/[id]` as a route. Create a placeholder now or omit until Split 06?

**Answer:** Create `[id]` placeholder now. Creates the route stub so navigation works end-to-end.

---

## Q7: Are there other portal entry points beyond the sidebar link?

**Question:** Is the "Command Center" sidebar link the only entry point, or should direct URL access (bookmarks, deep links) also be handled?

**Answer:** Sidebar link + URL direct access. Ensure direct URL navigation to `/management/*` works correctly — layout guards should handle this, not just link updates.

---

## Q8: Mobile sidebar pattern for `ManagementSidebar`?

**Question:** Should `ManagementSidebar` use the same mobile pattern as the global sidebar (hamburger + full-height overlay drawer), or a simpler sheet/bottom-nav approach?

**Answer:** Same pattern as global sidebar — hamburger button + full-height overlay drawer for consistent UX across the app.
