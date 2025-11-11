from django.test import TestCase
from django.urls import reverse
from finance.models import OverBoughtSold


class OverBoughtSoldViewIntegrationTests(TestCase):
    def setUp(self):
        self.url = reverse("finance:overboughtsold_list")

    def test_list_renders_items(self):
        OverBoughtSold.objects.create(symbol="OLD")
        OverBoughtSold.objects.create(symbol="NEW")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "OLD")
        self.assertContains(resp, "NEW")

    def test_empty_state_message(self):
        OverBoughtSold.objects.all().delete()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No stocks available")
