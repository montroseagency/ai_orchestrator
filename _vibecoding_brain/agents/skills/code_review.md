## Skill: Backend Code Review Patterns
> Always injected for: Backend Tester on BACKEND and FULLSTACK tasks.

### Django/DRF Anti-Patterns — Flag as CRITICAL
- `MyModel.objects.all()` or `.filter()` in a view with no user/role scope → missing permission scope
- `serializer.data` returned without first calling `serializer.is_valid(raise_exception=True)` → silent validation bypass
- `request.data["key"]` without `.get()` or explicit `is_valid()` → KeyError on missing field
- String interpolation in `.raw()` or `cursor.execute(f"...")` → SQL injection vector
- `@api_view` decorator without `@permission_classes` or class-based view without `permission_classes` attribute → unauthenticated endpoint
- Business logic > 10 lines inside a view method (should be in `services/`) → architecture violation (MINOR unless it contains auth/permission logic)
- `FileField`/`ImageField` with `upload_to` using `request.data` → path traversal risk

### N+1 Query Detection — Flag as CRITICAL
Patterns that indicate N+1 queries:
- A `.filter()`, `.get()`, or `.save()` called inside a `for` loop over a queryset
- Accessing `obj.related_model` (ForeignKey/OneToOne) inside a loop without `select_related` in the queryset
- `prefetch_related` used on a ForeignKey or OneToOne field (should be `select_related`)
- `.count()` called inside a loop instead of annotating the queryset
- Missing `only()` or `defer()` on wide-column models fetched in bulk list views

### Security Checklist — All CRITICAL
- `@csrf_exempt`: always flag — must have documented justification in a comment
- `DEBUG = True` or hardcoded secret key in code: flag immediately
- `AllowAny` permission class on endpoints that handle user data
- Response serializer includes `password`, `token`, `secret`, `key`, or `internal_id` field
- `FileField` `upload_to` value derived from user input
- `.values()` or `.values_list()` returning more columns than needed for the operation

### Migration Safety Rules
- New non-nullable column on an existing table: requires `null=True, blank=True` OR a `default=` value
- Renaming a column safely requires three migrations: (1) add new column, (2) backfill data, (3) remove old column — never rename in one step
- Deleting a column: remove from code first, deploy, then create the migration to drop it
- `RunPython` in migrations: must be reversible (provide reverse function) unless explicitly noted

### Celery / Async Tasks
- Tasks that call the database must handle `DoesNotExist` — the object may be deleted before the task runs
- Tasks must be idempotent — safe to retry on failure
- `shared_task` or `@app.task` with `bind=True` for access to `self.retry()`
- Never pass Django model instances as task arguments — pass PKs and re-fetch inside the task
