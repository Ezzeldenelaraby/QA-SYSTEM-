from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ManagementReviewMeeting
from .forms import ManagementReviewMeetingForm
from apps.actions.models import Action
from apps.core.utils import log_audit

@login_required
def meeting_list(request):
    status_filter = request.GET.get('status')
    meetings = ManagementReviewMeeting.objects.select_related('chairperson').all()
    if status_filter:
        meetings = meetings.filter(status=status_filter)

    total_count = ManagementReviewMeeting.objects.count()
    completed_count = ManagementReviewMeeting.objects.filter(status__in=[ManagementReviewMeeting.Status.COMPLETED, ManagementReviewMeeting.Status.MINUTES_APPROVED]).count()
    scheduled_count = ManagementReviewMeeting.objects.filter(status=ManagementReviewMeeting.Status.SCHEDULED).count()

    return render(request, 'management_review/meeting_list.html', {
        'meetings': meetings,
        'total_count': total_count,
        'completed_count': completed_count,
        'scheduled_count': scheduled_count,
        'selected_status': status_filter,
    })

@login_required
def meeting_detail(request, pk):
    meeting = get_object_or_404(ManagementReviewMeeting.objects.select_related('chairperson'), pk=pk)
    
    # Associated actions
    actions = Action.objects.filter(
        source_type='MANAGEMENT_REVIEW',
        source_id=meeting.id
    ).select_related('assigned_to', 'department')

    return render(request, 'management_review/meeting_detail.html', {
        'meeting': meeting,
        'actions': actions,
    })

@login_required
def meeting_create(request):
    if request.method == 'POST':
        form = ManagementReviewMeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save()
            log_audit(request.user, 'CREATE', 'ManagementReviewMeeting', meeting.id, meeting.meeting_number)
            messages.success(request, f"Management Review Meeting '{meeting.meeting_number}' created successfully.")
            return redirect('management_review:detail', pk=meeting.pk)
    else:
        form = ManagementReviewMeetingForm()

    return render(request, 'management_review/meeting_form.html', {
        'form': form,
        'title': 'Convene New Management Review Meeting'
    })

@login_required
def meeting_update(request, pk):
    meeting = get_object_or_404(ManagementReviewMeeting, pk=pk)
    if request.method == 'POST':
        form = ManagementReviewMeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            form.save()
            log_audit(request.user, 'UPDATE', 'ManagementReviewMeeting', meeting.id, meeting.meeting_number)
            messages.success(request, f"Management Review Meeting '{meeting.meeting_number}' updated successfully.")
            return redirect('management_review:detail', pk=meeting.pk)
    else:
        form = ManagementReviewMeetingForm(instance=meeting)

    return render(request, 'management_review/meeting_form.html', {
        'form': form,
        'meeting': meeting,
        'title': f'Edit Meeting: {meeting.meeting_number}'
    })

@login_required
def meeting_approve_minutes(request, pk):
    meeting = get_object_or_404(ManagementReviewMeeting, pk=pk)
    if request.method == 'POST':
        meeting.status = ManagementReviewMeeting.Status.MINUTES_APPROVED
        meeting.save(update_fields=['status'])
        log_audit(request.user, 'APPROVE', 'ManagementReviewMeeting', meeting.id, f"Approved minutes for {meeting.meeting_number}")
        messages.success(request, f"Minutes of Review '{meeting.meeting_number}' formally signed off and approved.")
    return redirect('management_review:detail', pk=meeting.pk)
