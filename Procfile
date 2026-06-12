web: gunicorn coda_project.wsgi
worker: celery -A coda_project worker --beat --loglevel=DEBUG