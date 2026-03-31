# Section 02: Portal Detection in `dashboard/layout.tsx`

## Overview

Add portal-detection logic to the root authenticated dashboard layout so that when a user navigates into `/dashboard/agent/marketing/management/*`, the global sidebar is suppressed and its left-margin offset is removed from the main content area.

**File to modify:** `client/app/dashboard/layout.tsx`

**Dependencies:** None. Section 05 (portal layout) depends on this being in place first.

---

## Tests First

See `client/app/dashboard/layout.test.tsx` — 10 tests covering portal and non-portal paths, Sidebar render conditional, and margin class conditional.

---

## Implementation

### How to Detect the Portal

`dashboard/layout.tsx` is a Client Component using `usePathname()`. Add the detection boolean before the return:

```ts
const isInPortal =
  pathname === '/dashboard/agent/marketing/management' ||
  (!!pathname && pathname.startsWith('/dashboard/agent/marketing/management/'));
```

**Note:** The dual check (exact match + startsWith with trailing slash) handles both the root path `/management` (no trailing slash, Next.js default) and sub-routes `/management/*`. Using only `startsWith('/management/')` would miss the root.

### Conditional Sidebar Rendering

```jsx
{!isInPortal && <Sidebar />}
```

### Conditional Sidebar Margin

```jsx
<div
  data-testid="main-content"
  className={cn(
    'flex-1 flex flex-col h-screen transition-all duration-200',
    !isInPortal && (sidebarCollapsed ? 'md:ml-16' : 'md:ml-60')
  )}
>
```

### What NOT to Change

- Topbar, ProfileIncompleteBanner, chat widgets, session/auth checks — all unchanged

---

## Actual Implementation Notes

- Added `data-testid="main-content"` to main wrapper for test queryability
- False-positive guard: `/dashboard/agent/marketing/management-reports` does NOT match ✓
- Code review: Approved without changes

**Test file:** `client/app/dashboard/layout.test.tsx` — 10 tests, all pass
