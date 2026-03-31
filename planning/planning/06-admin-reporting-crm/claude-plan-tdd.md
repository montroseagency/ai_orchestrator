# TDD Plan: Admin Reporting & Client CRM Hub

## Testing Context

**Backend:** Django with `pytest-django`. Test files in `server/api/tests/`. Use `APITestCase` or `pytest` fixtures with `django.test.Client`. Factory pattern for model instances.

**Frontend:** Vitest + React Testing Library. Config: `client/vitest.config.ts`. Setup: `client/vitest.setup.ts` (`@testing-library/jest-dom`). Test files in `__tests__/` directories with `*.test.tsx` naming. Use `renderWithQuery` from `client/test-utils/scheduling.tsx`. Mock factories: `createMockTimeBlock`, `createMockGlobalTask` (extend with new ones below).

---

## Section 1: Backend Migrations

### Tests to write first

**Before implementing migrations:**

- Test `AgentGlobalTask` serializer includes `review_feedback` field (read-only for agents)
- Test `review_feedback` is empty string by default on new tasks
- Test `MarketingPlan` serializer includes `strategy_notes` field
- Test `strategy_notes` is empty string by default on new plans
- Test `AgentTimeBlock` query with `(client, date)` filter uses the new index (explain plan check or just functional test that filter returns correct results)

---

## Section 2: Client Report API

### Tests to write first

**New mock factory needed:**
```typescript
// createMockClientReport(overrides?) → ClientReportResponse
```

**Backend tests (pytest):**

- Test report endpoint returns 403 if requesting agent is not assigned to the client
- Test report endpoint returns 404 if client does not exist
- Test `days_worked` counts distinct dates correctly (3 time blocks on 2 dates → days_worked=2)
- Test `total_hours` sums duration_minutes and divides by 60 correctly
- Test `weekly_breakdown` groups time blocks by ISO week correctly
- Test `category_breakdown` correctly groups hours by task category
- Test `tasks` list is filtered to the date range (tasks outside range excluded)
- Test `tasks` list capped at 200 records
- Test default date range: no params → last 90 days
- Test partial date range: only `end_date` provided → `start_date` = 90 days before
- Test `unique_categories` contains category names from tasks within range
- Test N+1: report query uses a bounded number of DB queries (assert query count ≤ N)

---

## Section 3: Marketing Plan API

### Tests to write first

**New mock factory needed:**
```typescript
// createMockMarketingPlan(overrides?) → { strategy_notes, pillars[], audiences[], updated_at }
```

**Backend tests:**

- Test agent GET returns `strategy_notes`, `pillars`, `audiences`, `updated_at` for existing plan
- Test agent GET returns 404 with empty plan data if client has no `MarketingPlan`
- Test agent GET returns 403 if agent not assigned to client
- Test admin POST creates `MarketingPlan` if none exists (get_or_create)
- Test admin POST updates `strategy_notes` on existing plan
- Test admin POST returns 403 for non-admin users
- Test admin POST validates `strategy_notes` is a string

---

## Section 4: Admin Approval Queue API

### Tests to write first

**New mock factory needed:**
```typescript
// createMockApprovalTask(overrides?) → AgentGlobalTask with status='in_review', agent.name, client.name
```

**Backend tests:**

- Test GET `/admin/approvals/` returns only `in_review` tasks, ordered by `updated_at` ASC
- Test GET response includes `agent.name`, `client.name`, `client.company`
- Test GET returns 403 for non-admin users
- Test POST `/admin/approvals/{id}/approve/` sets `status='done'`, clears `review_feedback`
- Test approve returns 404 if task does not exist
- Test approve returns 409 if task is not in `in_review` status (concurrent modification)
- Test POST `/admin/approvals/{id}/reject/` sets `status='in_progress'`, stores `feedback` in `review_feedback`
- Test reject returns 400 if `feedback` is empty or missing
- Test reject returns 409 if task is not in `in_review` status
- Test both approve and reject return 403 for non-admin users
- Test notification is dispatched after approve (mock notification service)
- Test notification is dispatched after reject (mock notification service)

---

## Section 5: Notification Types

### Tests to write first

**Backend tests:**

- Test `NOTIFICATION_TYPES` includes `task_review_submitted`, `task_approved`, `task_rejected`
- Test `notify_task_review_submitted(task)` creates a Django `Notification` record with correct type
- Test `notify_task_approved(task, admin_name)` creates notification for the task's agent
- Test `notify_task_rejected(task, admin_name, feedback)` creates notification for the task's agent

---

## Section 6: Category Management API

### Tests to write first

**New mock factory needed:**
```typescript
// createMockTaskCategory(overrides?) → TaskCategoryItem with id, name, sort_order, is_active
```

**Backend tests:**

- Test GET `/admin/categories/` returns all categories including inactive ones
- Test GET `/agent/task-categories/` returns only `is_active=True` categories
- Test POST creates a new category with required fields
- Test POST validates name uniqueness (slug collision)
- Test PATCH updates category fields
- Test DELETE sets `is_active=False` (soft delete), does not remove the record
- Test PATCH reorder updates `sort_order` for all given IDs in correct order
- Test reorder wraps in single transaction (atomic)
- Test all admin endpoints return 403 for non-admin users

---

## Section 7: Export API

### Tests to write first

**Backend tests:**

- Test CSV export returns `text/csv` content type with `Content-Disposition: attachment`
- Test CSV rows contain: Task Title, Status, Category, Client, Date, Hours Spent, Agent
- Test CSV rows match tasks in the report for the given date range
- Test PDF export returns `application/pdf` content type
- Test PDF export calls `PDFService.generate_client_report_pdf` with correct arguments
- Test export returns 403 if agent not assigned to client
- Test `format=invalid` returns 400

---

## Section 8: ClientDetailHub Frontend Component

### Tests to write first

**Frontend tests (`ClientDetailHub.test.tsx`):**

- Test: renders 4 tabs (Overview, Tasks, Marketing Plan, Time & Capacity)
- Test: clicking each tab renders the correct tab component
- Test: Overview tab is active by default
- Test: passes `agentType='marketing'` to TasksTab correctly
- Test: passes `agentType='developer'` to TasksTab correctly

**Frontend tests (`OverviewTab.test.tsx`):**

- Test: renders client info card with name, company, status
- Test: renders stat cards (Total Tasks, Completed, In Progress, Days Worked, Total Hours)
- Test: renders recent activity feed with last 10 tasks
- Test: shows loading skeleton while data is fetching
- Test: shows empty state if no tasks exist for client

**Frontend tests (`TasksTab.test.tsx`):**

- Test: renders `ViewToggle` and `TaskFilterBar`
- Test: `agentType='marketing'` — renders kanban/list views
- Test: `agentType='developer'` — renders same views plus "Coming soon" milestones placeholder
- Test: task list is pre-filtered to the clientId
- Test: switching view toggle persists to localStorage

**Frontend tests (`MarketingPlanTab.test.tsx`):**

- Test: renders markdown content from `strategy_notes` when non-empty
- Test: renders ContentPillar cards with name, description, color badge
- Test: renders AudiencePersona cards with name, description
- Test: shows empty state when `strategy_notes` is empty and no pillars/audiences
- Test: does NOT render raw HTML tags from `strategy_notes` (XSS protection — `<script>` tag should be sanitized)

**Frontend tests (`TimeCapacityTab.test.tsx`):**

- Test: renders "Last 90d" button as active by default
- Test: clicking "Last 30d" triggers refetch with updated date params
- Test: renders weekly bar chart when weekly_breakdown data exists
- Test: renders category donut chart when category_breakdown data exists
- Test: renders monthly summary table rows
- Test: "Export Report" button opens `ExportReportModal`
- Test: shows loading state while report data is fetching

**Frontend tests (`ExportReportModal.test.tsx`):**

- Test: renders current date range in modal
- Test: CSV and PDF format options are selectable
- Test: "Download" button navigates to correct export URL with date params and format
- Test: modal closes on cancel

---

## Section 9: Admin Approvals Page

### Tests to write first

**Frontend tests (`ApprovalsPage.test.tsx`):**

- Test: fetches and renders table of `in_review` tasks on mount
- Test: table shows Agent, Task, Client, Submitted columns
- Test: clicking a row opens the review Drawer
- Test: Drawer shows task title, agent, client, description
- Test: "Approve" button calls approve endpoint and removes row from table on success
- Test: "Reject" button is disabled when feedback textarea is empty
- Test: "Reject" button calls reject endpoint with feedback and removes row on success
- Test: shows error toast on approve/reject API failure
- Test: shows empty state when no pending approvals exist
- Test: nav badge shows count of pending approvals

---

## Section 10: Admin Category Management Page

### Tests to write first

**Frontend tests (`CategoryManagement.test.tsx`):**

- Test: renders list of categories with name, color swatch, department badge
- Test: drag-end event dispatches reorder API call with correct ordered_ids
- Test: on reorder API error, invalidates categories query (triggers refetch)
- Test: "Add Category" button opens modal
- Test: modal submit calls POST `/admin/categories/` with form data
- Test: "Edit" button opens modal with pre-filled values
- Test: active toggle calls PATCH with `{ is_active: false }`
- Test: "Delete" button shows confirmation modal
- Test: confirming delete calls DELETE endpoint (soft delete)
- Test: preview badge updates in real-time as form values change

---

## Section 11: Agent Re-submission Workflow

### Tests to write first

**Backend tests:**

- Test `resubmit/` action transitions `in_progress → in_review` and clears `review_feedback`
- Test `resubmit/` returns 400 if task status is not `in_progress`
- Test `resubmit/` returns 403 if requesting agent does not own the task
- Test `resubmit/` triggers `task_review_submitted` notification to admins

**Frontend tests (additions to task card/modal):**

- Test: task with `review_feedback` non-empty and `status='in_progress'` shows rejection feedback panel
- Test: rejection feedback panel renders feedback text
- Test: "Re-submit for Review" button calls `resubmit/` endpoint
- Test: on success, task status updates to `in_review` and feedback panel hides

---

## Section 12: Agent Client Page Integration

### Tests to write first

- Test: `/agent/marketing/clients/[id]` renders `ClientDetailHub` with `agentType='marketing'`
- Test: `/agent/developer/clients/[id]` renders `ClientDetailHub` with `agentType='developer'`
- Test: page shows loading state while client data is fetching
- Test: page shows error state if client fetch fails

---

## Section 13: Tests (additional integration)

### Mock Factories Summary

All new mock factories to add to `client/test-utils/`:

```typescript
// createMockClientReport(overrides?) → ClientReportResponse
// createMockMarketingPlan(overrides?) → MarketingPlanDetailResponse
// createMockApprovalTask(overrides?) → AgentGlobalTask with in_review status
// createMockTaskCategory(overrides?) → TaskCategoryItem
```

### Running Tests

- Frontend: `cd client && npx vitest run` (or `npx vitest --watch` for development)
- Backend: `cd server && pytest api/tests/ -v`
- Both should pass before any PR is submitted

### Coverage Requirements

No strict coverage threshold defined, but each new API view must have at minimum:
- Happy path test
- Auth/permission test (403 for unauthorized)
- Validation test (400 for bad input)
- Edge case test (empty data, not found)
