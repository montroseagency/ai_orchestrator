# Research Findings: Backend Task Model Restructuring

## Part 1: Codebase Analysis

### 1.1 AgentGlobalTask Model

**File:** `server/api/models/agent_scheduling.py` (lines 80-170)

Current fields:
- `id` (UUID PK), `agent` (FK→Agent), `title`, `description`
- `status` (TextChoices: todo, in_progress, done)
- `priority` (TextChoices: low, medium, high)
- `task_category` (CharField with TASK_CATEGORY_CHOICES — hardcoded list)
- `due_date`, `scheduled_date`, `time_block` (FK→AgentTimeBlock)
- `estimated_minutes`, `start_time`, `end_time` (added in migration 0069)
- `recurring_source` (FK→RecurringTaskTemplate, SET_NULL)
- `order`, `completed_at`, `created_at`, `updated_at`

**Meta:** ordering=['order', '-created_at'], indexes on (agent, status), (agent, scheduled_date), (agent, task_category)

**Key:** No client FK exists currently. The `task_category` is a CharField with choices, NOT a separate model.

### 1.2 RecurringTaskTemplate Model

**File:** `server/api/models/agent_scheduling.py` (lines 291-364)

Current fields:
- `id` (UUID PK), `agent` (FK→Agent), `title`, `description`, `priority`, `task_category`, `estimated_minutes`
- `target_type` (global, marketing_task, project_task)
- `client` (FK→Client, nullable) — **already has client FK!**
- `apply_to_all_clients` (BooleanField)
- `recurrence_type` (daily, weekly, biweekly, monthly)
- `days_of_week` (JSONField), `day_of_month` (IntegerField)
- `create_ahead_days` (IntegerField, default=1)
- `effective_from`, `effective_until` (DateFields)
- `is_active`, `last_generated_date`

**Important:** RecurringTaskTemplate already has more recurrence sophistication than the spec assumes. It supports `apply_to_all_clients` and `target_type` for generating different task types.

### 1.3 TaskCategory Choices (Hardcoded)

```python
TASK_CATEGORY_CHOICES = [
    ('admin', 'Admin'), ('strategy', 'Strategy'), ('creative', 'Creative'),
    ('analytical', 'Analytical'), ('communication', 'Communication'),
    ('professional_development', 'Professional Development'), ('internal', 'Internal'),
    ('planning', 'Planning'), ('research', 'Research'),
    ('coding', 'Coding'), ('review', 'Code Review'), ('devops', 'DevOps'),
    ('content_creation', 'Content Creation'),
]
```

Used by: AgentGlobalTask, RecurringTaskTemplate, MarketingTask, ProjectTask

### 1.4 Serializers

**File:** `server/api/serializers/agent_scheduling.py`

`AgentGlobalTaskSerializer`:
- Fields: all model fields + computed `is_overdue`, `time_block_title`
- Read-only: id, agent, completed_at, created_at, updated_at
- Auto-sets agent from request.user.agent_profile
- Auto-sets completed_at on status='done'

`RecurringTaskTemplateSerializer`:
- Fields: all model fields + computed `client_name`
- Read-only: id, agent, last_generated_date, created_at, updated_at

### 1.5 ViewSets & Endpoints

**File:** `server/api/views/agent/scheduling_views.py`

- `AgentGlobalTaskViewSet` — standard CRUD, filters: status, task_category, scheduled_date, due_before, priority
- `RecurringTaskTemplateViewSet` — CRUD + custom `generate-now` action
- `command_center` view — aggregated daily dashboard
- `cross_client_tasks` view — unified cross-client task list

Permission: `[IsAuthenticated, IsAnyAgent]` on all scheduling endpoints.

### 1.6 Celery Tasks

**File:** `server/api/tasks/scheduling_tasks.py`

Two scheduled tasks:
1. `generate_recurring_time_blocks()` — generates AgentTimeBlock from AgentRecurringBlock templates (7-day lookahead)
2. `generate_recurring_tasks()` — generates tasks from RecurringTaskTemplate (pull model, periodic execution)

Helper: `_should_generate_on_date(template, target_date)` handles daily/weekly/biweekly/monthly patterns.

**Current generation is PULL-based (Celery Beat periodic), not JIT.** The spec requires switching to JIT (generate on completion).

### 1.7 Client Model

**File:** `server/api/models/clients.py`

Key fields: `id` (UUID), `name`, `email`, `company`, `status`, `marketing_agent` (FK→Agent), `website_agent` (FK→Agent)

Related tasks via: `marketing_tasks` (MarketingTask), `website_projects` → `tasks` (ProjectTask)

### 1.8 User Roles & Permissions

User roles: admin, client, agent. Agent has `department` field (marketing, Website Development).

`IsAnyAgent` permission class checks `request.user.role == 'agent'` and `hasattr(request.user, 'agent_profile')`.

**No admin-specific API permission class exists yet.** Will need `IsAdmin` or `IsAdminUser` for category management endpoints.

### 1.9 Testing

- **Framework:** Django TestCase
- **Current state:** `server/api/tests.py` is empty (only imports)
- **No existing scheduling tests**
- Run with: `python manage.py test api`

### 1.10 Migration History

- `0066_agent_scheduling.py` (Mar 21) — Initial scheduling models
- `0067_add_task_category.py` (Mar 21) — Added task_category field
- `0069_...start_time_end_time.py` (Mar 24) — Added start_time/end_time to AgentGlobalTask

### 1.11 Signals

- `auto_assign_agent_to_client` (post_save on Client) — auto-assigns agents to new clients
- `auto_set_phase_timestamps` (pre_save on WebsiteProjectPhase) — manages phase dates
- **No task-related signals currently.**

### 1.12 Key Architecture Notes

- Scheduling is **agent-centric** (all models have agent FK)
- `ScheduledTaskLink` uses **GenericForeignKey** for cross-task-type linking
- Marketing/website agent distinction at view layer via `_get_agent_client_ids(agent)`
- Scheduling models NOT registered in Django admin

---

## Part 2: Best Practices Research

### 2.1 Django Recurring Task Patterns

**Recommended approach: Hybrid (store rules + JIT generation)**

Store recurrence metadata as discrete fields on the model (not opaque RRULE strings) for queryability. Use `dateutil.rrule` for computing next occurrences.

**Recommended fields:**
- `frequency` (DAILY, WEEKLY, MONTHLY, YEARLY)
- `interval` (every N units)
- `by_weekday` (JSONField, ISO weekday numbers)
- `count` or `until` (mutually exclusive end conditions)
- `dtstart` (first occurrence)

**JIT pattern for task completion:**
```python
from dateutil.rrule import rrule, WEEKLY
rule = rrule(freq=WEEKLY, interval=1, byweekday=[MO, WE], dtstart=start_date)
next_date = rule.after(completed_instance.scheduled_date)
```

**Key insight:** Since tasks need per-instance state (completed, notes, etc.), generate concrete instances. JIT on completion is ideal — create next instance when current one is marked done.

**Pitfalls:** Always handle timezone-aware datetimes. `count` and `until` are mutually exclusive. Use `apps.get_model()` in migrations.

### 2.2 DRF Nested Serializer Best Practices

**Recommendation: Separate read/write serializers**

```python
class TaskReadSerializer(ModelSerializer):
    category = CategorySerializer(read_only=True)  # nested for GET

class TaskWriteSerializer(ModelSerializer):
    category = PrimaryKeyRelatedField(queryset=...)  # PK for POST/PATCH

class TaskViewSet(ModelViewSet):
    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return TaskWriteSerializer
        return TaskReadSerializer
```

**Performance:** Always use `select_related` for FKs and `prefetch_related` for reverse FKs in `get_queryset()`. Read-only ModelSerializer is ~40% faster than writable.

**Alternative:** `to_representation` override for simple cases, but separate serializers are better for API schema clarity.

### 2.3 Django Data Migration Strategies

**Three-step pattern for merging RecurringTaskTemplate → AgentGlobalTask:**

1. **Migration A (schema):** Add all new fields to AgentGlobalTask as **nullable**
2. **Migration B (data):** `RunPython` to copy data from RecurringTaskTemplate into AgentGlobalTask. Use `apps.get_model()`, provide reverse function, batch large updates.
3. **Migration C (schema):** Add defaults/constraints on fields that need them

**Then in a later deploy:**
4. **Migration D (schema):** `DeleteModel('RecurringTaskTemplate')` — only after all code references removed

**Critical rules:**
- Never combine DDL and DML in one migration
- Always use `apps.get_model()` in RunPython (not direct imports)
- Always provide reverse functions
- Review SQL before production: `python manage.py sqlmigrate`
- Back up database before data migrations

**Sources:**
- Loopwerk: Safe Django Migrations (2025)
- Vinta Software: Dos and Don'ts for Django Migrations
- Django Official: Writing Migrations
- Haki Benita: DRF Performance
- dateutil.rrule Documentation
