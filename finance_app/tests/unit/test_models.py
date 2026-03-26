from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
from finance_app.models import PaymentInformation


User = get_user_model()


class PaymentInformationModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass"
        )

    def get_datetime(self):
        return timezone.make_aware(datetime(2026, 3, 20, 10, 30))

    def test_payment_creation(self):
        payment = PaymentInformation.objects.create(
            user=self.user,
            payment_fees=50000,
            down_payment=20000,
            student_bonus=5000,
            plan=1,
            subplan=101,
            pricing_plan="A",
            payment_method="MPESA",
            contract_submitted_date=self.get_datetime(),
            client_signature="John Doe",
            company_rep="Brenda",
            client_date="2026-03-20"
        )

        self.assertEqual(payment.payment_fees, 50000)
        self.assertEqual(payment.down_payment, 20000)

    def test_fee_balance_calculation(self):
        payment = PaymentInformation.objects.create(
            user=self.user,
            payment_fees=50000,
            down_payment=20000,
            student_bonus=5000,
            plan=1,
            pricing_plan="A",
            payment_method="MPESA",
            contract_submitted_date=self.get_datetime(),
            client_signature="John Doe",
            company_rep="Brenda",
            client_date="2026-03-20"
        )

        self.assertEqual(payment.fee_balance, 25000)

    def test_string_representation(self):
        payment = PaymentInformation.objects.create(
            user=self.user,
            payment_fees=40000,
            down_payment=10000,
            plan=1,
            pricing_plan="A",
            payment_method="MPESA",
            contract_submitted_date=self.get_datetime(),
            client_signature="John Doe",
            company_rep="Brenda",
            client_date="2026-03-20"
        )

        self.assertIn("Payment", str(payment))