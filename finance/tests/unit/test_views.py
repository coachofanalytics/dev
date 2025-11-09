from django.test import TestCase, Client
from django.urls import reverse
from finance.models import PaymentInformation
from django.utils import timezone


class PaymentInformationListViewTest(TestCase):
    """Tests for the PaymentInformation list view"""

    def setUp(self):
        """Create test data"""
        self.client = Client()
        self.url = reverse('paymentinformation_list')  # adjust to your URL name

        # Create sample PaymentInformation records
        self.payment1 = PaymentInformation.objects.create(
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

        self.payment2 = PaymentInformation.objects.create(
            payment_fees=2000,
            down_payment=800,
            student_bonus=200,
            fee_balance=1000,
            plan="Premium",
            subplan="Gold",
            payment_method="PayPal",
            contract_submitted_date=timezone.now(),
            client_signature="Mary K.",
            company_rep="Robert O.",
            client_date="2025-02-10",
            description="Payment for data analysis course",
            is_active=True,
            is_featured=True
        )

    def test_view_url_exists(self):
        """Ensure the URL is reachable"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        """Ensure the view uses the correct template"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'finance/payments_information.html')

    def test_view_returns_all_payments(self):
        """Ensure the context contains all PaymentInformation records"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        payments = response.context['payments']
        self.assertEqual(len(payments), 2)
        self.assertIn(self.payment1, payments)
        self.assertIn(self.payment2, payments)

    def test_view_displays_payment_data(self):
        """Ensure payment data is rendered in the response"""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')
        self.assertIn("Standard", content)
        self.assertIn("Premium", content)
        self.assertIn("Mobile Money", content)
        self.assertIn("PayPal", content)
