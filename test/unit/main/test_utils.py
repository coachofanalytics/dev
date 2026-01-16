import types
import pytest
from datetime import datetime


def test_countdown_in_month_returns_tuple():
    from main.utils import countdown_in_month
    res = countdown_in_month()
    assert isinstance(res, tuple)
    assert len(res) == 5
    days, seconds, minutes, hours, now = res
    assert isinstance(days, int)
    assert isinstance(seconds, float) or isinstance(seconds, int)
    assert isinstance(now, datetime)


def test_path_values_with_fake_request():
    class FakeRequest:
        def __init__(self, path, referer=None):
            self.path = path
            self.META = {}
            if referer:
                self.META['HTTP_REFERER'] = referer

    from main.utils import path_values
    r = FakeRequest('/a/b/c/', referer='http://example.com/x/y')
    path_vals, sub_title, pre_sub = path_values(r)
    assert sub_title == 'c'
    assert isinstance(path_vals, list)


def test_generate_chatbot_response_is_mocked(monkeypatch):
    # Mock openai.OpenAI and its chat return structure
    class DummyChoice:
        def __init__(self, text):
            self.message = types.SimpleNamespace(content=text)

    class DummyResp:
        def __init__(self, text):
            self.choices = [DummyChoice(text)]

    class DummyClient:
        def __init__(self, api_key=None):
            pass

        class chat:
            @staticmethod
            def completions():
                return None

    # Instead monkeypatch the openai.OpenAI to return object with chat.completions.create
    class ChatClient:
        def __init__(self, api_key=None):
            self.chat = types.SimpleNamespace()
            def create(**kwargs):
                return DummyResp('reply')
            self.chat.completions = types.SimpleNamespace(create=create)

    monkeypatch.setenv('OPENAI_API_KEY', 'x')
    monkeypatch.setattr('openai.OpenAI', ChatClient, raising=False)
    from main.utils import generate_chatbot_response
    out = generate_chatbot_response('hi')
    assert out == 'reply'
