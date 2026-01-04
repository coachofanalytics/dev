import time
from django.test import TestCase
from decimal import Decimal
from datetime import date
from investments.models import InvestmentStrategy

class ModelPerformanceTests(TestCase):

    def setUp(self):
        """Prepare base data for bulk operations."""
        self.base_data = {
            "symbol": "AAPL",
            "action": "BUY",
            "expiry": date(2026, 1, 1),
            "day_to_expiry": 30,
            "earnings_date": date(2026, 1, 15),
            "on_date": date.today(),
            "strike_price": Decimal("150.00"),
            "mid_price": Decimal("2.50"),
            "ask_price": Decimal("2.60"),
            "iv_rank": Decimal("30.00"),
            "stock_price": Decimal("155.00"),
            "raw_return": Decimal("0.05"),
            "annualized_return": Decimal("0.60"),
            "opening": Decimal("2.45"),
            "comment": "Performance test entry"
        }

    def test_bulk_create_performance(self):
        """Ensure creating 1000 records happens in a reasonable timeframe."""
        objs = [InvestmentStrategy(**self.base_data) for _ in range(1000)]
        
        start_time = time.time()
        InvestmentStrategy.objects.bulk_create(objs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        # Threshold: 1000 records should generally save in under 0.5 seconds on local dev
        self.assertLess(execution_time, 1.0, f"Bulk create took too long: {execution_time}s")

    def test_query_retrieval_speed(self):
        """Test how fast we can retrieve and filter across a populated table."""
        # Setup: Create 500 records
        objs = [InvestmentStrategy(**self.base_data) for _ in range(500)]
        InvestmentStrategy.objects.bulk_create(objs)
        
        start_time = time.time()
        # Test a filter and count operation
        count = InvestmentStrategy.objects.filter(symbol="AAPL").count()
        end_time = time.time()
        
        execution_time = end_time - start_time
        self.assertEqual(count, 500)
        self.assertLess(execution_time, 0.1, f"Filtering took too long: {execution_time}s")









from django.test import TestCase
from decimal import Decimal
from datetime import date

from investments.models import Daily_Trades


class DailyTradesPerformanceTest(TestCase):

    def test_bulk_insert_1000_records(self):
        trades = [
            Daily_Trades(
                symbol="SPY",
                transaction=f"PERF-SPY-{i}",
                price=Decimal("450.0000"),
                strike_price=Decimal("0.0000"),
                action="BTO",
                qty=1,
                date=date.today(),
                account_type="CASH",
                credit=Decimal("0.0000"),
                debit=Decimal("450.0000"),
            )
            for i in range(1000)
        ]

        Daily_Trades.objects.bulk_create(trades)

        self.assertEqual(Daily_Trades.objects.count(), 1000)

    def test_filter_by_symbol_performance(self):
        Daily_Trades.objects.create(
            symbol="TSLA",
            transaction="PERF-TSLA-001",
            price=Decimal("250.0000"),
            strike_price=Decimal("0.0000"),
            action="BTO",
            qty=1,
            date=date.today(),
            account_type="CASH",
            credit=Decimal("0.0000"),
            debit=Decimal("250.0000"),
        )

        qs = Daily_Trades.objects.filter(symbol="TSLA")
        self.assertEqual(qs.count(), 1)
