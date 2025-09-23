web: gunicorn coda_project.wsgi:application --timeout 90 --graceful-timeout 90 --workers 2 --threads 2 --worker-tmp-dir /dev/shm --log-file -

# web: cd coda && PYTHONPATH=/app/coda:/app gunicorn coda_project.wsgi:application --timeout 90 --graceful-timeout 90 --workers 2 --threads 2 --worker-tmp-dir /dev/shm --log-file -