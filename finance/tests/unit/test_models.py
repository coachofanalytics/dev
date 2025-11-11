from django.test import TestCase
from finance.models import OverBoughtSold
from django.utils import timezone


class OverBoughtSoldModelTest(TestCase):
    def setUp(self):
        """
        This method is used to set up initial conditions for tests.
        Creates an instance of the OverBoughtSold model.
        """
        self.stock = OverBoughtSold.objects.create(
            symbol="AAPL",
            description="Apple Inc.",
            last=145.30,
            volume=50000,
            RSI=75.0,
            EPS=5.50,
            PE=28.0,
            rank="Top Performer",
            profit_margins=22.5,
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

    def test_status_overbought(self):
        """
        Test if the stock is correctly classified as 'Overbought' when RSI > 70.
        """
        self.assertEqual(self.stock.status, "Overbought")

    def test_status_oversold(self):
        """
        Test if the stock is correctly classified as 'Oversold' when RSI < 30.
        """
        self.stock.RSI = 25.0
        self.stock.save()  # Save the change to the database
        self.assertEqual(self.stock.status, "Oversold")

    def test_status_neutral(self):
        """
        Test if the stock is correctly classified as 'Neutral' when RSI is between 30 and 70.
        """
        self.stock.RSI = 50.0
        self.stock.save()  # Save the change to the database
        self.assertEqual(self.stock.status, "Neutral")

    def test_status_unknown(self):
        """
        Test if the stock status is 'Unknown' when RSI is None or invalid.
        """
        self.stock.RSI = None
        self.stock.save()  # Save the change to the database
        self.assertEqual(self.stock.status, "Unknown")

    def test_model_string_representation(self):
        """
        Test the string representation of the model.
        """
        self.assertEqual(str(self.stock), "AAPL")

    def test_field_defaults(self):
        """
        Test the default values for fields like created_at and updated_at.
        """
        self.assertIsInstance(self.stock.created_at, timezone.datetime)
        self.assertIsInstance(self.stock.updated_at, timezone.datetime)

    def test_ordering(self):
        """
        Test the ordering of stocks by created_at (descending).
        """
        # Create a second stock with a later created_at timestamp
        stock2 = OverBoughtSold.objects.create(
            symbol="GOOG",
            description="Google Inc.",
            last=2750.30,
            volume=100000,
            RSI=80.0,
            EPS=10.25,
            PE=26.9,
            rank="Mid Performer",
            profit_margins=18.4,
            created_at=timezone.now()
            + timezone.timedelta(seconds=10),  # Later timestamp
            updated_at=timezone.now() + timezone.timedelta(seconds=10),
        )

        # Fetch stocks from the database ordered by created_at (descending)
        stocks = OverBoughtSold.objects.all()

        # Ensure that the first stock in the list is 'GOOG' (created later)
        self.assertEqual(stocks[0], stock2)
        self.assertEqual(
            stocks[1], self.stock
        )  # The first stock should be GOOG and second should be AAPL
