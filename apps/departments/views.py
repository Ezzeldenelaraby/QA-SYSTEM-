from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Department
from .forms import DepartmentForm
from apps.core.utils import log_audit

@login_required
def department_list(request):
    departments = Department.objects.select_related('manager').all()
    return render(request, 'departments/department_list.html', {'departments': departments})

@login_required
def department_create(request):
    if not (request.user.is_super_admin or request.user.is_qa_manager):
        messages.error(request, "Permission denied.")
        return redirect('departments:list')

    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            log_audit(request.user, 'CREATE', 'Department', dept.id, dept.name)
            messages.success(request, f"Department '{dept.name}' created.")
            return redirect('departments:list')
    else:
        form = DepartmentForm()

    return render(request, 'departments/department_form.html', {'form': form, 'title': 'Create Department'})

@login_required
def department_edit(request, dept_id):
    if not (request.user.is_super_admin or request.user.is_qa_manager):
        messages.error(request, "Permission denied.")
        return redirect('departments:list')

    dept = get_object_or_404(Department, id=dept_id)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            log_audit(request.user, 'UPDATE', 'Department', dept.id, dept.name)
            messages.success(request, f"Department '{dept.name}' updated.")
            return redirect('departments:list')
    else:
        form = DepartmentForm(instance=dept)

    return render(request, 'departments/department_form.html', {'form': form, 'title': f'Edit Department: {dept.name}'})
