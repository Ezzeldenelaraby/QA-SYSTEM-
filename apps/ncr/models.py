from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel, SoftDeleteModel

class NCR(TimeStampedModel, SoftDeleteModel):
    class Source(models.TextChoices):
        INTERNAL_AUDIT = 'INTERNAL_AUDIT', 'Internal Audit'
        EXTERNAL_AUDIT = 'EXTERNAL_AUDIT', 'External Audit'
        INSPECTION = 'INSPECTION', 'Shop Floor Inspection'
        PRODUCTION = 'PRODUCTION', 'Production Routine'
        CUSTOMER_COMPLAINT = 'CUSTOMER_COMPLAINT', 'Customer Complaint'
        SUPPLIER = 'SUPPLIER', 'Supplier / Incoming'
        MANAGEMENT_REVIEW = 'MANAGEMENT_REVIEW', 'Management Review'
        OTHER = 'OTHER', 'Other'

    class Classification(models.TextChoices):
        MINOR = 'MINOR', 'Minor'
        MAJOR = 'MAJOR', 'Major'
        CRITICAL = 'CRITICAL', 'Critical'

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        CONTAINMENT = 'CONTAINMENT', 'Containment'
        ROOT_CAUSE_ANALYSIS = 'RCA', 'Root Cause Analysis'
        CORRECTIVE_ACTION = 'CORRECTIVE_ACTION', 'Corrective Action'
        VERIFICATION = 'VERIFICATION', 'Verification'
        CLOSED = 'CLOSED', 'Closed'

    ncr_number = models.CharField(max_length=50, unique=True, db_index=True)
    date = models.DateField(default=timezone.now)
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='ncrs'
    )
    process = models.ForeignKey(
        'processes.Process',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ncrs'
    )
    product = models.CharField(max_length=150, help_text="Part name or product description")
    batch_lot = models.CharField(max_length=100, help_text="Batch or Lot Number")
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reported_ncrs'
    )
    source = models.CharField(max_length=30, choices=Source.choices, default=Source.PRODUCTION)
    description = models.TextField(help_text="Clear description of the nonconformity")
    requirement = models.TextField(help_text="Standard, drawing tolerance, or procedure requirement violated")
    evidence = models.TextField(blank=True, help_text="Evidence observed or measured data")
    evidence_file = models.FileField(upload_to='ncr/evidence/%Y/%m/', null=True, blank=True)
    classification = models.CharField(max_length=20, choices=Classification.choices, default=Classification.MINOR)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    
    immediate_correction = models.TextField(blank=True, help_text="Immediate fix applied to affected parts (quarantine, rework, scrap)")
    containment_action = models.TextField(blank=True, help_text="Action to prevent affected material from escaping to customer or downstream")
    root_cause_summary = models.TextField(blank=True, help_text="Final root cause conclusion")
    
    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_ncrs'
    )
    due_date = models.DateField()
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.OPEN, db_index=True)
    
    verification_notes = models.TextField(blank=True, help_text="QA sign-off and verification results")
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_ncrs'
    )
    closed_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = 'Nonconformity Report'
        verbose_name_plural = 'Nonconformity Reports'

    def __str__(self):
        return f"{self.ncr_number} - {self.product} ({self.get_status_display()})"

    def clean(self):
        # Prevent closure if mandatory validation fields are missing
        if self.status == self.Status.CLOSED:
            missing = []
            if not self.immediate_correction:
                missing.append("Immediate Correction")
            if not self.containment_action:
                missing.append("Containment Action")
            if not self.root_cause_summary:
                missing.append("Root Cause Summary")
            if not self.verification_notes:
                missing.append("Verification Notes")
            if not self.verified_by:
                missing.append("Verified By (QA sign-off)")
            if missing:
                raise ValidationError(f"Cannot close NCR without completing required fields: {', '.join(missing)}.")

    def save(self, *args, **kwargs):
        if not self.ncr_number:
            self.ncr_number = self.generate_ncr_number()
        if self.status == self.Status.CLOSED and not self.closed_date:
            self.closed_date = timezone.now().date()
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def generate_ncr_number(cls):
        year = timezone.now().year
        prefix = f"NCR-{year}-"
        last = cls.all_objects.filter(ncr_number__startswith=prefix).order_by('ncr_number').last()
        if last:
            try:
                seq = int(last.ncr_number.split('-')[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"


class FiveWhysAnalysis(models.Model):
    ncr = models.OneToOneField(NCR, on_delete=models.CASCADE, related_name='five_whys')
    problem_statement = models.TextField()
    why_1 = models.TextField(blank=True, verbose_name="1. Why did the issue occur?")
    why_2 = models.TextField(blank=True, verbose_name="2. Why?")
    why_3 = models.TextField(blank=True, verbose_name="3. Why?")
    why_4 = models.TextField(blank=True, verbose_name="4. Why?")
    why_5 = models.TextField(blank=True, verbose_name="5. Why? (Root Cause)")
    root_cause_conclusion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"5-Whys for {self.ncr.ncr_number}"


class FishboneCause(models.Model):
    class Category(models.TextChoices):
        MAN = 'MAN', 'Man (People / Operator)'
        MACHINE = 'MACHINE', 'Machine (Equipment / Tooling)'
        METHOD = 'METHOD', 'Method (Procedures / Process)'
        MATERIAL = 'MATERIAL', 'Material (Raw Material / Parts)'
        MEASUREMENT = 'MEASUREMENT', 'Measurement (Inspection / Gage)'
        ENVIRONMENT = 'ENVIRONMENT', 'Environment (Workplace / Temperature)'

    ncr = models.ForeignKey(NCR, on_delete=models.CASCADE, related_name='fishbone_causes')
    category = models.CharField(max_length=20, choices=Category.choices)
    cause_description = models.CharField(max_length=255)
    is_primary = models.BooleanField(default=False, help_text="Is this confirmed as a key root cause?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', '-is_primary', 'id']

    def __str__(self):
        return f"{self.get_category_display()}: {self.cause_description}"
