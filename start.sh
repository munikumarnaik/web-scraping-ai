#!/bin/bash
set -e

echo "==== Railway Deployment Start ===="
echo "PORT: $PORT"
echo "DATABASE_URL exists: $([ -n "$DATABASE_URL" ] && echo "YES" || echo "NO")"
echo "ALLOWED_HOSTS: $ALLOWED_HOSTS"
echo "DEBUG: $DEBUG"
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"

echo ""
echo "==== Collecting Static Files ===="
python manage.py collectstatic --no-input

echo ""
echo "==== Running Migrations ===="
python manage.py migrate --no-input

echo ""
echo "==== Testing Django Configuration ===="
python manage.py check --deploy

echo ""
echo "==== Testing WSGI Application ===="
python test_wsgi.py

echo ""
echo "==== Starting Gunicorn on port ${PORT:-8000} ===="
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level debug \
    --capture-output \
    --enable-stdio-inheritance
