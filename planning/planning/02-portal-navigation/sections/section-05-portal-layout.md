# Section 05: Portal Layout Wrapper (`management/layout.tsx`)

## Overview

Create the Next.js layout file that wraps all `/management/*` routes. Renders `ManagementSidebar` on the left, breadcrumb at the top of the content area, and `{children}` through to portal pages. Topbar persists from outer `dashboard/layout.tsx`.

**Files created:**
- `client/app/dashboard/agent/marketing/management/layout.tsx`
- `client/components/common/error-boundary.tsx` (was empty, now contains `PortalErrorBoundary`)

**Dependencies:** Sections 02 ✓, 03 ✓, 04 ✓

---

## Tests First

See `client/app/dashboard/agent/marketing/management/layout.test.tsx` — 5 tests.

---

## Actual Implementation

### layout.tsx

Server Component (no `'use client'`). Structure:

```
<div class="flex h-screen">
  <ManagementSidebar />
  <main class="flex-1 overflow-y-auto pt-14">
    <div class="px-6 pt-4 pb-2"><Breadcrumb /></div>
    <PortalErrorBoundary>{children}</PortalErrorBoundary>
  </main>
</div>
```

- `pt-14` = 56px, matching `--topbar-height: 56px` CSS variable
- Breadcrumb wrapped in padding div for consistent spacing

### PortalErrorBoundary

Class component in `client/components/common/error-boundary.tsx`. Fallback shows:
- "Something went wrong in Command Centre."
- Link back to `/dashboard/agent/marketing/`

Code review: Approved without changes.

**Test file:** `client/app/dashboard/agent/marketing/management/layout.test.tsx` — 5 tests, all pass
