from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel, SoftDeleteModel

class Document(TimeStampedModel, SoftDeleteModel):
    class DocType(models.TextChoices):
        POLICY = 'POLICY', 'Policy'
        PROCEDURE = 'PROCEDURE', 'Procedure'
        WORK_INSTRUCTION = 'WORK_INSTRUCTION', 'Work Instruction'
        FORM = 'FORM', 'Form'
        CHECKLIST = 'CHECKLIST', 'Checklist'
        FLOWCHART = 'FLOWCHART', 'Flowchart'
        SPECIFICATION = 'SPECIFICATION', 'Specification'
        MANUAL = 'MANUAL', 'Manual'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        APPROVED = 'APPROVED', 'Approved'
        OBSOLETE = 'OBSOLETE', 'Obsolete'

    document_number = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=30, choices=DocType.choices, default=DocType.PROCEDURE)
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='documents'
    )
    process = models.ForeignKey(
        'processes.Process',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    revision_number = models.CharField(max_length=20, default='01')
    issue_date = models.DateField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    review_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='owned_documents'
    )
    prepared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='prepared_documents'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_documents'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_documents'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    file_attachment = models.FileField(upload_to='documents/%Y/%m/', null=True, blank=True)
    revision_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['document_number']

    def __str__(self):
        return f"{self.document_number} - {self.title} (Rev {self.revision_number})"


class DocumentRevision(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='revisions')
    revision_number = models.CharField(max_length=20)
    file_attachment = models.FileField(upload_to='documents/revisions/%Y/%m/', null=True, blank=True)
    revision_reason = models.TextField()
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_revisions'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.document.document_number} - Rev {self.revision_number}"
