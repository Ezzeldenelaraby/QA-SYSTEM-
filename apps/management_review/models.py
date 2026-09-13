from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimeStampedModel, SoftDeleteModel

class ManagementReviewMeeting(TimeStampedModel, SoftDeleteModel):
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        COMPLETED = 'COMPLETED', 'Completed'
        MINUTES_DRAFT = 'MINUTES_DRAFT', 'Minutes Draft'
        MINUTES_APPROVED = 'MINUTES_APPROVED', 'Minutes Approved'

    meeting_number = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    meeting_date = models.DateField(default=timezone.now)
    chairperson = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='chaired_reviews'
    )
    participants = models.TextField(help_text="Names/Titles of attendees present")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.SCHEDULED)
    general_summary = models.TextField(blank=True, help_text="Executive review overview and opening statement")

    # ISO 9001 Clause 9.3.2 Inputs
    inputs_previous_actions = models.TextField(blank=True, verbose_name="Status of actions from previous management reviews")
    inputs_audit_results = models.TextField(blank=True, verbose_name="Internal and external audit findings summary")
    inputs_customer_feedback = models.TextField(blank=True, verbose_name="Customer satisfaction & feedback")
    inputs_process_performance = models.TextField(blank=True, verbose_name="Process performance & conformity of products")
    inputs_quality_objectives = models.TextField(blank=True, verbose_name="Extent to which quality objectives have been met")
    inputs_ncr_capa_status = models.TextField(blank=True, verbose_name="Nonconformities and corrective actions status")
    inputs_supplier_performance = models.TextField(blank=True, verbose_name="Performance of external providers and suppliers")
    inputs_risks_opportunities = models.TextField(blank=True, verbose_name="Effectiveness of actions taken to address risks & opportunities")
    inputs_resource_needs = models.TextField(blank=True, verbose_name="Adequacy of resources")
    inputs_improvement_opportunities = models.TextField(blank=True, verbose_name="Opportunities for continual improvement")

    # ISO 9001 Clause 9.3.3 Outputs
    outputs_decisions = models.TextField(blank=True, verbose_name="Decisions related to opportunities for improvement")
    outputs_resource_requirements = models.TextField(blank=True, verbose_name="Resource needs decided")
    outputs_improvement_projects = models.TextField(blank=True, verbose_name="Quality management system change decisions")

    class Meta:
        ordering = ['-meeting_date', '-id']

    def __str__(self):
        return f"{self.meeting_number}: {self.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.meeting_number:
            self.meeting_number = self.generate_meeting_number()
        super().save(*args, **kwargs)

    @classmethod
    def generate_meeting_number(cls):
        year = timezone.now().year
        prefix = f"MR-{year}-"
        last = cls.all_objects.filter(meeting_number__startswith=prefix).order_by('meeting_number').last()
        if last:
            try:
                seq = int(last.meeting_number.split('-')[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"
