# Interview Transcript: Admin Reporting & Client CRM Hub

## Q1: Which agent dashboards should get the 4-tab CRM hub?

**Question:** The enhanced client detail (4-tab CRM hub) — which agent dashboards should get it?

**Answer:** Both marketing AND developer agent dashboards.

**Implications:** A single shared `ClientDetailHub` component will be built and used in both `/agent/marketing/clients/[id]` and `/agent/developer/clients/[id]`. The developer page is simpler but will still show all 4 tabs.

---

## Q2: Backend state of AgentGlobalTask

**Question:** Does AgentGlobalTask currently have a client FK from Split 01, and is 'in_review' a valid status choice on the backend?

**Answer:** "Not sure — need to check"

**Verified from codebase:**
- `AgentGlobalTask` has `client = models.ForeignKey("Client", ...)` ✓
- Status choices include `IN_REVIEW = 'in_review', 'In Review'` ✓
- `TaskCategory` DB model already exists with `sort_order` field ✓
- No `review_feedback` field on `AgentGlobalTask` — needs adding

---

## Q3: Marketing Plan storage model

**Question:** How should Marketing Plan content be stored?

**Answer:** New MarketingPlan model — but codebase research revealed `MarketingPlan` already exists (`server/api/models/marketing_core.py`) as a `OneToOneField` to `Client` with `ContentPillar` and `AudiencePersona` related records.

**Implication:** We add a `strategy_notes = models.TextField(blank=True)` field to the existing `MarketingPlan` model instead of creating a new one.

---

## Q4: Marketing Plan tab content

**Question:** The existing MarketingPlan model has structured data (ContentPillar, AudiencePersona) but no free-form markdown. How should the Marketing Plan tab work?

**Answer:** Add markdown field + show existing data.

**Spec:** Add `strategy_notes` TextField to `MarketingPlan`. The tab renders:
1. `strategy_notes` as rich-text/markdown (admin-editable, read-only for agents)
2. ContentPillar records displayed as structured cards
3. AudiencePersona records displayed as structured cards

---

## Q5: Developer agent Tasks tab

**Question:** Developer clients — which task types show in the Tasks tab?

**Answer:** Both global tasks AND website project tasks for that client.

**Spec:** The Tasks tab for developer clients will show:
- `AgentGlobalTask` filtered by `client=clientId`
- Website project tasks/milestones for that client (from `WebsiteProject` model)

---

## Q6: Rejection notes storage

**Question:** Where should rejection feedback live?

**Answer:** Add `review_feedback` field to `AgentGlobalTask` (simple TextField).

**Spec:**
- New migration: `review_feedback = models.TextField(blank=True)` on `AgentGlobalTask`
- Cleared (set to `''`) when agent re-submits for review
- Shown to agent in their task detail view when task is returned

---

## Q7: Export format scope

**Question:** Should we implement both PDF and CSV export in this split?

**Answer:** The user mentioned there's an existing quote system in admin that already does PDF generation — if reusable, implement both; otherwise CSV only.

**Verified from codebase:** `server/api/services/pdf_service.py` already has a full `PDFService` class using WeasyPrint with Montrose branding (logo, colors, company info, `generate_quote_pdf()`).

**Decision:** Implement BOTH CSV and PDF in this split by extending `PDFService` with `generate_client_report_pdf()`.

---

## Q8: Admin approval queue scope

**Question:** Which task types appear in the approval queue?

**Answer:** AgentGlobalTask only.

**Spec:** `GET /admin/approvals/` returns `AgentGlobalTask.objects.filter(status='in_review')`. Marketing tasks and project tasks are excluded.

---

## Q9: Time & Capacity chart date range

**Question:** How much historical data should the Time & Capacity tab charts show?

**Answer:** Default last 90 days with a date range picker.

**Spec:**
- Default: last 90 days from today
- Agent can select: Last 30 days, Last 90 days, Last 6 months, Custom range
- Affects: weekly bar chart, category donut chart, monthly summary table
- The "Export Report" button uses the same date range

---

## Q10: PDF service reuse

**Question:** Extend existing PDFService or create a separate one for client reports?

**Answer:** Extend existing PDFService (add `generate_client_report_pdf()` method).

**Spec:** New method in `server/api/services/pdf_service.py`. Reuses logo, brand colors, company info. New HTML template: `server/api/templates/reports/client_report_pdf.html`.

---

## Q11: Category data state

**Question:** Are there existing categories in the DB that agents are using?

**Answer:** Yes — existing live data, migrations must not destroy category references.

**Spec:**
- `sort_order` field already exists on `TaskCategory`
- CRUD operations must use soft-delete (toggle `is_active`) not hard delete
- Reorder via bulk PATCH `ordered_ids[]` updates `sort_order` only

---

## Q12: Time data source for aggregations

**Question:** Should hours/days worked come from time blocks only, or also task estimates?

**Answer:** Time blocks only.

**Spec:** All aggregations use `AgentTimeBlock` filtered by `client=clientId` and date range:
- **Days Worked** = count of distinct `date` values
- **Total Hours** = sum of `duration_minutes` / 60
- **Weekly breakdown** = group by ISO week, sum hours
- **Category breakdown** = join time blocks → tasks → category, sum hours per category
