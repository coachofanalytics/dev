from django.test import Client, TestCase
from django.urls import reverse, NoReverseMatch


class AdminLoginIntegrationTest(TestCase):
    def test_admin_login_page_resolves_or_is_skipped(self):
        try:
            url = reverse("admin:login")
        except NoReverseMatch:
            self.skipTest("Admin URLs not configured; skipping integration test.")
        client = Client()
        resp = client.get(url)
        self.assertIn(resp.status_code, (200, 302))
