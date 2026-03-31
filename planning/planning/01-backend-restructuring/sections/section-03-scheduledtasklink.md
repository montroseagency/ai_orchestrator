Now I have all the context I need. Let me produce the section content.

# Section 3: ScheduledTaskLink Simplification

## Overview

This section replaces the `GenericForeignKey` pattern on the `ScheduledTaskLink` model with a direct `ForeignKey` to `AgentGlobalTask`. With the move to a unified task model (completed in sections 01 and 02), the polymorphic link via `content_type` + `object_id` is no longer needed.

**Dependencies:** Section 02 (AgentGlobalTask model changes) must be complete, since the new FK points to `AgentGlobalTask`.

**Blocks:** Section 04 (migrations), which codifies this model change into migration files.

## File to Modify

`/home/ubuntu/Montrroase_website/server/api/models/agent_scheduling.py`

The `ScheduledTaskLink` class currently lives at line 172 of this file.

## Current State

The existing model uses Django's `GenericForeignKey` mechanism:

- `content_type` -- FK to `ContentType`, identifies which model the link points to (MarketingTask, ProjectTask, or AgentGlobalTask)
- `object_id` -- UUID of the linked object
- `task` -- a `GenericForeignKey('content_type', 'object_id')` virtual attribute
- `unique_together` is `['content_type', 'object_id', 'agent']`
- An index exists on `['agent', 'scheduled_date']`

The model also has: `id` (UUID PK), `agent` (FK to Agent), `scheduled_date`, `time_block` (FK to AgentTimeBlock, nullable), `order`, and `created_at`.

The imports at the top of the file include `GenericForeignKey` from `django.contrib.contenttypes.fields` and `ContentType` from `django.contrib.contenttypes.models`.

## Target State

After this section, the model should have:

- **Remove** the `content_type` field (FK to ContentType)
- **Remove** the `object_id` field (UUIDField)
- **Remove** the `task = GenericForeignKey(...)` virtual attribute
- **Add** a `task` field as a direct `ForeignKey` to `AgentGlobalTask`, nullable, with `on_delete=models.CASCADE` and `related_name='scheduled_links_as_task'` (or similar, to avoid clash with `time_block`'s related name)
- **Update** `unique_together` from `['content_type', 'object_id', 'agent']` to `['task', 'agent']`
- **Update** the `__str__` method, which currently references `self.content_type.model` and `self.object_id`
- **Remove** the `GenericForeignKey` and `ContentType` imports if no other model in the file uses them (verify first)

The existing index on `['agent', 'scheduled_date']` should be kept as-is.

## Tests (Write First)

These tests should be placed in a test file at `/home/ubuntu/Montrroase_website/server/api/tests/test_scheduled_task_link.py` (or appended to a consolidated test file if the project uses one). They validate the model structure after the change, so they will only pass once both the model code and the migration (section 04) are applied.

```python
# server/api/tests/test_scheduled_task_link.py

from django.test import TestCase
from django.db import IntegrityError
from api.models.agent_scheduling import ScheduledTaskLink, AgentGlobalTask

class ScheduledTaskLinkModelTests(TestCase):
    """Tests for the simplified ScheduledTaskLink model (direct FK, no GenericFK)."""

    def setUp(self):
        """Create an agent and a global task for use in link tests."""
        # Create required User, Agent, and AgentGlobalTask fixtures.
        # Use the project's existing model factories or manual creation.
        ...

    def test_task_field_is_direct_fk_to_agent_global_task(self):
        """ScheduledTaskLink.task is a real ForeignKey to AgentGlobalTask,
        not a GenericForeignKey."""
        ...

    def test_unique_together_on_task_and_agent(self):
        """Creating two links with the same (task, agent) pair raises IntegrityError."""
        ...

    def test_creating_link_with_task_fk_works(self):
        """A ScheduledTaskLink can be created by assigning a task FK directly."""
        ...

    def test_deleting_agent_global_task_cascades_to_link(self):
        """Deleting the linked AgentGlobalTask also deletes the ScheduledTaskLink."""
        ...

    def test_generic_fk_fields_do_not_exist(self):
        """The model no longer has content_type or object_id fields."""
        ...
```

### Test Details

**test_task_field_is_direct_fk_to_agent_global_task:** Retrieve the `task` field from `ScheduledTaskLink._meta.get_field('task')` and assert it is an instance of `django.db.models.ForeignKey`. Assert its `related_model` is `AgentGlobalTask`.

**test_unique_together_on_task_and_agent:** Create one `ScheduledTaskLink` with a given task and agent. Attempt to create a second with the same pair. Assert `IntegrityError` is raised.

**test_creating_link_with_task_fk_works:** Create a `ScheduledTaskLink` by passing `task=some_global_task, agent=some_agent`. Assert the link saves and `link.task` returns the correct `AgentGlobalTask` instance.

**test_deleting_agent_global_task_cascades_to_link:** Create a link, delete the `AgentGlobalTask`, assert the link no longer exists in the database.

**test_generic_fk_fields_do_not_exist:** Assert that `ScheduledTaskLink._meta.get_field('content_type')` raises `FieldDoesNotExist`, and likewise for `object_id`.

## Implementation Details

### Model Changes

In `/home/ubuntu/Montrroase_website/server/api/models/agent_scheduling.py`, replace the GenericFK fields on the `ScheduledTaskLink` class. The updated class should look structurally like this (showing only the changed portions):

**Remove these fields:**
```python
content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
object_id = models.UUIDField()
task = GenericForeignKey('content_type', 'object_id')
```

**Add this field:**
```python
task = models.ForeignKey(
    'AgentGlobalTask', on_delete=models.CASCADE, null=True, blank=True,
    related_name='scheduled_task_links'
)
```

The field is nullable during the transition period (migration B will populate existing rows). Section 04 Migration C may later add a NOT NULL constraint if desired, but the plan keeps all new fields nullable by design.

**Update Meta:**
```python
class Meta:
    unique_together = ['task', 'agent']
    indexes = [
        models.Index(fields=['agent', 'scheduled_date']),
    ]
```

**Update `__str__`:**
```python
def __str__(self):
    task_label = self.task.title if self.task else 'unlinked'
    return f"Link: {self.agent} → {task_label}"
```

### Import Cleanup

Check whether `GenericForeignKey` and `ContentType` are used by any other model in `agent_scheduling.py`. If not, remove these imports:

```python
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
```

If other models in the same file still reference them, keep the imports.

### Downstream Impact (Reference Only -- Handled in Other Sections)

The following files reference the GenericFK pattern on `ScheduledTaskLink` and will need updates in their respective sections:

- **Serializer** (`/home/ubuntu/Montrroase_website/server/api/serializers/agent_scheduling.py`): `ScheduledTaskLinkSerializer` currently references `content_type`, `content_type_model`, and `object_id` fields, and uses `obj.content_type.model` in `get_task_type`. This is addressed in section 06.

- **ViewSet** (`/home/ubuntu/Montrroase_website/server/api/views/agent/scheduling_views.py`): `ScheduledTaskLinkViewSet.get_queryset()` currently calls `.select_related('content_type')`. This should change to `.select_related('task')`. The function-based views (`command_center`, `cross_client_tasks`) that query `ScheduledTaskLink` using the GenericFK pattern must also update. These are addressed in section 07.

- **Migration file** (`/home/ubuntu/Montrroase_website/server/api/migrations/0066_agent_scheduling.py`): The original migration that created `ScheduledTaskLink` with GenericFK fields. This does not need modification -- a new migration in section 04 will alter the model.

- **URL routing** (`/home/ubuntu/Montrroase_website/server/api/urls.py`): No changes needed for this section; the `ScheduledTaskLinkViewSet` registration remains the same (only the model it operates on changes internally).

### Why CASCADE (Not SET_NULL)

The `on_delete=models.CASCADE` is chosen because a `ScheduledTaskLink` has no meaning without the task it links to. If the `AgentGlobalTask` is deleted, the schedule link should be cleaned up automatically. This differs from the `AgentGlobalTask.client` FK (which uses `SET_NULL` because a task can exist without a client).

### Migration Note

The actual migration for this model change is handled entirely in section 04 (Migration A for schema changes, Migration B for data population of the new `task` FK from old `object_id` values). This section only defines the model-level code changes. Do not run `makemigrations` until sections 01, 02, and 03 model changes are all in place.