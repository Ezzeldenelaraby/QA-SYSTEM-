from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Inspection, InspectionItem
from .forms import InspectionForm, InspectionItemForm
from apps.ncr.models import NCR
from apps.core.utils import log_audit

@login_required
def inspection_list(request):
    inspections = Inspection.objects.select_related('process', 'inspector').all()

    result = request.GET.get('result')
    process = request.GET.get('process')
    if result:
        inspections = inspections.filter(overall_result=result)
    if process:
        inspections = inspections.filter(process_id=process)

    return render(request, 'inspections/inspection_list.html', {
        'inspections': inspections,
        'selected_result': result,
    })

@login_required
def inspection_detail(request, insp_id):
    inspection = get_object_or_404(
        Inspection.objects.select_related('process', 'inspector', 'linked_ncr'),
        id=insp_id
    )
    items = inspection.items.all()
    item_form = InspectionItemForm()
    has_ng = any(item.result == 'NG' for item in items)

    return render(request, 'inspections/inspection_detail.html', {
        'inspection': inspection,
        'items': items,
        'item_form': item_form,
        'has_ng': has_ng,
    })

@login_required
def inspection_create(request):
    if request.method == 'POST':
        form = InspectionForm(request.POST)
        if form.is_valid():
            insp = form.save()
            log_audit(request.user, 'CREATE', 'Inspection', insp.id, insp.inspection_number)
            messages.success(request, f"Inspection Sheet '{insp.inspection_number}' created.")
            return redirect('inspections:detail', insp_id=insp.id)
    else:
        form = InspectionForm(initial={'inspector': request.user, 'date': timezone.now().date()})

    return render(request, 'inspections/inspection_form.html', {'form': form, 'title': 'Create Shop Floor Inspection Sheet'})

@login_required
def inspection_edit(request, insp_id):
    insp = get_object_or_404(Inspection, id=insp_id)
    if request.method == 'POST':
        form = InspectionForm(request.POST, instance=insp)
        if form.is_valid():
            form.save()
            log_audit(request.user, 'UPDATE', 'Inspection', insp.id, insp.inspection_number)
            messages.success(request, f"Inspection '{insp.inspection_number}' updated.")
            return redirect('inspections:detail', insp_id=insp.id)
    else:
        form = InspectionForm(instance=insp)

    return render(request, 'inspections/inspection_form.html', {'form': form, 'title': f'Edit Inspection: {insp.inspection_number}', 'inspection': insp})

@login_required
def inspection_add_item(request, insp_id):
    insp = get_object_or_404(Inspection, id=insp_id)
    if request.method == 'POST':
        form = InspectionItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.inspection = insp
            item.save()

            # Auto flag overall result if NG
            if item.result == 'NG' and insp.overall_result != 'NG':
                insp.overall_result = 'NG'
                insp.save(update_fields=['overall_result'])

            messages.success(request, f"Inspection item '{item.checkpoint_name}' logged.")
    return redirect('inspections:detail', insp_id=insp.id)

@login_required
def inspection_create_ncr(request, insp_id):
    insp = get_object_or_404(Inspection, id=insp_id)
    if insp.linked_ncr:
        messages.info(request, "An NCR is already linked to this inspection.")
        return redirect('ncr:detail', ncr_id=insp.linked_ncr.id)

    ng_items = insp.items.filter(result='NG')
    ng_desc = "\n".join([f"- {item.checkpoint_name}: Measured {item.measured_value} {item.unit} (Spec: {item.specification}). {item.comment}" for item in ng_items])
    ng_req = "\n".join([f"- {item.checkpoint_name}: {item.specification}" for item in ng_items])

    ncr = NCR.objects.create(
        date=timezone.now().date(),
        department=insp.process.department,
        process=insp.process,
        product=insp.product,
        batch_lot=insp.batch_lot,
        reported_by=request.user,
        source=NCR.Source.INSPECTION,
        description=f"Nonconformance detected during shop floor inspection {insp.inspection_number} on machine {insp.machine} ({insp.get_shift_display()}):\n\n{ng_desc or insp.comments}",
        requirement=ng_req or "Standard drawing specification tolerances.",
        evidence=f"Inspection sheet {insp.inspection_number}. Measured by {insp.inspector.full_name}",
        classification=NCR.Classification.MAJOR if len(ng_items) > 1 else NCR.Classification.MINOR,
        severity=NCR.Severity.HIGH,
        immediate_correction=f"Quarantine batch {insp.batch_lot} at machine {insp.machine}.",
        containment_action="Check preceding and succeeding pieces from current machining run.",
        responsible_person=insp.process.process_owner or request.user,
        due_date=timezone.now().date() + timezone.timedelta(days=7),
        status=NCR.Status.OPEN
    )

    insp.linked_ncr = ncr
    insp.save(update_fields=['linked_ncr'])

    log_audit(request.user, 'CREATE', 'NCR', ncr.id, ncr.ncr_number, notes=f'Auto-created from inspection {insp.inspection_number}')
    messages.success(request, f"Successfully raised NCR '{ncr.ncr_number}' from failed inspection checkpoints!")
    return redirect('ncr:detail', ncr_id=ncr.id)
