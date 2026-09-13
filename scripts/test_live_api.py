import urllib.request
import urllib.parse
import json

base_url = "http://127.0.0.1:8000"

def request_json(path, data=None, token=None, method='GET'):
    url = f"{base_url}{path}"
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Token {token}'
    
    encoded_data = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            return e.code, json.loads(error_body)
        except Exception:
            return e.code, error_body

print("=" * 70)
print("   QMS HUB - REST API & ADVANCED INTEGRATIONS LIVE VERIFICATION")
print("=" * 70)

# 1. Obtain Auth Token
print("\n[Step 1] Requesting API Token for 'admin'...")
status, token_resp = request_json(
    "/api/v1/token/",
    data={'username': 'admin', 'password': 'Admin@123456'},
    method='POST'
)
assert status == 200, f"Token request failed: {token_resp}"
token = token_resp['token']
print(f" -> Token acquired successfully: {token[:12]}... (Status: {status})")

# 2. Query Live Quality KPIs
print("\n[Step 2] Fetching Live Quality KPIs Feed (/api/v1/dashboard/kpis/)...")
status, kpi_data = request_json("/api/v1/dashboard/kpis/", token=token)
assert status == 200
print(f" -> Response Status: {status} OK")
print(f" -> System Health: {kpi_data['system_health']}")
print(f" -> Metrics: Open NCRs={kpi_data['metrics']['open_ncrs']} | "
      f"Overdue Actions={kpi_data['metrics']['overdue_actions']} | "
      f"Compliance={kpi_data['metrics']['calibration_compliance_rate_pct']}%")

# 3. Shop-Floor Gauge Verification (Metrology Check before use)
print("\n[Step 3] Scanning Instrument Calibration Status (/api/v1/calibration/verify/EQ-CAL-001/)...")
status, calib_data = request_json("/api/v1/calibration/verify/EQ-CAL-001/", token=token)
assert status == 200, f"Equipment lookup failed: {calib_data}"
print(f" -> Instrument: {calib_data['equipment_name']} ({calib_data['equipment_id']})")
print(f" -> Status: {calib_data['status_display']} | Is Usable: {calib_data['is_usable']}")
print(f" -> Advisory: {calib_data['advisory']}")

# 4. Automated Vision / CMM Defect Report Ingestion
print("\n[Step 4] Ingesting Automated Defect from Machine Vision Camera (/api/v1/ncr/)...")
ncr_payload = {
    'date': '2026-09-13',
    'department': 1,
    'process': 1,
    'product': 'AI-Inspected Transmission Gear Tooth',
    'batch_lot': 'LOT-VISION-882',
    'source': 'INSPECTION',
    'classification': 'CRITICAL',
    'severity': 'CRITICAL',
    'status': 'OPEN',
    'due_date': '2026-09-16',
    'description': 'Micro-crack detected by Keyence AI Camera Vision System at tooth root #4.',
    'requirement': 'ISO 1328-1 Gear flank integrity specification.',
    'containment_action': 'Vision system triggered automatic pneumatic reject arm to scrap bin.',
}
status, ncr_resp = request_json("/api/v1/ncr/", data=ncr_payload, token=token, method='POST')
assert status == 201, f"NCR creation failed: {ncr_resp}"
print(f" -> NCR Registered via REST API! Assigned Number: {ncr_resp['ncr_number']} (ID: {ncr_resp['id']})")
print(f" -> Severity: {ncr_resp['severity']} | Product: {ncr_resp['product']}")

# 5. Automated CMM Inspection Ingestion with Out-of-Tolerance Trigger
print("\n[Step 5] Ingesting Digital Caliper / CMM Probe Batch Data (/api/v1/inspections/)...")
insp_payload = {
    'date': '2026-09-13',
    'process': 1,
    'product': 'Hydraulic Valve Spool',
    'batch_lot': 'LOT-VALVE-009',
    'machine': 'CNC Grinder #1',
    'shift': 'MORNING',
    'overall_result': 'OK',
    'comments': 'Streamed from Mitutoyo USB MeasurLink CMM Station',
    'items': [
        {
            'checkpoint_name': 'Outside Diameter Step A',
            'specification': '25.000 +/- 0.005 mm',
            'measured_value': '25.002 mm',
            'unit': 'mm',
            'result': 'OK',
            'comment': 'Within upper/lower control limits'
        },
        {
            'checkpoint_name': 'Outside Diameter Step B',
            'specification': '20.000 +/- 0.005 mm',
            'measured_value': '20.012 mm',
            'unit': 'mm',
            'result': 'NG',
            'comment': 'Over maximum specification by 0.007mm'
        }
    ]
}
status, insp_resp = request_json("/api/v1/inspections/", data=insp_payload, token=token, method='POST')
assert status == 201, f"Inspection creation failed: {insp_resp}"
print(f" -> Inspection logged: {insp_resp['inspection_number']} | Overall Result: {insp_resp['overall_result']}")
print(f" -> Auto-triggered Linked NCR ID: #{insp_resp['linked_ncr']}")

print("\n" + "=" * 70)
print("  ALL ADVANCED REST API INTEGRATION ENDPOINTS VERIFIED 100% OPERATIONAL!")
print("=" * 70)
