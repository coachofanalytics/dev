from django.test import TestCase
from django.template.loader import render_to_string
from accounts.models import PaymentInformation, CustomerUser,Payment_History
from django.utils import timezone
from django.urls import reverse

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
        html = render_to_string("", {"payments": [self.payment]})
        self.assertIn("Payment Fees", html)
        self.assertIn("Down Payment", html)
        self.assertIn("Bonus", html)
        self.assertIn("Method", html)
        self.assertIn("Actions", html)




class PaymentHistoryTemplateTest(TestCase):
    """✅ Ensure the template renders correctly"""

    def setUp(self):
        self.customer = CustomerUser.objects.create(
            first_name="Chris",
            last_name="Maghas",
            email="chris@example.com",
            is_active=True
        )
        self.payment = Payment_History.objects.create(
            customer=self.customer,
            payment_fees=10000,
            down_payment=500,
            student_bonus=100,
            fee_balance=9400,
            plan=1,
            subplan=1,
            payment_method="Mpesa",
            contract_submitted_date=timezone.now(),
            client_signature="Signed",
            company_rep="Rep 1",
            client_date="2025-01-12",
            rep_date="2025-01-13"
        )
        self.url = reverse('accounts:accounts-paymenthistory_list')

    def test_template_used(self):
        """✅ Check correct template used"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'accounts/Paymenthistory_list_html')

    def test_page_contains_payment_data(self):
        """✅ Template renders payment data properly"""
        response = self.client.get(self.url)
        # self.assertContains(response, "Chris")
        self.assertContains(response, "Mpesa")
        self.assertContains(response, "10000")




class PaymentHistorycreateTemplateTest(TestCase):
    """Ensure the template renders correctly for creating Payment History"""

    def setUp(self):
        """Setup test data"""
        # Create a customer for the payment history
        self.customer = CustomerUser.objects.create(
            first_name="Chris",
            last_name="Maghas",
            email="chris@example.com",
            is_active=True
        )

        # Create a payment history record
        self.payment = Payment_History.objects.create(
            customer=self.customer,
            payment_fees=10000,
            down_payment=500,
            student_bonus=100,
            fee_balance=9400,
            plan=1,
            subplan=1,
            payment_method="Mpesa",
            contract_submitted_date=timezone.now(),
            client_signature="Signed",
            company_rep="Rep 1",
            client_date="2025-01-12",
            rep_date="2025-01-13"
        )
        
        # Define URL for testing the payment history list
        self.url = reverse('accounts:accounts-paymenthistory_list')  # Adjust to the correct URL name

    def test_template_used(self):
        """Test that the correct template is used"""
        response = self.client.get(self.url)
        # Assert that the 'paymenthistory_list.html' template is used
        self.assertTemplateUsed(response, 'accounts/Paymenthistory_list_html')

    def test_page_contains_payment_data(self):
        """Test that the template contains the payment data"""
        response = self.client.get(self.url)

        # Check if certain data exists in the rendered template
        # self.assertContains(response, "Brenda")
        self.assertContains(response, "Mpesa")
        self.assertContains(response, "10000")


