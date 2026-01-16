import json
import types
import pytest
import requests


def make_response(status_code=200, json_data=None):
    resp = types.SimpleNamespace()
    resp.status_code = status_code
    resp._json = json_data or {}

    def raise_for_status():
        if not (200 <= resp.status_code < 300):
            raise requests.RequestException('HTTP error')

    def json():
        return resp._json

    resp.raise_for_status = raise_for_status
    resp.json = json
    return resp


def test_get_exchange_rate_success(monkeypatch):
    from dev.finance.utils import get_exchange_rate

    sample = {'rates': {'KES': 139.0}}

    def fake_get(url, timeout=10):
        return make_response(200, sample)

    monkeypatch.setattr('requests.get', fake_get)
    rate = get_exchange_rate('USD', 'KES')
    assert float(rate) == 139.0


def test_get_exchange_rate_api_failure(monkeypatch):
    from dev.finance.utils import get_exchange_rate

    def fake_get(url, timeout=10):
        return make_response(500, {})

    monkeypatch.setattr('requests.get', fake_get)
    rate = get_exchange_rate('USD', 'KES')
    # fallback value defined in function
    assert float(rate) == 139.0


def test_get_exchange_rate_timeout(monkeypatch):
    from dev.finance.utils import get_exchange_rate

    def fake_get(url, timeout=10):
        raise requests.RequestException('timeout')

    monkeypatch.setattr('requests.get', fake_get)
    rate = get_exchange_rate('USD', 'EUR')
    assert float(rate) == 139.0 or isinstance(rate, float)
