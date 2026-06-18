from time import perf_counter
from django.test import TestCase, Client
from django.urls import reverse
from django.test.utils import override_settings


@override_settings(STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
class CrisisPagePerformanceTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_crisis_page_renders_under_800ms(self):
        url = reverse("main:crisis_page")
        self.client.get(url)
        durations = []
        resp = None
        for _ in range(3):
            t0 = perf_counter()
            resp = self.client.get(url)
            durations.append(perf_counter() - t0)
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 200)
        self.assertLess(min(durations), 0.8)
