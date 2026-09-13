import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

# Automatically apply database migrations and ensure default superuser on boot
try:
    from django.core.management import call_command
    call_command('migrate', interactive=False)
    call_command('ensure_superuser')
except Exception as e:
    print(f"[STARTUP NOTICE] Automated migration check: {e}")
