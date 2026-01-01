from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from investments.models import InvestmentStrategy

class ModelRegressionTests(TestCase):

    def setUp(self):
        self.base_data = {
            "symbol": "TSLA",
            "action": "PUT",
            "expiry": date(2025, 12, 19),
            "day_to_expiry": 45,
            "earnings_date": date(2025, 10, 20),
            "on_date": date.today(),
            "strike_price": Decimal("200.00"),
            "mid_price": Decimal("5.00"),
            "ask_price": Decimal("5.10"),
            "iv_rank": Decimal("40.00"),
            "stock_price": Decimal("210.00"),
            "raw_return": Decimal("0.0250"),
            "annualized_return": Decimal("0.2000"),
            "opening": Decimal("5.00"),
            "comment": "Regression test case"
        }

    def test_decimal_max_digits_regression(self):
        """
        Regression: Ensure that prices exceeding 12 digits (as defined in the model) 
        properly raise a ValidationError to prevent database overflow.
        """
        invalid_price = Decimal('10000000000.00') # 13 digits total
        strategy = InvestmentStrategy(**self.base_data)
        strategy.strike_price = invalid_price
        
        with self.assertRaises(ValidationError):
            strategy.full_clean() # full_clean triggers the field validation

    def test_negative_day_to_expiry_logic(self):
        """
        Regression: Ensure the model handles or allows 0/negative days if 
        a trade is logged post-expiry (or verify current business rules).
        """
        self.base_data['day_to_expiry'] = 0
        strategy = InvestmentStrategy.objects.create(**self.base_data)
        self.assertEqual(strategy.day_to_expiry, 0)

    def test_long_comment_truncation(self):
        """
        Regression: Ensure TextField actually handles very large strings 
        without crashing (common regression when switching DB backends).
        """
        long_text = "Data " * 1000
        self.base_data['comment'] = long_text
        strategy = InvestmentStrategy.objects.create(**self.base_data)
        self.assertEqual(len(strategy.comment), 5000)