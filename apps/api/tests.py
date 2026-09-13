from django.test import TestCase
from django.utils import timezone
from django.core import mail
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from apps.accounts.models import User
from apps.departments.models import Department
from apps.processes.models import Process
from apps.ncr.models import NCR
from apps.calibration.models import Equipment
from apps.inspections.models import Inspection

class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.dept = Department.objects.create(name='Machining', code='MCH')
        self.process = Process.objects.create(name='CNC Lathe', code='PROC-CNC', department=self.dept)

        self.qa_manager = User.objects.create_user(
            username='qamgr',
            email='qamgr@factory.local',
            password='Password123!',
            role=User.Role.QA_MANAGER
        )
        self.token = Token.objects.create(user=self.qa_manager)

        self.gauge_valid = Equipment.objects.create(
            equipment_id='MIC-TEST-01',
            equipment_name='Digital Micrometer',
            category=Equipment.Category.MICROMETER,
            serial_number='SN-MIC-01',
            department=self.dept,
            location='CNC Line 1',
            status=Equipment.Status.VALID,
            last_calibration_date=timezone.now().date(),
            next_calibration_date=timezone.now().date() + timezone.timedelta(days=180)
        )

        self.gauge_expired = Equipment.objects.create(
            equipment_id='CALIPER-EXP-01',
            equipment_name='Shop Caliper',
            category=Equipment.Category.CALIPER,
            serial_number='SN-CAL-EXP',
            department=self.dept,
            location='Tool Crib',
            status=Equipment.Status.EXPIRED,
            last_calibration_date=timezone.now().date() - timezone.timedelta(days=400),
            next_calibration_date=timezone.now().date() - timezone.timedelta(days=35)
        )

    def test_unauthenticated_request_rejected(self):
        resp = self.client.get('/api/v1/ncr/')
        self.assertEqual(resp.status_code, 401)

    def test_token_authenticated_get_ncr(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        resp = self.client.get('/api/v1/ncr/')
        self.assertEqual(resp.status_code, 200)

    def test_ncr_creation_via_api(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        payload = {
            'date': timezone.now().date().isoformat(),
            'department': self.dept.id,
            'process': self.process.id,
            'product': 'Robotic Arm Joint Pin',
            'batch_lot': 'LOT-PIN-900',
            'source': 'INSPECTION',
            'classification': 'MAJOR',
            'severity': 'HIGH',
            'status': 'OPEN',
            'due_date': (timezone.now().date() + timezone.timedelta(days=7)).isoformat(),
            'description': 'Pinhole porosity detected on bearing contact surface.',
            'requirement': 'Zero porosity allowed per ASTM E155 standard.',
            'containment_action': 'Hold 120 pins in quarantine bin.',
        }
        resp = self.client.post('/api/v1/ncr/', payload, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(NCR.objects.filter(product='Robotic Arm Joint Pin').exists())
        created_ncr = NCR.objects.get(product='Robotic Arm Joint Pin')
        self.assertEqual(created_ncr.reported_by, self.qa_manager)

    def test_critical_ncr_via_api_dispatches_email(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        payload = {
            'date': timezone.now().date().isoformat(),
            'department': self.dept.id,
            'process': self.process.id,
            'product': 'Engine Mount Bracket',
            'batch_lot': 'LOT-EMB-101',
            'source': 'INSPECTION',
            'classification': 'CRITICAL',
            'severity': 'CRITICAL',
            'status': 'OPEN',
            'due_date': timezone.now().date().isoformat(),
            'description': 'Structural crack observed along primary weld seam.',
            'requirement': 'Weld structural integrity standard AWS D1.1.',
            'containment_action': 'Stop assembly line immediately.',
        }
        resp = self.client.post('/api/v1/ncr/', payload, format='json')
        self.assertEqual(resp.status_code, 201)
        # Verify email was dispatched
        self.assertGreater(len(mail.outbox), 0)
        email = mail.outbox[-1]
        self.assertIn("CRITICAL DEFECT ALERT", email.subject)
        self.assertIn("Engine Mount Bracket", email.body)

    def test_calibration_verify_api_valid_gauge(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        resp = self.client.get(f'/api/v1/calibration/verify/{self.gauge_valid.equipment_id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['is_usable'])
        self.assertTrue(resp.data['allow_checkout'])
        self.assertEqual(resp.data['status'], 'VALID')

    def test_calibration_verify_api_expired_gauge(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        resp = self.client.get(f'/api/v1/calibration/verify/{self.gauge_expired.serial_number}/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['is_usable'])
        self.assertFalse(resp.data['allow_checkout'])
        self.assertIn("DO NOT USE", resp.data['advisory'])

    def test_calibration_verify_api_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        resp = self.client.get('/api/v1/calibration/verify/NONEXISTENT-999/')
        self.assertEqual(resp.status_code, 404)

    def test_inspection_ingestion_api_with_ng_triggers_ncr(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        payload = {
            'date': timezone.now().date().isoformat(),
            'process': self.process.id,
            'product': 'Cylinder Sleeve',
            'batch_lot': 'LOT-CS-44',
            'machine': 'CNC Bore Mill #2',
            'shift': 'MORNING',
            'overall_result': 'OK',
            'comments': 'Automated CMM probe test',
            'items': [
                {
                    'checkpoint_name': 'Inner Bore Diameter',
                    'specification': '80.00 +/- 0.01 mm',
                    'measured_value': '80.05 mm',
                    'unit': 'mm',
                    'result': 'NG',
                    'comment': 'Over upper tolerance limit'
                }
            ]
        }
        resp = self.client.post('/api/v1/inspections/', payload, format='json')
        self.assertEqual(resp.status_code, 201)
        inspection_id = resp.data['id']
        inspection = Inspection.objects.get(id=inspection_id)
        # Overall result should have turned to NG
        self.assertEqual(inspection.overall_result, 'NG')
        # Linked NCR should have been automatically generated
        self.assertIsNotNone(inspection.linked_ncr)
        self.assertEqual(inspection.linked_ncr.product, 'Cylinder Sleeve')

    def test_dashboard_kpis_api(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        resp = self.client.get('/api/v1/dashboard/kpis/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('system_health', resp.data)
        self.assertIn('metrics', resp.data)
        self.assertIn('calibration_compliance_rate_pct', resp.data['metrics'])
