# External Review Integration Notes

## Review Source
- Gemini 2.5 Flash (iteration 1)

---

## Integrating

### 1. Agent Re-submission Workflow
**Why:** The plan covers admin approval/rejection but never defines how an agent re-submits a rejected task. Without this, `review_feedback` is a dead end — the agent sees feedback but has no API/UI path to act on it. This is a genuine functional gap.

**Change:** Add a Section 13 to the plan: "Agent Re-submission" — defines `POST /agent/tasks/{task_id}/resubmit/` endpoint (transition `in_progress → in_review`, clears `review_feedback`), and notes that the agent's task detail view shows the `review_feedback` when status is `in_progress` (post-rejection).

### 2. `tasks` list in ClientReportData — scope to date range
**Why:** "All tasks ever for a client" could be thousands of records for long-term clients, making the response huge and the UI slow. Filtering to the selected date range makes the report coherent.

**Change:** Update Section 2 — `tasks` list is filtered to tasks with `created_at` or `completed_at` within the date range. Add a note about limiting to 200 records max for the JSON response; export endpoints get full data.

### 3. Race condition protection on approval actions
**Why:** Two admins acting on the same task simultaneously could cause double-state transitions. `select_for_update` inside `transaction.atomic()` prevents this at the DB level.

**Change:** Update Section 4 — both `approve_task()` and `reject_task()` use `AgentGlobalTask.objects.select_for_update().get(id=task_id)` inside `transaction.atomic()`, and verify status is still `in_review` before proceeding.

### 4. Inactive categories filtered from agent-facing UIs
**Why:** Deactivating a category should hide it from agent task creation forms. This was implied by the soft-delete approach but not explicitly stated.

**Change:** Add explicit note in Section 6 — agent-facing `GET /agent/task-categories/` (and any category dropdowns) must filter `is_active=True` by default. Admin endpoint returns all (including inactive).

### 5. Category reorder — error recovery (not pure fire-and-forget)
**Why:** If the reorder PATCH fails silently, the frontend shows incorrect order until the user refreshes. Better UX: on error, trigger refetch.

**Change:** Update Section 10 — on API error, call `queryClient.invalidateQueries(['categories'])` to refetch the authoritative order from the server (in addition to showing toast). This reconciles state without rolling back complex drag state.

### 6. XSS sanitization for markdown rendering
**Why:** `strategy_notes` is admin-written, but defense-in-depth requires sanitization. Using `dangerouslySetInnerHTML` without sanitization is a vulnerability.

**Change:** Update Section 8 (MarketingPlanTab) — use `react-markdown` (or equivalent) with `rehype-sanitize` to render `strategy_notes`. Explicitly disallow raw HTML. This is standard practice for markdown rendering in React.

### 7. N+1 queries — explicit `select_related` calls
**Why:** Approval queue fetches agent name + client name; without `select_related`, each row triggers extra queries. The plan mentioned these relationships but didn't specify how to load them efficiently.

**Change:** Update Section 4 — approval queue query uses `select_related('agent__user', 'client')`. Update Section 2 — report tasks list uses `select_related('task_category_ref')`.

### 8. Database index on `AgentTimeBlock(client, date)`
**Why:** The report aggregation filters time blocks by client + date range. Without this index, every report request is a full table scan on time blocks.

**Change:** Update Section 1 — add a new migration (Migration C) that adds `Index(fields=['client', 'date'])` to `AgentTimeBlock`. This is separate from the two model-change migrations.

### 9. SSRF mitigation for PDF generation
**Why:** WeasyPrint fetches external resources referenced in HTML content. If `strategy_notes` or task descriptions contain external URLs in templates, this could expose internal network resources.

**Change:** Update Section 7 — note that `generate_client_report_pdf()` uses the same `django_url_fetcher` pattern as the existing quote PDFs (which already restricts resource loading to Django-resolved URLs). Content fields are not rendered in the PDF template — only structured data fields are.

### 10. Developer client Tasks tab — scope out "Project Milestones" undefined dependency
**Why:** "Website project API" is undefined in this plan. Depending on an undefined API creates an implementation blocker.

**Change:** Update Section 8 (TasksTab for developer clients) — developer clients show `AgentGlobalTask` filtered by client only. "Project Milestones" section is deferred to a future split when the website project task API is formally defined. The hub component is structured to accommodate this addition later (reserved tab area or accordion with "coming soon" placeholder).

---

## Not Integrating

### Rate limiting
**Why not:** Rate limiting is a platform-wide concern managed at the infrastructure/DRF level. Adding it to this plan would scope-creep into platform security work. The existing platform presumably has rate limiting policies.

### OverviewTab activity feed using `useGlobalTasks`
**Why not:** The reviewer correctly notes `useGlobalTasks` returns current task state, not a history log. However, the spec says "recent activity feed (last 10 task status changes)" which is acceptable to implement as "last 10 tasks ordered by `updated_at`" — this is a pragmatic interpretation. A full audit log system is out of scope for this split.

### Auditing/history for approval actions
**Why not:** The spec doesn't require audit logging. Adding it increases scope significantly. Future split.

### Monitoring, UAT, I18n, A11y, deployment/rollback strategy
**Why not:** These are cross-cutting platform concerns outside the scope of a feature implementation plan. They belong in platform engineering and QA processes.

### Load testing
**Why not:** Out of scope for feature planning. Can be addressed in platform testing strategy.

### Tight coupling of notification type enum
**Why not:** The existing architecture already uses this enum pattern throughout the codebase. Changing the architecture of the notification service is a separate platform concern.

### `MarketingPlan` `get_or_create` behavior
**Why not:** `get_or_create` is the correct and standard Django pattern for a `OneToOneField`. The reviewer's concern is valid but the behavior (get if exists, create if not) is precisely what we want.

### Department choices for category
**Why not:** These are static choices defined in the model's `TextChoices` — the frontend reads them from the API's metadata or hardcodes the enum. Not a dynamic managed resource.

### Quick action buttons on agent client page
**Why not:** The plan already says "discuss with user if needed." These buttons are an existing UI concern handled during implementation, not a planning decision.
