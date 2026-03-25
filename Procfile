release: python manage.py migrate
web: gunicorn coda_project.wsgi
worker: celery -A coda_project worker --loglevel=info
beat: celery -A coda_project beat --loglevel=info