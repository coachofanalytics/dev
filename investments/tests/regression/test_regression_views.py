from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from decimal import Decimal
from investments.models import InvestmentStrategy

class ViewRegressionTests(TestCase):

    def setUp(self):
        """Set up the environment for regression testing."""
        self.client = Client()
        self.url = reverse('investments:InvestmentStrategy_list')

    def test_view_with_zero_investments(self):
        """
        Regression: Ensure the page still loads (Status 200) and 
        displays the 'No strategies' message when the DB is empty.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Assuming you have an 'empty' block in your template
        self.assertContains(response, "No investment strategies found")

    def test_view_handles_extremely_long_comment(self):
        """
        Regression: Ensure very long text in the comment field doesn't 
        break the layout or cause a server error (HTTP 500).
        """
        long_comment = "Risk " * 2000 # 10,000 characters
        InvestmentStrategy.objects.create(
            symbol="LONG", action="BUY", expiry=date.today(), day_to_expiry=1,
            earnings_date=date.today(), on_date=date.today(), strike_price=100,
            mid_price=1, ask_price=1.1, iv_rank=20, stock_price=101,
            raw_return=0.1, annualized_return=1.2, opening=0.9, comment=long_comment
        )
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('investments', response.context)

    def test_view_precision_rendering(self):
        """
        Regression: Ensure Decimal values (like IV Rank) are rendered 
        with the correct precision in the HTML.
        """
        InvestmentStrategy.objects.create(
            symbol="PREC", action="BUY", expiry=date.today(), day_to_expiry=1,
            earnings_date=date.today(), on_date=date.today(), strike_price=100,
            mid_price=1, ask_price=1.1, iv_rank=Decimal("45.27"), stock_price=101,
            raw_return=0.1, annualized_return=1.2, opening=0.9, comment="Test"
        )
        
        response = self.client.get(self.url)
        self.assertContains(response, "45.27")

    def test_invalid_url_parameters_ignored(self):
        """
        Regression: Ensure that passing junk query parameters doesn't 
        cause the list view to crash.
        """
        response = self.client.get(self.url + "?page=abc&sort=xyz")
        self.assertEqual(response.status_code, 200)



from django.test import TestCase, Client
from django.urls import reverse
from investments.models import InvestmentStrategy

class CreateViewRegressionTests(TestCase):

    def setUp(self):
        """Set up the test client and the Create URL."""
        self.client = Client()
        self.url = reverse('investments:InvestmentStrategy_create')

    def test_create_view_empty_post_regression(self):
        """
        Regression: Ensure that submitting a completely empty POST 
        request does not result in a 500 Server Error. 
        It should return 200 (re-rendering the form with errors).
        """
        response = self.client.post(self.url, {})
        
        # A 500 error means the code crashed. A 200 means it handled the error.
        self.assertEqual(response.status_code, 200)
        
        # Verify that the form is returned with errors
        self.assertFalse(response.context['form'].is_valid())
        self.assertEqual(InvestmentStrategy.objects.count(), 0)

    def test_create_view_malformed_data_regression(self):
        """
        Regression: Ensure that sending strings to numeric fields 
        (like strike_price) is caught by validation and doesn't crash the DB.
        """
        bad_data = {
            'symbol': 'AAPL',
            'strike_price': 'NOT_A_NUMBER',  # This should be a Decimal/Float
            'iv_rank': 'HIGH',               # This should be a Number
        }
        response = self.client.post(self.url, bad_data)
        
        self.assertEqual(response.status_code, 200)
        # Check that the strike_price specifically has a validation error
        self.assertFormError(response, 'form', 'strike_price', 'Enter a number.')

    def test_create_view_get_request_no_data(self):
        """
        Regression: Ensure the page simply loads a blank form 
        on a GET request without any side effects.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'].initial, dict)        




def test_update_with_invalid_data_regression(self):
        """Regression: Ensure partial/bad data doesn't update the DB."""
        # FIX: Include earnings_date and on_date to avoid IntegrityError
        strategy = InvestmentStrategy.objects.create(
            symbol="TEST", 
            strike_price=100, 
            iv_rank=10, 
            day_to_expiry=1, 
            expiry=date.today(),
            earnings_date=date.today(),  # Added this
            on_date=date.today()         # Added this just in case
        )
        url = reverse('investments:InvestmentStrategy_update', kwargs={'pk': strategy.pk})
        
        # Post data with an empty symbol (which is invalid)
        response = self.client.post(url, {
            'symbol': '', 
            'strike_price': 100,
            'earnings_date': str(date.today()),
            'expiry': str(date.today())
        })
        
        # Should return 200 (re-render form with error), not 302 (redirect)
        self.assertEqual(response.status_code, 200) 
        
        # Refresh from database and check that the symbol is STILL "TEST"
        strategy.refresh_from_db()
        self.assertEqual(strategy.symbol, "TEST")







class DeleteRegressionTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_delete_nonexistent_id_regression(self):
        """Regression: Ensure deleting a fake ID returns 404, not a 500 crash."""
        url = reverse('investments:InvestmentStrategy_delete', kwargs={'pk': 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)    










from django.test import TestCase
from django.urls import reverse
from decimal import Decimal
from datetime import date

from investments.models import Daily_Trades


class DailyTradesListRegressionTest(TestCase):

    def setUp(self):
        Daily_Trades.objects.create(
            symbol="MSFT",
            transaction="REG-MSFT-001",
            price=Decimal("300.0000"),
            strike_price=Decimal("0.0000"),
            action="BTO",
            qty=5,
            date=date.today(),
            account_type="CASH",
            credit=Decimal("0.0000"),
            debit=Decimal("1500.0000"),
        )

    def test_list_view_url_still_resolves(self):
        response = self.client.get(
            reverse("investments:daily_trades_list")
        )
        self.assertEqual(response.status_code, 200)

    def test_existing_trade_still_appears(self):
        response = self.client.get(
            reverse("investments:daily_trades_list")
        )
        self.assertContains(response, "MSFT")

    def test_net_calculation_regression(self):
        response = self.client.get(
            reverse("investments:daily_trades_list")
        )

        self.assertEqual(
            response.context["total_net"],
            Decimal("-1500.0000")
        )





from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.urls import reverse
from investments.models import Daily_Trades

class DailyTradesCreateViewTest(TestCase):

    def setUp(self):
        # Using the URL name defined in your project
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
            "page_number": "1", # Added because it's usually required in your model
        }

    def test_create_view_url_exists(self):
        """View should respond with HTTP 200"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_create_view_uses_correct_template(self):
        """Fixed: Using 'trades_create.html' as identified in logs"""
        response = self.client.get(self.url)
        # Your previous error showed the actual template is 'trades_create.html'
        self.assertTemplateUsed(response, "investments/trades_create.html")

    def test_valid_trade_is_created(self):
        """Successful POST should redirect (302) and save to DB"""
        response = self.client.post(self.url, data=self.valid_payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Daily_Trades.objects.count(), 1)

    def test_trade_fields_saved_correctly(self):
        """Verify the data in the DB matches the payload"""
        self.client.post(self.url, data=self.valid_payload)
        trade = Daily_Trades.objects.first()

        self.assertEqual(trade.symbol, "AAPL")
        self.assertEqual(trade.action, "BTO")
        self.assertEqual(trade.qty, 10)
        # Ensure Decimal comparison is accurate
        self.assertEqual(trade.debit, Decimal("1800.0000"))

    def test_invalid_form_does_not_create_trade(self):
        """Missing required field should stay on page (200) and not save"""
        invalid_payload = self.valid_payload.copy()
        invalid_payload.pop("symbol") # Symbol is required

        response = self.client.post(self.url, data=invalid_payload)
        
        # 200 means the form re-rendered with errors
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Daily_Trades.objects.count(), 0)
        # Explicitly check for the form error
        self.assertFormError(response, 'form', 'symbol', 'This field is required.')