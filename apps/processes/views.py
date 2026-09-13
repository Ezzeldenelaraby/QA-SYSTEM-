from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Process
from .forms import ProcessForm
from apps.core.utils import log_audit

@login_required
def process_list(request):
    processes = Process.objects.select_related('department', 'process_owner').all()
    return render(request, 'processes/process_list.html', {'processes': processes})

@login_required
def process_detail(request, process_id):
    process = get_object_or_404(
        Process.objects.select_related('department', 'process_owner'),
        id=process_id
    )
    # Linked data for 360-degree traceability tabs
    documents = process.documents.select_related('owner').all()
    risks = process.risks.select_related('responsible_person').all()
    objectives = process.objectives.all()
    ncrs = process.ncrs.select_related('reported_by', 'responsible_person').all()
    audits = process.audits.select_related('lead_auditor').all()
    actions = process.actions.select_related('assigned_to').all()
    inspections = process.inspections.select_related('inspector').all()

    context = {
        'process': process,
        'documents': documents,
        'risks': risks,
        'objectives': objectives,
        'ncrs': ncrs,
        'audits': audits,
        'actions': actions,
        'inspections': inspections,
    }
    return render(request, 'processes/process_detail.html', context)

@login_required
def process_create(request):
    if not (request.user.is_super_admin or request.user.is_qa_staff or request.user.role == 'PROCESS_OWNER'):
        messages.error(request, "Permission denied to define processes.")
        return redirect('processes:list')

    if request.method == 'POST':
        form = ProcessForm(request.POST)
        if form.is_valid():
            proc = form.save()
            log_audit(request.user, 'CREATE', 'Process', proc.id, proc.name)
            messages.success(request, f"Process '{proc.code}' created.")
            return redirect('processes:detail', process_id=proc.id)
    else:
        form = ProcessForm()

    return render(request, 'processes/process_form.html', {'form': form, 'title': 'Create Manufacturing Process'})

@login_required
def process_edit(request, process_id):
    proc = get_object_or_404(Process, id=process_id)
    if not (request.user.is_super_admin or request.user.is_qa_staff or request.user == proc.process_owner):
        messages.error(request, "Permission denied to edit this process.")
        return redirect('processes:detail', process_id=proc.id)

    if request.method == 'POST':
        form = ProcessForm(request.POST, instance=proc)
        if form.is_valid():
            form.save()
            log_audit(request.user, 'UPDATE', 'Process', proc.id, proc.name)
            messages.success(request, f"Process '{proc.code}' updated.")
            return redirect('processes:detail', process_id=proc.id)
    else:
        form = ProcessForm(instance=proc)

    return render(request, 'processes/process_form.html', {'form': form, 'title': f'Edit Process: {proc.code}', 'process': proc})
