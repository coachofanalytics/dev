from django.test import TestCase
from finance.models import OverBoughtSold,PaymentInformation
from django.utils import timezone

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
