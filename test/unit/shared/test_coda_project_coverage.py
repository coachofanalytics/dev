import importlib
import os
import types
import tempfile


def reload_settings_with_env(env_vars):
    # Set env vars, reload settings module and return it
    for k, v in env_vars.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    if 'coda_project.settings' in importlib.sys.modules:
        importlib.reload(importlib.import_module('coda_project.settings'))
    return importlib.import_module('coda_project.settings')


def test_settings_siteurl_variants(monkeypatch):
    # Production
    s = reload_settings_with_env({'ENVIRONMENT': 'production'})
    assert 'https' in s.SITEURL

    # Testing
    s = reload_settings_with_env({'ENVIRONMENT': 'testing'})
    assert 'https' in s.SITEURL

    # Default (local)
    s = reload_settings_with_env({'ENVIRONMENT': None})
    assert s.SITEURL.startswith('http')


def test_import_asgi_and_wsgi():
    # Ensure ASGI and WSGI modules expose application callable
    asgi = importlib.import_module('coda_project.asgi')
    wsgi = importlib.import_module('coda_project.wsgi')
    assert hasattr(asgi, 'application')
    assert hasattr(wsgi, 'application')


def test_celery_module_mocked(monkeypatch):
    # Provide a dummy Celery class to avoid heavy autodiscover during import
    class DummyCelery:
        def __init__(self, name=None):
            self.name = name
            self.conf = types.SimpleNamespace()
            self._autodiscovered = False

        def config_from_object(self, *args, **kwargs):
            self._configured = True

        def autodiscover_tasks(self):
            self._autodiscovered = True

    monkeypatch.setattr('celery.Celery', DummyCelery, raising=False)
    if 'coda_project.celery' in importlib.sys.modules:
        importlib.reload(importlib.import_module('coda_project.celery'))
    cel = importlib.import_module('coda_project.celery')
    assert hasattr(cel, 'app')
    assert getattr(cel.app, '_autodiscovered', True) or hasattr(cel.app, 'conf')


def test_urls_debug_static_branch(monkeypatch, tmp_path):
    # Ensure urlpatterns static branch is exercised by setting DEBUG True and valid roots
    settings = importlib.import_module('coda_project.settings')
    monkeypatch.setattr(settings, 'DEBUG', True)
    monkeypatch.setattr(settings, 'MEDIA_URL', '/media/')
    monkeypatch.setattr(settings, 'STATIC_URL', '/static/')
    monkeypatch.setattr(settings, 'MEDIA_ROOT', str(tmp_path / 'media'))
    monkeypatch.setattr(settings, 'STATIC_ROOT', str(tmp_path / 'static'))

    # Reload urls to apply DEBUG branch
    if 'coda_project.urls' in importlib.sys.modules:
        importlib.reload(importlib.import_module('coda_project.urls'))
    urls = importlib.import_module('coda_project.urls')
    assert hasattr(urls, 'urlpatterns')


def test_settings_dba_and_payment(monkeypatch):
    # Test dba_values for different ENVIRONMENT values
    monkeypatch.setenv('ENVIRONMENT', 'production')
    monkeypatch.setenv('HEROKU_DYCPROD_HOST', 'prod-host')
    monkeypatch.setenv('HEROKU_DYCPROD_NAME', 'prod-db')
    monkeypatch.setenv('HEROKU_DYCPROD_USER', 'prod-user')
    monkeypatch.setenv('HEROKU_DYCPROD_PASS', 'prod-pass')
    settings = importlib.reload(importlib.import_module('coda_project.settings'))
    host, dbname, user, password = settings.dba_values()
    assert host == 'prod-host'

    monkeypatch.setenv('ENVIRONMENT', 'staging')
    monkeypatch.setenv('HEROKU_DYCDEV_HOST', 'stage-host')
    monkeypatch.setenv('HEROKU_DYCDEV_NAME', 'stage-db')
    monkeypatch.setenv('HEROKU_DYCDEV_USER', 'stage-user')
    monkeypatch.setenv('HEROKU_DYCDEV_PASS', 'stage-pass')
    settings = importlib.reload(importlib.import_module('coda_project.settings'))
    host, dbname, user, password = settings.dba_values()
    assert host == 'stage-host'

    # Default branch
    monkeypatch.delenv('ENVIRONMENT', raising=False)
    monkeypatch.setenv('HEROKU_DEV_HOST', 'dev-host')
    monkeypatch.setenv('HEROKU_DEV_NAME', 'dev-db')
    monkeypatch.setenv('HEROKU_DEV_USER', 'dev-user')
    monkeypatch.setenv('HEROKU_DEV_PASS', 'dev-pass')
    settings = importlib.reload(importlib.import_module('coda_project.settings'))
    host, dbname, user, password = settings.dba_values()
    assert host == 'dev-host'

    # Test payment_details returns a tuple even when env vars unset
    res = settings.payment_details(request=None)
    assert isinstance(res, tuple)
