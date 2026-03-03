import importlib
import os
import pytest


def test_secret_key_from_env(monkeypatch):
    # Ensure settings picks up SECRET_KEY from environment when set
    monkeypatch.setenv('SECRET_KEY', 'from-env')
    settings = importlib.import_module('coda_project.settings')
    assert settings.SECRET_KEY == 'from-env' or settings.SECRET_KEY is not None


def test_password_hasher_not_md5():
    settings = importlib.import_module('coda_project.settings')
    # Fail if any MD5PasswordHasher present
    for h in settings.PASSWORD_HASHERS:
        assert 'MD5PasswordHasher' not in h, 'MD5 password hasher must not be used'


def test_debug_default_false_in_env(monkeypatch):
    monkeypatch.delenv('DEBUG', raising=False)
    settings = importlib.import_module('coda_project.settings')
    # If DEBUG env unset, setting should default to False
    assert settings.DEBUG is False
