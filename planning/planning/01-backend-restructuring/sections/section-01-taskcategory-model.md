Good -- the actual department values are `marketing` and `website`, not `developer`. The plan (claude-plan.md) correctly says `marketing/website/both`. The spec (claude-spec.md) says `developer` which is wrong. I'll follow the plan which aligns with the actual codebase.

Now I have everything I need.

# Section 1: TaskCategory Model and Seed Data

## Overview

This section introduces a new `TaskCategory` Django model in `server/api/models/agent_scheduling.py` that replaces the existing hardcoded `TASK_CATEGORY_CHOICES` list on `AgentGlobalTask`. The model allows admins to CRUD categories through an API, and agents to see department-filtered lists. A data migration seeds 11 default categories.

**File to modify:** `/home/ubuntu/Montrroase_website/server/api/models/agent_scheduling.py`
**File to modify:** `/home/ubuntu/Montrroase_website/server/api/tests.py` (currently empty)

**Dependencies:** None -- this is the first section and has no prerequisites.
**Blocks:** Section 02 (AgentGlobalTask model changes), Section 04 (migrations).

---

## Tests (Write First)

All tests go in `/home/ubuntu/Montrroase_website/server/api/tests.py`. Use `django.test.TestCase`.

### Model Tests

```python
# Test: TaskCategory creates with all required fields and defaults
# - Create a TaskCategory with only `name` and `department` set
# - Assert id is a UUID, color defaults to '#2563EB', is_active defaults to True,
#   sort_order defaults to 0, requires_review defaults to False

# Test: TaskCategory.slug auto-generates from name on creation
# - Create TaskCategory(name='QA Review', department='website')
# - Assert slug == 'qa-review'

# Test: TaskCategory.slug does NOT update when name changes (prevents URL breakage)
# - Create a category, note the slug
# - Change the name, save
# - Assert slug is unchanged

# Test: TaskCategory.name uniqueness constraint rejects duplicates
# - Create two categories with the same name
# - Assert IntegrityError is raised on the second

# Test: TaskCategory.slug uniqueness constraint rejects duplicates
# - Create two categories whose names would produce the same slug
# - Assert IntegrityError is raised

# Test: TaskCategory.department choices limited to marketing/website/both
# - Create categories with each valid value -- should succeed
# - Attempt to use full_clean() with an invalid department value -- should raise ValidationError

# Test: TaskCategory.color defaults to '#2563EB'
# - Create a category without specifying color
# - Assert color == '#2563EB'

# Test: TaskCategory ordering is by (sort_order, name)
# - Create categories with different sort_order and name values
# - Query TaskCategory.objects.all() and assert the order matches (sort_order ASC, then name ASC)

# Test: TaskCategory.__str__ returns name
# - Create a category with name='Design'
# - Assert str(category) == 'Design'
```

### Seed Data Migration Tests

These tests verify the data migration (implemented in Section 04) but the expectations are defined here since the seed data specification lives in this section.

```python
# Test: After migration, 11 seed categories exist
# - Assert TaskCategory.objects.count() == 11

# Test: Seed categories have correct department assignments
# - 'copywriting' slug has department='marketing'
# - 'qa-review' slug has department='website'
# - 'design' slug has department='both'

# Test: Copywriting and QA Review categories have requires_review=True
# - Assert TaskCategory.objects.filter(requires_review=True).count() == 2
# - Assert the slugs are 'copywriting' and 'qa-review'

# Test: Seed category slugs are correctly generated
# - Assert all 11 expected slugs exist: design, copywriting, seo-optimization,
#   qa-review, client-communication, administrative-ops, content-creation,
#   strategy, research, development, devops
```

### Index Tests

```python
# Test: Query filtering by (is_active, department) uses index
# - Execute TaskCategory.objects.filter(is_active=True, department='marketing')
# - Assert query completes without error (functional verification)
```

---

## Implementation Details

### TaskCategory Model

Add the `TaskCategory` class to `/home/ubuntu/Montrroase_website/server/api/models/agent_scheduling.py`, placing it **before** the `AgentGlobalTask` class (since `AgentGlobalTask` will later reference it via FK in Section 02).

Key design decisions:

1. **UUID primary key** -- consistent with all other models in this codebase (AgentTimeBlock, AgentGlobalTask, ScheduledTaskLink all use `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`).

2. **Department choices** -- must use `marketing`, `website`, `both` to align with `Agent.DEPARTMENT_CHOICES` in `server/api/models/users.py` which uses `('marketing', 'Marketing')` and `('website', 'Website Development')`. Note: the spec document incorrectly lists `developer` but the actual codebase uses `website`. Use `website`.

3. **Slug auto-generation** -- override `save()` to auto-generate slug from name using `django.utils.text.slugify`, but only when the object has no slug yet (i.e., on first save / creation). This prevents URL breakage if the name is later changed.

4. **`requires_review` field** -- when True, tasks in this category are intercepted at completion time and redirected to `in_review` status instead of `done`. This is enforced in the serializer layer (Section 06), not in this model.

### Model Skeleton

```python
class TaskCategory(models.Model):
    """Admin-configurable task categories replacing hardcoded TASK_CATEGORY_CHOICES."""
    DEPARTMENT_CHOICES = [
        ('marketing', 'Marketing'),
        ('website', 'Website'),
        ('both', 'Both'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    color = models.CharField(max_length=7, default='#2563EB', help_text='Hex color e.g. #2563EB')
    icon = models.CharField(max_length=50, blank=True, help_text='Lucide icon name')
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default='both')
    requires_review = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_task_categories'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'department']),
        ]
        verbose_name_plural = 'task categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name on creation only."""
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
```

Note on the `created_by` FK: The User model is in `server/api/models/users.py`. Check the actual import path -- if the app label is `api`, the FK reference should be `'User'` (same app) or use `settings.AUTH_USER_MODEL` if User is a custom auth user. Look at how existing FKs to User are defined in the codebase (e.g., `Agent.user` uses `User` directly). Follow the same pattern.

### Seed Data

The seed data is applied via a data migration (created in Section 04). The 11 categories to seed are:

| Name | Slug | Department | Color | Requires Review |
|------|------|-----------|-------|-----------------|
| Design | design | both | #8B5CF6 | False |
| Copywriting | copywriting | marketing | #F59E0B | True |
| SEO Optimization | seo-optimization | marketing | #10B981 | False |
| QA Review | qa-review | website | #EF4444 | True |
| Client Communication | client-communication | both | #3B82F6 | False |
| Administrative Ops | administrative-ops | both | #6B7280 | False |
| Content Creation | content-creation | marketing | #EC4899 | False |
| Strategy | strategy | marketing | #8B5CF6 | False |
| Research | research | both | #14B8A6 | False |
| Development | development | website | #2563EB | False |
| DevOps | devops | website | #F97316 | False |

**Important department mapping note:** The spec lists QA Review, Development, and DevOps as `developer` department, but the actual `Agent.DEPARTMENT_CHOICES` uses `website` not `developer`. Use `website` for these three categories.

### Category-to-old-CharField Mapping

For the data migration in Section 04, this is the mapping from old `TASK_CATEGORY_CHOICES` values to new category slugs:

| Old CharField Value | New Category Slug |
|---|---|
| `admin` | `administrative-ops` |
| `strategy` | `strategy` |
| `creative` | `design` |
| `analytical` | `research` |
| `communication` | `client-communication` |
| `professional_development` | (no mapping -- dropped) |
| `internal` | `administrative-ops` |
| `planning` | `strategy` |
| `research` | `research` |
| `coding` | `development` |
| `review` | `qa-review` |
| `devops` | `devops` |
| `content_creation` | `content-creation` |

This mapping is documented here for Section 04's use but the model code itself does not contain it.

### Existing Code Coexistence

The existing `TASK_CATEGORY_CHOICES` list on `AgentGlobalTask` (lines 92-109 of `agent_scheduling.py`) and the `task_category` CharField (line 125-127) must remain untouched in this section. They are removed later in Migration D (Section 04). Both the old CharField and the new `TaskCategory` model coexist until then.

---

## Checklist

1. Write tests in `/home/ubuntu/Montrroase_website/server/api/tests.py` for the `TaskCategory` model (model tests and index tests above; seed data tests can be written as stubs that will pass once Section 04 migrations are applied)
2. Add the `TaskCategory` model class to `/home/ubuntu/Montrroase_website/server/api/models/agent_scheduling.py`, placed before `AgentGlobalTask`
3. Ensure the import for `uuid` already exists at the top of the file (it does, line 7)
4. Do NOT create migrations yet -- that is Section 04's responsibility
5. Do NOT modify `AgentGlobalTask` or any other existing model -- that is Section 02's responsibility
6. Run tests with `cd /home/ubuntu/Montrroase_website/server && python manage.py test api` to verify model tests pass (note: tests requiring the DB table will fail until migrations in Section 04 are applied; structure tests using `TestCase` will work after migrations)

## Implementation Notes (Actual)

**Files modified:**
- `server/api/models/agent_scheduling.py` — added `TaskCategory` class before `AgentGlobalTask`; added `from django.core.exceptions import ValidationError` and `from django.utils.text import slugify` at module level
- `server/api/tests.py` — added all model tests, seed data stubs, and index test

**Deviations from plan:**
- `slug` field: added `editable=False` (admin protection)
- Added `clean()` method for slug collision detection (raises `ValidationError` if two names slugify identically); per user decision during code review
- `slugify` moved from lazy import inside `save()` to module-level import

**Tests:** 13 test methods written (9 model + 1 index + 3 seed stubs).
Seed data tests (`TaskCategorySeedDataTest`) require Section 04 data migration to pass.