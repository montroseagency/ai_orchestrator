# Section 07: Export API

## Overview

This section adds a file-download export endpoint to the client report system. Agents can export a client report as either a CSV or PDF file, scoped to a date range. The endpoint is a companion to the read-only report endpoint built in section 03 and shares the same authorization check (agent must be assigned to the client).

**Dependencies:**
- Section 01 (backend migrations) — `review_feedback` on `AgentGlobalTask`, `(client, date)` index on `AgentTimeBlock`
- Section 03 (client report API) — `ClientReportView`, `ClientReportData` aggregation logic, and the `client_report_views.py` file where this export view will live

---

## Files to Create / Modify

| Action | Path |
|--------|------|
| Modify | `server/api/views/agent/client_report_views.py` — add `ClientReportExportView` class; extracted `_build_report_data`, `_get_authorized_client` helpers |
| Modify | `server/api/services/pdf_service.py` — appended `_build_weekly_chart_svg`, `_render_report_html`, `generate_client_report_pdf` to `PDFService` class (no separate template file — HTML built via f-string inline) |
| Modify | `server/api/urls.py` — registered `agent/clients/<uuid:client_id>/report/export/` |
| Modify | `server/api/tests.py` — added `ClientReportExportViewTests` (11 tests)

**Note:** The HTML template was implemented as an inline f-string in `_render_report_html` rather than a separate `.html` file, consistent with `generate_quote_pdf` approach.

**Note:** Query param renamed `format` → `file_format` to avoid DRF's `URL_FORMAT_OVERRIDE` intercepting `?format=` for content negotiation before the view executes.

---

## Tests First

Write these tests in `server/api/tests/test_export_api.py` before implementing. Use `pytest-django` with `APITestCase`. Fixtures should create an `Agent` assigned to a `Client`, with several `AgentTimeBlock` and `AgentGlobalTask` records covering a date range.

### Test stubs

```python
class TestClientReportExportView(APITestCase):

    def test_csv_export_returns_text_csv_content_type(self):
        """GET ?format=csv returns Content-Type: text/csv"""

    def test_csv_export_returns_attachment_content_disposition(self):
        """Response has Content-Disposition: attachment; filename=... header"""

    def test_csv_rows_contain_expected_columns(self):
        """CSV header row: Task Title, Status, Category, Client, Date, Hours Spent, Agent"""

    def test_csv_rows_match_tasks_in_date_range(self):
        """Each task in the date range appears as exactly one CSV row with correct values"""

    def test_csv_excludes_tasks_outside_date_range(self):
        """Tasks with completed_at or created_at outside start/end are not in CSV"""

    def test_pdf_export_returns_application_pdf_content_type(self):
        """GET ?format=pdf returns Content-Type: application/pdf"""

    def test_pdf_export_calls_generate_client_report_pdf(self):
        """PDFService.generate_client_report_pdf is called with report_data, client, period"""

    def test_export_returns_403_if_agent_not_assigned_to_client(self):
        """Agent requesting export for a client they don't manage gets 403"""

    def test_export_returns_400_for_invalid_format(self):
        """?format=xls or missing format returns HTTP 400"""

    def test_export_returns_404_if_client_does_not_exist(self):
        """Non-existent client ID returns 404"""

    def test_csv_filename_includes_client_name_and_date_range(self):
        """Content-Disposition filename is like client-name_2026-01-01_2026-03-31.csv"""

    def test_pdf_export_returns_pdf_bytes_as_response_body(self):
        """Response body is non-empty bytes when WeasyPrint succeeds"""
```

---

## Endpoint Contract

```
GET /agent/clients/{id}/report/export/
Query params:
  start_date  — YYYY-MM-DD (optional, defaults match section 03 logic)
  end_date    — YYYY-MM-DD (optional)
  format      — "csv" or "pdf" (required; return 400 if missing or invalid)
Auth: IsAuthenticated; requesting agent must be assigned to this client
Returns: file download (Content-Disposition: attachment)
```

The date range parsing and authorization check are identical to `ClientReportView` from section 03. Extract that shared logic into a module-level helper or mixin so both views call the same code without duplication.

---

## CSV Implementation

Use Python's built-in `csv` module with Django's `StreamingHttpResponse`. This avoids buffering the entire CSV in memory, which matters for large datasets (the export endpoint is not capped at 200 rows unlike the JSON endpoint).

```python
# server/api/agent/client_report_views.py

import csv
from django.http import StreamingHttpResponse

class Echo:
    """An object that implements just the write method of the file-like interface."""
    def write(self, value):
        return value

def _stream_csv_rows(tasks, client, agent_name):
    """
    Generator that yields CSV rows for StreamingHttpResponse.
    Yields header row first, then one row per task.
    Each task dict should have: title, status, category, date, hours_spent
    """

class ClientReportExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """
        Export client report as CSV or PDF.
        Validates format param, authorizes agent-client relationship,
        builds report data, then dispatches to _export_csv or _export_pdf.
        """

    def _export_csv(self, report_data, client, period):
        """
        Returns StreamingHttpResponse with text/csv content type.
        Filename: {client-slug}_{start_date}_{end_date}.csv
        """

    def _export_pdf(self, report_data, client, period):
        """
        Calls PDFService.generate_client_report_pdf(report_data, client, period).
        Returns HttpResponse with application/pdf content type and
        Content-Disposition: attachment; filename=...
        """
```

**CSV column order and values:**

| Column | Source |
|--------|--------|
| Task Title | `task['title']` |
| Status | `task['status']` (human-readable: Done, In Progress, etc.) |
| Category | `task['category']` (category name string) |
| Client | `client.name` |
| Date | `task['completed_at']` if set, else `task['created_at']` (YYYY-MM-DD) |
| Hours Spent | `task['hours_spent']` formatted to 2 decimal places |
| Agent | The requesting agent's name |

The tasks list comes from the same aggregation logic as section 03's `ClientReportView` — call the shared aggregation function rather than re-querying. The export endpoint does **not** apply the 200-record cap.

---

## PDF Implementation

### PDFService extension

Add a new static method to the existing `PDFService` class in `server/api/services/pdf_service.py`. The class already has `COMPANY_INFO`, `COLORS`, and `get_logo_base64()` — reuse all of them.

```python
@staticmethod
def generate_client_report_pdf(report_data: dict, client, period: dict) -> bytes:
    """
    Generate branded PDF client report.

    Uses WeasyPrint + Montrose branding (same setup as generate_quote_pdf).
    Template: server/api/templates/reports/client_report_pdf.html
    Includes: header with logo, summary stats table, monthly breakdown table, task list.
    Charts: inline SVG bar chart for weekly hours (no JS — WeasyPrint cannot execute JS).
    Security: uses django_url_fetcher (same as quote PDFs) to restrict resource loading
    to Django-resolved URLs only, preventing SSRF via externally-referenced URLs.
    Content fields (task descriptions) are NOT rendered — only structured data fields.

    Args:
        report_data: dict matching ClientReportData structure from section 03
        client: Client model instance
        period: dict with 'start' and 'end' date strings

    Returns:
        bytes: PDF file content, or fallback minimal PDF bytes on WeasyPrint failure
    """
```

The method follows the same pattern as `generate_quote_pdf`:
1. Try `from weasyprint import HTML, CSS` — log warning and return fallback bytes if unavailable
2. Call `_render_report_html(report_data, client, period)` to build the HTML string
3. Call `HTML(string=html_content).write_pdf()` and return bytes
4. On exception, log error and return minimal fallback PDF bytes

### HTML template (`client_report_pdf.html`)

Create `server/api/templates/reports/client_report_pdf.html`. The template is rendered from a plain Python dict context — it does not use Django template engine (the existing `generate_quote_pdf` builds HTML via f-strings; follow the same pattern for consistency). It must include:

1. **Header** — Montrose logo (base64 embedded), company name, report title "Client Report", client name + company, date range
2. **Summary stats** — 2-column layout: Total Tasks / Completed / In Progress / Total Hours / Days Worked
3. **Weekly Hours bar chart** — inline SVG `<rect>` elements. Bar heights are calculated proportionally in Python before template rendering. X-axis: week start dates. Y-axis: hours. No JavaScript.
4. **Monthly Breakdown table** — columns: Month, Days Worked, Hours, Tasks Completed
5. **Task List table** — columns: Task Title, Status, Category, Date, Hours Spent. Capped at 100 rows in the PDF (the full dataset is in the CSV). If more than 100 tasks exist, add a note: "Showing first 100 tasks. Export as CSV for complete list."
6. **Footer** — same as quote PDF: company name, website, email, phone, generation date

**Security constraints:**
- Do not render `strategy_notes`, task descriptions, or any user-supplied free-text in the PDF template. Only render structured fields (names, status enums, dates, numbers).
- This prevents SSRF via embedded URLs in markdown content.
- The same `django_url_fetcher` used by `generate_quote_pdf` must be passed to `HTML(..., url_fetcher=django_url_fetcher)` to restrict external resource loading.

### SVG bar chart calculation

Before rendering the template, compute bar positions in Python:

```python
def _build_weekly_chart_svg(weekly_breakdown: list, width=400, height=120) -> str:
    """
    Build an inline SVG bar chart string from weekly_breakdown data.
    Each entry: { week_start: str, hours: float }
    Returns SVG string to embed directly in HTML.
    Bar widths are evenly distributed. Heights are proportional to max hours.
    Returns empty string if weekly_breakdown is empty.
    """
```

This function is a private static method on `PDFService`. The SVG string is embedded directly in the HTML: `<div class="chart">{svg_string}</div>`.

---

## URL Registration

In `server/api/urls.py`, register the export view alongside the existing client report view. Both views live in `server/api/agent/client_report_views.py`:

```python
from api.agent.client_report_views import ClientReportView, ClientReportExportView

# Under agent/ prefix:
path('agent/clients/<int:pk>/report/', ClientReportView.as_view(), name='client_report'),
path('agent/clients/<int:pk>/report/export/', ClientReportExportView.as_view(), name='client_report_export'),
```

---

## Authorization Pattern

The export view uses the same authorization as `ClientReportView`. The agent-client membership check should be a shared helper — either a module-level function in `client_report_views.py` or a mixin class both views inherit from:

```python
def _get_authorized_client(request, pk):
    """
    Fetch Client by pk and verify the requesting agent is assigned to it.
    Returns Client instance.
    Raises Http404 if client does not exist.
    Raises PermissionDenied if requesting user's agent is not assigned to this client.
    """
```

Both `ClientReportView.get()` and `ClientReportExportView.get()` call this helper before doing anything else.

---

## Implementation Checklist

1. Add `_get_authorized_client` helper to `client_report_views.py` (refactor from section 03 if it duplicates logic)
2. Add `ClientReportExportView` class to `client_report_views.py` with `_export_csv` and `_export_pdf` methods
3. Add `_build_weekly_chart_svg` static method to `PDFService`
4. Add `generate_client_report_pdf` static method to `PDFService`
5. Create `server/api/templates/reports/client_report_pdf.html` (or equivalent f-string renderer `_render_report_html`)
6. Register URL in `server/api/urls.py`
7. Write and pass all tests in `server/api/tests/test_export_api.py`
