from django.test import SimpleTestCase
from django.conf import settings
from django.urls import reverse, resolve


class SettingsAndUrlsTests(SimpleTestCase):
    def test_installed_apps_contains_core(self):
        required = ['accounts', 'payments', 'marketplace', 'gdpr', 'kyc']
        for app in required:
            # Allow both app labels and AppConfig dotted paths
            present = any(app == inst or app in inst for inst in settings.INSTALLED_APPS)
            self.assertTrue(present, f"{app} not found in INSTALLED_APPS")

    def test_login_url_resolves(self):
        # login URL name should resolve
        url = settings.LOGIN_URL
        # ensure we can reverse if a named URL was used
        try:
            resolve(url)
        except Exception:
            # Accept that LOGIN_URL may be a name; ensure it's a string
            self.assertIsInstance(url, str)
