diff --git a/server/api/models/agent_scheduling.py b/server/api/models/agent_scheduling.py
index c1b318c19..06eb1fca9 100644
--- a/server/api/models/agent_scheduling.py
+++ b/server/api/models/agent_scheduling.py
@@ -3,8 +3,6 @@ from datetime import datetime, timedelta
 from django.conf import settings
 from django.core.exceptions import ValidationError
 from django.db import models
-from django.contrib.contenttypes.fields import GenericForeignKey
-from django.contrib.contenttypes.models import ContentType
 from django.utils import timezone
 from django.utils.text import slugify
 import uuid
@@ -272,16 +270,15 @@ class AgentGlobalTask(models.Model):
 
 
 class ScheduledTaskLink(models.Model):
-    """Links existing client tasks (MarketingTask/ProjectTask) to the agent's schedule."""
+    """Links an AgentGlobalTask to the agent's schedule."""
     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
     agent = models.ForeignKey(
         'Agent', on_delete=models.CASCADE, related_name='scheduled_task_links'
     )
-
-    # Generic FK to MarketingTask or ProjectTask
-    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
-    object_id = models.UUIDField()
-    task = GenericForeignKey('content_type', 'object_id')
+    task = models.ForeignKey(
+        'AgentGlobalTask', on_delete=models.CASCADE, null=True, blank=True,
+        related_name='scheduled_task_links'
+    )
 
     scheduled_date = models.DateField(null=True, blank=True)
     time_block = models.ForeignKey(
@@ -293,13 +290,14 @@ class ScheduledTaskLink(models.Model):
     created_at = models.DateTimeField(default=timezone.now)
 
     class Meta:
-        unique_together = ['content_type', 'object_id', 'agent']
+        unique_together = ['task', 'agent']
         indexes = [
             models.Index(fields=['agent', 'scheduled_date']),
         ]
 
     def __str__(self):
-        return f"Link: {self.agent} → {self.content_type.model}#{self.object_id}"
+        task_label = self.task.title if self.task else 'unlinked'
+        return f"Link: {self.agent} → {task_label}"
 
 
 class WeeklyPlan(models.Model):
diff --git a/server/api/tests.py b/server/api/tests.py
index 1026e6e65..fa51ab072 100644
--- a/server/api/tests.py
+++ b/server/api/tests.py
@@ -152,6 +152,52 @@ class TaskCategorySeedDataTest(TestCase):
             self.assertIn(slug, existing, f"Missing seed slug: {slug}")
 
 
+# ---------------------------------------------------------------------------
+# Section 03: ScheduledTaskLink simplification tests
+# ---------------------------------------------------------------------------
+
+from api.models.agent_scheduling import ScheduledTaskLink
+
+
+class ScheduledTaskLinkFKTest(TestCase):
+    """ScheduledTaskLink uses direct FK to AgentGlobalTask (no GenericFK)."""
+
+    def setUp(self):
+        user = User.objects.create_user(
+            username='agent03', password='pass', email='agent03@test.com', role='agent'
+        )
+        self.agent = Agent.objects.create(user=user, department='marketing')
+        self.task = AgentGlobalTask.objects.create(agent=self.agent, title='Task A')
+
+    def test_task_field_is_fk_to_agent_global_task(self):
+        from django.db.models import ForeignKey
+        field = ScheduledTaskLink._meta.get_field('task')
+        self.assertIsInstance(field, ForeignKey)
+        self.assertEqual(field.related_model, AgentGlobalTask)
+
+    def test_creating_link_with_task_fk_works(self):
+        link = ScheduledTaskLink.objects.create(agent=self.agent, task=self.task)
+        link.refresh_from_db()
+        self.assertEqual(link.task_id, self.task.pk)
+
+    def test_unique_together_task_and_agent(self):
+        ScheduledTaskLink.objects.create(agent=self.agent, task=self.task)
+        with self.assertRaises(IntegrityError):
+            ScheduledTaskLink.objects.create(agent=self.agent, task=self.task)
+
+    def test_deleting_task_cascades_to_link(self):
+        link = ScheduledTaskLink.objects.create(agent=self.agent, task=self.task)
+        self.task.delete()
+        self.assertFalse(ScheduledTaskLink.objects.filter(pk=link.pk).exists())
+
+    def test_generic_fk_fields_do_not_exist(self):
+        from django.core.exceptions import FieldDoesNotExist
+        with self.assertRaises(FieldDoesNotExist):
+            ScheduledTaskLink._meta.get_field('content_type')
+        with self.assertRaises(FieldDoesNotExist):
+            ScheduledTaskLink._meta.get_field('object_id')
+
+
 # ---------------------------------------------------------------------------
 # Section 02: AgentGlobalTask model extension tests
 # ---------------------------------------------------------------------------
