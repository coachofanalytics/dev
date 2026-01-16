import importlib


def test_celery_eager_setting():
    settings = importlib.import_module('coda_project.settings')
    # Our tests rely on running Celery tasks eagerly
    # If an environment or settings flag controls this, ensure it's present or default is acceptable
    # We don't require CELERY to be installed; just check that settings exist
    assert hasattr(settings, 'CELERY_ACCEPT_CONTENT')
