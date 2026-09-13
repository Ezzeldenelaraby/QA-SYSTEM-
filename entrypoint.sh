#!/bin/sh
set -e

echo "=== [QMS HUB CONTAINER INITIALIZATION] ==="

echo "-> Applying database migrations..."
python manage.py migrate --noinput

echo "-> Ensuring production superuser..."
python manage.py ensure_superuser

echo "-> Starting Gunicorn WSGI application server..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
