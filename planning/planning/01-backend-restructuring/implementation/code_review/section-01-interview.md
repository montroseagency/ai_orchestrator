# Section 01 Code Review Interview Transcript

## Auto-fixes Applied

1. **Moved `slugify` import to module level** — was inside `save()`, now at top of file with other imports.
2. **Added `editable=False` to slug field** — prevents accidental slug changes in Django admin.

## User Interview

### Q: Slug collision handling?
**Finding:** Two categories with names that slugify identically (e.g. 'QA Review' and 'QA-Review') would hit a DB IntegrityError silently.

**User decision:** Raise ValidationError in `clean()` with clear message.

**Fix applied:** Added `clean()` method that slugifies the candidate name, queries for existing slug (excluding current record on edit), and raises `ValidationError({'name': ...})` if a collision is detected. Also added test `test_slug_collision_raises_validation_error`.

## Items Let Go (Nitpicks)

- Color hex validation — spec doesn't require it, no validator added
- `sort_order` non-negative validation — not in spec
- Test class naming `TaskCategoryDefaultsTest` vs singular — harmless
