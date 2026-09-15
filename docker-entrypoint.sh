#!/bin/sh
set -e

python - <<'PY'
import os
import time

import psycopg

connection_settings = {
    'dbname': os.environ.get('POSTGRES_DB', 'cmms'),
    'user': os.environ.get('POSTGRES_USER', 'cmms'),
    'password': os.environ.get('POSTGRES_PASSWORD', 'cmms'),
    'host': os.environ.get('POSTGRES_HOST', 'db'),
    'port': os.environ.get('POSTGRES_PORT', '5432'),
}

while True:
    try:
        with psycopg.connect(**connection_settings, connect_timeout=3):
            break
    except psycopg.OperationalError:
        time.sleep(1)
PY

python manage.py migrate --noinput

exec "$@"
