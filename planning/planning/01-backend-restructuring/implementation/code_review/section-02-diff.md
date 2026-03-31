diff --git a/server/api/models/agent_scheduling.py b/server/api/models/agent_scheduling.py
index 3479f3a3f..c1b318c19 100644
--- a/server/api/models/agent_scheduling.py
+++ b/server/api/models/agent_scheduling.py
@@ -137,6 +137,7 @@ class AgentGlobalTask(models.Model):
     class Status(models.TextChoices):
         TODO = 'todo', 'To Do'
         IN_PROGRESS = 'in_progress', 'In Progress'
+        IN_REVIEW = 'in_review', 'In Review'
         DONE = 'done', 'Done'
 
     class Priority(models.TextChoices):
@@ -180,6 +181,48 @@ class AgentGlobalTask(models.Model):
     task_category = models.CharField(
         max_length=30, choices=TASK_CATEGORY_CHOICES, blank=True
     )
+    client = models.ForeignKey(
+        'Client', on_delete=models.SET_NULL, null=True, blank=True,
+        related_name='global_tasks'
+    )
+    task_category_ref = models.ForeignKey(
+        'TaskCategory', on_delete=models.SET_NULL, null=True, blank=True,
+        related_name='tasks'
+    )
+
+    # Recurrence fields (embedded on task, replacing RecurringTaskTemplate FK)
+    is_recurring = models.BooleanField(default=False)
+    recurrence_frequency = models.CharField(
+        max_length=20, null=True, blank=True,
+        choices=[
+            ('daily', 'Daily'),
+            ('weekly', 'Weekly'),
+            ('biweekly', 'Biweekly'),
+            ('monthly', 'Monthly'),
+            ('yearly', 'Yearly'),
+            ('custom', 'Custom'),
+        ]
+    )
+    recurrence_days = models.JSONField(
+        null=True, blank=True,
+        help_text='ISO weekday numbers for weekly patterns, e.g. [0,2,4] for Mon/Wed/Fri'
+    )
+    recurrence_interval = models.IntegerField(null=True, blank=True, default=1)
+    recurrence_end_type = models.CharField(
+        max_length=10, null=True, blank=True,
+        choices=[
+            ('never', 'Never'),
+            ('count', 'After N occurrences'),
+            ('date', 'Until date'),
+        ]
+    )
+    recurrence_end_count = models.IntegerField(null=True, blank=True)
+    recurrence_end_date = models.DateField(null=True, blank=True)
+    recurrence_parent = models.ForeignKey(
+        'self', on_delete=models.SET_NULL, null=True, blank=True,
+        related_name='recurrence_instances'
+    )
+    recurrence_instance_number = models.IntegerField(null=True, blank=True)
 
     due_date = models.DateField(null=True, blank=True)
     scheduled_date = models.DateField(null=True, blank=True)
@@ -207,7 +250,11 @@ class AgentGlobalTask(models.Model):
         indexes = [
             models.Index(fields=['agent', 'status']),
             models.Index(fields=['agent', 'scheduled_date']),
-            models.Index(fields=['agent', 'task_category']),
+            models.Index(fields=['agent', 'task_category']),  # removed in Migration D
+            models.Index(fields=['agent', 'client']),
+            models.Index(fields=['task_category_ref', 'status']),
+            models.Index(fields=['recurrence_parent']),
+            models.Index(fields=['client', 'scheduled_date']),
         ]
 
     @property
diff --git a/server/api/tests.py b/server/api/tests.py
index 2f5607acd..c8b48e361 100644
--- a/server/api/tests.py
+++ b/server/api/tests.py
@@ -2,7 +2,9 @@ from django.test import TestCase
 from django.core.exceptions import ValidationError
 from django.db import IntegrityError
 
-from api.models.agent_scheduling import TaskCategory
+from api.models.agent_scheduling import TaskCategory, AgentGlobalTask
+from api.models.users import User, Agent
+from api.models.clients import Client
 
 
 # ---------------------------------------------------------------------------
@@ -146,3 +148,137 @@ class TaskCategorySeedDataTest(TestCase):
         existing = set(TaskCategory.objects.values_list('slug', flat=True))
         for slug in self.EXPECTED_SLUGS:
             self.assertIn(slug, existing, f"Missing seed slug: {slug}")
+
+
+# ---------------------------------------------------------------------------
+# Section 02: AgentGlobalTask model extension tests
+# ---------------------------------------------------------------------------
+
+def make_agent():
+    """Helper: create a User + Agent for tests."""
+    user = User.objects.create_user(
+        username='testagent', password='pass', email='agent@test.com', role='agent'
+    )
+    agent = Agent.objects.create(user=user, department='marketing')
+    return agent
+
+
+def make_client():
+    """Helper: create a minimal Client."""
+    import datetime
+    return Client.objects.create(
+        name='Test Client',
+        email='client@test.com',
+        company='Test Co',
+        start_date=datetime.date.today(),
+        status='active',
+    )
+
+
+class AgentGlobalTaskClientFKTest(TestCase):
+    """AgentGlobalTask.client FK behaviour."""
+
+    def setUp(self):
+        self.agent = make_agent()
+        self.client_obj = make_client()
+
+    def _make_task(self, **kwargs):
+        return AgentGlobalTask.objects.create(
+            agent=self.agent, title='Test task', **kwargs
+        )
+
+    def test_client_is_nullable(self):
+        task = self._make_task()
+        self.assertIsNone(task.client)
+
+    def test_client_fk_links_correctly(self):
+        task = self._make_task(client=self.client_obj)
+        task.refresh_from_db()
+        self.assertEqual(task.client_id, self.client_obj.pk)
+
+    def test_delete_client_sets_null(self):
+        task = self._make_task(client=self.client_obj)
+        self.client_obj.delete()
+        task.refresh_from_db()
+        self.assertIsNone(task.client)
+
+
+class AgentGlobalTaskCategoryFKTest(TestCase):
+    """AgentGlobalTask.task_category_ref FK behaviour."""
+
+    def setUp(self):
+        self.agent = make_agent()
+        self.category = TaskCategory.objects.create(name='Design', department='both')
+
+    def _make_task(self, **kwargs):
+        return AgentGlobalTask.objects.create(
+            agent=self.agent, title='Test task', **kwargs
+        )
+
+    def test_category_ref_is_nullable(self):
+        task = self._make_task()
+        self.assertIsNone(task.task_category_ref)
+
+    def test_category_ref_links_correctly(self):
+        task = self._make_task(task_category_ref=self.category)
+        task.refresh_from_db()
+        self.assertEqual(task.task_category_ref_id, self.category.pk)
+
+    def test_delete_category_sets_null(self):
+        task = self._make_task(task_category_ref=self.category)
+        self.category.delete()
+        task.refresh_from_db()
+        self.assertIsNone(task.task_category_ref)
+
+
+class AgentGlobalTaskRecurrenceFieldsTest(TestCase):
+    """Recurrence fields on AgentGlobalTask."""
+
+    def setUp(self):
+        self.agent = make_agent()
+
+    def _make_task(self, **kwargs):
+        return AgentGlobalTask.objects.create(
+            agent=self.agent, title='Test task', **kwargs
+        )
+
+    def test_is_recurring_defaults_false(self):
+        task = self._make_task()
+        self.assertFalse(task.is_recurring)
+
+    def test_recurrence_fields_allow_null(self):
+        task = self._make_task(is_recurring=False)
+        self.assertIsNone(task.recurrence_frequency)
+        self.assertIsNone(task.recurrence_days)
+        self.assertIsNone(task.recurrence_parent)
+        self.assertIsNone(task.recurrence_instance_number)
+
+    def test_recurrence_days_stores_json_array(self):
+        task = self._make_task(is_recurring=True, recurrence_frequency='weekly', recurrence_days=[1, 3])
+        task.refresh_from_db()
+        self.assertEqual(task.recurrence_days, [1, 3])
+
+    def test_recurrence_parent_self_fk(self):
+        parent = self._make_task(is_recurring=True, recurrence_frequency='daily')
+        child = self._make_task(recurrence_parent=parent, recurrence_instance_number=1)
+        child.refresh_from_db()
+        self.assertEqual(child.recurrence_parent_id, parent.pk)
+        self.assertEqual(child.recurrence_instance_number, 1)
+
+
+class AgentGlobalTaskStatusExtensionTest(TestCase):
+    """Status choices include in_review."""
+
+    def setUp(self):
+        self.agent = make_agent()
+
+    def test_in_review_choice_exists(self):
+        choices_values = [c[0] for c in AgentGlobalTask.Status.choices]
+        self.assertIn('in_review', choices_values)
+
+    def test_task_can_be_set_to_in_review(self):
+        task = AgentGlobalTask.objects.create(
+            agent=self.agent, title='Test', status=AgentGlobalTask.Status.IN_REVIEW
+        )
+        task.refresh_from_db()
+        self.assertEqual(task.status, 'in_review')
