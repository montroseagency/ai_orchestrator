<!-- PROJECT_CONFIG
runtime: typescript-npm
test_command: npm test
END_PROJECT_CONFIG -->

<!-- SECTION_MANIFEST
section-01-backend-migrations
section-02-notification-types
section-03-client-report-api
section-04-marketing-plan-api
section-05-approval-queue-api
section-06-category-management-api
section-07-export-api
section-08-client-detail-hub
section-09-admin-approvals-page
section-10-admin-category-page
section-11-agent-resubmission
section-12-agent-page-integration
section-13-tests
END_MANIFEST -->

# Implementation Sections Index — Admin Reporting & Client CRM Hub

## Overview

13 sections implementing the full admin reporting and CRM hub feature. Work is split across Django backend (sections 01–07, 11) and Next.js frontend (sections 08–12), with a final test-consolidation section. Backend migrations must land first to unblock API work; API sections can run in parallel after that; frontend sections depend on their respective API sections.

---

## Dependency Graph

| Section | Depends On | Blocks | Parallelizable |
|---------|------------|--------|----------------|
| section-01-backend-migrations | — | 03, 04, 05, 11 | Yes |
| section-02-notification-types | — | 05, 11 | Yes |
| section-03-client-report-api | 01 | 07, 08 | Yes (after 01) |
| section-04-marketing-plan-api | 01 | 08 | Yes (after 01) |
| section-05-approval-queue-api | 01, 02 | 09 | Yes (after 01+02) |
| section-06-category-management-api | — | 10 | Yes |
| section-07-export-api | 03 | 13 | Yes (after 03) |
| section-08-client-detail-hub | 03, 04 | 12, 13 | Yes (after 03+04) |
| section-09-admin-approvals-page | 05 | 13 | Yes (after 05) |
| section-10-admin-category-page | 06 | 13 | Yes (after 06) |
| section-11-agent-resubmission | 01, 02 | 13 | Yes (after 01+02) |
| section-12-agent-page-integration | 08 | 13 | Yes (after 08) |
| section-13-tests | 07, 08, 09, 10, 11, 12 | — | No (final) |

---

## Execution Order (Batches)

**Batch 1** — No dependencies (parallel):
- `section-01-backend-migrations`
- `section-02-notification-types`
- `section-06-category-management-api`

**Batch 2** — After Batch 1 (parallel):
- `section-03-client-report-api` (needs 01)
- `section-04-marketing-plan-api` (needs 01)
- `section-05-approval-queue-api` (needs 01, 02)
- `section-11-agent-resubmission` (needs 01, 02)

**Batch 3** — After Batch 2 (parallel):
- `section-07-export-api` (needs 03)
- `section-08-client-detail-hub` (needs 03, 04)
- `section-09-admin-approvals-page` (needs 05)
- `section-10-admin-category-page` (needs 06)

**Batch 4** — After Batch 3 (sequential):
- `section-12-agent-page-integration` (needs 08)
- `section-13-tests` (needs all prior sections)

---

## Section Summaries

### section-01-backend-migrations
Three Django migrations: add `review_feedback` TextField to `AgentGlobalTask`, add `strategy_notes` TextField to `MarketingPlan`, and add a composite `(client, date)` index on `AgentTimeBlock`. Update serializers for the new fields.

### section-02-notification-types
Add three new notification type choices to Django's `NOTIFICATION_TYPES` and three helper functions (`notify_task_review_submitted`, `notify_task_approved`, `notify_task_rejected`). Register the same three type strings in the Node.js notification-realtime service enum.

### section-03-client-report-api
New Django view `ClientReportView` at `server/api/agent/client_report_views.py`. Aggregates `AgentTimeBlock` + `AgentGlobalTask` by client and date range. Returns summary stats, category breakdown, weekly breakdown, monthly summary, and task list. Date range defaults to last 90 days.

### section-04-marketing-plan-api
Agent GET endpoint at `/agent/clients/{id}/marketing-plan/` returns `strategy_notes`, `pillars`, `audiences`. Admin POST endpoint at `/admin/clients/{id}/marketing-plan/` creates or updates the plan's `strategy_notes`. `MarketingPlanDetailSerializer` with nested `ContentPillarSerializer` and `AudiencePersonaSerializer`.

### section-05-approval-queue-api
New Django file `server/api/admin/approval_views.py`. Implements `GET /admin/approvals/` (in_review tasks with agent and client info), `POST /admin/approvals/{id}/approve/` (status→done, notify agent), `POST /admin/approvals/{id}/reject/` (status→in_progress, store feedback, notify agent). Uses `select_for_update()` in `transaction.atomic()` to prevent race conditions.

### section-06-category-management-api
New Django viewset `server/api/admin/category_views.py`. Full CRUD for `TaskCategory` (List/Create/Update/soft-Delete) plus a custom `reorder` action that bulk-updates `sort_order` in one `transaction.atomic()`. Ensures agent-facing category endpoint filters `is_active=True`.

### section-07-export-api
Export endpoint at `/agent/clients/{id}/report/export/` with `?format=csv|pdf`. CSV uses Python's `csv` module with `StreamingHttpResponse`. PDF extends `PDFService.generate_client_report_pdf()` using WeasyPrint with a new branded HTML template and inline SVG charts (no JS). Both require agent-client authorization.

### section-08-client-detail-hub
New shared frontend component tree at `client/components/portal/crm/`. `ClientDetailHub.tsx` with 4 tabs: OverviewTab (stats + activity), TasksTab (list/kanban filtered by client), MarketingPlanTab (markdown + pillars/audiences), TimeCapacityTab (charts + date range + export). React Query hooks `useClientReport` and `useClientMarketingPlan`. `ExportReportModal` for format/date range selection.

### section-09-admin-approvals-page
New Next.js page at `client/app/dashboard/admin/approvals/page.tsx`. Fetches and displays `in_review` tasks in `DataTable`. Clicking a row opens a `Drawer` with task detail, feedback textarea, Approve and Reject buttons. Sidebar badge shows pending count. Polls every 60s and listens on Socket.IO for real-time updates.

### section-10-admin-category-page
New Next.js page at `client/app/dashboard/admin/settings/categories/page.tsx`. Sortable list of `TaskCategory` rows using `@dnd-kit/sortable`. Each row has color swatch, department badge, active toggle, edit and delete buttons. Add/Edit via `Modal`. Drag-end dispatches bulk reorder PATCH with optimistic update + error rollback. Also updates admin sidebar nav with Approvals link and new Settings group.

### section-11-agent-resubmission
New `resubmit/` custom action on `AgentGlobalTaskViewSet` (backend). Frontend additions to the task card/modal: rejection feedback panel shown when `review_feedback` is non-empty and `status='in_progress'`, plus "Re-submit for Review" button that calls the endpoint and clears the panel on success.

### section-12-agent-page-integration
Wire `ClientDetailHub` into existing agent detail pages. Marketing: update `client/app/dashboard/agent/marketing/clients/[id]/page.tsx` to render `<ClientDetailHub clientId={params.id} agentType="marketing" />`. Developer: create `client/app/dashboard/agent/developer/clients/[id]/page.tsx` with `agentType="developer"`.

### section-13-tests
Consolidation section for any remaining test gaps. Add mock factories (`createMockClientReport`, `createMockMarketingPlan`, `createMockApprovalTask`, `createMockTaskCategory`) to `client/test-utils/`. Verify all frontend and backend tests pass end-to-end. No new production code in this section.
