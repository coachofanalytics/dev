import pytest


def test_cron_registration_present():
    # Basic assertion that CRONJOBS is defined in settings
    from django.conf import settings
    assert hasattr(settings, 'CRONJOBS')
    assert isinstance(settings.CRONJOBS, list)
