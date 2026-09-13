from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimeStampedModel, SoftDeleteModel, SystemSetting

class Risk(TimeStampedModel, SoftDeleteModel):
    class RiskLevel(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        MITIGATING = 'MITIGATING', 'Mitigation In Progress'
        CONTROLLED = 'CONTROLLED', 'Controlled'
        CLOSED = 'CLOSED', 'Closed'

    risk_id = models.CharField(max_length=50, unique=True, db_index=True)
    process = models.ForeignKey(
        'processes.Process',
        on_delete=models.CASCADE,
        related_name='risks'
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        related_name='risks'
    )
    description = models.TextField(help_text="Detailed description of the risk event")
    cause = models.TextField(help_text="Root causes or vulnerability factors")
    potential_consequence = models.TextField(help_text="Impact on product quality, customer or compliance")
    existing_control = models.TextField(blank=True, help_text="Current preventive or detective controls")
    likelihood = models.IntegerField(
        choices=[(1, '1 - Very Rare'), (2, '2 - Rare'), (3, '3 - Moderate'), (4, '4 - Likely'), (5, '5 - Very Frequent')],
        default=3
    )
    severity = models.IntegerField(
        choices=[(1, '1 - Negligible'), (2, '2 - Minor'), (3, '3 - Moderate'), (4, '4 - Critical'), (5, '5 - Catastrophic')],
        default=3
    )
    risk_score = models.IntegerField(editable=False, default=9)
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, editable=False, default=RiskLevel.MEDIUM)
    action_required = models.BooleanField(default=True)
    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_risks'
    )
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    effectiveness = models.TextField(blank=True, help_text="Review of residual risk effectiveness")
    evidence = models.TextField(blank=True, help_text="Evidence of mitigation implementation")
    review_date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-risk_score', 'risk_id']

    def __str__(self):
        return f"{self.risk_id} ({self.get_risk_level_display()} - {self.risk_score}): {self.description[:40]}"

    def calculate_level(self, score):
        try:
            settings_obj = SystemSetting.get_settings()
            high_thresh = settings_obj.risk_high_threshold or 10
            crit_thresh = settings_obj.risk_critical_threshold or 15
        except Exception:
            high_thresh = 10
            crit_thresh = 15

        if score >= crit_thresh:
            return self.RiskLevel.CRITICAL
        elif score >= high_thresh:
            return self.RiskLevel.HIGH
        elif score >= 5:
            return self.RiskLevel.MEDIUM
        return self.RiskLevel.LOW

    def save(self, *args, **kwargs):
        self.risk_score = int(self.likelihood) * int(self.severity)
        self.risk_level = self.calculate_level(self.risk_score)
        if not self.risk_id:
            self.risk_id = self.generate_risk_id()
        super().save(*args, **kwargs)

    @classmethod
    def generate_risk_id(cls):
        year = timezone.now().year
        prefix = f"RSK-{year}-"
        last = cls.all_objects.filter(risk_id__startswith=prefix).order_by('risk_id').last()
        if last:
            try:
                seq = int(last.risk_id.split('-')[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"
