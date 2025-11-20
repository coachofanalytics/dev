web: gunicorn config.wsgi --log-file -
worker: celery -A config worker --loglevel=info
release: python manage.py migrate
