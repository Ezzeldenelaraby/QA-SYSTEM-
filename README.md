# 🏭 QMS Hub - Industrial Quality Management System
### Production-Ready ISO 9001:2015 & IATF 16949 QMS Web Application

---

## 📌 1. Overview / نظرة عامة

**QMS Hub** is a full-featured, enterprise-grade Quality Assurance & Quality Management System (QA/QMS) designed specifically for industrial manufacturing plants. Engineered in accordance with international quality standards (**ISO 9001:2015** and **IATF 16949**), it eliminates fragmented spreadsheets and paper silos by unifying shopfloor nonconformities, 8D CAPA investigations, 5x5 risk management, calibration intervals, competency matrixes, management reviews, and audit trails into a cohesive, secure web platform.

**نظام QMS Hub** هو تطبيق ويب متكامل ومصمم للعمل في بيئات الإنتاج الصناعي والمصانع وفق معايير الجودة العالمية ISO 9001 و IATF 16949 لإدارة توكيد وضبط الجودة، متابعة حالات عدم المطابقة NCR، الإجراءات التصحيحية والوقائية CAPA، تحليل الأسباب الجذرية (5 Whys و Fishbone Diagram)، سجل المخاطر 5x5، معايرة أجهزة القياس، مصفوفة تدريب وكفاءة العاملين، واجتماعات مراجعة الإدارة.

---

## 🛠️ 2. Technology Stack / التقنيات المستخدمة

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend** | Python 3.12+ / Django 5.1+ | Robust enterprise application framework |
| **Database** | PostgreSQL (Production) / SQLite (Dev) | Relational data integrity, ACID transactions, soft delete |
| **Frontend** | Bootstrap 5.3 + Bootstrap Icons | Responsive industrial UI, accessible and clean corporate theme |
| **Charts & Metrics**| Chart.js (CDN) | Real-time interactive dashboards and KPI graphs |
| **Reporting & Export**| `openpyxl` & Python `csv` | Formatted `.xlsx` and `.csv` streaming downloads |
| **Static Assets** | WhiteNoise | Production static asset compression and caching |
| **WSGI Server** | Gunicorn | High-performance production WSGI application server |
| **Config & Secrets** | `python-dotenv` / Environment Variables | Zero hardcoded credentials (12-Factor App methodology) |
| **Deployment** | Railway / Docker / Nixpacks | Production cloud deployment ready |

---

## 🏛️ 3. Modular Architecture (18 Apps) / البنية المعمارية

```text
qms_hub/
├── config/                  # Django project configuration (settings, urls, wsgi)
├── static/                  # Corporate navy theme, custom styles, app.js
│   ├── css/custom.css       # 5x5 risk matrix grid, badges, sidebar styling
│   └── js/app.js            # Live calculations, notifications API, auto-dismiss alerts
├── templates/               # Modular Django templates extending base.html
│   ├── base.html            # Navigation sidebar, topbar search, notifications dropdown
│   ├── 403.html, 404.html, 500.html
│   └── [app_folders]/       # Granular CRUD templates for each module
├── apps/
│   ├── accounts/            # Custom User model, 10 industrial roles, RBAC decorators
│   ├── actions/             # Action Central, automated numbering, overdue detection
│   ├── api/                 # Django REST Framework (Token Auth, ERP/MES/IoT integration)
│   ├── audits/              # Internal audit schedules, checklists, finding escalation
│   ├── calibration/         # Equipment master list, dynamic 30-day/expired alerts
│   ├── capa/                # 8D Corrective actions, effectiveness verification guards
│   ├── core/                # TimeStampedModel, SoftDeleteModel, audit logs, middleware
│   ├── dashboard/           # Executive KPI aggregations and Chart.js datasets
│   ├── departments/         # Production areas, machining, assembly, stamping, lab
│   ├── documents/           # SOP control, revisions, workflows (Draft -> Approved)
│   ├── inspections/         # Receiving, in-process, final QC, 1-click NCR conversion
│   ├── management_review/   # ISO 9001 Clause 9.3 input/output compliance records
│   ├── ncr/                 # Nonconformities, 5-Whys, Fishbone diagram, closure guards
│   ├── notifications/       # User alert feeds, unread badges, AJAX read mark
│   ├── objectives/          # Quality KPIs, monthly tracking, performance charts
│   ├── processes/           # Process mapping (SIPOC, inputs, tools, quality gates)
│   ├── reports/             # Multi-module Excel (.xlsx) and CSV streaming exports
│   ├── risks/               # ISO 9001 Clause 6.1 5x5 risk matrix & mitigation plans
│   └── training/            # Competency matrix (Employee x Course), certificate tracking
├── Procfile                 # Railway process declaration
├── railway.json             # Railway Nixpacks deployment instructions
├── runtime.txt              # Python runtime pinning
├── requirements.txt         # Production dependencies
└── .env.example             # Template for environment variables
```

---

## ⚙️ 4. Local Development Setup / خطوات التثبيت والتشغيل المحلي

### 1. Clone the repository
```bash
git clone https://github.com/your-username/qms_hub.git
cd qms_hub
```

### 2. Create and activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure your `.env` contains:
```ini
SECRET_KEY=your-secure-random-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.railway.app
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,https://*.railway.app
DATABASE_URL=
```
*(Leave `DATABASE_URL` blank for local development to use SQLite automatically).*

### 5. Apply Database Migrations
```bash
python manage.py migrate
```

### 6. Seed Complete Demo Data
To populate the database with realistic industrial records across all 18 modules (Departments, Processes, Users, Documents, Risks, NCRs, 5-Whys, Fishbone, CAPAs, Actions, Audits, Inspections, Calibration, Training, and Reviews):
```bash
python manage.py seed_demo_data
```

### 7. Run Local Development Server
```bash
python manage.py runserver
```
Navigate to: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 🔑 5. Default Credentials & Role Matrix / بيانات تسجيل الدخول

The demo seeder provisions user accounts across all 10 specialized roles:

| Username | Password | Role / Function | Key Permissions |
| :--- | :--- | :--- | :--- |
| **`admin`** | `Admin@123456` | Super Admin / Plant Director | Full system administration, settings, audits |
| **`m.khalil`** | `Password@123` | QA Manager | Approve documents, close NCRs, sign off CAPAs |
| **`y.mansoor`** | `Password@123` | QA Engineer | Investigate NCRs, lead 5-Whys & Fishbone, CAPA |
| **`t.hassan`** | `Password@123` | QC Inspector | Log inspections, raise NCRs with red tags |
| **`h.salem`** | `Password@123` | Production Manager | Department oversight, assign containment |
| **`m.fawzy`** | `Password@123` | Department Head (Machining) | Review departmental risks and action items |
| **`a.samir`** | `Password@123` | Process Owner (Stamping) | Maintain process maps, SIPOC gates |
| **`s.radwan`** | `Password@123` | Quality Auditor | Conduct audits, log nonconformances |
| **`k.nabil`** | `Password@123` | Shop Floor Technician | Complete assigned actions, view training |
| **`n.zaher`** | `Password@123` | Management Viewer | Executive read-only visibility |

---

## 🧪 6. Running Automated Tests / تشغيل الاختبارات الآلية

The application includes a comprehensive test suite covering RBAC permissions, NCR closure guard validations, CAPA verification requirements, risk score calculations, action overdue logic, and data exports.

Execute the test suite:
```bash
python manage.py test apps.core
```
Output:
```text
Ran 18 tests in ~28s
OK (0 failures, 0 errors)
```

---

## 🚀 7. Production Deployment to Railway / النشر على منصة Railway

QMS Hub is pre-configured with `Procfile`, `railway.json`, and `WhiteNoise` for zero-friction deployment on **Railway**:

### Step 1: Push Code to GitHub
```bash
git init
git add .
git commit -m "Initial commit: Production-ready QMS Hub"
git branch -M main
git remote add origin https://github.com/your-username/qms_hub.git
git push -u origin main
```

### Step 2: Create Railway Project
1. Log in to [Railway.app](https://railway.app/).
2. Click **New Project** &rarr; **Deploy from GitHub repo**.
3. Select your `qms_hub` repository.

### Step 3: Add PostgreSQL Database
1. Inside your Railway project canvas, click **New** &rarr; **Database** &rarr; **Add PostgreSQL**.
2. Railway will automatically provision a production PostgreSQL instance and expose the `DATABASE_URL` variable.

### Step 4: Configure Environment Variables in Railway
Under the Web Service **Variables** tab, configure:
- `SECRET_KEY` = `<Generate a long random string>`
- `DEBUG` = `False`
- `ALLOWED_HOSTS` = `.railway.app,yourcustomdomain.com`
- `CSRF_TRUSTED_ORIGINS` = `https://*.railway.app,https://yourcustomdomain.com`
- `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` *(Automatically linked by Railway)*

### Step 5: Automatic Build & Deployment
Railway detects `railway.json` and `Procfile`, automatically:
1. Installs Python 3.12 via Nixpacks.
2. Installs requirements via `pip install -r requirements.txt`.
3. Runs `python manage.py migrate`.
4. Runs `python manage.py collectstatic --noinput`.
5. Starts Gunicorn: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`.

### Step 6: Initial Superuser / Data Seeding on Production
Use the Railway Web Terminal or Railway CLI:
```bash
railway run python manage.py seed_demo_data
# or create custom admin
railway run python manage.py createsuperuser
```

---

## 🧭 8. System Route Map / خريطة الروابط الرئيسية

| Module | URL | Description |
| :--- | :--- | :--- |
| **Executive Dashboard** | `/` | Real-time KPIs, Chart.js trends, calibration watchlist |
| **Processes (SIPOC)** | `/processes/` | Process registry, parameters, and 360° traceability |
| **Documents (SOPs)** | `/documents/` | Version-controlled documents, approvals, revisions |
| **Risk Register (5x5)** | `/risks/` | ISO 9001 Clause 6.1 matrix and mitigation tracker |
| **Risk Matrix 5x5 Grid** | `/risks/matrix/` | Interactive heat map visualization |
| **Quality Objectives** | `/objectives/` | Measurable targets, monthly trends, status cards |
| **Nonconformance (NCR)** | `/ncr/` | Defect logging, 5-Whys, Fishbone diagram |
| **CAPA Management** | `/capa/` | 8D corrective actions & effectiveness verification |
| **Action Central** | `/actions/` | Cross-module action tracker with overdue alerts |
| **My Actions** | `/actions/my-actions/` | Personal task workspace for logged-in user |
| **Internal Audits** | `/audits/` | Annual audit schedule, checklists, and findings |
| **Quality Inspections** | `/inspections/` | Receiving, in-process & final QC, auto-NCR creation |
| **SPC & Process Capability** | `/inspections/spc/` | IATF 16949 Cp/Cpk calculation & dynamic control charts |
| **Calibration Registry** | `/calibration/` | Measurement equipment, intervals, 30-day alerts |
| **Training Matrix** | `/training/` | Employee competency grid & qualification tracker |
| **Management Review** | `/management-review/` | ISO 9001 Clause 9.3 agenda, minutes & sign-off |
| **Reports & Exports** | `/reports/` | Excel (.xlsx) & CSV downloads across all modules |
| **8D Problem Report PDF** | `/capa/<id>/8d-pdf/` | Automotive & aerospace formal 8D PDF export |
| **Material Hold Tag** | `/ncr/<id>/red-tag/` | Printable Red Tag with QR code for quarantined lots |
| **Metrology Calibration Tag** | `/calibration/<id>/sticker/` | Printable calibration sticker with QR code |
| **System Settings** | `/core/settings/` | Plant name, thresholds, calibration interval config |
| **Audit Trail** | `/core/audit-trail/` | Immutable log of all system changes with user stamps |
| **API Developer Portal** | `/api/v1/docs/` | Interactive developer documentation and testing suite |
| **Liveness & Health Probe**| `/health/` | Production container and Kubernetes liveness probe |
| **REST API Token Auth** | `/api/v1/token/` | Obtain API authentication token for external systems |
| **REST API - NCRs** | `/api/v1/ncr/` | Automated defect ingestion from vision cameras / MES |
| **REST API - QC Ingestion**| `/api/v1/inspections/` | Measurement streaming from digital calipers & CMM |
| **REST API - Calibration** | `/api/v1/calibration/verify/<serial>/` | Fast gauge status check before shop-floor checkout |
| **REST API - Live KPIs** | `/api/v1/dashboard/kpis/` | Real-time JSON feed for factory-floor Andon TV screens |

---

## ⚡ 9. Industrial REST API & Hardware Integrations

QMS Hub includes an industrial REST API layer powered by **Django REST Framework** for automated factory integration:

### 1. Token Authentication:
```http
POST /api/v1/token/
Content-Type: application/json

{"username": "admin", "password": "Admin@123456"}
```
Response:
```json
{"token": "580f359bd910..."}
```

Include the token in headers: `Authorization: Token 580f359bd910...`

### 2. Automated Defect Reporting (Vision Systems & Line Tablets):
`POST /api/v1/ncr/`: Allows Keyence / Cognex vision inspection cameras or automated sorting gates to report defects directly into QMS with zero human data-entry delay.

### 3. Digital Gauges & CMM Probe Ingestion:
`POST /api/v1/inspections/`: Stream digital micrometer, caliper, and CMM batch readings. If any checkpoint is out-of-tolerance (`result = 'NG'`), an NCR is auto-generated and linked immediately.

### 4. Live Gauge Checkout Verification:
`GET /api/v1/calibration/verify/<serial_number>/`: Tool-crib barcoding station scans the gauge before issuing it to a machine operator. If expired, returns `"allow_checkout": false` and `"advisory": "DO NOT USE"`.

### 5. Shop-Floor TV / Andon Screen Metrics:
`GET /api/v1/dashboard/kpis/`: Provides real-time JSON feed with open NCR counts, overdue actions, open CAPAs, and calibration compliance rate.

---

## 📧 10. Automated Email Alerting System (SMTP)

QMS Hub features an automated notification and email engine delivering styled industrial HTML alerts:

* **Critical Defect Escalation:** Automatically emails QA Leadership and Department Heads when a `CRITICAL` NCR is raised.
* **Metrology Due Warnings:** Warns calibration technicians 30 days before gauge expiry.
* **Daily Compliance Digest:** Emails an executive health summary to the plant QA Manager.

### Environment Configuration:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_sendgrid_or_smtp_password
DEFAULT_FROM_EMAIL=alerts@yourfactory-qms.com
```
*(In local development or when unconfigured, falls back cleanly to the console backend without blocking requests).*

---

## ⏰ 11. Scheduled Compliance Automation (Cron)

Run plant compliance scans daily:
```bash
python manage.py run_quality_health_check --send-digest
```
* **Windows:** Use `scripts/run_daily_health_check.bat` with **Windows Task Scheduler** to trigger daily at 08:00 AM.
* **Railway / Cloud:** Configure a Railway Cron service or Cloud Scheduler to trigger the management command daily.

---

## 🔒 12. Key Business Rules & Quality Assurance Logic

1. **Strict NCR Closure Guard**:
   An NCR cannot be closed (`status = 'CLOSED'`) until containment actions, root-cause summary, verification notes, and authorized QA sign-off are fully completed.
2. **CAPA Effectiveness Verification**:
   A CAPA cannot be closed without documented effectiveness verification evidence proving that the root cause has been permanently mitigated without recurrence.
3. **Dynamic 5x5 Risk Rating**:
   Risk score is dynamically calculated as $\text{Score} = \text{Likelihood (1-5)} \times \text{Severity (1-5)}$. Risks with score $\ge 15$ are automatically classified as `CRITICAL`, and $\ge 10$ as `HIGH`.
4. **Automated Equipment Calibration Lifecycle**:
   Equipment calibration deadlines are calculated automatically from calibration frequency intervals. Active gauges entering within the 30-day window automatically trigger warnings; overdue equipment triggers hard warnings and appears on the executive dashboard watchlist.
5. **Soft Delete & Full Audit Trail**:
   All core records inherit `SoftDeleteModel` to prevent accidental loss of compliance data. Every record modification is stamped by the `AuditLogMiddleware` with user ID, IP address, timestamp, and action description.
6. **Mobile QR Code Verification**:
   Instant base64 QR code generation on measurement instruments and rejected material hold tags, allowing operators to verify compliance live from any mobile device on the shopfloor.
7. **Daily Quality Health Check Cron Command**:
   Execute `python manage.py run_quality_health_check` to run plant-wide automated scans that detect expired calibration, overdue actions, and expiring employee training certifications.

---

## 📄 License & Ownership
Engineered for industrial manufacturing plants adhering to ISO 9001:2015 and IATF 16949 quality standards.
All rights reserved.
