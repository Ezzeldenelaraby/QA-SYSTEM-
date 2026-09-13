from django.db import models
from django.conf import settings
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from apps.core.models import TimeStampedModel, SoftDeleteModel

class Course(TimeStampedModel, SoftDeleteModel):
    class CourseType(models.TextChoices):
        SOP = 'SOP', 'Standard Operating Procedure (SOP)'
        SAFETY = 'SAFETY', 'Safety & EHS'
        QUALITY = 'QUALITY', 'Quality Management & Standards'
        TECHNICAL = 'TECHNICAL', 'Technical & Machine Operation'
        ONBOARDING = 'ONBOARDING', 'General Onboarding'

    code = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=200)
    course_type = models.CharField(max_length=30, choices=CourseType.choices, default=CourseType.SOP)
    related_process = models.ForeignKey(
        'processes.Process',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )
    related_document = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )
    validity_months = models.PositiveIntegerField(default=12, help_text="Validity duration before retraining is needed")
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.title}"


class TrainingRecord(TimeStampedModel, SoftDeleteModel):
    class Result(models.TextChoices):
        PASS = 'PASS', 'Pass / Certified'
        FAIL = 'FAIL', 'Fail'
        ATTENDED = 'ATTENDED', 'Attended'

    class Competency(models.TextChoices):
        COMPETENT = 'COMPETENT', 'Competent'
        NEEDS_IMPROVEMENT = 'NEEDS_IMPROVEMENT', 'Needs Improvement'
        NOT_EVALUATED = 'NOT_EVALUATED', 'Not Evaluated'

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='training_records'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name='records'
    )
    trainer = models.CharField(max_length=150, help_text="Internal or external certified trainer")
    training_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)
    result = models.CharField(max_length=20, choices=Result.choices, default=Result.PASS)
    competency_status = models.CharField(max_length=30, choices=Competency.choices, default=Competency.COMPETENT)
    certificate_file = models.FileField(upload_to='training/certificates/%Y/%m/', null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-training_date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.course.code} ({self.get_competency_status_display()})"

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

    def save(self, *args, **kwargs):
        if self.training_date and not self.expiry_date and self.course.validity_months:
            self.expiry_date = self.training_date + relativedelta(months=self.course.validity_months)
        super().save(*args, **kwargs)
