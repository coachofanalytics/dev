from django.test import SimpleTestCase
from django.urls import reverse, resolve


class CrisisUrlsUnitTest(SimpleTestCase):
    def test_crisis_page_url_resolves(self):
        url = reverse("main:crisis_page")
        match = resolve(url)
        self.assertIsNotNone(match)

    def test_subscribe_alerts_url_resolves(self):
        url = reverse("main:subscribe_alerts")
        match = resolve(url)
        self.assertIsNotNone(match)

    def test_activate_helpline_url_resolves(self):
        url = reverse("main:activate_helpline")
        match = resolve(url)
        self.assertIsNotNone(match)

