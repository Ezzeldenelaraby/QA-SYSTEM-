from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        QA_MANAGER = 'QA_MANAGER', 'QA Manager'
        QA_ENGINEER = 'QA_ENGINEER', 'QA Engineer'
        QC_INSPECTOR = 'QC_INSPECTOR', 'QC Inspector'
        PRODUCTION_MANAGER = 'PRODUCTION_MANAGER', 'Production Manager'
        DEPARTMENT_HEAD = 'DEPARTMENT_HEAD', 'Department Head'
        PROCESS_OWNER = 'PROCESS_OWNER', 'Process Owner'
        AUDITOR = 'AUDITOR', 'Auditor'
        EMPLOYEE = 'EMPLOYEE', 'Employee'
        MANAGEMENT_VIEWER = 'MANAGEMENT_VIEWER', 'Management Viewer'

    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members'
    )
    job_title = models.CharField(max_length=100, blank=True)
    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        db_index=True
    )
    phone = models.CharField(max_length=30, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    @property
    def full_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.username

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"

    @property
    def is_super_admin(self):
        return self.is_superuser or self.role == self.Role.SUPER_ADMIN

    @property
    def is_qa_manager(self):
        return self.is_super_admin or self.role == self.Role.QA_MANAGER

    @property
    def is_qa_staff(self):
        return self.is_super_admin or self.role in [self.Role.QA_MANAGER, self.Role.QA_ENGINEER]

    @property
    def is_qc_inspector(self):
        return self.is_super_admin or self.role in [self.Role.QC_INSPECTOR, self.Role.QA_ENGINEER, self.Role.QA_MANAGER]

    @property
    def is_auditor(self):
        return self.is_super_admin or self.role in [self.Role.AUDITOR, self.Role.QA_MANAGER, self.Role.QA_ENGINEER]

    @property
    def is_dept_head(self):
        return self.is_super_admin or self.role in [self.Role.DEPARTMENT_HEAD, self.Role.PRODUCTION_MANAGER, self.Role.QA_MANAGER]

    def can_approve_documents(self):
        return self.is_super_admin or self.role in [self.Role.QA_MANAGER, self.Role.DEPARTMENT_HEAD, self.Role.PRODUCTION_MANAGER]

    def can_close_ncr(self):
        return self.is_super_admin or self.role in [self.Role.QA_MANAGER, self.Role.QA_ENGINEER]

    def can_verify_capa(self):
        return self.is_super_admin or self.role in [self.Role.QA_MANAGER, self.Role.QA_ENGINEER, self.Role.AUDITOR]
