from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from apps.core.models import TimeStampedModel, SoftDeleteModel, SystemSetting

class Equipment(TimeStampedModel, SoftDeleteModel):
    class Status(models.TextChoices):
        VALID = 'VALID', 'Valid (In Tolerance)'
        DUE_SOON = 'DUE_SOON', 'Calibration Due Soon'
        EXPIRED = 'EXPIRED', 'Calibration Expired'
        OUT_OF_SERVICE = 'OUT_OF_SERVICE', 'Out of Service'

    class Category(models.TextChoices):
        MICROMETER = 'MICROMETER', 'Micrometer'
        CALIPER = 'CALIPER', 'Vernier / Digital Caliper'
        DIAL_INDICATOR = 'DIAL_INDICATOR', 'Dial Indicator'
        PRESSURE_GAUGE = 'PRESSURE_GAUGE', 'Pressure Gauge'
        SCALE = 'SCALE', 'Weighing Scale'
        TEMPERATURE = 'TEMPERATURE', 'Temperature Sensor / Controller'
        MULTIMETER = 'MULTIMETER', 'Multimeter'
        TORQUE_WRENCH = 'TORQUE_WRENCH', 'Torque Wrench'
        CMM = 'CMM', 'Coordinate Measuring Machine (CMM)'
        OTHER = 'OTHER', 'Other Measuring Device'

    equipment_id = models.CharField(max_length=50, unique=True, db_index=True)
    equipment_name = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.CALIPER)
    manufacturer = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='equipment'
    )
    location = models.CharField(max_length=150, help_text="Workshop, Lab, Line A, Tool Crib, etc.")
    measurement_range = models.CharField(max_length=100, blank=True, help_text="e.g. 0 - 150 mm, 0 - 10 Bar")
    accuracy = models.CharField(max_length=100, blank=True, help_text="e.g. +/- 0.02 mm, Class 1.0")
    calibration_frequency_months = models.PositiveIntegerField(default=12, help_text="Calibration cycle in months")
    last_calibration_date = models.DateField(default=timezone.now)
    next_calibration_date = models.DateField(blank=True, null=True)
    calibration_provider = models.CharField(max_length=150, default="Internal Metrology Lab")
    certificate_file = models.FileField(upload_to='calibration/certificates/%Y/%m/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.VALID, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['next_calibration_date', 'equipment_id']
        verbose_name_plural = 'Equipment'

    def __str__(self):
        return f"{self.equipment_id} - {self.equipment_name} ({self.get_status_display()})"

    @property
    def days_until_due(self):
        if not self.next_calibration_date:
            return 0
        return (self.next_calibration_date - timezone.now().date()).days

    def update_status(self):
        if self.status == self.Status.OUT_OF_SERVICE:
            return
        
        try:
            alert_days = SystemSetting.get_settings().calibration_alert_days or 30
        except Exception:
            alert_days = 30

        today = timezone.now().date()
        if self.next_calibration_date:
            if self.next_calibration_date < today:
                self.status = self.Status.EXPIRED
            elif (self.next_calibration_date - today).days <= alert_days:
                self.status = self.Status.DUE_SOON
            else:
                self.status = self.Status.VALID

    def save(self, *args, **kwargs):
        if self.last_calibration_date and not self.next_calibration_date:
            self.next_calibration_date = self.last_calibration_date + relativedelta(months=self.calibration_frequency_months)
        self.update_status()
        super().save(*args, **kwargs)
