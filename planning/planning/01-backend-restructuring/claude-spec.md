# Complete Specification: Split 01 — Backend Task Model & API Restructuring

## Overview

Refactor the Django backend to support a unified task system. This split is the foundation for all 5 subsequent splits — every frontend feature depends on its API shape.

**Key decisions from stakeholder interview:**
- Fresh/dev database → straightforward migration, no rollback complexity
- JIT always auto-creates next recurring instance (no agent prompt)
- Review is category-driven: categories with `requires_review=True` auto-intercept completion
- Clean API break: old recurring-task endpoints removed immediately
- Categories are department-filtered (agents only see their department + "both")
- ScheduledTaskLink simplified from GenericFK to direct FK
- Seed categories auto-created in data migration
- Celery periodic task generator removed entirely — JIT is sole mechanism

---

## 1. TaskCategory Model (NEW)

**File:** `server/api/models/agent_scheduling.py`

```
TaskCategory:
  id: UUID (primary key, default=uuid4)
  name: CharField (unique, max_length=100)
  slug: SlugField (auto-generated from name, unique)
  color: CharField (hex color, max_length=7, default='#2563EB')
  icon: CharField (optional, max_length=50, Lucide icon name)
  department: CharField (choices: marketing, developer, both; default='both')
  requires_review: BooleanField (default=False)
  is_active: BooleanField (default=True)
  sort_order: IntegerField (default=0)
  created_by: FK → User (nullable, on_delete=SET_NULL)
  created_at: DateTimeField (auto_now_add)
  updated_at: DateTimeField (auto_now)

  class Meta:
    ordering = ['sort_order', 'name']
    indexes: (is_active, department)
```

**Seed categories (auto-created in data migration):**
| Name | Slug | Department | Color | Requires Review |
|------|------|-----------|-------|-----------------|
| Design | design | both | #8B5CF6 | False |
| Copywriting | copywriting | marketing | #F59E0B | True |
| SEO Optimization | seo-optimization | marketing | #10B981 | False |
| QA Review | qa-review | developer | #EF4444 | True |
| Client Communication | client-communication | both | #3B82F6 | False |
| Administrative Ops | administrative-ops | both | #6B7280 | False |
| Content Creation | content-creation | marketing | #EC4899 | False |
| Strategy | strategy | marketing | #8B5CF6 | False |
| Research | research | both | #14B8A6 | False |
| Development | development | developer | #2563EB | False |
| DevOps | devops | developer | #F97316 | False |

---

## 2. AgentGlobalTask Model (MODIFIED)

**File:** `server/api/models/agent_scheduling.py` (lines 80-170 currently)

### New Fields to Add

```python
# Client tagging
client = models.ForeignKey('Client', null=True, blank=True, on_delete=models.SET_NULL, related_name='global_tasks')

# Category (replaces CharField task_category)
task_category_ref = models.ForeignKey('TaskCategory', null=True, blank=True, on_delete=models.SET_NULL, related_name='tasks')

# Recurrence fields (replaces RecurringTaskTemplate)
is_recurring = models.BooleanField(default=False)
recurrence_frequency = models.CharField(max_length=20, choices=RECURRENCE_FREQUENCY_CHOICES, null=True, blank=True)
recurrence_days = models.JSONField(null=True, blank=True, help_text='ISO weekday numbers, e.g. [1,3] for Mon/Wed')
recurrence_interval = models.IntegerField(null=True, blank=True, default=1, help_text='Every N units')
recurrence_end_type = models.CharField(max_length=10, choices=RECURRENCE_END_CHOICES, null=True, blank=True)
recurrence_end_count = models.IntegerField(null=True, blank=True)
recurrence_end_date = models.DateField(null=True, blank=True)
recurrence_parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='recurrence_children')
recurrence_instance_number = models.IntegerField(null=True, blank=True)
```

### Status Field Change

```python
class TaskStatus(models.TextChoices):
    TODO = 'todo', 'To Do'
    IN_PROGRESS = 'in_progress', 'In Progress'
    IN_REVIEW = 'in_review', 'In Review'  # NEW
    DONE = 'done', 'Done'
```

### Choice Constants

```python
RECURRENCE_FREQUENCY_CHOICES = [
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('biweekly', 'Biweekly'),
    ('monthly', 'Monthly'),
    ('yearly', 'Yearly'),
    ('custom', 'Custom'),
]

RECURRENCE_END_CHOICES = [
    ('never', 'Never'),
    ('count', 'After N occurrences'),
    ('date', 'On specific date'),
]
```

### New Indexes

```python
class Meta:
    indexes = [
        # Existing
        models.Index(fields=['agent', 'status']),
        models.Index(fields=['agent', 'scheduled_date']),
        # New
        models.Index(fields=['agent', 'client']),
        models.Index(fields=['task_category_ref', 'status']),
        models.Index(fields=['recurrence_parent']),
        models.Index(fields=['client', 'scheduled_date']),  # For Split 06 reporting
    ]
```

---

## 3. ScheduledTaskLink Simplification

**Current:** Uses ContentType + GenericForeignKey to link to any task type.

**Change:** Replace with direct FK to AgentGlobalTask:

```python
class ScheduledTaskLink(models.Model):
    time_block = models.ForeignKey('AgentTimeBlock', on_delete=models.CASCADE, related_name='task_links')
    task = models.ForeignKey('AgentGlobalTask', on_delete=models.CASCADE, related_name='time_block_links')
    # Remove: content_type, object_id, content_object (GenericFK)
```

---

## 4. RecurringTaskTemplate Deprecation

**Strategy:** Since database is fresh/dev, do a clean migration:

1. **Migration A (schema):** Add all new fields to AgentGlobalTask as nullable
2. **Migration B (data):** Convert existing RecurringTaskTemplate records into AgentGlobalTask records with `is_recurring=True`, seed TaskCategory records
3. **Migration C (schema):** Add indexes, enforce any non-null constraints needed
4. **Migration D (cleanup):** Remove RecurringTaskTemplate model, remove old `task_category` CharField from AgentGlobalTask, remove GenericFK fields from ScheduledTaskLink

All 4 migrations ship in same deploy (fresh DB makes this safe).

### Data Migration Logic (Migration B)

```python
def migrate_recurring_templates(apps, schema_editor):
    RecurringTaskTemplate = apps.get_model('api', 'RecurringTaskTemplate')
    AgentGlobalTask = apps.get_model('api', 'AgentGlobalTask')

    for template in RecurringTaskTemplate.objects.filter(is_active=True, target_type='global'):
        AgentGlobalTask.objects.create(
            agent=template.agent,
            title=template.title,
            description=template.description,
            priority=template.priority,
            client=template.client,
            is_recurring=True,
            recurrence_frequency=_map_recurrence_type(template.recurrence_type),
            recurrence_days=template.days_of_week,
            recurrence_interval=1,
            recurrence_end_type='date' if template.effective_until else 'never',
            recurrence_end_date=template.effective_until,
            status='todo',
            scheduled_date=_calculate_next_date(template),
        )

def migrate_task_categories(apps, schema_editor):
    # Map old CharField values to new TaskCategory FK
    TaskCategory = apps.get_model('api', 'TaskCategory')
    AgentGlobalTask = apps.get_model('api', 'AgentGlobalTask')

    # Create seed categories first (see table in section 1)
    # Then update existing tasks to link to new categories
    category_map = {}
    for old_value, new_slug in OLD_TO_NEW_CATEGORY_MAP.items():
        cat = TaskCategory.objects.filter(slug=new_slug).first()
        if cat:
            category_map[old_value] = cat

    for task in AgentGlobalTask.objects.exclude(task_category='').exclude(task_category__isnull=True):
        if task.task_category in category_map:
            task.task_category_ref = category_map[task.task_category]
            task.save(update_fields=['task_category_ref'])
```

### Old-to-New Category Mapping

```python
OLD_TO_NEW_CATEGORY_MAP = {
    'admin': 'administrative-ops',
    'strategy': 'strategy',
    'creative': 'design',
    'analytical': 'research',
    'communication': 'client-communication',
    'professional_development': 'research',
    'internal': 'administrative-ops',
    'planning': 'strategy',
    'research': 'research',
    'coding': 'development',
    'review': 'qa-review',
    'devops': 'devops',
    'content_creation': 'content-creation',
}
```

---

## 5. JIT Recurring Task Generation

### Trigger Point

When `AgentGlobalTask.status` transitions to `done` (or `in_review` for review-required categories):

```python
def complete_task(task):
    # Check if category requires review
    if task.task_category_ref and task.task_category_ref.requires_review:
        if task.status != 'in_review':
            task.status = 'in_review'
            task.save()
            return task, None  # No JIT yet — JIT fires when admin approves (sets done)

    task.status = 'done'
    task.completed_at = timezone.now()
    task.save()

    next_task = None
    if task.is_recurring:
        next_task = generate_next_recurring_instance(task)

    return task, next_task
```

### Next Instance Calculation

Use `dateutil.rrule` for computing next occurrence:

```python
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY, MO, TU, WE, TH, FR, SA, SU

WEEKDAY_MAP = {1: MO, 2: TU, 3: WE, 4: TH, 5: FR, 6: SA, 7: SU}
FREQ_MAP = {'daily': DAILY, 'weekly': WEEKLY, 'monthly': MONTHLY, 'yearly': YEARLY, 'biweekly': WEEKLY, 'custom': WEEKLY}

def calculate_next_date(task):
    freq = FREQ_MAP.get(task.recurrence_frequency, WEEKLY)
    interval = task.recurrence_interval or 1
    if task.recurrence_frequency == 'biweekly':
        interval = 2

    kwargs = {'freq': freq, 'interval': interval, 'dtstart': task.scheduled_date, 'count': 2}
    if task.recurrence_days:
        kwargs['byweekday'] = [WEEKDAY_MAP[d] for d in task.recurrence_days]

    rule = rrule(**kwargs)
    next_date = rule.after(task.scheduled_date)

    # Check end conditions
    if task.recurrence_end_type == 'date' and next_date and next_date.date() > task.recurrence_end_date:
        return None
    if task.recurrence_end_type == 'count' and task.recurrence_instance_number >= task.recurrence_end_count:
        return None

    return next_date
```

### Generated Instance Fields

```python
def generate_next_recurring_instance(completed_task):
    next_date = calculate_next_date(completed_task)
    if not next_date:
        return None

    parent = completed_task.recurrence_parent or completed_task
    instance_num = (completed_task.recurrence_instance_number or 1) + 1

    return AgentGlobalTask.objects.create(
        agent=completed_task.agent,
        title=completed_task.title,
        description=completed_task.description,
        priority=completed_task.priority,
        client=completed_task.client,
        task_category_ref=completed_task.task_category_ref,
        is_recurring=True,
        recurrence_frequency=completed_task.recurrence_frequency,
        recurrence_days=completed_task.recurrence_days,
        recurrence_interval=completed_task.recurrence_interval,
        recurrence_end_type=completed_task.recurrence_end_type,
        recurrence_end_count=completed_task.recurrence_end_count,
        recurrence_end_date=completed_task.recurrence_end_date,
        recurrence_parent=parent,
        recurrence_instance_number=instance_num,
        scheduled_date=next_date,
        estimated_minutes=completed_task.estimated_minutes,
        status='todo',
    )
```

---

## 6. Review-Required Category Flow

### Status Transition Rules

```
Normal category:      todo → in_progress → done
Review category:      todo → in_progress → in_review → done
                                              ↓
                                          (rejected) → in_progress
```

### Backend Enforcement

When a task's status is set to `done`:
1. Check `task.task_category_ref.requires_review`
2. If True AND current status is NOT `in_review` → override status to `in_review`
3. If True AND current status IS `in_review` → allow `done` (admin is approving)
4. JIT recurring generation fires only when status actually reaches `done`

### Serializer Validation

```python
def validate_status(self, value):
    if value == 'done' and self.instance:
        cat = self.instance.task_category_ref
        if cat and cat.requires_review and self.instance.status != 'in_review':
            return 'in_review'  # Intercept: auto-redirect to review
    return value
```

---

## 7. API Endpoints

### TaskCategory Endpoints (NEW)

| Method | URL | Permission | Description |
|--------|-----|-----------|-------------|
| GET | `/agent/schedule/task-categories/` | IsAuthenticated, IsAnyAgent | List active categories filtered by agent's department |
| GET | `/admin/task-categories/` | IsAuthenticated, IsAdmin | List ALL categories (including inactive) |
| POST | `/admin/task-categories/` | IsAuthenticated, IsAdmin | Create category |
| PATCH | `/admin/task-categories/{id}/` | IsAuthenticated, IsAdmin | Update category |
| DELETE | `/admin/task-categories/{id}/` | IsAuthenticated, IsAdmin | Soft-delete (set is_active=False) |

### AgentGlobalTask Endpoints (MODIFIED)

| Method | URL | Permission | Changes |
|--------|-----|-----------|---------|
| GET | `/agent/schedule/global-tasks/` | IsAnyAgent | New filters: `?client={id}`, `?task_category_id={id}`, `?is_recurring=true` |
| POST | `/agent/schedule/global-tasks/` | IsAnyAgent | Accepts new fields: client, task_category_id, recurrence_* |
| PATCH | `/agent/schedule/global-tasks/{id}/` | IsAnyAgent | Status validation with review-required interception |
| POST | `/agent/schedule/global-tasks/{id}/complete/` | IsAnyAgent | NEW: dedicated completion endpoint, triggers JIT + review interception |

### Removed Endpoints

| URL | Reason |
|-----|--------|
| `/agent/schedule/recurring-tasks/` | Merged into global-tasks with recurrence fields |
| All RecurringTaskTemplate CRUD | Replaced by is_recurring flag on AgentGlobalTask |

---

## 8. Serializers

### TaskCategorySerializer

```python
class TaskCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskCategory
        fields = ['id', 'name', 'slug', 'color', 'icon', 'department', 'requires_review', 'is_active', 'sort_order']
        read_only_fields = ['id', 'slug']
```

### AgentGlobalTaskReadSerializer

```python
class AgentGlobalTaskReadSerializer(serializers.ModelSerializer):
    task_category_detail = TaskCategorySerializer(source='task_category_ref', read_only=True)
    client_name = serializers.CharField(source='client.name', default='', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    time_block_title = serializers.CharField(source='time_block.title', default='', read_only=True)

    class Meta:
        model = AgentGlobalTask
        fields = [
            'id', 'agent', 'title', 'description', 'status', 'priority',
            'client', 'client_name', 'task_category_ref', 'task_category_detail',
            'due_date', 'scheduled_date', 'time_block', 'time_block_title',
            'estimated_minutes', 'start_time', 'end_time',
            'is_recurring', 'recurrence_frequency', 'recurrence_days', 'recurrence_interval',
            'recurrence_end_type', 'recurrence_end_count', 'recurrence_end_date',
            'recurrence_parent', 'recurrence_instance_number',
            'order', 'completed_at', 'created_at', 'updated_at',
            'is_overdue',
        ]
```

### AgentGlobalTaskWriteSerializer

```python
class AgentGlobalTaskWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentGlobalTask
        fields = [
            'title', 'description', 'status', 'priority',
            'client', 'task_category_ref',
            'due_date', 'scheduled_date', 'time_block',
            'estimated_minutes', 'start_time', 'end_time',
            'is_recurring', 'recurrence_frequency', 'recurrence_days', 'recurrence_interval',
            'recurrence_end_type', 'recurrence_end_count', 'recurrence_end_date',
            'order',
        ]

    def validate_status(self, value):
        # Review-required interception logic
        ...

    def validate(self, data):
        # If is_recurring=True, require recurrence_frequency
        # If recurrence_end_type='count', require recurrence_end_count
        # If recurrence_end_type='date', require recurrence_end_date
        ...
```

---

## 9. Permissions

### IsAdmin Permission Class (NEW)

```python
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
```

**File:** `server/api/permissions.py` (or wherever IsAnyAgent lives)

---

## 10. Celery Task Cleanup

### Remove
- `generate_recurring_tasks()` from `server/api/tasks/scheduling_tasks.py`
- Its Celery Beat schedule entry

### Keep
- `generate_recurring_time_blocks()` — still needed for AgentRecurringBlock → AgentTimeBlock generation

---

## 11. Frontend Type Updates

**File:** `client/lib/types/scheduling.ts`

```typescript
export type GlobalTaskStatus = 'todo' | 'in_progress' | 'in_review' | 'done';

export interface TaskCategoryItem {
  id: string;
  name: string;
  slug: string;
  color: string;
  icon: string | null;
  department: 'marketing' | 'developer' | 'both';
  requires_review: boolean;
  is_active: boolean;
  sort_order: number;
}

export interface AgentGlobalTask {
  id: string;
  agent: string;
  title: string;
  description: string;
  status: GlobalTaskStatus;
  priority: 'low' | 'medium' | 'high';
  client: string | null;
  client_name: string;
  task_category_ref: string | null;
  task_category_detail: TaskCategoryItem | null;
  due_date: string | null;
  scheduled_date: string | null;
  time_block: string | null;
  time_block_title: string;
  estimated_minutes: number | null;
  start_time: string | null;
  end_time: string | null;
  is_recurring: boolean;
  recurrence_frequency: 'daily' | 'weekly' | 'biweekly' | 'monthly' | 'yearly' | 'custom' | null;
  recurrence_days: number[] | null;
  recurrence_interval: number | null;
  recurrence_end_type: 'never' | 'count' | 'date' | null;
  recurrence_end_count: number | null;
  recurrence_end_date: string | null;
  recurrence_parent: string | null;
  recurrence_instance_number: number | null;
  order: number;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  is_overdue: boolean;
}

// Remove: RecurringTaskTemplate interface
// Remove: old TaskCategory union type
```

---

## 12. Frontend API Updates

**File:** `client/lib/api/scheduling.ts`

### New Methods
```typescript
getTaskCategories(department?: string): Promise<TaskCategoryItem[]>
createTaskCategory(data: CreateTaskCategoryRequest): Promise<TaskCategoryItem>  // admin
updateTaskCategory(id: string, data: Partial<TaskCategoryItem>): Promise<TaskCategoryItem>  // admin
deleteTaskCategory(id: string): Promise<void>  // admin (soft delete)
completeGlobalTask(id: string): Promise<{ task: AgentGlobalTask; next_task: AgentGlobalTask | null }>
```

### Modified Methods
```typescript
getGlobalTasks(params?: { client?: string; task_category_id?: string; is_recurring?: boolean; ...existing }): Promise<AgentGlobalTask[]>
createGlobalTask(data: CreateGlobalTaskRequest): Promise<AgentGlobalTask>  // add new fields
updateGlobalTask(id: string, data: UpdateGlobalTaskRequest): Promise<AgentGlobalTask>  // add new fields
```

### Removed Methods
```typescript
// DELETE: getRecurringTasks(), createRecurringTask(), updateRecurringTask(), deleteRecurringTask()
```

---

## 13. ViewSet Changes

### AgentGlobalTaskViewSet

- Add `get_serializer_class()` to return Read vs Write serializer based on action
- Add `get_queryset()` with `select_related('client', 'task_category_ref')` for performance
- Add new filters: `client`, `task_category_id`, `is_recurring`
- Add `@action(detail=True, methods=['post'])` for `complete` endpoint
- Remove RecurringTaskTemplateViewSet and its router registration

### TaskCategoryViewSet (NEW)

- Agent-facing: list only, filtered by department
- Admin-facing: full CRUD with IsAdmin permission

---

## Acceptance Criteria

1. `TaskCategory` model exists with seed data auto-created in migration
2. `AgentGlobalTask` has all new fields (client, task_category_ref, recurrence_*, status includes in_review)
3. `ScheduledTaskLink` uses direct FK instead of GenericFK
4. `RecurringTaskTemplate` model removed
5. Old `task_category` CharField removed from AgentGlobalTask
6. Existing tasks survive migration with category mapping
7. JIT recurring task generation works via `/complete/` endpoint
8. Review-required categories auto-intercept completion → set `in_review`
9. Category API: agents see department-filtered list; admins have full CRUD
10. IsAdmin permission class exists and protects admin endpoints
11. Celery `generate_recurring_tasks` removed; `generate_recurring_time_blocks` preserved
12. Frontend types updated to match new API shape
13. Frontend API wrapper updated with new/modified/removed methods
14. All existing functionality (create, update, list, filter) still works
