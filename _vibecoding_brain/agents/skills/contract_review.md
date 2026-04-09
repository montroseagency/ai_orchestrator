# Contract Review Skill — Frontend-Backend Alignment Patterns

> Injected into the Code Reviewer agent. Contains specific patterns to check for contract mismatches, derived from past bugs (RULE-3, RULE-4, RULE-5).

---

## Pattern 1: URL Path Extraction & Comparison

### Backend — Extract registered paths from `urls.py`

Look for these registration patterns in `server/api/urls.py`:

```python
# Router registration
router.register(r'clients', ClientViewSet, basename='client')
# → URL: /api/clients/  (list), /api/clients/{pk}/ (detail)

# Path registration
path('agent/developer/project-overview/', DeveloperProjectOverviewView.as_view()),
# → URL: /api/agent/developer/project-overview/

# Nested under a prefix
urlpatterns = [
    path('api/', include([
        path('admin/', include([...]))
    ]))
]
```

### Frontend — Extract API method paths from `api.ts`

Look for these patterns in `client/lib/api.ts`:

```typescript
// Direct path in method
async getDeveloperProjectOverview() {
  return this.get('/agent/developer/project-overview/');
}

// Path with interpolation
async getClient(id: string) {
  return this.get(`/clients/${id}/`);
}
```

### Common Mismatches (from RULE-3)
- Singular vs plural: `/project/` vs `/projects/`
- Hyphenated vs nested: `/project-overview/` vs `/projects/overview/`
- Missing trailing slash: `/clients` vs `/clients/`
- Wrong prefix: `/agent/developer/` vs `/developer/agent/`

---

## Pattern 2: Serializer Fields → TypeScript Types

### Backend — Extract response fields from serializers

```python
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'status', 'created_at', 'client']
        # Response keys: id, name, status, created_at, client
```

Watch for `source=` remapping:
```python
class ProjectSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='name')
    # Response key is "project_name", NOT "name"
```

Watch for method fields:
```python
class ProjectSerializer(serializers.ModelSerializer):
    active_tasks_count = serializers.SerializerMethodField()
    # Response key: "active_tasks_count" — must exist in TS type
```

### Frontend — Extract type fields from types.ts

```typescript
interface Project {
  id: string;
  name: string;       // ← Does this match serializer? Or is it "project_name"?
  status: string;
  created_at: string;
  client: string;
}
```

### Common Mismatches (from RULE-4)
- Backend `project_id` → Frontend expects `id`
- Backend `pending_quotes` → Frontend expects `quotes_pending`
- Backend `created_at` (snake_case) → Frontend `createdAt` (camelCase) without a transform layer
- Backend returns `null` → Frontend types `string` (not `string | null`)

---

## Pattern 3: Multi-Branch Response Structures

### When to Check (from RULE-5)
Any component that branches on `agentType`, `userRole`, `portalType`, or similar discriminators.

### What to Verify
```typescript
// WRONG — reading from wrong path
const activeProjects = stats.active_projects;  // ← wrong for developer agents

// CORRECT — documented per-branch
// For developer agents: data.developer_stats.active_projects_count
// For marketing agents: data.marketing_stats.active_campaigns
const activeProjects = agentType === 'developer'
  ? data.developer_stats.active_projects_count
  : data.marketing_stats.active_campaigns;
```

### Check
- Does the backend view return different structures for different user types?
- Does the frontend correctly branch and read the right keys?
- Is each branch documented with a comment?

---

## Pattern 4: Pagination Wrapper

### Backend
If the view uses `PageNumberPagination` or `LimitOffsetPagination`, the response is wrapped:
```json
{
  "count": 42,
  "next": "http://api/items/?page=2",
  "previous": null,
  "results": [...]
}
```

### Frontend
Must access `.results` for the data array, not treat the response as a direct array:
```typescript
// WRONG
const items: Item[] = await api.getItems();

// CORRECT
const response = await api.getItems();
const items: Item[] = response.results;
```

### Check
- Is the view paginated? (Look for `pagination_class` or default pagination in settings)
- Does the frontend handle the pagination wrapper?
- Does the TypeScript type include `count`, `next`, `previous`, `results`?

---

## Pattern 5: Request Payload Matching

### Serializer write fields
```python
class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['name', 'client', 'project_type', 'description']
        # name: required (no default, no blank=True)
        # description: optional (blank=True on model)
```

### Frontend form submission
```typescript
const payload = {
  name: formData.name,
  client: formData.clientId,      // ← key must be "client", not "clientId"
  project_type: formData.type,    // ← key must be "project_type", not "type"
  description: formData.description,
};
```

### Check
- Do payload keys match serializer field names exactly?
- Are required fields always sent?
- Are optional fields sent as `null` or omitted (not `undefined`)?

---

## Checklist Summary

For each new endpoint, verify this chain:

```
urls.py registration → api.ts method path  → MUST MATCH
serializer fields    → TypeScript interface → MUST MATCH
serializer source=   → response key name   → MUST MATCH remapped name
pagination class     → frontend handling   → MUST handle wrapper
write serializer     → request payload     → MUST match field names
role-branched views  → frontend branches   → MUST document per-branch
```
