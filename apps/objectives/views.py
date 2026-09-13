from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
from .models import QualityObjective, ObjectiveMeasurement
from .forms import QualityObjectiveForm, ObjectiveMeasurementForm
from apps.core.utils import log_audit

@login_required
def objective_list(request):
    objectives = QualityObjective.objects.select_related('department', 'process', 'responsible_person').all()

    status = request.GET.get('status')
    department = request.GET.get('department')
    if status:
        objectives = objectives.filter(status=status)
    if department:
        objectives = objectives.filter(department_id=department)

    return render(request, 'objectives/objective_list.html', {
        'objectives': objectives,
        'selected_status': status,
    })

@login_required
def objective_detail(request, obj_id):
    obj = get_object_or_404(
        QualityObjective.objects.select_related('department', 'process', 'responsible_person'),
        id=obj_id
    )
    measurements = obj.measurements.all().order_by('period_date')
    measurement_form = ObjectiveMeasurementForm()

    # Prepare historical trend chart data
    chart_labels = [m.period_date.strftime('%b %Y') for m in measurements]
    chart_values = [float(m.value) for m in measurements]
    target_values = [float(obj.target)] * len(measurements)

    context = {
        'objective': obj,
        'measurements': measurements,
        'measurement_form': measurement_form,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_values_json': json.dumps(chart_values),
        'target_values_json': json.dumps(target_values),
    }
    return render(request, 'objectives/objective_detail.html', context)

@login_required
def objective_create(request):
    if request.method == 'POST':
        form = QualityObjectiveForm(request.POST)
        if form.is_valid():
            obj = form.save()
            log_audit(request.user, 'CREATE', 'QualityObjective', obj.id, obj.code)
            messages.success(request, f"Quality Objective '{obj.code}' created.")
            return redirect('objectives:detail', obj_id=obj.id)
    else:
        form = QualityObjectiveForm()

    return render(request, 'objectives/objective_form.html', {'form': form, 'title': 'Establish Quality Objective (KPI)'})

@login_required
def objective_edit(request, obj_id):
    obj = get_object_or_404(QualityObjective, id=obj_id)
    if request.method == 'POST':
        form = QualityObjectiveForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            log_audit(request.user, 'UPDATE', 'QualityObjective', obj.id, obj.code)
            messages.success(request, f"Quality Objective '{obj.code}' updated.")
            return redirect('objectives:detail', obj_id=obj.id)
    else:
        form = QualityObjectiveForm(instance=obj)

    return render(request, 'objectives/objective_form.html', {'form': form, 'title': f'Edit Objective: {obj.code}', 'objective': obj})

@login_required
def objective_add_measurement(request, obj_id):
    obj = get_object_or_404(QualityObjective, id=obj_id)
    if request.method == 'POST':
        form = ObjectiveMeasurementForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.objective = obj
            m.recorded_by = request.user
            m.save()

            # Update latest actual result on objective
            obj.actual_result = m.value
            obj.save()

            log_audit(request.user, 'UPDATE', 'QualityObjective', obj.id, obj.code, notes=f'Recorded monthly metric: {m.value} {obj.unit}')
            messages.success(request, f"Monthly measurement recorded: {m.value} {obj.unit}")
    return redirect('objectives:detail', obj_id=obj.id)
