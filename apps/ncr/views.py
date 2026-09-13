from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import NCR, FiveWhysAnalysis, FishboneCause
from .forms import NCRForm, FiveWhysForm, FishboneCauseForm, NCRCloseForm
from apps.capa.models import CAPA
from apps.core.utils import log_audit
from apps.notifications.models import Notification

@login_required
def ncr_list(request):
    ncrs = NCR.objects.select_related('department', 'process', 'reported_by', 'responsible_person').all()

    classification = request.GET.get('classification')
    status = request.GET.get('status')
    department = request.GET.get('department')
    process = request.GET.get('process')

    if classification:
        ncrs = ncrs.filter(classification=classification)
    if status:
        ncrs = ncrs.filter(status=status)
    if department:
        ncrs = ncrs.filter(department_id=department)
    if process:
        ncrs = ncrs.filter(process_id=process)

    return render(request, 'ncr/ncr_list.html', {
        'ncrs': ncrs,
        'selected_classification': classification,
        'selected_status': status,
    })

@login_required
def ncr_detail(request, ncr_id):
    ncr = get_object_or_404(
        NCR.objects.select_related('department', 'process', 'reported_by', 'responsible_person', 'verified_by'),
        id=ncr_id
    )

    # 5 Whys Analysis instance
    try:
        five_whys = ncr.five_whys
        five_whys_form = FiveWhysForm(instance=five_whys)
    except FiveWhysAnalysis.DoesNotExist:
        five_whys = None
        five_whys_form = FiveWhysForm(initial={'problem_statement': f"{ncr.product}: {ncr.description}"})

    # Fishbone causes grouped by 6Ms
    fishbone_causes = ncr.fishbone_causes.all()
    fishbone_by_category = {
        'MAN': [c for c in fishbone_causes if c.category == 'MAN'],
        'MACHINE': [c for c in fishbone_causes if c.category == 'MACHINE'],
        'METHOD': [c for c in fishbone_causes if c.category == 'METHOD'],
        'MATERIAL': [c for c in fishbone_causes if c.category == 'MATERIAL'],
        'MEASUREMENT': [c for c in fishbone_causes if c.category == 'MEASUREMENT'],
        'ENVIRONMENT': [c for c in fishbone_causes if c.category == 'ENVIRONMENT'],
    }

    fishbone_form = FishboneCauseForm()
    close_form = NCRCloseForm(instance=ncr)

    from apps.core.utils import generate_qr_code_base64
    qr_code_data = generate_qr_code_base64(request.build_absolute_uri())

    context = {
        'ncr': ncr,
        'five_whys': five_whys,
        'five_whys_form': five_whys_form,
        'fishbone_by_category': fishbone_by_category,
        'fishbone_form': fishbone_form,
        'close_form': close_form,
        'qr_code_data': qr_code_data,
    }
    return render(request, 'ncr/ncr_detail.html', context)

@login_required
def ncr_create(request):
    if request.method == 'POST':
        form = NCRForm(request.POST, request.FILES)
        if form.is_valid():
            ncr = form.save(commit=False)
            ncr.reported_by = request.user
            ncr.save()

            log_audit(request.user, 'CREATE', 'NCR', ncr.id, ncr.ncr_number)

            Notification.create_notification(
                recipient=ncr.responsible_person,
                title=f"NCR Assigned: {ncr.ncr_number}",
                message=f"You have been assigned nonconformity {ncr.ncr_number} on {ncr.product}.",
                link=f"/ncr/{ncr.id}/"
            )

            # Auto-alert QA Leadership if severity is CRITICAL
            if ncr.severity == NCR.Severity.CRITICAL or ncr.classification == NCR.Classification.CRITICAL:
                from django.contrib.auth import get_user_model
                from apps.core.notifications import send_qms_email
                User = get_user_model()
                qa_leaders = User.objects.filter(role__in=[User.Role.QA_MANAGER, User.Role.SUPER_ADMIN], is_active=True)
                for leader in qa_leaders:
                    Notification.create_notification(
                        recipient=leader,
                        title=f"🚨 CRITICAL NCR RAISED: {ncr.ncr_number}",
                        message=f"CRITICAL defect on {ncr.product} ({ncr.department.name}). Containment required!",
                        link=f"/ncr/{ncr.id}/"
                    )
                recipient_emails = [l.email for l in qa_leaders if l.email]
                if recipient_emails:
                    send_qms_email(
                        subject=f"CRITICAL DEFECT ALERT: {ncr.ncr_number} - {ncr.product}",
                        template_name="emails/ncr_critical_alert.html",
                        context={'ncr': ncr},
                        recipient_list=recipient_emails
                    )

            messages.success(request, f"Nonconformity Report '{ncr.ncr_number}' registered successfully.")
            return redirect('ncr:detail', ncr_id=ncr.id)
    else:
        initial = {'date': timezone.now().date(), 'reported_by': request.user}
        if request.GET.get('process_id'):
            initial['process'] = request.GET.get('process_id')
        form = NCRForm(initial=initial)

    return render(request, 'ncr/ncr_form.html', {'form': form, 'title': 'Raise Nonconformity Report (NCR)'})

@login_required
def ncr_print_red_tag(request, ncr_id):
    ncr = get_object_or_404(
        NCR.objects.select_related('department', 'process', 'reported_by', 'responsible_person'),
        id=ncr_id
    )
    from apps.core.utils import generate_qr_code_base64
    ncr_url = request.build_absolute_uri(f"/ncr/{ncr.id}/")
    qr_code_data = generate_qr_code_base64(ncr_url)
    return render(request, 'ncr/red_tag_print.html', {
        'ncr': ncr,
        'qr_code_data': qr_code_data,
    })

@login_required
def ncr_edit(request, ncr_id):
    ncr = get_object_or_404(NCR, id=ncr_id)
    if ncr.status == NCR.Status.CLOSED and not request.user.can_close_ncr():
        messages.error(request, "Closed NCR cannot be modified without QA Manager permissions.")
        return redirect('ncr:detail', ncr_id=ncr.id)

    if request.method == 'POST':
        form = NCRForm(request.POST, request.FILES, instance=ncr)
        if form.is_valid():
            form.save()
            log_audit(request.user, 'UPDATE', 'NCR', ncr.id, ncr.ncr_number)
            messages.success(request, f"NCR '{ncr.ncr_number}' updated.")
            return redirect('ncr:detail', ncr_id=ncr.id)
    else:
        form = NCRForm(instance=ncr)

    return render(request, 'ncr/ncr_form.html', {'form': form, 'title': f'Edit NCR: {ncr.ncr_number}', 'ncr': ncr})

@login_required
def ncr_save_five_whys(request, ncr_id):
    ncr = get_object_or_404(NCR, id=ncr_id)
    try:
        five_whys = ncr.five_whys
    except FiveWhysAnalysis.DoesNotExist:
        five_whys = FiveWhysAnalysis(ncr=ncr)

    if request.method == 'POST':
        form = FiveWhysForm(request.POST, instance=five_whys)
        if form.is_valid():
            fw = form.save(commit=False)
            fw.ncr = ncr
            fw.save()

            if fw.root_cause_conclusion:
                ncr.root_cause_summary = fw.root_cause_conclusion
                ncr.save(update_fields=['root_cause_summary'])

            log_audit(request.user, 'UPDATE', 'NCR', ncr.id, ncr.ncr_number, notes='Updated 5-Why Analysis')
            messages.success(request, "5-Whys Root Cause Analysis saved.")
    return redirect('ncr:detail', ncr_id=ncr.id)

@login_required
def ncr_add_fishbone_cause(request, ncr_id):
    ncr = get_object_or_404(NCR, id=ncr_id)
    if request.method == 'POST':
        form = FishboneCauseForm(request.POST)
        if form.is_valid():
            cause = form.save(commit=False)
            cause.ncr = ncr
            cause.save()
            log_audit(request.user, 'UPDATE', 'NCR', ncr.id, ncr.ncr_number, notes=f'Added Fishbone cause under {cause.category}')
            messages.success(request, f"Added cause to {cause.get_category_display()}.")
    return redirect('ncr:detail', ncr_id=ncr.id)

@login_required
def ncr_close_view(request, ncr_id):
    ncr = get_object_or_404(NCR, id=ncr_id)
    if not request.user.can_close_ncr():
        messages.error(request, "Only QA Managers or QA Engineers can formally verify and close NCRs.")
        return redirect('ncr:detail', ncr_id=ncr.id)

    if request.method == 'POST':
        form = NCRCloseForm(request.POST, instance=ncr)
        if form.is_valid():
            ncr_obj = form.save(commit=False)
            ncr_obj.status = NCR.Status.CLOSED
            ncr_obj.verified_by = request.user
            ncr_obj.closed_date = timezone.now().date()
            try:
                ncr_obj.save()
                log_audit(request.user, 'CLOSE', 'NCR', ncr_obj.id, ncr_obj.ncr_number, notes='Verified and formally closed')
                messages.success(request, f"NCR '{ncr_obj.ncr_number}' successfully closed and verified.")
            except Exception as e:
                messages.error(request, str(e))
    return redirect('ncr:detail', ncr_id=ncr.id)

@login_required
def ncr_escalate_capa(request, ncr_id):
    ncr = get_object_or_404(NCR, id=ncr_id)
    if request.method == 'POST':
        capa = CAPA.objects.create(
            title=f"CAPA for {ncr.ncr_number}: {ncr.product}",
            source=CAPA.Source.NCR,
            related_ncr=ncr,
            description=f"Escalated from {ncr.ncr_number}.\n\nProblem: {ncr.description}\n\nRequirement: {ncr.requirement}",
            root_cause=ncr.root_cause_summary or "Root cause investigation underway.",
            corrective_action=ncr.containment_action or "Containment initiated.",
            preventive_action="Evaluate systemic occurrence and update relevant FMEA / standard procedures.",
            responsible_person=ncr.responsible_person,
            start_date=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=30),
            verification_method="Audit next 3 production batches and evaluate Cpk index.",
            status=CAPA.Status.OPEN
        )
        log_audit(request.user, 'CREATE', 'CAPA', capa.id, capa.capa_number, notes=f'Escalated from {ncr.ncr_number}')
        messages.success(request, f"Successfully escalated NCR {ncr.ncr_number} to {capa.capa_number}.")
        return redirect('capa:detail', capa_id=capa.id)
    return redirect('ncr:detail', ncr_id=ncr.id)
