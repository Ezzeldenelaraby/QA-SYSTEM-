from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User
from apps.departments.models import Department
from apps.processes.models import Process
from apps.inspections.models import Inspection, InspectionItem
from apps.ncr.models import NCR

class SPCTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Machining', code='MCH')
        self.process = Process.objects.create(name='CNC Turning', code='CNC-01', department=self.dept)
        self.user = User.objects.create_user(
            username='inspector_spc',
            password='Password123!',
            role=User.Role.QC_INSPECTOR,
            department=self.dept
        )
        self.client.login(username='inspector_spc', password='Password123!')

    def test_spc_analysis_default_calculation(self):
        resp = self.client.get(reverse('inspections:spc'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('cpk', resp.context)
        self.assertIn('cp', resp.context)
        self.assertIn('mean', resp.context)
        self.assertIn('std_dev', resp.context)
        self.assertGreater(resp.context['cpk'], 0)
        self.assertEqual(resp.context['sample_size'], 25)

    def test_spc_analysis_custom_samples(self):
        url = reverse('inspections:spc') + "?feature=Shaft+Step&usl=20.05&lsl=19.95&target=20.00&samples=20.01,20.02,19.99,20.00,20.01,20.03,19.98,20.00"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['sample_size'], 8)
        self.assertAlmostEqual(resp.context['mean'], 20.005, places=3)
        self.assertIn('verdict', resp.context)

    def test_inspection_create_ncr_flow(self):
        insp = Inspection.objects.create(
            process=self.process,
            product='Drive Gear',
            batch_lot='LOT-G1',
            machine='Gear Hobber #1',
            inspector=self.user,
            overall_result=Inspection.Result.NG
        )
        InspectionItem.objects.create(
            inspection=insp,
            checkpoint_name='Tooth Pitch Diameter',
            specification='50.00 +/- 0.02 mm',
            measured_value='50.08 mm',
            unit='mm',
            result=InspectionItem.ItemResult.NG
        )
        resp = self.client.get(reverse('inspections:create_ncr', kwargs={'insp_id': insp.id}))
        self.assertEqual(resp.status_code, 302)
        insp.refresh_from_db()
        self.assertIsNotNone(insp.linked_ncr)
        self.assertEqual(insp.linked_ncr.product, 'Drive Gear')
