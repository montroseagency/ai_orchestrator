diff --git a/server/api/services/pdf_service.py b/server/api/services/pdf_service.py
index 434b07ebf..e8b977d5a 100644
--- a/server/api/services/pdf_service.py
+++ b/server/api/services/pdf_service.py
@@ -957,3 +957,191 @@ class PDFService:
 
         quote.pdf_file.save(filename, ContentFile(pdf_content), save=True)
         return quote.pdf_file.path
+
+    # ─── Client Report PDF ────────────────────────────────────────────────────
+
+    @staticmethod
+    def _build_weekly_chart_svg(weekly_breakdown: list, width: int = 400, height: int = 120) -> str:
+        """Build an inline SVG bar chart from weekly breakdown data.
+
+        Each entry: {'week_start': str, 'hours': float}
+        Returns SVG string to embed directly in HTML, or empty string if no data.
+        """
+        if not weekly_breakdown:
+            return ''
+
+        max_hours = max((w['hours'] for w in weekly_breakdown), default=0)
+        if max_hours == 0:
+            return ''
+
+        n = len(weekly_breakdown)
+        bar_area_width = width - 60
+        bar_w = max(4, bar_area_width // n - 4)
+        chart_height = height - 30
+
+        bars = []
+        for i, w in enumerate(weekly_breakdown):
+            bar_h = int((w['hours'] / max_hours) * chart_height)
+            x = 40 + i * (bar_area_width // n)
+            y = chart_height - bar_h + 5
+            label = w['week_start'][5:]  # MM-DD
+            bars.append(
+                f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h}" fill="#2563eb" rx="2"/>'
+                f'<text x="{x + bar_w // 2}" y="{height - 5}" text-anchor="middle" '
+                f'font-size="8" fill="#64748b">{label}</text>'
+                f'<text x="{x + bar_w // 2}" y="{y - 2}" text-anchor="middle" '
+                f'font-size="8" fill="#1e293b">{w["hours"]:.1f}</text>'
+            )
+
+        return (
+            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
+            f'viewBox="0 0 {width} {height}">'
+            + ''.join(bars)
+            + '</svg>'
+        )
+
+    @staticmethod
+    def _render_report_html(report_data: dict, client, period: dict) -> str:
+        """Render client report to HTML string for WeasyPrint."""
+        company = PDFService.COMPANY_INFO
+        colors = PDFService.COLORS
+
+        logo_base64 = PDFService.get_logo_base64()
+        logo_html = (
+            f'<img src="data:image/png;base64,{logo_base64}" alt="{company["name"]}" style="height:40px;">'
+            if logo_base64
+            else f'<span style="font-weight:bold;font-size:1.2em;">{company["name"]}</span>'
+        )
+
+        summary = report_data.get('summary', {})
+        weekly = report_data.get('weekly_breakdown', [])
+        monthly = report_data.get('monthly_summary', [])
+        tasks = report_data.get('tasks', [])[:100]
+        total_tasks = summary.get('total_tasks', 0)
+        show_truncation = total_tasks > 100
+
+        svg_chart = PDFService._build_weekly_chart_svg(weekly)
+
+        monthly_rows = ''.join(
+            f'<tr><td>{m["month"]}</td><td>{m["days"]}</td>'
+            f'<td>{m["hours"]:.2f}</td><td>{m["tasks_completed"]}</td></tr>'
+            for m in monthly
+        )
+
+        task_rows = ''.join(
+            f'<tr><td>{t["title"]}</td><td>{t["status"].replace("_", " ").title()}</td>'
+            f'<td>{t["category"] or ""}</td>'
+            f'<td>{t["completed_at"] or t.get("created_at", "")}</td>'
+            f'<td>{t["hours_spent"]:.2f}</td></tr>'
+            for t in tasks
+        )
+
+        truncation_note = (
+            '<p style="color:#64748b;font-style:italic;">'
+            f'Showing first 100 tasks. Export as CSV for complete list ({total_tasks} total).'
+            '</p>'
+            if show_truncation else ''
+        )
+
+        from datetime import date as _date
+        generated = _date.today().isoformat()
+
+        primary = colors['primary']
+        secondary = colors['secondary']
+        text = colors['text']
+        muted = colors['muted']
+        light_bg = colors['light_bg']
+        border = colors['border']
+
+        return f"""<!DOCTYPE html>
+<html>
+<head>
+<meta charset="utf-8">
+<style>
+  body {{ font-family: Arial, sans-serif; color: {text}; font-size: 12px; margin: 0; padding: 20px; }}
+  .header {{ display: flex; justify-content: space-between; align-items: flex-start;
+             border-bottom: 3px solid {primary}; padding-bottom: 12px; margin-bottom: 20px; }}
+  .report-title {{ color: {primary}; font-size: 22px; font-weight: bold; }}
+  .client-info {{ color: {muted}; font-size: 11px; margin-top: 4px; }}
+  .stats-grid {{ display: flex; gap: 16px; margin: 16px 0; }}
+  .stat-box {{ background: {light_bg}; border: 1px solid {border};
+               border-radius: 6px; padding: 12px; flex: 1; text-align: center; }}
+  .stat-val {{ font-size: 20px; font-weight: bold; color: {secondary}; }}
+  .stat-lbl {{ font-size: 10px; color: {muted}; margin-top: 4px; }}
+  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
+  th {{ background: {primary}; color: white; padding: 6px 8px; text-align: left; font-size: 11px; }}
+  td {{ padding: 5px 8px; border-bottom: 1px solid {border}; font-size: 11px; }}
+  tr:nth-child(even) td {{ background: {light_bg}; }}
+  h3 {{ color: {primary}; font-size: 14px; margin: 16px 0 6px; }}
+  .chart {{ margin: 8px 0 16px; }}
+  .footer {{ border-top: 1px solid {border}; margin-top: 24px; padding-top: 8px;
+             font-size: 10px; color: {muted}; text-align: center; }}
+</style>
+</head>
+<body>
+<div class="header">
+  <div>
+    {logo_html}
+    <div class="report-title">Client Report</div>
+    <div class="client-info">{client.name or ''} — {client.company or ''}</div>
+    <div class="client-info">Period: {period['start']} to {period['end']}</div>
+  </div>
+  <div style="text-align:right;font-size:10px;color:{muted};">{company['name']}<br>{company['website']}</div>
+</div>
+
+<div class="stats-grid">
+  <div class="stat-box"><div class="stat-val">{summary.get('total_tasks', 0)}</div><div class="stat-lbl">Total Tasks</div></div>
+  <div class="stat-box"><div class="stat-val">{summary.get('completed_tasks', 0)}</div><div class="stat-lbl">Completed</div></div>
+  <div class="stat-box"><div class="stat-val">{summary.get('in_progress_tasks', 0)}</div><div class="stat-lbl">In Progress</div></div>
+  <div class="stat-box"><div class="stat-val">{summary.get('total_hours', 0):.1f}h</div><div class="stat-lbl">Total Hours</div></div>
+  <div class="stat-box"><div class="stat-val">{summary.get('days_worked', 0)}</div><div class="stat-lbl">Days Worked</div></div>
+</div>
+
+<h3>Weekly Hours</h3>
+<div class="chart">{svg_chart}</div>
+
+<h3>Monthly Breakdown</h3>
+<table>
+  <tr><th>Month</th><th>Days Worked</th><th>Hours</th><th>Tasks Completed</th></tr>
+  {monthly_rows}
+</table>
+
+<h3>Task List</h3>
+{truncation_note}
+<table>
+  <tr><th>Task Title</th><th>Status</th><th>Category</th><th>Date</th><th>Hours Spent</th></tr>
+  {task_rows}
+</table>
+
+<div class="footer">
+  {company['name']} · {company['website']} · {company['email']} · {company['phone']} · Generated {generated}
+</div>
+</body>
+</html>"""
+
+    @staticmethod
+    def generate_client_report_pdf(report_data: dict, client, period: dict) -> bytes:
+        """Generate branded PDF client report using WeasyPrint.
+
+        Falls back to minimal valid PDF bytes if WeasyPrint is unavailable.
+        """
+        _FALLBACK = (
+            b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n'
+            b'2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n'
+            b'3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R>>endobj\n'
+            b'xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n'
+            b'0000000058 00000 n\n0000000115 00000 n\n'
+            b'trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF'
+        )
+        try:
+            from weasyprint import HTML
+        except ImportError:
+            logger.warning("WeasyPrint not installed; returning fallback PDF bytes for client report")
+            return _FALLBACK
+
+        html_content = PDFService._render_report_html(report_data, client, period)
+        try:
+            return HTML(string=html_content).write_pdf()
+        except Exception as exc:
+            logger.error("WeasyPrint failed to generate client report PDF: %s", exc)
+            return _FALLBACK
diff --git a/server/api/tests.py b/server/api/tests.py
index feca869c7..25dcac856 100644
--- a/server/api/tests.py
+++ b/server/api/tests.py
@@ -1860,3 +1860,111 @@ class AdminCategoryManagementAPITests(APITestCase):
         self.assertNotIn(str(self.cat_inactive.id), ids)
         self.assertIn(str(self.cat1.id), ids)
 
+
+
+# ---------------------------------------------------------------------------
+# Section 07: Export API
+# ---------------------------------------------------------------------------
+
+class ClientReportExportViewTests(APITestCase):
+
+    def setUp(self):
+        agent_user = User.objects.create_user(
+            username='export_agent', password='x', email='export_agent@t.com', role='agent'
+        )
+        self.agent = Agent.objects.create(user=agent_user, department='marketing')
+        self.client_obj = Client.objects.create(
+            name='Export Client', company='Export Co', email='export@t.com',
+            start_date=datetime.date.today(), status='active',
+            marketing_agent=self.agent,
+        )
+        self.api = APIClient()
+        self.api.force_authenticate(user=agent_user)
+
+        # Other agent — not assigned to client
+        other_user = User.objects.create_user(
+            username='other_export_agent', password='x', email='other_export@t.com', role='agent'
+        )
+        other_agent = Agent.objects.create(user=other_user, department='marketing')
+        self.other_api = APIClient()
+        self.other_api.force_authenticate(user=other_user)
+
+        # Create a task in range
+        self.task = AgentGlobalTask.objects.create(
+            agent=self.agent,
+            client=self.client_obj,
+            title='Export Task',
+            status=AgentGlobalTask.Status.DONE,
+        )
+
+    def _export_url(self):
+        return f'/api/agent/clients/{self.client_obj.id}/report/export/'
+
+    def test_csv_export_returns_text_csv_content_type(self):
+        response = self.api.get(self._export_url(), {'file_format': 'csv'})
+        self.assertEqual(response.status_code, 200)
+        self.assertIn('text/csv', response['Content-Type'])
+
+    def test_csv_export_returns_attachment_content_disposition(self):
+        response = self.api.get(self._export_url(), {'file_format': 'csv'})
+        self.assertEqual(response.status_code, 200)
+        self.assertIn('attachment', response.get('Content-Disposition', ''))
+
+    def test_csv_filename_includes_client_name(self):
+        response = self.api.get(self._export_url(), {'file_format': 'csv'})
+        self.assertEqual(response.status_code, 200)
+        cd = response.get('Content-Disposition', '')
+        self.assertIn('.csv', cd)
+
+    def test_csv_rows_contain_expected_columns(self):
+        response = self.api.get(self._export_url(), {'file_format': 'csv'})
+        self.assertEqual(response.status_code, 200)
+        content = b''.join(response.streaming_content).decode('utf-8')
+        self.assertIn('Task Title', content)
+        self.assertIn('Status', content)
+        self.assertIn('Category', content)
+        self.assertIn('Client', content)
+        self.assertIn('Hours Spent', content)
+        self.assertIn('Agent', content)
+
+    def test_pdf_export_returns_application_pdf_content_type(self):
+        with unittest.mock.patch(
+            'api.services.pdf_service.PDFService.generate_client_report_pdf',
+            return_value=b'%PDF-1.4 fake'
+        ):
+            response = self.api.get(self._export_url(), {'file_format': 'pdf'})
+        self.assertEqual(response.status_code, 200)
+        self.assertIn('application/pdf', response['Content-Type'])
+
+    def test_pdf_export_calls_generate_client_report_pdf(self):
+        with unittest.mock.patch(
+            'api.services.pdf_service.PDFService.generate_client_report_pdf',
+            return_value=b'%PDF-1.4 fake'
+        ) as mock_pdf:
+            self.api.get(self._export_url(), {'file_format': 'pdf'})
+        mock_pdf.assert_called_once()
+
+    def test_export_returns_403_if_agent_not_assigned(self):
+        response = self.other_api.get(self._export_url(), {'file_format': 'csv'})
+        self.assertEqual(response.status_code, 403)
+
+    def test_export_returns_400_for_invalid_format(self):
+        response = self.api.get(self._export_url(), {'file_format': 'xls'})
+        self.assertEqual(response.status_code, 400)
+
+    def test_export_returns_400_for_missing_format(self):
+        response = self.api.get(self._export_url())
+        self.assertEqual(response.status_code, 400)
+
+    def test_export_returns_404_if_client_does_not_exist(self):
+        response = self.api.get(f'/api/agent/clients/{uuid.uuid4()}/report/export/', {'file_format': 'csv'})
+        self.assertEqual(response.status_code, 404)
+
+    def test_pdf_export_returns_non_empty_bytes(self):
+        with unittest.mock.patch(
+            'api.services.pdf_service.PDFService.generate_client_report_pdf',
+            return_value=b'%PDF-1.4 fake'
+        ):
+            response = self.api.get(self._export_url(), {'file_format': 'pdf'})
+        self.assertEqual(response.status_code, 200)
+        self.assertGreater(len(response.content), 0)
diff --git a/server/api/urls.py b/server/api/urls.py
index d55005639..840307067 100644
--- a/server/api/urls.py
+++ b/server/api/urls.py
@@ -165,7 +165,7 @@ from .views.agent.scheduling_views import (
 )
 
 # Import client report view (section 03)
-from .views.agent.client_report_views import ClientReportView
+from .views.agent.client_report_views import ClientReportView, ClientReportExportView
 
 # Import marketing plan views (section 04)
 from .views.agent.marketing_plan_views import (
@@ -556,8 +556,9 @@ urlpatterns = [
     path('agent/schedule/command-center/', command_center, name='agent_command_center'),
     path('agent/schedule/cross-client-tasks/', cross_client_tasks, name='agent_cross_client_tasks'),
 
-    # Agent client report endpoints (section 03)
+    # Agent client report endpoints (sections 03, 07)
     path('agent/clients/<uuid:client_id>/report/', ClientReportView.as_view(), name='agent_client_report'),
+    path('agent/clients/<uuid:client_id>/report/export/', ClientReportExportView.as_view(), name='agent_client_report_export'),
 
     # Marketing plan endpoints (section 04)
     path('agent/clients/<uuid:client_id>/marketing-plan/', AgentClientMarketingPlanView.as_view(), name='agent_client_marketing_plan'),
diff --git a/server/api/views/agent/client_report_views.py b/server/api/views/agent/client_report_views.py
index e4da56206..f12d71c07 100644
--- a/server/api/views/agent/client_report_views.py
+++ b/server/api/views/agent/client_report_views.py
@@ -3,14 +3,17 @@ Client Report API — aggregates AgentTimeBlock + AgentGlobalTask data
 for a single client over a configurable date range.
 
 GET /agent/clients/{id}/report/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
+GET /agent/clients/{id}/report/export/?format=csv|pdf&start_date=...&end_date=...
 Auth: IsAuthenticated + IsAnyAgent (agent must be assigned to the client)
 """
+import csv
 from collections import defaultdict
 from datetime import date, timedelta, datetime as dt
 
 from django.db.models import Q
+from django.http import StreamingHttpResponse, HttpResponse
 from django.shortcuts import get_object_or_404
-from rest_framework.exceptions import ValidationError
+from rest_framework.exceptions import ValidationError, PermissionDenied
 from rest_framework.permissions import IsAuthenticated
 from rest_framework.response import Response
 from rest_framework.views import APIView
@@ -28,6 +31,20 @@ def _is_agent_assigned_to_client(agent, client):
     return False
 
 
+def _get_authorized_client(request, client_id):
+    """Fetch Client by UUID and verify the requesting agent is assigned to it.
+
+    Returns the Client instance.
+    Raises Http404 if client does not exist.
+    Raises PermissionDenied (403) if the agent is not assigned to this client.
+    """
+    client = get_object_or_404(Client, id=client_id)
+    agent = _get_agent(request)
+    if not _is_agent_assigned_to_client(agent, client):
+        raise PermissionDenied('You are not assigned to this client.')
+    return client, agent
+
+
 def _parse_date_range(request):
     """Parse start_date / end_date from query params with defaults.
 
@@ -69,6 +86,136 @@ def _block_duration_minutes(block_date, start_time, end_time):
     return int((end - start).total_seconds() / 60)
 
 
+def _build_report_data(client, start_date, end_date):
+    """Aggregate time block and task data for a client over a date range.
+
+    Returns a dict matching the ClientReportData structure (same shape as the
+    JSON response from ClientReportView). The tasks list is uncapped — callers
+    must apply any display limits themselves.
+    """
+    # Fetch time blocks in range
+    time_blocks = list(
+        AgentTimeBlock.objects.filter(
+            client=client,
+            date__range=(start_date, end_date),
+        ).values('id', 'date', 'start_time', 'end_time')
+    )
+
+    # Fetch all tasks in range
+    tasks_qs = (
+        AgentGlobalTask.objects.filter(client=client)
+        .filter(
+            Q(created_at__date__range=(start_date, end_date))
+            | Q(completed_at__date__range=(start_date, end_date))
+        )
+        .select_related('task_category_ref', 'time_block')
+        .order_by('-completed_at', '-created_at')
+    )
+    all_tasks = list(tasks_qs)
+
+    # Summary
+    total_tasks = len(all_tasks)
+    completed_tasks = sum(1 for t in all_tasks if t.status == 'done')
+    in_progress_tasks = sum(1 for t in all_tasks if t.status == 'in_progress')
+    dates_worked = {b['date'] for b in time_blocks}
+    days_worked = len(dates_worked)
+    total_minutes = sum(
+        _block_duration_minutes(b['date'], b['start_time'], b['end_time'])
+        for b in time_blocks
+    )
+    total_hours = round(total_minutes / 60, 2)
+    unique_categories = sorted({
+        t.task_category_ref.name for t in all_tasks if t.task_category_ref
+    })
+
+    # Duration map: time_block id → minutes
+    tb_duration = {
+        b['id']: _block_duration_minutes(b['date'], b['start_time'], b['end_time'])
+        for b in time_blocks
+    }
+
+    # Category breakdown
+    cat_data = defaultdict(lambda: {'task_count': 0, 'minutes': 0})
+    for task in all_tasks:
+        cat_name = task.task_category_ref.name if task.task_category_ref else 'Uncategorized'
+        cat_data[cat_name]['task_count'] += 1
+        if task.time_block_id and task.time_block_id in tb_duration:
+            cat_data[cat_name]['minutes'] += tb_duration[task.time_block_id]
+
+    category_breakdown = [
+        {'category': cat, 'hours': round(data['minutes'] / 60, 2), 'task_count': data['task_count']}
+        for cat, data in sorted(cat_data.items())
+    ]
+
+    # Weekly breakdown
+    week_minutes = defaultdict(int)
+    week_tasks_completed = defaultdict(int)
+    for b in time_blocks:
+        block_date = b['date']
+        week_start = block_date - timedelta(days=block_date.weekday())
+        week_minutes[week_start] += _block_duration_minutes(block_date, b['start_time'], b['end_time'])
+    for task in all_tasks:
+        if task.status == 'done' and task.completed_at:
+            task_date = task.completed_at.date()
+            if start_date <= task_date <= end_date:
+                week_start = task_date - timedelta(days=task_date.weekday())
+                week_tasks_completed[week_start] += 1
+
+    all_week_starts = sorted(set(list(week_minutes.keys()) + list(week_tasks_completed.keys())))
+    weekly_breakdown = [
+        {'week_start': w.isoformat(), 'hours': round(week_minutes[w] / 60, 2), 'tasks_completed': week_tasks_completed[w]}
+        for w in all_week_starts
+    ]
+
+    # Monthly summary
+    month_data = defaultdict(lambda: {'minutes': 0, 'days': set(), 'tasks_completed': 0})
+    for b in time_blocks:
+        block_date = b['date']
+        month_key = block_date.strftime('%Y-%m')
+        month_data[month_key]['minutes'] += _block_duration_minutes(block_date, b['start_time'], b['end_time'])
+        month_data[month_key]['days'].add(block_date)
+    for task in all_tasks:
+        if task.status == 'done' and task.completed_at:
+            task_date = task.completed_at.date()
+            if start_date <= task_date <= end_date:
+                month_key = task_date.strftime('%Y-%m')
+                month_data[month_key]['tasks_completed'] += 1
+
+    monthly_summary = [
+        {'month': month_key, 'days': len(data['days']), 'hours': round(data['minutes'] / 60, 2), 'tasks_completed': data['tasks_completed']}
+        for month_key, data in sorted(month_data.items())
+    ]
+
+    # Tasks list (uncapped)
+    tasks_list = [
+        {
+            'id': str(task.id),
+            'title': task.title,
+            'status': task.status,
+            'category': task.task_category_ref.name if task.task_category_ref else None,
+            'hours_spent': round(tb_duration.get(task.time_block_id, 0) / 60, 2),
+            'completed_at': task.completed_at.date().isoformat() if task.completed_at else None,
+            'created_at': task.created_at.date().isoformat() if task.created_at else None,
+        }
+        for task in all_tasks
+    ]
+
+    return {
+        'summary': {
+            'total_tasks': total_tasks,
+            'completed_tasks': completed_tasks,
+            'in_progress_tasks': in_progress_tasks,
+            'total_hours': total_hours,
+            'days_worked': days_worked,
+            'unique_categories': unique_categories,
+        },
+        'category_breakdown': category_breakdown,
+        'weekly_breakdown': weekly_breakdown,
+        'monthly_summary': monthly_summary,
+        'tasks': tasks_list,
+    }
+
+
 class ClientReportView(APIView):
     """Aggregate time and task data for a single client over a date range.
 
@@ -78,165 +225,86 @@ class ClientReportView(APIView):
     permission_classes = [IsAuthenticated, IsAnyAgent]
 
     def get(self, request, client_id):
-        agent = _get_agent(request)
         start_date, end_date = _parse_date_range(request)
+        client, _agent = _get_authorized_client(request, client_id)
+        report = _build_report_data(client, start_date, end_date)
 
-        # 1. Fetch client (404 if missing)
-        client = get_object_or_404(Client, id=client_id)
+        return Response({
+            'client': {'id': str(client.id), 'name': client.name, 'company': client.company},
+            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
+            **report,
+            'tasks': report['tasks'][:200],  # JSON view caps at 200
+        })
 
-        # 2. Authorization check
-        if not _is_agent_assigned_to_client(agent, client):
-            return Response({'detail': 'Forbidden.'}, status=403)
 
-        # 3. Fetch time blocks in range (use .values() to avoid instantiating model objects)
-        time_blocks = list(
-            AgentTimeBlock.objects.filter(
-                client=client,
-                date__range=(start_date, end_date),
-            ).values('id', 'date', 'start_time', 'end_time')
-        )
+class _Echo:
+    """File-like object that returns the value passed to write() — used for StreamingHttpResponse CSV."""
+    def write(self, value):
+        return value
 
-        # 4. Fetch all tasks in range (used for both aggregation and the tasks list)
-        tasks_qs = (
-            AgentGlobalTask.objects.filter(client=client)
-            .filter(
-                Q(created_at__date__range=(start_date, end_date))
-                | Q(completed_at__date__range=(start_date, end_date))
-            )
-            .select_related('task_category_ref', 'time_block')
-            .order_by('-completed_at', '-created_at')
-        )
-        all_tasks = list(tasks_qs)
-        tasks_list = all_tasks[:200]
 
-        # --- Summary ---
-        total_tasks = len(all_tasks)
-        completed_tasks = sum(1 for t in all_tasks if t.status == 'done')
-        in_progress_tasks = sum(1 for t in all_tasks if t.status == 'in_progress')
+def _stream_csv_rows(tasks, client_name, agent_name):
+    """Generator yielding CSV rows: header first, then one row per task."""
+    pseudo_buffer = _Echo()
+    writer = csv.writer(pseudo_buffer)
+    yield writer.writerow(['Task Title', 'Status', 'Category', 'Client', 'Date', 'Hours Spent', 'Agent'])
+    for task in tasks:
+        date_val = task.get('completed_at') or task.get('created_at') or ''
+        yield writer.writerow([
+            task['title'],
+            task['status'],
+            task['category'] or '',
+            client_name,
+            date_val,
+            f"{task['hours_spent']:.2f}",
+            agent_name,
+        ])
 
-        dates_worked = {b['date'] for b in time_blocks}
-        days_worked = len(dates_worked)
 
-        total_minutes = sum(
-            _block_duration_minutes(b['date'], b['start_time'], b['end_time'])
-            for b in time_blocks
-        )
-        total_hours = round(total_minutes / 60, 2)
+class ClientReportExportView(APIView):
+    """Export a client report as CSV or PDF.
 
-        unique_categories = sorted({
-            t.task_category_ref.name
-            for t in all_tasks
-            if t.task_category_ref
-        })
+    GET /agent/clients/{id}/report/export/?file_format=csv|pdf&start_date=...&end_date=...
 
-        # --- Duration map: time_block id → minutes ---
-        tb_duration = {
-            b['id']: _block_duration_minutes(b['date'], b['start_time'], b['end_time'])
-            for b in time_blocks
-        }
+    Uses `file_format` (not `format`) to avoid conflict with DRF's URL_FORMAT_OVERRIDE
+    which intercepts `?format=` for content negotiation before the view runs.
+    """
+    permission_classes = [IsAuthenticated, IsAnyAgent]
 
-        # --- Category breakdown ---
-        cat_data = defaultdict(lambda: {'task_count': 0, 'minutes': 0})
-        for task in all_tasks:
-            cat_name = task.task_category_ref.name if task.task_category_ref else 'Uncategorized'
-            cat_data[cat_name]['task_count'] += 1
-            if task.time_block_id and task.time_block_id in tb_duration:
-                cat_data[cat_name]['minutes'] += tb_duration[task.time_block_id]
-
-        category_breakdown = [
-            {
-                'category': cat,
-                'hours': round(data['minutes'] / 60, 2),
-                'task_count': data['task_count'],
-            }
-            for cat, data in sorted(cat_data.items())
-        ]
-
-        # --- Weekly breakdown ---
-        week_minutes = defaultdict(int)
-        week_tasks_completed = defaultdict(int)
-
-        for b in time_blocks:
-            block_date = b['date']
-            week_start = block_date - timedelta(days=block_date.weekday())
-            week_minutes[week_start] += _block_duration_minutes(block_date, b['start_time'], b['end_time'])
-
-        for task in all_tasks:
-            if task.status == 'done' and task.completed_at:
-                task_date = task.completed_at.date()
-                if start_date <= task_date <= end_date:
-                    week_start = task_date - timedelta(days=task_date.weekday())
-                    week_tasks_completed[week_start] += 1
-
-        all_week_starts = sorted(set(list(week_minutes.keys()) + list(week_tasks_completed.keys())))
-        weekly_breakdown = [
-            {
-                'week_start': w.isoformat(),
-                'hours': round(week_minutes[w] / 60, 2),
-                'tasks_completed': week_tasks_completed[w],
-            }
-            for w in all_week_starts
-        ]
-
-        # --- Monthly summary ---
-        month_data = defaultdict(lambda: {'minutes': 0, 'days': set(), 'tasks_completed': 0})
-
-        for b in time_blocks:
-            block_date = b['date']
-            month_key = block_date.strftime('%Y-%m')
-            month_data[month_key]['minutes'] += _block_duration_minutes(block_date, b['start_time'], b['end_time'])
-            month_data[month_key]['days'].add(block_date)
-
-        for task in all_tasks:
-            if task.status == 'done' and task.completed_at:
-                task_date = task.completed_at.date()
-                if start_date <= task_date <= end_date:
-                    month_key = task_date.strftime('%Y-%m')
-                    month_data[month_key]['tasks_completed'] += 1
-
-        monthly_summary = [
-            {
-                'month': month_key,
-                'days': len(data['days']),
-                'hours': round(data['minutes'] / 60, 2),
-                'tasks_completed': data['tasks_completed'],
-            }
-            for month_key, data in sorted(month_data.items())
-        ]
-
-        # --- Tasks list ---
-        tasks_response = [
-            {
-                'id': str(task.id),
-                'title': task.title,
-                'status': task.status,
-                'category': task.task_category_ref.name if task.task_category_ref else None,
-                'hours_spent': round(tb_duration.get(task.time_block_id, 0) / 60, 2),
-                'completed_at': task.completed_at.date().isoformat() if task.completed_at else None,
-            }
-            for task in tasks_list
-        ]
+    def get(self, request, client_id):
+        export_format = request.query_params.get('file_format', '').lower()
+        if export_format not in ('csv', 'pdf'):
+            return Response({'detail': 'file_format query param must be "csv" or "pdf".'}, status=400)
 
-        return Response({
-            'client': {
-                'id': str(client.id),
-                'name': client.name,
-                'company': client.company,
-            },
-            'period': {
-                'start': start_date.isoformat(),
-                'end': end_date.isoformat(),
-            },
-            'summary': {
-                'total_tasks': total_tasks,
-                'completed_tasks': completed_tasks,
-                'in_progress_tasks': in_progress_tasks,
-                'total_hours': total_hours,
-                'days_worked': days_worked,
-                'unique_categories': unique_categories,
-            },
-            'category_breakdown': category_breakdown,
-            'weekly_breakdown': weekly_breakdown,
-            'monthly_summary': monthly_summary,
-            'tasks': tasks_response,
-        })
+        start_date, end_date = _parse_date_range(request)
+        client, agent = _get_authorized_client(request, client_id)
+        report = _build_report_data(client, start_date, end_date)
+        period = {'start': start_date.isoformat(), 'end': end_date.isoformat()}
+
+        if export_format == 'csv':
+            return self._export_csv(report, client, agent, period)
+        return self._export_pdf(report, client, period)
+
+    def _export_csv(self, report, client, agent, period):
+        from django.utils.text import slugify
+        agent_name = agent.user.get_full_name() or agent.user.username
+        client_slug = slugify(client.name or client.company or 'client')
+        filename = f'{client_slug}_{period["start"]}_{period["end"]}.csv'
+
+        response = StreamingHttpResponse(
+            _stream_csv_rows(report['tasks'], client.name or client.company, agent_name),
+            content_type='text/csv; charset=utf-8',
+        )
+        response['Content-Disposition'] = f'attachment; filename="{filename}"'
+        return response
+
+    def _export_pdf(self, report, client, period):
+        from api.services.pdf_service import PDFService
+        from django.utils.text import slugify
+        client_slug = slugify(client.name or client.company or 'client')
+        filename = f'{client_slug}_{period["start"]}_{period["end"]}.pdf'
+
+        pdf_bytes = PDFService.generate_client_report_pdf(report, client, period)
+        response = HttpResponse(pdf_bytes, content_type='application/pdf')
+        response['Content-Disposition'] = f'attachment; filename="{filename}"'
+        return response
