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


@login_required
def spc_analysis_view(request):
    """
    Statistical Process Control (SPC) & Process Capability (Cp / Cpk) Engine.
    IATF 16949 compliant capability assessment.
    """
    import math

    feature_name = request.GET.get('feature', 'Cylinder Outer Diameter (Ø45mm)')
    usl_param = request.GET.get('usl')
    lsl_param = request.GET.get('lsl')
    target_param = request.GET.get('target')
    raw_samples = request.GET.get('samples', '')

    default_samples = [
        45.012, 45.008, 45.015, 44.995, 45.002,
        45.005, 45.018, 44.998, 45.004, 45.009,
        45.011, 45.003, 44.997, 45.006, 45.014,
        45.000, 45.008, 45.002, 45.010, 45.007,
        45.004, 44.999, 45.006, 45.012, 45.003
    ]

    try:
        usl = float(usl_param) if usl_param else 45.025
        lsl = float(lsl_param) if lsl_param else 44.975
        target = float(target_param) if target_param else 45.000
    except ValueError:
        usl, lsl, target = 45.025, 44.975, 45.000

    samples = []
    if raw_samples:
        for val in raw_samples.replace(',', ' ').replace('\n', ' ').split():
            try:
                samples.append(float(val))
            except ValueError:
                pass
    if not samples:
        samples = default_samples

    n = len(samples)
    mean = sum(samples) / n
    variance = sum((x - mean) ** 2 for x in samples) / (n - 1) if n > 1 else 0
    std_dev = math.sqrt(variance)

    # Process capability calculations
    tolerance = usl - lsl
    cp = tolerance / (6 * std_dev) if std_dev > 0 else 0
    cpu = (usl - mean) / (3 * std_dev) if std_dev > 0 else 0
    cpl = (mean - lsl) / (3 * std_dev) if std_dev > 0 else 0
    cpk = min(cpu, cpl) if std_dev > 0 else 0

    # Control Limits (X-bar individual chart)
    ucl = mean + 3 * std_dev
    lcl = mean - 3 * std_dev

    # Evaluation verdict
    if cpk >= 1.67:
        verdict = "EXCELLENT / WORLD CLASS"
        verdict_color = "success"
        verdict_desc = "Six Sigma process performance (Cpk >= 1.67). Expected defect rate < 1 PPM."
    elif cpk >= 1.33:
        verdict = "CAPABLE & ADEQUATE"
        verdict_color = "success"
        verdict_desc = "Standard automotive / aerospace benchmark capability (Cpk >= 1.33)."
    elif cpk >= 1.00:
        verdict = "MARGINALLY CAPABLE"
        verdict_color = "warning"
        verdict_desc = "Process produces items close to specification limits. Continuous monitoring required."
    else:
        verdict = "INCAPABLE / HIGH DEFECT RISK"
        verdict_color = "danger"
        verdict_desc = "Process variation exceeds tolerance limits. Scrap/rework is actively generated."

    # Histogram calculation
    min_val = min(min(samples), lsl)
    max_val = max(max(samples), usl)
    num_bins = 10
    bin_width = (max_val - min_val) / num_bins if max_val > min_val else 1
    bins = [min_val + i * bin_width for i in range(num_bins + 1)]
    bin_labels = [f"{bins[i]:.3f}" for i in range(num_bins)]
    bin_counts = [0] * num_bins
    for s in samples:
        for i in range(num_bins):
            if i == num_bins - 1:
                if bins[i] <= s <= bins[i+1]:
                    bin_counts[i] += 1
                    break
            elif bins[i] <= s < bins[i+1]:
                bin_counts[i] += 1
                break

    context = {
        'feature_name': feature_name,
        'usl': usl,
        'lsl': lsl,
        'target': target,
        'samples_str': ", ".join(f"{x:.3f}" for x in samples),
        'sample_size': n,
        'mean': round(mean, 4),
        'std_dev': round(std_dev, 4),
        'cp': round(cp, 2),
        'cpu': round(cpu, 2),
        'cpl': round(cpl, 2),
        'cpk': round(cpk, 2),
        'ucl': round(ucl, 4),
        'lcl': round(lcl, 4),
        'verdict': verdict,
        'verdict_color': verdict_color,
        'verdict_desc': verdict_desc,
        'samples': samples,
        'sample_indices': list(range(1, n + 1)),
        'bin_labels': bin_labels,
        'bin_counts': bin_counts,
    }
    return render(request, 'inspections/spc_analysis.html', context)
