# Section 09 Code Review Interview

## Auto-Fixes Applied

### MAJOR M-2: Concurrent submit race condition
- Added `submittingRef = useRef(false)` as a synchronous guard in both `handleApprove` and `handleReject`
- Guards checked before any async work begins; ref reset in `finally`

### MAJOR M-3: columns array and openDrawer recreated on every render
- `openDrawer`, `closeDrawer`, `removeTask`, `handleApprove`, `handleReject` all wrapped in `useCallback`
- `columns` array wrapped in `useMemo([openDrawer])`

### MAJOR M-4: null/malformed timestamp guard
- Added ternary guard `row.updated_at ? formatDistanceToNow(...) : '—'` in both table column and drawer header

## Not Actioned

### CRITICAL C-1: Sidebar fetches full task objects for count
- Decision: No `/admin/approvals/count/` endpoint was defined in section-05 backend spec
- Current approach (fetch tasks list, use `.length`) is acceptable given the admin-only context
- The socket `on`/`off` concern is moot — verified `useCallback` wraps both in socket-context.tsx

### CRITICAL C-2: Server-side role guard
- Django permission_classes handled in section-05; Next.js middleware handles admin route guarding globally — out of scope for this section
