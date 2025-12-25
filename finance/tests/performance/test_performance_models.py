from django.test import TestCase
from django.utils import timezone
from finance.models import OverBoughtSold
from accounts.models import CustomerUser
from finance.models import PaymentInformation
from decimal import Decimal
from datetime import timedelta
import time


class OverBoughtSoldPerformanceTest(TestCase):
    def setUp(self):
        """
        This method is used to set up initial conditions for the performance tests.
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

    def test_create_performance(self):
        """
        Test the performance of creating 1000 stock entries.
        """
        start_time = time.time()

        # Create 1000 stock entries, symbol passed separately
        for i in range(1000):
            OverBoughtSold.objects.create(
                **self.stock_data, symbol=f"AAPL_{i}"  # Unique symbol for each entry
            )

        end_time = time.time()
        total_time = end_time - start_time

        print(f"Time taken to create 1000 stock entries: {total_time:.2f} seconds")
        self.assertTrue(
            total_time < 5,
            f"Creation of 1000 stock entries took too long: {total_time:.2f} seconds",
        )

    def test_retrieve_performance(self):
        """
        Test the performance of retrieving stock entries.
        """
        # Bulk create 1000 stock entries
        OverBoughtSold.objects.bulk_create(
            [OverBoughtSold(**self.stock_data, symbol=f"AAPL_{i}") for i in range(1000)]
        )

        start_time = time.time()

        # Test retrieving 1000 stock entries
        OverBoughtSold.objects.all()  # No need to assign it to a variable

        end_time = time.time()
        total_time = end_time - start_time

        print(f"Time taken to retrieve 1000 stock entries: {total_time:.2f} seconds")
        self.assertTrue(
            total_time < 2,
            f"Retrieval of 1000 stock entries took too long: {total_time:.2f} seconds",
        )

    def test_update_performance(self):
        """
        Test the performance of updating stock entries.
        """
        # Bulk create 1000 stock entries
        OverBoughtSold.objects.bulk_create(
            [OverBoughtSold(**self.stock_data, symbol=f"AAPL_{i}") for i in range(1000)]
        )

        start_time = time.time()

        # Update RSI for all stock entries
        for stock in OverBoughtSold.objects.all():
            stock.RSI = 50  # Update RSI to a new value
            stock.save()

        end_time = time.time()
        total_time = end_time - start_time

        print(f"Time taken to update 1000 stock entries: {total_time:.2f} seconds")
        self.assertTrue(
            total_time < 5,
            f"Update of 1000 stock entries took too long: {total_time:.2f} seconds",
        )

    def test_delete_performance(self):
        """
        Test the performance of deleting 1000 stock entries.
        """
        # Bulk create 1000 stock entries
        OverBoughtSold.objects.bulk_create(
            [OverBoughtSold(**self.stock_data, symbol=f"AAPL_{i}") for i in range(1000)]
        )

        start_time = time.time()

        # Delete all stock entries
        OverBoughtSold.objects.all().delete()

        end_time = time.time()
        total_time = end_time - start_time

        print(f"Time taken to delete 1000 stock entries: {total_time:.2f} seconds")
        self.assertTrue(
            total_time < 5,
            f"Deletion of 1000 stock entries took too long: {total_time:.2f} seconds",
        )
from django.test import TestCase
from django.utils import timezone
from accounts.models import CustomerUser
from finance.models import PaymentInformation
from decimal import Decimal
from datetime import timedelta
import time


class PaymentInformationModelPerformanceTest(TestCase):
    def setUp(self):
        """
        This method is used to set up initial conditions for performance tests.
        Creates a large number of instances of the PaymentInformation model to test the performance.
        """
        self.customer = CustomerUser.objects.create(
            username="brenda",
            email="brenda@example.com"
        )
        
        # Create a large number of PaymentInformation instances for performance testing
        for i in range(1000):
            PaymentInformation.objects.create(
                customer=self.customer,
                total_fees=Decimal(f'{1000 + i}.00'),
                down_payment=Decimal('500.00'),
                student_bonus=Decimal('0.00'),
                payment_method="Cash",
                contract_submitted_date=timezone.now() - timedelta(days=i),
                is_active=True,
                is_tested=False,
                is_reviewed=False
            )

    def test_performance_payment_query(self):
        """
        Test the performance of querying a large number of payment records.
        """
        with self.assertNumQueries(1):  # Expecting 1 query for retrieving the records
            payments = list(PaymentInformation.objects.all())  # Force query evaluation by converting to a list

    def test_performance_payment_filtering(self):
        """
        Test the performance of filtering payment records by customer.
        """
        with self.assertNumQueries(1):  # Expecting 1 query for filtering
            payments = list(PaymentInformation.objects.filter(customer=self.customer))  # Force query evaluation

    def test_performance_payment_count(self):
        """
        Test the performance of counting a large number of payment records.
        """
        with self.assertNumQueries(1):  # Only one query to count all the records
            payment_count = PaymentInformation.objects.count()
            self.assertEqual(payment_count, 1000)
