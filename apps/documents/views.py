from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Document, DocumentRevision
from .forms import DocumentForm, NewRevisionForm
from apps.core.utils import log_audit
from apps.notifications.models import Notification

@login_required
def document_list(request):
    docs = Document.objects.select_related('department', 'process', 'owner').all()
    
    doc_type = request.GET.get('doc_type')
    status = request.GET.get('status')
    department = request.GET.get('department')
    
    if doc_type:
        docs = docs.filter(document_type=doc_type)
    if status:
        docs = docs.filter(status=status)
    if department:
        docs = docs.filter(department_id=department)

    context = {
        'documents': docs,
        'selected_type': doc_type,
        'selected_status': status,
    }
    return render(request, 'documents/document_list.html', context)

@login_required
def document_detail(request, doc_id):
    doc = get_object_or_404(
        Document.objects.select_related('department', 'process', 'owner', 'prepared_by', 'reviewed_by', 'approved_by'),
        id=doc_id
    )
    revisions = doc.revisions.select_related('approved_by', 'created_by').all()
    revision_form = NewRevisionForm()
    return render(request, 'documents/document_detail.html', {
        'doc': doc,
        'revisions': revisions,
        'revision_form': revision_form
    })

@login_required
def document_create(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.status = Document.Status.DRAFT
            doc.save()
            log_audit(request.user, 'CREATE', 'Document', doc.id, doc.document_number)
            messages.success(request, f"Document '{doc.document_number}' created as Draft.")
            return redirect('documents:detail', doc_id=doc.id)
    else:
        form = DocumentForm()

    return render(request, 'documents/document_form.html', {'form': form, 'title': 'Create Controlled Document'})

@login_required
def document_edit(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    if doc.status == Document.Status.APPROVED and not request.user.can_approve_documents():
        messages.error(request, "Approved documents cannot be edited directly. Please create a new revision.")
        return redirect('documents:detail', doc_id=doc.id)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            log_audit(request.user, 'UPDATE', 'Document', doc.id, doc.document_number)
            messages.success(request, f"Document '{doc.document_number}' updated.")
            return redirect('documents:detail', doc_id=doc.id)
    else:
        form = DocumentForm(instance=doc)

    return render(request, 'documents/document_form.html', {'form': form, 'title': f'Edit Document: {doc.document_number}', 'doc': doc})

@login_required
def document_submit_review(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    if doc.status != Document.Status.DRAFT:
        messages.warning(request, "Only draft documents can be submitted for review.")
        return redirect('documents:detail', doc_id=doc.id)

    doc.status = Document.Status.UNDER_REVIEW
    doc.save(update_fields=['status'])
    log_audit(request.user, 'UPDATE', 'Document', doc.id, doc.document_number, notes='Submitted for QA review')

    # Notify QA managers
    if doc.reviewed_by:
        Notification.create_notification(
            recipient=doc.reviewed_by,
            title=f"Document Review: {doc.document_number}",
            message=f"{request.user.full_name} submitted document {doc.document_number} for your review.",
            link=f"/documents/{doc.id}/"
        )

    messages.success(request, f"Document '{doc.document_number}' submitted for review.")
    return redirect('documents:detail', doc_id=doc.id)

@login_required
def document_approve(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    if not request.user.can_approve_documents():
        messages.error(request, "You do not have the required authority to approve controlled documents.")
        return redirect('documents:detail', doc_id=doc.id)

    doc.status = Document.Status.APPROVED
    doc.approved_by = request.user
    if not doc.effective_date:
        doc.effective_date = timezone.now().date()
    doc.save(update_fields=['status', 'approved_by', 'effective_date'])

    log_audit(request.user, 'APPROVE', 'Document', doc.id, doc.document_number, notes=f'Approved by {request.user.full_name}')
    messages.success(request, f"Document '{doc.document_number}' successfully Approved.")
    return redirect('documents:detail', doc_id=doc.id)

@login_required
def document_reject(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    if not request.user.can_approve_documents():
        messages.error(request, "Permission denied.")
        return redirect('documents:detail', doc_id=doc.id)

    doc.status = Document.Status.DRAFT
    doc.save(update_fields=['status'])
    log_audit(request.user, 'REJECT', 'Document', doc.id, doc.document_number, notes='Rejected back to Draft')
    messages.warning(request, f"Document '{doc.document_number}' returned to Draft status.")
    return redirect('documents:detail', doc_id=doc.id)

@login_required
def document_new_revision(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    if request.method == 'POST':
        form = NewRevisionForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Archive current version to DocumentRevision
            DocumentRevision.objects.create(
                document=doc,
                revision_number=doc.revision_number,
                file_attachment=doc.file_attachment,
                revision_reason=doc.revision_reason or "Superseded revision archive",
                approved_by=doc.approved_by,
                approved_at=timezone.now(),
                created_by=request.user
            )

            # 2. Update doc to new revision in DRAFT status
            doc.revision_number = form.cleaned_data['new_revision_number']
            doc.revision_reason = form.cleaned_data['revision_reason']
            if form.cleaned_data.get('new_file'):
                doc.file_attachment = form.cleaned_data['new_file']
            doc.status = Document.Status.DRAFT
            doc.approved_by = None
            doc.save()

            log_audit(request.user, 'UPDATE', 'Document', doc.id, doc.document_number, notes=f'Created new revision {doc.revision_number}')
            messages.success(request, f"New revision Rev {doc.revision_number} initialized in Draft status.")
    return redirect('documents:detail', doc_id=doc.id)

@login_required
def document_mark_obsolete(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    if not request.user.can_approve_documents():
        messages.error(request, "Permission denied.")
        return redirect('documents:detail', doc_id=doc.id)

    doc.status = Document.Status.OBSOLETE
    doc.save(update_fields=['status'])
    log_audit(request.user, 'UPDATE', 'Document', doc.id, doc.document_number, notes='Marked as Obsolete')
    messages.info(request, f"Document '{doc.document_number}' marked as Obsolete.")
    return redirect('documents:detail', doc_id=doc.id)
