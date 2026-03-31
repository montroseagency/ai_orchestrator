Now I have all the context I need. Let me check the latest migration number to know what the new migrations should be numbered.

The latest migration is `0053`. So the four new migrations will be `0054`, `0055`, `0056`, `0057`.

Now I have everything needed to write the section.

# Section 4: Django Migrations

## Overview

This section creates four sequential Django migrations that codify the model changes from sections 1-3 into the database schema. All four migrations ship in one deploy. The database is fresh/development, so there is no production data migration risk.

**Dependencies:** Sections 1 (TaskCategory model), 2 (AgentGlobalTask changes), and 3 (ScheduledTaskLink simplification) must be completed first -- the model code must exist before generating migrations.

**Blocks:** Sections 5, 6, 7, and 8 all depend on these migrations being applied.

**Files to create:**
- `/home/ubuntu/Montrroase_website/server/api/migrations/0054_task_restructure_schema.py` (Migration A)
- `/home/ubuntu/Montrroase_website/server/api/migrations/0055_task_restructure_data.py` (Migration B)
- `/home/ubuntu/Montrroase_website/server/api/migrations/0056_task_restructure_indexes.py` (Migration C)
- `/home/ubuntu/Montrroase_website/server/api/migrations/0057_task_restructure_cleanup.py` (Migration D)

**Files to modify:**
- `/home/ubuntu/Montrroase_website/server/api/models/agent_scheduling.py` (model code must already reflect sections 1-3)

The latest existing migration is `0053_contentidea_ai_generated_sections_and_more.py`, so the new migrations start at `0054`.

---

## Tests

Write tests in `/home/ubuntu/Montrroase_website/server/api/tests/test_migrations.py` (or `server/api/tests.py` if that is the established location). Use `django.test.TestCase`.

```python
class MigrationTests(TestCase):
    """Test that all four migrations apply and reverse correctly."""

    # Test: All migrations apply cleanly on a fresh database (migrate from zero)
    # Verify by calling: management.call_command('migrate', 'api', verbosity=0)
    # This implicitly tests Migration A, B, C, D in sequence.

    # Test: All migrations have reverse functions (migrate backward)
    # Verify by calling: management.call_command('migrate', 'api', '0053', verbosity=0)
    # Then re-apply: management.call_command('migrate', 'api', verbosity=0)

    # Test: After Migration B, 11 seed TaskCategory records exist
    # Query TaskCategory.objects.count() == 11

    # Test: After Migration B, seed categories have correct department assignments
    # Verify 'copywriting' has department='marketing', 'design' has department='both', etc.

    # Test: After Migration B, Copywriting and QA Review have requires_review=True
    # All other seed categories have requires_review=False

    # Test: After Migration B, any existing RecurringTaskTemplate records
    #   with target_type='global' and is_active=True are converted to
    #   AgentGlobalTask with is_recurring=True

    # Test: After Migration D, RecurringTaskTemplate model no longer exists
    #   in the schema (apps.get_model('api', 'RecurringTaskTemplate') raises LookupError)

    # Test: After Migration D, old task_category CharField is removed from AgentGlobalTask
    #   Verify the field is not in AgentGlobalTask._meta.get_fields()

    # Test: After Migration D, recurring_source FK is removed from
    #   both AgentGlobalTask and AgentTimeBlock
```

**Note on testing migrations:** Django does not natively support testing individual migrations in isolation easily. The recommended approach is:

1. Test that the full migration chain applies without errors using `call_command('migrate')`.
2. Test that reverse migrations work using `call_command('migrate', 'api', '0053')`.
3. After all migrations are applied, test that seed data exists and model fields are as expected by querying the ORM.
4. For RecurringTaskTemplate conversion, create template records in a `setUp`, apply migrations, and verify converted records exist.

Since the database is fresh, the most practical tests verify post-migration state: seed data presence, field existence, and model removal.

---

## Migration A: Schema Additions (`0054_task_restructure_schema.py`)

**Depends on:** `('api', '0053_contentidea_ai_generated_sections_and_more')`

This migration handles all structural schema changes. It must be generated after model code from sections 1-3 is in place. You can use `python manage.py makemigrations` and then split the auto-generated migration, or write it by hand.

### Operations

1. **Create `TaskCategory` model** with all fields:
   - `id` (UUIDField, primary key, default=uuid.uuid4)
   - `name` (CharField, max_length=100, unique=True)
   - `slug` (SlugField, unique=True)
   - `color` (CharField, max_length=7, default='#2563EB')
   - `icon` (CharField, max_length=50, blank=True)
   - `department` (CharField, max_length=20, choices: marketing/website/both)
   - `requires_review` (BooleanField, default=False)
   - `is_active` (BooleanField, default=True)
   - `sort_order` (IntegerField, default=0)
   - `created_by` (FK to User, null=True, blank=True, on_delete=SET_NULL)
   - `created_at` (DateTimeField)
   - `updated_at` (DateTimeField, auto_now=True)
   - Index on `(is_active, department)`
   - Ordering: `['sort_order', 'name']`

2. **Add fields to `AgentGlobalTask`** (all nullable to allow the migration to apply on existing rows):
   - `client` (FK to Client, null=True, blank=True, on_delete=SET_NULL, related_name='global_tasks')
   - `task_category_ref` (FK to TaskCategory, null=True, blank=True, on_delete=SET_NULL)
   - `is_recurring` (BooleanField, default=False)
   - `recurrence_frequency` (CharField, max_length=20, null=True, blank=True, choices: daily/weekly/biweekly/monthly/yearly/custom)
   - `recurrence_days` (JSONField, null=True, blank=True)
   - `recurrence_interval` (IntegerField, null=True, blank=True, default=1)
   - `recurrence_end_type` (CharField, max_length=10, null=True, blank=True, choices: never/count/date)
   - `recurrence_end_count` (IntegerField, null=True, blank=True)
   - `recurrence_end_date` (DateField, null=True, blank=True)
   - `recurrence_parent` (self FK, null=True, blank=True, on_delete=SET_NULL)
   - `recurrence_instance_number` (IntegerField, null=True, blank=True)

3. **Update `AgentGlobalTask.Status` choices** to include `IN_REVIEW = 'in_review'`. This is a model-level change; the `AlterField` operation updates the choices on the `status` field.

4. **Modify `ScheduledTaskLink`:**
   - Remove `content_type` FK field
   - Remove `object_id` UUIDField
   - (The `GenericForeignKey` attribute is not a database column -- it is removed from the model code, not the migration)
   - Add `task` FK to AgentGlobalTask (null=True, blank=True, on_delete=SET_NULL)
   - Update `unique_together` from `['content_type', 'object_id', 'agent']` to `['task', 'agent']`

### Important ordering within Migration A

The `content_type` and `object_id` fields must be removed and `unique_together` must be altered in the correct order. The safest sequence:

1. `AlterUniqueTogether` on ScheduledTaskLink to remove the old constraint (set to empty `set()`)
2. `RemoveField` for `content_type`
3. `RemoveField` for `object_id`
4. `AddField` for the new `task` FK
5. `AlterUniqueTogether` to set the new constraint `{('task', 'agent')}`

### Reverse function

For reversibility, the reverse operations are handled automatically by Django's `migrations.CreateModel`, `AddField`, `RemoveField`, etc. -- they have built-in reverse operations. No custom `RunPython` in this migration.

---

## Migration B: Data Population (`0055_task_restructure_data.py`)

**Depends on:** `('api', '0054_task_restructure_schema')`

This is a `RunPython` data migration with two forward functions and their reverses.

### Operation 1: Seed TaskCategory records

Create the 11 default categories. The full seed data table:

| Name | Slug | Department | Color | requires_review | sort_order |
|------|------|-----------|-------|-----------------|------------|
| Design | design | both | #8B5CF6 | False | 0 |
| Copywriting | copywriting | marketing | #F59E0B | True | 1 |
| SEO Optimization | seo-optimization | marketing | #10B981 | False | 2 |
| QA Review | qa-review | developer | #EF4444 | True | 3 |
| Client Communication | client-communication | both | #3B82F6 | False | 4 |
| Administrative Ops | administrative-ops | both | #6B7280 | False | 5 |
| Content Creation | content-creation | marketing | #EC4899 | False | 6 |
| Strategy | strategy | marketing | #8B5CF6 | False | 7 |
| Research | research | both | #14B8A6 | False | 8 |
| Development | development | developer | #2563EB | False | 9 |
| DevOps | devops | developer | #F97316 | False | 10 |

The forward function uses `apps.get_model('api', 'TaskCategory')` (never direct model imports). Use `get_or_create` keyed on `slug` to make the migration idempotent.

The reverse function deletes seed categories by their known slugs.

### Operation 2: Map old task_category CharField values to new task_category_ref FK

The mapping from old CharField values to new TaskCategory slugs:

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

The forward function:
1. Build a dictionary mapping slug to TaskCategory instance
2. Iterate over `AgentGlobalTask.objects.exclude(task_category='').exclude(task_category__isnull=True)`
3. Look up the matching slug via `OLD_TO_NEW_CATEGORY_MAP`
4. Set `task.task_category_ref` to the resolved category and save

The reverse function sets `task_category_ref` back to None for all tasks (since the reverse of the category mapping is lossy, this is acceptable for a dev database).

### Operation 3: Convert RecurringTaskTemplate records to AgentGlobalTask

Only convert templates where `target_type='global'` and `is_active=True`. Templates targeting `marketing_task` or `project_task` are intentionally skipped (those models are deprecated in later splits).

The forward function:
1. Get `RecurringTaskTemplate` and `AgentGlobalTask` via `apps.get_model()`
2. For each qualifying template, create an `AgentGlobalTask` with:
   - Copy `agent`, `title`, `description`, `priority`, `client`
   - Set `is_recurring=True`
   - Map `recurrence_type` to `recurrence_frequency` (daily->daily, weekly->weekly, biweekly->biweekly, monthly->monthly)
   - Set `recurrence_days` from `template.days_of_week`
   - Set `recurrence_interval=1`
   - Set `recurrence_end_type='date'` if `effective_until` exists, else `'never'`
   - Set `recurrence_end_date` from `effective_until`
   - Set `status='todo'`
   - Set `scheduled_date` using a simple next-date calculation (use `datetime.date.today()` as fallback -- full `dateutil.rrule` logic is not available in migrations without importing it, so a simple calculation is acceptable here)

The reverse function deletes any `AgentGlobalTask` records where `is_recurring=True` and `recurrence_parent` is None (i.e., the converted templates, not JIT-generated instances). This is safe because the database is fresh.

### Operation 4: Populate ScheduledTaskLink.task from existing data

If any `ScheduledTaskLink` rows exist (unlikely on fresh DB), this step would have populated the new `task` FK from the old GenericFK data. Since `content_type` and `object_id` were already removed in Migration A, this step is effectively a no-op for a fresh database. Include it as a stub `RunPython` with `migrations.RunPython.noop` for both forward and reverse, with a comment explaining the rationale.

**Critical rule:** All `RunPython` operations must use `apps.get_model()` to get model references. Never use direct model imports inside migration functions.

---

## Migration C: Constraint Enforcement & Indexes (`0056_task_restructure_indexes.py`)

**Depends on:** `('api', '0055_task_restructure_data')`

### Operations

1. **Add indexes on AgentGlobalTask:**
   - `models.Index(fields=['agent', 'client'])` -- for client-filtered task queries
   - `models.Index(fields=['task_category_ref', 'status'])` -- for category-filtered views
   - `models.Index(fields=['recurrence_parent'])` -- for JIT instance lookups
   - `models.Index(fields=['client', 'scheduled_date'])` -- for Split 06 client reporting

2. **Add unique_together on AgentGlobalTask:**
   - `unique_together = {('recurrence_parent', 'recurrence_instance_number')}` -- prevents duplicate JIT instances. This is the database-level safety net for the race condition prevention described in section 5.

**Note:** All new fields remain nullable by design. No NOT NULL constraints are added in this migration. The nullable design allows tasks to exist without recurrence fields, without a client, and without a category.

### Reverse

Django's `AddIndex` and `AlterUniqueTogether` operations have built-in reverse operations. No custom reverse code needed.

---

## Migration D: Cleanup (`0057_task_restructure_cleanup.py`)

**Depends on:** `('api', '0056_task_restructure_indexes')`

This migration removes deprecated fields and models. The order of operations is critical.

### Operations (in order)

1. **Remove `recurring_source` FK from `AgentGlobalTask`** -- this FK points to `RecurringTaskTemplate`. It must be removed BEFORE deleting the `RecurringTaskTemplate` model, or Django will refuse the migration.

2. **Remove `recurring_source` FK from `AgentTimeBlock`** -- same FK pointing to `RecurringTaskTemplate` (line 49 of agent_scheduling.py). Note: this is `AgentTimeBlock.recurring_source` which points to `AgentRecurringBlock`, NOT `RecurringTaskTemplate`. Double-check the actual FK target before removing. Only remove if it points to `RecurringTaskTemplate`. Looking at the existing code:
   - `AgentTimeBlock.recurring_source` points to `AgentRecurringBlock` (line 49-52) -- do NOT remove this
   - `AgentGlobalTask.recurring_source` points to `RecurringTaskTemplate` (line 139-142) -- remove this

   Correction: only `AgentGlobalTask.recurring_source` needs removal. `AgentTimeBlock.recurring_source` points to `AgentRecurringBlock` which is a separate, still-active system for recurring time blocks.

3. **Delete `RecurringTaskTemplate` model** -- after removing all FKs that reference it.

4. **Remove `task_category` CharField from `AgentGlobalTask`** -- the old CharField is no longer needed since data has been migrated to `task_category_ref` FK in Migration B.

5. **Remove `TASK_CATEGORY_CHOICES` constant** -- this is a code-level change (in the model file), not a migration operation. The migration should remove the `choices` reference from the old field, but the constant itself is removed from the Python source.

### Reverse

For reversibility:
- Re-add `recurring_source` FK to AgentGlobalTask (pointing to RecurringTaskTemplate)
- Re-create `RecurringTaskTemplate` model with all its original fields
- Re-add `task_category` CharField to AgentGlobalTask
- The reverse of `DeleteModel` is the original `CreateModel`, which Django handles if you use the proper migration operation

---

## Workflow for Creating the Migrations

The recommended workflow:

1. **Apply model changes from sections 1-3** to `server/api/models/agent_scheduling.py`
2. Run `python manage.py makemigrations api` -- Django will auto-detect the schema changes and generate a migration
3. Split the auto-generated migration into Migration A (schema only) and adjust naming
4. Write Migration B (data) by hand as a `RunPython` migration
5. Write Migration C (indexes) by hand or extract from auto-generated operations
6. Write Migration D (cleanup) -- apply the final model changes (remove old fields/model from code), then run `makemigrations` again

An alternative approach is to write all four migrations by hand, which gives full control over operation ordering. This is preferred given the complexity.

---

## Verification

After all four migrations are created, verify:

```bash
cd /home/ubuntu/Montrroase_website/server
python manage.py showmigrations api | tail -10
# Should show 0054, 0055, 0056, 0057 as unapplied

python manage.py migrate api
# Should apply all four without errors

python manage.py migrate api 0053
# Should reverse all four without errors (tests reversibility)

python manage.py migrate api
# Re-apply to restore state
```

Then verify seed data:

```bash
python manage.py shell -c "
from api.models.agent_scheduling import TaskCategory
print(f'Categories: {TaskCategory.objects.count()}')  # Should be 11
print(f'Review categories: {TaskCategory.objects.filter(requires_review=True).count()}')  # Should be 2
"
```

---

## Risk Notes

1. **Migration ordering:** Migrations A-B-C-D must have explicit `dependencies` linking each to the previous. Django uses the dependency chain to determine execution order.

2. **`recurring_source` FK on AgentTimeBlock:** This FK points to `AgentRecurringBlock`, NOT `RecurringTaskTemplate`. Do not remove it. Only `AgentGlobalTask.recurring_source` (pointing to `RecurringTaskTemplate`) should be removed.

3. **ScheduledTaskLink GenericFK removal:** The `GenericForeignKey` attribute itself is not a database column -- it is a Python-level descriptor. The migration only needs to remove `content_type` (FK) and `object_id` (UUIDField). The `GenericForeignKey('content_type', 'object_id')` line is removed from the model source code, not from the migration.

4. **`unique_together` on `(recurrence_parent, recurrence_instance_number)`:** Both fields are nullable. In most databases (including PostgreSQL), `NULL != NULL` in unique constraints, meaning two rows with `recurrence_parent=NULL` will not conflict. This is the desired behavior -- only actual recurring task instances (with non-null parent) are protected against duplicates.

5. **Seed data idempotency:** Use `get_or_create` in the seed function so the migration can be re-run safely if needed during development.