<!-- PROJECT_CONFIG
runtime: typescript-npm
test_command: cd client && npx vitest run
END_PROJECT_CONFIG -->

<!-- SECTION_MANIFEST
section-01-data-foundation
section-02-view-chrome
section-03-kanban-view
section-04-list-view
section-05-task-modal
section-06-page-composition
END_MANIFEST -->

# Implementation Sections Index

## Dependency Graph

| Section | Depends On | Blocks | Parallelizable |
|---------|------------|--------|----------------|
| section-01-data-foundation | - | 02, 03, 04, 05, 06 | Yes |
| section-02-view-chrome | 01 | 06 | Yes (with 03, 04, 05) |
| section-03-kanban-view | 01 | 06 | Yes (with 02, 04, 05) |
| section-04-list-view | 01 | 06 | Yes (with 02, 03, 05) |
| section-05-task-modal | 01 | 06 | Yes (with 02, 03, 04) |
| section-06-page-composition | 01, 02, 03, 04, 05 | - | No |

## Execution Order

1. **section-01-data-foundation** (no dependencies — run first)
2. **section-02-view-chrome, section-03-kanban-view, section-04-list-view, section-05-task-modal** (all run in parallel after section-01)
3. **section-06-page-composition** (final — requires all previous sections)

## Section Summaries

### section-01-data-foundation
Pure utility layer with no external React dependencies. Includes:
- `clientPalette.ts` — deterministic client-ID-to-color mapping with null/undefined guard
- `ClientBadge.tsx` — color-coded client chip with "Unassigned" fallback
- `useTaskFilters.ts` — URL param parsing/updating hook (useSearchParams + useRouter)

TDD: write `clientPalette.test.ts` and `useTaskFilters.test.ts` first.

### section-02-view-chrome
UI chrome components rendered above the task view area. Includes:
- `ViewToggle.tsx` — Kanban/List segmented control (Lucide icons, localStorage + URL param sync)
- `TaskFilterBar.tsx` — horizontal filter row (client chips, category, status, priority dropdowns, debounced search)

Depends on section-01 for `useTaskFilters`, `ClientBadge`.
TDD: write `ViewToggle.test.tsx` and `TaskFilterBar.test.tsx` first.

### section-03-kanban-view
Drag-and-drop Kanban board. Includes:
- `TaskCard.tsx` — card with title, badges, priority dot, due date, recurrence icon, drag handle
- `TaskCardOverlay.tsx` — DragOverlay ghost copy during drag
- `KanbanColumn.tsx` — droppable column with SortableContext, empty-state, task count badge
- `TasksKanbanView.tsx` — DndContext root, 4 columns, onDragEnd logic with useCompleteGlobalTask/useUpdateGlobalTask, optimistic updates + error toasts

Depends on section-01 for `ClientBadge`, `clientPalette`.
TDD: write `TaskCard.test.tsx`, `KanbanColumn.test.tsx`, `TasksKanbanView.test.tsx` first.

### section-04-list-view
Sortable table list view with bulk operations. Includes:
- `TasksListView.tsx` — HTML table, sortable columns, inline status dropdown, row-click modal, mobile card layout fallback
- `BulkActionBar.tsx` — appears when rows selected; bulk status change and delete with per-item error handling

Depends on section-01 for `ClientBadge`.
TDD: write `TasksListView.test.tsx` and `BulkActionBar.test.tsx` first.

### section-05-task-modal
Create/edit task modal with recurrence rule builder. Includes:
- `RecurrenceBuilder.tsx` — frequency selector (Daily/Weekly/Biweekly/Monthly/Yearly/Custom), day-of-week checkboxes, interval input, end condition radio group; extracted from RecurringTaskManager (which is NOT modified)
- `TaskModal.tsx` — multi-section modal (Basic Info, Assignment, Scheduling, Recurrence toggle); explicit user-editable field payload; Save / Save & Schedule / Cancel actions

Depends on section-01 for type awareness; uses existing `modal.tsx` UI primitive.
TDD: write `RecurrenceBuilder.test.tsx` and `TaskModal.test.tsx` first.

### section-06-page-composition
Top-level page entry point and integration tests. Includes:
- `page.tsx` — composes ViewToggle, TaskFilterBar, TasksKanbanView/TasksListView (conditional on view), TaskModal at page level; reads filters from useTaskFilters; single useGlobalTasks call; "+ New Task" button

Depends on all previous sections.
TDD: write `page.test.tsx` first (integration test covering view switching, filter preservation, modal open/close).
