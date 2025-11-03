#!/usr/bin/env sh
set -e

echo "Aguardando Postgres..."
until nc -z -v -w5 db 5432; do sleep 2; done

python manage.py migrate --noinput || true
python manage.py collectstatic --noinput || true

exec uvicorn agent_hub.asgi:application --host 0.0.0.0 --port 1167 --reload
