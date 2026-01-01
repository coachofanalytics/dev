from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from decimal import Decimal
from investments.models import InvestmentStrategy

class ViewIntegrationTests(TestCase):
    def setUp(self):
        """Set up client and common data."""
        self.client = Client()
        self.url = reverse('investments:InvestmentStrategy_list')

    def test_view_renders_database_record_details(self):
        """Integration: Verify DB data displays correctly in the HTML table."""
        InvestmentStrategy.objects.create(
            symbol="MSFT", action="CALL", expiry=date(2026, 1, 1), 
            day_to_expiry=1, earnings_date=date(2026, 1, 1), on_date=date.today(), 
            strike_price=Decimal("400.00"), mid_price=Decimal("5.00"), 
            ask_price=Decimal("5.10"), iv_rank=Decimal("30.00"), 
            stock_price=Decimal("405.00"), raw_return=Decimal("0.05"), 
            annualized_return=Decimal("0.50"), opening=Decimal("4.80"), 
            is_active=True
        )
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MSFT")
        self.assertContains(response, "Active")

    def test_multiple_records_integration(self):
        """Integration: Verify multiple records are counted and shown."""
        # Ensure there is NO extra space at the start of these lines
        InvestmentStrategy.objects.create(
            symbol="A", action="BUY", expiry=date(2026, 1, 1), day_to_expiry=10,
            earnings_date=date(2026, 1, 1), on_date=date.today(), strike_price=10,
            mid_price=1, ask_price=1.1, iv_rank=10, stock_price=11,
            raw_return=0.1, annualized_return=1.2, opening=0.9
        )
        InvestmentStrategy.objects.create(
            symbol="B", action="SELL", expiry=date(2026, 1, 1), day_to_expiry=20,
            earnings_date=date(2026, 1, 1), on_date=date.today(), strike_price=20,
            mid_price=2, ask_price=2.2, iv_rank=20, stock_price=22,
            raw_return=0.2, annualized_return=2.4, opening=1.8
        )
        
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['investments']), 2)