# Code Review Interview: section-07-export-api

## Interview Decisions

No items required user input — all decisions were auto-resolvable.

---

## Auto-Fixes Applied

1. **XSS in `_render_report_html`** — Added `html.escape()` (stdlib `html` module) to all user-supplied values: `t["title"]`, `t["category"]`, `t["status"]`, `m["month"]`, `t["completed_at"]`/`t.get("created_at")`, `client.name`, `client.company`, `company["name"]`, `company["website"]`, `company["email"]`, `company["phone"]`. Pre-escaped into local variables before the f-string to keep the template readable.

2. **Docstring `?format=` → `?file_format=`** — Module-level docstring in `client_report_views.py` and `ClientReportExportView` class docstring both updated to reflect the `file_format` rename.

3. **Inline `from datetime import date as _date`** — Kept as-is since `pdf_service.py` does not have a top-level `date` import; the inline import avoids polluting the module namespace.

---

## Items Let Go

- **Unbounded task list in memory** — Intentional design: reports are per-client, date-scoped, and expected to fit in memory for agency-scale data. Out of scope to restructure `_build_report_data`.
- **Content-Disposition RFC 5987** — `slugify()` ensures ASCII-safe filenames; the internal API doesn't require RFC 5987 encoding.
- **SVG interpolation contract** — Data is ORM-sourced (ISO dates, floats); documenting the contract is unnecessary overhead.
- **`hours_spent` overcounting** — Pre-existing design from section 03; out of scope.
- **`_get_agent` AttributeError for staff users** — Pre-existing behavior; `IsAnyAgent` is expected to guard this. Out of scope.
- **Additional tests** (CSV special chars, date range in export, WeasyPrint fallback, empty list) — Acceptable coverage for this section. Section 13 consolidation can add regression tests.
