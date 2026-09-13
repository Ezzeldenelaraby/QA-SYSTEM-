#!/bin/sh
set -e

echo "=== [QMS HUB CONTAINER INITIALIZATION] ==="

# Run database migrations
echo "-> Applying database migrations..."
python manage.py migrate --noinput

# Collect static files for WhiteNoise
echo "-> Collecting static assets..."
python manage.py collectstatic --noinput

# Start Gunicorn WSGI server
echo "-> Starting high-performance Gunicorn WSGI application server..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${GUNICORN_WORKERS:-3} \
    --threads ${GUNICORN_THREADS:-2} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
