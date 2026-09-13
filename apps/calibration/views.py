from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Equipment
from .forms import EquipmentForm
from apps.core.utils import log_audit

@login_required
def calibration_list(request):
    equipment = Equipment.objects.select_related('department').all()

    # Dynamic status update
    for eq in equipment:
        old_status = eq.status
        eq.update_status()
        if eq.status != old_status:
            eq.save(update_fields=['status'])

    category = request.GET.get('category')
    status = request.GET.get('status')
    department = request.GET.get('department')

    if category:
        equipment = equipment.filter(category=category)
    if status:
        equipment = equipment.filter(status=status)
    if department:
        equipment = equipment.filter(department_id=department)

    # Alerts counters
    expired_count = Equipment.objects.filter(status=Equipment.Status.EXPIRED).count()
    due_soon_count = Equipment.objects.filter(status=Equipment.Status.DUE_SOON).count()

    return render(request, 'calibration/equipment_list.html', {
        'equipment': equipment,
        'selected_category': category,
        'selected_status': status,
        'expired_count': expired_count,
        'due_soon_count': due_soon_count,
    })

@login_required
def calibration_detail(request, eq_id):
    eq = get_object_or_404(
        Equipment.objects.select_related('department'),
        id=eq_id
    )
    eq.update_status()
    from apps.core.utils import generate_qr_code_base64
    qr_code_data = generate_qr_code_base64(request.build_absolute_uri())
    return render(request, 'calibration/equipment_detail.html', {
        'eq': eq,
        'qr_code_data': qr_code_data,
    })

@login_required
def equipment_sticker(request, eq_id):
    equipment = get_object_or_404(Equipment.objects.select_related('department'), id=eq_id)
    from apps.core.utils import generate_qr_code_base64
    eq_url = request.build_absolute_uri(f"/calibration/{equipment.id}/")
    qr_code_data = generate_qr_code_base64(eq_url)
    return render(request, 'calibration/calibration_sticker.html', {
        'equipment': equipment,
        'qr_code_data': qr_code_data,
    })

@login_required
def calibration_create(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES)
        if form.is_valid():
            eq = form.save()
            log_audit(request.user, 'CREATE', 'Equipment', eq.id, eq.equipment_id)
            messages.success(request, f"Equipment '{eq.equipment_id}' registered in metrology system.")
            return redirect('calibration:detail', eq_id=eq.id)
    else:
        form = EquipmentForm()

    return render(request, 'calibration/equipment_form.html', {'form': form, 'title': 'Register Measuring & Test Equipment'})

@login_required
def calibration_edit(request, eq_id):
    eq = get_object_or_404(Equipment, id=eq_id)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES, instance=eq)
        if form.is_valid():
            form.save()
            log_audit(request.user, 'UPDATE', 'Equipment', eq.id, eq.equipment_id)
            messages.success(request, f"Equipment '{eq.equipment_id}' updated.")
            return redirect('calibration:detail', eq_id=eq.id)
    else:
        form = EquipmentForm(instance=eq)

    return render(request, 'calibration/equipment_form.html', {'form': form, 'title': f'Edit Equipment: {eq.equipment_id}', 'equipment': eq})
