# Research Findings: Portal Isolation & Contextual Navigation

_Combined codebase + web research for planning/02-portal-navigation_

---

## 1. Codebase Findings

### 1.1 Existing Sidebar (`client/components/dashboard/sidebar.tsx`)

**Type:** Client Component (`'use client'`)

**Structure:**
- Props: `SidebarProps { isGuestMode?: boolean; onGuestSignIn?: () => void }`
- Fixed layout: `left-0 top-0 h-screen`, responsive collapsed/expanded widths
- Responsive: Collapsed = `w-16` (64px), Expanded = `w-60` (240px)
- Mobile: Full-width drawer with translate transitions and overlay
- Desktop: Always visible with toggle collapse button

**Navigation:**
- Uses `NavGroup` component from `./NavGroup`
- Active state via `usePathname()` hook
- Active styling: `bg-accent-light` (#DBEAFE) + `border-l-2 border-accent` (#2563EB) + `text-accent`
- Role-based nav groups: Admin, Client, Marketing Agent, Developer Agent, Guest
- Collapse state persisted to `localStorage['sidebar-collapsed']`
- Mobile menu state: local `useState`

**Marketing Agent nav structure (relevant section):**
```
Content, Ads Manager, Media & Resources, Strategy, Workflow, Services
```
The "Command Center" link currently routes to `/dashboard/agent/marketing/schedule/` — this needs to be updated to `/dashboard/agent/marketing/management/`.

**Portal detection hook point:** The sidebar is the right place to add portal detection logic since it already uses `usePathname()`.

---

### 1.2 Existing Layout Files

**`client/app/dashboard/layout.tsx` (Client Component)**
- Provides global structure: `flex h-screen bg-surface-subtle overflow-hidden`
- Renders: `<Sidebar>`, topbar, `<ProfileIncompleteBanner>`, main content area, chat widgets
- Sidebar margin: `md:ml-60` (expanded) or `md:ml-16` (collapsed), synced via localStorage polling (100ms interval)
- Includes: SocketProvider, UnreadMessagesProvider, NotificationSocketProvider, CallProvider, ReactQueryProvider
- Guest routes bypass most layout structure via `GUEST_ROUTES` constant
- Full-height messages layout vs scrollable content layout

**`client/app/dashboard/agent/marketing/layout.tsx` (Client Component)**
- Minimal passthrough — adds mobile FAB (`MobileWorkflowSheet`) on specific routes:
  - `/schedule`, `/tasks`, `/notes`, `/calendar`, `/marketing/strategy`, marketing home
- Positioned: `fixed bottom-20 right-4 z-30`, mobile-only (`lg:hidden`)

**`client/app/dashboard/agent/marketing/ads-manager/layout.tsx`**
- **Key reference for portal pattern** — implements a portal within the dashboard:
  - Creates `AdsManagerContextType` context for portal state
  - `AdsManagerErrorBoundary` class-based error boundary
  - Portal-specific header with title, description, client selector widget
  - Conditional children rendering (requires client selection before showing content)
- This is the closest existing example of a sub-portal pattern

---

### 1.3 Existing Breadcrumb Component

**`client/components/dashboard/breadcrumb.tsx` — ALREADY EXISTS**

Current implementation:
- Auto-generates breadcrumbs from `usePathname()`
- Splits path by `/`, filters out 'dashboard'
- Maps segments via `pathLabels` dictionary
- Skips numeric IDs and UUIDs
- Last segment is non-linked (current page)
- `ChevronRight` icons as separators

**Action:** Extend `pathLabels` to include management portal segments ('management', 'tasks', 'calendar', 'clients', 'notes'). Likely reuse as-is with minor additions.

---

### 1.4 Design Tokens (`client/app/globals.css`)

All tokens confirmed — matching spec exactly:

```css
/* Colors */
--color-accent: #2563EB;
--color-accent-light: #DBEAFE;
--color-accent-dark: #1D4ED8;
--color-surface: #FFFFFF;
--color-surface-subtle: #FAFAFA;
--color-surface-muted: #F4F4F5;
--color-border: #E4E4E7;
--color-text: #18181B;
--color-text-secondary: #52525B;
--color-text-muted: #A1A1AA;

/* Layout */
--sidebar-expanded: 240px;
--sidebar-collapsed: 64px;
--topbar-height: 56px;

/* Transitions */
--transition-fast: 150ms;
--transition-default: 200ms;
--transition-slow: 300ms;
```

Existing utility classes:
- `.nav-item-active` — active nav item styling
- `.sidebar-transition` — sidebar width transition
- `cn()` utility (clsx + tailwind-merge) for conditional class merging

---

### 1.5 Testing Setup

**Status: No testing framework configured.**
- No Jest, Vitest, or similar in `package.json`
- No test files found in codebase
- ESLint is present (^9)

---

### 1.6 Existing Component Patterns

**Standard imports:**
```typescript
'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { [IconName] } from 'lucide-react';
import { useAuth } from '@/lib/hooks/useAuth';
import { cn } from '@/lib/utils';
```

**All icons:** `lucide-react`, sized `w-5 h-5`

**Conditional class pattern:** Template literals or `cn()` utility

**localStorage sync pattern:**
```typescript
useEffect(() => {
  const saved = localStorage.getItem('key');
  if (saved) setState(JSON.parse(saved));
}, []);
```

---

### 1.7 Management Portal Directory Status

**Does not exist yet.** Full directory tree to create:
```
client/app/dashboard/agent/marketing/management/
├── layout.tsx       ← portal wrapper
├── page.tsx         ← portal overview
├── tasks/page.tsx
├── calendar/page.tsx
├── clients/page.tsx
│   └── [id]/page.tsx
└── notes/page.tsx
```

---

## 2. Web Research Findings

### 2.1 Nested Layouts & Portal Isolation

**Best practice (Next.js App Router 2025):** Use route groups with per-group `layout.tsx` for full portal isolation. Route group folders use `(name)` syntax — the parentheses are stripped from the URL.

**For partial isolation** (sub-portal that lives within the dashboard URL tree, as this spec requires), a nested `layout.tsx` at the management route level is the correct approach. The management layout replaces the parent sidebar/shell for all routes under it.

**Critical note:** Multiple root layouts (defining `<html>`/`<body>` per group) trigger a **full page reload** on cross-group navigation. Since our portal is nested inside the existing dashboard URL tree (not a route group sibling), this is not a concern here — we stay in the same root layout tree.

**Partial rendering benefit:** When navigating within the portal (e.g., `/management/tasks` → `/management/calendar`), only the page re-renders. The `management/layout.tsx` preserves state.

---

### 2.2 Conditional Sidebar Rendering

**Three patterns evaluated:**

| Scenario | Pattern |
|---|---|
| Completely different sidebar | Route groups — no `usePathname` needed |
| Same sidebar, different active item | `usePathname` in sidebar Client Component |
| Sidebar visibility depends on auth/roles | Middleware header + Server Component |

**Recommendation for this spec:** The management portal sidebar is entirely different (different links, different title, "Return to Dashboard" button). The cleanest approach is:

**Option A (Structural):** Use a `management/layout.tsx` that renders `<ManagementSidebar>` and wraps children directly — the parent `dashboard/layout.tsx` continues to render its global `<Sidebar>` for all non-management routes. This works because the management layout sits in its own subtree.

**However:** The spec says to modify `sidebar.tsx` to detect the portal. This is **Option B**: add `usePathname` detection in `sidebar.tsx` and render `<ManagementSidebar>` instead of the global sidebar when `pathname.includes('/management/')`.

**Decision:** Option A (structural, via layout.tsx) is cleaner and avoids modifying the global sidebar. But the spec explicitly requests both — a new management layout AND a modification to sidebar.tsx. The layout.tsx approach makes the sidebar.tsx modification minimal.

---

### 2.3 Breadcrumb Navigation

**Component type:** Must be a Client Component — `usePathname` is client-only (official Next.js docs confirm this is intentional).

**Best practice pattern:**
```tsx
'use client';
import { usePathname } from 'next/navigation';
import Link from 'next/link';

const LABEL_MAP: Record<string, string> = {
  management: 'Command Centre',
  tasks: 'Tasks',
  calendar: 'Calendar',
  clients: 'Clients',
  notes: 'Notes',
};

export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split('/').filter(Boolean);
  // filter out 'dashboard', build crumbs from remaining segments
}
```

**Existing `breadcrumb.tsx` already implements this pattern** — just needs `LABEL_MAP` extended for management portal segments.

**Dynamic labels (for `clients/[id]`):** Use React Context so the detail page can inject the client name as the trailing breadcrumb label. Pattern: `useBreadcrumbLabel(clientName)` hook that writes to a BreadcrumbContext.

**Hydration:** Generally safe for breadcrumbs. No special handling needed unless rewrites in `next.config.js` alter the visible URL.

---

### 2.4 Layout Transitions

**Three approaches (stability ranking):**

1. **`template.tsx` + Framer Motion entry animation (Stable — Recommended)**
   - `template.tsx` remounts on every navigation (unlike `layout.tsx`)
   - Provides reliable enter animations
   - No exit animation support (component unmounts immediately)
   - Zero internal API risk

2. **FrozenRouter + `AnimatePresence` (Advanced, Fragile)**
   - Uses `LayoutRouterContext` from `next/dist/shared/lib/...` (internal, non-public API)
   - Provides full enter + exit animations
   - Risks breaking on any Next.js minor update
   - Community confirms it still works on Next.js 16.x as of early 2026

3. **`next-view-transitions` library (CSS cross-fades, Stable)**
   - Production-ready polyfill by Shu Ding
   - Uses View Transitions API (Chrome 111+, Safari 18+, Firefox 130+)
   - Replace `next/link` with library's `<Link>` component
   - Browser support is now solid for target audience

**Recommendation for this spec:** Use `template.tsx` with a simple opacity + slight Y-translate entry animation. This matches the spec's request for "smooth transition animation" without risking instability. Keep it to 200ms matching `--transition-default`.

---

## 3. Key Architectural Decisions (Synthesis)

### 3.1 Portal Sidebar Approach

**Recommended:** Create `management/layout.tsx` that renders `ManagementSidebar` directly, suppressing the global sidebar for all management routes.

The global `dashboard/layout.tsx` renders `<Sidebar>` unconditionally today. Two options to suppress it inside the portal:

**Option 1 (Cleaner):** Pass portal detection to the sidebar via props or let the sidebar detect `pathname.includes('/management/')` and render nothing (returning `null`). The management layout then renders its own sidebar.

**Option 2 (Alternative):** Restructure `dashboard/layout.tsx` to not render `<Sidebar>` for management routes, and let the management layout handle its own sidebar. Requires modifying `dashboard/layout.tsx`.

The spec says to modify `sidebar.tsx` to detect portal mode. This aligns with Option 1: sidebar.tsx checks pathname, renders `ManagementSidebar` when in portal.

### 3.2 Breadcrumbs

Reuse existing `breadcrumb.tsx`. Extend its `pathLabels` map to include:
- `management` → "Command Centre"
- `tasks` → "Tasks"
- `calendar` → "Calendar"
- `clients` → "Clients"
- `notes` → "Notes"

For `clients/[id]` routes, add a BreadcrumbContext for dynamic client name injection.

### 3.3 Transitions

Use `management/template.tsx` with Framer Motion (or a simple CSS transition) for portal entry. 200ms opacity + Y-translate fade-in.

### 3.4 Testing

No testing framework exists. For this feature (pure UI/layout), recommend adding Vitest + React Testing Library. Key test targets:
- Portal detection logic (`isInPortal` utility)
- Breadcrumb label generation
- ManagementSidebar renders correct nav items
- "Return to Dashboard" button navigation

Since no testing infrastructure exists, the plan should call out testing setup as a prerequisite or note that it's deferred.

---

## 4. Implementation Readiness

| Component | Status | Notes |
|---|---|---|
| Design tokens | ✅ Ready | All CSS vars confirmed |
| `breadcrumb.tsx` | ✅ Exists | Extend `pathLabels` only |
| `sidebar.tsx` portal detection | ⚠️ Modify | Add `pathname.includes('/management/')` check |
| `management/layout.tsx` | ⚪ Create | Portal wrapper |
| `ManagementSidebar` | ⚪ Create | Contextual sidebar |
| `management/page.tsx` | ⚪ Create | Placeholder overview |
| `management/tasks/page.tsx` | ⚪ Create | Placeholder |
| `management/calendar/page.tsx` | ⚪ Create | Placeholder |
| `management/clients/page.tsx` | ⚪ Create | Placeholder |
| `management/notes/page.tsx` | ⚪ Create | Placeholder |
| `management/template.tsx` | ⚪ Create | Entry animation |
| Test framework | ❌ None | Vitest + RTL setup needed or defer |
| Ads Manager layout | ✅ Reference | Portal pattern exists here |
