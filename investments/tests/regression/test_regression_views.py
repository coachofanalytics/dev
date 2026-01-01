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