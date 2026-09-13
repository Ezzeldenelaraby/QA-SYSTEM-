import csv
import io
import openpyxl
from io import BytesIO
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User
from apps.departments.models import Department
from apps.calibration.models import Equipment
from apps.objectives.models import QualityObjective


class ReportsAndBulkImportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(
            name="Quality Control",
            code="QA",
            description="Quality assurance and laboratory"
        )
        self.admin = User.objects.create_superuser(
            username="admin_test",
            email="admin_test@factory.local",
            password="AdminPassword123!",
            role=User.Role.SUPER_ADMIN,
            department=self.dept
        )
        self.client.force_login(self.admin)

    def test_report_index_view(self):
        url = reverse('reports:index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reports & Data Exports")
        self.assertContains(response, "Bulk Import Wizard")

    def test_export_ncr_xlsx(self):
        url = reverse('reports:export') + '?module=ncr&format=xlsx'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_export_ncr_csv(self):
        url = reverse('reports:export') + '?module=ncr&format=csv'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_download_import_templates(self):
        for m in ['equipment', 'users', 'departments', 'objectives']:
            url = reverse('reports:download_template', kwargs={'model_type': m})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            self.assertTrue(response['Content-Disposition'].startswith('attachment; filename='))

    def test_bulk_import_equipment_dry_run_and_commit(self):
        # 1. Prepare sample Excel file
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append([
            'Equipment ID', 'Equipment Name', 'Category', 'Manufacturer',
            'Model', 'Serial Number', 'Department Code', 'Location',
            'Calibration Frequency Months', 'Last Calibration Date (YYYY-MM-DD)'
        ])
        ws.append([
            'EQ-TEST-99', 'Digital Caliper 150mm', 'CALIPER', 'Mitutoyo',
            '500-196', 'SN-TEST-999', 'QA', 'Lab Station 1',
            '12', '2024-01-01'
        ])
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        buf.name = 'test_equipment.xlsx'

        # 2. Stage 1: Dry-Run Validation
        url = reverse('reports:bulk_import')
        response = self.client.post(url, {
            'model_type': 'equipment',
            'commit': '0',
            'import_file': buf
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pre-Flight Validation Report")
        self.assertContains(response, "EQ-TEST-99")
        self.assertContains(response, "Ready to Commit")

        # Verify it was cached in session
        session_data = self.client.session.get('bulk_import_pending')
        self.assertIsNotNone(session_data)
        self.assertEqual(len(session_data['valid_rows']), 1)

        # 3. Stage 2: Commit
        commit_response = self.client.post(url, {
            'model_type': 'equipment',
            'commit': '1'
        })
        self.assertEqual(commit_response.status_code, 302)
        self.assertTrue(Equipment.objects.filter(equipment_id='EQ-TEST-99').exists())
        eq = Equipment.objects.get(equipment_id='EQ-TEST-99')
        self.assertEqual(eq.serial_number, 'SN-TEST-999')
        self.assertEqual(eq.department, self.dept)
