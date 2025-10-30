from django.test import TestCase
from finance.models import OverBoughtSold
from django.utils import timezone


class OverBoughtSoldIntegrationTest(TestCase):
    def setUp(self):
        # Create several objects to test the integration of save() + condition logic
        self.stock1 = OverBoughtSold.objects.create(
            symbol="AAPL",
            description="Apple Inc.",
            last="190.50",
            volume="5000000",
            rsi="72",
            eps="5.9",
            pe="34",
            rank="1",
            profit_margin="25%"
        )

        self.stock2 = OverBoughtSold.objects.create(
            symbol="TSLA",
            description="Tesla Motors",
            last="180.10",
            volume="6000000",
            rsi="28",
            eps="2.5",
            pe="22",
            rank="2",
            profit_margin="10%"
        )

    def test_records_are_saved_with_auto_condition(self):
        """Ensure save() automatically sets condition_integer"""
        self.assertEqual(self.stock1.condition_integer, 1)   # RSI 72 → Overbought
        self.assertEqual(self.stock2.condition_integer, -1)  # RSI 28 → Oversold

    def test_auto_timestamp_fields(self):
        """Verify that created_at and updated_at timestamps are auto populated"""
        self.assertIsNotNone(self.stock1.created_at)
        self.assertIsNotNone(self.stock1.updated_at)
        self.assertLessEqual(self.stock1.created_at, timezone.now())

    def test_update_model_changes_updated_at(self):
        """Ensure updated_at field changes when record is updated"""
        old_updated_time = self.stock1.updated_at
        self.stock1.volume = "7000000"
        self.stock1.save()
        self.stock1.refresh_from_db()
        self.assertGreater(self.stock1.updated_at, old_updated_time)

    def test_condition_label_reflects_condition_integer(self):
        """Integration between label mapping and condition calculation"""
        self.assertEqual(self.stock1.condition_label(), "Overbought")
        self.assertEqual(self.stock2.condition_label(), "Oversold")

    def test_bulk_create_and_query_integration(self):
        """Test integration with Django ORM bulk operations"""
        records = [
            OverBoughtSold(symbol="GOOG", rsi="55", volume="4000000"),
            OverBoughtSold(symbol="AMZN", rsi="15", volume="3000000"),
            OverBoughtSold(symbol="META", rsi="80", volume="2500000"),
        ]
        OverBoughtSold.objects.bulk_create(records)

        all_records = OverBoughtSold.objects.all()
        self.assertEqual(all_records.count(), 5)  # 2 from setup + 3 bulk created

        # Verify that condition is correctly recalculated when saved individually
        for stock in all_records:
            stock.save()  # triggers auto condition update
        meta = OverBoughtSold.objects.get(symbol="META")
        self.assertEqual(meta.condition_label(), "Overbought")
