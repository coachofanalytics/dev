import os
import importlib.util
from pathlib import Path


def test_test_settings_secret_key_from_env(monkeypatch):
    # Ensure the test settings obtain SECRET_KEY from env when provided
    monkeypatch.setenv('TEST_SECRET_KEY', 'env-secret')
    spec = importlib.util.spec_from_file_location('test.test_settings',
                                                  Path(__file__).resolve().parents[3] / 'test_settings.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.SECRET_KEY == 'env-secret'


def test_password_hasher_not_md5():
    from test import test_settings
    for hasher in test_settings.PASSWORD_HASHERS:
        assert 'MD5' not in hasher.upper()


def test_debug_is_false():
    from test import test_settings
    assert test_settings.DEBUG is False
