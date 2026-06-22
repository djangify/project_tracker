#!/bin/bash
set -e

cd /home/tracker

# Activate virtualenv
source /home/tracker/venv/bin/activate

# Django settings
export DJANGO_SETTINGS_MODULE=config.settings

# Start tracker gunicorn
exec gunicorn config.wsgi:application \
  --bind 127.0.0.1:8002 \
  --workers 2 \
  --timeout 60

