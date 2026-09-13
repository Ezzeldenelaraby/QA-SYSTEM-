from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimeStampedModel, SoftDeleteModel

class Action(TimeStampedModel, SoftDeleteModel):
    class SourceType(models.TextChoices):
        GENERIC = 'GENERIC', 'Generic Action'
        NCR = 'NCR', 'Nonconformity Report (NCR)'
        CAPA = 'CAPA', 'CAPA'
        AUDIT = 'AUDIT', 'Internal Audit Finding'
        RISK = 'RISK', 'Risk Mitigation'
        MANAGEMENT_REVIEW = 'MANAGEMENT_REVIEW', 'Management Review'
        INSPECTION = 'INSPECTION', 'Inspection'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        PENDING_VERIFICATION = 'PENDING_VERIFICATION', 'Pending Verification'
        COMPLETED = 'COMPLETED', 'Completed'
        OVERDUE = 'OVERDUE', 'Overdue'
        CANCELLED = 'CANCELLED', 'Cancelled'

    action_number = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    source_type = models.CharField(max_length=30, choices=SourceType.choices, default=SourceType.GENERIC)
    source_id = models.CharField(max_length=100, blank=True, help_text="Reference ID of the originating record")
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actions'
    )
    process = models.ForeignKey(
        'processes.Process',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actions'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_actions'
    )
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    start_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.OPEN, db_index=True)
    evidence = models.TextField(blank=True, help_text="Action implementation evidence and summary")
    evidence_file = models.FileField(upload_to='actions/evidence/%Y/%m/', null=True, blank=True)
    verification = models.TextField(blank=True, help_text="QA / Supervisor verification notes")
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_actions'
    )

    class Meta:
        ordering = ['due_date', '-priority']

    def __str__(self):
        return f"{self.action_number}: {self.title}"

    @property
    def is_overdue(self):
        if self.status in [self.Status.COMPLETED, self.Status.CANCELLED]:
            return False
        return self.due_date < timezone.now().date()

    def update_overdue_status(self):
        """Update status to OVERDUE if deadline has passed."""
        if self.is_overdue and self.status not in [self.Status.COMPLETED, self.Status.CANCELLED]:
            self.status = self.Status.OVERDUE
            self.save(update_fields=['status'])

    def save(self, *args, **kwargs):
        if not self.action_number:
            self.action_number = self.generate_action_number()
        super().save(*args, **kwargs)

    @classmethod
    def generate_action_number(cls):
        year = timezone.now().year
        prefix = f"ACT-{year}-"
        last = cls.all_objects.filter(action_number__startswith=prefix).order_by('action_number').last()
        if last:
            try:
                seq = int(last.action_number.split('-')[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"
