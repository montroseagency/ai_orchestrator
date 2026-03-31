diff --git a/server/api/serializers/agent_scheduling.py b/server/api/serializers/agent_scheduling.py
index fe0f62476..93f55d00a 100644
--- a/server/api/serializers/agent_scheduling.py
+++ b/server/api/serializers/agent_scheduling.py
@@ -165,13 +165,10 @@ class AgentGlobalTaskWriteSerializer(serializers.ModelSerializer):
 
     def validate_status(self, value):
         """Redirect 'done' to 'in_review' for requires_review categories."""
-        if value != 'done':
+        if self.instance is None:
             return value
-        instance = self.instance
-        if instance is None:
-            return value
-        category = instance.task_category_ref
-        if category and category.requires_review and instance.status != 'in_review':
+        from api.services.recurrence import should_intercept_for_review
+        if should_intercept_for_review(self.instance, value):
             return 'in_review'
         return value
 
diff --git a/server/api/services/recurrence.py b/server/api/services/recurrence.py
new file mode 100644
index 000000000..bf89120cb
--- /dev/null
+++ b/server/api/services/recurrence.py
@@ -0,0 +1,143 @@
+"""
+JIT recurring task generation service.
+
+Provides three public functions:
+  - calculate_next_date(task) -> date | None
+  - generate_next_instance(task) -> AgentGlobalTask | None
+  - should_intercept_for_review(task, new_status) -> bool
+"""
+from datetime import date
+
+from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY, MO, TU, WE, TH, FR, SA, SU
+
+from django.db import IntegrityError
+
+# ISO weekday number (0=Mon) → rrule weekday constant
+WEEKDAY_MAP = [MO, TU, WE, TH, FR, SA, SU]
+
+_FREQ_MAP = {
+    'daily': DAILY,
+    'weekly': WEEKLY,
+    'biweekly': WEEKLY,  # interval forced to 2
+    'monthly': MONTHLY,
+    'yearly': YEARLY,
+    'custom': WEEKLY,    # uses recurrence_interval
+}
+
+
+def calculate_next_date(task):
+    """
+    Compute the next occurrence date for a recurring task.
+
+    Returns a date object, or None if the end condition has been reached.
+    """
+    if not task.is_recurring or not task.recurrence_frequency:
+        return None
+
+    freq = _FREQ_MAP.get(task.recurrence_frequency)
+    if freq is None:
+        return None
+
+    dtstart = task.scheduled_date or date.today()
+
+    # Interval
+    if task.recurrence_frequency == 'biweekly':
+        interval = 2
+    else:
+        interval = task.recurrence_interval or 1
+
+    # Weekday filter (only for weekly-family frequencies)
+    byweekday = None
+    if task.recurrence_days and freq == WEEKLY:
+        byweekday = [WEEKDAY_MAP[d] for d in task.recurrence_days if 0 <= d <= 6]
+
+    rule = rrule(
+        freq=freq,
+        interval=interval,
+        dtstart=dtstart,
+        byweekday=byweekday or None,
+    )
+
+    next_dt = rule.after(dtstart)
+    if next_dt is None:
+        return None
+
+    next_date = next_dt.date() if hasattr(next_dt, 'date') else next_dt
+
+    # Check end conditions
+    end_type = task.recurrence_end_type
+    if end_type == 'date':
+        if task.recurrence_end_date and next_date > task.recurrence_end_date:
+            return None
+    elif end_type == 'count':
+        if (task.recurrence_instance_number or 0) >= (task.recurrence_end_count or 0):
+            return None
+
+    return next_date
+
+
+def generate_next_instance(task):
+    """
+    Create the next recurring task instance after a task is completed.
+
+    Returns the new AgentGlobalTask, or None if no further instance should be created
+    (non-recurring, end condition reached, or duplicate prevented by DB constraint).
+    """
+    from api.models import AgentGlobalTask
+
+    if not task.is_recurring:
+        return None
+
+    next_date = calculate_next_date(task)
+    if next_date is None:
+        return None
+
+    parent = task.recurrence_parent if task.recurrence_parent_id else task
+    next_instance_number = (task.recurrence_instance_number or 0) + 1
+
+    try:
+        new_task = AgentGlobalTask.objects.create(
+            agent=task.agent,
+            title=task.title,
+            description=task.description,
+            priority=task.priority,
+            estimated_minutes=task.estimated_minutes,
+            client=task.client,
+            task_category_ref=task.task_category_ref,
+            is_recurring=True,
+            recurrence_frequency=task.recurrence_frequency,
+            recurrence_days=task.recurrence_days,
+            recurrence_interval=task.recurrence_interval,
+            recurrence_end_type=task.recurrence_end_type,
+            recurrence_end_count=task.recurrence_end_count,
+            recurrence_end_date=task.recurrence_end_date,
+            status='todo',
+            scheduled_date=next_date,
+            recurrence_parent=parent,
+            recurrence_instance_number=next_instance_number,
+        )
+    except IntegrityError:
+        # Race condition: unique_together (recurrence_parent, recurrence_instance_number)
+        # caught a duplicate — another request already generated this instance.
+        return None
+
+    return new_task
+
+
+def should_intercept_for_review(task, new_status):
+    """
+    Return True if the transition to 'done' should be redirected to 'in_review'.
+
+    Interception applies when:
+    - new_status is 'done'
+    - the task's category has requires_review=True
+    - the task is NOT already 'in_review' (which means admin is approving)
+    """
+    if new_status != 'done':
+        return False
+    category = task.task_category_ref
+    if not category or not category.requires_review:
+        return False
+    if task.status == 'in_review':
+        return False
+    return True
diff --git a/server/api/tests.py b/server/api/tests.py
index 5ff078653..4a5102677 100644
--- a/server/api/tests.py
+++ b/server/api/tests.py
@@ -543,3 +543,239 @@ class IsAdminPermissionTest(TestCase):
     def test_unauthenticated_denied(self):
         from api.views.agent.scheduling_views import IsAdmin
         self.assertFalse(IsAdmin().has_permission(self._request(authenticated=False), None))
+
+
+# ---------------------------------------------------------------------------
+# Section 05: JIT recurrence service tests
+# ---------------------------------------------------------------------------
+
+def make_recurring_task(agent, category=None, frequency='daily', days=None,
+                        interval=1, end_type=None, end_count=None, end_date=None,
+                        scheduled_date=None, instance_number=None, parent=None):
+    import datetime as dt
+    return AgentGlobalTask.objects.create(
+        agent=agent,
+        title='Recurring task',
+        is_recurring=True,
+        recurrence_frequency=frequency,
+        recurrence_days=days,
+        recurrence_interval=interval,
+        recurrence_end_type=end_type,
+        recurrence_end_count=end_count,
+        recurrence_end_date=end_date,
+        scheduled_date=scheduled_date or dt.date(2025, 1, 6),  # Monday
+        recurrence_instance_number=instance_number,
+        recurrence_parent=parent,
+        task_category_ref=category,
+        status='done',
+    )
+
+
+class CalculateNextDateTest(TestCase):
+
+    def setUp(self):
+        user = User.objects.create_user(
+            username='agt05', password='x', email='a05@t.com', role='agent'
+        )
+        self.agent = Agent.objects.create(user=user, department='marketing')
+
+    def test_daily_returns_next_day(self):
+        from api.services.recurrence import calculate_next_date
+        task = make_recurring_task(self.agent, frequency='daily',
+                                   scheduled_date=datetime.date(2025, 1, 6))
+        result = calculate_next_date(task)
+        self.assertEqual(result, datetime.date(2025, 1, 7))
+
+    def test_weekly_with_days_returns_next_matching_day(self):
+        from api.services.recurrence import calculate_next_date
+        # Monday Jan 6 2025, recurrence on Mon(0) and Wed(2) → next Wed Jan 8
+        task = make_recurring_task(self.agent, frequency='weekly', days=[0, 2],
+                                   scheduled_date=datetime.date(2025, 1, 6))
+        result = calculate_next_date(task)
+        self.assertEqual(result, datetime.date(2025, 1, 8))
+
+    def test_biweekly_returns_two_weeks_later(self):
+        from api.services.recurrence import calculate_next_date
+        task = make_recurring_task(self.agent, frequency='biweekly',
+                                   scheduled_date=datetime.date(2025, 1, 6))
+        result = calculate_next_date(task)
+        self.assertEqual(result, datetime.date(2025, 1, 20))
+
+    def test_monthly_preserves_day_of_month(self):
+        from api.services.recurrence import calculate_next_date
+        task = make_recurring_task(self.agent, frequency='monthly',
+                                   scheduled_date=datetime.date(2025, 1, 15))
+        result = calculate_next_date(task)
+        self.assertEqual(result, datetime.date(2025, 2, 15))
+
+    def test_custom_interval_3_weekly(self):
+        from api.services.recurrence import calculate_next_date
+        task = make_recurring_task(self.agent, frequency='custom', interval=3,
+                                   scheduled_date=datetime.date(2025, 1, 6))
+        result = calculate_next_date(task)
+        self.assertEqual(result, datetime.date(2025, 1, 27))
+
+    def test_end_type_date_returns_none_past_end(self):
+        from api.services.recurrence import calculate_next_date
+        task = make_recurring_task(self.agent, frequency='daily',
+                                   scheduled_date=datetime.date(2025, 1, 6),
+                                   end_type='date',
+                                   end_date=datetime.date(2025, 1, 6))
+        self.assertIsNone(calculate_next_date(task))
+
+    def test_end_type_count_returns_none_at_limit(self):
+        from api.services.recurrence import calculate_next_date
+        task = make_recurring_task(self.agent, frequency='daily',
+                                   scheduled_date=datetime.date(2025, 1, 6),
+                                   end_type='count', end_count=3, instance_number=3)
+        self.assertIsNone(calculate_next_date(task))
+
+    def test_end_type_never_always_returns(self):
+        from api.services.recurrence import calculate_next_date
+        task = make_recurring_task(self.agent, frequency='daily',
+                                   scheduled_date=datetime.date(2025, 1, 6),
+                                   end_type='never')
+        self.assertIsNotNone(calculate_next_date(task))
+
+
+class GenerateNextInstanceTest(TestCase):
+
+    def setUp(self):
+        user = User.objects.create_user(
+            username='agt05b', password='x', email='a05b@t.com', role='agent'
+        )
+        self.agent = Agent.objects.create(user=user, department='marketing')
+        self.category = TaskCategory.objects.create(name='RecurCat', department='both')
+
+    def test_creates_new_task_with_todo_status(self):
+        from api.services.recurrence import generate_next_instance
+        task = make_recurring_task(self.agent, category=self.category,
+                                   frequency='daily', scheduled_date=datetime.date(2025, 1, 6))
+        new_task = generate_next_instance(task)
+        self.assertIsNotNone(new_task)
+        self.assertEqual(new_task.status, 'todo')
+
+    def test_copies_fields_from_parent(self):
+        from api.services.recurrence import generate_next_instance
+        task = make_recurring_task(self.agent, category=self.category,
+                                   frequency='daily', scheduled_date=datetime.date(2025, 1, 6))
+        new_task = generate_next_instance(task)
+        self.assertEqual(new_task.title, task.title)
+        self.assertEqual(new_task.task_category_ref_id, self.category.pk)
+
+    def test_sets_recurrence_parent(self):
+        from api.services.recurrence import generate_next_instance
+        task = make_recurring_task(self.agent, frequency='daily',
+                                   scheduled_date=datetime.date(2025, 1, 6))
+        new_task = generate_next_instance(task)
+        self.assertEqual(new_task.recurrence_parent_id, task.pk)
+
+    def test_increments_instance_number(self):
+        from api.services.recurrence import generate_next_instance
+        task = make_recurring_task(self.agent, frequency='daily',
+                                   scheduled_date=datetime.date(2025, 1, 6),
+                                   instance_number=2)
+        new_task = generate_next_instance(task)
+        self.assertEqual(new_task.recurrence_instance_number, 3)
+
+    def test_sets_calculated_scheduled_date(self):
+        from api.services.recurrence import generate_next_instance
+        task = make_recurring_task(self.agent, frequency='daily',
+                                   scheduled_date=datetime.date(2025, 1, 6))
+        new_task = generate_next_instance(task)
+        self.assertEqual(new_task.scheduled_date, datetime.date(2025, 1, 7))
+
+    def test_non_recurring_returns_none(self):
+        from api.services.recurrence import generate_next_instance
+        task = AgentGlobalTask.objects.create(
+            agent=self.agent, title='Non-recurring', is_recurring=False
+        )
+        self.assertIsNone(generate_next_instance(task))
+
+
+class ReviewInterceptionTest(TestCase):
+
+    def setUp(self):
+        user = User.objects.create_user(
+            username='agt05c', password='x', email='a05c@t.com', role='agent'
+        )
+        self.agent = Agent.objects.create(user=user, department='marketing')
+        self.review_cat = TaskCategory.objects.create(
+            name='RvwCat05', department='both', requires_review=True
+        )
+        self.normal_cat = TaskCategory.objects.create(
+            name='NormCat05', department='both', requires_review=False
+        )
+
+    def test_review_category_redirects_to_in_review(self):
+        from api.services.recurrence import should_intercept_for_review
+        task = AgentGlobalTask.objects.create(
+            agent=self.agent, title='T', status='in_progress',
+            task_category_ref=self.review_cat
+        )
+        self.assertTrue(should_intercept_for_review(task, 'done'))
+
+    def test_review_category_allows_done_from_in_review(self):
+        from api.services.recurrence import should_intercept_for_review
+        task = AgentGlobalTask.objects.create(
+            agent=self.agent, title='T', status='in_review',
+            task_category_ref=self.review_cat
+        )
+        self.assertFalse(should_intercept_for_review(task, 'done'))
+
+    def test_non_review_category_allows_done(self):
+        from api.services.recurrence import should_intercept_for_review
+        task = AgentGlobalTask.objects.create(
+            agent=self.agent, title='T', status='in_progress',
+            task_category_ref=self.normal_cat
+        )
+        self.assertFalse(should_intercept_for_review(task, 'done'))
+
+    def test_non_done_status_never_intercepted(self):
+        from api.services.recurrence import should_intercept_for_review
+        task = AgentGlobalTask.objects.create(
+            agent=self.agent, title='T', status='in_progress',
+            task_category_ref=self.review_cat
+        )
+        self.assertFalse(should_intercept_for_review(task, 'in_progress'))
+
+
+class RaceConditionTest(TestCase):
+
+    def setUp(self):
+        user = User.objects.create_user(
+            username='agt05d', password='x', email='a05d@t.com', role='agent'
+        )
+        self.agent = Agent.objects.create(user=user, department='marketing')
+
+    def test_unique_constraint_prevents_duplicate_instances(self):
+        parent = AgentGlobalTask.objects.create(
+            agent=self.agent, title='Parent', is_recurring=True,
+            recurrence_frequency='daily', scheduled_date=datetime.date(2025, 1, 6)
+        )
+        AgentGlobalTask.objects.create(
+            agent=self.agent, title='Instance 1', is_recurring=True,
+            recurrence_frequency='daily',
+            recurrence_parent=parent, recurrence_instance_number=1,
+            scheduled_date=datetime.date(2025, 1, 7)
+        )
+        with self.assertRaises(IntegrityError):
+            AgentGlobalTask.objects.create(
+                agent=self.agent, title='Duplicate', is_recurring=True,
+                recurrence_frequency='daily',
+                recurrence_parent=parent, recurrence_instance_number=1,
+                scheduled_date=datetime.date(2025, 1, 7)
+            )
+
+    def test_duplicate_generate_call_returns_none(self):
+        from api.services.recurrence import generate_next_instance
+        task = make_recurring_task(self.agent, frequency='daily',
+                                   scheduled_date=datetime.date(2025, 1, 6),
+                                   instance_number=0)
+        first = generate_next_instance(task)
+        self.assertIsNotNone(first)
+        # Simulate calling again with same task (instance_number still 0)
+        second = generate_next_instance(task)
+        # Second call should return None (IntegrityError caught) since the
+        # unique_together (recurrence_parent=task, instance_number=1) already exists
+        self.assertIsNone(second)
