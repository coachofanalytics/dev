release: python manage.py migrate auth --noinput && python manage.py migrate accounts --noinput && python manage.py migrate --noinput
web: gunicorn coda_project.wsgi
worker: celery -A coda_project worker --beat --loglevel=DEBUG