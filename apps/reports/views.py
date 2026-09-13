import csv
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, Http404
from django.utils import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta

from apps.core.utils import log_audit
from apps.accounts.models import User
from apps.objectives.models import QualityObjective
from apps.ncr.models import NCR
from apps.capa.models import CAPA
from apps.actions.models import Action
from apps.risks.models import Risk
from apps.inspections.models import Inspection
from apps.calibration.models import Equipment
from apps.training.models import TrainingRecord
from apps.audits.models import AuditFinding
from apps.departments.models import Department

@login_required
def report_index(request):
    departments = Department.objects.all()
    return render(request, 'reports/index.html', {
        'departments': departments,
        'today': timezone.now().date(),
    })

@login_required
def export_dataset(request):
    module = request.GET.get('module', 'ncr')
    export_format = request.GET.get('format', 'xlsx')
    dept_id = request.GET.get('department')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Prepare datasets based on module
    headers, rows, filename_prefix = get_module_data(module, dept_id, start_date, end_date)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{filename_prefix}_{timestamp}.{export_format}"

    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        return response

    elif export_format == 'xlsx':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = module.upper()

        # Styles
        header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        regular_font = Font(name="Calibri", size=10)
        thin_border = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )

        # Write Header
        ws.append(headers)
        for col_num, cell in enumerate(ws[1], 1):
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Write Data
        for row in rows:
            ws.append(row)

        # Apply borders and auto-fit columns
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(headers)):
            for cell in row:
                cell.font = regular_font
                cell.border = thin_border

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    return HttpResponse("Invalid format", status=400)


def get_module_data(module, dept_id=None, start_date=None, end_date=None):
    if module == 'ncr':
        qs = NCR.objects.select_related('department', 'reported_by', 'process').all()
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)
        
        headers = ['NCR Number', 'Product', 'Severity', 'Status', 'Department', 'Process', 'Reported By', 'Created Date', 'Containment Action', 'Root Cause']
        rows = [
            [
                n.ncr_number,
                n.product,
                n.get_severity_display(),
                n.get_status_display(),
                n.department.name if n.department else '',
                n.process.code if n.process else '',
                n.reported_by.full_name if n.reported_by else '',
                n.created_at.strftime('%Y-%m-%d %H:%M'),
                n.containment_action,
                n.root_cause_summary
            ]
            for n in qs
        ]
        return headers, rows, 'NCR_Report'

    elif module == 'capa':
        qs = CAPA.objects.select_related('responsible_person', 'responsible_person__department', 'related_ncr').all()
        if dept_id:
            qs = qs.filter(responsible_person__department_id=dept_id)
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)
        
        headers = ['CAPA Number', 'Title', 'Source', 'Status', 'Department', 'Responsible Person', 'Related NCR', 'Due Date', 'Effectiveness Result', 'Created Date']
        rows = [
            [
                c.capa_number,
                c.title,
                c.get_source_display(),
                c.get_status_display(),
                c.responsible_person.department.name if c.responsible_person and c.responsible_person.department else '',
                c.responsible_person.full_name if c.responsible_person else '',
                c.related_ncr.ncr_number if c.related_ncr else '',
                c.due_date.strftime('%Y-%m-%d') if c.due_date else '',
                c.effectiveness_result,
                c.created_at.strftime('%Y-%m-%d')
            ]
            for c in qs
        ]
        return headers, rows, 'CAPA_Report'

    elif module == 'actions':
        qs = Action.objects.select_related('assigned_to', 'department').all()
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)
        
        headers = ['Action Number', 'Title', 'Source Type', 'Source ID', 'Assignee', 'Department', 'Priority', 'Status', 'Due Date', 'Completed Date']
        rows = [
            [
                a.action_number,
                a.title,
                a.get_source_type_display(),
                a.source_id or '',
                a.assigned_to.full_name if a.assigned_to else '',
                a.department.name if a.department else '',
                a.get_priority_display(),
                a.get_status_display(),
                a.due_date.strftime('%Y-%m-%d') if a.due_date else '',
                a.completed_at.strftime('%Y-%m-%d') if a.completed_at else ''
            ]
            for a in qs
        ]
        return headers, rows, 'Actions_Report'

    elif module == 'risks':
        qs = Risk.objects.select_related('department', 'process', 'responsible_person').all()
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        
        headers = ['Risk ID', 'Description', 'Process', 'Likelihood (1-5)', 'Severity (1-5)', 'Score', 'Risk Level', 'Status', 'Department', 'Responsible Person', 'Existing Control']
        rows = [
            [
                r.risk_id,
                r.description,
                r.process.code if r.process else '',
                r.likelihood,
                r.severity,
                r.risk_score,
                r.get_risk_level_display(),
                r.get_status_display(),
                r.department.name if r.department else '',
                r.responsible_person.full_name if r.responsible_person else '',
                r.existing_control
            ]
            for r in qs
        ]
        return headers, rows, 'Risks_Register_Report'

    elif module == 'calibration':
        qs = Equipment.objects.select_related('department').all()
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        
        headers = ['Equipment ID', 'Name', 'Model', 'Serial Number', 'Department', 'Location', 'Interval (Months)', 'Last Calibration', 'Next Calibration', 'Status']
        rows = [
            [
                e.equipment_id,
                e.equipment_name,
                e.model,
                e.serial_number,
                e.department.name if e.department else '',
                e.location,
                e.calibration_frequency_months,
                e.last_calibration_date.strftime('%Y-%m-%d') if e.last_calibration_date else '',
                e.next_calibration_date.strftime('%Y-%m-%d') if e.next_calibration_date else '',
                e.get_status_display()
            ]
            for e in qs
        ]
        return headers, rows, 'Calibration_Equipment_Report'

    elif module == 'training':
        qs = TrainingRecord.objects.select_related('employee', 'course').all()
        if dept_id:
            qs = qs.filter(employee__department_id=dept_id)
        
        headers = ['Employee', 'Employee ID', 'Course Code', 'Course Title', 'Trainer', 'Training Date', 'Expiry Date', 'Result', 'Competency']
        rows = [
            [
                t.employee.full_name,
                t.employee.username,
                t.course.code,
                t.course.title,
                t.trainer,
                t.training_date.strftime('%Y-%m-%d'),
                t.expiry_date.strftime('%Y-%m-%d') if t.expiry_date else 'No Expiry',
                t.get_result_display(),
                t.get_competency_status_display()
            ]
            for t in qs
        ]
        return headers, rows, 'Training_Competency_Report'

    elif module == 'inspections':
        qs = Inspection.objects.select_related('inspector', 'process').all()
        
        headers = ['Inspection Number', 'Lot / Batch Number', 'Type', 'Inspector', 'Inspection Date', 'Result', 'Total Inspected', 'Defective Qty']
        rows = [
            [
                i.inspection_number,
                i.lot_number,
                i.get_inspection_type_display(),
                i.inspector.full_name if i.inspector else '',
                i.inspection_date.strftime('%Y-%m-%d'),
                i.get_result_display(),
                i.sample_size,
                i.defective_quantity
            ]
            for i in qs
        ]
        return headers, rows, 'Inspections_Report'

    else:
        return ['Info'], [['No data']], 'Report'


IMPORT_TEMPLATES = {
    'equipment': {
        'filename': 'template_equipment_master.xlsx',
        'title': 'EQUIPMENT_MASTER',
        'headers': ['Equipment ID', 'Equipment Name', 'Category', 'Manufacturer', 'Model', 'Serial Number', 'Department Code', 'Location', 'Calibration Frequency Months', 'Last Calibration Date (YYYY-MM-DD)'],
        'samples': [
            ['EQ-MIC-001', 'Digital Micrometer 0-25mm', 'MICROMETER', 'Mitutoyo', '293-240-30', 'SN-998201', 'QA', 'QC Metrology Room', 12, '2024-01-15'],
            ['EQ-CAL-002', 'Vernier Caliper 150mm', 'CALIPER', 'Mitutoyo', '500-196-30', 'SN-441029', 'MCH', 'Machine Shop Station 2', 6, '2024-02-01']
        ]
    },
    'users': {
        'filename': 'template_users_employees.xlsx',
        'title': 'EMPLOYEES',
        'headers': ['Username', 'Email', 'First Name', 'Last Name', 'Employee ID', 'Role', 'Department Code', 'Job Title'],
        'samples': [
            ['jdoe', 'jdoe@factory.local', 'John', 'Doe', 'EMP-1021', 'QC_INSPECTOR', 'QA', 'Senior Quality Inspector'],
            ['asmith', 'asmith@factory.local', 'Alice', 'Smith', 'EMP-1022', 'QA_ENGINEER', 'QA', 'Lead Quality Engineer']
        ]
    },
    'departments': {
        'filename': 'template_departments.xlsx',
        'title': 'DEPARTMENTS',
        'headers': ['Code', 'Name', 'Description'],
        'samples': [
            ['PKG', 'Packaging & Shipping', 'Final product packaging, labeling, and palletizing'],
            ['WHS', 'Warehouse & Material Receiving', 'Raw material storage, quarantine inspection, and parts inventory']
        ]
    },
    'objectives': {
        'filename': 'template_quality_objectives.xlsx',
        'title': 'QUALITY_OBJECTIVES',
        'headers': ['Objective Code', 'Objective Name', 'KPI Metric', 'Target Value', 'Baseline Value', 'Unit', 'Department Code', 'Due Date (YYYY-MM-DD)', 'Description'],
        'samples': [
            ['OBJ-QA-01', 'Reduce Incoming Material Defect Rate', 'Incoming Defect Rate', 0.5, 1.8, '%', 'QA', '2024-12-31', 'Drive supplier quality audits and sampling rigor'],
            ['OBJ-MCH-02', 'Improve First Pass Yield on CNC Lines', 'CNC First Pass Yield', 99.2, 97.5, '%', 'MCH', '2024-12-31', 'Enhance tool calibration cycles and in-process checks']
        ]
    }
}

@login_required
def download_import_template(request, model_type):
    config = IMPORT_TEMPLATES.get(model_type)
    if not config:
        raise Http404("Unknown import template type")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = config['title']

    header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    sample_font = Font(name="Calibri", size=10, italic=True, color="4A5568")

    ws.append(config['headers'])
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for sample in config['samples']:
        ws.append(sample)

    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(config['headers'])):
        for cell in row:
            cell.font = sample_font

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{config["filename"]}"'
    return response

@login_required
def bulk_import_view(request):
    if not (request.user.is_superuser or request.user.role in ['SUPER_ADMIN', 'QA_MANAGER', 'PLANT_MANAGER', 'QA_ENGINEER']):
        messages.error(request, "Permission denied: Master Data Bulk Import requires QA Engineer or Manager privileges.")
        return redirect('reports:index')

    preview = None
    model_type = request.GET.get('model_type', 'equipment')

    if request.method == 'POST':
        action_commit = request.POST.get('commit') == '1'
        model_type = request.POST.get('model_type', 'equipment')

        # Stage 2: Commit pending import
        if action_commit:
            pending = request.session.get('bulk_import_pending')
            if not pending or pending.get('model_type') != model_type:
                messages.error(request, "No pending validated import data found. Please upload again.")
                return redirect('reports:bulk_import')

            rows_to_create = pending.get('valid_rows', [])
            created_count = 0

            try:
                with transaction.atomic():
                    if model_type == 'equipment':
                        for r in rows_to_create:
                            dept = Department.objects.filter(code__iexact=r['department_code']).first()
                            last_cal = datetime.strptime(r['last_calibration_date'], '%Y-%m-%d').date()
                            freq = int(r.get('frequency', 12))
                            next_cal = last_cal + relativedelta(months=freq)

                            Equipment.objects.create(
                                equipment_id=r['equipment_id'],
                                equipment_name=r['equipment_name'],
                                category=r.get('category', 'CALIPER'),
                                manufacturer=r.get('manufacturer', ''),
                                model=r.get('model', ''),
                                serial_number=r.get('serial_number', ''),
                                department=dept,
                                location=r.get('location', 'Shop Floor'),
                                calibration_frequency_months=freq,
                                last_calibration_date=last_cal,
                                next_calibration_date=next_cal,
                                status=Equipment.Status.VALID
                            )
                            created_count += 1

                    elif model_type == 'users':
                        for r in rows_to_create:
                            dept = Department.objects.filter(code__iexact=r['department_code']).first() if r.get('department_code') else None
                            u = User.objects.create_user(
                                username=r['username'],
                                email=r['email'],
                                password='Welcome@2024',
                                first_name=r.get('first_name', ''),
                                last_name=r.get('last_name', ''),
                                employee_id=r.get('employee_id', ''),
                                role=r.get('role', 'QC_INSPECTOR'),
                                department=dept
                            )
                            created_count += 1

                    elif model_type == 'departments':
                        for r in rows_to_create:
                            Department.objects.create(
                                code=r['code'],
                                name=r['name'],
                                description=r.get('description', '')
                            )
                            created_count += 1

                    elif model_type == 'objectives':
                        for r in rows_to_create:
                            dept = Department.objects.filter(code__iexact=r['department_code']).first()
                            due = datetime.strptime(r['due_date'], '%Y-%m-%d').date()
                            QualityObjective.objects.create(
                                code=r['code'],
                                name=r['name'],
                                kpi=r['kpi'],
                                target=r['target'],
                                baseline=r.get('baseline', 0.0),
                                unit=r.get('unit', '%'),
                                department=dept,
                                due_date=due,
                                responsible_person=request.user,
                                description=r.get('description', '')
                            )
                            created_count += 1

                log_audit(
                    request.user,
                    'BULK_IMPORT',
                    model_type.upper(),
                    f"{created_count}_RECORDS",
                    f"Bulk Import {model_type.capitalize()}",
                    notes=f"Successfully imported {created_count} records from {pending.get('filename')}"
                )
                del request.session['bulk_import_pending']
                messages.success(request, f"Successfully imported {created_count} {model_type} records into QMS database!")

                if model_type == 'equipment':
                    return redirect('calibration:list')
                elif model_type == 'users':
                    return redirect('accounts:user_list')
                elif model_type == 'departments':
                    return redirect('departments:list')
                else:
                    return redirect('objectives:list')

            except Exception as e:
                messages.error(request, f"Import transaction failed: {e}")
                return redirect('reports:bulk_import')

        # Stage 1: Dry-Run File Validation
        uploaded_file = request.FILES.get('import_file')
        if not uploaded_file:
            messages.warning(request, "Please select an Excel (.xlsx) or CSV file to import.")
            return redirect('reports:bulk_import')

        raw_rows = []
        filename = uploaded_file.name.lower()

        try:
            if filename.endswith('.xlsx'):
                wb = openpyxl.load_workbook(uploaded_file, data_only=True)
                ws = wb.active
                for row in ws.iter_rows(values_only=True):
                    if any(cell is not None and str(cell).strip() != '' for cell in row):
                        raw_rows.append([str(cell).strip() if cell is not None else '' for cell in row])
            elif filename.endswith('.csv'):
                content = uploaded_file.read().decode('utf-8', errors='ignore')
                reader = csv.reader(content.splitlines())
                for row in reader:
                    if any(cell.strip() != '' for cell in row):
                        raw_rows.append([cell.strip() for cell in row])
            else:
                messages.error(request, "Unsupported file format. Please upload .xlsx or .csv.")
                return redirect('reports:bulk_import')
        except Exception as e:
            messages.error(request, f"Error parsing uploaded file: {e}")
            return redirect('reports:bulk_import')

        if len(raw_rows) < 2:
            messages.error(request, "The uploaded file does not contain any data rows.")
            return redirect('reports:bulk_import')

        header_row = [h.lower() for h in raw_rows[0]]
        data_rows = raw_rows[1:]

        valid_rows = []
        errors = []

        # Validate by Model Type
        if model_type == 'equipment':
            existing_ids = set(Equipment.objects.values_list('equipment_id', flat=True))
            existing_sns = set(Equipment.objects.filter(serial_number__gt='').values_list('serial_number', flat=True))
            departments_map = {d.code.upper(): d for d in Department.objects.all()}

            for idx, r in enumerate(data_rows, start=2):
                row_errors = []
                if len(r) < 8:
                    row_errors.append("Row has insufficient columns")
                    errors.append({'row': idx, 'identifier': r[0] if r else 'N/A', 'errors': row_errors})
                    continue

                eq_id = r[0]
                eq_name = r[1]
                category = r[2].upper() if len(r) > 2 and r[2] else 'CALIPER'
                mfg = r[3] if len(r) > 3 else ''
                model = r[4] if len(r) > 4 else ''
                sn = r[5] if len(r) > 5 else ''
                dept_code = r[6].upper() if len(r) > 6 else ''
                loc = r[7] if len(r) > 7 else 'Shop Floor'
                freq = r[8] if len(r) > 8 and r[8] else '12'
                last_cal_str = r[9] if len(r) > 9 and r[9] else timezone.now().strftime('%Y-%m-%d')

                if not eq_id:
                    row_errors.append("Equipment ID is required")
                elif eq_id in existing_ids:
                    row_errors.append(f"Equipment ID '{eq_id}' already exists in database")

                if not eq_name:
                    row_errors.append("Equipment Name is required")

                if sn and sn in existing_sns:
                    row_errors.append(f"Serial Number '{sn}' already exists in database")

                if not dept_code or dept_code not in departments_map:
                    row_errors.append(f"Department Code '{dept_code}' does not exist in master departments")

                try:
                    freq_int = int(freq)
                    if freq_int <= 0:
                        row_errors.append("Frequency must be positive integer")
                except ValueError:
                    row_errors.append(f"Invalid calibration frequency '{freq}'")

                try:
                    # Clean date string (handles timestamps from excel like '2024-01-15 00:00:00')
                    clean_date = last_cal_str.split(' ')[0]
                    datetime.strptime(clean_date, '%Y-%m-%d')
                except ValueError:
                    row_errors.append(f"Invalid date format '{last_cal_str}' (expected YYYY-MM-DD)")

                if row_errors:
                    errors.append({'row': idx, 'identifier': eq_id or f"Row #{idx}", 'errors': row_errors})
                else:
                    valid_rows.append({
                        'equipment_id': eq_id,
                        'equipment_name': eq_name,
                        'category': category,
                        'manufacturer': mfg,
                        'model': model,
                        'serial_number': sn,
                        'department_code': dept_code,
                        'location': loc,
                        'frequency': int(freq),
                        'last_calibration_date': clean_date
                    })

        elif model_type == 'users':
            existing_usernames = set(User.objects.values_list('username', flat=True))
            existing_emails = set(User.objects.values_list('email', flat=True))
            departments_map = {d.code.upper(): d for d in Department.objects.all()}

            for idx, r in enumerate(data_rows, start=2):
                row_errors = []
                if len(r) < 6:
                    row_errors.append("Row has insufficient columns")
                    errors.append({'row': idx, 'identifier': r[0] if r else 'N/A', 'errors': row_errors})
                    continue

                username = r[0].lower()
                email = r[1].lower()
                first_name = r[2] if len(r) > 2 else ''
                last_name = r[3] if len(r) > 3 else ''
                emp_id = r[4] if len(r) > 4 else ''
                role = r[5].upper() if len(r) > 5 and r[5] else 'QC_INSPECTOR'
                dept_code = r[6].upper() if len(r) > 6 and r[6] else ''
                title = r[7] if len(r) > 7 else ''

                if not username:
                    row_errors.append("Username is required")
                elif username in existing_usernames:
                    row_errors.append(f"Username '{username}' already exists")

                if not email:
                    row_errors.append("Email is required")
                elif email in existing_emails:
                    row_errors.append(f"Email '{email}' already registered")

                if role not in User.Role.values:
                    row_errors.append(f"Invalid role '{role}'")

                if dept_code and dept_code not in departments_map:
                    row_errors.append(f"Unknown department code '{dept_code}'")

                if row_errors:
                    errors.append({'row': idx, 'identifier': username or f"Row #{idx}", 'errors': row_errors})
                else:
                    valid_rows.append({
                        'username': username,
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'employee_id': emp_id,
                        'role': role,
                        'department_code': dept_code,
                        'title': title
                    })

        elif model_type == 'departments':
            existing_codes = set(Department.objects.values_list('code', flat=True))
            for idx, r in enumerate(data_rows, start=2):
                row_errors = []
                code = r[0].upper() if len(r) > 0 else ''
                name = r[1] if len(r) > 1 else ''
                desc = r[2] if len(r) > 2 else ''

                if not code:
                    row_errors.append("Department Code is required")
                elif code in existing_codes:
                    row_errors.append(f"Department code '{code}' already exists")

                if not name:
                    row_errors.append("Department Name is required")

                if row_errors:
                    errors.append({'row': idx, 'identifier': code or f"Row #{idx}", 'errors': row_errors})
                else:
                    valid_rows.append({'code': code, 'name': name, 'description': desc})

        elif model_type == 'objectives':
            existing_codes = set(QualityObjective.objects.values_list('code', flat=True))
            departments_map = {d.code.upper(): d for d in Department.objects.all()}

            for idx, r in enumerate(data_rows, start=2):
                row_errors = []
                code = r[0] if len(r) > 0 else ''
                name = r[1] if len(r) > 1 else ''
                kpi = r[2] if len(r) > 2 else ''
                target = r[3] if len(r) > 3 else ''
                baseline = r[4] if len(r) > 4 and r[4] else '0.0'
                unit = r[5] if len(r) > 5 and r[5] else '%'
                dept_code = r[6].upper() if len(r) > 6 else ''
                due_str = r[7] if len(r) > 7 else ''
                desc = r[8] if len(r) > 8 else ''

                if not code:
                    row_errors.append("Objective Code is required")
                elif code in existing_codes:
                    row_errors.append(f"Objective code '{code}' already exists")

                if not name:
                    row_errors.append("Objective Name is required")

                if not kpi:
                    row_errors.append("KPI metric is required")

                try:
                    target_val = float(target)
                except ValueError:
                    row_errors.append(f"Invalid target value '{target}'")

                try:
                    baseline_val = float(baseline)
                except ValueError:
                    row_errors.append(f"Invalid baseline value '{baseline}'")

                if not dept_code or dept_code not in departments_map:
                    row_errors.append(f"Department code '{dept_code}' not found")

                try:
                    clean_due = due_str.split(' ')[0]
                    datetime.strptime(clean_due, '%Y-%m-%d')
                except ValueError:
                    row_errors.append(f"Invalid due date '{due_str}' (expected YYYY-MM-DD)")

                if row_errors:
                    errors.append({'row': idx, 'identifier': code or f"Row #{idx}", 'errors': row_errors})
                else:
                    valid_rows.append({
                        'code': code,
                        'name': name,
                        'kpi': kpi,
                        'target': target_val,
                        'baseline': baseline_val,
                        'unit': unit,
                        'department_code': dept_code,
                        'due_date': clean_due,
                        'description': desc
                    })

        # Save to session for Stage 2 Commit
        request.session['bulk_import_pending'] = {
            'model_type': model_type,
            'valid_rows': valid_rows,
            'filename': uploaded_file.name
        }

        preview = {
            'total_rows': len(data_rows),
            'valid_count': len(valid_rows),
            'invalid_count': len(errors),
            'errors': errors,
            'valid_samples': valid_rows[:8],
            'model_type': model_type,
            'filename': uploaded_file.name
        }

    return render(request, 'reports/bulk_import.html', {
        'preview': preview,
        'model_type': model_type,
        'templates': IMPORT_TEMPLATES,
    })
