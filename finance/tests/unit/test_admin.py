from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model  # Get the custom user model
from accounts.models import CustomerUser  # Import your custom user model
from finance.models import PaymentInformation, OverBoughtSold
from decimal import Decimal
from django.utils import timezone


class AdminTestCase(TestCase):
    def setUp(self):
        """
        This method sets up the test environment by creating necessary test data
        for admin testing.
        """
        # Create a superuser using the custom user model (CustomerUser)
        self.superuser = CustomerUser.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password"
        )
        
        # Create a test customer user
        self.customer = CustomerUser.objects.create(
            username="brenda",
            email="brenda@example.com"
        )

        # Create a PaymentInformation instance
        self.payment_info = PaymentInformation.objects.create(
            customer=self.customer,
            total_fees=Decimal('6000.00'),
            down_payment=Decimal('0.00'),
            student_bonus=Decimal('0.00'),
            payment_method="Cash",
            contract_submitted_date=timezone.now(),
            is_active=True,
            is_tested=False,
            is_reviewed=False
        )

        # Create an OverBoughtSold instance
        self.stock = OverBoughtSold.objects.create(
            symbol="AAPL",
            description="Apple Inc.",
            last=145.30,
            volume=50000,
            RSI=75.0,
            EPS=5.50,
            PE=28.0,
            rank="Top Performer",
            profit_margins=22.5,
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

    def test_payment_information_admin(self):
        """
        Test if the PaymentInformation model is accessible in the admin interface.
        """
        self.client.login(username="admin", password="password")
        url = reverse("admin:finance_paymentinformation_changelist")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Check if the header contains 'Payment Information'
        self.assertContains(response, "Payment Information")

        # Check if the customer name appears in the list view
        self.assertContains(response, self.customer.username)
        self.assertContains(response, str(self.payment_info.total_fees))

    def test_payment_information_change_view(self):
        """
        Test if the change view for PaymentInformation is working.
        """
        self.client.login(username="admin", password="password")
        url = reverse("admin:finance_paymentinformation_change", args=[self.payment_info.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Change payment information")  # Update this as per actual page content
