from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel, SoftDeleteModel

class Process(TimeStampedModel, SoftDeleteModel):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        INACTIVE = 'INACTIVE', 'Inactive'

    code = models.CharField(max_length=30, unique=True, db_index=True)
    name = models.CharField(max_length=150)
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='processes'
    )
    process_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_processes'
    )
    description = models.TextField()
    inputs = models.TextField(blank=True, help_text="Inputs to the process (e.g. raw material, engineering drawings)")
    outputs = models.TextField(blank=True, help_text="Outputs from the process (e.g. machined parts, inspection certificates)")
    equipment = models.TextField(blank=True, help_text="Major equipment involved (e.g. 5-Axis CNC Mill)")
    tools = models.TextField(blank=True, help_text="Tools and fixtures required")
    parameters = models.TextField(blank=True, help_text="Critical process parameters (e.g. Feed rate, Spindle speed, Temperature)")
    inspection_points = models.TextField(blank=True, help_text="In-process and final inspection checkpoints")
    quality_gates = models.TextField(blank=True, help_text="Quality gates required before handoff")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    class Meta:
        ordering = ['code']
        verbose_name_plural = 'Processes'

    def __str__(self):
        return f"{self.code} - {self.name}"
