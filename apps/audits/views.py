from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import AuditPlan, AuditChecklistItem, AuditFinding
from .forms import AuditPlanForm, AuditChecklistForm, AuditFindingForm
from apps.ncr.models import NCR
from apps.actions.models import Action
from apps.core.utils import log_audit

@login_required
def audit_list(request):
    audits = AuditPlan.objects.select_related('department', 'process', 'lead_auditor').all()

    status = request.GET.get('status')
    department = request.GET.get('department')
    if status:
        audits = audits.filter(status=status)
    if department:
        audits = audits.filter(department_id=department)

    return render(request, 'audits/audit_list.html', {
        'audits': audits,
        'selected_status': status,
    })

@login_required
def audit_detail(request, audit_id):
    audit = get_object_or_404(
        AuditPlan.objects.select_related('department', 'process', 'lead_auditor'),
        id=audit_id
    )
    checklist_items = audit.checklist_items.all()
    findings = audit.findings.select_related('responsible_person', 'linked_ncr', 'linked_action').all()

    checklist_form = AuditChecklistForm()
    finding_form = AuditFindingForm()

    context = {
        'audit': audit,
        'checklist_items': checklist_items,
        'findings': findings,
        'checklist_form': checklist_form,
        'finding_form': finding_form,
    }
    return render(request, 'audits/audit_detail.html', context)

@login_required
def audit_create(request):
    if not (request.user.is_super_admin or request.user.is_auditor or request.user.is_qa_staff):
        messages.error(request, "Only qualified Auditors or QA Staff can schedule audits.")
        return redirect('audits:list')

    if request.method == 'POST':
        form = AuditPlanForm(request.POST)
        if form.is_valid():
            audit = form.save()
            log_audit(request.user, 'CREATE', 'AuditPlan', audit.id, audit.audit_number)
            messages.success(request, f"Audit Plan '{audit.audit_number}' scheduled.")
            return redirect('audits:detail', audit_id=audit.id)
    else:
        form = AuditPlanForm(initial={'lead_auditor': request.user, 'audit_date': timezone.now().date()})

    return render(request, 'audits/audit_form.html', {'form': form, 'title': 'Schedule Internal Quality Audit'})

@login_required
def audit_edit(request, audit_id):
    audit = get_object_or_404(AuditPlan, id=audit_id)
    if request.method == 'POST':
        form = AuditPlanForm(request.POST, instance=audit)
        if form.is_valid():
            form.save()
            log_audit(request.user, 'UPDATE', 'AuditPlan', audit.id, audit.audit_number)
            messages.success(request, f"Audit Plan '{audit.audit_number}' updated.")
            return redirect('audits:detail', audit_id=audit.id)
    else:
        form = AuditPlanForm(instance=audit)

    return render(request, 'audits/audit_form.html', {'form': form, 'title': f'Edit Audit: {audit.audit_number}', 'audit': audit})

@login_required
def audit_add_checklist_item(request, audit_id):
    audit = get_object_or_404(AuditPlan, id=audit_id)
    if request.method == 'POST':
        form = AuditChecklistForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.audit = audit
            item.save()
            log_audit(request.user, 'CREATE', 'AuditChecklist', item.id, f"{audit.audit_number}: {item.iso_clause}")
            messages.success(request, "Checklist item added.")
    return redirect('audits:detail', audit_id=audit.id)

@login_required
def audit_add_finding(request, audit_id):
    audit = get_object_or_404(AuditPlan, id=audit_id)
    if request.method == 'POST':
        form = AuditFindingForm(request.POST)
        if form.is_valid():
            fnd = form.save(commit=False)
            fnd.audit = audit
            fnd.save()
            log_audit(request.user, 'CREATE', 'AuditFinding', fnd.id, fnd.finding_number)
            messages.success(request, f"Audit Finding '{fnd.finding_number}' recorded.")
    return redirect('audits:detail', audit_id=audit.id)

@login_required
def audit_finding_create_ncr(request, finding_id):
    finding = get_object_or_404(AuditFinding, id=finding_id)
    if finding.linked_ncr:
        messages.info(request, "An NCR has already been raised for this finding.")
        return redirect('ncr:detail', ncr_id=finding.linked_ncr.id)

    # 1-click create NCR
    ncr = NCR.objects.create(
        date=timezone.now().date(),
        department=finding.audit.department,
        process=finding.audit.process,
        product=f"Audit Finding Ref: {finding.finding_number}",
        batch_lot="AUDIT-VERIFICATION",
        reported_by=request.user,
        source=NCR.Source.INTERNAL_AUDIT,
        description=f"Generated from Audit Finding {finding.finding_number} ({finding.audit.audit_number}):\n{finding.description}",
        requirement=f"ISO 9001 Clause {finding.clause}",
        evidence=finding.evidence,
        classification=NCR.Classification.MAJOR if finding.finding_type == AuditFinding.FindingType.MAJOR_NC else NCR.Classification.MINOR,
        severity=NCR.Severity.HIGH if finding.finding_type == AuditFinding.FindingType.MAJOR_NC else NCR.Severity.MEDIUM,
        responsible_person=finding.responsible_person,
        due_date=finding.due_date,
        status=NCR.Status.OPEN
    )
    finding.linked_ncr = ncr
    finding.save(update_fields=['linked_ncr'])

    log_audit(request.user, 'CREATE', 'NCR', ncr.id, ncr.ncr_number, notes=f'Created from finding {finding.finding_number}')
    messages.success(request, f"Successfully created NCR '{ncr.ncr_number}' from audit finding.")
    return redirect('ncr:detail', ncr_id=ncr.id)

@login_required
def audit_finding_create_action(request, finding_id):
    finding = get_object_or_404(AuditFinding, id=finding_id)
    if finding.linked_action:
        messages.info(request, "An Action has already been linked to this finding.")
        return redirect('actions:detail', action_id=finding.linked_action.id)

    # 1-click create Action
    action = Action.objects.create(
        action_number=Action.generate_action_number(),
        title=f"Address Audit Finding: {finding.finding_number}",
        description=f"Action required to close audit finding {finding.finding_number} (Clause {finding.clause}):\n{finding.description}",
        source_type=Action.SourceType.AUDIT,
        source_id=finding.finding_number,
        department=finding.audit.department,
        process=finding.audit.process,
        assigned_to=finding.responsible_person,
        created_by=request.user,
        priority=Action.Priority.HIGH if finding.finding_type in [AuditFinding.FindingType.MAJOR_NC, AuditFinding.FindingType.MINOR_NC] else Action.Priority.MEDIUM,
        start_date=timezone.now().date(),
        due_date=finding.due_date,
        status=Action.Status.OPEN
    )
    finding.linked_action = action
    finding.save(update_fields=['linked_action'])

    log_audit(request.user, 'CREATE', 'Action', action.id, action.action_number, notes=f'Created from finding {finding.finding_number}')
    messages.success(request, f"Successfully created Action '{action.action_number}' from audit finding.")
    return redirect('actions:detail', action_id=action.id)
