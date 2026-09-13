import urllib.request
import urllib.parse
import http.cookiejar
import re

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

base_url = "http://127.0.0.1:8000"

print("--- 1. Fetching Login Page ---")
login_page = opener.open(f"{base_url}/accounts/login/").read().decode('utf-8')
csrf_match = re.search(r"name=['\"]csrfmiddlewaretoken['\"]\s+value=['\"]([^'\"]+)['\"]", login_page)
if not csrf_match:
    csrf_match = re.search(r"value=['\"]([^'\"]+)['\"]\s+name=['\"]csrfmiddlewaretoken['\"]", login_page)

csrf_token = csrf_match.group(1) if csrf_match else ""
print(f"CSRF Token captured: {csrf_token[:15]}...")

print("\n--- 2. Logging in as Admin (admin / Admin@123456) ---")
login_data = urllib.parse.urlencode({
    'csrfmiddlewaretoken': csrf_token,
    'username': 'admin',
    'password': 'Admin@123456'
}).encode('utf-8')

req = urllib.request.Request(
    f"{base_url}/accounts/login/",
    data=login_data,
    headers={'Referer': f"{base_url}/accounts/login/"}
)
resp = opener.open(req)
print(f"Login response URL: {resp.geturl()} | Status: {resp.status}")

urls_to_test = [
    ("/", "Executive Dashboard"),
    ("/ncr/", "Nonconformity (NCR) List"),
    ("/ncr/1/", "NCR Detail View"),
    ("/ncr/1/red-tag/", "Printable Red / Hold Tag"),
    ("/capa/", "CAPA Register"),
    ("/capa/1/", "CAPA 8D Detail View"),
    ("/capa/1/8d-pdf/", "8D Problem Solving Report (PDF)"),
    ("/calibration/", "Calibration Master List"),
    ("/calibration/1/", "Equipment Metrology Detail"),
    ("/calibration/1/sticker/", "Printable Calibration Sticker"),
    ("/risks/", "Risks Register"),
    ("/risks/matrix/", "5x5 Risk Heat Map"),
    ("/actions/", "Action Central"),
    ("/actions/my-actions/", "My Personal Actions"),
    ("/training/", "Training & Competency Matrix"),
    ("/management-review/", "Management Review List"),
    ("/management-review/1/", "Management Review Detail"),
    ("/audits/", "Internal Audits Schedule"),
    ("/inspections/", "Quality Inspections"),
    ("/reports/", "Reports & Export Center"),
    ("/reports/export/?module=ncr&format=xlsx", "NCR Excel (.xlsx) Download"),
    ("/reports/export/?module=ncr&format=csv", "NCR CSV Download"),
    ("/core/settings/", "System Settings"),
    ("/core/audit-trail/", "Compliance Audit Trail"),
]

print("\n--- 3. Testing All Core Endpoints ---")
all_passed = True
for path, desc in urls_to_test:
    target = f"{base_url}{path}"
    try:
        r = opener.open(target, timeout=10)
        content_type = r.headers.get('Content-Type', '')
        size = len(r.read())
        print(f"[SUCCESS 200] {desc:36} -> {path:35} ({size:,} bytes | {content_type.split(';')[0]})")
    except Exception as e:
        print(f"[FAILED]      {desc:36} -> {path:35} ERROR: {e}")
        all_passed = False

if all_passed:
    print("\nSUCCESS: ALL 24 SYSTEM ENDPOINTS PASSED FLAWLESSLY WITH HTTP 200!")
else:
    print("\nSome endpoints encountered issues.")
