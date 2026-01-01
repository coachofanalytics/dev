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




from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from investments.models import InvestmentStrategy

class InvestmentStrategyCreateViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.create_url = reverse('investments:InvestmentStrategy_create')
        self.list_url = reverse('investments:InvestmentStrategy_list')

    def test_create_view_get_request(self):
        """Verify the create page loads with a blank form."""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        # Matches your view: render(request, "investments/investments_create.html", ...)
        self.assertTemplateUsed(response, "investments/investments_create.html")
        self.assertIn('form', response.context)

    def test_create_view_post_success(self):
        """Verify that a valid POST request saves a record and redirects."""
        data = {
            'symbol': 'TSLA',
            'action': 'IRON CONDOR',
            'expiry': '2026-06-01',
            'day_to_expiry': 45,
            'earnings_date': '2026-04-15',
            'on_date': str(date.today()),
            'strike_price': 180.00,
            'mid_price': 5.50,
            'ask_price': 5.60,
            'iv_rank': 65.0,
            'stock_price': 175.00,
            'raw_return': 0.08,
            'annualized_return': 0.75,
            'opening': 5.40,
            'comment': 'High IV rank strategy',
            'is_active': True
        }
        response = self.client.post(self.create_url, data)
        self.assertRedirects(response, self.list_url)
        self.assertEqual(InvestmentStrategy.objects.filter(symbol='TSLA').count(), 1)