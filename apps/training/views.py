from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Course, TrainingRecord
from .forms import CourseForm, TrainingRecordForm
from apps.core.utils import log_audit

User = get_user_model()

@login_required
def training_matrix_view(request):
    department_id = request.GET.get('department')
    employees = User.objects.filter(is_active=True).select_related('department').order_by('first_name')
    if department_id:
        employees = employees.filter(department_id=department_id)

    courses = Course.objects.all().order_by('code')
    records = TrainingRecord.objects.select_related('employee', 'course').all()

    # Build matrix map: (emp_id, course_id) -> record
    record_map = {(r.employee_id, r.course_id): r for r in records}

    matrix_rows = []
    completed_total = 0
    missing_total = 0
    expired_total = 0

    for emp in employees:
        row_cells = []
        for c in courses:
            rec = record_map.get((emp.id, c.id))
            if rec:
                if rec.is_expired:
                    status = 'EXPIRED'
                    css = 'badge-red'
                    expired_total += 1
                else:
                    status = 'COMPLETED'
                    css = 'badge-green'
                    completed_total += 1
            else:
                status = 'MISSING'
                css = 'badge-yellow'
                missing_total += 1
            row_cells.append({'status': status, 'css': css, 'record': rec})
        matrix_rows.append({'employee': emp, 'cells': row_cells})

    total_slots = len(employees) * len(courses) if courses and employees else 1
    completion_rate = round((completed_total / total_slots) * 100, 1)

    from apps.departments.models import Department
    departments = Department.objects.all()

    return render(request, 'training/training_matrix.html', {
        'matrix_rows': matrix_rows,
        'courses': courses,
        'completion_rate': completion_rate,
        'completed_total': completed_total,
        'expired_total': expired_total,
        'missing_total': missing_total,
        'departments': departments,
        'selected_dept': department_id,
    })

@login_required
def course_list(request):
    courses = Course.objects.select_related('related_process', 'related_document').all()
    return render(request, 'training/course_list.html', {'courses': courses})

@login_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            log_audit(request.user, 'CREATE', 'Course', course.id, course.code)
            messages.success(request, f"Course '{course.code}' registered in training catalog.")
            return redirect('training:course_list')
    else:
        form = CourseForm()

    return render(request, 'training/course_form.html', {'form': form, 'title': 'Register Training Course'})

@login_required
def record_list(request):
    records = TrainingRecord.objects.select_related('employee', 'course').all()
    return render(request, 'training/record_list.html', {'records': records})

@login_required
def record_create(request):
    if request.method == 'POST':
        form = TrainingRecordForm(request.POST, request.FILES)
        if form.is_valid():
            rec = form.save()
            log_audit(request.user, 'CREATE', 'TrainingRecord', rec.id, f"{rec.employee.username}: {rec.course.code}")
            messages.success(request, f"Training recorded for {rec.employee.full_name}.")
            return redirect('training:matrix')
    else:
        form = TrainingRecordForm()

    return render(request, 'training/record_form.html', {'form': form, 'title': 'Log Employee Training Record'})
