release: cd coda && python manage.py migrate --noinput
web: cd coda && gunicorn coda_project.wsgi:application --timeout 90 --graceful-timeout 90 --workers 2 --threads 2 --worker-tmp-dir /dev/shm --log-file -
worker: cd coda && celery -A coda.celeryapp worker -l info --concurrency=2
beat: cd coda && celery -A coda.celeryapp beat -l info