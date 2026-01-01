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
        # Check for your 'Active' logic in the template
        self.assertContains(response, "Active")

    def test_multiple_records_integration(self):
        """Integration: Verify multiple records are counted and shown."""
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


class CreateUpdateIntegrationTests(TestCase):
    def setUp(self):
        """Set up the test client and URLs."""
        self.client = Client()
        self.create_url = reverse('investments:InvestmentStrategy_create')
        self.list_url = reverse('investments:InvestmentStrategy_list')

    def test_create_to_list_flow_integration(self):
        """Integration: Test creating a strategy and seeing it on the dashboard."""
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
            'is_active': True
        }

        response = self.client.post(self.create_url, strategy_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "investments/investments_list.html")
        self.assertTrue(InvestmentStrategy.objects.filter(symbol='NVDA').exists())
        self.assertContains(response, "NVDA")

    def test_full_update_flow_integration(self):
        """Integration: Update a record and verify changes in the List view."""
        item = InvestmentStrategy.objects.create(
            symbol="OLD", action="BUY", strike_price=100, iv_rank=10, 
            day_to_expiry=1, expiry=date(2026, 1, 1), earnings_date=date(2026, 1, 1), 
            on_date=date.today(), mid_price=1.0, ask_price=1.1, 
            stock_price=105.0, raw_return=0.01, annualized_return=0.1, opening=0.9
        )
        
        update_url = reverse('investments:InvestmentStrategy_update', kwargs={'pk': item.pk})
        
        updated_data = {
            'symbol': 'NEW_TICKER',
            'action': 'SELL',
            'strike_price': 200,
            'iv_rank': 55,
            'day_to_expiry': 45,
            'expiry': '2026-06-01',
            'earnings_date': '2026-02-01',
            'on_date': str(date.today()),
            'mid_price': 5, 'ask_price': 6, 'stock_price': 205,
            'raw_return': 0.1, 'annualized_return': 1.2, 'opening': 4.5
        }

        response = self.client.post(update_url, updated_data, follow=True)
        self.assertRedirects(response, self.list_url)
        self.assertContains(response, "NEW_TICKER")
        self.assertEqual(InvestmentStrategy.objects.count(), 1)


class DeleteIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_list_to_delete_flow_integration(self):
        """Integration: Verify deletion flow works and clears DB."""
        # ADDED ALL REQUIRED FIELDS to prevent IntegrityError
        item = InvestmentStrategy.objects.create(
            symbol="INTEGRATE_DEL", action="PUT", strike_price=50, 
            iv_rank=5, day_to_expiry=1, expiry=date.today(),
            earnings_date=date.today(), on_date=date.today(),
            mid_price=1.0, ask_price=1.1, stock_price=55.0,
            raw_return=0.01, annualized_return=0.1, opening=0.9
        )
        
        list_url = reverse('investments:InvestmentStrategy_list')
        delete_url = reverse('investments:InvestmentStrategy_delete', kwargs={'pk': item.pk})

        # Confirm it exists
        response = self.client.get(list_url)
        self.assertContains(response, "INTEGRATE_DEL")

        # Perform deletion
        response = self.client.post(delete_url, follow=True)

        # Confirm it is gone
        self.assertTemplateUsed(response, "investments/investments_list.html")
        self.assertNotContains(response, "INTEGRATE_DEL")
        self.assertEqual(InvestmentStrategy.objects.count(), 0)