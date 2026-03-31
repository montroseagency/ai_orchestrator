# Section 13: Tests — Consolidation & Mock Factories

## Purpose

This is the final section of the Admin Reporting & Client CRM Hub split. It adds no new production code. Its job is to:

1. Add four missing mock factory functions to `client/test-utils/scheduling.tsx`
2. Verify all frontend and backend tests pass end-to-end
3. Confirm coverage minimums are met for every new API view

All prior sections (01–12) must be complete before this section is started.

---

## Dependencies (all must be done first)

- `section-07-export-api` — export endpoint tests exist
- `section-08-client-detail-hub` — `ClientDetailHub` + tab component tests exist
- `section-09-admin-approvals-page` — approvals page tests exist
- `section-10-admin-category-page` — category management page tests exist
- `section-11-agent-resubmission` — resubmit workflow tests exist
- `section-12-agent-page-integration` — agent client page integration tests exist

---

## Files to Modify

| File | Change |
|------|--------|
| `client/test-utils/scheduling.tsx` | Add 4 new mock factory functions |

No other files are created or modified. Do not add production code here.

---

## Step 1: Add Mock Factories to `client/test-utils/scheduling.tsx`

The existing file exports `createMockTimeBlock`, `createMockGlobalTask`, `mockUseSchedulingEngine`, `makeMockCommandCenterData`, and `renderWithQuery`. Four new factories need to be appended.

### TypeScript Types Required

Before writing the factories, confirm the TypeScript types exist in `client/lib/types/`. If they do not yet exist (because section-08 deferred their definition), define inline interfaces within the factory functions. The types these factories return are:

- `ClientReportResponse` — the full response shape from `GET /agent/clients/{id}/report/`
- `MarketingPlanDetailResponse` — the response from `GET /agent/clients/{id}/marketing-plan/`
- `ApprovalTask` (or `AgentGlobalTask` extended with `in_review` status, `review_feedback`, `agent.name`, `client.company`) — an item from `GET /admin/approvals/`
- `TaskCategoryItem` — a single `TaskCategory` row from `GET /admin/categories/`

Import these from `@/lib/types/` if they exist. If the type imports fail, define local interfaces inside the factory rather than blocking progress.

### Factory Stubs

Add the following four exports to the bottom of `client/test-utils/scheduling.tsx`:

```typescript
/** Returns a valid ClientReportResponse. Pass overrides to customise specific fields. */
export function createMockClientReport(
  overrides?: Partial<ClientReportResponse>
): ClientReportResponse {
  // Returns a complete mock with:
  // - client: { id, name, company }
  // - period: { start: '2026-01-01', end: '2026-03-29' }
  // - summary: { total_tasks: 10, completed_tasks: 7, in_progress_tasks: 2,
  //              total_hours: 42.5, days_worked: 18, unique_categories: ['Copywriting', 'Design'] }
  // - category_breakdown: [{ category: 'Copywriting', hours: 25, task_count: 5 }, ...]
  // - weekly_breakdown: [{ week_start: '2026-03-23', hours: 10, tasks_completed: 3 }, ...]
  // - monthly_summary: [{ month: '2026-03', days: 18, hours: 42.5, tasks_completed: 7 }]
  // - tasks: array of 2 task stubs (use createMockGlobalTask internally, add hours_spent + completed_at)
}

/** Returns a valid MarketingPlanDetailResponse. Pass overrides to customise specific fields. */
export function createMockMarketingPlan(
  overrides?: Partial<MarketingPlanDetailResponse>
): MarketingPlanDetailResponse {
  // Returns:
  // - strategy_notes: '## Strategy\n\nFocus on brand awareness in Q2.'
  // - pillars: [{ id: 'pillar-1', name: 'Brand Awareness', description: 'Top-of-funnel content',
  //               color: '#6366F1', target_percentage: 40 }]
  // - audiences: [{ id: 'audience-1', name: 'SMB Founders', description: 'Small business owners aged 30-50' }]
  // - updated_at: '2026-03-20T10:00:00Z'
}

/** Returns a valid ApprovalTask (AgentGlobalTask in in_review status with admin-facing fields). */
export function createMockApprovalTask(
  overrides?: Partial<ApprovalTask>
): ApprovalTask {
  // Returns:
  // - id: 'task-review-1'
  // - title: 'Write Nike Q2 Brief'
  // - description: 'Full brief covering campaign objectives and deliverables.'
  // - status: 'in_review'
  // - review_feedback: ''
  // - agent: { id: 'agent-1', name: 'Alex Smith' }
  // - client: { id: 'client-1', name: 'Nike Contact', company: 'Nike' }
  // - task_category_ref: 'cat-1'
  // - task_category_detail: { id: 'cat-1', name: 'Copywriting', color: '#F59E0B' }
  // - updated_at: '2026-03-28T14:00:00Z'
  // - created_at: '2026-03-27T09:00:00Z'
}

/** Returns a valid TaskCategoryItem. Pass overrides to customise specific fields. */
export function createMockTaskCategory(
  overrides?: Partial<TaskCategoryItem>
): TaskCategoryItem {
  // Returns:
  // - id: 'cat-1'
  // - name: 'Copywriting'
  // - slug: 'copywriting'
  // - color: '#F59E0B'
  // - icon: 'PenLine'
  // - department: 'marketing'
  // - sort_order: 1
  // - is_active: true
}
```

Each factory must spread `overrides` at the end of the returned object so any field can be replaced in tests, following the same pattern as `createMockTimeBlock` and `createMockGlobalTask`.

---

## Step 2: Backend Coverage Check

For each new Django view, confirm the following minimum tests exist in `server/api/tests/`. Each view requires at minimum one test per category below. These tests should have been written in the relevant backend sections — this section only verifies they are present.

### Approval Queue (`server/api/admin/approval_views.py`)

| Test scenario | Expected result |
|---|---|
| `GET /admin/approvals/` — admin user | 200, only `in_review` tasks returned, ordered by `updated_at` ASC |
| `GET /admin/approvals/` — non-admin | 403 |
| `POST /admin/approvals/{id}/approve/` — valid | status=`done`, `review_feedback=''` |
| `POST /admin/approvals/{id}/approve/` — task not `in_review` | 409 Conflict |
| `POST /admin/approvals/{id}/reject/` — with feedback | status=`in_progress`, feedback stored |
| `POST /admin/approvals/{id}/reject/` — empty feedback | 400 |
| `POST /admin/approvals/{id}/reject/` — task not `in_review` | 409 Conflict |
| Either action — non-admin | 403 |

### Agent Re-submission (`AgentGlobalTaskViewSet.resubmit`)

| Test scenario | Expected result |
|---|---|
| `POST /agent/tasks/{id}/resubmit/` — `in_progress` task | status=`in_review`, `review_feedback=''` |
| `POST /agent/tasks/{id}/resubmit/` — task not `in_progress` | 400 |
| `POST /agent/tasks/{id}/resubmit/` — wrong agent | 403 |
| `POST /agent/tasks/{id}/resubmit/` — dispatches notification | notification helper called |

### Client Report (`server/api/agent/client_report_views.py`)

| Test scenario | Expected result |
|---|---|
| Agent not assigned to client | 403 |
| `days_worked` with 3 blocks on 2 dates | `days_worked=2` |
| `total_hours` sum | correct float (minutes / 60) |
| No date params | defaults to last 90 days |
| Tasks outside date range | excluded from `tasks` list |

### Category Management (`server/api/admin/category_views.py`)

| Test scenario | Expected result |
|---|---|
| `DELETE /admin/categories/{id}/` | `is_active=False`, record still exists |
| `PATCH /admin/categories/reorder/` | `sort_order` updated for all IDs in order |
| `GET /agent/task-categories/` | only `is_active=True` returned |
| All admin endpoints — non-admin | 403 |

### Marketing Plan (`server/api/agent/` and `server/api/admin/`)

| Test scenario | Expected result |
|---|---|
| `GET` — client has no `MarketingPlan` | 404 or empty plan shape (per implementation) |
| Admin `POST` — no existing plan | plan created (`get_or_create`) |
| `GET` — agent not assigned | 403 |

### Export (`server/api/agent/client_report_views.py`)

| Test scenario | Expected result |
|---|---|
| `?format=csv` | `text/csv`, `Content-Disposition: attachment` |
| `?format=pdf` | `application/pdf` |
| `?format=invalid` | 400 |
| Agent not assigned to client | 403 |

---

## Step 3: Frontend Coverage Check

These test files should have been created in their respective sections. Verify they exist and run cleanly.

| Test file | Section that created it |
|---|---|
| `client/components/portal/crm/__tests__/ClientDetailHub.test.tsx` | section-08 |
| `client/components/portal/crm/__tests__/OverviewTab.test.tsx` | section-08 |
| `client/components/portal/crm/__tests__/TasksTab.test.tsx` | section-08 |
| `client/components/portal/crm/__tests__/MarketingPlanTab.test.tsx` | section-08 |
| `client/components/portal/crm/__tests__/TimeCapacityTab.test.tsx` | section-08 |
| `client/components/portal/crm/__tests__/ExportReportModal.test.tsx` | section-08 |
| `client/app/dashboard/admin/approvals/__tests__/ApprovalsPage.test.tsx` | section-09 |
| `client/app/dashboard/admin/settings/categories/__tests__/CategoryManagement.test.tsx` | section-10 |
| `client/app/dashboard/agent/marketing/clients/__tests__/ClientDetailPage.test.tsx` | section-12 |

### Key assertions to verify are present

**`ClientDetailHub.test.tsx`** — must cover:
- Renders 4 tab labels: Overview, Tasks, Marketing Plan, Time & Capacity
- Clicking each tab renders the correct child component
- Overview tab is active by default
- `agentType='marketing'` and `agentType='developer'` props both reach `TasksTab`

**`TimeCapacityTab.test.tsx`** — must cover:
- "Last 90d" is active by default
- Clicking "Last 30d" triggers `useClientReport` refetch with new date params
- `ExportReportModal` opens on "Export Report" button click

**`ApprovalsPage.test.tsx`** — must cover:
- Table renders rows from mock API response
- Clicking a row opens the `Drawer`
- "Reject" button is disabled when feedback textarea is empty
- Approve removes the row from the table

**`CategoryManagement.test.tsx`** — must cover:
- `onDragEnd` calls the reorder API with `ordered_ids`
- Delete button shows `confirmation-modal` before calling DELETE endpoint
- "Add Category" button opens modal

---

## Step 4: Running the Full Test Suite

After adding the mock factories and confirming all test files exist, run:

```bash
# Frontend
cd client && npx vitest run

# Backend
cd server && pytest api/tests/ -v
```

Both commands must exit with zero failures before this section is considered complete.

If any test fails:
- Do not modify production code to make tests pass — fix the test or the factory stub
- If a test was broken by a factory shape mismatch (e.g., a field name changed during implementation), update the factory in `scheduling.tsx` to match the real shape
- If a backend test fixture is stale, update the fixture — do not remove the test

---

## Coverage Requirements (minimum per new view)

No strict percentage threshold, but every new API view and viewset action must have at minimum:

1. **Happy path test** — correct data returned / correct state transition
2. **Auth/permission test** — 403 returned for unauthorized caller
3. **Validation test** — 400 returned for invalid/missing input
4. **Edge case test** — empty dataset, not-found (404), or conflict (409) where applicable

The mock factories added in Step 1 are the primary enabler for frontend tests meeting this bar — they provide consistent, fully-typed test data without requiring MSW or real API calls.
