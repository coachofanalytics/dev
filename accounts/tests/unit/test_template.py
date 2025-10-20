from django.test import TestCase
from django.template.loader import render_to_string
from accounts.models import PaymentInformation, CustomerUser
from django.utils import timezone

class PaymentInformationTemplateTest(TestCase):
    """✅ Ensures the list template renders correctly"""

    def setUp(self):
        self.customer = CustomerUser.objects.create(
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com"
        )
        self.payment = PaymentInformation.objects.create(
            customer_id=self.customer,
            payment_fees=5000.00,
            down_payment=500.00,
            student_bonus=100.00,
            plan=1,
            payment_method="Cheque",
            contract_submitted_date=timezone.now(),
            client_signature="Signed",
            company_rep="Admin"
        )

    def test_template_contains_expected_fields(self):
        """✅ Checks that template has table headers"""
        html = render_to_string("accounts/paymentinformation_list.html", {"payments": [self.payment]})
        self.assertIn("Payment Fees", html)
        self.assertIn("Down Payment", html)
        self.assertIn("Bonus", html)
        self.assertIn("Method", html)
        self.assertIn("Actions", html)
