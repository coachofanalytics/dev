#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Unified local dev server
# Usage:
#   scripts/dev/dev_server.sh [--https] [--port 8000] [--settings local|clone]
# Defaults:
#   --port 8000
#   --settings clone (uses coda_project.coda_settings.local_prod_clone_settings)

HTTPS=false
PORT=8000
SETTINGS=clone

while [[ $# -gt 0 ]]; do
  case "$1" in
    --https) HTTPS=true; shift ;;
    --port) PORT="${2:-8000}"; shift 2 ;;
    --settings) SETTINGS="${2:-clone}"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--https] [--port 8000] [--settings local|clone]"; exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ "$SETTINGS" == "clone" ]]; then
  DJANGO_SETTINGS="coda_project.coda_settings.local_prod_clone_settings"
else
  DJANGO_SETTINGS="coda_project.coda_settings.local_settings"
fi

echo "=========================================="
echo "CODA Dev Server"
echo "HTTPS     : $HTTPS"
echo "PORT      : $PORT"
echo "SETTINGS  : $DJANGO_SETTINGS"
echo "=========================================="

cd "$(dirname "$0")/../.."/coda

if $HTTPS; then
  # Start HTTPS using Django's runserver_plus if available or fallback to runserver
  if python -c "import django_extensions" >/dev/null 2>&1; then
    python manage.py runserver_plus 0.0.0.0:$PORT --settings=$DJANGO_SETTINGS
  else
    echo "WARNING: django-extensions not installed; starting HTTP instead"
    python manage.py runserver 0.0.0.0:$PORT --settings=$DJANGO_SETTINGS
  fi
else
  python manage.py runserver 0.0.0.0:$PORT --settings=$DJANGO_SETTINGS
fi
