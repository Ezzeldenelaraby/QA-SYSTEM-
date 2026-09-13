from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import SystemSetting, AuditLog
from .utils import log_audit
from apps.ncr.models import NCR
from apps.capa.models import CAPA
from apps.actions.models import Action
from apps.documents.models import Document
from apps.calibration.models import Equipment
from apps.processes.models import Process

@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()
    results = {
        'query': query,
        'ncrs': [],
        'capas': [],
        'actions': [],
        'documents': [],
        'equipment': [],
        'processes': [],
        'total_count': 0
    }
    
    if query:
        results['ncrs'] = NCR.objects.filter(
            Q(ncr_number__icontains=query) |
            Q(product__icontains=query) |
            Q(description__icontains=query) |
            Q(batch_lot__icontains=query)
        )[:10]

        results['capas'] = CAPA.objects.filter(
            Q(capa_number__icontains=query) |
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )[:10]

        results['actions'] = Action.objects.filter(
            Q(action_number__icontains=query) |
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )[:10]

        results['documents'] = Document.objects.filter(
            Q(document_number__icontains=query) |
            Q(title__icontains=query)
        )[:10]

        results['equipment'] = Equipment.objects.filter(
            Q(equipment_id__icontains=query) |
            Q(equipment_name__icontains=query) |
            Q(serial_number__icontains=query)
        )[:10]

        results['processes'] = Process.objects.filter(
            Q(code__icontains=query) |
            Q(name__icontains=query)
        )[:10]

        results['total_count'] = (
            len(results['ncrs']) + len(results['capas']) + len(results['actions']) +
            len(results['documents']) + len(results['equipment']) + len(results['processes'])
        )

    return render(request, 'core/search_results.html', {'results': results})

@login_required
def system_settings_view(request):
    if not (request.user.is_superuser or request.user.role in ['SUPER_ADMIN', 'QA_MANAGER', 'PLANT_MANAGER']):
        messages.error(request, "Only Super Admin, QA Manager, or Plant Manager can adjust system settings.")
        return redirect('dashboard:index')

    settings_obj = SystemSetting.get_settings()
    if request.method == 'POST':
        settings_obj.company_name = request.POST.get('company_name', settings_obj.company_name)
        settings_obj.ncr_prefix = request.POST.get('ncr_prefix', settings_obj.ncr_prefix)
        settings_obj.capa_prefix = request.POST.get('capa_prefix', settings_obj.capa_prefix)
        settings_obj.action_prefix = request.POST.get('action_prefix', settings_obj.action_prefix)
        settings_obj.audit_prefix = request.POST.get('audit_prefix', settings_obj.audit_prefix)
        settings_obj.calibration_alert_days = int(request.POST.get('calibration_alert_days', 30))
        settings_obj.risk_high_threshold = int(request.POST.get('risk_high_threshold', 10))
        settings_obj.risk_critical_threshold = int(request.POST.get('risk_critical_threshold', 15))
        if 'company_logo' in request.FILES:
            settings_obj.company_logo = request.FILES['company_logo']
        settings_obj.save()

        log_audit(request.user, 'UPDATE', 'SystemSetting', settings_obj.id, 'System Global Settings', notes='Updated organization settings')
        messages.success(request, "System settings updated successfully.")
        return redirect('core:system_settings')

    # Retrieve existing disaster recovery backups
    from pathlib import Path
    from datetime import datetime
    from django.conf import settings
    backup_dir = Path(settings.BASE_DIR) / 'backups'
    backup_archives = []
    if backup_dir.exists():
        for f in sorted(backup_dir.glob('qms_*'), key=lambda p: p.stat().st_mtime, reverse=True):
            if f.is_file():
                size_mb = f.stat().st_size / (1024 * 1024)
                backup_archives.append({
                    'filename': f.name,
                    'size_mb': f"{size_mb:.2f}",
                    'size_bytes': f.stat().st_size,
                    'created_at': datetime.fromtimestamp(f.stat().st_mtime),
                })

    return render(request, 'core/system_settings.html', {
        'settings_obj': settings_obj,
        'backup_archives': backup_archives,
    })

@login_required
def trigger_backup_view(request):
    if not (request.user.is_superuser or request.user.role in ['SUPER_ADMIN', 'QA_MANAGER', 'PLANT_MANAGER']):
        messages.error(request, "Permission denied: Database backup requires Admin or QA Director privileges.")
        return redirect('core:system_settings')

    if request.method == 'POST':
        from django.core.management import call_command
        try:
            call_command('backup_database')
            messages.success(request, "New ISO 9001 disaster recovery database backup created successfully.")
        except Exception as e:
            messages.error(request, f"Backup creation failed: {e}")

    return redirect('core:system_settings')

@login_required
def download_backup_view(request, filename):
    if not (request.user.is_superuser or request.user.role in ['SUPER_ADMIN', 'QA_MANAGER', 'PLANT_MANAGER']):
        messages.error(request, "Permission denied.")
        return redirect('core:system_settings')

    from pathlib import Path
    from django.conf import settings
    from django.http import FileResponse, Http404

    # Security check: sanitize filename to prevent directory traversal
    if not filename.startswith('qms_') or '..' in filename or '/' in filename or '\\' in filename:
        raise Http404("Invalid backup archive specified.")

    backup_path = Path(settings.BASE_DIR) / 'backups' / filename
    if not backup_path.exists() or not backup_path.is_file():
        raise Http404("Backup file does not exist.")

    log_audit(request.user, 'DOWNLOAD', 'System', filename, f"Downloaded Backup {filename}")
    return FileResponse(open(backup_path, 'rb'), as_attachment=True, filename=filename)

@login_required
def scan_lookup(request):
    """
    Shop-floor barcode gun and QR camera resolver.
    Accepts ?code=<str>&redirect=1|0
    """
    import re
    from django.http import JsonResponse
    from apps.inspections.models import Inspection
    from apps.audits.models import AuditPlan

    code = request.GET.get('code', '').strip()
    redirect_flag = request.GET.get('redirect', '0') in ['1', 'true', 'True']

    if not code:
        if redirect_flag:
            messages.warning(request, "No barcode or QR code was supplied.")
            return redirect('dashboard:index')
        return JsonResponse({'found': False, 'message': 'No code supplied'})

    result = None

    # 1. Check URL patterns (e.g. if camera scanned full URL on tag)
    # /ncr/(\d+)
    ncr_url_match = re.search(r'/ncr/(\d+)', code)
    if ncr_url_match:
        ncr = NCR.objects.filter(id=ncr_url_match.group(1)).first()
        if ncr:
            result = {
                'type': 'NCR',
                'title': f"NCR {ncr.ncr_number}: {ncr.product}",
                'identifier': ncr.ncr_number,
                'status': ncr.get_status_display(),
                'status_badge': 'bg-danger' if ncr.status == NCR.Status.OPEN else 'bg-success',
                'department': ncr.department.name if ncr.department else '',
                'url': f"/ncr/{ncr.id}/",
                'actions': [
                    {'label': 'Open NCR', 'url': f"/ncr/{ncr.id}/", 'icon': 'bi-eye'},
                    {'label': 'Print Red Tag', 'url': f"/ncr/{ncr.id}/red-tag/", 'icon': 'bi-printer', 'target': '_blank'}
                ]
            }

    # /calibration/(\d+)
    if not result:
        cal_url_match = re.search(r'/calibration/(\d+)', code)
        if cal_url_match:
            eq = Equipment.objects.filter(id=cal_url_match.group(1)).first()
            if eq:
                result = {
                    'type': 'Equipment',
                    'title': f"{eq.equipment_name} ({eq.model or 'N/A'})",
                    'identifier': f"{eq.equipment_id} | S/N: {eq.serial_number or 'N/A'}",
                    'status': eq.get_status_display(),
                    'status_badge': 'bg-success' if eq.status == Equipment.Status.VALID else ('bg-warning' if eq.status == Equipment.Status.DUE_SOON else 'bg-danger'),
                    'department': eq.department.name if eq.department else '',
                    'url': f"/calibration/{eq.id}/",
                    'actions': [
                        {'label': 'Equipment Master', 'url': f"/calibration/{eq.id}/", 'icon': 'bi-tools'},
                        {'label': 'Print Calibration Sticker', 'url': f"/calibration/{eq.id}/sticker/", 'icon': 'bi-qr-code', 'target': '_blank'},
                        {'label': 'Record Calibration', 'url': f"/calibration/{eq.id}/calibrate/", 'icon': 'bi-plus-circle'}
                    ]
                }

    # 2. Check Prefixed Tags or IDs
    if not result:
        # Check Equipment by ID or Serial Number
        eq = Equipment.objects.filter(
            Q(equipment_id__iexact=code) |
            Q(serial_number__iexact=code) |
            Q(equipment_id__iexact=code.replace('QMS:CAL:', '').replace('CAL:', ''))
        ).first()
        if eq:
            result = {
                'type': 'Equipment',
                'title': f"{eq.equipment_name} ({eq.model or 'N/A'})",
                'identifier': f"{eq.equipment_id} | S/N: {eq.serial_number or 'N/A'}",
                'status': eq.get_status_display(),
                'status_badge': 'bg-success' if eq.status == Equipment.Status.VALID else ('bg-warning' if eq.status == Equipment.Status.DUE_SOON else 'bg-danger'),
                'department': eq.department.name if eq.department else '',
                'url': f"/calibration/{eq.id}/",
                'actions': [
                    {'label': 'Equipment Master', 'url': f"/calibration/{eq.id}/", 'icon': 'bi-tools'},
                    {'label': 'Print Calibration Sticker', 'url': f"/calibration/{eq.id}/sticker/", 'icon': 'bi-qr-code', 'target': '_blank'},
                    {'label': 'Record Calibration', 'url': f"/calibration/{eq.id}/calibrate/", 'icon': 'bi-plus-circle'}
                ]
            }

    if not result:
        # Check NCR by Number, ID, or Batch Lot
        ncr_clean = code.replace('QMS:NCR:', '').replace('NCR:', '')
        ncr = NCR.objects.filter(
            Q(ncr_number__iexact=code) |
            Q(ncr_number__iexact=ncr_clean) |
            Q(batch_lot__iexact=code)
        ).first()
        if ncr:
            result = {
                'type': 'NCR',
                'title': f"NCR {ncr.ncr_number}: {ncr.product}",
                'identifier': ncr.ncr_number,
                'status': ncr.get_status_display(),
                'status_badge': 'bg-danger' if ncr.status == NCR.Status.OPEN else 'bg-success',
                'department': ncr.department.name if ncr.department else '',
                'url': f"/ncr/{ncr.id}/",
                'actions': [
                    {'label': 'Open NCR', 'url': f"/ncr/{ncr.id}/", 'icon': 'bi-eye'},
                    {'label': 'Print Red Tag', 'url': f"/ncr/{ncr.id}/red-tag/", 'icon': 'bi-printer', 'target': '_blank'}
                ]
            }

    if not result:
        # Check CAPA
        capa = CAPA.objects.filter(capa_number__iexact=code).first()
        if capa:
            result = {
                'type': 'CAPA',
                'title': f"{capa.capa_number}: {capa.title}",
                'identifier': capa.capa_number,
                'status': capa.get_status_display(),
                'status_badge': 'bg-info',
                'department': capa.department.name if capa.department else '',
                'url': f"/capa/{capa.id}/",
                'actions': [
                    {'label': 'Open CAPA', 'url': f"/capa/{capa.id}/", 'icon': 'bi-arrow-repeat'},
                    {'label': 'Download 8D PDF', 'url': f"/capa/{capa.id}/8d-pdf/", 'icon': 'bi-file-pdf', 'target': '_blank'}
                ]
            }

    if not result:
        # Check Action
        action = Action.objects.filter(action_number__iexact=code).first()
        if action:
            result = {
                'type': 'Action',
                'title': f"{action.action_number}: {action.title}",
                'identifier': action.action_number,
                'status': action.get_status_display(),
                'status_badge': 'bg-primary',
                'department': action.department.name if action.department else '',
                'url': f"/actions/{action.id}/",
                'actions': [
                    {'label': 'Open Action', 'url': f"/actions/{action.id}/", 'icon': 'bi-check2-square'}
                ]
            }

    if not result:
        # Check Document
        doc = Document.objects.filter(document_number__iexact=code).first()
        if doc:
            result = {
                'type': 'Document',
                'title': f"{doc.document_number}: {doc.title}",
                'identifier': f"{doc.document_number} (Rev: {doc.current_revision})",
                'status': doc.get_status_display(),
                'status_badge': 'bg-secondary',
                'department': doc.department.name if doc.department else '',
                'url': f"/documents/{doc.id}/",
                'actions': [
                    {'label': 'View Document', 'url': f"/documents/{doc.id}/", 'icon': 'bi-file-text'}
                ]
            }

    if not result:
        # Check Process
        prc = Process.objects.filter(code__iexact=code).first()
        if prc:
            result = {
                'type': 'Process',
                'title': f"{prc.code}: {prc.name}",
                'identifier': prc.code,
                'status': 'Active SIPOC',
                'status_badge': 'bg-dark',
                'department': prc.department.name if prc.department else '',
                'url': f"/processes/{prc.id}/",
                'actions': [
                    {'label': 'View Process Map', 'url': f"/processes/{prc.id}/", 'icon': 'bi-diagram-3'}
                ]
            }

    if not result:
        # Check Inspection
        insp = Inspection.objects.filter(
            Q(inspection_number__iexact=code) |
            Q(batch_lot__iexact=code) |
            Q(id=int(code) if code.isdigit() else -1)
        ).first()
        if insp:
            result = {
                'type': 'Inspection',
                'title': f"{insp.inspection_number}: {insp.product}",
                'identifier': f"Lot/Batch #{insp.batch_lot}",
                'status': insp.get_overall_result_display(),
                'status_badge': 'bg-success' if insp.overall_result == 'PASS' else 'bg-danger',
                'department': '',
                'url': f"/inspections/{insp.id}/",
                'actions': [
                    {'label': 'View Inspection', 'url': f"/inspections/{insp.id}/", 'icon': 'bi-card-checklist'}
                ]
            }

    if not result:
        # Check Audit Plan
        audit = AuditPlan.objects.filter(audit_number__iexact=code).first()
        if audit:
            result = {
                'type': 'Internal Audit',
                'title': f"{audit.audit_number}: {audit.audit_title}",
                'identifier': audit.audit_number,
                'status': audit.get_status_display(),
                'status_badge': 'bg-primary',
                'department': audit.department.name if audit.department else '',
                'url': f"/audits/{audit.id}/",
                'actions': [
                    {'label': 'View Audit Plan', 'url': f"/audits/{audit.id}/", 'icon': 'bi-clipboard2-check'}
                ]
            }

    if result:
        if redirect_flag:
            return redirect(result['url'])
        return JsonResponse({'found': True, 'item': result})
    else:
        if redirect_flag:
            messages.warning(request, f"No QMS asset, tag, or document matched barcode: '{code}'")
            return redirect('dashboard:index')
        return JsonResponse({'found': False, 'message': f"No QMS record matched '{code}'"})

@login_required
def audit_trail_view(request):
    logs = AuditLog.objects.select_related('user').all()

    module = request.GET.get('module')
    action = request.GET.get('action')
    if module:
        logs = logs.filter(module=module)
    if action:
        logs = logs.filter(action=action)

    modules_list = AuditLog.objects.values_list('module', flat=True).distinct()
    return render(request, 'core/audit_trail.html', {
        'logs': logs[:100],
        'modules_list': modules_list,
        'selected_module': module,
        'selected_action': action,
    })

def custom_permission_denied(request, exception=None):
    return render(request, '403.html', status=403)

def custom_page_not_found(request, exception=None):
    return render(request, '404.html', status=404)

def custom_server_error(request):
    return render(request, '500.html', status=500)

def health_check(request):
    """
    Liveness and readiness health check probe for Railway, Docker, Kubernetes, and load balancers.
    """
    from django.http import JsonResponse
    from django.db import connection
    from django.utils import timezone

    db_ok = True
    db_error = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as e:
        db_ok = False
        db_error = str(e)

    status_code = 200 if db_ok else 503
    return JsonResponse({
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "error": db_error,
        "timestamp": timezone.now().isoformat(),
        "version": "1.0.0"
    }, status=status_code)
