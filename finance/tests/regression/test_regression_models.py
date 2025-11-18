from django.test import TestCase
from finance.models import OverBoughtSold,PaymentInformation,PayslipConfig
from django.utils import timezone
from decimal import Decimal

class OverBoughtSoldRegressionTest(TestCase):
    """
    Regression tests for the OverBoughtSold model to ensure that
    condition calculation, saving logic, and label mapping remain correct
    after future code changes.
    """

    def setUp(self):
        self.stock_overbought = OverBoughtSold.objects.create(symbol="AAPL", rsi="75")
        self.stock_oversold = OverBoughtSold.objects.create(symbol="TSLA", rsi="25")
        self.stock_neutral = OverBoughtSold.objects.create(symbol="GOOG", rsi="50")
        self.stock_invalid = OverBoughtSold.objects.create(symbol="MSFT", rsi="invalid")

    def test_regression_condition_integer_consistency(self):
        """
        Test that the RSI condition logic (Overbought, Oversold, Neutral)
        produces consistent integer results as originally designed.
        """
        self.assertEqual(self.stock_overbought.condition_integer, 1)
        self.assertEqual(self.stock_oversold.condition_integer, -1)
        self.assertEqual(self.stock_neutral.condition_integer, 0)
        self.assertIsNone(self.stock_invalid.condition_integer)

    def test_regression_label_consistency(self):
        """
        Verify that label mapping has not changed unintentionally.
        """
        self.assertEqual(self.stock_overbought.condition_label(), "Overbought")
        self.assertEqual(self.stock_oversold.condition_label(), "Oversold")
        self.assertEqual(self.stock_neutral.condition_label(), "Neutral")
        self.assertEqual(self.stock_invalid.condition_label(), "Unknown")

    def test_regression_save_does_not_break_condition_calculation(self):
        """
        Ensure that saving again does not break the automatic RSI condition logic.
        """
        self.stock_neutral.rsi = "80"
        self.stock_neutral.save()
        self.stock_neutral.refresh_from_db()
        self.assertEqual(self.stock_neutral.condition_label(), "Overbought")

    def test_regression_string_output_stability(self):
        """
        Confirm that __str__() output format remains stable.
        """
        self.assertEqual(str(self.stock_overbought), "AAPL - Overbought")
        self.assertEqual(str(self.stock_oversold), "TSLA - Oversold")
        self.assertEqual(str(self.stock_neutral), "GOOG - Neutral")
        self.assertEqual(str(self.stock_invalid), "MSFT - Unknown")

    def test_regression_missing_fields_handling(self):
        """
        Ensure no crash occurs when optional fields are missing.
        """
        stock = OverBoughtSold.objects.create(symbol=None, rsi="60")
        self.assertEqual(stock.condition_label(), "Neutral")
        self.assertIn("Unknown", str(stock))




class PaymentInformationRegressionTest(TestCase):

    def setUp(self):
        """Set up initial test data"""
        self.payment_data = {
            'payment_fees': 1500,
            'down_payment': 500,
            'student_bonus': 100,
            'fee_balance': 900,
            'plan': "Standard",
            'subplan': "Silver",
            'payment_method': "Mobile Money",
            'contract_submitted_date': timezone.now(),
            'client_signature': "John Doe",
            'company_rep': "Alice M.",
            'client_date': "2025-01-15",
            'description': "First installment for tuition",
            'is_active': True,
            'is_featured': False
        }

    def test_payment_information_creation(self):
        """Test that a PaymentInformation object is correctly created and saved."""
        payment = PaymentInformation.objects.create(**self.payment_data)
        
        # Verify that all fields are saved correctly
        self.assertEqual(payment.payment_fees, 1500)
        self.assertEqual(payment.plan, "Standard")
        self.assertEqual(payment.fee_balance, 900)
        self.assertTrue(payment.is_active)
        self.assertFalse(payment.is_featured)

    def test_invalid_payment_information_creation(self):
        """Test that invalid PaymentInformation data (e.g., missing required fields) raises an error."""
        invalid_data = self.payment_data.copy()
        invalid_data['payment_fees'] = None  # Remove payment_fees to make it invalid
        
        # Assert that creating a PaymentInformation object without a required field (payment_fees) raises an error
        with self.assertRaises(Exception):
            PaymentInformation.objects.create(**invalid_data)
    
    def test_string_representation(self):
        """Test the string representation (__str__) of the model."""
        payment = PaymentInformation.objects.create(**self.payment_data)
        
        # Ensure the string representation is in the correct format
        self.assertEqual(str(payment), "Standard - Mobile Money")

    def test_update_payment_information(self):
        """Test that an existing PaymentInformation object can be updated."""
        payment = PaymentInformation.objects.create(**self.payment_data)
        
        # Update the payment information
        payment.plan = "Premium"
        payment.save()
        
        # Retrieve the updated object
        updated_payment = PaymentInformation.objects.get(id=payment.id)
        
        # Verify that the changes were saved correctly
        self.assertEqual(updated_payment.plan, "Premium")

    def test_delete_payment_information(self):
        """Test that a PaymentInformation object can be deleted."""
        payment = PaymentInformation.objects.create(**self.payment_data)
        
        # Delete the payment information
        payment_id = payment.id
        payment.delete()
        
        # Ensure that the payment information is deleted
        with self.assertRaises(PaymentInformation.DoesNotExist):
            PaymentInformation.objects.get(id=payment_id)

    def test_query_filter(self):
        """Test querying PaymentInformation by filter."""
        PaymentInformation.objects.create(**self.payment_data)
        
        # Query PaymentInformation by a specific field (plan)
        payment = PaymentInformation.objects.filter(plan="Standard").first()
        
        # Verify that the query returned the expected result
        self.assertIsNotNone(payment)
        self.assertEqual(payment.plan, "Standard")

    def test_non_null_constraints(self):
        """Test that fields with non-null constraints are validated."""
        invalid_data = self.payment_data.copy()
        invalid_data['payment_fees'] = None  # payment_fees is a non-null field
        
        with self.assertRaises(Exception):  # Expecting an error since payment_fees is required
            PaymentInformation.objects.create(**invalid_data)
    
    def test_field_defaults(self):
        """Test the default values for fields like is_active and is_featured."""
        payment = PaymentInformation.objects.create(**self.payment_data)
        
        # Ensure that the default values for Boolean fields are correct
        self.assertTrue(payment.is_active)  # Default True
        self.assertFalse(payment.is_featured)  # Default False



# finance/tests/regression/test_regression_models.py
from django.test import TestCase
from django.db import IntegrityError
from finance.models import Default_Payment_Fees

class DefaultPaymentFeesRegressionTest(TestCase):
    
    def setUp(self):
        """Set up initial test data before each test."""
        self.payment_fee = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=500,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=300,
            student_bonus_payment_per_month=150
        )

    def test_default_payment_fees_creation(self):
        """Ensure a Default_Payment_Fees object is created successfully."""
        payment_fee = Default_Payment_Fees.objects.get(id=self.payment_fee.id)
        self.assertEqual(payment_fee.job_down_payment_per_month, 500)
        self.assertEqual(payment_fee.job_plan_hours_per_month, 160)
        self.assertEqual(payment_fee.student_down_payment_per_month, 300)
        self.assertEqual(payment_fee.student_bonus_payment_per_month, 150)

    def test_default_payment_fees_str(self):
        """Ensure the __str__ representation of the object is correct."""
        self.assertEqual(str(self.payment_fee), f"Default Payment Fee {self.payment_fee.id}")

    def test_default_payment_fees_not_null(self):
        """Test NOT NULL constraint: should raise IntegrityError if a required field is NULL."""
        with self.assertRaises(IntegrityError):
            Default_Payment_Fees.objects.create(
                job_down_payment_per_month=None,  # NULL not allowed
                job_plan_hours_per_month=160,
                student_down_payment_per_month=300,
                student_bonus_payment_per_month=150
            )

    def test_field_values(self):
        """Ensure updating a field persists correctly."""
        self.payment_fee.job_down_payment_per_month = 600
        self.payment_fee.save()
        updated_payment_fee = Default_Payment_Fees.objects.get(id=self.payment_fee.id)
        self.assertEqual(updated_payment_fee.job_down_payment_per_month, 600)

    def test_default_payment_fees_count(self):
        """Ensure record count increases correctly when a new object is created."""
        initial_count = Default_Payment_Fees.objects.count()
        Default_Payment_Fees.objects.create(
            job_down_payment_per_month=700,
            job_plan_hours_per_month=180,
            student_down_payment_per_month=400,
            student_bonus_payment_per_month=200
        )
        new_count = Default_Payment_Fees.objects.count()
        self.assertEqual(new_count, initial_count + 1)






from django.core.exceptions import ValidationError


class PayslipConfigRegressionTests(TestCase):
    """
    Regression tests ensure that previously fixed issues DO NOT reappear.
    Add new regression cases anytime a bug is fixed.
    """

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

    def test_decimal_values_do_not_round_or_truncate(self):
        """Ensure decimal precision is preserved."""
        self.assertEqual(self.config.loan_amount, Decimal("100000.00"))
        self.assertEqual(self.config.ls_amount, Decimal("3500.00"))

    def test_boolean_fields_store_correct_values(self):
        """Ensure boolean fields save & load correctly."""
        self.assertTrue(self.config.loan_status)
        self.assertTrue(self.config.laptop_status)

    def test_string_representation_no_crash(self):
        """Ensure __str__ works without errors."""
        s = str(self.config)
        self.assertIn("Loan Status", s)
        self.assertIn("Laptop Status", s)

    def test_no_negative_values_allowed(self):
        """
        Regression Test:
        Ensures negative values raise a ValidationError.
        Note: Django ONLY validates negatives when full_clean() is called.
        """
        invalid_config = PayslipConfig(
            loan_status=True,
            loan_amount=Decimal("-100"),
            loan_repayment_percentage=Decimal("10.00"),
            laptop_status=True,
            lb_amount=Decimal("30000.00"),
            ls_amount=Decimal("3500.00"),
            ls_max_limit=Decimal("40000.00"),
            rp_starting_period="Month 1",
            rp_starting_amount=Decimal("1500.00"),
            rp_increment_percentage=Decimal("5.00"),
        )

        with self.assertRaises(ValidationError):
            invalid_config.full_clean()  # This triggers validators

    def test_required_fields_not_empty(self):
        """Ensure rp_starting_period is not blank."""
        self.assertNotEqual(self.config.rp_starting_period, "")
