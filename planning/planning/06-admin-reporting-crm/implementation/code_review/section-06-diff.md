diff --git a/server/api/serializers/agent_scheduling.py b/server/api/serializers/agent_scheduling.py
index d7e0b48ac..eebf65081 100644
--- a/server/api/serializers/agent_scheduling.py
+++ b/server/api/serializers/agent_scheduling.py
@@ -106,6 +106,18 @@ class TaskCategorySerializer(serializers.ModelSerializer):
         read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
 
 
+class TaskCategoryAdminSerializer(serializers.ModelSerializer):
+    """Admin write serializer — created_by is set automatically by the view."""
+    class Meta:
+        model = TaskCategory
+        fields = [
+            'id', 'name', 'slug', 'color', 'icon',
+            'department', 'requires_review', 'is_active', 'sort_order',
+            'created_by', 'created_at', 'updated_at',
+        ]
+        read_only_fields = ['id', 'slug', 'created_by', 'created_at', 'updated_at']
+
+
 # ── Global Task Read Serializer ──────────────────────────────
 
 _RECURRENCE_FIELDS = [
diff --git a/server/api/tests.py b/server/api/tests.py
index f16cf7a03..31447e5f3 100644
--- a/server/api/tests.py
+++ b/server/api/tests.py
@@ -1697,3 +1697,159 @@ class NotificationTypesApprovalTests(TestCase):
         mock_pub.assert_called_once()
         data = mock_pub.call_args.kwargs.get('data') or mock_pub.call_args[1].get('data', {})
         self.assertEqual(data.get('type'), 'task_rejected')
+
+
+# ---------------------------------------------------------------------------
+# Section 06: Admin Category Management API
+# ---------------------------------------------------------------------------
+
+class AdminCategoryManagementAPITests(APITestCase):
+
+    def setUp(self):
+        self.admin_user = User.objects.create_user(
+            username='cat_admin', password='x', email='cat_admin@t.com', role='admin'
+        )
+        agent_user = User.objects.create_user(
+            username='cat_agent', password='x', email='cat_agent@t.com', role='agent'
+        )
+        self.agent_obj = Agent.objects.create(user=agent_user, department='marketing')
+        self.admin_api = APIClient()
+        self.admin_api.force_authenticate(user=self.admin_user)
+        self.agent_api = APIClient()
+        self.agent_api.force_authenticate(user=agent_user)
+
+        self.cat1 = TaskCategory.objects.create(
+            name='S06 Design', slug='s06-design', color='#ff0000', department='marketing',
+            sort_order=1, is_active=True, created_by=self.admin_user,
+        )
+        self.cat2 = TaskCategory.objects.create(
+            name='S06 Copy', slug='s06-copy', color='#00ff00', department='marketing',
+            sort_order=2, is_active=True, created_by=self.admin_user,
+        )
+        self.cat_inactive = TaskCategory.objects.create(
+            name='S06 OldCat', slug='s06-old-cat', color='#0000ff', department='both',
+            sort_order=99, is_active=False, created_by=self.admin_user,
+        )
+
+    def _list_url(self):
+        return '/api/admin/task-categories/'
+
+    def _detail_url(self, pk):
+        return f'/api/admin/task-categories/{pk}/'
+
+    def _reorder_url(self):
+        return '/api/admin/task-categories/reorder/'
+
+    def _agent_list_url(self):
+        return '/api/agent/schedule/task-categories/'
+
+    # --- List ---
+
+    def test_list_returns_all_categories_for_admin(self):
+        response = self.admin_api.get(self._list_url())
+        self.assertEqual(response.status_code, 200)
+        ids = [str(c['id']) for c in response.data['results']]
+        self.assertIn(str(self.cat1.id), ids)
+        self.assertIn(str(self.cat2.id), ids)
+        self.assertIn(str(self.cat_inactive.id), ids)
+
+    def test_list_returns_403_for_agent(self):
+        response = self.agent_api.get(self._list_url())
+        self.assertEqual(response.status_code, 403)
+
+    # --- Create ---
+
+    def test_create_category(self):
+        payload = {
+            'name': 'S06 Strategy',
+            'color': '#123456',
+            'department': 'both',
+            'requires_review': False,
+        }
+        response = self.admin_api.post(self._list_url(), payload, format='json')
+        self.assertEqual(response.status_code, 201)
+        self.assertEqual(response.data['name'], 'S06 Strategy')
+
+    def test_create_returns_400_on_blank_name(self):
+        payload = {'name': '', 'color': '#123456', 'department': 'both'}
+        response = self.admin_api.post(self._list_url(), payload, format='json')
+        self.assertEqual(response.status_code, 400)
+
+    # --- Update ---
+
+    def test_partial_update_category(self):
+        response = self.admin_api.patch(
+            self._detail_url(self.cat1.id), {'color': '#aabbcc'}, format='json'
+        )
+        self.assertEqual(response.status_code, 200)
+        self.cat1.refresh_from_db()
+        self.assertEqual(self.cat1.color, '#aabbcc')
+
+    def test_update_is_active_toggle(self):
+        response = self.admin_api.patch(
+            self._detail_url(self.cat1.id), {'is_active': False}, format='json'
+        )
+        self.assertEqual(response.status_code, 200)
+        self.cat1.refresh_from_db()
+        self.assertFalse(self.cat1.is_active)
+
+    # --- Soft Delete ---
+
+    def test_soft_delete_sets_is_active_false(self):
+        response = self.admin_api.delete(self._detail_url(self.cat1.id))
+        self.assertEqual(response.status_code, 204)
+        self.cat1.refresh_from_db()
+        self.assertFalse(self.cat1.is_active)
+
+    def test_soft_delete_record_still_exists(self):
+        self.admin_api.delete(self._detail_url(self.cat1.id))
+        self.assertTrue(TaskCategory.objects.filter(id=self.cat1.id).exists())
+
+    def test_soft_delete_returns_403_for_agent(self):
+        response = self.agent_api.delete(self._detail_url(self.cat1.id))
+        self.assertEqual(response.status_code, 403)
+
+    # --- Reorder ---
+
+    def test_reorder_bulk_updates_sort_order(self):
+        payload = {
+            'order': [
+                {'id': str(self.cat2.id), 'sort_order': 1},
+                {'id': str(self.cat1.id), 'sort_order': 2},
+            ]
+        }
+        response = self.admin_api.post(self._reorder_url(), payload, format='json')
+        self.assertEqual(response.status_code, 200)
+        self.cat1.refresh_from_db()
+        self.cat2.refresh_from_db()
+        self.assertEqual(self.cat1.sort_order, 2)
+        self.assertEqual(self.cat2.sort_order, 1)
+
+    def test_reorder_returns_400_on_missing_category(self):
+        payload = {
+            'order': [
+                {'id': str(uuid.uuid4()), 'sort_order': 1},
+            ]
+        }
+        response = self.admin_api.post(self._reorder_url(), payload, format='json')
+        self.assertEqual(response.status_code, 400)
+
+    def test_reorder_returns_403_for_agent(self):
+        payload = {'order': [{'id': str(self.cat1.id), 'sort_order': 5}]}
+        response = self.agent_api.post(self._reorder_url(), payload, format='json')
+        self.assertEqual(response.status_code, 403)
+
+    def test_reorder_returns_400_on_empty_order(self):
+        response = self.admin_api.post(self._reorder_url(), {'order': []}, format='json')
+        self.assertEqual(response.status_code, 400)
+
+    # --- Agent-facing list filters active only ---
+
+    def test_agent_category_list_only_returns_active(self):
+        response = self.agent_api.get(self._agent_list_url())
+        self.assertEqual(response.status_code, 200)
+        results = response.data.get('results', response.data)
+        ids = [str(c['id']) for c in results]
+        self.assertNotIn(str(self.cat_inactive.id), ids)
+        self.assertIn(str(self.cat1.id), ids)
+
diff --git a/server/api/views/agent/scheduling_views.py b/server/api/views/agent/scheduling_views.py
index 2c40ab6ae..9f6498d9c 100644
--- a/server/api/views/agent/scheduling_views.py
+++ b/server/api/views/agent/scheduling_views.py
@@ -20,7 +20,7 @@ from api.models import (
 from api.serializers.agent_scheduling import (
     AgentTimeBlockSerializer, AgentTimeBlockBulkSerializer,
     AgentGlobalTaskReadSerializer, AgentGlobalTaskWriteSerializer,
-    TaskCategorySerializer,
+    TaskCategorySerializer, TaskCategoryAdminSerializer,
     ScheduledTaskLinkSerializer,
     WeeklyPlanSerializer,
     AgentRecurringBlockSerializer,
@@ -339,7 +339,7 @@ class AgentTaskCategoryViewSet(viewsets.ReadOnlyModelViewSet):
 class AdminTaskCategoryViewSet(viewsets.ModelViewSet):
     """Admin-facing: full CRUD for task categories."""
     permission_classes = [IsAuthenticated, IsAdmin]
-    serializer_class = TaskCategorySerializer
+    serializer_class = TaskCategoryAdminSerializer
     queryset = TaskCategory.objects.all().order_by('sort_order', 'name')
 
     def perform_create(self, serializer):
@@ -350,6 +350,27 @@ class AdminTaskCategoryViewSet(viewsets.ModelViewSet):
         instance.is_active = False
         instance.save(update_fields=['is_active'])
 
+    @action(detail=False, methods=['post'], url_path='reorder')
+    def reorder(self, request):
+        """Bulk-update sort_order for a list of category IDs."""
+        order = request.data.get('order', [])
+        if not order:
+            return Response({'error': 'order list is required and must not be empty.'}, status=status.HTTP_400_BAD_REQUEST)
+
+        ids = [item.get('id') for item in order]
+        existing_ids = set(
+            str(pk) for pk in TaskCategory.objects.filter(id__in=ids).values_list('id', flat=True)
+        )
+        missing = [str(i) for i in ids if str(i) not in existing_ids]
+        if missing:
+            return Response({'error': f'Unknown category IDs: {missing}'}, status=status.HTTP_400_BAD_REQUEST)
+
+        with transaction.atomic():
+            for item in order:
+                TaskCategory.objects.filter(id=item['id']).update(sort_order=item['sort_order'])
+
+        return Response({'status': 'reordered'})
+
 
 # ── Command Center (aggregation) ─────────────────────────────
 
