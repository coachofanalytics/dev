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


from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from investments.models import InvestmentStrategy

class CreateIntegrationTests(TestCase):

    def setUp(self):
        """Set up the test client and URLs."""
        self.client = Client()
        self.create_url = reverse('investments:InvestmentStrategy_create')
        self.list_url = reverse('investments:InvestmentStrategy_list')

    def test_create_to_list_flow_integration(self):
        """
        Integration: Test the full flow of creating a strategy 
        and seeing it appear on the dashboard.
        """
        strategy_data = {
            'symbol': 'NVDA',
            'action': 'PUT SELL',
            'expiry': '2026-05-20',
            'day_to_expiry': 45,
            'earnings_date': '2026-02-15',
            'on_date': str(date.today()),
            'strike_price': 110.00,
            'mid_price': 4.20,
            'ask_price': 4.30,
            'iv_rank': 45.5,
            'stock_price': 115.00,
            'raw_return': 0.04,
            'annualized_return': 0.35,
            'opening': 4.10,
            'comment': 'Integration test.',
            'is_active': True
        }

        # Submit and follow the redirect to the list page
        response = self.client.post(self.create_url, strategy_data, follow=True)

        # 1. Check if we ended up on the list page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "investments/investments_list.html")

        # 2. Check if the database has the record
        self.assertTrue(InvestmentStrategy.objects.filter(symbol='NVDA').exists())

        # 3. Verify the context data exists in the FINAL response
        # We check 'investments' because that is what the List View provides
        self.assertIn('investments', response.context)
        self.assertEqual(len(response.context['investments']), 1)
        self.assertContains(response, "NVDA")

    def test_view_renders_existing_records(self):
        """Integration: Ensure the list view displays pre-existing DB records."""
        InvestmentStrategy.objects.create(
            symbol="MSFT", action="CALL", expiry=date(2026,1,1), 
            day_to_expiry=1, earnings_date=date(2026,1,1), on_date=date.today(), 
            strike_price=400, mid_price=5, ask_price=5.1, iv_rank=30, 
            stock_price=405, raw_return=0.05, annualized_return=0.5, opening=4.8
        )
        
        response = self.client.get(self.list_url)
        self.assertEqual(len(response.context['investments']), 1)
        self.assertContains(response, "MSFT")