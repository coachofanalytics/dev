from django.test import TestCase
from django.urls import reverse
from finance.models import OverBoughtSold

class OverBoughtSoldTemplateRegressionTests(TestCase):
    def setUp(self):
        self.url = reverse("finance:overboughtsold_list")

    def test_header_and_columns_render(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, "📊 OverBoughtSold Records")
        for col in ["Symbol", "Description", "Last", "Volume", "RSI", "EPS", "PE", "Rank", "Profit Margins", "Created At"]:
            self.assertIn(col, resp.content.decode())

    def test_row_markup_for_record(self):
        OverBoughtSold.objects.create(symbol="NVDA", description="NVIDIA")
        resp = self.client.get(self.url)
        self.assertContains(resp, "<td", html=False)  # at least one cell exists
        self.assertContains(resp, "NVDA")
        self.assertContains(resp, "NVIDIA")

    def test_empty_block_text(self):
        OverBoughtSold.objects.all().delete()
        resp = self.client.get(self.url)
        self.assertContains(resp, "No stocks available")
