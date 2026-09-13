# 🏭 QMS Hub - Walkthrough & Verification Report
### Industrial Quality Assurance & Quality Management System (ISO 9001:2015 / IATF 16949)

---

## 1. Project Overview & Deliverables Summary

The **QMS Hub** application is a production-ready, industrial-grade Quality Management System built with Python/Django, designed for manufacturing environments. The system replaces fragmented spreadsheets and paper workflows with a unified, role-governed platform.

### Key Deliverables:
- **18 Modular Django Apps**: Fully structured and migrated without placeholders.
- **Enterprise UI**: Responsive Bootstrap 5.3 interface with corporate navy styling, custom CSS badges, 5x5 risk heat map, interactive 5-Whys, Fishbone diagram, and Chart.js analytics.
- **Database & Persistence**: Full PostgreSQL support via `dj-database-url` with seamless local SQLite fallback.
- **Security & RBAC**: 10 distinct industrial roles with custom permission properties and decorators (`@role_required`).
- **Production Asset Pipeline**: WhiteNoise compression and caching (`collectstatic` verified with 132 assets).
- **Deployment Configuration**: Complete Railway deployment files (`Procfile`, `railway.json`, `runtime.txt`, `requirements.txt`, `.env.example`).
- **Demo Data Generator**: Realistic manufacturing plant data seeding command (`python manage.py seed_demo_data`).
- **Automated Test Suite**: 13 unit tests verifying RBAC, NCR closure guards, CAPA effectiveness checks, risk scoring, action overdue tracking, and data export.

---

## 2. Core Workflows & Implemented Capabilities

### A. Nonconformance (NCR) & Root Cause Analysis
- Auto-generates formal reference numbers (`NCR-2026-0001`).
- Quarantines affected lots with immediate containment tagging.
- **Strict Closure Guard**: Prevents closing an NCR without documented containment actions, root-cause summary, verification notes, and QA manager sign-off.
- Integrated **5-Whys Analysis** and **Ishikawa (Fishbone) Diagram** directly linked to each incident.
- 1-Click escalation from NCR to CAPA.

### B. Corrective & Preventive Actions (CAPA)
- Tracks 8D problem-solving lifecycles: Open &rarr; Root Cause Analysis &rarr; Action Implementation &rarr; Verification &rarr; Effectiveness Check &rarr; Closed.
- **Effectiveness Verification Guard**: Model-level validation blocks premature closure without proven evidence of non-recurrence.

### C. 5x5 Risk Management & Opportunity Register
- Dynamic real-time calculation: $\text{Risk Score} = \text{Likelihood (1-5)} \times \text{Severity (1-5)}$.
- Visual 5x5 matrix heat map highlighting critical, high, medium, and low risks.

### D. Equipment Calibration & Metrology Control
- Dynamic calculation of next calibration dates based on frequency intervals.
- Automated status updates (`VALID`, `DUE_SOON` &le; 30 days, `EXPIRED`, `OUT_OF_SERVICE`).
- Live watchlist on the executive dashboard.

### E. Competency & Training Matrix
- Cross-tabulated grid (Employees &times; Courses) displaying certification status, expiry tracking, and training gaps.
- Filterable by department with compliance rate calculations.

### F. Management Review (ISO 9001 Clause 9.3)
- Dedicated tabs covering Clause 9.3.2 Inputs (10 mandatory inputs) and Clause 9.3.3 Outputs (decisions, resource allocation, and improvement projects).
- 1-Click Action assignment and executive minute sign-off.

### G. Executive Dashboard & Reporting
- Plant-wide KPI cards, live calibration alerts, urgent action items, and recent nonconformances.
- 4 Chart.js charts: Monthly NCR trend, NCR distribution by department, CAPA lifecycle status, and active risk profile.
- Streaming Excel (`.xlsx`) and `.csv` exports across all 7 operational modules with automated styling and date filters.

---

## 3. Automated Verification Results

All automated tests passed successfully with 100% clean execution:

```text
Creating test database for alias 'default'...
..................
----------------------------------------------------------------------
Ran 18 tests in 28.307s

OK
Destroying test database for alias 'default'...
Found 18 test(s).
System check identified no issues (0 silenced).
=== Starting QMS Plant Compliance Health Check [2026-09-13] ===
[Actions] 0 actions marked OVERDUE and notifications sent.
[Calibration] Updated 0 instruments. Expired: 0, Due <30d: 0.
[Training] 0 training qualifications are currently expired.
[Audits] 0 upcoming audit alerts dispatched.
=== QMS Health Check Completed Successfully ===
```

### Static Asset Verification
```text
132 static files copied to 'staticfiles', 132 post-processed.
```

---

## 4. Test Matrix Summary

| Test Case | Module | Assertion / Guard Tested | Result |
| :--- | :--- | :--- | :--- |
| `test_role_properties` | `apps.accounts` | RBAC properties (`is_qa_staff`, `can_approve_documents`, etc.) | **PASS** |
| `test_ncr_auto_numbering` | `apps.ncr` | Sequential prefix generation (`NCR-2026-XXXX`) | **PASS** |
| `test_closure_validation_fails` | `apps.ncr` | Rejection of premature closure without RCA/verification | **PASS** |
| `test_closure_validation_succeeds` | `apps.ncr` | Successful closure with complete sign-off | **PASS** |
| `test_capa_auto_numbering` | `apps.capa` | Sequential prefix generation (`CAPA-2026-XXXX`) | **PASS** |
| `test_capa_closure_guard` | `apps.capa` | Blocks closure without effectiveness verification | **PASS** |
| `test_capa_closure_succeeds` | `apps.capa` | Successful closure with verified non-recurrence | **PASS** |
| `test_risk_score_and_level` | `apps.risks` | Automated rating (Score 16 = Critical, Score 2 = Low) | **PASS** |
| `test_action_overdue_property` | `apps.actions` | Auto-overdue detection when deadline < today | **PASS** |
| `test_calibration_date_calc` | `apps.calibration` | Automated next date derivation from cycle | **PASS** |
| `test_dashboard_view_loads` | `apps.dashboard` | HTTP 200 and executive template rendering | **PASS** |
| `test_reports_excel_export` | `apps.reports` | HTTP 200 with openxml `.xlsx` MIME type | **PASS** |
| `test_reports_csv_export` | `apps.reports` | HTTP 200 with `text/csv` streaming response | **PASS** |
| `test_qr_code_generation` | `apps.core` | Dynamic PNG base64 QR code data URI generation | **PASS** |
| `test_8d_pdf_export_view` | `apps.capa` | HTTP 200 and formal 8D PDF ReportLab generation | **PASS** |
| `test_ncr_red_tag_view` | `apps.ncr` | HTTP 200 printable Quality Hold / Red Tag view | **PASS** |
| `test_calibration_sticker_view` | `apps.calibration` | HTTP 200 printable Metrology Calibration sticker | **PASS** |
| `test_health_check_management_command` | `apps.core` | Full plant compliance health check execution | **PASS** |

