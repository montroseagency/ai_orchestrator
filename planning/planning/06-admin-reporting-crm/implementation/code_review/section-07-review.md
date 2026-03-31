# Section 07 Code Review — Client Report Export API

**Reviewer:** Senior Django/Python Code Review
**Date:** 2026-03-30
**Scope:** `ClientReportExportView`, `PDFService` PDF methods, URL registration, 11 export tests

---

## Summary

The implementation is well-structured overall. The `_build_report_data` refactor cleanly extracts shared logic, the streaming CSV approach is correct, and the WeasyPrint fallback is pragmatic. There are a few issues worth addressing — one security concern in the HTML template, a couple of correctness/edge-case gaps, and several minor issues.

---

## Findings

---

### 1. XSS in `_render_report_html` via unescaped user data

**Severity: Critical**

Multiple fields from the database are interpolated directly into the HTML string without HTML-escaping:

```python
# client_report_views.py — task_rows builder
f'<tr><td>{t["title"]}</td><td>{t["status"].replace("_", " ").title()}</td>'
f'<td>{t["category"] or ""}</td>'

# _render_report_html — client info section
<div class="client-info">{client.name or ''} — {client.company or ''}</div>

# monthly_rows
f'<tr><td>{m["month"]}</td>...'
```

The context note says these values "came from the DB already sanitized by ORM" — but the ORM provides no HTML sanitisation. A task title of `<script>alert(1)</script>` or `</td><td style="...">` is stored and returned as-is. While WeasyPrint renders to PDF (mitigating JS execution risk), maliciously crafted content can still break the PDF layout or inject additional HTML tags into the rendered output. More importantly, if this rendering path is ever reused in a web context the XSS becomes directly exploitable.

**Fix:** Wrap all user-supplied values with `html.escape()` (stdlib `html` module). At minimum: `t["title"]`, `t["category"]`, `m["month"]`, `client.name`, `client.company`, `company["name"]`, `company["website"]`, `company["email"]`, `company["phone"]`.

```python
import html as _html
# e.g.:
f'<td>{_html.escape(t["title"])}</td>'
```

---

### 2. `Content-Disposition` filename not RFC 5987 safe

**Severity: Important**

```python
response['Content-Disposition'] = f'attachment; filename="{filename}"'
```

`slugify()` ensures the filename is ASCII-safe and hyphenated, which does protect against the worst cases. However the quotes around the filename are not escaped, and `slugify` may produce an empty string for non-ASCII-only names (e.g. a client name entirely in Arabic or Chinese). In that case `filename` becomes `_YYYY-MM-DD_YYYY-MM-DD.csv` — acceptable, but the empty-slug edge case should be tested.

More importantly, if `client.name` contains characters that survive `slugify` in edge cases and later code paths skip `slugify`, this becomes a header injection vector. Consider using `urllib.parse.quote(filename)` or the RFC 5987 `filename*=UTF-8''...` form.

**Fix (minimal):** Add a guard for the empty-slug case and verify `slugify` is always applied before interpolation. Already done here, but worth a unit test.

---

### 3. `_build_report_data` loads all tasks into memory — no upper bound

**Severity: Important**

```python
all_tasks = list(tasks_qs)
```

The tasks queryset has no `.limit()`. For a long-lived client with thousands of tasks over a wide date range (the default date range is 90 days but callers can supply any range), this materialises all matching tasks and all their related objects into RAM. The CSV export then streams rows, but by this point the full list is already in memory.

**Fix:** For CSV export, stream directly from the queryset using `.iterator()` rather than pre-materialising the full list. The `_build_report_data` function could accept a `max_tasks` parameter or the CSV path could bypass it for the tasks list while still using it for the summary/aggregation portion (which operates over `time_blocks` and can remain bounded by `AgentTimeBlock` which is likely smaller).

Alternatively, document a hard cap (e.g. 10 000 tasks) to prevent runaway memory use.

---

### 4. Docstring in `client_report_views.py` header still says `?format=csv|pdf`

**Severity: Minor**

```python
# Line 345 in the file header docstring:
GET /agent/clients/{id}/report/export/?format=csv|pdf&start_date=...&end_date=...
```

The param was intentionally renamed to `file_format` (documented in the review context), but the module-level docstring was not updated. This will mislead future developers.

**Fix:** Change to `?file_format=csv|pdf`.

---

### 5. `_build_weekly_chart_svg` — unsanitised `week_start` and `hours` in SVG

**Severity: Minor**

The SVG method accepts `weekly_breakdown` dicts where `week_start` is a string (ISO date from `.isoformat()`) and `hours` is a float. These come from internal computation so in practice are safe. However, the function signature accepts any `list` from callers, and `w['week_start'][5:]` and `{w["hours"]:.1f}` are interpolated directly into SVG element attributes and text nodes.

If this method were ever called with external data, `week_start` containing `"` or `<` would break the SVG. Documenting the contract (values must be ORM-sourced ISO dates and floats) or adding `isinstance` guards would be sufficient.

**Fix (minimal):** Add a note in the docstring that `week_start` must be a valid ISO date string and `hours` must be numeric.

---

### 6. `_render_report_html` imports `date` inside the function

**Severity: Nitpick**

```python
from datetime import date as _date
generated = _date.today().isoformat()
```

`date` is already imported at the module level in `client_report_views.py` (`from datetime import date, timedelta, ...`). In `pdf_service.py`, this inline import is understandable since the module may not import `datetime`, but it adds minor visual clutter. Check whether `datetime.date` or a module-level `date` import is already present in `pdf_service.py` and use that instead.

---

### 7. `hours_spent` attribution is time-block-based, not per-task

**Severity: Minor (design note)**

```python
'hours_spent': round(tb_duration.get(task.time_block_id, 0) / 60, 2),
```

If multiple tasks share the same `time_block`, each task is credited the full block duration, and the sum of `hours_spent` across tasks will overcount total hours. This was presumably a pre-existing design decision from the original `ClientReportView`, but now that this data is exported to CSV/PDF it may mislead clients reviewing the per-task breakdown. The total hours in the summary (summed from blocks, not tasks) will be correct, creating a visible discrepancy.

**Fix:** Either add a note/disclaimer to the export ("Hours reflect the time block associated with each task, not per-task effort") or divide block time evenly among tasks sharing that block.

---

### 8. Missing test: CSV streaming content with special characters

**Severity: Minor**

The test suite covers column headers and basic CSV output, but does not test that task titles containing commas, quotes, or newlines are correctly escaped by the `csv.writer`. The `_Echo` + `csv.writer` pattern handles this correctly by default, but a regression test would be valuable:

```python
# Suggested test case
self.task.title = 'Task with "quotes", and commas\nand newline'
self.task.save()
response = self.api.get(self._export_url(), {'file_format': 'csv'})
content = b''.join(response.streaming_content).decode('utf-8')
# assert it parses to exactly 2 rows (header + 1 task) via csv.reader
```

---

### 9. Missing test: PDF export with WeasyPrint actually unavailable (fallback path)

**Severity: Minor**

The existing PDF tests mock `generate_client_report_pdf` entirely. There is no test that exercises the `ImportError` fallback path inside `generate_client_report_pdf` — confirming the fallback bytes are a valid (non-empty) PDF structure. Since the fallback is a hand-crafted PDF bytestring, a unit test of the service method in isolation (with WeasyPrint mocked to raise `ImportError`) would catch accidental corruption of those bytes.

---

### 10. Missing test: date range params passed through to export

**Severity: Minor**

None of the 11 tests verify that `start_date`/`end_date` query params actually filter the data in the CSV/PDF output. A test with a task outside the requested date range that confirms it is absent from the export would improve confidence in the date filtering logic.

---

### 11. `_get_authorized_client` — `_get_agent` may raise `AttributeError` for non-agent staff users

**Severity: Minor**

`_get_agent` (inherited from the existing codebase) presumably fetches `request.user.agent`. If an authenticated user has no associated `Agent` record (e.g., a superuser or admin-role user who satisfies `IsAuthenticated` but not `IsAnyAgent`), and `IsAnyAgent` does not short-circuit before `_get_agent` is called, this raises an unhandled `AttributeError` rather than returning a clean 403. Review whether `IsAnyAgent` guarantees an `Agent` relation exists before the view body executes.

---

## Test Coverage Summary

| Scenario | Covered |
|---|---|
| CSV 200 + content-type | Yes |
| CSV content-disposition | Yes |
| CSV filename includes `.csv` | Yes |
| CSV column headers | Yes |
| PDF 200 + content-type | Yes |
| PDF `generate_client_report_pdf` called | Yes |
| 403 if agent not assigned | Yes |
| 400 for invalid format | Yes |
| 400 for missing format | Yes |
| 404 for missing client | Yes |
| PDF non-empty bytes | Yes |
| CSV special characters in title | **No** |
| Date range filtering in export | **No** |
| PDF WeasyPrint ImportError fallback | **No** |
| Empty task list export | **No** |
| `slugify` produces empty slug | **No** |

---

## Priority Summary

| # | Severity | Finding |
|---|---|---|
| 1 | **Critical** | XSS via unescaped HTML in `_render_report_html` |
| 2 | **Important** | `Content-Disposition` filename edge cases |
| 3 | **Important** | Unbounded task list materialised into memory |
| 4 | Minor | Docstring still says `?format=` instead of `?file_format=` |
| 5 | Minor | SVG interpolation contract not documented |
| 6 | Nitpick | Inline `datetime` import already available at module scope |
| 7 | Minor | `hours_spent` overcounting when tasks share a time block |
| 8 | Minor | Missing test for CSV special character escaping |
| 9 | Minor | Missing test for WeasyPrint ImportError fallback |
| 10 | Minor | Missing test verifying date range filters export data |
| 11 | Minor | `_get_agent` may raise `AttributeError` for staff without Agent record |
