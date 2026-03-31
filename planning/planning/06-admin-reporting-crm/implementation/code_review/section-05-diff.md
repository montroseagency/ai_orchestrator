diff --git a/server/api/tests.py b/server/api/tests.py
index 9201feb00..055e3ae39 100644
--- a/server/api/tests.py
+++ b/server/api/tests.py
@@ -1,4 +1,5 @@
 import datetime
+import unittest.mock
 
 from django.test import TestCase
 from django.core.exceptions import ValidationError
@@ -9,6 +10,7 @@ from api.models.agent_scheduling import TaskCategory, AgentGlobalTask, Scheduled
 from api.models.users import User, Agent
 from api.models.clients import Client
 from api.models.marketing_core import MarketingPlan, ContentPillar, AudiencePersona
+from api.services.notification_service import NotificationService
 
 
 # ---------------------------------------------------------------------------
@@ -1493,3 +1495,205 @@ class MarketingPlanAPISection04Test(APITestCase):
         pillar_names = [p['name'] for p in response.data['pillars']]
         self.assertIn('Active Pillar', pillar_names)
         self.assertNotIn('Inactive Pillar', pillar_names)
+
+
+# ---------------------------------------------------------------------------
+# Section 06 (plan 05): Admin Approval Queue API
+# ---------------------------------------------------------------------------
+
+class ApprovalQueueAPITests(APITestCase):
+
+    def setUp(self):
+        self.admin_user = User.objects.create_user(
+            username='approvals_admin', password='x', email='approvals_admin@t.com', role='admin'
+        )
+        agent_user = User.objects.create_user(
+            username='approvals_agent', password='x', email='approvals_agent@t.com', role='agent'
+        )
+        self.agent = Agent.objects.create(user=agent_user, department='marketing')
+        self.client_obj = Client.objects.create(
+            name='Approval Client', company='Approval Co', email='aclient@t.com',
+            start_date=datetime.date.today(), status='active',
+        )
+        self.task = AgentGlobalTask.objects.create(
+            agent=self.agent,
+            client=self.client_obj,
+            title='Review Me',
+            status=AgentGlobalTask.Status.IN_REVIEW,
+        )
+        self.admin_api = APIClient()
+        self.admin_api.force_authenticate(user=self.admin_user)
+        self.agent_api = APIClient()
+        self.agent_api.force_authenticate(user=agent_user)
+
+    def _approve_url(self, task_id=None):
+        tid = task_id or self.task.id
+        return f'/api/admin/approvals/{tid}/approve/'
+
+    def _reject_url(self, task_id=None):
+        tid = task_id or self.task.id
+        return f'/api/admin/approvals/{tid}/reject/'
+
+    def _list_url(self):
+        return '/api/admin/approvals/'
+
+    def test_list_returns_only_in_review_tasks(self):
+        AgentGlobalTask.objects.create(
+            agent=self.agent, client=self.client_obj, title='Done Task',
+            status=AgentGlobalTask.Status.DONE,
+        )
+        response = self.admin_api.get(self._list_url())
+        self.assertEqual(response.status_code, 200)
+        ids = [t['id'] for t in response.data]
+        self.assertIn(str(self.task.id), ids)
+        self.assertEqual(len(ids), 1)
+
+    def test_list_ordered_by_updated_at_asc(self):
+        task2 = AgentGlobalTask.objects.create(
+            agent=self.agent, client=self.client_obj, title='Older',
+            status=AgentGlobalTask.Status.IN_REVIEW,
+        )
+        # Force task2 to have an earlier updated_at
+        AgentGlobalTask.objects.filter(id=task2.id).update(updated_at='2020-01-01T00:00:00Z')
+        response = self.admin_api.get(self._list_url())
+        self.assertEqual(response.status_code, 200)
+        self.assertEqual(response.data[0]['id'], str(task2.id))
+
+    def test_list_includes_agent_client_names(self):
+        response = self.admin_api.get(self._list_url())
+        self.assertEqual(response.status_code, 200)
+        task_data = response.data[0]
+        self.assertIn('agent_name', task_data)
+        self.assertIn('client_name', task_data)
+        self.assertIn('client_company', task_data)
+
+    def test_list_returns_403_for_non_admin(self):
+        response = self.agent_api.get(self._list_url())
+        self.assertEqual(response.status_code, 403)
+
+    def test_approve_sets_status_done_clears_feedback(self):
+        self.task.review_feedback = 'old feedback'
+        self.task.save()
+        with unittest.mock.patch.object(NotificationService, 'notify_task_approved'):
+            response = self.admin_api.post(self._approve_url())
+        self.assertEqual(response.status_code, 200)
+        self.task.refresh_from_db()
+        self.assertEqual(self.task.status, AgentGlobalTask.Status.DONE)
+        self.assertEqual(self.task.review_feedback, '')
+
+    def test_approve_returns_404_for_nonexistent_task(self):
+        import uuid
+        response = self.admin_api.post(self._approve_url(task_id=uuid.uuid4()))
+        self.assertEqual(response.status_code, 404)
+
+    def test_approve_returns_409_when_task_not_in_review(self):
+        self.task.status = AgentGlobalTask.Status.DONE
+        self.task.save()
+        response = self.admin_api.post(self._approve_url())
+        self.assertEqual(response.status_code, 409)
+
+    def test_approve_returns_403_for_non_admin(self):
+        response = self.agent_api.post(self._approve_url())
+        self.assertEqual(response.status_code, 403)
+
+    def test_reject_sets_status_in_progress_stores_feedback(self):
+        with unittest.mock.patch.object(NotificationService, 'notify_task_rejected'):
+            response = self.admin_api.post(self._reject_url(), {'feedback': 'Needs work'}, format='json')
+        self.assertEqual(response.status_code, 200)
+        self.task.refresh_from_db()
+        self.assertEqual(self.task.status, AgentGlobalTask.Status.IN_PROGRESS)
+        self.assertEqual(self.task.review_feedback, 'Needs work')
+
+    def test_reject_returns_400_when_feedback_empty(self):
+        response = self.admin_api.post(self._reject_url(), {'feedback': ''}, format='json')
+        self.assertEqual(response.status_code, 400)
+
+    def test_reject_returns_400_when_feedback_missing(self):
+        response = self.admin_api.post(self._reject_url(), {}, format='json')
+        self.assertEqual(response.status_code, 400)
+
+    def test_reject_returns_409_when_task_not_in_review(self):
+        self.task.status = AgentGlobalTask.Status.IN_PROGRESS
+        self.task.save()
+        response = self.admin_api.post(self._reject_url(), {'feedback': 'Late'}, format='json')
+        self.assertEqual(response.status_code, 409)
+
+    def test_reject_returns_403_for_non_admin(self):
+        response = self.agent_api.post(self._reject_url(), {'feedback': 'x'}, format='json')
+        self.assertEqual(response.status_code, 403)
+
+    def test_approve_dispatches_notification(self):
+        with unittest.mock.patch.object(NotificationService, 'notify_task_approved') as mock_notify:
+            self.admin_api.post(self._approve_url())
+        mock_notify.assert_called_once()
+        call_task = mock_notify.call_args[0][0]
+        self.assertEqual(call_task.id, self.task.id)
+
+    def test_reject_dispatches_notification(self):
+        with unittest.mock.patch.object(NotificationService, 'notify_task_rejected') as mock_notify:
+            self.admin_api.post(self._reject_url(), {'feedback': 'Fix it'}, format='json')
+        mock_notify.assert_called_once()
+        call_task = mock_notify.call_args[0][0]
+        self.assertEqual(call_task.id, self.task.id)
+
+
+class NotificationTypesApprovalTests(TestCase):
+
+    def test_notification_types_includes_task_review_submitted(self):
+        from api.models.notifications import Notification
+        types_dict = dict(Notification.NOTIFICATION_TYPES)
+        self.assertIn('task_review_submitted', types_dict)
+
+    def test_notification_types_includes_task_approved(self):
+        from api.models.notifications import Notification
+        types_dict = dict(Notification.NOTIFICATION_TYPES)
+        self.assertIn('task_approved', types_dict)
+
+    def test_notification_types_includes_task_rejected(self):
+        from api.models.notifications import Notification
+        types_dict = dict(Notification.NOTIFICATION_TYPES)
+        self.assertIn('task_rejected', types_dict)
+
+    def test_notify_task_approved_creates_notification_for_agent(self):
+        from api.services.notification_service import NotificationService
+        agent_user = User.objects.create_user(
+            username='ntf_agent', password='x', email='ntf_agent@t.com', role='agent'
+        )
+        agent = Agent.objects.create(user=agent_user, department='marketing')
+        client_obj = Client.objects.create(
+            name='NTF Client', company='NTF Co', email='ntfclient@t.com',
+            start_date=datetime.date.today(), status='active',
+        )
+        task = AgentGlobalTask.objects.create(
+            agent=agent, client=client_obj, title='NTF Task',
+            status=AgentGlobalTask.Status.DONE,
+        )
+        with unittest.mock.patch(
+            'api.services.notification_service.publish_notification_event'
+        ) as mock_pub:
+            NotificationService.notify_task_approved(task, 'Admin User')
+        mock_pub.assert_called_once()
+        data = mock_pub.call_args.kwargs.get('data') or mock_pub.call_args[1].get('data', {})
+        self.assertEqual(data.get('type'), 'task_approved')
+
+    def test_notify_task_rejected_creates_notification_for_agent(self):
+        from api.services.notification_service import NotificationService
+        agent_user = User.objects.create_user(
+            username='ntf_agent2', password='x', email='ntf_agent2@t.com', role='agent'
+        )
+        agent = Agent.objects.create(user=agent_user, department='marketing')
+        client_obj = Client.objects.create(
+            name='NTF Client2', company='NTF Co2', email='ntfclient2@t.com',
+            start_date=datetime.date.today(), status='active',
+        )
+        task = AgentGlobalTask.objects.create(
+            agent=agent, client=client_obj, title='NTF Task2',
+            status=AgentGlobalTask.Status.IN_PROGRESS,
+        )
+        with unittest.mock.patch(
+            'api.services.notification_service.publish_notification_event'
+        ) as mock_pub:
+            NotificationService.notify_task_rejected(task, 'Admin User', 'Needs improvement')
+        mock_pub.assert_called_once()
+        data = mock_pub.call_args.kwargs.get('data') or mock_pub.call_args[1].get('data', {})
+        self.assertEqual(data.get('type'), 'task_rejected')
diff --git a/server/api/urls.py b/server/api/urls.py
index 39fc41b9b..d55005639 100644
--- a/server/api/urls.py
+++ b/server/api/urls.py
@@ -199,6 +199,7 @@ from .views.admin.marketing_tier_views import MarketingPlanTierViewSet, ClientMa
 from .views.admin.service_views import ServiceCategoryViewSet, ServiceViewSet
 
 from .views.communication import WebRTCCredentialsView
+from .views.admin.approval_views import list_approvals, approve_task_view, reject_task_view
 
 
 # Create router and register viewsets
@@ -482,6 +483,11 @@ urlpatterns = [
     path('admin/pending-verifications/', get_pending_verifications, name='pending_verifications'),
     path('admin/approve-verification/<uuid:verification_id>/', approve_payment_verification, name='approve_verification'),
 
+    # Admin approval queue endpoints
+    path('admin/approvals/', list_approvals, name='admin-approvals-list'),
+    path('admin/approvals/<uuid:task_id>/approve/', approve_task_view, name='admin-approvals-approve'),
+    path('admin/approvals/<uuid:task_id>/reject/', reject_task_view, name='admin-approvals-reject'),
+
     # Admin client assignment endpoints
     path('admin/clients/<uuid:client_id>/assign-agent/', assign_agent_to_client, name='assign_agent_to_client'),
     path('admin/clients/<uuid:client_id>/unassign-agent/', unassign_agent_from_client, name='unassign_agent_from_client'),
diff --git a/server/api/views/admin/approval_views.py b/server/api/views/admin/approval_views.py
new file mode 100644
index 000000000..125e72e19
--- /dev/null
+++ b/server/api/views/admin/approval_views.py
@@ -0,0 +1,160 @@
+import logging
+from rest_framework import permissions, status, serializers
+from rest_framework.decorators import api_view, permission_classes
+from rest_framework.permissions import IsAuthenticated
+from rest_framework.response import Response
+from django.db import transaction
+
+from ...models.agent_scheduling import AgentGlobalTask
+from ...services.notification_service import NotificationService
+
+logger = logging.getLogger(__name__)
+
+
+class IsAdminUser(permissions.BasePermission):
+    """Allow access only to users with role='admin'."""
+    def has_permission(self, request, view):
+        return request.user.is_authenticated and request.user.role == 'admin'
+
+
+class ApprovalTaskSerializer(serializers.ModelSerializer):
+    """Read serializer for the admin approval queue. Includes nested agent and client info."""
+    agent_name = serializers.SerializerMethodField()
+    client_name = serializers.SerializerMethodField()
+    client_company = serializers.SerializerMethodField()
+    category_name = serializers.SerializerMethodField()
+
+    class Meta:
+        model = AgentGlobalTask
+        fields = [
+            'id', 'title', 'description', 'status', 'priority',
+            'review_feedback', 'updated_at', 'created_at',
+            'agent_name', 'client_name', 'client_company', 'category_name',
+        ]
+
+    def get_agent_name(self, obj):
+        if obj.agent and obj.agent.user:
+            return obj.agent.user.get_full_name() or obj.agent.user.username
+        return ''
+
+    def get_client_name(self, obj):
+        if obj.client:
+            return obj.client.name or obj.client.company or ''
+        return ''
+
+    def get_client_company(self, obj):
+        if obj.client:
+            return obj.client.company or ''
+        return ''
+
+    def get_category_name(self, obj):
+        if obj.task_category_ref:
+            return obj.task_category_ref.name
+        return ''
+
+
+def approve_task(task_id, admin_user):
+    """Approve a task in review.
+
+    Uses select_for_update() inside transaction.atomic() to prevent race conditions.
+    Sets: status='done', review_feedback=''
+    Dispatches: task_approved notification (after transaction commits).
+    Raises AgentGlobalTask.DoesNotExist if task not found.
+    Raises ValueError if task is not in_review.
+    """
+    with transaction.atomic():
+        task = AgentGlobalTask.objects.select_for_update().get(id=task_id)
+        if task.status != AgentGlobalTask.Status.IN_REVIEW:
+            raise ValueError(f"Task {task_id} is not in_review (current: {task.status})")
+        task.status = AgentGlobalTask.Status.DONE
+        task.review_feedback = ''
+        task.save(update_fields=['status', 'review_feedback'])
+
+    approved_by = admin_user.get_full_name() or admin_user.username
+    try:
+        NotificationService.notify_task_approved(task, approved_by)
+    except Exception:
+        logger.exception("Failed to send task_approved notification for task %s", task_id)
+
+    return task
+
+
+def reject_task(task_id, admin_user, feedback: str):
+    """Reject a task in review with required feedback.
+
+    Uses select_for_update() inside transaction.atomic() to prevent race conditions.
+    Sets: status='in_progress', review_feedback=feedback
+    Dispatches: task_rejected notification (after transaction commits).
+    Raises AgentGlobalTask.DoesNotExist if task not found.
+    Raises ValueError if task is not in_review or feedback is blank.
+    """
+    if not feedback or not feedback.strip():
+        raise ValueError("Feedback is required when rejecting a task.")
+
+    with transaction.atomic():
+        task = AgentGlobalTask.objects.select_for_update().get(id=task_id)
+        if task.status != AgentGlobalTask.Status.IN_REVIEW:
+            raise ValueError(f"Task {task_id} is not in_review (current: {task.status})")
+        task.status = AgentGlobalTask.Status.IN_PROGRESS
+        task.review_feedback = feedback
+        task.save(update_fields=['status', 'review_feedback'])
+
+    rejected_by = admin_user.get_full_name() or admin_user.username
+    try:
+        NotificationService.notify_task_rejected(task, rejected_by, feedback)
+    except Exception:
+        logger.exception("Failed to send task_rejected notification for task %s", task_id)
+
+    return task
+
+
+@api_view(['GET'])
+@permission_classes([IsAuthenticated, IsAdminUser])
+def list_approvals(request):
+    """GET /admin/approvals/
+
+    Returns all AgentGlobalTask records with status='in_review', ordered by updated_at ASC.
+    """
+    tasks = (
+        AgentGlobalTask.objects
+        .filter(status=AgentGlobalTask.Status.IN_REVIEW)
+        .select_related('agent__user', 'client', 'task_category_ref')
+        .order_by('updated_at')
+    )
+    serializer = ApprovalTaskSerializer(tasks, many=True)
+    return Response(serializer.data)
+
+
+@api_view(['POST'])
+@permission_classes([IsAuthenticated, IsAdminUser])
+def approve_task_view(request, task_id):
+    """POST /admin/approvals/{task_id}/approve/"""
+    try:
+        task = approve_task(task_id, request.user)
+    except AgentGlobalTask.DoesNotExist:
+        return Response({'error': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)
+    except ValueError as exc:
+        return Response({'error': str(exc)}, status=status.HTTP_409_CONFLICT)
+    return Response(ApprovalTaskSerializer(task).data)
+
+
+@api_view(['POST'])
+@permission_classes([IsAuthenticated, IsAdminUser])
+def reject_task_view(request, task_id):
+    """POST /admin/approvals/{task_id}/reject/
+
+    Body: { "feedback": "string" } — required, non-empty.
+    """
+    feedback = request.data.get('feedback', '').strip()
+    if not feedback:
+        return Response(
+            {'error': 'feedback is required and must not be blank.'},
+            status=status.HTTP_400_BAD_REQUEST,
+        )
+    try:
+        task = reject_task(task_id, request.user, feedback)
+    except AgentGlobalTask.DoesNotExist:
+        return Response({'error': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)
+    except ValueError as exc:
+        return Response({'error': str(exc)}, status=status.HTTP_409_CONFLICT)
+    return Response(ApprovalTaskSerializer(task).data)
