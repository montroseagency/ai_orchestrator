diff --git a/server/api/serializers/agent_scheduling.py b/server/api/serializers/agent_scheduling.py
index 411e354cd..fe0f62476 100644
--- a/server/api/serializers/agent_scheduling.py
+++ b/server/api/serializers/agent_scheduling.py
@@ -5,6 +5,7 @@ from api.models import (
     AgentTimeBlock, AgentGlobalTask, ScheduledTaskLink, WeeklyPlan,
     AgentRecurringBlock, RecurringTaskTemplate,
     MarketingTask, ProjectTask,
+    TaskCategory,
 )
 
 
@@ -63,12 +64,12 @@ class AgentGlobalTaskSerializer(serializers.ModelSerializer):
         model = AgentGlobalTask
         fields = [
             'id', 'agent', 'title', 'description',
-            'status', 'priority', 'task_category',
+            'status', 'priority',
             'due_date', 'scheduled_date',
             'start_time', 'end_time',
             'time_block', 'time_block_title',
             'estimated_minutes', 'is_overdue', 'order',
-            'recurring_source', 'completed_at',
+            'completed_at',
             'created_at', 'updated_at',
         ]
         read_only_fields = ['id', 'agent', 'completed_at', 'created_at', 'updated_at']
@@ -92,6 +93,117 @@ class AgentGlobalTaskSerializer(serializers.ModelSerializer):
         return super().update(instance, validated_data)
 
 
+# ── Task Category ────────────────────────────────────────────
+
+class TaskCategorySerializer(serializers.ModelSerializer):
+    class Meta:
+        model = TaskCategory
+        fields = [
+            'id', 'name', 'slug', 'color', 'icon',
+            'department', 'requires_review', 'is_active', 'sort_order',
+            'created_by', 'created_at', 'updated_at',
+        ]
+        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
+
+
+# ── Global Task Read Serializer ──────────────────────────────
+
+_RECURRENCE_FIELDS = [
+    'is_recurring', 'recurrence_frequency', 'recurrence_days',
+    'recurrence_interval', 'recurrence_end_type', 'recurrence_end_count',
+    'recurrence_end_date', 'recurrence_parent', 'recurrence_instance_number',
+]
+
+
+class AgentGlobalTaskReadSerializer(serializers.ModelSerializer):
+    """Read-only serializer — used for GET list/detail responses."""
+    is_overdue = serializers.SerializerMethodField()
+    time_block_title = serializers.CharField(
+        source='time_block.title', read_only=True, default=''
+    )
+    client_name = serializers.CharField(source='client.company', read_only=True, default='')
+    task_category_detail = TaskCategorySerializer(source='task_category_ref', read_only=True)
+
+    class Meta:
+        model = AgentGlobalTask
+        fields = [
+            'id', 'agent', 'title', 'description',
+            'status', 'priority',
+            'client', 'client_name',
+            'task_category_ref', 'task_category_detail',
+            'due_date', 'scheduled_date',
+            'start_time', 'end_time',
+            'time_block', 'time_block_title',
+            'estimated_minutes', 'is_overdue', 'order',
+            'completed_at', 'created_at', 'updated_at',
+        ] + _RECURRENCE_FIELDS
+        read_only_fields = fields
+
+    def get_is_overdue(self, obj):
+        if not obj.due_date or obj.status in ('done', 'in_review'):
+            return False
+        return obj.due_date < tz.now().date()
+
+
+# ── Global Task Write Serializer ─────────────────────────────
+
+class AgentGlobalTaskWriteSerializer(serializers.ModelSerializer):
+    """Write serializer — used for POST/PATCH requests."""
+
+    class Meta:
+        model = AgentGlobalTask
+        fields = [
+            'id', 'agent',
+            'title', 'description', 'status', 'priority',
+            'client', 'task_category_ref',
+            'due_date', 'scheduled_date',
+            'start_time', 'end_time',
+            'time_block', 'estimated_minutes', 'order',
+            'completed_at', 'created_at', 'updated_at',
+        ] + _RECURRENCE_FIELDS
+        read_only_fields = ['id', 'agent', 'completed_at', 'created_at', 'updated_at']
+
+    def validate_status(self, value):
+        """Redirect 'done' to 'in_review' for requires_review categories."""
+        if value != 'done':
+            return value
+        instance = self.instance
+        if instance is None:
+            return value
+        category = instance.task_category_ref
+        if category and category.requires_review and instance.status != 'in_review':
+            return 'in_review'
+        return value
+
+    def validate(self, attrs):
+        """Require recurrence_frequency when is_recurring=True."""
+        is_recurring = attrs.get('is_recurring')
+        if is_recurring is None and self.instance:
+            is_recurring = self.instance.is_recurring
+        if is_recurring:
+            frequency = attrs.get('recurrence_frequency')
+            if frequency is None and self.instance:
+                frequency = self.instance.recurrence_frequency
+            if not frequency:
+                raise serializers.ValidationError(
+                    {'recurrence_frequency': 'Required when is_recurring is True.'}
+                )
+        return attrs
+
+    def create(self, validated_data):
+        request = self.context.get('request')
+        validated_data['agent'] = request.user.agent_profile
+        return super().create(validated_data)
+
+    def update(self, instance, validated_data):
+        new_status = validated_data.get('status')
+        if new_status == 'done' and instance.status != 'done':
+            validated_data['completed_at'] = tz.now()
+        elif new_status and new_status not in ('done', 'in_review'):
+            validated_data['completed_at'] = None
+        return super().update(instance, validated_data)
+
+
 # ── Scheduled Task Link ─────────────────────────────────────
 
 class ScheduledTaskLinkSerializer(serializers.ModelSerializer):
diff --git a/server/api/tests.py b/server/api/tests.py
index abe9107a7..b980bcc8e 100644
--- a/server/api/tests.py
+++ b/server/api/tests.py
@@ -3,6 +3,7 @@ import datetime
 from django.test import TestCase
 from django.core.exceptions import ValidationError
 from django.db import IntegrityError
+from rest_framework.test import APIRequestFactory
 
 from api.models.agent_scheduling import TaskCategory, AgentGlobalTask, ScheduledTaskLink
 from api.models.users import User, Agent
@@ -365,3 +366,162 @@ class AgentGlobalTaskStatusExtensionTest(TestCase):
         )
         task.refresh_from_db()
         self.assertEqual(task.status, 'in_review')
+
+
+# ---------------------------------------------------------------------------
+# Section 06: Serializer and permission tests
+# ---------------------------------------------------------------------------
+
+def make_admin_user():
+    return User.objects.create_user(
+        username='admin06', password='pass', email='admin@test.com', role='admin'
+    )
+
+
+class AgentGlobalTaskReadSerializerTest(TestCase):
+
+    def setUp(self):
+        from api.models.clients import Client
+        user = User.objects.create_user(
+            username='agent06r', password='pass', email='a06r@test.com', role='agent'
+        )
+        self.agent = Agent.objects.create(user=user, department='marketing')
+        self.category = TaskCategory.objects.create(name='Design S6', department='both', color='#fff')
+        self.client_obj = Client.objects.create(
+            name='Cl06', email='cl06@test.com', company='Co06',
+            start_date=datetime.date.today(), status='active',
+        )
+        self.task = AgentGlobalTask.objects.create(
+            agent=self.agent, title='Read test task',
+            client=self.client_obj, task_category_ref=self.category,
+            due_date=datetime.date(2020, 1, 1), status='in_progress',
+        )
+
+    def test_includes_nested_task_category_detail(self):
+        from api.serializers.agent_scheduling import AgentGlobalTaskReadSerializer
+        data = AgentGlobalTaskReadSerializer(self.task).data
+        self.assertIn('task_category_detail', data)
+        self.assertEqual(data['task_category_detail']['name'], 'Design S6')
+
+    def test_includes_client_name(self):
+        from api.serializers.agent_scheduling import AgentGlobalTaskReadSerializer
+        data = AgentGlobalTaskReadSerializer(self.task).data
+        self.assertEqual(data['client_name'], 'Co06')
+
+    def test_is_overdue_true_for_past_due_date(self):
+        from api.serializers.agent_scheduling import AgentGlobalTaskReadSerializer
+        data = AgentGlobalTaskReadSerializer(self.task).data
+        self.assertTrue(data['is_overdue'])
+
+    def test_includes_recurrence_fields(self):
+        from api.serializers.agent_scheduling import AgentGlobalTaskReadSerializer
+        data = AgentGlobalTaskReadSerializer(self.task).data
+        self.assertIn('is_recurring', data)
+        self.assertIn('recurrence_frequency', data)
+        self.assertIn('recurrence_days', data)
+
+
+class AgentGlobalTaskWriteSerializerTest(TestCase):
+
+    def setUp(self):
+        user = User.objects.create_user(
+            username='agent06w', password='pass', email='a06w@test.com', role='agent'
+        )
+        self.agent = Agent.objects.create(user=user, department='marketing')
+        self.review_cat = TaskCategory.objects.create(
+            name='QA S6', department='website', requires_review=True
+        )
+        self.normal_cat = TaskCategory.objects.create(
+            name='Dev S6', department='website', requires_review=False
+        )
+
+    def _make_task(self, status='in_progress', category=None):
+        return AgentGlobalTask.objects.create(
+            agent=self.agent, title='Write test task',
+            status=status, task_category_ref=category,
+        )
+
+    def test_validate_status_redirects_done_to_in_review(self):
+        from api.serializers.agent_scheduling import AgentGlobalTaskWriteSerializer
+        task = self._make_task(status='in_progress', category=self.review_cat)
+        s = AgentGlobalTaskWriteSerializer(task, data={'status': 'done'}, partial=True)
+        self.assertTrue(s.is_valid(), s.errors)
+        self.assertEqual(s.validated_data['status'], 'in_review')
+
+    def test_validate_status_allows_done_from_in_review(self):
+        from api.serializers.agent_scheduling import AgentGlobalTaskWriteSerializer
+        task = self._make_task(status='in_review', category=self.review_cat)
+        s = AgentGlobalTaskWriteSerializer(task, data={'status': 'done'}, partial=True)
+        self.assertTrue(s.is_valid(), s.errors)
+        self.assertEqual(s.validated_data['status'], 'done')
+
+    def test_validate_status_normal_category_allows_done(self):
+        from api.serializers.agent_scheduling import AgentGlobalTaskWriteSerializer
+        task = self._make_task(status='in_progress', category=self.normal_cat)
+        s = AgentGlobalTaskWriteSerializer(task, data={'status': 'done'}, partial=True)
+        self.assertTrue(s.is_valid(), s.errors)
+        self.assertEqual(s.validated_data['status'], 'done')
+
+    def test_validate_recurrence_requires_frequency(self):
+        from api.serializers.agent_scheduling import AgentGlobalTaskWriteSerializer
+        task = self._make_task()
+        s = AgentGlobalTaskWriteSerializer(
+            task, data={'is_recurring': True}, partial=True
+        )
+        self.assertFalse(s.is_valid())
+        self.assertIn('recurrence_frequency', s.errors)
+
+
+class TaskCategorySerializerTest(TestCase):
+
+    def setUp(self):
+        self.category = TaskCategory.objects.create(
+            name='Ser Cat', department='both', color='#abc123', sort_order=3
+        )
+
+    def test_serializes_all_expected_fields(self):
+        from api.serializers.agent_scheduling import TaskCategorySerializer
+        data = TaskCategorySerializer(self.category).data
+        for field in ('id', 'name', 'slug', 'color', 'department', 'requires_review', 'is_active', 'sort_order'):
+            self.assertIn(field, data)
+
+    def test_slug_is_read_only(self):
+        from api.serializers.agent_scheduling import TaskCategorySerializer
+        s = TaskCategorySerializer(self.category, data={'name': 'Ser Cat', 'slug': 'custom-slug', 'department': 'both'})
+        self.assertTrue(s.is_valid(), s.errors)
+        # slug in validated_data should not contain the provided value
+        self.assertNotIn('slug', s.validated_data)
+
+
+class IsAdminPermissionTest(TestCase):
+
+    def setUp(self):
+        self.factory = APIRequestFactory()
+
+    def _request(self, role=None, authenticated=True):
+        request = self.factory.get('/')
+        if authenticated and role:
+            user = User.objects.create_user(
+                username=f'perm_{role}', password='x', email=f'{role}@p.com', role=role
+            )
+            request.user = user
+        else:
+            from django.contrib.auth.models import AnonymousUser
+            request.user = AnonymousUser()
+        return request
+
+    def test_admin_allowed(self):
+        from api.views.agent.scheduling_views import IsAdmin
+        self.assertTrue(IsAdmin().has_permission(self._request('admin'), None))
+
+    def test_agent_denied(self):
+        from api.views.agent.scheduling_views import IsAdmin
+        self.assertFalse(IsAdmin().has_permission(self._request('agent'), None))
+
+    def test_client_denied(self):
+        from api.views.agent.scheduling_views import IsAdmin
+        self.assertFalse(IsAdmin().has_permission(self._request('client'), None))
+
+    def test_unauthenticated_denied(self):
+        from api.views.agent.scheduling_views import IsAdmin
+        self.assertFalse(IsAdmin().has_permission(self._request(authenticated=False), None))
diff --git a/server/api/views/agent/scheduling_views.py b/server/api/views/agent/scheduling_views.py
index 553e6457f..69f96a9e3 100644
--- a/server/api/views/agent/scheduling_views.py
+++ b/server/api/views/agent/scheduling_views.py
@@ -37,6 +37,12 @@ class IsAnyAgent(BasePermission):
         return hasattr(request.user, 'agent_profile')
 
 
+class IsAdmin(BasePermission):
+    """Permission class that allows only admin users."""
+    def has_permission(self, request, view):
+        return request.user.is_authenticated and request.user.role == 'admin'
+
+
 def _get_agent(request):
     return request.user.agent_profile
 
