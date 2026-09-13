from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import CAPA
from .forms import CAPAForm, CAPAEffectivenessForm
from apps.core.utils import log_audit
from apps.notifications.models import Notification

@login_required
def capa_list(request):
    capas = CAPA.objects.select_related('related_ncr', 'responsible_person', 'verified_by').all()

    status = request.GET.get('status')
    source = request.GET.get('source')
    if status:
        capas = capas.filter(status=status)
    if source:
        capas = capas.filter(source=source)

    return render(request, 'capa/capa_list.html', {
        'capas': capas,
        'selected_status': status,
        'selected_source': source,
    })

@login_required
def capa_detail(request, capa_id):
    capa = get_object_or_404(
        CAPA.objects.select_related('related_ncr', 'related_finding', 'related_risk', 'responsible_person', 'verified_by'),
        id=capa_id
    )
    eff_form = CAPAEffectivenessForm(instance=capa)
    from apps.core.utils import generate_qr_code_base64
    qr_code_data = generate_qr_code_base64(request.build_absolute_uri())
    return render(request, 'capa/capa_detail.html', {
        'capa': capa,
        'eff_form': eff_form,
        'qr_code_data': qr_code_data,
    })

@login_required
def capa_8d_pdf(request, capa_id):
    from django.http import HttpResponse
    from .reports import generate_8d_pdf
    capa = get_object_or_404(
        CAPA.objects.select_related('related_ncr', 'related_finding', 'related_risk', 'responsible_person', 'verified_by'),
        id=capa_id
    )
    pdf_bytes = generate_8d_pdf(capa)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="8D_Report_{capa.capa_number}.pdf"'
    return response

@login_required
def capa_create(request):
    if request.method == 'POST':
        form = CAPAForm(request.POST, request.FILES)
        if form.is_valid():
            capa = form.save()
            log_audit(request.user, 'CREATE', 'CAPA', capa.id, capa.capa_number)

            Notification.create_notification(
                recipient=capa.responsible_person,
                title=f"CAPA Assigned: {capa.capa_number}",
                message=f"You have been assigned lead on {capa.capa_number}: {capa.title}",
                link=f"/capa/{capa.id}/"
            )

            messages.success(request, f"CAPA '{capa.capa_number}' initiated.")
            return redirect('capa:detail', capa_id=capa.id)
    else:
        form = CAPAForm()

    return render(request, 'capa/capa_form.html', {'form': form, 'title': 'Initiate Corrective & Preventive Action (CAPA)'})

@login_required
def capa_edit(request, capa_id):
    capa = get_object_or_404(CAPA, id=capa_id)
    if capa.status == CAPA.Status.CLOSED and not request.user.can_verify_capa():
        messages.error(request, "Closed CAPAs cannot be modified without Quality Manager authority.")
        return redirect('capa:detail', capa_id=capa.id)

    if request.method == 'POST':
        form = CAPAForm(request.POST, request.FILES, instance=capa)
        if form.is_valid():
            form.save()
            log_audit(request.user, 'UPDATE', 'CAPA', capa.id, capa.capa_number)
            messages.success(request, f"CAPA '{capa.capa_number}' updated.")
            return redirect('capa:detail', capa_id=capa.id)
    else:
        form = CAPAForm(instance=capa)

    return render(request, 'capa/capa_form.html', {'form': form, 'title': f'Edit CAPA: {capa.capa_number}', 'capa': capa})

@login_required
def capa_close(request, capa_id):
    capa = get_object_or_404(CAPA, id=capa_id)
    if not request.user.can_verify_capa():
        messages.error(request, "Only certified QA Managers or Auditors can formally close CAPA projects.")
        return redirect('capa:detail', capa_id=capa.id)

    if request.method == 'POST':
        form = CAPAEffectivenessForm(request.POST, instance=capa)
        if form.is_valid():
            capa_obj = form.save(commit=False)
            capa_obj.status = CAPA.Status.CLOSED
            capa_obj.verified_by = request.user
            capa_obj.completion_date = timezone.now().date()
            try:
                capa_obj.save()
                log_audit(request.user, 'CLOSE', 'CAPA', capa_obj.id, capa_obj.capa_number, notes='Effectiveness verified and formally closed')
                messages.success(request, f"CAPA '{capa_obj.capa_number}' verified and formally Closed.")
            except Exception as e:
                messages.error(request, str(e))
    return redirect('capa:detail', capa_id=capa.id)
