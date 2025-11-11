# tests.py

from django.test import TestCase
from django.urls import reverse
from finance.models import OverBoughtSold

class OverBoughtSoldListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create sample data for OverBoughtSold model
        OverBoughtSold.objects.create(
            symbol="AAPL", 
            description="Apple Inc.",
            last=145.30,
            volume=1000000,
            RSI=72.5,
            EPS=3.45,
            PE=35.2,
            profit_margins=25.5
        )
        OverBoughtSold.objects.create(
            symbol="GOOGL",
            description="Google Inc.",
            last=2735.93,
            volume=500000,
            RSI=28.0,
            EPS=7.50,
            PE=36.5,
            profit_margins=30.0
        )

    def test_view_url_exists_at_desired_location(self):
        # Use reverse() to get the correct URL based on its name
        url = reverse('finance:overboughtsold_list')  # Use the app name to reverse the URL
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        url = reverse('finance:overboughtsold_list')  # Use the app name to reverse the URL
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'finance/overboughtsold_list.html')

    def test_pagination_is_correct(self):
        url = reverse('finance:overboughtsold_list')  # Use the app name to reverse the URL
        response = self.client.get(f"{url}?page=1")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AAPL")
        self.assertContains(response, "GOOGL")

    def test_no_stocks(self):
        # Delete all stocks to test the "no stocks available" message
        OverBoughtSold.objects.all().delete()
        url = reverse('finance:overboughtsold_list')  # Use the app name to reverse the URL
        response = self.client.get(url)
        self.assertContains(response, "No stocks available")
