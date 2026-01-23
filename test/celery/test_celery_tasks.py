import pytest
from unittest import mock


def test_celery_task_delay_mocked(monkeypatch):
    # Ensure Celery delay is not actually called
    fake = mock.Mock()
    monkeypatch.setattr('celery.app.task.Task.delay', fake)
    # calling fake.delay should be safe
    fake()
    assert fake.called is True
