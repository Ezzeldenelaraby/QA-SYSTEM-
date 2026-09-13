from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimeStampedModel, SoftDeleteModel

class Inspection(TimeStampedModel, SoftDeleteModel):
    class Shift(models.TextChoices):
        MORNING = 'MORNING', 'Morning Shift (1st)'
        AFTERNOON = 'AFTERNOON', 'Afternoon Shift (2nd)'
        NIGHT = 'NIGHT', 'Night Shift (3rd)'

    class Result(models.TextChoices):
        OK = 'OK', 'Conforming (OK)'
        NG = 'NG', 'Nonconforming (NG)'
        PENDING = 'PENDING', 'Pending Inspection'

    inspection_number = models.CharField(max_length=50, unique=True, db_index=True)
    date = models.DateField(default=timezone.now)
    process = models.ForeignKey(
        'processes.Process',
        on_delete=models.PROTECT,
        related_name='inspections'
    )
    product = models.CharField(max_length=150)
    batch_lot = models.CharField(max_length=100)
    machine = models.CharField(max_length=100, help_text="Machine ID / Line number")
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='conducted_inspections'
    )
    shift = models.CharField(max_length=20, choices=Shift.choices, default=Shift.MORNING)
    overall_result = models.CharField(max_length=20, choices=Result.choices, default=Result.OK, db_index=True)
    comments = models.TextField(blank=True)
    linked_ncr = models.ForeignKey(
        'ncr.NCR',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inspections'
    )

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.inspection_number}: {self.product} ({self.get_overall_result_display()})"

    def save(self, *args, **kwargs):
        if not self.inspection_number:
            self.inspection_number = self.generate_inspection_number()
        super().save(*args, **kwargs)

    @classmethod
    def generate_inspection_number(cls):
        year = timezone.now().year
        prefix = f"INSP-{year}-"
        last = cls.all_objects.filter(inspection_number__startswith=prefix).order_by('inspection_number').last()
        if last:
            try:
                seq = int(last.inspection_number.split('-')[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"


class InspectionItem(models.Model):
    class ItemResult(models.TextChoices):
        OK = 'OK', 'OK'
        NG = 'NG', 'NG (No Good)'
        NA = 'NA', 'N/A'

    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='items')
    checkpoint_name = models.CharField(max_length=150, help_text="e.g. Outer Diameter, Surface Finish, Torque")
    specification = models.CharField(max_length=150, help_text="e.g. 50.00 +/- 0.02 mm, Ra <= 0.8")
    measured_value = models.CharField(max_length=100, help_text="Actual measured value or observed state")
    unit = models.CharField(max_length=30, blank=True)
    result = models.CharField(max_length=10, choices=ItemResult.choices, default=ItemResult.OK)
    comment = models.TextField(blank=True)
    photo = models.ImageField(upload_to='inspections/photos/%Y/%m/', null=True, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.checkpoint_name}: {self.measured_value} [{self.result}]"
