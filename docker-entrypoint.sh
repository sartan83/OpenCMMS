#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    until python manage.py check --database default >/dev/null 2>&1; do
        sleep 1
    done
    python manage.py migrate --noinput
fi

exec "$@"
