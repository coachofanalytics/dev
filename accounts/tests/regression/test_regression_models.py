# accounts/tests/test_regression_model.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Payment_History

User = get_user_model()


class PaymentHistoryRegressionTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="regressionuser",
            email="regression@example.com",
            password="password123"
        )

    def test_updating_bonus_recalculates_balance(self):
        payment = Payment_History.objects.create(
            customer=self.user,
            payment_fees=6000,
            down_payment=1000,
            plan=1,
            payment_method="Cash",
            client_signature="Client",
            company_rep="Company"
        )

        payment.student_bonus = 2000
        payment.save()

        self.assertEqual(payment.fee_balance, 3000)

    def test_updating_down_payment_recalculates_balance(self):
        payment = Payment_History.objects.create(
            customer=self.user,
            payment_fees=6000,
            down_payment=1000,
            plan=1,
            payment_method="Cash",
            client_signature="Client",
            company_rep="Company"
        )

        payment.down_payment = 2000
        payment.save()

        self.assertEqual(payment.fee_balance, 4000)
