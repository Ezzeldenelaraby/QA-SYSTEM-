from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
from django.core import mail
from apps.core.notifications import send_qms_email

from apps.departments.models import Department
from apps.processes.models import Process
from apps.ncr.models import NCR
from apps.capa.models import CAPA
from apps.actions.models import Action
from apps.risks.models import Risk
from apps.calibration.models import Equipment

User = get_user_model()

class UserRolePermissionsTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Quality Assurance', code='QA')
        self.qa_manager = User.objects.create_user(
            username='qamgr',
            password='Password123!',
            first_name='QA',
            last_name='Manager',
            role=User.Role.QA_MANAGER,
            department=self.dept
        )
        self.operator = User.objects.create_user(
            username='op1',
            password='Password123!',
            first_name='Shop',
            last_name='Operator',
            role=User.Role.EMPLOYEE,
            department=self.dept
        )

    def test_role_properties(self):
        self.assertTrue(self.qa_manager.is_qa_staff)
        self.assertTrue(self.qa_manager.can_approve_documents())
        self.assertTrue(self.qa_manager.can_close_ncr())
        self.assertTrue(self.qa_manager.can_verify_capa())

        self.assertFalse(self.operator.is_qa_staff)
        self.assertFalse(self.operator.can_approve_documents())
        self.assertFalse(self.operator.can_close_ncr())
        self.assertFalse(self.operator.can_verify_capa())


class NCRWorkflowAndClosureValidationTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Machining Line 1', code='MCH')
        self.user = User.objects.create_user(
            username='inspector',
            password='Password123!',
            role=User.Role.QC_INSPECTOR,
            department=self.dept
        )
        self.process = Process.objects.create(
            name='CNC Milling',
            code='PRC-MCH-01',
            process_owner=self.user,
            department=self.dept,
            description='Precision CNC milling operations'
        )

    def test_ncr_auto_numbering(self):
        ncr = NCR.objects.create(
            product='Transmission Gear Pinion',
            batch_lot='LOT-2026-001',
            department=self.dept,
            process=self.process,
            reported_by=self.user,
            responsible_person=self.user,
            classification=NCR.Classification.MAJOR,
            severity=NCR.Severity.HIGH,
            description='Bore dimension 25.08mm out of spec 25.00 +/- 0.03mm',
            requirement='Technical Drawing DWG-MCH-001',
            containment_action='Parts quarantined with red hold tags',
            due_date=timezone.now().date() + timedelta(days=7)
        )
        self.assertTrue(ncr.ncr_number.startswith('NCR-'))

    def test_closure_validation_fails_without_root_cause(self):
        ncr = NCR.objects.create(
            product='Aluminum Casting Bracket',
            batch_lot='LOT-2026-002',
            department=self.dept,
            reported_by=self.user,
            responsible_person=self.user,
            classification=NCR.Classification.MINOR,
            severity=NCR.Severity.LOW,
            description='Surface porosity defect on non-machined face',
            requirement='Visual Inspection Standard VIS-01',
            containment_action='Inspected remaining lot',
            due_date=timezone.now().date() + timedelta(days=7)
        )
        # Attempt to mark closed without root_cause_summary, verification_notes, verified_by
        ncr.status = NCR.Status.CLOSED
        with self.assertRaises(ValidationError):
            ncr.clean()

    def test_closure_validation_succeeds_with_all_mandatory_fields(self):
        ncr = NCR.objects.create(
            product='Shaft Coupling',
            batch_lot='LOT-2026-003',
            department=self.dept,
            reported_by=self.user,
            responsible_person=self.user,
            classification=NCR.Classification.MINOR,
            severity=NCR.Severity.LOW,
            description='Tool wear offset error',
            requirement='Inspection Sheet IS-05',
            due_date=timezone.now().date() + timedelta(days=7),
            immediate_correction='Adjusted CNC tool wear offset by -0.025mm',
            containment_action='Machine paused and calibrated; 15 units sorted',
            root_cause_summary='Carbide insert worn past 150 machining cycles',
            verification_notes='Verified 5 consecutive parts 100% acceptable',
            verified_by=self.user,
            status=NCR.Status.CLOSED
        )
        # clean() should pass without raising ValidationError
        ncr.clean()
        ncr.save()
        self.assertEqual(ncr.status, NCR.Status.CLOSED)


class CAPAWorkflowAndValidationTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Assembly Line', code='ASM')
        self.champion = User.objects.create_user(
            username='lead_eng',
            password='Password123!',
            role=User.Role.QA_ENGINEER,
            department=self.dept
        )

    def test_capa_auto_numbering(self):
        capa = CAPA.objects.create(
            title='High scrap rate due to connector pin misalignment',
            responsible_person=self.champion,
            source=CAPA.Source.NCR,
            description='Crimping fixture misalignment causing bent terminal pins',
            root_cause='Loose locating dowel pin in assembly jig',
            corrective_action='Replaced fixture with hardened steel insert',
            preventive_action='Scheduled weekly jig torque checks',
            due_date=timezone.now().date() + timedelta(days=30),
            verification_method='Run 500 samples with zero defects'
        )
        self.assertTrue(capa.capa_number.startswith('CAPA-'))

    def test_capa_closure_guard_requires_effectiveness_review(self):
        capa = CAPA.objects.create(
            title='Packaging leakage investigation',
            responsible_person=self.champion,
            source=CAPA.Source.CUSTOMER,
            description='Heat seal temperature fluctuating',
            root_cause='Heater element wire degradation',
            corrective_action='Replaced heater element',
            preventive_action='Added thermocouple temperature alarm',
            due_date=timezone.now().date() + timedelta(days=30),
            verification_method='Pressure decay test on 50 consecutive pouches'
        )
        capa.status = CAPA.Status.CLOSED
        with self.assertRaises(ValidationError):
            capa.clean()

    def test_capa_closure_succeeds_with_effectiveness_review(self):
        capa = CAPA.objects.create(
            title='Packaging seal upgrade',
            responsible_person=self.champion,
            source=CAPA.Source.AUDIT,
            description='Thermal band degradation',
            root_cause='Thermocouple calibration drift',
            corrective_action='Replaced heater band',
            preventive_action='Added monthly calibration check',
            due_date=timezone.now().date() + timedelta(days=30),
            verification_method='Visual and seal leak test',
            status=CAPA.Status.CLOSED,
            completion_date=timezone.now().date(),
            verified_by=self.champion,
            effectiveness_result='Zero seal leaks detected across 30 days of production runs.'
        )
        capa.clean()
        capa.save()
        self.assertEqual(capa.status, CAPA.Status.CLOSED)


class RiskScoreCalculationTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Safety & Environment', code='EHS')
        self.owner = User.objects.create_user(
            username='ehs_lead',
            password='Password123!',
            role=User.Role.PROCESS_OWNER,
            department=self.dept
        )
        self.process = Process.objects.create(
            name='Hydraulic Stamping',
            code='PRC-EHS-01',
            process_owner=self.owner,
            department=self.dept,
            description='Heavy stamping press'
        )

    def test_risk_score_and_level_derivation(self):
        # Critical Risk: 4 * 4 = 16 (Critical >= 15)
        risk1 = Risk.objects.create(
            risk_id='RSK-001',
            process=self.process,
            department=self.dept,
            description='Hydraulic press fluid leak',
            cause='Seal degradation under high cycle rate',
            potential_consequence='Oil spill and production stoppage',
            responsible_person=self.owner,
            likelihood=4,
            severity=4
        )
        self.assertEqual(risk1.risk_score, 16)
        self.assertEqual(risk1.risk_level, Risk.RiskLevel.CRITICAL)

        # Low Risk: 1 * 2 = 2 (Low <= 4)
        risk2 = Risk.objects.create(
            risk_id='RSK-002',
            process=self.process,
            department=self.dept,
            description='Minor barcode label printer delay',
            cause='Ribbon runout',
            potential_consequence='5 minute dispatch delay',
            responsible_person=self.owner,
            likelihood=1,
            severity=2
        )
        self.assertEqual(risk2.risk_score, 2)
        self.assertEqual(risk2.risk_level, Risk.RiskLevel.LOW)


class ActionOverdueLogicTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Maintenance', code='MNT')
        self.user = User.objects.create_user(username='tech1', password='Password123!', department=self.dept)

    def test_action_overdue_property(self):
        yesterday = timezone.now().date() - timedelta(days=1)
        tomorrow = timezone.now().date() + timedelta(days=1)

        action_overdue = Action.objects.create(
            title='Inspect tooling calibration',
            assigned_to=self.user,
            department=self.dept,
            due_date=yesterday,
            status=Action.Status.IN_PROGRESS
        )
        self.assertTrue(action_overdue.is_overdue)

        action_future = Action.objects.create(
            title='Update work instruction',
            assigned_to=self.user,
            department=self.dept,
            due_date=tomorrow,
            status=Action.Status.OPEN
        )
        self.assertFalse(action_future.is_overdue)


class EquipmentCalibrationDateTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Tool Room', code='TLR')

    def test_calibration_date_auto_calculation(self):
        today = timezone.now().date()
        equip = Equipment.objects.create(
            equipment_id='CAL-MIC-99',
            equipment_name='Digital Outside Micrometer 0-25mm',
            department=self.dept,
            location='Inspection Bench 1',
            calibration_frequency_months=6,
            last_calibration_date=today
        )
        # Next calibration should be calculated 6 months later
        self.assertIsNotNone(equip.next_calibration_date)
        self.assertEqual(equip.status, Equipment.Status.VALID)


class DashboardAndReportsExportTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Quality Assurance', code='QA')
        self.user = User.objects.create_user(
            username='admin_tester',
            password='Password123!',
            is_staff=True,
            is_superuser=True,
            role=User.Role.SUPER_ADMIN,
            department=self.dept
        )
        self.client = Client()
        self.client.login(username='admin_tester', password='Password123!')

    def test_dashboard_view_loads_successfully(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Executive QMS Dashboard')

    def test_reports_excel_export(self):
        response = self.client.get(reverse('reports:export') + '?module=ncr&format=xlsx')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_reports_csv_export(self):
        response = self.client.get(reverse('reports:export') + '?module=ncr&format=csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')


from django.core.management import call_command
from apps.core.utils import generate_qr_code_base64

class EnterpriseEnhancementsTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Quality Assurance', code='QA')
        self.user = User.objects.create_user(
            username='qa_lead_enh',
            password='Password123!',
            is_staff=True,
            is_superuser=True,
            role=User.Role.QA_MANAGER,
            department=self.dept
        )
        self.client = Client()
        self.client.login(username='qa_lead_enh', password='Password123!')

        self.ncr = NCR.objects.create(
            product='Turbocharger Impeller',
            batch_lot='LOT-TURBO-01',
            department=self.dept,
            reported_by=self.user,
            responsible_person=self.user,
            classification=NCR.Classification.CRITICAL,
            severity=NCR.Severity.CRITICAL,
            description='Blade clearance out of specification',
            requirement='Drawing DWG-TRB-01',
            containment_action='Lot isolated in quarantine cage',
            due_date=timezone.now().date() + timedelta(days=5)
        )

        self.capa = CAPA.objects.create(
            title='Impeller blade clearance correction',
            responsible_person=self.user,
            related_ncr=self.ncr,
            source=CAPA.Source.NCR,
            description='Cutter head vibration during 5-axis pass',
            root_cause='Spindle bearing preload loss',
            corrective_action='Replaced high-speed spindle assembly',
            preventive_action='Installed continuous vibration monitoring sensor',
            due_date=timezone.now().date() + timedelta(days=20),
            verification_method='Vibration FFT analysis and 50 pcs dimensional check'
        )

        self.equipment = Equipment.objects.create(
            equipment_id='CAL-TOR-50',
            equipment_name='Digital Torque Wrench 10-100 Nm',
            department=self.dept,
            location='Assembly Cell 2',
            calibration_frequency_months=12,
            last_calibration_date=timezone.now().date()
        )

    def test_qr_code_generation(self):
        qr_uri = generate_qr_code_base64("https://qmshub.factory.internal/calibration/1/")
        self.assertTrue(qr_uri.startswith("data:image/png;base64,"))
        self.assertGreater(len(qr_uri), 100)

    def test_8d_pdf_export_view(self):
        response = self.client.get(reverse('capa:pdf_8d', kwargs={'capa_id': self.capa.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertGreater(len(response.content), 1000)

    def test_ncr_red_tag_view(self):
        response = self.client.get(reverse('ncr:red_tag', kwargs={'ncr_id': self.ncr.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'QUALITY HOLD')
        self.assertContains(response, self.ncr.ncr_number)

    def test_calibration_sticker_view(self):
        response = self.client.get(reverse('calibration:sticker', kwargs={'eq_id': self.equipment.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CALIBRATION CERTIFIED')
        self.assertContains(response, self.equipment.equipment_id)

    def test_health_check_management_command(self):
        call_command('run_quality_health_check')

    def test_health_check_management_command_with_digest(self):
        call_command('run_quality_health_check', send_digest=True)
        # Should execute cleanly without errors

    def test_send_qms_email_dispatches_html_and_text(self):
        result = send_qms_email(
            subject="Test Plant Notice",
            template_name="emails/base_email.html",
            context={'email_title': 'Notice Test'},
            recipient_list=['qa@factory.local']
        )
        self.assertTrue(result)
        self.assertGreater(len(mail.outbox), 0)
        sent = mail.outbox[-1]
        self.assertEqual(sent.subject, "[QMS Hub] Test Plant Notice")
        self.assertEqual(sent.to, ['qa@factory.local'])
        self.assertIn("Industrial QMS Hub", sent.body)

    def test_scan_lookup_equipment(self):
        url = reverse('core:scan_lookup') + f'?code={self.equipment.equipment_id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['found'])
        self.assertEqual(data['item']['type'], 'Equipment')
        self.assertIn(self.equipment.equipment_name, data['item']['title'])

    def test_scan_lookup_ncr(self):
        url = reverse('core:scan_lookup') + f'?code={self.ncr.ncr_number}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['found'])
        self.assertEqual(data['item']['type'], 'NCR')

    def test_scan_lookup_redirect_mode(self):
        url = reverse('core:scan_lookup') + f'?code={self.ncr.ncr_number}&redirect=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/ncr/{self.ncr.id}/")

    def test_scan_lookup_unknown_code(self):
        url = reverse('core:scan_lookup') + '?code=DOES_NOT_EXIST_XYZ'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['found'])

    def test_backup_database_command(self):
        from io import StringIO
        out = StringIO()
        call_command('backup_database', stdout=out)
        output = out.getvalue()
        self.assertIn("Successfully created backup archive", output)

    def test_trigger_backup_view(self):
        response = self.client.post(reverse('core:trigger_backup'))
        self.assertEqual(response.status_code, 302)


