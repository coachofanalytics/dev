from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from decimal import Decimal
from investments.models import InvestmentStrategy

class InvestmentStrategyViewTest(TestCase):

    def setUp(self):
        """Set up a test client and sample data."""
        self.client = Client()
        
        # Create sample data for the test database
        self.strategy = InvestmentStrategy.objects.create(
            symbol="AAPL",
            action="IRON CONDOR",
            expiry=date(2026, 2, 20),
            day_to_expiry=30,
            earnings_date=date(2026, 1, 15),
            on_date=date.today(),
            strike_price=Decimal("180.00"),
            mid_price=Decimal("2.50"),
            ask_price=Decimal("2.60"),
            iv_rank=Decimal("45.20"),
            stock_price=Decimal("185.00"),
            raw_return=Decimal("0.05"),
            annualized_return=Decimal("0.60"),
            opening=Decimal("2.45"),
            comment="Test strategy entry."
        )
        
        # This matches your app_name='investments' and path name='InvestmentStrategy_list'
        self.url = reverse('investments:InvestmentStrategy_list') 

    def test_list_view_status_code(self):
        """Verify the page loads successfully (HTTP 200)."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_list_view_template(self):
        """Verify the correct template is used."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "investments/investments_list.html")

    def test_list_view_context_data(self):
        """Verify the 'investments' key exists in context."""
        response = self.client.get(self.url)
        
        # FIXED: Changed 'Investment' to 'investments' to match your View's output
        self.assertIn('investments', response.context)
        self.assertEqual(len(response.context['investments']), 1)
        self.assertEqual(response.context['investments'][0].symbol, "AAPL")

    def test_list_view_content(self):
        """Verify that the symbol appears in the rendered HTML."""
        response = self.client.get(self.url)
        self.assertContains(response, "AAPL")