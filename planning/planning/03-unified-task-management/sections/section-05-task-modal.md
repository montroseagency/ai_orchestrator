# Section 05 — Task Modal

## Overview

This section implements the create/edit task modal and the standalone recurrence rule builder it depends on. When complete, agents can create new tasks and edit existing ones through a structured multi-section modal with full recurrence support.

**Parallel with:** section-02 (view chrome), section-03 (kanban view), section-04 (list view)
**Depends on:** section-01 (data foundation — types, hooks, `clientPalette.ts`)
**Blocks:** section-06 (page composition)

---

## Files to Create

```
client/components/management/tasks/RecurrenceBuilder.tsx
client/components/management/tasks/TaskModal.tsx

client/app/dashboard/agent/marketing/management/tasks/__tests__/RecurrenceBuilder.test.tsx
client/app/dashboard/agent/marketing/management/tasks/__tests__/TaskModal.test.tsx
```

**Do NOT modify:**
- `client/components/agent/scheduling/RecurringTaskManager.tsx` — reference only; leave it untouched
- `client/components/ui/modal.tsx` — use as-is

---

## Background

`TaskModal.tsx` is the primary interface for creating and editing tasks. It is rendered at the page level (in `page.tsx`, not inside Kanban or List components) to avoid z-index stacking issues.

`RecurrenceBuilder.tsx` is a standalone component extracted from `RecurringTaskManager.tsx` (which lives at `client/components/agent/scheduling/RecurringTaskManager.tsx`). The existing `RecurringTaskManager` is the reference implementation — study it to understand the recurrence field names, day-toggle pattern, and end-condition logic. Do not copy it verbatim: `RecurrenceBuilder` is a controlled sub-component (receives all values via props, emits changes via callbacks) with two additional frequencies (`yearly`, `custom`) that `RecurringTaskManager` does not currently support.

### Key types (from `client/lib/types/scheduling.ts`)

```typescript
// Already complete — no additions needed
type RecurrenceFrequency = 'daily' | 'weekly' | 'biweekly' | 'monthly' | 'yearly' | 'custom';
type RecurrenceEndType = 'never' | 'date' | 'count';
type TaskPriority = 'low' | 'medium' | 'high';

// Full task shape — used in edit mode
type AgentGlobalTask  // (see scheduling.ts for all fields)
```

### Key hooks (from `client/lib/hooks/useScheduling.ts`)

```typescript
useCreateGlobalTask()   // returns mutation; use in create mode
useUpdateGlobalTask()   // returns mutation; use in edit mode
useTaskCategories(dept?: string)  // returns TaskCategoryItem[]
```

`useClients()` — check `client/lib/hooks/` for an existing hook. If none exists, create `client/lib/hooks/useClients.ts` that fetches `GET /api/clients/` and returns `Client[]` (minimum fields: `id: string`, `name: string`). Wrap in React Query `useQuery` with key `['clients']`.

### Modal primitives (from `client/components/ui/modal.tsx`)

These are the exact exports to use — do not create custom modal markup:

```typescript
Modal          // props: isOpen, onClose, children, size ('sm'|'md'|'lg'|'xl'|'full')
ModalHeader    // props: children, onClose?
ModalTitle     // props: children
ModalContent   // props: children, className? — scrollable, max-height capped
ModalFooter    // props: children — right-aligned action row
```

### Rich text editor

No TipTap, Quill, Slate, or Lexical is installed in `client/package.json`. Use a plain `<textarea>` for the description field and add a comment `{/* TODO: replace with rich text editor when installed */}`.

---

## Tests First

Write all tests before implementing the components. Run `cd client && npx vitest run` — tests must fail (red) before implementation, and pass (green) after.

### `RecurrenceBuilder.test.tsx`

```typescript
// Mock imports: none needed — this is a pure controlled component
// Render helper: provide all required props with sensible defaults

describe('RecurrenceBuilder', () => {
  it('renders frequency selector with all 6 options: Daily, Weekly, Biweekly, Monthly, Yearly, Custom')
  it('hides day-of-week checkboxes when frequency is Daily')
  it('hides day-of-week checkboxes when frequency is Monthly')
  it('hides day-of-week checkboxes when frequency is Yearly')
  it('shows day-of-week checkboxes when frequency is Weekly')
  it('shows day-of-week checkboxes when frequency is Custom')
  it('renders interval field with unit label "days" when frequency is Daily')
  it('renders interval field with unit label "weeks" when frequency is Weekly')
  it('renders end condition radio group with options: Never, After N occurrences, On date')
  it('shows number input when "After N occurrences" end condition is selected')
  it('shows date input when "On date" end condition is selected')
  it('shows neither extra input when "Never" end condition is selected')
  it('calls onChange callbacks with correct updated values when frequency changes')
  it('calls onChange callbacks with correct updated values when day-of-week checkbox toggled')
  it('calls onChange callbacks with correct updated values when end type changes')
})
```

### `TaskModal.test.tsx`

```typescript
// Mocks needed:
vi.mock('@/lib/hooks/useScheduling', () => ({
  useCreateGlobalTask: () => ({ mutateAsync: vi.fn().mockResolvedValue({}), isPending: false }),
  useUpdateGlobalTask: () => ({ mutateAsync: vi.fn().mockResolvedValue({}), isPending: false }),
  useTaskCategories: () => ({ data: [{ id: 'cat1', name: 'SEO', color: '#4F46E5' }] }),
}))
vi.mock('@/lib/hooks/useClients', () => ({
  useClients: () => ({ data: [{ id: 'c1', name: 'Acme Corp' }] }),
}))

describe('TaskModal — create mode', () => {
  it('renders section headings: Basic Info, Assignment, Scheduling, Recurrence')
  it('renders required fields: title input, priority toggle, client select, category select, due date input')
  it('recurrence section is hidden by default (toggle is off)')
  it('toggling the recurrence switch shows RecurrenceBuilder')
  it('title field is required — Save is disabled when title is empty')
  it('Save calls useCreateGlobalTask with only user-editable fields (no id, created_at, owner_id, is_overdue)')
  it('Cancel calls onClose without triggering any mutation')
  it('"Save & Schedule" saves the task AND shows toast "Calendar scheduling coming soon"')
  it('modal closes (onClose called) after successful save')
  it('modal stays open on save failure and shows error feedback')
})

describe('TaskModal — edit mode', () => {
  it('all fields are pre-populated with existing task values when task prop is provided')
  it('Save calls useUpdateGlobalTask (not useCreateGlobalTask) with correct id and updated fields')
  it('recurrence section is visible when task.is_recurring is true')
})
```

---

## Implementation: `RecurrenceBuilder.tsx`

**Location:** `client/components/management/tasks/RecurrenceBuilder.tsx`

### Props interface

```typescript
interface RecurrenceBuilderProps {
  frequency: RecurrenceFrequency;
  interval: number;
  daysOfWeek: number[];          // 0=Mon … 6=Sun (matches existing DAY_NAMES from scheduling.ts)
  endType: RecurrenceEndType;
  endDate: string;               // ISO date string or ''
  endCount: number | '';         // '' means not set
  onFrequencyChange: (v: RecurrenceFrequency) => void;
  onIntervalChange: (v: number) => void;
  onDaysOfWeekChange: (v: number[]) => void;
  onEndTypeChange: (v: RecurrenceEndType) => void;
  onEndDateChange: (v: string) => void;
  onEndCountChange: (v: number | '') => void;
}
```

### Frequency options (all 6)

```typescript
const FREQUENCY_OPTIONS = [
  { value: 'daily',    label: 'Daily' },
  { value: 'weekly',   label: 'Weekly' },
  { value: 'biweekly', label: 'Biweekly' },
  { value: 'monthly',  label: 'Monthly' },
  { value: 'yearly',   label: 'Yearly' },
  { value: 'custom',   label: 'Custom' },
];
```

### Interval unit label

Derive a unit label string from frequency for the "Every N [unit]" display:

```
daily    → 'days'
weekly   → 'weeks'
biweekly → 'weeks'
monthly  → 'months'
yearly   → 'years'
custom   → 'days'  (fallback)
```

### Day-of-week visibility

Show the day-of-week toggle buttons when `frequency === 'weekly' || frequency === 'custom'`. Import `DAY_NAMES` from `@/lib/types/scheduling` — it's the same array used by `RecurringTaskManager`. Use the same `DayToggle` pattern (individual toggle buttons, Mon–Sun).

### End condition

Render a radio group with three options:
- `never` → "Never" (no extra input)
- `count` → "After N occurrences" (reveals a number input)
- `date` → "On date" (reveals a `<input type="date">`)

### Styling

Follow the same pattern as `RecurringTaskManager`: `block text-xs font-medium text-secondary mb-1` labels, `space-y-4` container. Use `Input` from `@/components/ui/input` for number and date inputs. Use `Select` from `@/components/ui/select` for the frequency dropdown.

---

## Implementation: `TaskModal.tsx`

**Location:** `client/components/management/tasks/TaskModal.tsx`

### Props interface

```typescript
interface TaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task?: AgentGlobalTask;  // undefined → create mode; defined → edit mode
}
```

### Form state

Manage a single `formState` object with `useState`. Use a generic setter:

```typescript
function setField<K extends keyof FormState>(key: K, value: FormState[K]) {
  setFormState(prev => ({ ...prev, [key]: value }));
}
```

The `FormState` type contains **only user-editable fields**:

```typescript
interface FormState {
  title: string;
  description: string;
  priority: TaskPriority;
  client_id: string;
  category_id: string;
  due_date: string;
  scheduled_date: string;
  start_time: string;
  end_time: string;
  show_time: boolean;           // controls visibility of start/end time fields (not sent to API)
  is_recurring: boolean;
  recurrence_frequency: RecurrenceFrequency;
  recurrence_interval: number;
  recurrence_days_of_week: number[];
  recurrence_end_type: RecurrenceEndType;
  recurrence_end_date: string;
  recurrence_end_count: number | '';
}
```

Note: `show_time` is local UI state only — never include it in the API payload.

### Default form state (create mode)

```typescript
const DEFAULT_FORM: FormState = {
  title: '',
  description: '',
  priority: 'medium',
  client_id: '',
  category_id: '',
  due_date: '',
  scheduled_date: '',
  start_time: '',
  end_time: '',
  show_time: false,
  is_recurring: false,
  recurrence_frequency: 'weekly',
  recurrence_interval: 1,
  recurrence_days_of_week: [],
  recurrence_end_type: 'never',
  recurrence_end_date: '',
  recurrence_end_count: '',
};
```

### Initializing from an existing task (edit mode)

When `task` prop changes (and is defined), initialize `formState` from the task. Only map the user-editable fields. Do not spread the entire task object — read each field explicitly to avoid smuggling read-only fields into the payload.

### API payload construction

Build the payload from `formState` fields only. Never include `id`, `created_at`, `owner_id`, `is_overdue`, `order`, `client_name`, or any computed fields.

For recurrence fields: only include them in the payload when `formState.is_recurring === true`. When `is_recurring` is false, pass `is_recurring: false` and omit all `recurrence_*` keys (or set them to null — match what the existing hooks expect).

### Modal structure

Use `size="lg"` to accommodate all sections comfortably.

```tsx
<Modal isOpen={isOpen} onClose={onClose} size="lg">
  <form onSubmit={handleSubmit}>
    <ModalHeader onClose={onClose}>
      <ModalTitle>{task ? 'Edit Task' : 'New Task'}</ModalTitle>
    </ModalHeader>
    <ModalContent className="space-y-6">
      {/* Section: Basic Info */}
      {/* Section: Assignment */}
      {/* Section: Scheduling */}
      {/* Section: Recurrence */}
    </ModalContent>
    <ModalFooter>
      {/* Cancel | Save & Schedule | Save */}
    </ModalFooter>
  </form>
</Modal>
```

### Section headings

Each section uses a consistent heading style:
```tsx
<h3 className="text-xs font-semibold uppercase tracking-wider text-secondary border-b border-border pb-1 mb-3">
  Basic Info
</h3>
```

### Section: Basic Info

- **Title:** `<Input>` with `required`. Bind to `formState.title`.
- **Description:** `<textarea>` (no rich text editor installed — see note above). Rows: 3. Bind to `formState.description`.
- **Priority:** three-button toggle group (not a `<select>`). Render three `<button type="button">` elements for Low / Medium / High. Active button style: `bg-accent text-white`. Inactive style: `bg-surface border border-border text-secondary`. Include a colored dot indicator per button (blue for low, amber for medium, red for high).

### Section: Assignment

- **Client:** `<Select>` from `@/components/ui/select`. Populate from `useClients().data`. Options: `[{ value: '', label: 'No client' }, ...clients.map(c => ({ value: c.id, label: c.name }))]`. Bind to `formState.client_id`.
- **Category:** `<Select>`. Populate from `useTaskCategories().data`. Options: `[{ value: '', label: 'No category' }, ...categories.map(c => ({ value: c.id, label: c.name }))]`. Bind to `formState.category_id`.

### Section: Scheduling

- **Due date:** `<Input type="date">`. Bind to `formState.due_date`.
- **Scheduled date:** `<Input type="date">`. Optional — include a label "(optional)". Bind to `formState.scheduled_date`.
- **Time fields:** Hidden by default. Reveal with a `<button type="button">` labeled "＋ Add time" / "− Remove time" that toggles `formState.show_time`. When visible, show side-by-side start/end `<Input type="time">` fields. Only include `start_time` and `end_time` in the API payload when `show_time` is true and the values are non-empty.

### Section: Recurrence

- Render an `is_recurring` toggle. Use a `<button type="button">` styled as a switch (or a checkbox — keep it simple). When off, show only the toggle label "Repeat this task". When on, render `<RecurrenceBuilder>` with all recurrence fields from `formState` and corresponding `setField` callbacks.

### Footer actions

```tsx
<ModalFooter>
  <Button type="button" variant="ghost" size="sm" onClick={onClose}>
    Cancel
  </Button>
  <Button type="button" variant="secondary" size="sm" onClick={handleSaveAndSchedule}>
    Save & Schedule
  </Button>
  <Button
    type="submit"
    variant="primary"
    size="sm"
    disabled={!formState.title.trim() || isPending}
  >
    {isPending ? 'Saving...' : (task ? 'Save changes' : 'Create task')}
  </Button>
</ModalFooter>
```

### handleSubmit logic

```typescript
async function handleSubmit(e: React.FormEvent) {
  e.preventDefault();
  if (!formState.title.trim()) return;
  // Build payload from formState — user-editable fields only
  // Call createTask.mutateAsync(payload) or updateTask.mutateAsync({ id: task.id, data: payload })
  // On success: onClose()
  // On error: show toast.error('Failed to save task') — do NOT call onClose()
}
```

### handleSaveAndSchedule logic

```typescript
async function handleSaveAndSchedule() {
  if (!formState.title.trim()) return;
  // Same save logic as handleSubmit
  // On success: onClose() + toast.info('Calendar scheduling coming soon')
  // On error: same error handling as handleSubmit
}
```

### isPending state

```typescript
const isPending = createTask.isPending || updateTask.isPending;
```

---

## Edge Cases

**Empty title:** The Save button must be disabled when `formState.title.trim() === ''`. The `<Input required>` on the title field also provides browser-native validation as a secondary guard.

**Recurrence fields on save with `is_recurring: false`:** Do not include any `recurrence_*` fields in the payload when toggling off recurrence. Passing stale recurrence values could confuse the backend.

**Edit mode initialization timing:** Use a `useEffect` with `[task]` dependency to re-initialize the form when `task` prop changes. Guard against running when `task` is `undefined` (create mode keeps the default form).

**Category ID vs category_ref:** The existing `RecurringTaskManager` uses `task_category_ref` as the field name. Verify the actual field name in `AgentGlobalTask` and `useCreateGlobalTask`/`useUpdateGlobalTask` payload shape before implementing. Match what the hooks expect — do not assume.

**`useClients` hook:** If you have to create it from scratch, place it at `client/lib/hooks/useClients.ts`. Minimum implementation:

```typescript
// client/lib/hooks/useClients.ts
export function useClients() {
  return useQuery({
    queryKey: ['clients'],
    queryFn: () => apiClient.get<Client[]>('/api/clients/'),
    staleTime: 5 * 60 * 1000,
  });
}
```

Where `Client` is at minimum `{ id: string; name: string }`. Add more fields if the type already exists elsewhere in the codebase.

---

## Implementation Checklist

1. Write `RecurrenceBuilder.test.tsx` — run vitest, confirm all fail
2. Implement `RecurrenceBuilder.tsx` — run vitest, confirm all pass
3. Write `TaskModal.test.tsx` — run vitest, confirm all fail
4. Check for existing `useClients` hook; create `useClients.ts` if missing
5. Implement `TaskModal.tsx` — run vitest, confirm all pass
6. Refactor if needed; keep tests green
