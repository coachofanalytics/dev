import time
from django.test import TestCase
from finance.models import OverBoughtSold


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
