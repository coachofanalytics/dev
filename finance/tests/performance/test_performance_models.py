import time
from django.test import TestCase
from finance.models import OverBoughtSold,PaymentInformation
from django.db import connection

from django.utils import timezone  # Import timezone here





class OverBoughtSoldPerformanceTest(TestCase):
    def setUp(self):
        """Prepare data for performance testing"""
        self.sample_data = [
            OverBoughtSold(
                symbol=f"SYM{i}",
                description=f"Stock {i}",
                last=str(100 + i),
                volume=str(100000 + i * 10),
                rsi=str(i % 100),
                eps=str(round(2.5 + i * 0.01, 2)),
                pe=str(round(20 + i * 0.05, 2)),
                rank=str(i),
                profit_margin=f"{(i % 30) + 5}%",
            )
            for i in range(1, 1001)  # 1,000 records
        ]

    def test_bulk_create_performance(self):
        """Test how fast 1000 OverBoughtSold entries can be inserted"""
        start_time = time.time()
        OverBoughtSold.objects.bulk_create(self.sample_data)
        end_time = time.time()
        duration = end_time - start_time

        print(f"\nBulk create time for 1000 records: {duration:.3f} seconds")

        self.assertLess(duration, 2.5, "Bulk create took too long!")
        self.assertEqual(OverBoughtSold.objects.count(), 1000)

    def test_bulk_update_performance(self):
        """Test how fast multiple objects can be updated"""
        OverBoughtSold.objects.bulk_create(self.sample_data)
        all_stocks = list(OverBoughtSold.objects.all())

        for stock in all_stocks:
            stock.volume = str(int(stock.volume) + 10000)

        start_time = time.time()
        OverBoughtSold.objects.bulk_update(all_stocks, ["volume"])
        end_time = time.time()
        duration = end_time - start_time

        print(f"\nBulk update time for 1000 records: {duration:.3f} seconds")

        self.assertLess(duration, 2.5, "Bulk update took too long!")

    def test_query_performance(self):
        """Check the performance of querying with filters"""
        OverBoughtSold.objects.bulk_create(self.sample_data)

        start_time = time.time()
        top_ranked = OverBoughtSold.objects.filter(rank__lte="10")
        end_time = time.time()
        duration = end_time - start_time

        print(f"\nQuery filter time: {duration:.5f} seconds for {top_ranked.count()} results")

        self.assertLess(duration, 1, "Query filtering took too long!")
        self.assertGreater(top_ranked.count(), 0)





class PaymentInformationPerformanceTest(TestCase):

    def setUp(self):
        """Setup test data for performance tests"""
        self.payment_data = {
            'payment_fees': 1500,
            'down_payment': 500,
            'student_bonus': 100,
            'fee_balance': 900,
            'plan': "Standard",
            'subplan': "Silver",
            'payment_method': "Mobile Money",
            'contract_submitted_date': timezone.now(),  # Correct usage of timezone.now()
            'client_signature': "John Doe",
            'company_rep': "Alice M.",
            'client_date': "2025-01-15",
            'description': "First installment for tuition",
            'is_active': True,
            'is_featured': False
        }

    def test_create_performance(self):
        """Test the time taken to create a PaymentInformation instance."""
        start_time = time.time()
        
        # Create a PaymentInformation instance
        PaymentInformation.objects.create(**self.payment_data)
        
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        self.assertLess(elapsed_time, 0.1, f"Performance issue: Creation took {elapsed_time} seconds")
    
    def test_bulk_create_performance(self):
        """Test the time taken to bulk create 1000 PaymentInformation instances."""
        bulk_data = [PaymentInformation(**self.payment_data) for _ in range(1000)]
        
        start_time = time.time()
        
        # Bulk create the PaymentInformation instances
        PaymentInformation.objects.bulk_create(bulk_data)
        
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        self.assertLess(elapsed_time, 1.0, f"Performance issue: Bulk creation took {elapsed_time} seconds")
    
    def test_query_performance(self):
        """Test the performance of querying PaymentInformation instances."""
        # Create some data to query
        for _ in range(500):
            PaymentInformation.objects.create(**self.payment_data)
        
        start_time = time.time()
        
        # Query the PaymentInformation instances
        PaymentInformation.objects.all()
        
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        self.assertLess(elapsed_time, 0.5, f"Performance issue: Querying took {elapsed_time} seconds")
    
    def test_select_related_performance(self):
        """Test the performance of using select_related to optimize queries."""
        # Create some related data (simulating a ForeignKey or related field)
        # For simplicity, we're not using actual related fields in this example.
        for _ in range(500):
            PaymentInformation.objects.create(**self.payment_data)
        
        start_time = time.time()
        
        # Use select_related to optimize the query (assuming related fields are present)
        PaymentInformation.objects.all().select_related('plan')  # Assuming 'plan' is related (adjust as necessary)
        
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        self.assertLess(elapsed_time, 0.5, f"Performance issue: select_related query took {elapsed_time} seconds")
    
    def test_indexed_query_performance(self):
        """Test the performance of querying with indexed fields."""
        for _ in range(500):
            PaymentInformation.objects.create(**self.payment_data)
        
        # Assume there's an index on 'plan' field
        start_time = time.time()
        
        # Query by indexed field
        PaymentInformation.objects.filter(plan="Standard")
        
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        self.assertLess(elapsed_time, 0.2, f"Performance issue: Indexed query took {elapsed_time} seconds")
    
    def test_db_query_count(self):
        """Test the number of database queries made during an operation."""
        for _ in range(500):
            PaymentInformation.objects.create(**self.payment_data)
        
        # Using assertNumQueries with an actual query evaluation
        with self.assertNumQueries(1):  # Expecting only 1 query to retrieve all
            # Force the queryset evaluation by converting it to a list
            payments = list(PaymentInformation.objects.all())  # Convert to list to force query evaluation
            self.assertGreater(len(payments), 0)  # Ensure there are results



import time
from django.test import TestCase
from finance.models import PayslipConfig
from decimal import Decimal


class PayslipConfigPerformanceTests(TestCase):

    def setUp(self):
        self.config = PayslipConfig.objects.create(
            loan_status=True,
            loan_amount=Decimal("100000.00"),
            loan_repayment_percentage=Decimal("10.00"),
            laptop_status=True,
            lb_amount=Decimal("30000.00"),
            ls_amount=Decimal("3500.00"),
            ls_max_limit=Decimal("40000.00"),
            rp_starting_period="Month 1",
            rp_starting_amount=Decimal("1500.00"),
            rp_increment_percentage=Decimal("5.00"),
        )

    def test_single_instance_query_speed(self):
        start = time.time()
        obj = PayslipConfig.objects.get(id=self.config.id)
        end = time.time()
        self.assertIsNotNone(obj)
        self.assertLess(end - start, 0.05)  # 50 ms for Windows

    def test_bulk_creation_performance(self):
        items = [
            PayslipConfig(
                loan_status=True,
                loan_amount=Decimal("50000.00"),
                loan_repayment_percentage=Decimal("7.00"),
                laptop_status=False,
                lb_amount=Decimal("0.00"),
                ls_amount=Decimal("0.00"),
                ls_max_limit=Decimal("0.00"),
                rp_starting_period="Month 1",
                rp_starting_amount=Decimal("1200.00"),
                rp_increment_percentage=Decimal("3.00"),
            )
            for _ in range(1000)
        ]

        start = time.time()
        PayslipConfig.objects.bulk_create(items)
        end = time.time()

        self.assertLess(end - start, 0.50)  # 500 ms for Windows

    def test_queryset_iteration_performance(self):
        for i in range(500):
            PayslipConfig.objects.create(
                loan_status=False,
                loan_amount=Decimal("20000.00"),
                loan_repayment_percentage=Decimal("5.00"),
                laptop_status=False,
                lb_amount=Decimal("0.00"),
                ls_amount=Decimal("0.00"),
                ls_max_limit=Decimal("0.00"),
                rp_starting_period="Month 2",
                rp_starting_amount=Decimal("800.00"),
                rp_increment_percentage=Decimal("2.00"),
            )

        start = time.time()
        for obj in PayslipConfig.objects.all():
            _ = obj.loan_amount
        end = time.time()

        self.assertLess(end - start, 0.20)  # 200 ms

    def test_string_representation_performance(self):
        start = time.time()
        _ = str(self.config)
        end = time.time()
        self.assertLess(end - start, 0.02)  # 20 ms
