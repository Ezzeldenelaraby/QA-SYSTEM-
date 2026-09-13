from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Action
from .forms import ActionForm, ActionCompleteForm, ActionVerifyForm
from apps.core.utils import log_audit
from apps.notifications.models import Notification

@login_required
def action_list(request):
    actions = Action.objects.select_related('department', 'process', 'assigned_to', 'created_by').all()
    
    # Auto refresh overdue actions
    today = timezone.now().date()
    for act in actions:
        if act.is_overdue and act.status not in [Action.Status.COMPLETED, Action.Status.CANCELLED, Action.Status.OVERDUE]:
            act.update_overdue_status()

    priority = request.GET.get('priority')
    status = request.GET.get('status')
    source_type = request.GET.get('source_type')
    assigned_to = request.GET.get('assigned_to')

    if priority:
        actions = actions.filter(priority=priority)
    if status:
        actions = actions.filter(status=status)
    if source_type:
        actions = actions.filter(source_type=source_type)
    if assigned_to:
        actions = actions.filter(assigned_to_id=assigned_to)

    return render(request, 'actions/action_list.html', {
        'actions': actions,
        'selected_priority': priority,
        'selected_status': status,
        'selected_source': source_type,
    })

@login_required
def my_actions(request):
    today = timezone.now().date()
    week_end = today + timedelta(days=7)

    base_qs = Action.objects.filter(assigned_to=request.user).select_related('department', 'process')
    for act in base_qs:
        if act.is_overdue and act.status not in [Action.Status.COMPLETED, Action.Status.CANCELLED, Action.Status.OVERDUE]:
            act.update_overdue_status()

    my_open = base_qs.filter(status__in=[Action.Status.OPEN, Action.Status.IN_PROGRESS, Action.Status.PENDING_VERIFICATION])
    due_today = base_qs.filter(due_date=today, status__in=[Action.Status.OPEN, Action.Status.IN_PROGRESS])
    due_week = base_qs.filter(due_date__gt=today, due_date__lte=week_end, status__in=[Action.Status.OPEN, Action.Status.IN_PROGRESS])
    overdue = base_qs.filter(status=Action.Status.OVERDUE)
    completed = base_qs.filter(status=Action.Status.COMPLETED)

    return render(request, 'actions/my_actions.html', {
        'my_open': my_open,
        'due_today': due_today,
        'due_week': due_week,
        'overdue': overdue,
        'completed': completed,
    })

@login_required
def action_detail(request, action_id):
    action = get_object_or_404(
        Action.objects.select_related('department', 'process', 'assigned_to', 'created_by', 'verified_by'),
        id=action_id
    )
    if action.is_overdue and action.status not in [Action.Status.COMPLETED, Action.Status.CANCELLED, Action.Status.OVERDUE]:
        action.update_overdue_status()

    complete_form = ActionCompleteForm(instance=action)
    verify_form = ActionVerifyForm(instance=action)

    return render(request, 'actions/action_detail.html', {
        'action': action,
        'complete_form': complete_form,
        'verify_form': verify_form,
    })

@login_required
def action_create(request):
    if request.method == 'POST':
        form = ActionForm(request.POST)
        if form.is_valid():
            action = form.save(commit=False)
            action.created_by = request.user
            action.action_number = Action.generate_action_number()
            action.save()

            log_audit(request.user, 'CREATE', 'Action', action.id, action.action_number)

            Notification.create_notification(
                recipient=action.assigned_to,
                title=f"New Action Assigned: {action.action_number}",
                message=f"You have been assigned action '{action.title}'. Due Date: {action.due_date}",
                link=f"/actions/{action.id}/"
            )

            messages.success(request, f"Action '{action.action_number}' created and assigned.")
            return redirect('actions:detail', action_id=action.id)
    else:
        initial_data = {}
        if request.GET.get('source_type'):
            initial_data['source_type'] = request.GET.get('source_type')
        if request.GET.get('source_id'):
            initial_data['source_id'] = request.GET.get('source_id')
        if request.GET.get('process_id'):
            initial_data['process'] = request.GET.get('process_id')
        form = ActionForm(initial=initial_data)

    return render(request, 'actions/action_form.html', {'form': form, 'title': 'Create New Action'})

@login_required
def action_edit(request, action_id):
    action = get_object_or_404(Action, id=action_id)
    if request.method == 'POST':
        form = ActionForm(request.POST, instance=action)
        if form.is_valid():
            form.save()
            log_audit(request.user, 'UPDATE', 'Action', action.id, action.action_number)
            messages.success(request, f"Action '{action.action_number}' updated.")
            return redirect('actions:detail', action_id=action.id)
    else:
        form = ActionForm(instance=action)

    return render(request, 'actions/action_form.html', {'form': form, 'title': f'Edit Action: {action.action_number}', 'action': action})

@login_required
def action_complete(request, action_id):
    action = get_object_or_404(Action, id=action_id)
    if request.method == 'POST':
        form = ActionCompleteForm(request.POST, request.FILES, instance=action)
        if form.is_valid():
            action = form.save(commit=False)
            action.status = Action.Status.PENDING_VERIFICATION
            action.completion_date = timezone.now().date()
            action.save()

            log_audit(request.user, 'UPDATE', 'Action', action.id, action.action_number, notes='Completed by assignee, pending verification')
            messages.success(request, f"Action '{action.action_number}' marked as completed. Submitted for verification.")
    return redirect('actions:detail', action_id=action.id)

@login_required
def action_verify(request, action_id):
    action = get_object_or_404(Action, id=action_id)
    if not (request.user.is_super_admin or request.user.is_qa_staff or request.user == action.created_by):
        messages.error(request, "Only the creator or QA staff can verify actions.")
        return redirect('actions:detail', action_id=action.id)

    if request.method == 'POST':
        form = ActionVerifyForm(request.POST, instance=action)
        if form.is_valid():
            action = form.save(commit=False)
            action.status = Action.Status.COMPLETED
            action.verified_by = request.user
            action.save()

            log_audit(request.user, 'APPROVE', 'Action', action.id, action.action_number, notes=f'Verified and closed by {request.user.full_name}')
            messages.success(request, f"Action '{action.action_number}' verified and formally Closed.")
    return redirect('actions:detail', action_id=action.id)
