diff --git a/server/api/models/agent_scheduling.py b/server/api/models/agent_scheduling.py
index 58a66b876..7809df443 100644
--- a/server/api/models/agent_scheduling.py
+++ b/server/api/models/agent_scheduling.py
@@ -1,5 +1,6 @@
 from datetime import datetime, timedelta
 
+from django.conf import settings
 from django.db import models
 from django.contrib.contenttypes.fields import GenericForeignKey
 from django.contrib.contenttypes.models import ContentType
@@ -7,6 +8,48 @@ from django.utils import timezone
 import uuid
 
 
+class TaskCategory(models.Model):
+    """Admin-configurable task categories replacing hardcoded TASK_CATEGORY_CHOICES."""
+    DEPARTMENT_CHOICES = [
+        ('marketing', 'Marketing'),
+        ('website', 'Website'),
+        ('both', 'Both'),
+    ]
+
+    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
+    name = models.CharField(max_length=100, unique=True)
+    slug = models.SlugField(max_length=110, unique=True, blank=True)
+    color = models.CharField(max_length=7, default='#2563EB', help_text='Hex color e.g. #2563EB')
+    icon = models.CharField(max_length=50, blank=True, help_text='Lucide icon name')
+    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default='both')
+    requires_review = models.BooleanField(default=False)
+    is_active = models.BooleanField(default=True)
+    sort_order = models.IntegerField(default=0)
+    created_by = models.ForeignKey(
+        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
+        related_name='created_task_categories'
+    )
+    created_at = models.DateTimeField(auto_now_add=True)
+    updated_at = models.DateTimeField(auto_now=True)
+
+    class Meta:
+        ordering = ['sort_order', 'name']
+        indexes = [
+            models.Index(fields=['is_active', 'department']),
+        ]
+        verbose_name_plural = 'task categories'
+
+    def __str__(self):
+        return self.name
+
+    def save(self, *args, **kwargs):
+        """Auto-generate slug from name on creation only."""
+        if not self.slug:
+            from django.utils.text import slugify
+            self.slug = slugify(self.name)
+        super().save(*args, **kwargs)
+
+
 class AgentTimeBlock(models.Model):
     """Time-blocked slots in an agent's daily schedule."""
     BLOCK_TYPE_CHOICES = [
diff --git a/server/api/tests.py b/server/api/tests.py
index 7ce503c2d..bd968cb5d 100644
--- a/server/api/tests.py
+++ b/server/api/tests.py
@@ -1,3 +1,141 @@
 from django.test import TestCase
+from django.core.exceptions import ValidationError
+from django.db import IntegrityError
 
-# Create your tests here.
+from api.models.agent_scheduling import TaskCategory
+
+
+# ---------------------------------------------------------------------------
+# Section 01: TaskCategory model tests
+# ---------------------------------------------------------------------------
+
+class TaskCategoryDefaultsTest(TestCase):
+    """TaskCategory creates with all required fields and correct defaults."""
+
+    def test_defaults(self):
+        cat = TaskCategory.objects.create(name='Design', department='both')
+        self.assertIsNotNone(cat.id)
+        self.assertEqual(cat.color, '#2563EB')
+        self.assertTrue(cat.is_active)
+        self.assertEqual(cat.sort_order, 0)
+        self.assertFalse(cat.requires_review)
+
+
+class TaskCategorySlugTest(TestCase):
+    """Slug auto-generates from name on creation."""
+
+    def test_slug_auto_generated(self):
+        cat = TaskCategory.objects.create(name='QA Review', department='website')
+        self.assertEqual(cat.slug, 'qa-review')
+
+    def test_slug_does_not_update_on_name_change(self):
+        cat = TaskCategory.objects.create(name='QA Review', department='website')
+        original_slug = cat.slug
+        cat.name = 'Quality Assurance'
+        cat.save()
+        cat.refresh_from_db()
+        self.assertEqual(cat.slug, original_slug)
+
+
+class TaskCategoryUniquenessTest(TestCase):
+    """Uniqueness constraints on name and slug."""
+
+    def test_name_unique(self):
+        TaskCategory.objects.create(name='Design', department='both')
+        with self.assertRaises(IntegrityError):
+            TaskCategory.objects.create(name='Design', department='marketing')
+
+    def test_slug_unique(self):
+        TaskCategory.objects.create(name='Design', department='both')
+        # Same slug would be generated for 'Design' again
+        with self.assertRaises(IntegrityError):
+            TaskCategory.objects.create(name='Design', slug='design', department='marketing')
+
+
+class TaskCategoryDepartmentChoicesTest(TestCase):
+    """Department field accepts valid choices and rejects invalid ones."""
+
+    def test_valid_departments(self):
+        for dept in ('marketing', 'website', 'both'):
+            cat = TaskCategory(name=f'Cat {dept}', department=dept)
+            cat.full_clean()  # should not raise
+
+    def test_invalid_department_raises(self):
+        cat = TaskCategory(name='Bad Dept', department='developer')
+        with self.assertRaises(ValidationError):
+            cat.full_clean()
+
+
+class TaskCategoryColorDefaultTest(TestCase):
+    """Color defaults to '#2563EB'."""
+
+    def test_color_default(self):
+        cat = TaskCategory.objects.create(name='Research', department='both')
+        self.assertEqual(cat.color, '#2563EB')
+
+
+class TaskCategoryOrderingTest(TestCase):
+    """TaskCategory ordering is by (sort_order, name)."""
+
+    def test_ordering(self):
+        TaskCategory.objects.create(name='Zebra', department='both', sort_order=1)
+        TaskCategory.objects.create(name='Alpha', department='both', sort_order=2)
+        TaskCategory.objects.create(name='Middle', department='both', sort_order=1)
+        cats = list(TaskCategory.objects.all().values_list('name', flat=True))
+        self.assertEqual(cats, ['Middle', 'Zebra', 'Alpha'])
+
+
+class TaskCategoryStrTest(TestCase):
+    """__str__ returns name."""
+
+    def test_str(self):
+        cat = TaskCategory.objects.create(name='Design', department='both')
+        self.assertEqual(str(cat), 'Design')
+
+
+class TaskCategoryIndexTest(TestCase):
+    """Filtering by (is_active, department) works without error."""
+
+    def test_filter_by_active_and_department(self):
+        TaskCategory.objects.create(name='SEO', department='marketing')
+        qs = TaskCategory.objects.filter(is_active=True, department='marketing')
+        self.assertEqual(qs.count(), 1)
+
+
+# ---------------------------------------------------------------------------
+# Section 01: Seed data migration tests (verified after Section 04 migrations)
+# ---------------------------------------------------------------------------
+
+class TaskCategorySeedDataTest(TestCase):
+    """Seed categories are present after data migration (Section 04)."""
+
+    EXPECTED_SLUGS = [
+        'design', 'copywriting', 'seo-optimization', 'qa-review',
+        'client-communication', 'administrative-ops', 'content-creation',
+        'strategy', 'research', 'development', 'devops',
+    ]
+
+    def test_seed_count(self):
+        self.assertEqual(TaskCategory.objects.count(), 11)
+
+    def test_seed_department_assignments(self):
+        self.assertEqual(
+            TaskCategory.objects.get(slug='copywriting').department, 'marketing'
+        )
+        self.assertEqual(
+            TaskCategory.objects.get(slug='qa-review').department, 'website'
+        )
+        self.assertEqual(
+            TaskCategory.objects.get(slug='design').department, 'both'
+        )
+
+    def test_requires_review_categories(self):
+        review_cats = TaskCategory.objects.filter(requires_review=True)
+        self.assertEqual(review_cats.count(), 2)
+        slugs = set(review_cats.values_list('slug', flat=True))
+        self.assertEqual(slugs, {'copywriting', 'qa-review'})
+
+    def test_seed_slugs(self):
+        existing = set(TaskCategory.objects.values_list('slug', flat=True))
+        for slug in self.EXPECTED_SLUGS:
+            self.assertIn(slug, existing, f"Missing seed slug: {slug}")
