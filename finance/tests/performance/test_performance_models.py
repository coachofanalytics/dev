from django.test import TestCase
from finance.models import OverBoughtSold
import time

class OverBoughtSoldPerformanceTest(TestCase):

    def test_bulk_create_performance(self):
        start = time.time()
        stocks = [
            OverBoughtSold(symbol=f"STOCK{i}", RSI=50)
            for i in range(10000)
        ]
        OverBoughtSold.objects.bulk_create(stocks)
        end = time.time()

        self.assertLess(end - start, 3, "Bulk insert took too long")

    def test_query_performance(self):
        OverBoughtSold.objects.bulk_create(
            [OverBoughtSold(symbol=f"S{i}", RSI=50) for i in range(5000)]
        )
        start = time.time()
        list(OverBoughtSold.objects.filter(RSI=50))
        end = time.time()

        self.assertLess(end - start, 0.5, "Query performance is too slow")
