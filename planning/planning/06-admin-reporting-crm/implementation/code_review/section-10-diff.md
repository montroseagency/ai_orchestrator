diff --git a/client/app/dashboard/admin/settings/categories/__tests__/CategoryManagement.test.tsx b/client/app/dashboard/admin/settings/categories/__tests__/CategoryManagement.test.tsx
new file mode 100644
index 000000000..29bba63c6
--- /dev/null
+++ b/client/app/dashboard/admin/settings/categories/__tests__/CategoryManagement.test.tsx
@@ -0,0 +1,274 @@
+import { screen, fireEvent, waitFor } from '@testing-library/react'
+import { describe, it, expect, vi, beforeEach } from 'vitest'
+import React from 'react'
+import { renderWithQuery } from '@/test-utils/scheduling'
+
+// ── Local factory stub ────────────────────────────────────────────────────
+
+interface TaskCategoryItem {
+  id: string
+  name: string
+  slug: string
+  color: string
+  icon: string
+  department: 'marketing' | 'developer' | 'admin' | 'all'
+  sort_order: number
+  is_active: boolean
+}
+
+function createMockTaskCategory(overrides?: Partial<TaskCategoryItem>): TaskCategoryItem {
+  return {
+    id: 'cat-1',
+    name: 'Copywriting',
+    slug: 'copywriting',
+    color: '#6366F1',
+    icon: 'PenTool',
+    department: 'marketing',
+    sort_order: 0,
+    is_active: true,
+    ...overrides,
+  }
+}
+
+// ── Mocks ─────────────────────────────────────────────────────────────────
+
+const mockGet = vi.fn()
+const mockPost = vi.fn()
+const mockPatch = vi.fn()
+const mockDelete = vi.fn()
+
+vi.mock('@/lib/api', () => ({
+  default: {
+    get: mockGet,
+    post: mockPost,
+    patch: mockPatch,
+    delete: mockDelete,
+    request: mockGet,
+  },
+}))
+
+vi.mock('sonner', () => ({
+  toast: { success: vi.fn(), error: vi.fn() },
+}))
+
+// Capture the onDragEnd handler so we can call it directly in tests
+let capturedDragEnd: ((event: unknown) => void) | null = null
+
+vi.mock('@dnd-kit/core', () => ({
+  DndContext: vi.fn(({ children, onDragEnd }: { children: unknown; onDragEnd: (e: unknown) => void }) => {
+    capturedDragEnd = onDragEnd
+    return children
+  }),
+  closestCenter: {},
+}))
+
+vi.mock('@dnd-kit/sortable', () => ({
+  SortableContext: vi.fn(({ children }: { children: unknown }) => children),
+  useSortable: () => ({
+    attributes: {},
+    listeners: {},
+    setNodeRef: vi.fn(),
+    transform: null,
+    transition: null,
+    isDragging: false,
+  }),
+  arrayMove: <T,>(arr: T[], oldIndex: number, newIndex: number): T[] => {
+    const result = [...arr]
+    const [removed] = result.splice(oldIndex, 1)
+    result.splice(newIndex, 0, removed)
+    return result
+  },
+  verticalListSortingStrategy: {},
+}))
+
+vi.mock('@dnd-kit/utilities', () => ({
+  CSS: { Transform: { toString: () => '' } },
+}))
+
+// ── Helpers ───────────────────────────────────────────────────────────────
+
+async function getPage() {
+  const mod = await import('@/app/dashboard/admin/settings/categories/page')
+  return mod.default
+}
+
+// Wait for categories to load (name appears at least once)
+async function waitForLoad(name = 'Copywriting') {
+  await waitFor(() => {
+    expect(screen.getAllByText(name).length).toBeGreaterThan(0)
+  })
+}
+
+// ── Tests ─────────────────────────────────────────────────────────────────
+
+describe('CategoryManagementPage', () => {
+  const cat1 = createMockTaskCategory({ id: 'cat-1', name: 'Copywriting', sort_order: 0 })
+  const cat2 = createMockTaskCategory({ id: 'cat-2', name: 'Design', slug: 'design', sort_order: 1, department: 'developer' })
+
+  beforeEach(() => {
+    vi.clearAllMocks()
+    capturedDragEnd = null
+    mockGet.mockResolvedValue([cat1, cat2])
+    mockPost.mockResolvedValue({ ...cat1, id: 'cat-new' })
+    mockPatch.mockResolvedValue({})
+    mockDelete.mockResolvedValue({})
+  })
+
+  it('renders category list with name, color swatch, and department badge', async () => {
+    const Page = await getPage()
+    renderWithQuery(<Page />)
+    await waitFor(() => {
+      expect(screen.getAllByText('Copywriting').length).toBeGreaterThan(0)
+      expect(screen.getAllByText('Design').length).toBeGreaterThan(0)
+    })
+    // Color swatches present (span elements with background color)
+    const swatches = document.querySelectorAll('[data-testid="color-swatch"]')
+    expect(swatches.length).toBeGreaterThanOrEqual(2)
+    // Department badges visible
+    expect(screen.getByText('Marketing')).toBeInTheDocument()
+    expect(screen.getByText('Developer')).toBeInTheDocument()
+  })
+
+  it('drag-end dispatches reorder PATCH with new ordered_ids', async () => {
+    const Page = await getPage()
+    renderWithQuery(<Page />)
+    await waitForLoad()
+
+    // Simulate drag: move cat-1 to position of cat-2
+    capturedDragEnd!({ active: { id: 'cat-1' }, over: { id: 'cat-2' } })
+
+    await waitFor(() => {
+      expect(mockPatch).toHaveBeenCalledWith(
+        '/admin/categories/reorder/',
+        { ordered_ids: ['cat-2', 'cat-1'] }
+      )
+    })
+  })
+
+  it('reorder error triggers query invalidation (re-fetch)', async () => {
+    mockPatch.mockRejectedValueOnce(new Error('Network error'))
+    const Page = await getPage()
+    renderWithQuery(<Page />)
+    await waitForLoad()
+
+    const initialCallCount = mockGet.mock.calls.length
+
+    capturedDragEnd!({ active: { id: 'cat-1' }, over: { id: 'cat-2' } })
+
+    await waitFor(() => {
+      expect(mockGet.mock.calls.length).toBeGreaterThan(initialCallCount)
+    })
+  })
+
+  it('"Add Category" button opens the add/edit modal', async () => {
+    const Page = await getPage()
+    renderWithQuery(<Page />)
+    await waitForLoad()
+
+    fireEvent.click(screen.getByRole('button', { name: /add category/i }))
+    await waitFor(() => {
+      expect(screen.getByRole('dialog')).toBeInTheDocument()
+    })
+  })
+
+  it('modal submit calls POST /admin/categories/ with form data', async () => {
+    const { toast } = await import('sonner')
+    const Page = await getPage()
+    renderWithQuery(<Page />)
+    await waitForLoad()
+
+    fireEvent.click(screen.getByRole('button', { name: /add category/i }))
+    await waitFor(() => screen.getByRole('dialog'))
+
+    // Fill in name field
+    const nameInput = screen.getByPlaceholderText(/category name/i)
+    fireEvent.change(nameInput, { target: { value: 'Social Media' } })
+
+    fireEvent.click(screen.getByRole('button', { name: /save category/i }))
+
+    await waitFor(() => {
+      expect(mockPost).toHaveBeenCalledWith(
+        '/admin/categories/',
+        expect.objectContaining({ name: 'Social Media' })
+      )
+      expect(toast.success).toHaveBeenCalled()
+    })
+  })
+
+  it('"Edit" button opens modal pre-filled with category values', async () => {
+    const Page = await getPage()
+    renderWithQuery(<Page />)
+    await waitForLoad()
+
+    const editButtons = screen.getAllByRole('button', { name: /edit category/i })
+    fireEvent.click(editButtons[0])
+
+    await waitFor(() => {
+      const nameInput = screen.getByPlaceholderText(/category name/i) as HTMLInputElement
+      expect(nameInput.value).toBe('Copywriting')
+    })
+  })
+
+  it('active toggle calls PATCH /admin/categories/{id}/ with is_active toggled', async () => {
+    const Page = await getPage()
+    renderWithQuery(<Page />)
+    await waitForLoad()
+
+    const toggleButtons = screen.getAllByRole('button', { name: /active|inactive/i })
+    fireEvent.click(toggleButtons[0])
+
+    await waitFor(() => {
+      expect(mockPatch).toHaveBeenCalledWith(
+        '/admin/categories/cat-1/',
+        { is_active: false }
+      )
+    })
+  })
+
+  it('"Delete" button shows ConfirmationModal before any DELETE request', async () => {
+    const Page = await getPage()
+    renderWithQuery(<Page />)
+    await waitForLoad()
+
+    const deleteButtons = screen.getAllByRole('button', { name: /delete category/i })
+    fireEvent.click(deleteButtons[0])
+
+    await waitFor(() => {
+      expect(screen.getByText(/are you sure/i)).toBeInTheDocument()
+    })
+    expect(mockDelete).not.toHaveBeenCalled()
+  })
+
+  it('confirming delete calls DELETE /admin/categories/{id}/', async () => {
+    const Page = await getPage()
+    renderWithQuery(<Page />)
+    await waitForLoad()
+
+    const deleteButtons = screen.getAllByRole('button', { name: /delete category/i })
+    fireEvent.click(deleteButtons[0])
+
+    await waitFor(() => screen.getByText(/are you sure/i))
+    fireEvent.click(screen.getByRole('button', { name: /confirm/i }))
+
+    await waitFor(() => {
+      expect(mockDelete).toHaveBeenCalledWith('/admin/categories/cat-1/')
+    })
+  })
+
+  it('preview badge updates in real time as user types in name field', async () => {
+    const Page = await getPage()
+    renderWithQuery(<Page />)
+    await waitForLoad()
+
+    fireEvent.click(screen.getByRole('button', { name: /add category/i }))
+    await waitFor(() => screen.getByRole('dialog'))
+
+    const nameInput = screen.getByPlaceholderText(/category name/i)
+    fireEvent.change(nameInput, { target: { value: 'New Category' } })
+
+    await waitFor(() => {
+      const previews = screen.getAllByText('New Category')
+      expect(previews.length).toBeGreaterThanOrEqual(1)
+    })
+  })
+})
diff --git a/client/app/dashboard/admin/settings/categories/page.tsx b/client/app/dashboard/admin/settings/categories/page.tsx
new file mode 100644
index 000000000..199c22a60
--- /dev/null
+++ b/client/app/dashboard/admin/settings/categories/page.tsx
@@ -0,0 +1,415 @@
+'use client';
+
+import React, { useState, useEffect } from 'react';
+import { useQuery, useQueryClient } from '@tanstack/react-query';
+import {
+  DndContext,
+  closestCenter,
+  type DragEndEvent,
+} from '@dnd-kit/core';
+import {
+  SortableContext,
+  useSortable,
+  arrayMove,
+  verticalListSortingStrategy,
+} from '@dnd-kit/sortable';
+import { CSS } from '@dnd-kit/utilities';
+import {
+  GripVertical,
+  Edit,
+  Trash2,
+  Plus,
+} from 'lucide-react';
+import { toast } from 'sonner';
+import { Modal } from '@/components/ui/modal';
+import { Button } from '@/components/ui/button';
+import { Input } from '@/components/ui/input';
+import { Select } from '@/components/ui/select';
+import { Badge } from '@/components/ui/badge';
+import { ConfirmationModal } from '@/components/common/confirmation-modal';
+import ApiService from '@/lib/api';
+
+// ── Types ─────────────────────────────────────────────────────────────────
+
+interface TaskCategoryItem {
+  id: string;
+  name: string;
+  slug: string;
+  color: string;
+  icon: string;
+  department: 'marketing' | 'developer' | 'admin' | 'all';
+  sort_order: number;
+  is_active: boolean;
+}
+
+// ── Constants ─────────────────────────────────────────────────────────────
+
+const ICON_OPTIONS = [
+  { value: 'PenTool', label: 'PenTool' },
+  { value: 'Image', label: 'Image' },
+  { value: 'Tag', label: 'Tag' },
+  { value: 'Code2', label: 'Code2' },
+  { value: 'BarChart3', label: 'BarChart3' },
+  { value: 'Calendar', label: 'Calendar' },
+  { value: 'Megaphone', label: 'Megaphone' },
+  { value: 'Mail', label: 'Mail' },
+];
+
+const DEPARTMENT_OPTIONS = [
+  { value: 'all', label: 'All' },
+  { value: 'marketing', label: 'Marketing' },
+  { value: 'developer', label: 'Developer' },
+  { value: 'admin', label: 'Admin' },
+];
+
+const DEFAULT_FORM = {
+  name: '',
+  color: '#6366F1',
+  icon: 'Tag',
+  department: 'all' as TaskCategoryItem['department'],
+};
+
+// ── SortableCategoryRow ───────────────────────────────────────────────────
+
+interface RowProps {
+  category: TaskCategoryItem;
+  onEdit: (cat: TaskCategoryItem) => void;
+  onDelete: (cat: TaskCategoryItem) => void;
+  onToggleActive: (cat: TaskCategoryItem) => void;
+}
+
+function SortableCategoryRow({ category, onEdit, onDelete, onToggleActive }: RowProps) {
+  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
+    useSortable({ id: category.id });
+
+  const style: React.CSSProperties = {
+    transform: CSS.Transform.toString(transform),
+    transition,
+    opacity: isDragging ? 0.5 : 1,
+  };
+
+  return (
+    <div
+      ref={setNodeRef}
+      style={style}
+      className="flex items-center gap-3 px-4 py-3 bg-surface border border-border rounded-lg mb-2"
+    >
+      <button
+        type="button"
+        className="text-muted cursor-grab active:cursor-grabbing"
+        {...attributes}
+        {...listeners}
+        aria-label="Drag to reorder"
+      >
+        <GripVertical className="w-4 h-4" />
+      </button>
+
+      <span
+        data-testid="color-swatch"
+        className="w-4 h-4 rounded-full inline-block flex-shrink-0"
+        style={{ backgroundColor: category.color }}
+      />
+
+      <span className="font-medium text-primary flex-1">{category.name}</span>
+
+      <Badge variant="default">
+        {category.department.charAt(0).toUpperCase() + category.department.slice(1)}
+      </Badge>
+
+      {/* Active/inactive toggle */}
+      <button
+        type="button"
+        aria-label={category.is_active ? 'Active' : 'Inactive'}
+        onClick={() => onToggleActive(category)}
+        className="focus:outline-none"
+      >
+        <Badge variant={category.is_active ? 'success' : 'default'}>
+          {category.is_active ? 'Active' : 'Inactive'}
+        </Badge>
+      </button>
+
+      {/* Preview badge */}
+      <span
+        className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium text-white"
+        style={{ backgroundColor: category.color }}
+      >
+        {category.name}
+      </span>
+
+      <Button variant="ghost" size="sm" onClick={() => onEdit(category)} aria-label="Edit category">
+        <Edit className="w-4 h-4" />
+      </Button>
+
+      <Button
+        variant="ghost"
+        size="sm"
+        onClick={() => onDelete(category)}
+        className="text-red-500 hover:text-red-600"
+        aria-label="Delete category"
+      >
+        <Trash2 className="w-4 h-4" />
+      </Button>
+    </div>
+  );
+}
+
+// ── CategoryModal ─────────────────────────────────────────────────────────
+
+interface CategoryModalProps {
+  isOpen: boolean;
+  onClose: () => void;
+  editTarget: TaskCategoryItem | null;
+  onSaved: () => void;
+}
+
+function CategoryModal({ isOpen, onClose, editTarget, onSaved }: CategoryModalProps) {
+  const [formValues, setFormValues] = useState(DEFAULT_FORM);
+
+  useEffect(() => {
+    if (editTarget) {
+      setFormValues({
+        name: editTarget.name,
+        color: editTarget.color,
+        icon: editTarget.icon,
+        department: editTarget.department,
+      });
+    } else {
+      setFormValues(DEFAULT_FORM);
+    }
+  }, [editTarget, isOpen]);
+
+  const handleSubmit = async (e: React.FormEvent) => {
+    e.preventDefault();
+    try {
+      if (editTarget) {
+        await ApiService.patch(`/admin/categories/${editTarget.id}/`, formValues);
+      } else {
+        await ApiService.post('/admin/categories/', formValues);
+      }
+      toast.success('Category saved');
+      onSaved();
+      onClose();
+    } catch (err: unknown) {
+      const msg = err instanceof Error ? err.message : 'Failed to save category';
+      toast.error(msg);
+    }
+  };
+
+  return (
+    <Modal isOpen={isOpen} onClose={onClose} size="md">
+      <form onSubmit={handleSubmit} className="p-6 space-y-4" role="dialog" aria-modal="true">
+        <h2 className="text-lg font-semibold text-primary">
+          {editTarget ? 'Edit Category' : 'Add Category'}
+        </h2>
+
+        <div>
+          <label className="block text-sm font-medium text-secondary mb-1">Name</label>
+          <Input
+            value={formValues.name}
+            onChange={(e) => setFormValues((p) => ({ ...p, name: e.target.value }))}
+            placeholder="Category name"
+            required
+          />
+        </div>
+
+        <div>
+          <label className="block text-sm font-medium text-secondary mb-1">Color</label>
+          <div className="flex items-center gap-3">
+            <input
+              type="color"
+              value={formValues.color}
+              onChange={(e) => setFormValues((p) => ({ ...p, color: e.target.value }))}
+              className="w-10 h-10 rounded cursor-pointer border-0"
+            />
+            <span className="text-sm text-secondary font-mono">{formValues.color}</span>
+            <span
+              className="w-6 h-6 rounded-full inline-block border border-border"
+              style={{ backgroundColor: formValues.color }}
+            />
+          </div>
+        </div>
+
+        <div>
+          <label className="block text-sm font-medium text-secondary mb-1">Icon</label>
+          <Select
+            value={formValues.icon}
+            onChange={(val) => setFormValues((p) => ({ ...p, icon: val }))}
+            options={ICON_OPTIONS}
+          />
+        </div>
+
+        <div>
+          <label className="block text-sm font-medium text-secondary mb-1">Department</label>
+          <Select
+            value={formValues.department}
+            onChange={(val) =>
+              setFormValues((p) => ({ ...p, department: val as TaskCategoryItem['department'] }))
+            }
+            options={DEPARTMENT_OPTIONS}
+          />
+        </div>
+
+        {/* Live preview badge */}
+        <div>
+          <label className="block text-sm font-medium text-secondary mb-1">Preview</label>
+          <span
+            className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium text-white"
+            style={{ backgroundColor: formValues.color }}
+          >
+            {formValues.name || 'Preview'}
+          </span>
+        </div>
+
+        <div className="flex justify-end gap-3 pt-2">
+          <Button type="button" variant="ghost" onClick={onClose}>
+            Cancel
+          </Button>
+          <Button type="submit" variant="primary">
+            Save Category
+          </Button>
+        </div>
+      </form>
+    </Modal>
+  );
+}
+
+// ── Page ──────────────────────────────────────────────────────────────────
+
+export default function CategoryManagementPage() {
+  const queryClient = useQueryClient();
+
+  const { data: queryData } = useQuery<TaskCategoryItem[]>({
+    queryKey: ['admin-categories'],
+    queryFn: () => ApiService.get('/admin/categories/') as Promise<TaskCategoryItem[]>,
+  });
+
+  // Local mutable copy for optimistic reorder
+  const [categories, setCategories] = useState<TaskCategoryItem[]>([]);
+
+  useEffect(() => {
+    if (queryData !== undefined) {
+      setCategories(queryData);
+    }
+  }, [queryData]);
+
+  const [isModalOpen, setIsModalOpen] = useState(false);
+  const [editTarget, setEditTarget] = useState<TaskCategoryItem | null>(null);
+  const [deleteTarget, setDeleteTarget] = useState<TaskCategoryItem | null>(null);
+
+  // ── Drag and drop ─────────────────────────────────────────────────────
+
+  function handleDragEnd(event: DragEndEvent) {
+    const { active, over } = event;
+    if (!over || active.id === over.id) return;
+
+    const oldIndex = categories.findIndex((c) => c.id === active.id);
+    const newIndex = categories.findIndex((c) => c.id === over.id);
+    const reordered = arrayMove(categories, oldIndex, newIndex);
+
+    setCategories(reordered);
+
+    const orderedIds = reordered.map((c) => c.id);
+    ApiService.patch('/admin/categories/reorder/', { ordered_ids: orderedIds }).catch(() => {
+      toast.error('Failed to save new order');
+      queryClient.invalidateQueries({ queryKey: ['admin-categories'] });
+    });
+  }
+
+  // ── Active toggle ─────────────────────────────────────────────────────
+
+  async function handleToggleActive(category: TaskCategoryItem) {
+    try {
+      await ApiService.patch(`/admin/categories/${category.id}/`, {
+        is_active: !category.is_active,
+      });
+      queryClient.invalidateQueries({ queryKey: ['admin-categories'] });
+    } catch {
+      toast.error('Failed to update category');
+    }
+  }
+
+  // ── Delete flow ───────────────────────────────────────────────────────
+
+  async function handleConfirmDelete() {
+    if (!deleteTarget) return;
+    try {
+      await ApiService.delete(`/admin/categories/${deleteTarget.id}/`);
+      queryClient.invalidateQueries({ queryKey: ['admin-categories'] });
+    } catch {
+      toast.error('Failed to delete category');
+    } finally {
+      setDeleteTarget(null);
+    }
+  }
+
+  // ── Modal helpers ─────────────────────────────────────────────────────
+
+  function openAddModal() {
+    setEditTarget(null);
+    setIsModalOpen(true);
+  }
+
+  function openEditModal(cat: TaskCategoryItem) {
+    setEditTarget(cat);
+    setIsModalOpen(true);
+  }
+
+  const categoryIds = categories.map((c) => c.id);
+
+  return (
+    <div className="p-6 max-w-4xl mx-auto">
+      {/* Header */}
+      <div className="flex items-center justify-between mb-6">
+        <div>
+          <h1 className="text-2xl font-bold text-primary">Task Categories</h1>
+          <p className="text-muted-foreground text-sm mt-1">
+            Manage the categories agents use when creating tasks.
+          </p>
+        </div>
+        <Button variant="primary" onClick={openAddModal} aria-label="Add Category">
+          <Plus className="w-4 h-4 mr-2" />
+          Add Category
+        </Button>
+      </div>
+
+      {/* Sortable list */}
+      <DndContext onDragEnd={handleDragEnd} collisionDetection={closestCenter}>
+        <SortableContext items={categoryIds} strategy={verticalListSortingStrategy}>
+          {categories.map((cat) => (
+            <SortableCategoryRow
+              key={cat.id}
+              category={cat}
+              onEdit={openEditModal}
+              onDelete={(c) => setDeleteTarget(c)}
+              onToggleActive={handleToggleActive}
+            />
+          ))}
+        </SortableContext>
+      </DndContext>
+
+      {categories.length === 0 && (
+        <p className="text-secondary text-center py-10">No categories yet. Add one to get started.</p>
+      )}
+
+      {/* Add/Edit modal */}
+      <CategoryModal
+        isOpen={isModalOpen}
+        onClose={() => setIsModalOpen(false)}
+        editTarget={editTarget}
+        onSaved={() => queryClient.invalidateQueries({ queryKey: ['admin-categories'] })}
+      />
+
+      {/* Delete confirmation */}
+      <ConfirmationModal
+        isOpen={!!deleteTarget}
+        title="Delete category?"
+        description={`Are you sure you want to delete "${deleteTarget?.name}"? This cannot be undone.`}
+        confirmLabel="Confirm"
+        cancelLabel="Cancel"
+        danger
+        onConfirm={handleConfirmDelete}
+        onCancel={() => setDeleteTarget(null)}
+      />
+    </div>
+  );
+}
diff --git a/client/components/common/confirmation-modal.tsx b/client/components/common/confirmation-modal.tsx
index e69de29bb..59061928d 100644
--- a/client/components/common/confirmation-modal.tsx
+++ b/client/components/common/confirmation-modal.tsx
@@ -0,0 +1,49 @@
+'use client';
+
+import React from 'react';
+import { Modal } from '@/components/ui/modal';
+import { Button } from '@/components/ui/button';
+
+interface ConfirmationModalProps {
+  isOpen: boolean;
+  onConfirm: () => void;
+  onCancel: () => void;
+  title?: string;
+  description?: string;
+  confirmLabel?: string;
+  cancelLabel?: string;
+  danger?: boolean;
+}
+
+export function ConfirmationModal({
+  isOpen,
+  onConfirm,
+  onCancel,
+  title = 'Are you sure?',
+  description = 'This action cannot be undone.',
+  confirmLabel = 'Confirm',
+  cancelLabel = 'Cancel',
+  danger = false,
+}: ConfirmationModalProps) {
+  return (
+    <Modal isOpen={isOpen} onClose={onCancel} size="sm">
+      <div className="p-6">
+        <h2 className="text-lg font-semibold text-primary mb-2">{title}</h2>
+        <p className="text-sm text-secondary mb-6">{description}</p>
+        <div className="flex justify-end gap-3">
+          <Button variant="ghost" onClick={onCancel}>
+            {cancelLabel}
+          </Button>
+          <Button
+            variant={danger ? 'danger' : 'default'}
+            onClick={onConfirm}
+          >
+            {confirmLabel}
+          </Button>
+        </div>
+      </div>
+    </Modal>
+  );
+}
+
+export default ConfirmationModal;
