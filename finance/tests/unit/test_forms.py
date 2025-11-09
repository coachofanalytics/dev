from django.test import TestCase
from finance.forms import Default_Payment_Fees_form
from finance.models import Default_Payment_Fees

class DefaultPaymentFeesFormTest(TestCase):

    def test_form_valid_data(self):
        """Form should be valid when all required fields are provided"""
        form_data = {
            'job_down_payment_per_month': 2000,
            'job_plan_hours_per_month': 160,
            'student_down_payment_per_month': 1500,
            'student_bonus_payment_per_month': 300
        }
        form = Default_Payment_Fees_form(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_missing_required_field(self):
        """Form should be invalid if a required field is missing"""
        form_data = {
            'job_down_payment_per_month': '',  # Missing required field
            'job_plan_hours_per_month': 160,
            'student_down_payment_per_month': 1500,
            'student_bonus_payment_per_month': 300
        }
        form = Default_Payment_Fees_form(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('job_down_payment_per_month', form.errors)

    def test_form_save_creates_object(self):
        """Saving the form should create a Default_Payment_Fees object"""
        form_data = {
            'job_down_payment_per_month': 2200,
            'job_plan_hours_per_month': 170,
            'student_down_payment_per_month': 1600,
            'student_bonus_payment_per_month': 350
        }
        form = Default_Payment_Fees_form(data=form_data)
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertIsInstance(obj, Default_Payment_Fees)
        self.assertEqual(obj.job_down_payment_per_month, 2200)
        self.assertEqual(obj.student_bonus_payment_per_month, 350)
