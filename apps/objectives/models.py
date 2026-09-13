from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimeStampedModel, SoftDeleteModel

class QualityObjective(TimeStampedModel, SoftDeleteModel):
    class Status(models.TextChoices):
        ON_TRACK = 'ON_TRACK', 'On Track'
        AT_RISK = 'AT_RISK', 'At Risk'
        ACHIEVED = 'ACHIEVED', 'Achieved'
        NOT_ACHIEVED = 'NOT_ACHIEVED', 'Not Achieved'

    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='objectives'
    )
    process = models.ForeignKey(
        'processes.Process',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='objectives'
    )
    description = models.TextField()
    kpi = models.CharField(max_length=150, help_text="e.g. First Pass Yield (FPY), Scrap Rate, Customer Complaints")
    measurement_method = models.CharField(max_length=200, help_text="How this metric is computed / captured")
    baseline = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    target = models.DecimalField(max_digits=10, decimal_places=2)
    actual_result = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=30, default='%', help_text="%, PPM, Hours, Count, etc.")
    start_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='managed_objectives'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ON_TRACK, db_index=True)
    achievement_percentage = models.DecimalField(max_digits=6, decimal_places=2, default=0.0, editable=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['due_date', 'code']

    def __str__(self):
        return f"{self.code} - {self.name} ({self.actual_result or 0}/{self.target} {self.unit})"

    def calculate_achievement(self):
        if self.actual_result is not None and self.target:
            try:
                # If target >= baseline, higher is better
                if self.target >= self.baseline:
                    delta_target = float(self.target) - float(self.baseline)
                    if delta_target != 0:
                        pct = ((float(self.actual_result) - float(self.baseline)) / delta_target) * 100.0
                    else:
                        pct = (float(self.actual_result) / float(self.target)) * 100.0
                else:
                    # Lower is better (e.g. scrap reduction from 5% to 1%)
                    delta_target = float(self.baseline) - float(self.target)
                    if delta_target != 0:
                        pct = ((float(self.baseline) - float(self.actual_result)) / delta_target) * 100.0
                    else:
                        pct = 100.0
                return round(max(0.0, pct), 2)
            except Exception:
                return 0.0
        return 0.0

    def save(self, *args, **kwargs):
        self.achievement_percentage = self.calculate_achievement()
        super().save(*args, **kwargs)


class ObjectiveMeasurement(models.Model):
    objective = models.ForeignKey(QualityObjective, on_delete=models.CASCADE, related_name='measurements')
    period_date = models.DateField(help_text="Measurement period date (e.g. month end)")
    value = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['period_date']
        unique_together = ('objective', 'period_date')

    def __str__(self):
        return f"{self.objective.code} - {self.period_date}: {self.value}"
