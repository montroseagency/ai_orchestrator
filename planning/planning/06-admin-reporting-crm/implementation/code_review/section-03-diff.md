diff --git a/server/api/tests.py b/server/api/tests.py
index aa2a8c42c..12536ca6c 100644
--- a/server/api/tests.py
+++ b/server/api/tests.py
@@ -1145,3 +1145,213 @@ class TestNotificationServiceTaskHelpers(TestCase):
         self.assertEqual(call_kwargs['user'], self.agent.user)
         self.assertEqual(call_kwargs['notification_type'], 'task_rejected')
         self.assertIn('Needs more detail', call_kwargs['message'])
+
+
+# ---------------------------------------------------------------------------
+# Section 03: ClientReportView tests
+# ---------------------------------------------------------------------------
+
+class ClientReportViewSection03Test(APITestCase):
+    """Tests for GET /api/agent/clients/{id}/report/"""
+
+    def setUp(self):
+        from django.utils import timezone as tz
+        self.today = datetime.date.today()
+
+        self.agent_user = User.objects.create_user(
+            username='agent03rpt', password='pass', email='agent03rpt@test.com', role='agent'
+        )
+        self.agent = Agent.objects.create(user=self.agent_user, department='marketing')
+
+        self.client_obj = Client.objects.create(
+            name='ReportClient', email='rc03@test.com', company='RC Co',
+            start_date=self.today, status='active',
+            marketing_agent=self.agent,
+        )
+        # Create a different agent so the auto-assign signal won't assign our agent to other_client
+        other_agent_user = User.objects.create_user(
+            username='other_agent03', password='pass', email='other_agent03@test.com', role='agent'
+        )
+        other_agent = Agent.objects.create(user=other_agent_user, department='marketing')
+        self.other_client = Client.objects.create(
+            name='OtherClient03', email='oc03@test.com', company='OC Co',
+            start_date=self.today, status='active',
+            marketing_agent=other_agent,
+        )
+        self.category = TaskCategory.objects.create(name='Copywriting03', department='both')
+        self.category2 = TaskCategory.objects.create(name='Strategy03', department='both')
+
+        self.api_client = APIClient()
+        self.api_client.force_authenticate(user=self.agent_user)
+
+    def _url(self, client_id=None):
+        cid = client_id or self.client_obj.id
+        return f'/api/agent/clients/{cid}/report/'
+
+    def _make_block(self, day_offset=0, start_hour=9, end_hour=10, client=None):
+        return AgentTimeBlock.objects.create(
+            agent=self.agent,
+            client=client or self.client_obj,
+            date=self.today - datetime.timedelta(days=day_offset),
+            start_time=datetime.time(start_hour, 0),
+            end_time=datetime.time(end_hour, 0),
+            block_type='deep_work',
+        )
+
+    def _make_task(self, status='todo', category=None, time_block=None, completed_at=None):
+        kwargs = {
+            'agent': self.agent,
+            'client': self.client_obj,
+            'title': 'Test task',
+            'status': status,
+        }
+        if category:
+            kwargs['task_category_ref'] = category
+        if time_block:
+            kwargs['time_block'] = time_block
+        if completed_at:
+            kwargs['completed_at'] = completed_at
+        return AgentGlobalTask.objects.create(**kwargs)
+
+    # --- Authorization ---
+
+    def test_client_report_returns_403_if_agent_not_assigned_to_client(self):
+        url = f'/api/agent/clients/{self.other_client.id}/report/'
+        response = self.api_client.get(url)
+        self.assertEqual(response.status_code, 403)
+
+    def test_client_report_returns_404_if_client_does_not_exist(self):
+        import uuid
+        url = f'/api/agent/clients/{uuid.uuid4()}/report/'
+        response = self.api_client.get(url)
+        self.assertEqual(response.status_code, 404)
+
+    def test_client_report_returns_403_for_unauthenticated_requests(self):
+        anon = APIClient()
+        response = anon.get(self._url())
+        # DRF returns 401 with JWT auth (WWW-Authenticate header present),
+        # 403 with session-only auth. Either is acceptable — the endpoint is blocked.
+        self.assertIn(response.status_code, [401, 403])
+
+    # --- Aggregation correctness ---
+
+    def test_days_worked_counts_distinct_dates(self):
+        self._make_block(day_offset=0)
+        self._make_block(day_offset=0)   # same date
+        self._make_block(day_offset=1)   # different date
+        response = self.api_client.get(self._url())
+        self.assertEqual(response.status_code, 200)
+        self.assertEqual(response.data['summary']['days_worked'], 2)
+
+    def test_total_hours_sums_duration_minutes_divided_by_60(self):
+        AgentTimeBlock.objects.create(
+            agent=self.agent, client=self.client_obj,
+            date=self.today, start_time=datetime.time(9, 0), end_time=datetime.time(10, 30),
+            block_type='deep_work',
+        )
+        AgentTimeBlock.objects.create(
+            agent=self.agent, client=self.client_obj,
+            date=self.today, start_time=datetime.time(11, 0), end_time=datetime.time(12, 30),
+            block_type='deep_work',
+        )
+        response = self.api_client.get(self._url())
+        self.assertEqual(response.status_code, 200)
+        self.assertEqual(response.data['summary']['total_hours'], 3.0)
+
+    def test_weekly_breakdown_groups_by_iso_week(self):
+        self._make_block(day_offset=0)
+        self._make_block(day_offset=10)
+        response = self.api_client.get(self._url())
+        self.assertEqual(response.status_code, 200)
+        self.assertIn('weekly_breakdown', response.data)
+        self.assertIsInstance(response.data['weekly_breakdown'], list)
+
+    def test_category_breakdown_groups_hours_by_task_category(self):
+        block1 = self._make_block(day_offset=0, start_hour=9, end_hour=11)
+        block2 = self._make_block(day_offset=1, start_hour=9, end_hour=10)
+        self._make_task(category=self.category, time_block=block1)
+        self._make_task(category=self.category2, time_block=block2)
+        response = self.api_client.get(self._url())
+        self.assertEqual(response.status_code, 200)
+        cats = {c['category']: c for c in response.data['category_breakdown']}
+        self.assertIn('Copywriting03', cats)
+        self.assertIn('Strategy03', cats)
+        self.assertEqual(cats['Copywriting03']['task_count'], 1)
+        self.assertEqual(cats['Strategy03']['task_count'], 1)
+
+    def test_tasks_list_filtered_to_date_range(self):
+        from django.utils import timezone as tz
+        in_range_task = self._make_task(status='done', completed_at=tz.now())
+        old_task = self._make_task(status='done')
+        old_task.completed_at = tz.now() - datetime.timedelta(days=91)
+        old_task.created_at = tz.now() - datetime.timedelta(days=91)
+        old_task.save()
+
+        response = self.api_client.get(self._url())
+        self.assertEqual(response.status_code, 200)
+        task_ids = [t['id'] for t in response.data['tasks']]
+        self.assertNotIn(str(old_task.id), task_ids)
+
+    def test_tasks_list_capped_at_200_records(self):
+        from django.utils import timezone as tz
+        for i in range(210):
+            AgentGlobalTask.objects.create(
+                agent=self.agent, client=self.client_obj,
+                title=f'Task {i}', status='todo',
+            )
+        response = self.api_client.get(self._url())
+        self.assertEqual(response.status_code, 200)
+        self.assertLessEqual(len(response.data['tasks']), 200)
+
+    def test_unique_categories_contains_category_names_from_tasks_in_range(self):
+        self._make_task(category=self.category)
+        self._make_task(category=self.category2)
+        response = self.api_client.get(self._url())
+        self.assertEqual(response.status_code, 200)
+        cats = response.data['summary']['unique_categories']
+        self.assertIn('Copywriting03', cats)
+        self.assertIn('Strategy03', cats)
+
+    def test_monthly_summary_groups_by_calendar_month(self):
+        self._make_block(day_offset=0)
+        self._make_block(day_offset=35)
+        response = self.api_client.get(self._url())
+        self.assertEqual(response.status_code, 200)
+        self.assertIn('monthly_summary', response.data)
+        self.assertIsInstance(response.data['monthly_summary'], list)
+
+    # --- Date range defaults ---
+
+    def test_default_date_range_is_last_90_days(self):
+        response = self.api_client.get(self._url())
+        self.assertEqual(response.status_code, 200)
+        expected_start = (self.today - datetime.timedelta(days=90)).isoformat()
+        expected_end = self.today.isoformat()
+        self.assertEqual(response.data['period']['start'], expected_start)
+        self.assertEqual(response.data['period']['end'], expected_end)
+
+    def test_only_end_date_provided_defaults_start_to_90_days_before(self):
+        end = datetime.date(2026, 3, 29)
+        expected_start = (end - datetime.timedelta(days=90)).isoformat()
+        response = self.api_client.get(self._url() + '?end_date=2026-03-29')
+        self.assertEqual(response.status_code, 200)
+        self.assertEqual(response.data['period']['start'], expected_start)
+        self.assertEqual(response.data['period']['end'], '2026-03-29')
+
+    def test_only_start_date_provided_defaults_end_to_today(self):
+        response = self.api_client.get(self._url() + '?start_date=2026-01-01')
+        self.assertEqual(response.status_code, 200)
+        self.assertEqual(response.data['period']['start'], '2026-01-01')
+        self.assertEqual(response.data['period']['end'], self.today.isoformat())
+
+    # --- Performance ---
+
+    def test_report_query_count_is_bounded(self):
+        from django.db import connection
+        from django.test.utils import CaptureQueriesContext
+        self._make_block()
+        self._make_task()
+        with CaptureQueriesContext(connection) as ctx:
+            response = self.api_client.get(self._url())
+        self.assertEqual(response.status_code, 200)
+        self.assertLessEqual(len(ctx), 6, f'Expected ≤ 6 queries, got {len(ctx)}')
diff --git a/server/api/urls.py b/server/api/urls.py
index a0ee0e1f7..4c7b01663 100644
--- a/server/api/urls.py
+++ b/server/api/urls.py
@@ -164,6 +164,9 @@ from .views.agent.scheduling_views import (
     command_center, cross_client_tasks,
 )
 
+# Import client report view (section 03)
+from .views.agent.client_report_views import ClientReportView
+
 # Import push notification views
 from .views.push_views import (
     vapid_public_key, subscribe as push_subscribe,
@@ -542,6 +545,9 @@ urlpatterns = [
     path('agent/schedule/command-center/', command_center, name='agent_command_center'),
     path('agent/schedule/cross-client-tasks/', cross_client_tasks, name='agent_cross_client_tasks'),
 
+    # Agent client report endpoints (section 03)
+    path('agent/clients/<uuid:client_id>/report/', ClientReportView.as_view(), name='agent_client_report'),
+
     # Admin analytics endpoints
     path('admin/analytics/agent-performance/', agent_performance, name='agent_performance'),
     path('admin/analytics/revenue/', revenue_dashboard, name='revenue_dashboard'),
diff --git a/server/api/views/agent/client_report_views.py b/server/api/views/agent/client_report_views.py
new file mode 100644
index 000000000..8ab62748e
--- /dev/null
+++ b/server/api/views/agent/client_report_views.py
@@ -0,0 +1,239 @@
+"""
+Client Report API — aggregates AgentTimeBlock + AgentGlobalTask data
+for a single client over a configurable date range.
+
+GET /agent/clients/{id}/report/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
+Auth: IsAuthenticated + IsAnyAgent (agent must be assigned to the client)
+"""
+from collections import defaultdict
+from datetime import date, timedelta, datetime as dt
+
+from django.db.models import Q
+from django.shortcuts import get_object_or_404
+from rest_framework.exceptions import ValidationError
+from rest_framework.permissions import IsAuthenticated
+from rest_framework.response import Response
+from rest_framework.views import APIView
+
+from api.models import AgentTimeBlock, AgentGlobalTask, Client
+from api.views.agent.scheduling_views import IsAnyAgent, _get_agent
+
+
+def _is_agent_assigned_to_client(agent, client):
+    """Return True if agent is assigned to client (marketing or website)."""
+    if agent.department == 'marketing':
+        return client.marketing_agent_id == agent.pk
+    elif agent.department == 'website':
+        return client.website_agent_id == agent.pk
+    return False
+
+
+def _parse_date_range(request):
+    """Parse start_date / end_date from query params with defaults.
+
+    - No params → (today - 90d, today)
+    - Only end_date → (end_date - 90d, end_date)
+    - Only start_date → (start_date, today)
+    Raises ValidationError (400) on bad date format.
+    """
+    today = date.today()
+    raw_start = request.query_params.get('start_date')
+    raw_end = request.query_params.get('end_date')
+
+    def _parse(s):
+        try:
+            return date.fromisoformat(s)
+        except ValueError:
+            raise ValidationError({'detail': f'Invalid date format: {s!r}. Use YYYY-MM-DD.'})
+
+    if raw_start and raw_end:
+        return _parse(raw_start), _parse(raw_end)
+    elif raw_start:
+        return _parse(raw_start), today
+    elif raw_end:
+        end = _parse(raw_end)
+        return end - timedelta(days=90), end
+    else:
+        return today - timedelta(days=90), today
+
+
+def _block_duration_minutes(start_time, end_time):
+    """Compute duration in minutes between two time objects."""
+    start = dt.combine(date.today(), start_time)
+    end = dt.combine(date.today(), end_time)
+    if end < start:
+        end += timedelta(days=1)
+    return int((end - start).total_seconds() / 60)
+
+
+class ClientReportView(APIView):
+    """Aggregate time and task data for a single client over a date range.
+
+    Returns 403 if the requesting agent is not assigned to the client.
+    Returns 404 if the client UUID does not exist.
+    """
+    permission_classes = [IsAuthenticated, IsAnyAgent]
+
+    def get(self, request, client_id):
+        agent = _get_agent(request)
+        start_date, end_date = _parse_date_range(request)
+
+        # 1. Fetch client (404 if missing)
+        client = get_object_or_404(Client, id=client_id)
+
+        # 2. Authorization check
+        if not _is_agent_assigned_to_client(agent, client):
+            return Response({'detail': 'Forbidden.'}, status=403)
+
+        # 3. Fetch time blocks in range (use .values() to avoid instantiating model objects)
+        time_blocks = list(
+            AgentTimeBlock.objects.filter(
+                client=client,
+                date__range=(start_date, end_date),
+            ).values('id', 'date', 'start_time', 'end_time')
+        )
+
+        # 4. Fetch all tasks in range (used for both aggregation and the tasks list)
+        tasks_qs = (
+            AgentGlobalTask.objects.filter(client=client)
+            .filter(
+                Q(created_at__date__range=(start_date, end_date))
+                | Q(completed_at__date__range=(start_date, end_date))
+            )
+            .select_related('task_category_ref', 'time_block')
+            .order_by('-completed_at', '-created_at')
+        )
+        all_tasks = list(tasks_qs)
+        tasks_list = all_tasks[:200]
+
+        # --- Summary ---
+        total_tasks = len(all_tasks)
+        completed_tasks = sum(1 for t in all_tasks if t.status == 'done')
+        in_progress_tasks = sum(1 for t in all_tasks if t.status == 'in_progress')
+
+        dates_worked = {b['date'] for b in time_blocks}
+        days_worked = len(dates_worked)
+
+        total_minutes = sum(
+            _block_duration_minutes(b['start_time'], b['end_time'])
+            for b in time_blocks
+        )
+        total_hours = round(total_minutes / 60, 2)
+
+        unique_categories = sorted({
+            t.task_category_ref.name
+            for t in all_tasks
+            if t.task_category_ref
+        })
+
+        # --- Duration map: time_block id → minutes ---
+        tb_duration = {
+            b['id']: _block_duration_minutes(b['start_time'], b['end_time'])
+            for b in time_blocks
+        }
+
+        # --- Category breakdown ---
+        cat_data = defaultdict(lambda: {'task_count': 0, 'minutes': 0})
+        for task in all_tasks:
+            cat_name = task.task_category_ref.name if task.task_category_ref else 'Uncategorized'
+            cat_data[cat_name]['task_count'] += 1
+            if task.time_block_id and task.time_block_id in tb_duration:
+                cat_data[cat_name]['minutes'] += tb_duration[task.time_block_id]
+
+        category_breakdown = [
+            {
+                'category': cat,
+                'hours': round(data['minutes'] / 60, 2),
+                'task_count': data['task_count'],
+            }
+            for cat, data in sorted(cat_data.items())
+        ]
+
+        # --- Weekly breakdown ---
+        week_minutes = defaultdict(int)
+        week_tasks_completed = defaultdict(int)
+
+        for b in time_blocks:
+            block_date = b['date']
+            week_start = block_date - timedelta(days=block_date.weekday())
+            week_minutes[week_start] += _block_duration_minutes(b['start_time'], b['end_time'])
+
+        for task in all_tasks:
+            if task.status == 'done' and task.completed_at:
+                task_date = task.completed_at.date()
+                if start_date <= task_date <= end_date:
+                    week_start = task_date - timedelta(days=task_date.weekday())
+                    week_tasks_completed[week_start] += 1
+
+        all_week_starts = sorted(set(list(week_minutes.keys()) + list(week_tasks_completed.keys())))
+        weekly_breakdown = [
+            {
+                'week_start': w.isoformat(),
+                'hours': round(week_minutes[w] / 60, 2),
+                'tasks_completed': week_tasks_completed[w],
+            }
+            for w in all_week_starts
+        ]
+
+        # --- Monthly summary ---
+        month_data = defaultdict(lambda: {'minutes': 0, 'days': set(), 'tasks_completed': 0})
+
+        for b in time_blocks:
+            block_date = b['date']
+            month_key = block_date.strftime('%Y-%m')
+            month_data[month_key]['minutes'] += _block_duration_minutes(b['start_time'], b['end_time'])
+            month_data[month_key]['days'].add(block_date)
+
+        for task in all_tasks:
+            if task.status == 'done' and task.completed_at:
+                task_date = task.completed_at.date()
+                if start_date <= task_date <= end_date:
+                    month_key = task_date.strftime('%Y-%m')
+                    month_data[month_key]['tasks_completed'] += 1
+
+        monthly_summary = [
+            {
+                'month': month_key,
+                'days': len(data['days']),
+                'hours': round(data['minutes'] / 60, 2),
+                'tasks_completed': data['tasks_completed'],
+            }
+            for month_key, data in sorted(month_data.items())
+        ]
+
+        # --- Tasks list ---
+        tasks_response = [
+            {
+                'id': str(task.id),
+                'title': task.title,
+                'status': task.status,
+                'category': task.task_category_ref.name if task.task_category_ref else None,
+                'hours_spent': round(tb_duration.get(task.time_block_id, 0) / 60, 2),
+                'completed_at': task.completed_at.date().isoformat() if task.completed_at else None,
+            }
+            for task in tasks_list
+        ]
+
+        return Response({
+            'client': {
+                'id': str(client.id),
+                'name': client.name,
+                'company': client.company,
+            },
+            'period': {
+                'start': start_date.isoformat(),
+                'end': end_date.isoformat(),
+            },
+            'summary': {
+                'total_tasks': total_tasks,
+                'completed_tasks': completed_tasks,
+                'in_progress_tasks': in_progress_tasks,
+                'total_hours': total_hours,
+                'days_worked': days_worked,
+                'unique_categories': unique_categories,
+            },
+            'category_breakdown': category_breakdown,
+            'weekly_breakdown': weekly_breakdown,
+            'monthly_summary': monthly_summary,
+            'tasks': tasks_response,
+        })
