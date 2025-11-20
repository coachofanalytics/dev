# Celery import disabled for web dynos - only worker dyno needs it
# The web dyno was crashing because it tried to connect to Redis on startup
# from .celery import app as celery_app

# __all__ = ('celery_app',)
