## Code Review: TaskCategory Model (Section 01)

### Correctness

**IMPORTANT** - Slug auto-generation logic has a flaw:
- The `save()` method checks `if not self.slug:` to decide whether to auto-generate
- However, according to the spec ("slug auto-gen on create only"), the slug should NEVER be updated after initial creation
- Current logic allows manual slug setting to bypass auto-generation, which is correct
- But the implementation doesn't prevent slug updates after creation - if someone explicitly sets a slug and saves again, it won't regenerate
- **Recommendation**: The logic is actually correct for the spec (generate only if blank). The test at line 97-103 confirms this behavior is intentional.

**CRITICAL** - UUID PK implementation is correct:
- ✓ `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)` matches spec exactly

**IMPORTANT** - Department choices and defaults:
- ✓ Choices defined correctly as list of tuples
- ✓ Default is 'both'
- Note: Hard-coded choices in model reduce flexibility; consider moving to settings if this needs to be environment-configurable

### Test Quality

**MINOR** - Test coverage has a gap:
- Seed data tests depend on Section 04 migrations; tests will fail if run without the data migration
- **Recommendation**: Add a comment clarifying these tests require the data migration

**IMPORTANT** - Missing validation test:
- No test for color field format validation
- No validator on color field enforces hex format

**NITPICK** - Test class naming: `TaskCategoryDefaultsTest` vs `TaskCategoryDefaultTest`

### Django Best Practices

**MINOR** - Lazy import in save() method:
- `slugify` imported inside `save()` — could be at module level (verify no circular deps)

**IMPORTANT** - Missing model validation:
- No `clean()` method to validate hex color format

**MINOR** - `blank=True` on slug allows admin editing; consider `editable=False`

### Security Issues
None identified.

### Potential Bugs

**IMPORTANT** - Slug uniqueness collision risk:
- "QA Review" and "QA-Review" both become "qa-review"
- Test only checks explicit duplicate, not slugify collision scenario

**MINOR** - `sort_order` has no non-negative validator

---

### Summary
Implementation is solid and matches spec. Main issues: slug collision edge case, color validation missing, minor test coverage gaps.
