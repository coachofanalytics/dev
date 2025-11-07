from django.test import TestCase
from finance.models import OverBoughtSold,PaymentInformation  
from django.utils import timezone# adjust app name if different

class OverBoughtSoldModelTest(TestCase):
    def setUp(self):
        # Create sample records
        self.overbought = OverBoughtSold.objects.create(symbol="AAPL", rsi="75")
        self.oversold = OverBoughtSold.objects.create(symbol="TSLA", rsi="25")
        self.neutral = OverBoughtSold.objects.create(symbol="GOOG", rsi="50")
        self.invalid = OverBoughtSold.objects.create(symbol="MSFT", rsi="invalid")

    def test_calculate_condition_integer(self):
        self.assertEqual(self.overbought.condition_integer, 1)
        self.assertEqual(self.oversold.condition_integer, -1)
        self.assertEqual(self.neutral.condition_integer, 0)
        self.assertIsNone(self.invalid.condition_integer)

    def test_condition_label(self):
        self.assertEqual(self.overbought.condition_label(), "Overbought")
        self.assertEqual(self.oversold.condition_label(), "Oversold")
        self.assertEqual(self.neutral.condition_label(), "Neutral")
        self.assertEqual(self.invalid.condition_label(), "Unknown")

    def test_str_representation(self):
        self.assertEqual(str(self.overbought), "AAPL - Overbought")
        self.assertEqual(str(self.oversold), "TSLA - Oversold")
        self.assertEqual(str(self.neutral), "GOOG - Neutral")
        self.assertEqual(str(self.invalid), "MSFT - Unknown")




class PaymentInformationModelTest(TestCase):

    def setUp(self):
        self.payment = PaymentInformation.objects.create(
            payment_fees=1500,
            down_payment=500,
            student_bonus=100,
            fee_balance=900,
            plan="Standard",
            subplan="Silver",
            payment_method="Mobile Money",
            contract_submitted_date=timezone.now(),
            client_signature="John Doe",
            company_rep="Alice M.",
            client_date="2025-01-15",
            description="First installment for tuition",
            is_active=True,
            is_featured=False
        )

    def test_payment_information_creation(self):
        """Test that a payment record is created successfully."""
        self.assertEqual(self.payment.plan, "Standard")
        self.assertEqual(self.payment.payment_fees, 1500)
        self.assertTrue(self.payment.is_active)
        self.assertFalse(self.payment.is_featured)

    def test_string_representation(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.payment), "Standard - Mobile Money")

    def test_fee_balance_is_correct_type(self):
        """Ensure fee_balance is an integer."""
        self.assertIsInstance(self.payment.fee_balance, int)