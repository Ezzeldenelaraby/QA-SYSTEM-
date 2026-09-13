from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimeStampedModel, SoftDeleteModel

class AuditPlan(TimeStampedModel, SoftDeleteModel):
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        REPORTING = 'REPORTING', 'Reporting'
        CLOSED = 'CLOSED', 'Closed'

    audit_number = models.CharField(max_length=50, unique=True, db_index=True)
    audit_title = models.CharField(max_length=255)
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='audits'
    )
    process = models.ForeignKey(
        'processes.Process',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audits'
    )
    lead_auditor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='led_audits'
    )
    audit_team = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='participated_audits'
    )
    audit_date = models.DateField()
    scope = models.TextField(help_text="Boundary, processes, and shifts covered by this audit")
    criteria = models.TextField(default="ISO 9001:2015, Quality Manual, Work Instructions")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.SCHEDULED, db_index=True)
    summary_notes = models.TextField(blank=True, help_text="Executive audit outcome summary")

    class Meta:
        ordering = ['-audit_date', '-id']

    def __str__(self):
        return f"{self.audit_number}: {self.audit_title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.audit_number:
            self.audit_number = self.generate_audit_number()
        super().save(*args, **kwargs)

    @classmethod
    def generate_audit_number(cls):
        year = timezone.now().year
        prefix = f"AUD-{year}-"
        last = cls.all_objects.filter(audit_number__startswith=prefix).order_by('audit_number').last()
        if last:
            try:
                seq = int(last.audit_number.split('-')[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"


class AuditChecklistItem(models.Model):
    class Result(models.TextChoices):
        CONFORMITY = 'CONFORMITY', 'Conformity'
        NONCONFORMITY = 'NONCONFORMITY', 'Nonconformity'
        OBSERVATION = 'OBSERVATION', 'Observation'
        OFI = 'OFI', 'Opportunity For Improvement'

    audit = models.ForeignKey(AuditPlan, on_delete=models.CASCADE, related_name='checklist_items')
    iso_clause = models.CharField(max_length=50, help_text="e.g. 7.1.5, 8.5.1, 9.2")
    question = models.TextField()
    requirement = models.TextField(blank=True)
    evidence = models.TextField(blank=True, help_text="Sampled records, documents, observations")
    result = models.CharField(max_length=30, choices=Result.choices, default=Result.CONFORMITY)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ['iso_clause', 'id']

    def __str__(self):
        return f"[{self.iso_clause}] {self.question[:60]} ({self.get_result_display()})"


class AuditFinding(models.Model):
    class FindingType(models.TextChoices):
        MAJOR_NC = 'MAJOR_NC', 'Major Nonconformity'
        MINOR_NC = 'MINOR_NC', 'Minor Nonconformity'
        OBSERVATION = 'OBSERVATION', 'Observation'
        OFI = 'OFI', 'Opportunity For Improvement'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        CLOSED = 'CLOSED', 'Closed'

    finding_number = models.CharField(max_length=50, unique=True, db_index=True)
    audit = models.ForeignKey(AuditPlan, on_delete=models.CASCADE, related_name='findings')
    finding_type = models.CharField(max_length=30, choices=FindingType.choices, default=FindingType.MINOR_NC)
    description = models.TextField()
    evidence = models.TextField()
    clause = models.CharField(max_length=50)
    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_audit_findings'
    )
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    linked_ncr = models.ForeignKey(
        'ncr.NCR',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_findings'
    )
    linked_action = models.ForeignKey(
        'actions.Action',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_findings'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['finding_number']

    def __str__(self):
        return f"{self.finding_number} - {self.get_finding_type_display()} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.finding_number:
            count = AuditFinding.objects.filter(audit=self.audit).count() + 1
            self.finding_number = f"FND-{self.audit.audit_number}-{count:02d}"
        super().save(*args, **kwargs)
