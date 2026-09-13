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
    if not (request.user.is_superuser or request.user.role in ['SUPER_ADMIN', 'QA_MANAGER']):
        messages.error(request, "Only Super Admin or QA Manager can adjust system settings.")
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

    return render(request, 'core/system_settings.html', {'settings_obj': settings_obj})

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
