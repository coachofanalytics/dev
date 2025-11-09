from django.test import TestCase
from django.urls import reverse
from finance.models import PaymentInformation
from django.utils import timezone


class PaymentInformationTemplateTest(TestCase):
    """Tests to ensure PaymentInformation_list renders the correct template and data"""

    def setUp(self):
        """Create sample payment data"""
        self.url = reverse('paymentinformation_list')

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

    def test_template_used(self):
        """Check that the correct template is used"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'finance/payments_information.html')

    def test_template_displays_payment_data(self):
        """Check that the template displays key payment fields"""
        response = self.client.get(self.url)
        html = response.content.decode('utf-8')

        # Check for presence of key text values in rendered HTML
        self.assertIn("Standard", html)
        self.assertIn("Silver", html)
        self.assertIn("Mobile Money", html)
        self.assertIn("John Doe", html)
        self.assertIn("Alice M.", html)
        self.assertIn("First installment for tuition", html)

    def test_context_contains_payments(self):
        """Ensure 'payments' is included in context data"""
        response = self.client.get(self.url)
        self.assertIn('payments', response.context)
        self.assertEqual(len(response.context['payments']), 1)
        self.assertEqual(response.context['payments'][0].plan, 'Standard')

    def test_empty_template_message(self):
        """Test that template displays correct message when there are no payments"""
        # Delete existing data to simulate empty state
        PaymentInformation.objects.all().delete()
        response = self.client.get(self.url)
        html = response.content.decode('utf-8')
        self.assertIn("No payment records available", html)
