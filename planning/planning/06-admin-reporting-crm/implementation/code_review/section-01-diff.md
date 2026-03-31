diff --git a/server/api/migrations/0075_agentglobaltask_review_feedback.py b/server/api/migrations/0075_agentglobaltask_review_feedback.py
new file mode 100644
index 000000000..158d3188e
--- /dev/null
+++ b/server/api/migrations/0075_agentglobaltask_review_feedback.py
@@ -0,0 +1,16 @@
+from django.db import migrations, models
+
+
+class Migration(migrations.Migration):
+
+    dependencies = [
+        ('api', '0074_recurringtasktemplate'),
+    ]
+
+    operations = [
+        migrations.AddField(
+            model_name='agentglobaltask',
+            name='review_feedback',
+            field=models.TextField(blank=True, default=''),
+        ),
+    ]
diff --git a/server/api/migrations/0076_marketingplan_strategy_notes.py b/server/api/migrations/0076_marketingplan_strategy_notes.py
new file mode 100644
index 000000000..db3014b52
--- /dev/null
+++ b/server/api/migrations/0076_marketingplan_strategy_notes.py
@@ -0,0 +1,16 @@
+from django.db import migrations, models
+
+
+class Migration(migrations.Migration):
+
+    dependencies = [
+        ('api', '0075_agentglobaltask_review_feedback'),
+    ]
+
+    operations = [
+        migrations.AddField(
+            model_name='marketingplan',
+            name='strategy_notes',
+            field=models.TextField(blank=True, default=''),
+        ),
+    ]
diff --git a/server/api/migrations/0077_agenttimeblock_client_date_index.py b/server/api/migrations/0077_agenttimeblock_client_date_index.py
new file mode 100644
index 000000000..708e0f2bb
--- /dev/null
+++ b/server/api/migrations/0077_agenttimeblock_client_date_index.py
@@ -0,0 +1,15 @@
+from django.db import migrations, models
+
+
+class Migration(migrations.Migration):
+
+    dependencies = [
+        ('api', '0076_marketingplan_strategy_notes'),
+    ]
+
+    operations = [
+        migrations.AddIndex(
+            model_name='agenttimeblock',
+            index=models.Index(fields=['client', 'date'], name='api_agenttime_client_date_idx'),
+        ),
+    ]
diff --git a/server/api/models/agent_scheduling.py b/server/api/models/agent_scheduling.py
index 6d6f13a45..9cfd8ba81 100644
--- a/server/api/models/agent_scheduling.py
+++ b/server/api/models/agent_scheduling.py
@@ -114,6 +114,7 @@ class AgentTimeBlock(models.Model):
         indexes = [
             models.Index(fields=['agent', 'date']),
             models.Index(fields=['agent', 'date', 'block_type']),
+            models.Index(fields=['client', 'date'], name='api_agenttime_client_date_idx'),
         ]
 
     def __str__(self):
@@ -210,6 +211,8 @@ class AgentGlobalTask(models.Model):
     start_time = models.TimeField(null=True, blank=True)
     end_time = models.TimeField(null=True, blank=True)
 
+    review_feedback = models.TextField(blank=True, default='')
+
     order = models.PositiveIntegerField(default=0)
     completed_at = models.DateTimeField(null=True, blank=True)
 
diff --git a/server/api/models/marketing_core.py b/server/api/models/marketing_core.py
index e3f8aef58..5799f405f 100644
--- a/server/api/models/marketing_core.py
+++ b/server/api/models/marketing_core.py
@@ -39,6 +39,7 @@ class MarketingPlan(models.Model):
     name = models.CharField(max_length=255, default="Marketing Plan")
     timezone = models.CharField(max_length=64, default="Europe/Tirane")
     is_active = models.BooleanField(default=True)
+    strategy_notes = models.TextField(blank=True, default='')
 
     created_by = models.ForeignKey(
         settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_marketing_plans"
diff --git a/server/api/serializers/agent_scheduling.py b/server/api/serializers/agent_scheduling.py
index 93f55d00a..d7e0b48ac 100644
--- a/server/api/serializers/agent_scheduling.py
+++ b/server/api/serializers/agent_scheduling.py
@@ -135,6 +135,7 @@ class AgentGlobalTaskReadSerializer(serializers.ModelSerializer):
             'start_time', 'end_time',
             'time_block', 'time_block_title',
             'estimated_minutes', 'is_overdue', 'order',
+            'review_feedback',
             'completed_at', 'created_at', 'updated_at',
         ] + _RECURRENCE_FIELDS
         read_only_fields = fields
@@ -149,6 +150,15 @@ class AgentGlobalTaskReadSerializer(serializers.ModelSerializer):
 
 class AgentGlobalTaskWriteSerializer(serializers.ModelSerializer):
     """Write serializer — used for POST/PATCH requests."""
+    recurrence_parent = serializers.PrimaryKeyRelatedField(
+        queryset=AgentGlobalTask.objects.all(),
+        required=False,
+        allow_null=True,
+        default=None
+    )
+    recurrence_instance_number = serializers.IntegerField(
+        required=False, allow_null=True, default=None
+    )
 
     class Meta:
         model = AgentGlobalTask
diff --git a/server/api/serializers/marketing_core.py b/server/api/serializers/marketing_core.py
index 681ae1b76..c6f9a7860 100644
--- a/server/api/serializers/marketing_core.py
+++ b/server/api/serializers/marketing_core.py
@@ -58,6 +58,7 @@ class MarketingPlanSerializer(serializers.ModelSerializer):
         model = MarketingPlan
         fields = [
             "id", "client", "name", "timezone", "is_active",
+            "strategy_notes",
             "created_by", "created_at", "updated_at",
             "pillars", "audiences",
         ]
diff --git a/server/api/tests.py b/server/api/tests.py
index ff7a420c8..b56e13c8c 100644
--- a/server/api/tests.py
+++ b/server/api/tests.py
@@ -5,9 +5,10 @@ from django.core.exceptions import ValidationError
 from django.db import IntegrityError
 from rest_framework.test import APIRequestFactory, APITestCase, APIClient
 
-from api.models.agent_scheduling import TaskCategory, AgentGlobalTask, ScheduledTaskLink
+from api.models.agent_scheduling import TaskCategory, AgentGlobalTask, ScheduledTaskLink, AgentTimeBlock
 from api.models.users import User, Agent
 from api.models.clients import Client
+from api.models.marketing_core import MarketingPlan
 
 
 # ---------------------------------------------------------------------------
@@ -983,3 +984,99 @@ class RoutingSection07Test(APITestCase):
         )
         response = self.api_client.post(f'/api/agent/schedule/global-tasks/{task.id}/complete/')
         self.assertNotEqual(response.status_code, 404)
+
+
+# ---------------------------------------------------------------------------
+# Section 06 — Backend Migrations (review_feedback, strategy_notes, index)
+# ---------------------------------------------------------------------------
+
+class TestAgentGlobalTaskReviewFeedback(TestCase):
+
+    def setUp(self):
+        user = User.objects.create_user(
+            username='mig_agent01', password='pass', email='mig01@test.com', role='agent'
+        )
+        self.agent = Agent.objects.create(user=user, department='marketing')
+
+    def test_review_feedback_field_exists_on_model(self):
+        task = AgentGlobalTask(agent=self.agent, title='T')
+        self.assertTrue(hasattr(task, 'review_feedback'))
+
+    def test_review_feedback_default_is_empty_string(self):
+        task = AgentGlobalTask.objects.create(agent=self.agent, title='T2')
+        self.assertEqual(task.review_feedback, '')
+
+    def test_review_feedback_in_read_serializer(self):
+        from api.serializers.agent_scheduling import AgentGlobalTaskReadSerializer
+        self.assertIn('review_feedback', AgentGlobalTaskReadSerializer.Meta.fields)
+
+    def test_review_feedback_not_in_write_serializer(self):
+        from api.serializers.agent_scheduling import AgentGlobalTaskWriteSerializer
+        self.assertNotIn('review_feedback', AgentGlobalTaskWriteSerializer.Meta.fields)
+
+
+class TestMarketingPlanStrategyNotes(TestCase):
+
+    def setUp(self):
+        import datetime
+        user = User.objects.create_user(
+            username='mig_admin01', password='pass', email='migadmin01@test.com', role='admin'
+        )
+        self.client_obj = Client.objects.create(
+            name='Test Co', email='testco@test.com', company='TestCo',
+            start_date=datetime.date(2025, 1, 1),
+        )
+        self.plan = MarketingPlan.objects.create(
+            client=self.client_obj, created_by=user
+        )
+
+    def test_strategy_notes_field_exists_on_model(self):
+        self.assertTrue(hasattr(self.plan, 'strategy_notes'))
+
+    def test_strategy_notes_default_is_empty_string(self):
+        self.assertEqual(self.plan.strategy_notes, '')
+
+    def test_strategy_notes_in_serializer(self):
+        from api.serializers.marketing_core import MarketingPlanSerializer
+        self.assertIn('strategy_notes', MarketingPlanSerializer.Meta.fields)
+
+
+class TestAgentTimeBlockClientDateIndex(TestCase):
+
+    def setUp(self):
+        import datetime
+        user = User.objects.create_user(
+            username='mig_agent02', password='pass', email='mig02@test.com', role='agent'
+        )
+        self.agent = Agent.objects.create(user=user, department='marketing')
+        self.client_a = Client.objects.create(
+            name='Client A', email='a@test.com', company='ClientA',
+            start_date=datetime.date(2025, 1, 1),
+        )
+        self.client_b = Client.objects.create(
+            name='Client B', email='b@test.com', company='ClientB',
+            start_date=datetime.date(2025, 1, 1),
+        )
+
+    def test_client_date_filter_returns_correct_results(self):
+        import datetime
+        AgentTimeBlock.objects.create(
+            agent=self.agent, date=datetime.date(2026, 1, 10),
+            start_time=datetime.time(9, 0), end_time=datetime.time(10, 0),
+            block_type='deep_work', client=self.client_a,
+        )
+        AgentTimeBlock.objects.create(
+            agent=self.agent, date=datetime.date(2026, 1, 15),
+            start_time=datetime.time(11, 0), end_time=datetime.time(12, 0),
+            block_type='reactive', client=self.client_a,
+        )
+        AgentTimeBlock.objects.create(
+            agent=self.agent, date=datetime.date(2026, 1, 12),
+            start_time=datetime.time(14, 0), end_time=datetime.time(15, 0),
+            block_type='creative', client=self.client_b,
+        )
+        qs = AgentTimeBlock.objects.filter(
+            client=self.client_a,
+            date__range=(datetime.date(2026, 1, 1), datetime.date(2026, 1, 31)),
+        )
+        self.assertEqual(qs.count(), 2)
