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










from investments.models import Daily_Trades

from django.test import TestCase
from django.urls import reverse
from decimal import Decimal
from datetime import date

from investments.models import Daily_Trades


class DailyTradesListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Create test data once for all tests
        """
        Daily_Trades.objects.create(
            symbol="AAPL",
            transaction="VIEW-AAPL-001",
            price=Decimal("180.0000"),
            strike_price=Decimal("0.0000"),
            action="BTO",
            qty=10,
            date=date.today(),
            account_type="CASH",
            credit=Decimal("0.0000"),
            debit=Decimal("1800.0000"),
        )

        Daily_Trades.objects.create(
            symbol="TSLA",
            transaction="VIEW-TSLA-002",
            price=Decimal("6.5000"),
            strike_price=Decimal("250.0000"),
            action="STO",
            qty=1,
            date=date.today(),
            expiry=date(2025, 2, 21),
            account_type="MARGIN",
            credit=Decimal("650.0000"),
            debit=Decimal("0.0000"),
        )

    def test_daily_trades_list_url_exists(self):
        """
        URL responds with HTTP 200
        """
        response = self.client.get(
            reverse("investments:daily_trades_list")
        )
        self.assertEqual(response.status_code, 200)

    def test_daily_trades_list_uses_correct_template(self):
        """
        Correct template is used
        """
        response = self.client.get(
            reverse("investments:daily_trades_list")
        )
        self.assertTemplateUsed(response, "investments/trade_list.html")

    def test_all_trades_are_displayed(self):
        """
        All trades appear in context
        """
        response = self.client.get(
            reverse("investments:daily_trades_list")
        )
        trades = response.context["trades"]

        self.assertEqual(trades.paginator.count, 2)
        self.assertContains(response, "AAPL")
        self.assertContains(response, "TSLA")

    def test_filter_by_symbol(self):
        """
        Symbol filter works
        """
        response = self.client.get(
            reverse("investments:daily_trades_list"),
            {"symbol": "AAPL"}
        )

        trades = response.context["trades"]

        self.assertEqual(trades.paginator.count, 1)
        self.assertContains(response, "AAPL")
        self.assertNotContains(response, "TSLA")

    def test_filter_by_action(self):
        """
        Action filter works
        """
        response = self.client.get(
            reverse("investments:daily_trades_list"),
            {"action": "STO"}
        )

        trades = response.context["trades"]

        self.assertEqual(trades.paginator.count, 1)
        self.assertContains(response, "TSLA")

    def test_date_range_filter(self):
        """
        Date filters work
        """
        response = self.client.get(
            reverse("investments:daily_trades_list"),
            {"start": date.today(), "end": date.today()}
        )

        self.assertEqual(
            response.context["trades"].paginator.count,
            2
        )

    def test_totals_are_calculated_correctly(self):
        """
        Totals are computed on filtered queryset
        """
        response = self.client.get(
            reverse("investments:daily_trades_list")
        )

        self.assertEqual(
            response.context["total_credit"],
            Decimal("650.0000")
        )
        self.assertEqual(
            response.context["total_debit"],
            Decimal("1800.0000")
        )
        self.assertEqual(
            response.context["total_net"],
            Decimal("-1150.0000")
        )

    def test_pagination_is_enabled(self):
        """
        Pagination exists and returns Page object
        """
        response = self.client.get(
            reverse("investments:daily_trades_list")
        )
        trades = response.context["trades"]

        self.assertTrue(hasattr(trades, "paginator"))
        self.assertTrue(hasattr(trades, "number"))










from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.urls import reverse

from investments.models import Daily_Trades


class DailyTradesCreateViewTest(TestCase):

    def setUp(self):
        self.url = reverse("investments:daily_trades_create")

        self.valid_payload = {
            "symbol": "AAPL",
            "transaction": "CRT-AAPL-001",
            "price": "180.0000",
            "strike_price": "0.0000",
            "action": "BTO",
            "qty": 10,
            "date": date.today(),
            "account_type": "CASH",
            "credit": "0.0000",
            "debit": "1800.0000",
            "description": "Buy Apple shares",
        }

    def test_create_view_url_exists(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_create_view_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "investments/trade_create.html")

    def test_valid_trade_is_created(self):
        response = self.client.post(self.url, data=self.valid_payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Daily_Trades.objects.count(), 1)

    def test_trade_fields_saved_correctly(self):
        self.client.post(self.url, data=self.valid_payload)
        trade = Daily_Trades.objects.first()

        self.assertEqual(trade.symbol, "AAPL")
        self.assertEqual(trade.action, "BTO")
        self.assertEqual(trade.qty, 10)
        self.assertEqual(trade.debit, Decimal("1800.0000"))

    def test_invalid_form_does_not_create_trade(self):
        invalid_payload = self.valid_payload.copy()
        invalid_payload.pop("symbol")

        response = self.client.post(self.url, data=invalid_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Daily_Trades.objects.count(), 0)




from django.test import TestCase
from django.urls import reverse
from decimal import Decimal
from datetime import date
from investments.models import Daily_Trades

class DailyTradesCreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("investments:daily_trades_create")
        cls.list_url = reverse("investments:daily_trades_list")

        cls.valid_payload = {
            "symbol": "AAPL",
            "transaction": "CRT-AAPL-001",
            "price": "180.0000",
            "strike_price": "0.0000",
            "action": "BTO",
            "qty": 10,
            "date": date.today(),
            "expiry": date.today(),
            "account_type": "CASH",
            "credit": "0.0000",
            "debit": "1800.0000",
            "page_number": "1",
            "description": "Valid trade",
        }

    # ----------------------------
    # UNIT TESTS
    # ----------------------------

    def test_create_view_url_exists(self):
        """Create view responds with HTTP 200"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_create_view_uses_correct_template(self):
        """Correct template is rendered (Fixed template name to trades_create)"""
        response = self.client.get(self.url)
        # Using the actual template found in your logs: trades_create.html
        self.assertTemplateUsed(response, "investments/trades_create.html")

    def test_valid_form_creates_trade(self):
        """Valid POST creates a Daily_Trades record and redirects (302)"""
        initial_count = Daily_Trades.objects.count()
        response = self.client.post(self.url, data=self.valid_payload)
        
        # A successful redirect means the form was valid and data was saved
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Daily_Trades.objects.count(), initial_count + 1)

    def test_valid_form_redirects_to_list(self):
        """Valid POST redirects to list view"""
        response = self.client.post(self.url, data=self.valid_payload)
        self.assertRedirects(response, self.list_url)

    def test_invalid_form_does_not_create_trade(self):
        """Invalid POST should return 200 (re-render form) and show errors"""
        invalid_payload = self.valid_payload.copy()
        invalid_payload.pop("symbol") # Missing required field

        response = self.client.post(self.url, data=invalid_payload)

        # 200 means it stayed on the page to show errors
        self.assertEqual(response.status_code, 200)
        # Check that the 'symbol' field specifically has an error
        self.assertFormError(response, 'form', 'symbol', 'This field is required.')

    # ----------------------------
    # REGRESSION TEST
    # ----------------------------

    def test_regression_missing_required_field(self):
        """Regression: missing numeric field must never save"""
        payload = self.valid_payload.copy()
        payload["price"] = "" # Invalid numeric data

        response = self.client.post(self.url, data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Daily_Trades.objects.count(), 0)

    # ----------------------------
    # INTEGRATION TEST
    # ----------------------------

    def test_integration_create_then_list(self):
        """Integration: create trade then confirm it appears in list view"""
        # 1. Create the trade
        self.client.post(self.url, data=self.valid_payload)

        # 2. Check the list view
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AAPL")
        self.assertContains(response, "CRT-AAPL-001")