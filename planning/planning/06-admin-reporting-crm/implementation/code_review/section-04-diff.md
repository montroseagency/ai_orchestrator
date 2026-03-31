diff --git a/server/api/serializers/marketing_core.py b/server/api/serializers/marketing_core.py
index c6f9a7860..6eab62eaf 100644
--- a/server/api/serializers/marketing_core.py
+++ b/server/api/serializers/marketing_core.py
@@ -50,6 +50,21 @@ class HashtagSerializer(serializers.ModelSerializer):
         return v.lower()
 
 
+class MarketingPlanDetailSerializer(serializers.ModelSerializer):
+    """Read-only serializer for CRM marketing plan tab (section 04).
+
+    Exposes strategy_notes, active pillars, all audiences, and updated_at.
+    Pillar filtering (is_active=True) must be done via Prefetch in the view.
+    """
+    pillars = ContentPillarSerializer(many=True, read_only=True)
+    audiences = AudiencePersonaSerializer(many=True, read_only=True)
+
+    class Meta:
+        model = MarketingPlan
+        fields = ['strategy_notes', 'pillars', 'audiences', 'updated_at']
+        read_only_fields = ['strategy_notes', 'pillars', 'audiences', 'updated_at']
+
+
 class MarketingPlanSerializer(serializers.ModelSerializer):
     pillars = ContentPillarSerializer(many=True, read_only=True)
     audiences = AudiencePersonaSerializer(many=True, read_only=True)
diff --git a/server/api/tests.py b/server/api/tests.py
index fbccbf745..1170270b2 100644
--- a/server/api/tests.py
+++ b/server/api/tests.py
@@ -8,7 +8,7 @@ from rest_framework.test import APIRequestFactory, APITestCase, APIClient
 from api.models.agent_scheduling import TaskCategory, AgentGlobalTask, ScheduledTaskLink, AgentTimeBlock
 from api.models.users import User, Agent
 from api.models.clients import Client
-from api.models.marketing_core import MarketingPlan
+from api.models.marketing_core import MarketingPlan, ContentPillar, AudiencePersona
 
 
 # ---------------------------------------------------------------------------
@@ -1355,3 +1355,139 @@ class ClientReportViewSection03Test(APITestCase):
             response = self.api_client.get(self._url())
         self.assertEqual(response.status_code, 200)
         self.assertLessEqual(len(ctx), 6, f'Expected ≤ 6 queries, got {len(ctx)}')
+
+
+# ---------------------------------------------------------------------------
+# Section 04: MarketingPlan API tests
+# ---------------------------------------------------------------------------
+
+class MarketingPlanAPISection04Test(APITestCase):
+    """Tests for GET /api/agent/clients/{id}/marketing-plan/ and
+    POST /api/admin/clients/{id}/marketing-plan/"""
+
+    def setUp(self):
+        self.today = datetime.date.today()
+
+        # Agent user
+        self.agent_user = User.objects.create_user(
+            username='agent04mkt', password='pass', email='agent04mkt@test.com', role='agent'
+        )
+        self.agent = Agent.objects.create(user=self.agent_user, department='marketing')
+
+        # Admin user
+        self.admin_user = User.objects.create_user(
+            username='admin04mkt', password='pass', email='admin04mkt@test.com', role='admin'
+        )
+
+        # Client user (non-agent, non-admin)
+        self.client_user = User.objects.create_user(
+            username='client04mkt', password='pass', email='client04mkt@test.com', role='client'
+        )
+
+        # Assigned client (avoids auto-assign collision by pre-assigning)
+        other_agent_user = User.objects.create_user(
+            username='other_agent04', password='pass', email='other_agent04@test.com', role='agent'
+        )
+        self.other_agent = Agent.objects.create(user=other_agent_user, department='marketing')
+
+        self.client_obj = Client.objects.create(
+            name='MktClient04', email='mc04@test.com', company='MC04 Co',
+            start_date=self.today, status='active',
+            marketing_agent=self.agent,
+        )
+        self.other_client = Client.objects.create(
+            name='OtherClient04', email='oc04@test.com', company='OC04 Co',
+            start_date=self.today, status='active',
+            marketing_agent=self.other_agent,
+        )
+
+        self.agent_api = APIClient()
+        self.agent_api.force_authenticate(user=self.agent_user)
+        self.admin_api = APIClient()
+        self.admin_api.force_authenticate(user=self.admin_user)
+        self.client_api = APIClient()
+        self.client_api.force_authenticate(user=self.client_user)
+
+    def _agent_url(self, client_id=None):
+        cid = client_id or self.client_obj.id
+        return f'/api/agent/clients/{cid}/marketing-plan/'
+
+    def _admin_url(self, client_id=None):
+        cid = client_id or self.client_obj.id
+        return f'/api/admin/clients/{cid}/marketing-plan/'
+
+    def _make_plan(self, client=None, strategy_notes='Test notes'):
+        c = client or self.client_obj
+        return MarketingPlan.objects.create(
+            client=c, name='Plan04', created_by=self.admin_user,
+            strategy_notes=strategy_notes,
+        )
+
+    # --- Agent GET ---
+
+    def test_agent_get_returns_strategy_notes_pillars_audiences_updated_at(self):
+        plan = self._make_plan(strategy_notes='Q2 Strategy')
+        ContentPillar.objects.create(plan=plan, name='Pillar A', is_active=True, weight=1)
+        AudiencePersona.objects.create(plan=plan, name='Audience A')
+        response = self.agent_api.get(self._agent_url())
+        self.assertEqual(response.status_code, 200)
+        self.assertEqual(response.data['strategy_notes'], 'Q2 Strategy')
+        self.assertIn('pillars', response.data)
+        self.assertIn('audiences', response.data)
+        self.assertIn('updated_at', response.data)
+        self.assertEqual(len(response.data['pillars']), 1)
+        self.assertEqual(len(response.data['audiences']), 1)
+
+    def test_agent_get_returns_404_if_no_marketing_plan_exists(self):
+        response = self.agent_api.get(self._agent_url())
+        self.assertEqual(response.status_code, 404)
+
+    def test_agent_get_returns_403_if_agent_not_assigned_to_client(self):
+        self._make_plan(client=self.other_client)
+        response = self.agent_api.get(self._agent_url(client_id=self.other_client.id))
+        self.assertEqual(response.status_code, 403)
+
+    def test_agent_get_returns_403_for_non_agent_user(self):
+        self._make_plan()
+        response = self.client_api.get(self._agent_url())
+        self.assertIn(response.status_code, [401, 403])
+
+    # --- Admin POST ---
+
+    def test_admin_post_creates_marketing_plan_if_none_exists(self):
+        self.assertEqual(MarketingPlan.objects.filter(client=self.client_obj).count(), 0)
+        response = self.admin_api.post(self._admin_url(), {'strategy_notes': 'New strategy'}, format='json')
+        self.assertEqual(response.status_code, 200)
+        self.assertEqual(MarketingPlan.objects.filter(client=self.client_obj).count(), 1)
+        self.assertEqual(response.data['strategy_notes'], 'New strategy')
+
+    def test_admin_post_updates_strategy_notes_on_existing_plan(self):
+        self._make_plan(strategy_notes='Old notes')
+        response = self.admin_api.post(self._admin_url(), {'strategy_notes': 'Updated notes'}, format='json')
+        self.assertEqual(response.status_code, 200)
+        self.assertEqual(MarketingPlan.objects.filter(client=self.client_obj).count(), 1)
+        self.assertEqual(response.data['strategy_notes'], 'Updated notes')
+
+    def test_admin_post_returns_403_for_non_admin_users(self):
+        response = self.agent_api.post(self._admin_url(), {'strategy_notes': 'x'}, format='json')
+        self.assertEqual(response.status_code, 403)
+
+    def test_admin_post_validates_strategy_notes_is_string(self):
+        response = self.admin_api.post(self._admin_url(), {'strategy_notes': 12345}, format='json')
+        self.assertEqual(response.status_code, 400)
+
+    def test_admin_post_allows_empty_string_strategy_notes(self):
+        self._make_plan(strategy_notes='Existing')
+        response = self.admin_api.post(self._admin_url(), {'strategy_notes': ''}, format='json')
+        self.assertEqual(response.status_code, 200)
+        self.assertEqual(response.data['strategy_notes'], '')
+
+    def test_active_pillars_only_in_agent_get(self):
+        plan = self._make_plan()
+        ContentPillar.objects.create(plan=plan, name='Active Pillar', is_active=True, weight=1)
+        ContentPillar.objects.create(plan=plan, name='Inactive Pillar', is_active=False, weight=2)
+        response = self.agent_api.get(self._agent_url())
+        self.assertEqual(response.status_code, 200)
+        pillar_names = [p['name'] for p in response.data['pillars']]
+        self.assertIn('Active Pillar', pillar_names)
+        self.assertNotIn('Inactive Pillar', pillar_names)
diff --git a/server/api/urls.py b/server/api/urls.py
index 4c7b01663..39fc41b9b 100644
--- a/server/api/urls.py
+++ b/server/api/urls.py
@@ -167,6 +167,11 @@ from .views.agent.scheduling_views import (
 # Import client report view (section 03)
 from .views.agent.client_report_views import ClientReportView
 
+# Import marketing plan views (section 04)
+from .views.agent.marketing_plan_views import (
+    AgentClientMarketingPlanView, AdminClientMarketingPlanView
+)
+
 # Import push notification views
 from .views.push_views import (
     vapid_public_key, subscribe as push_subscribe,
@@ -548,6 +553,10 @@ urlpatterns = [
     # Agent client report endpoints (section 03)
     path('agent/clients/<uuid:client_id>/report/', ClientReportView.as_view(), name='agent_client_report'),
 
+    # Marketing plan endpoints (section 04)
+    path('agent/clients/<uuid:client_id>/marketing-plan/', AgentClientMarketingPlanView.as_view(), name='agent_client_marketing_plan'),
+    path('admin/clients/<uuid:client_id>/marketing-plan/', AdminClientMarketingPlanView.as_view(), name='admin_client_marketing_plan'),
+
     # Admin analytics endpoints
     path('admin/analytics/agent-performance/', agent_performance, name='agent_performance'),
     path('admin/analytics/revenue/', revenue_dashboard, name='revenue_dashboard'),
diff --git a/server/api/views/agent/marketing_plan_views.py b/server/api/views/agent/marketing_plan_views.py
new file mode 100644
index 000000000..9a1b66550
--- /dev/null
+++ b/server/api/views/agent/marketing_plan_views.py
@@ -0,0 +1,106 @@
+"""
+Marketing Plan API — agent GET and admin POST for client marketing plans.
+
+GET  /agent/clients/{client_id}/marketing-plan/  — read plan (agent only)
+POST /admin/clients/{client_id}/marketing-plan/  — create/update strategy_notes (admin only)
+"""
+from django.db.models import Prefetch
+from django.shortcuts import get_object_or_404
+from rest_framework.permissions import IsAuthenticated
+from rest_framework.response import Response
+from rest_framework.views import APIView
+
+from api.models import Client, MarketingPlan, ContentPillar
+from api.serializers.marketing_core import MarketingPlanDetailSerializer
+from api.views.agent.scheduling_views import _get_agent
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
+class AgentClientMarketingPlanView(APIView):
+    """Read the marketing plan for a client.
+
+    Agent must be assigned to the client.
+    Returns 404 if no MarketingPlan exists for the client.
+    Returns 403 if requesting user is not an agent assigned to the client.
+    """
+    permission_classes = [IsAuthenticated]
+
+    def get(self, request, client_id):
+        # Auth: must be an agent
+        if request.user.role != 'agent' or not hasattr(request.user, 'agent_profile'):
+            return Response({'detail': 'Forbidden.'}, status=403)
+
+        agent = _get_agent(request)
+        client = get_object_or_404(Client, id=client_id)
+
+        # Auth: agent must be assigned to this client
+        if not _is_agent_assigned_to_client(agent, client):
+            return Response({'detail': 'Forbidden.'}, status=403)
+
+        # Fetch plan with prefetched active pillars and all audiences
+        active_pillars_qs = ContentPillar.objects.filter(is_active=True)
+        try:
+            plan = (
+                MarketingPlan.objects
+                .prefetch_related(
+                    Prefetch('pillars', queryset=active_pillars_qs),
+                    'audiences',
+                )
+                .get(client=client)
+            )
+        except MarketingPlan.DoesNotExist:
+            return Response({'detail': 'No marketing plan found for this client.'}, status=404)
+
+        serializer = MarketingPlanDetailSerializer(plan)
+        return Response(serializer.data)
+
+
+class AdminClientMarketingPlanView(APIView):
+    """Create or update strategy_notes for a client's marketing plan.
+
+    Admin only. Uses get_or_create — safe to call when no plan exists.
+    """
+    permission_classes = [IsAuthenticated]
+
+    def post(self, request, client_id):
+        # Auth: must be admin
+        if request.user.role != 'admin':
+            return Response({'detail': 'Forbidden.'}, status=403)
+
+        strategy_notes = request.data.get('strategy_notes')
+        if not isinstance(strategy_notes, str):
+            return Response(
+                {'strategy_notes': 'This field is required and must be a string.'},
+                status=400,
+            )
+
+        client = get_object_or_404(Client, id=client_id)
+
+        plan, _ = MarketingPlan.objects.get_or_create(
+            client=client,
+            defaults={'created_by': request.user},
+        )
+        plan.strategy_notes = strategy_notes
+        plan.save(update_fields=['strategy_notes', 'updated_at'])
+
+        # Re-fetch with prefetch for serialization
+        active_pillars_qs = ContentPillar.objects.filter(is_active=True)
+        plan = (
+            MarketingPlan.objects
+            .prefetch_related(
+                Prefetch('pillars', queryset=active_pillars_qs),
+                'audiences',
+            )
+            .get(pk=plan.pk)
+        )
+
+        serializer = MarketingPlanDetailSerializer(plan)
+        return Response(serializer.data)
