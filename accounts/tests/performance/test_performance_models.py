import time
from django.test import TestCase
from accounts.models import OverBoughtSold

class OverBoughtSoldPerformanceTest(TestCase):

    def setUp(self):
        # Create a large number of OverBoughtSold instances for performance testing
        self.records = []
        for i in range(1000):  # Creating 1000 records for performance testing
            self.records.append(OverBoughtSold.objects.create(
                symbol=f"SYM{i}",
                RSI="35",  # Valid RSI value above 30
                description=f"Description {i}",
                last="150",
                volume=10000,
                EPS="5.2",
                PE="30",
                rank="1",
                profit_margins="20%"
            ))

    def test_condition_integer_performance(self):
        # Measure the performance of the condition_integer property
        start_time = time.time()

        # Loop through all records and access the condition_integer property
        for stock in self.records:
            stock.condition_integer

        end_time = time.time()
        elapsed_time = end_time - start_time

        # We want the execution time for all 1000 records to be less than 1 second
        self.assertLess(elapsed_time, 1, f"Performance test failed, execution took {elapsed_time:.4f} seconds")

    def test_str_method_performance(self):
        # Measure the performance of the __str__ method
        start_time = time.time()

        # Loop through all records and call the __str__ method
        for stock in self.records:
            str(stock)

        end_time = time.time()
        elapsed_time = end_time - start_time

        # We want the execution time for all 1000 records to be less than 1 second
        self.assertLess(elapsed_time, 1, f"Performance test failed, execution took {elapsed_time:.4f} seconds")
