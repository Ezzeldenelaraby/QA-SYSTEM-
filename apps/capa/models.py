from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel, SoftDeleteModel

class CAPA(TimeStampedModel, SoftDeleteModel):
    class Source(models.TextChoices):
        NCR = 'NCR', 'Nonconformity Report (NCR)'
        AUDIT = 'AUDIT', 'Audit Finding'
        RISK = 'RISK', 'Risk Assessment'
        CUSTOMER = 'CUSTOMER', 'Customer Complaint'
        MANAGEMENT_REVIEW = 'MANAGEMENT_REVIEW', 'Management Review'
        RECURRENT_ISSUE = 'RECURRENT_ISSUE', 'Recurrent Process Deviation'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        ANALYSIS = 'ANALYSIS', 'Root Cause Analysis'
        IMPLEMENTATION = 'IMPLEMENTATION', 'Implementation'
        VERIFICATION = 'VERIFICATION', 'Verification'
        EFFECTIVENESS_CHECK = 'EFFECTIVENESS_CHECK', 'Effectiveness Check'
        CLOSED = 'CLOSED', 'Closed'

    capa_number = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    source = models.CharField(max_length=30, choices=Source.choices, default=Source.NCR)
    related_ncr = models.ForeignKey(
        'ncr.NCR',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='capas'
    )
    related_finding = models.ForeignKey(
        'audits.AuditFinding',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='capas'
    )
    related_risk = models.ForeignKey(
        'risks.Risk',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='capas'
    )
    description = models.TextField(help_text="Detailed problem description and background")
    root_cause = models.TextField(help_text="Underlying systemic root cause")
    corrective_action = models.TextField(help_text="Action to eliminate the cause of existing nonconformity")
    preventive_action = models.TextField(help_text="Action to eliminate causes of potential nonconformities across processes")
    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_capas'
    )
    start_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    verification_method = models.CharField(max_length=255, help_text="Method used to verify implementation & effectiveness")
    effectiveness_result = models.TextField(blank=True, help_text="Evidence and metrics proving non-recurrence")
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_capas'
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.OPEN, db_index=True)
    evidence = models.TextField(blank=True, help_text="Summary of supporting implementation evidence")
    evidence_file = models.FileField(upload_to='capa/evidence/%Y/%m/', null=True, blank=True)

    class Meta:
        ordering = ['-start_date', '-id']
        verbose_name = 'CAPA'
        verbose_name_plural = 'CAPAs'

    def __str__(self):
        return f"{self.capa_number}: {self.title} ({self.get_status_display()})"

    def clean(self):
        if self.status == self.Status.CLOSED:
            missing = []
            if not self.effectiveness_result:
                missing.append("Effectiveness Verification Result")
            if not self.verified_by:
                missing.append("Verified By (Sign-off)")
            if not self.completion_date:
                missing.append("Completion Date")
            if missing:
                raise ValidationError(f"Cannot close CAPA without required fields: {', '.join(missing)}.")

    def save(self, *args, **kwargs):
        if not self.capa_number:
            self.capa_number = self.generate_capa_number()
        if self.status == self.Status.CLOSED and not self.completion_date:
            self.completion_date = timezone.now().date()
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def generate_capa_number(cls):
        year = timezone.now().year
        prefix = f"CAPA-{year}-"
        last = cls.all_objects.filter(capa_number__startswith=prefix).order_by('capa_number').last()
        if last:
            try:
                seq = int(last.capa_number.split('-')[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"
