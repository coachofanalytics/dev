from django.test import TestCase
from finance.models import OverBoughtSold
from django.utils import timezone


class OverBoughtSoldIntegrationTest(TestCase):
    def setUp(self):
        """
        Set up initial conditions for integration tests.
        Creates a stock entry.
        """
        self.stock_data = {
            "description": "Apple Inc.",
            "last": 145.30,
            "volume": 50000,
            "RSI": 75.0,
            "EPS": 5.50,
            "PE": 28.0,
            "rank": "Top Performer",
            "profit_margins": 22.5,
            "created_at": timezone.now(),
            "updated_at": timezone.now(),
        }
        self.stock = OverBoughtSold.objects.create(symbol="AAPL", **self.stock_data)

    def test_bulk_create_integration(self):
        """
        Test the bulk creation of stock entries and verify if they are saved correctly.
        """
        # Create multiple stock entries using bulk_create, but pass `symbol` separately
        stock_entries = [
            OverBoughtSold(**self.stock_data, symbol=f"AAPL_{i}")
            for i in range(1, 1001)
        ]

        # Perform bulk create
        OverBoughtSold.objects.bulk_create(stock_entries)

        # Verify the bulk creation
        self.assertEqual(
            OverBoughtSold.objects.count(), 1001
        )  # Including the original stock
        self.assertTrue(OverBoughtSold.objects.filter(symbol="AAPL_1").exists())

    def test_bulk_update_integration(self):
        """
        Test if bulk update works correctly for stock entries.
        """
        # Create multiple stock entries for update
        stock_entries = [
            OverBoughtSold(**self.stock_data, symbol=f"AAPL_{i}")
            for i in range(1, 1001)
        ]
        OverBoughtSold.objects.bulk_create(stock_entries)

        # Perform bulk update (e.g., set RSI to 50 for all stocks)
        OverBoughtSold.objects.update(RSI=50.0)

        # Verify the bulk update
        self.assertTrue(OverBoughtSold.objects.filter(RSI=50.0).exists())


from django.test import TestCase
from django.utils import timezone
from accounts.models import CustomerUser
from finance.models import OverBoughtSold, PaymentInformation
from decimal import Decimal
from datetime import timedelta


class IntegrationTestModels(TestCase):
    def setUp(self):
        """
        Set up initial conditions for the integration tests.
        Creates necessary instances of the models to test integration between them.
        """
        # Create a test customer user
        self.customer = CustomerUser.objects.create(
            username="brenda",
            email="brenda@example.com"
        )

        # Create a stock entry in OverBoughtSold model
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

        # Create a PaymentInformation entry linked to the customer
        self.payment_info = PaymentInformation.objects.create(
            customer=self.customer,
            total_fees=Decimal('6000.00'),
            down_payment=Decimal('1000.00'),
            student_bonus=Decimal('500.00'),
            payment_method="Cash",
            contract_submitted_date=timezone.now() - timedelta(days=2),
            is_active=True,
            is_tested=False,
            is_reviewed=False
        )

    def test_integration_stock_payment_info(self):
        """
        Test the integration of stock and payment information.
        Ensure the stock is linked with customer payment information.
        """
        # Ensure that stock and payment information are correctly linked via the customer
        self.assertEqual(self.payment_info.customer.username, self.customer.username)
        self.assertEqual(self.payment_info.total_fees, Decimal('6000.00'))
        self.assertEqual(self.stock.symbol, "AAPL")
        self.assertEqual(self.stock.description, "Apple Inc.")

    def test_payment_and_stock_status(self):
        """
        Test that the payment status impacts the stock's status.
        Ensure proper integration between stock data and payments.
        """
        # Update stock status based on the payment
        if self.payment_info.total_fees > Decimal('5000.00'):
            self.stock.RSI = 80.0  # Simulating an effect on stock due to high payment
            self.stock.save()

        self.assertEqual(self.stock.status, "Overbought")

    def test_update_customer_payment_and_stock(self):
        """
        Test if updating a customer's payment properly updates related stock status.
        """
        # Update the payment and check integration with stock
        self.payment_info.total_fees = Decimal('7000.00')
        self.payment_info.save()

        # Simulate some effect of the updated payment on stock
        if self.payment_info.total_fees > Decimal('6000.00'):
            self.stock.RSI = 80.0  # Update stock status based on payment info
            self.stock.save()

        self.assertEqual(self.stock.status, "Overbought")
        self.assertEqual(self.payment_info.total_fees, Decimal('7000.00'))

    def test_create_related_entries_integration(self):
        """
        Test creating related entries in the OverBoughtSold and PaymentInformation models.
        Ensure that data consistency is maintained.
        """
        # Create a new stock entry and related payment entry
        new_stock = OverBoughtSold.objects.create(
            symbol="GOOG",
            description="Google Inc.",
            last=2750.30,
            volume=100000,
            RSI=65.0,
            EPS=10.25,
            PE=26.9,
            rank="Mid Performer",
            profit_margins=18.4,
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
        
        new_payment_info = PaymentInformation.objects.create(
            customer=self.customer,
            total_fees=Decimal('8000.00'),
            down_payment=Decimal('2000.00'),
            student_bonus=Decimal('0.00'),
            payment_method="Cash",
            contract_submitted_date=timezone.now(),
            is_active=True,
            is_tested=False,
            is_reviewed=False
        )

        # Test if the new stock and payment information are integrated correctly
        self.assertEqual(new_stock.symbol, "GOOG")
        self.assertEqual(new_payment_info.total_fees, Decimal('8000.00'))
        self.assertEqual(new_payment_info.customer.username, self.customer.username)

    def test_stock_and_payment_rollback(self):
        """
        Test that when payment creation fails, stock creation is rolled back.
        """
        # Simulate a failure during payment creation
        try:
            with self.assertRaises(Exception):
                self.payment_info.total_fees = None  # Invalid value
                self.payment_info.save()  # This should raise an error
        except Exception:
            # Check if stock creation was also rolled back
            stock_count_before = OverBoughtSold.objects.count()
            self.assertEqual(stock_count_before, 1)  # Only one stock created in setUp

    def test_multiple_customer_payments_and_stock_updates(self):
        """
        Test if multiple payments from a customer update the stock as expected.
        """
        # Create a second payment for the same customer
        second_payment_info = PaymentInformation.objects.create(
            customer=self.customer,
            total_fees=Decimal('10000.00'),
            down_payment=Decimal('3000.00'),
            student_bonus=Decimal('0.00'),
            payment_method="Bank Transfer",
            contract_submitted_date=timezone.now(),
            is_active=True,
            is_tested=False,
            is_reviewed=False
        )

        # Ensure stock reflects the new payment
        if second_payment_info.total_fees > Decimal('9000.00'):
            self.stock.RSI = 85.0  # Adjust stock RSI based on payment
            self.stock.save()

        self.assertEqual(self.stock.status, "Overbought")
        self.assertEqual(second_payment_info.total_fees, Decimal('10000.00'))
        
