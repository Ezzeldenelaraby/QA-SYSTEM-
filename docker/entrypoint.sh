#!/bin/sh

echo "=== [QMS HUB PRODUCTION INITIALIZATION] ==="

echo "-> Running database migrations..."
python manage.py migrate --noinput || echo "[WARNING] Migrate encountered an error, continuing..."

echo "-> Ensuring default superuser..."
python manage.py ensure_superuser || echo "[WARNING] Ensure superuser encountered an error, continuing..."

echo "-> Collecting static assets..."
python manage.py collectstatic --noinput || echo "[WARNING] Collectstatic encountered an error, continuing..."

echo "-> Starting Gunicorn WSGI server on port ${PORT:-8000}..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
