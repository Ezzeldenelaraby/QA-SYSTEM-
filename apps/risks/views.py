from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Risk
from .forms import RiskForm
from apps.core.utils import log_audit

@login_required
def risk_list(request):
    risks = Risk.objects.select_related('process', 'department', 'responsible_person').all()

    level = request.GET.get('level')
    status = request.GET.get('status')
    department = request.GET.get('department')
    process = request.GET.get('process')

    if level:
        risks = risks.filter(risk_level=level)
    if status:
        risks = risks.filter(status=status)
    if department:
        risks = risks.filter(department_id=department)
    if process:
        risks = risks.filter(process_id=process)

    return render(request, 'risks/risk_list.html', {
        'risks': risks,
        'selected_level': level,
        'selected_status': status,
    })

@login_required
def risk_matrix_view(request):
    risks = Risk.objects.select_related('process', 'department', 'responsible_person').all()

    # Build 5x5 matrix structure: Severity (5 down to 1) x Likelihood (1 up to 5)
    matrix = {}
    for s in range(5, 0, -1):
        matrix[s] = {}
        for l in range(1, 6):
            score = s * l
            # classify cell color
            if score >= 15:
                cell_class = 'rm-crit'
            elif score >= 10:
                cell_class = 'rm-high'
            elif score >= 5:
                cell_class = 'rm-med'
            else:
                cell_class = 'rm-low'

            cell_risks = [r for r in risks if r.severity == s and r.likelihood == l]
            matrix[s][l] = {
                'score': score,
                'class': cell_class,
                'count': len(cell_risks),
                'risks': cell_risks,
            }

    return render(request, 'risks/risk_matrix.html', {'matrix': matrix, 'total_risks': len(risks)})

@login_required
def risk_detail(request, risk_id):
    risk = get_object_or_404(
        Risk.objects.select_related('process', 'department', 'responsible_person'),
        id=risk_id
    )
    return render(request, 'risks/risk_detail.html', {'risk': risk})

@login_required
def risk_create(request):
    if request.method == 'POST':
        form = RiskForm(request.POST)
        if form.is_valid():
            risk = form.save()
            log_audit(request.user, 'CREATE', 'Risk', risk.id, risk.risk_id, notes=f'Score {risk.risk_score} - {risk.risk_level}')
            messages.success(request, f"Risk '{risk.risk_id}' registered successfully.")
            return redirect('risks:detail', risk_id=risk.id)
    else:
        form = RiskForm()

    return render(request, 'risks/risk_form.html', {'form': form, 'title': 'Register New Process Risk (FMEA)'})

@login_required
def risk_edit(request, risk_id):
    risk = get_object_or_404(Risk, id=risk_id)
    if request.method == 'POST':
        form = RiskForm(request.POST, instance=risk)
        if form.is_valid():
            form.save()
            log_audit(request.user, 'UPDATE', 'Risk', risk.id, risk.risk_id)
            messages.success(request, f"Risk '{risk.risk_id}' updated.")
            return redirect('risks:detail', risk_id=risk.id)
    else:
        form = RiskForm(instance=risk)

    return render(request, 'risks/risk_form.html', {'form': form, 'title': f'Edit Risk: {risk.risk_id}', 'risk': risk})
