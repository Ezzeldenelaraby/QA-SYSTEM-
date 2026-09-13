from django.db import models
from django.conf import settings
from django.utils import timezone
from .middleware import get_current_user


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop('alive_only', True)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self.alive_only:
            return SoftDeleteQuerySet(self.model, using=self._db).alive()
        return SoftDeleteQuerySet(self.model, using=self._db)

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_updated'
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and user.is_authenticated and getattr(user, 'pk', None):
            try:
                from django.contrib.auth import get_user_model
                UserModel = get_user_model()
                # Verify that the user actually exists in the active database connection
                if UserModel.objects.filter(pk=user.pk).exists():
                    if not self.pk and not self.created_by:
                        self.created_by = user
                    self.updated_by = user
            except Exception:
                pass
        super().save(*args, **kwargs)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_deleted'
    )

    objects = SoftDeleteManager()
    all_objects = SoftDeleteManager(alive_only=False)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        user = get_current_user()
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user and user.is_authenticated:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('CLOSE', 'Close'),
        ('REOPEN', 'Reopen'),
        ('LOGIN', 'Login'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    module = models.CharField(max_length=50, db_index=True)
    record_id = models.CharField(max_length=100, db_index=True)
    record_name = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        username = self.user.username if self.user else 'System'
        return f"{self.timestamp:%Y-%m-%d %H:%M} - {username} - {self.action} on {self.module} #{self.record_id}"


class SystemSetting(models.Model):
    company_name = models.CharField(max_length=150, default="Apex Precision Engineering Ltd. (QMS Hub)")
    company_logo = models.ImageField(upload_to='settings/', null=True, blank=True)
    date_format = models.CharField(max_length=20, default="YYYY-MM-DD")
    ncr_prefix = models.CharField(max_length=10, default="NCR")
    capa_prefix = models.CharField(max_length=10, default="CAPA")
    action_prefix = models.CharField(max_length=10, default="ACT")
    audit_prefix = models.CharField(max_length=10, default="AUD")
    notification_days_before = models.PositiveIntegerField(default=7, help_text="Days before due date to send alert")
    calibration_alert_days = models.PositiveIntegerField(default=30, help_text="Days before calibration expiry to alert")
    risk_high_threshold = models.PositiveIntegerField(default=10)
    risk_critical_threshold = models.PositiveIntegerField(default=15)

    def __str__(self):
        return self.company_name

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj
