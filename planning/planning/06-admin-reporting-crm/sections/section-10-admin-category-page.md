# Section 10: Admin Category Management Page

## Overview

This section implements a new Next.js admin page that lets admins manage `TaskCategory` records — the categories agents select when creating tasks. The page provides full CRUD (create, read, update, soft-delete) with drag-and-drop row reordering.

**Depends on:** `section-06-category-management-api` — the Django viewset providing the REST endpoints this page calls must exist before the frontend can be wired up.

**Blocks:** `section-13-tests` (final test consolidation).

---

## Files Created / Modified

| Action | Path |
|--------|------|
| Create | `client/app/dashboard/admin/settings/categories/page.tsx` |
| Create | `client/app/dashboard/admin/settings/categories/__tests__/CategoryManagement.test.tsx` |
| Create | `client/components/common/confirmation-modal.tsx` (was empty stub) |
| Create | `client/lib/types/categories.ts` (shared type extracted from page) |
| Already done | `client/components/dashboard/sidebar.tsx` (Approvals + Settings group already present from section 09) |

## Deviations from Plan

- **Sidebar**: Already had `CheckCircle2`/`Tag` imports, `Approvals` in business group, `settings` group, and `Settings` NavGroup render from section 09. No changes needed.
- **`ConfirmationModal`**: The `client/components/common/confirmation-modal.tsx` file was an empty stub. Implemented a reusable confirmation modal wrapping `Modal` + `Button`.
- **`TaskCategoryItem` type**: Extracted to `client/lib/types/categories.ts` (shared, reusable by other sections).
- **Reorder pattern**: Used `useMutation` with `onMutate`/`onError`/`onSettled` for proper optimistic update + rollback (instead of manual useState shadow).
- **Loading/error states**: Added spinner and error alert to the page (not in original spec but added per code review).
- **`DEFAULT_FORM`**: Changed to a factory function call `{ ...EMPTY_FORM }` to avoid shared object mutation issues.
- **`role="dialog"` on `<form>`**: Removed (accessibility fix — `Modal` wraps content in a div, not a dialog element).
- **`ConfirmationModal` exports**: Removed duplicate `export default` — named export only (`export function ConfirmationModal`). All callers use `{ ConfirmationModal }` import.

## Tests

- 12 tests, all passing
- DnD mocked via `vi.fn()` factory (no JSX in mock — avoids hoisting issues)
- `capturedDragEnd` captures onDragEnd handler for direct invocation in tests
- Reorder error test uses `toast.error` assertion (not call-count heuristic)
- Added failure-path tests for POST (modal save) and PATCH (toggle active) error cases

---

## Tests First

File: `client/app/dashboard/admin/settings/categories/__tests__/CategoryManagement.test.tsx`

Use `renderWithQuery` from `client/test-utils/scheduling.tsx` and the `createMockTaskCategory` factory (added in section 13 — stub it locally in this test file if section 13 is not yet merged).

### Mock Factory (stub locally if needed)

```typescript
function createMockTaskCategory(overrides?: Partial<TaskCategoryItem>): TaskCategoryItem {
  return {
    id: 'cat-1',
    name: 'Copywriting',
    slug: 'copywriting',
    color: '#6366F1',
    icon: 'PenTool',
    department: 'marketing',
    sort_order: 0,
    is_active: true,
    ...overrides,
  }
}
```

### Test Cases

- **Renders category list:** given a mocked GET `/admin/categories/` response containing two categories, the page renders each category's name, color swatch, and department badge.
- **Drag-end dispatches reorder:** simulating a `DragEndEvent` (via `@dnd-kit` testing utilities or by calling the `onDragEnd` handler directly) results in a PATCH call to `/admin/categories/reorder/` containing `{ ordered_ids: [...] }` in the new order.
- **Reorder error triggers query invalidation:** when the reorder PATCH returns an error, `queryClient.invalidateQueries(['admin-categories'])` is called (verify by checking that the categories are re-fetched).
- **"Add Category" button opens modal:** clicking "Add Category" causes the add/edit modal to become visible.
- **Modal submit calls POST:** filling in name + color in the modal and submitting calls `POST /admin/categories/` with the form data.
- **"Edit" button opens modal pre-filled:** clicking the edit button on a category row causes the modal to open with that category's existing values populated.
- **Active toggle calls PATCH:** clicking the active/inactive toggle on a category row calls `PATCH /admin/categories/{id}/` with `{ is_active: false }` (or `true` when toggling back).
- **"Delete" button shows confirmation modal:** clicking the delete button renders the `ConfirmationModal` component before any DELETE request is fired.
- **Confirming delete calls DELETE endpoint:** confirming the confirmation modal calls `DELETE /admin/categories/{id}/` (which performs a soft delete on the backend).
- **Preview badge updates in real time:** as the user types in the name field or changes the color in the modal, the preview badge re-renders with the updated values without waiting for submission.

All tests mock `ApiService` (default import from `@/lib/api`) to intercept HTTP calls. Use `vi.mock('@/lib/api')` and assert call arguments with `expect(ApiService.patch).toHaveBeenCalledWith(...)`.

---

## Implementation Details

### Page: `client/app/dashboard/admin/settings/categories/page.tsx`

`'use client'` directive at the top. Fetches categories from the backend using React Query (`useQuery(['admin-categories'], ...)` calling `GET /admin/categories/`). Renders the list via `@dnd-kit/sortable`.

#### Type

```typescript
interface TaskCategoryItem {
  id: string
  name: string
  slug: string
  color: string        // hex string, e.g. '#6366F1'
  icon: string         // lucide icon name string, e.g. 'PenTool'
  department: 'marketing' | 'developer' | 'admin' | 'all'
  sort_order: number
  is_active: boolean
}
```

#### Layout Structure

```
<page>
  <header>
    <h1>Task Categories</h1>
    <p className="text-muted-foreground">Manage the categories agents use when creating tasks.</p>
    <Button onClick={openAddModal}>Add Category</Button>
  </header>

  <DndContext onDragEnd={handleDragEnd} collisionDetection={closestCenter}>
    <SortableContext items={categoryIds} strategy={verticalListSortingStrategy}>
      {categories.map(cat => <SortableCategoryRow key={cat.id} category={cat} />)}
    </SortableContext>
  </DndContext>

  {isModalOpen && <CategoryModal ... />}
  {deleteTarget && <ConfirmationModal ... />}
```

The page wraps the entire category list in `DndContext` + `SortableContext` from `@dnd-kit/sortable`. Import `closestCenter` and `verticalListSortingStrategy` from their respective packages.

#### Sortable Row Component

Each row is a small inline component (or a named function in the same file) that calls `useSortable(id)` from `@dnd-kit/sortable`. It applies `transform` and `transition` styles from the hook's return value. Contents:

- `GripVertical` icon (from `lucide-react`) with `{...attributes} {...listeners}` spread on it — the drag handle
- Color swatch: `<span className="w-4 h-4 rounded-full inline-block" style={{ backgroundColor: category.color }} />`
- Category name (bold)
- Department `<Badge>` — label is the department value capitalized
- Active/inactive toggle: a `<button>` that renders a `<Badge variant={is_active ? 'success' : 'default'}>` and calls `handleToggleActive(category)` on click
- Edit `<Button variant="ghost" size="sm">` with `<Edit className="w-4 h-4" />` icon
- Delete `<Button variant="ghost" size="sm">` with `<Trash2 className="w-4 h-4" />` icon, styled in red
- Preview badge section: shows a small colored badge with the category name using the category's `color`, to mimic how it appears in task views

#### Drag-and-Drop Logic

```typescript
function handleDragEnd(event: DragEndEvent) {
  const { active, over } = event
  if (!over || active.id === over.id) return

  // 1. Compute new order with arrayMove (from @dnd-kit/sortable)
  const oldIndex = categories.findIndex(c => c.id === active.id)
  const newIndex = categories.findIndex(c => c.id === over.id)
  const reordered = arrayMove(categories, oldIndex, newIndex)

  // 2. Optimistic update
  setCategories(reordered)

  // 3. Persist to backend
  const orderedIds = reordered.map(c => c.id)
  ApiService.patch('/admin/categories/reorder/', { ordered_ids: orderedIds })
    .catch(() => {
      // Show error toast
      toast.error('Failed to save new order')
      // Rollback by refetching authoritative order
      queryClient.invalidateQueries(['admin-categories'])
    })
}
```

Use `useState` to hold a local mutable copy of the categories array (initialized from React Query data). This allows the optimistic reorder to update visually before the API call completes.

#### Active Toggle

```typescript
async function handleToggleActive(category: TaskCategoryItem) {
  await ApiService.patch(`/admin/categories/${category.id}/`, {
    is_active: !category.is_active,
  })
  queryClient.invalidateQueries(['admin-categories'])
}
```

Wrap in try/catch and show a `toast.error(...)` on failure.

#### Delete Flow

Clicking the delete button sets `deleteTarget` state to the category. This renders `ConfirmationModal` from `client/components/common/confirmation-modal.tsx`. On confirm, call `ApiService.delete('/admin/categories/${deleteTarget.id}/')` then `queryClient.invalidateQueries(['admin-categories'])`. On cancel or after success, clear `deleteTarget` to null.

---

### Add/Edit Modal

Use `Modal` from `client/components/ui/modal.tsx`.

#### Form Fields

| Field | Component | Notes |
|-------|-----------|-------|
| Name | `Input` (required) | Text, required |
| Color | `<input type="color" />` + preview swatch | Native color picker; show live hex string and a `<span style={{ backgroundColor: formValues.color }}>` preview |
| Icon | `Select` from `client/components/ui/select.tsx` | List of common lucide icon names as string options (e.g. `['PenTool', 'Image', 'Tag', 'Code2', 'BarChart3', 'Calendar', 'Megaphone', 'Mail']`) |
| Department | `Select` | Options: `marketing`, `developer`, `admin`, `all` |
| Preview | Read-only badge | Re-renders in real time from current form values: `<Badge style={{ backgroundColor: formValues.color }}>{ formValues.name || 'Preview' }</Badge>` |

When editing, pre-populate all fields with the selected category's values. When adding, start with empty name, `'#6366F1'` as default color, `'Tag'` as default icon, `'all'` as default department.

On submit:
- If adding: `ApiService.post('/admin/categories/', formValues)` then invalidate query and close modal
- If editing: `ApiService.patch('/admin/categories/${editTarget.id}/', formValues)` then invalidate query and close modal

Show `toast.success('Category saved')` on success and `toast.error(errorMessage)` on failure. Use the `sonner` toast library (already installed at `import { toast } from 'sonner'`).

---

### Sidebar Update

File: `client/components/dashboard/sidebar.tsx`

The `adminNavGroups` object currently has groups: `main`, `business`, `team`, `company`, `platform`, `bottom`.

**Two additions are required:**

1. **Add "Approvals" to the `business` group** (this links to section 09's page):
   ```typescript
   { href: '/dashboard/admin/approvals', label: 'Approvals', icon: <CheckCircle2 className="w-5 h-5" /> }
   ```
   Import `CheckCircle2` from `lucide-react`.

2. **Add a new `settings` group** to `adminNavGroups` containing the category management link:
   ```typescript
   settings: [
     { href: '/dashboard/admin/settings/categories', label: 'Categories', icon: <Tag className="w-5 h-5" /> },
   ],
   ```
   Import `Tag` from `lucide-react`.

The sidebar rendering JSX (around line 386) currently renders `business`, `team`, `company`, `platform` groups. Add a render call for the new `settings` group in the same pattern as the existing groups. Place it after `platform` and before `bottom`.

---

## API Endpoints Consumed

All require the user to be authenticated as admin (`IsAdminUser`).

| Method | URL | Purpose |
|--------|-----|---------|
| GET | `/admin/categories/` | Fetch all categories including inactive |
| POST | `/admin/categories/` | Create new category |
| PATCH | `/admin/categories/{id}/` | Update fields (name, color, icon, department, is_active) |
| DELETE | `/admin/categories/{id}/` | Soft delete (sets `is_active=False`) |
| PATCH | `/admin/categories/reorder/` | Bulk sort_order update — body: `{ ordered_ids: string[] }` |

The backend serializer (`TaskCategoryAdminSerializer`) exposes: `id`, `name`, `slug`, `color`, `icon`, `department`, `sort_order`, `is_active`.

---

## Key Libraries Used

- `@dnd-kit/core` — `DndContext`, `DragEndEvent`, `closestCenter`
- `@dnd-kit/sortable` — `SortableContext`, `useSortable`, `arrayMove`, `verticalListSortingStrategy`
- `lucide-react` — `GripVertical`, `Edit`, `Trash2`, `Plus`, `CheckCircle2`, `Tag`
- `sonner` — `toast.success` / `toast.error`
- `@tanstack/react-query` — `useQuery`, `useQueryClient`
- `client/components/ui/modal.tsx` — `Modal` (add/edit form)
- `client/components/ui/button.tsx` — `Button`
- `client/components/ui/input.tsx` — `Input`
- `client/components/ui/select.tsx` — `Select`
- `client/components/ui/badge.tsx` — `Badge`
- `client/components/common/confirmation-modal.tsx` — `ConfirmationModal` (delete confirmation)
- `client/lib/api.ts` — `ApiService` (default export) for all HTTP calls

Do not implement custom modal, drag-and-drop, or toast logic from scratch — all of the above are pre-installed.

---

## Implementation Checklist

1. Create the directory `client/app/dashboard/admin/settings/categories/`
2. Write the test file at `__tests__/CategoryManagement.test.tsx` with all test cases listed above
3. Create `page.tsx` with:
   - `TaskCategoryItem` type definition
   - React Query fetch for categories list
   - Local `categories` state initialized from query data
   - `DndContext` + `SortableContext` + `SortableCategoryRow` component
   - `handleDragEnd` with optimistic update and error rollback
   - `handleToggleActive` with `PATCH` + query invalidation
   - Delete button → `ConfirmationModal` flow
   - "Add Category" button → `CategoryModal` flow
4. Implement `CategoryModal` (can be in the same file or a small sub-component):
   - All four form fields with live preview badge
   - POST on add, PATCH on edit
5. Update `client/components/dashboard/sidebar.tsx`:
   - Import `CheckCircle2` and `Tag` from `lucide-react`
   - Add Approvals entry to `business` group in `adminNavGroups`
   - Add `settings` group with Categories entry
   - Add render call for `settings` group in the JSX output
