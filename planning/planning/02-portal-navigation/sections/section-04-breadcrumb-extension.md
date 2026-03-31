# Section 04: Breadcrumb Extension

## Overview

Minimal change to `client/components/dashboard/breadcrumb.tsx`: add portal segment entries to the `pathLabels` map.

**File to modify:** `client/components/dashboard/breadcrumb.tsx`

**Dependencies:** None. Section 05 (portal layout) uses `<Breadcrumb>` with these labels.

---

## Tests First

See `client/components/dashboard/breadcrumb.test.tsx` — 10 tests covering individual segment label mappings and full breadcrumb trail behavior.

---

## Implementation

### What to Add

Three entries were missing and added to `pathLabels`:

```ts
management: 'Command Centre',
tasks: 'Tasks',
notes: 'Notes',
```

`calendar` and `clients` already existed in the map with correct values — no changes needed for those.

### No Structural Changes

Component logic unchanged. Label map addition is the only change.

### Dynamic Segment Behaviour (`clients/[id]`)

For `/management/clients/abc123`, the breadcrumb fallback logic capitalises the first char: `abc123 → Abc123`. This is the existing behavior for unmapped segments.

---

## Actual Implementation Notes

- "Command Centre" uses British spelling per portal branding spec ✓
- Code review: Approved without changes

**Test file:** `client/components/dashboard/breadcrumb.test.tsx` — 10 tests, all pass
