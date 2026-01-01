from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from decimal import Decimal
from investments.models import InvestmentStrategy

class InvestmentStrategyViewTest(TestCase):
    def setUp(self):
        """Set up a test client and sample data for List View."""
        self.client = Client()
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
        self.url = reverse('investments:InvestmentStrategy_list') 

    def test_list_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_list_view_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "investments/investments_list.html")

    def test_list_view_context_data(self):
        response = self.client.get(self.url)
        self.assertIn('investments', response.context)
        self.assertEqual(len(response.context['investments']), 1)
        self.assertEqual(response.context['investments'][0].symbol, "AAPL")
def test_create_view_post_success(self):
        """Verify that a valid POST request saves a record and redirects."""
        data = {
            'symbol': 'TSLA',
            'action': 'IRON CONDOR',
            'expiry': '2026-06-01',
            'day_to_expiry': 45,
            'earnings_date': '2026-04-15',
            'on_date': str(date.today()),
            'strike_price': '180.00',    # Changed to string for form submission
            'mid_price': '5.50',         # Added/Ensured strings for decimals
            'ask_price': '5.60',
            'iv_rank': '65.0',
            'stock_price': '175.00',
            'raw_return': '0.08',
            'annualized_return': '0.75',
            'opening': '5.40',
            'comment': 'High IV rank strategy',
            'is_active': True
        }
        # We use follow=True to see where it goes if it succeeds
        response = self.client.post(self.create_url, data)
        
        # If this still fails, print the errors to see exactly what is wrong:
        if response.status_code == 200:
            print(response.context['form'].errors)
            
        self.assertRedirects(response, self.list_url)
        self.assertEqual(InvestmentStrategy.objects.filter(symbol='TSLA').count(), 1)

class InvestmentStrategyUpdateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.strategy = InvestmentStrategy.objects.create(
            symbol="AAPL", action="BUY", expiry=date(2026,1,1), day_to_expiry=30,
            earnings_date=date(2026,1,1), on_date=date.today(), strike_price=150,
            mid_price=2.0, ask_price=2.1, iv_rank=40, stock_price=155,
            raw_return=0.05, annualized_return=0.5, opening=1.9
        )
        self.url = reverse('investments:InvestmentStrategy_update', kwargs={'pk': self.strategy.pk})

    def test_update_view_status_and_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "investments/investment_update.html")
        self.assertEqual(response.context['form'].instance.pk, self.strategy.pk)

class InvestmentStrategyDeleteViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        # FIXED: Fields like mid_price are included to prevent IntegrityError
        self.strategy = InvestmentStrategy.objects.create(
            symbol="DEL_ME", action="SELL", strike_price=100, 
            iv_rank=10, day_to_expiry=1, expiry=date.today(),
            earnings_date=date.today(), on_date=date.today(),
            mid_price=1.0, ask_price=1.1, stock_price=100,
            raw_return=0.0, annualized_return=0.0, opening=1.0
        )
        self.url = reverse('investments:InvestmentStrategy_delete', kwargs={'pk': self.strategy.pk})

    def test_delete_view_post_request(self):
        """Verify that a POST request actually deletes the object."""
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('investments:InvestmentStrategy_list'))
        self.assertEqual(InvestmentStrategy.objects.filter(pk=self.strategy.pk).count(), 0)