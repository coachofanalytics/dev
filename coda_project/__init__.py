# ourvenv/cfehome/__init__.py
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
# from .celery import app as celery_app  # noqa
import os
os.environ["GOOGLE_API_KEY"] = "your-key"
os.environ["GOOGLE_CSE_ID"] = "your-search-engine-id"
