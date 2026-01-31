#!/bin/bash
set -e

echo "=========================================="
echo "eBuilder Docker Entrypoint"
echo "=========================================="

INIT_MARKER="/app/db/.initialized"

if [ ! -f "$INIT_MARKER" ]; then
    echo "First boot detected"

    python manage.py migrate --noinput
    # Configure Django Sites framework with customer domain
    python -c "
import django; django.setup()
from django.contrib.sites.models import Site
import os
Site.objects.update_or_create(
    id=1,
    defaults={
        'domain': os.environ.get('SHOP_DOMAIN', 'localhost'),
        'name': os.environ.get('SITE_NAME', 'My Shop')
    }
)
print(f\"Site configured: {os.environ.get('SHOP_DOMAIN', 'localhost')}\")"


    if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
        python manage.py create_admin_from_env
    fi

    python manage.py create_demo_product
    python manage.py create_default_policies
    python manage.py collectstatic --noinput

    echo "$(date -Iseconds)" > "$INIT_MARKER"
else
    python manage.py migrate --noinput
fi

# ALWAYS ensure static files are present
python manage.py collectstatic --noinput

exec gunicorn ebuilder.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3
