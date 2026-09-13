from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.departments.models import Department
from apps.core.models import SystemSetting

User = get_user_model()


class Command(BaseCommand):
    help = "Ensure default superuser and baseline settings exist on production startup."

    def handle(self, *args, **options):
        # 1. System Settings
        SystemSetting.get_settings()

        # 2. Default QA Department
        dept, _ = Department.objects.get_or_create(
            code="QA",
            defaults={"name": "Quality Assurance", "description": "Quality Management & Standards"}
        )

        # 3. Superuser
        if not User.objects.filter(is_superuser=True).exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@factory.local',
                password='Admin@123456',
                first_name='System',
                last_name='Administrator',
                role=User.Role.SUPER_ADMIN,
                department=dept
            )
            self.stdout.write(self.style.SUCCESS("Created production superuser 'admin' [password: Admin@123456]"))
        else:
            self.stdout.write("Superuser already present.")
