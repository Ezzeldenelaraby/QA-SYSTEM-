import json
from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth import get_user_model

from apps.ncr.models import NCR
from apps.capa.models import CAPA
from apps.actions.models import Action
from apps.calibration.models import Equipment
from apps.risks.models import Risk
from apps.objectives.models import QualityObjective
from apps.audits.models import AuditFinding
from apps.departments.models import Department
from apps.training.models import Course, TrainingRecord

User = get_user_model()

@login_required
def index(request):
    today = timezone.now().date()
    dept_id = request.GET.get('department')
    
    # 1. Base querysets (with optional department filter)
    ncr_qs = NCR.objects.all()
    capa_qs = CAPA.objects.all()
    action_qs = Action.objects.all()
    risk_qs = Risk.objects.all()
    equip_qs = Equipment.objects.all()

    if dept_id:
        ncr_qs = ncr_qs.filter(department_id=dept_id)
        capa_qs = capa_qs.filter(responsible_person__department_id=dept_id)
        action_qs = action_qs.filter(department_id=dept_id)
        risk_qs = risk_qs.filter(department_id=dept_id)
        equip_qs = equip_qs.filter(department_id=dept_id)

    # 2. Executive KPI Counts
    open_ncrs_count = ncr_qs.filter(status__in=[NCR.Status.OPEN, NCR.Status.CONTAINMENT, NCR.Status.ROOT_CAUSE_ANALYSIS]).count()
    critical_ncrs_count = ncr_qs.filter(severity=NCR.Severity.CRITICAL, status__in=[NCR.Status.OPEN, NCR.Status.CONTAINMENT]).count()
    
    open_capas_count = capa_qs.filter(status__in=[CAPA.Status.OPEN, CAPA.Status.ANALYSIS, CAPA.Status.IMPLEMENTATION, CAPA.Status.VERIFICATION, CAPA.Status.EFFECTIVENESS_CHECK]).count()
    pending_verification_capas = capa_qs.filter(status__in=[CAPA.Status.VERIFICATION, CAPA.Status.EFFECTIVENESS_CHECK]).count()

    total_actions_count = action_qs.count()
    # Check overdue status actively
    overdue_actions_count = action_qs.filter(
        Q(status=Action.Status.OVERDUE) |
        (Q(due_date__lt=today) & ~Q(status__in=[Action.Status.COMPLETED, Action.Status.CANCELLED]))
    ).count()
    open_actions_count = action_qs.filter(status__in=[Action.Status.OPEN, Action.Status.IN_PROGRESS]).count()

    # Calibration Alerts
    active_equip_qs = equip_qs.exclude(status=Equipment.Status.OUT_OF_SERVICE)
    cal_overdue_count = active_equip_qs.filter(next_calibration_date__lt=today).count()
    cal_due_30_count = active_equip_qs.filter(
        next_calibration_date__gte=today,
        next_calibration_date__lte=today + timedelta(days=30)
    ).count()

    # Risk Metrics
    high_critical_risks_count = risk_qs.filter(risk_level__in=[Risk.RiskLevel.HIGH, Risk.RiskLevel.CRITICAL], status=Risk.Status.OPEN).count()

    # Training Compliance
    total_active_users = User.objects.filter(is_active=True).count()
    total_courses = Course.objects.count()
    possible_training_slots = total_active_users * total_courses if total_courses and total_active_users else 1
    valid_training_records = TrainingRecord.objects.filter(
        Q(expiry_date__gte=today) | Q(expiry_date__isnull=True),
        result=TrainingRecord.Result.PASS
    ).count()
    training_compliance_rate = round(min((valid_training_records / possible_training_slots) * 100, 100.0), 1)

    # 3. Monthly NCR Trend (Past 6 Months)
    months_labels = []
    ncr_trend_data = []
    for i in range(5, -1, -1):
        # Calculate month date window
        # First day of month (i months ago)
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1
        
        month_label = f"{year}-{month:02d}"
        months_labels.append(month_label)
        
        # Count NCRs created in that month
        cnt = ncr_qs.filter(created_at__year=year, created_at__month=month).count()
        ncr_trend_data.append(cnt)

    # 4. NCR by Department Distribution
    dept_ncrs = (
        NCR.objects.filter(department__isnull=False)
        .values('department__name')
        .annotate(total=Count('id'))
        .order_by('-total')[:6]
    )
    dept_labels = [item['department__name'] for item in dept_ncrs]
    dept_counts = [item['total'] for item in dept_ncrs]
    if not dept_labels:
        dept_labels = ['General']
        dept_counts = [ncr_qs.count()]

    # 5. CAPA Status Distribution
    capa_statuses = [
        ('Open', capa_qs.filter(status=CAPA.Status.OPEN).count()),
        ('Root Cause', capa_qs.filter(status=CAPA.Status.ANALYSIS).count()),
        ('Implementation', capa_qs.filter(status=CAPA.Status.IMPLEMENTATION).count()),
        ('Verification', capa_qs.filter(status__in=[CAPA.Status.VERIFICATION, CAPA.Status.EFFECTIVENESS_CHECK]).count()),
        ('Closed', capa_qs.filter(status=CAPA.Status.CLOSED).count()),
    ]
    capa_status_labels = [s[0] for s in capa_statuses]
    capa_status_counts = [s[1] for s in capa_statuses]

    # 6. Risk Level Breakdown
    risk_levels = [
        ('Low', risk_qs.filter(risk_level=Risk.RiskLevel.LOW).count()),
        ('Medium', risk_qs.filter(risk_level=Risk.RiskLevel.MEDIUM).count()),
        ('High', risk_qs.filter(risk_level=Risk.RiskLevel.HIGH).count()),
        ('Critical', risk_qs.filter(risk_level=Risk.RiskLevel.CRITICAL).count()),
    ]
    risk_level_labels = [r[0] for r in risk_levels]
    risk_level_counts = [r[1] for r in risk_levels]

    # 7. Recent Items Tables
    recent_ncrs = ncr_qs.select_related('department', 'reported_by').order_by('-created_at')[:5]
    recent_actions = action_qs.select_related('assigned_to', 'department').order_by('due_date')[:5]
    equipment_alerts = active_equip_qs.filter(
        next_calibration_date__lte=today + timedelta(days=30)
    ).order_by('next_calibration_date')[:5]

    departments = Department.objects.all()

    context = {
        # KPIs
        'open_ncrs_count': open_ncrs_count,
        'critical_ncrs_count': critical_ncrs_count,
        'open_capas_count': open_capas_count,
        'pending_verification_capas': pending_verification_capas,
        'total_actions_count': total_actions_count,
        'overdue_actions_count': overdue_actions_count,
        'open_actions_count': open_actions_count,
        'cal_overdue_count': cal_overdue_count,
        'cal_due_30_count': cal_due_30_count,
        'high_critical_risks_count': high_critical_risks_count,
        'training_compliance_rate': training_compliance_rate,
        
        # Recent Tables
        'recent_ncrs': recent_ncrs,
        'recent_actions': recent_actions,
        'equipment_alerts': equipment_alerts,
        
        # Filters
        'departments': departments,
        'selected_dept': dept_id,

        # Chart Data JSON
        'ncr_months_json': json.dumps(months_labels),
        'ncr_trend_json': json.dumps(ncr_trend_data),
        'dept_labels_json': json.dumps(dept_labels),
        'dept_counts_json': json.dumps(dept_counts),
        'capa_status_labels_json': json.dumps(capa_status_labels),
        'capa_status_counts_json': json.dumps(capa_status_counts),
        'risk_level_labels_json': json.dumps(risk_level_labels),
        'risk_level_counts_json': json.dumps(risk_level_counts),
    }

    return render(request, 'dashboard/index.html', context)
