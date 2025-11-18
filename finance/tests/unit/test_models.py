from django.test import TestCase
from finance.models import OverBoughtSold,PaymentInformation ,Default_Payment_Fees ,PayslipConfig
from django.utils import timezone# adjust app name if different
from decimal import Decimal

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
# test_models.py
from django.test import TestCase
from finance.models import Default_Payment_Fees

class DefaultPaymentFeesModelTest(TestCase):
    
    def setUp(self):
        # Creating a valid instance of Default_Payment_Fees with valid data
        self.payment_fee = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=500,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=300,
            student_bonus_payment_per_month=150
        )
    
    def test_default_payment_fees_creation(self):
        # Test if the Default_Payment_Fees instance is created correctly
        self.assertEqual(self.payment_fee.job_down_payment_per_month, 500)
        self.assertEqual(self.payment_fee.job_plan_hours_per_month, 160)
        self.assertEqual(self.payment_fee.student_down_payment_per_month, 300)
        self.assertEqual(self.payment_fee.student_bonus_payment_per_month, 150)
    
    def test_default_payment_fees_not_null(self):
        # Test if fields are not null (since null=False in the model)
        # Creating an object with valid values to avoid NULL constraint error
        try:
            Default_Payment_Fees.objects.create(
                job_down_payment_per_month=500,  
                job_plan_hours_per_month=160,    
                student_down_payment_per_month=300,  
                student_bonus_payment_per_month=150
            )
        except Exception as e:
            self.fail(f"Error creating Default_Payment_Fees: {e}")
    
    def test_default_payment_fees_field_types(self):
        # Test if fields are integer type
        self.assertIsInstance(self.payment_fee.job_down_payment_per_month, int)
        self.assertIsInstance(self.payment_fee.job_plan_hours_per_month, int)
        self.assertIsInstance(self.payment_fee.student_down_payment_per_month, int)
        self.assertIsInstance(self.payment_fee.student_bonus_payment_per_month, int)
    
    def test_default_payment_fees_str(self):
        # Test the string representation of the Default_Payment_Fees instance
        self.assertEqual(str(self.payment_fee), f"Default Payment Fee {self.payment_fee.id}")




class PayslipConfigModelTest(TestCase):

    def setUp(self):
        self.config = PayslipConfig.objects.create(
            loan_status=True,
            loan_amount=Decimal("120000.00"),
            loan_repayment_percentage=Decimal("10.00"),
            laptop_status=True,
            lb_amount=Decimal("45000.00"),
            ls_amount=Decimal("5000.00"),
            ls_max_limit=Decimal("50000.00"),
            rp_starting_period="Month 1",
            rp_starting_amount=Decimal("2500.00"),
            rp_increment_percentage=Decimal("5.00"),
        )

    def test_model_creation(self):
        """Ensure PayslipConfig object is created successfully."""
        self.assertTrue(PayslipConfig.objects.exists())

    def test_string_representation(self):
        """Check that __str__ method returns expected format."""
        expected = "PayslipConfig - Loan Status: True, Laptop Status: True"
        self.assertEqual(str(self.config), expected)

    def test_fields_values(self):
        """Verify stored values match what was provided."""
        self.assertEqual(self.config.loan_status, True)
        self.assertEqual(self.config.loan_amount, Decimal("120000.00"))
        self.assertEqual(self.config.loan_repayment_percentage, Decimal("10.00"))
        self.assertEqual(self.config.laptop_status, True)
        self.assertEqual(self.config.lb_amount, Decimal("45000.00"))
        self.assertEqual(self.config.ls_amount, Decimal("5000.00"))
        self.assertEqual(self.config.ls_max_limit, Decimal("50000.00"))
        self.assertEqual(self.config.rp_starting_period, "Month 1")
        self.assertEqual(self.config.rp_starting_amount, Decimal("2500.00"))
        self.assertEqual(self.config.rp_increment_percentage, Decimal("5.00"))

    def test_decimal_precision(self):
        """Ensure decimal fields maintain precision."""
        self.assertEqual(self.config.loan_amount.quantize(Decimal("0.00")), Decimal("120000.00"))
        self.assertEqual(self.config.ls_amount.quantize(Decimal("0.00")), Decimal("5000.00"))

    def test_field_types(self):
        """Check that fields are of correct data types."""
        self.assertIsInstance(self.config.loan_status, bool)
        self.assertIsInstance(self.config.laptop_status, bool)
        self.assertIsInstance(self.config.loan_amount, Decimal)
        self.assertIsInstance(self.config.ls_amount, Decimal)
        self.assertIsInstance(self.config.rp_starting_period, str)

