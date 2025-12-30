# accounts/tests/test_regression_model.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Payment_History
from django.utils import timezone

from accounts.models import LoginHistory
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




User = get_user_model()


class LoginHistoryRegressionTest(TestCase):
    """
    Regression tests ensure existing model behavior
    does not change unintentionally.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="regression_user",
            email="regression@test.com",
            password="password123"
        )

    def test_login_history_can_be_created_with_minimum_fields(self):
        """
        Regression: model must allow creation with only `user`
        """
        history = LoginHistory.objects.create(user=self.user)

        self.assertIsNotNone(history.id)
        self.assertEqual(history.user, self.user)

    def test_ip_address_and_user_agent_are_optional(self):
        """
        Regression: nullable fields must remain optional
        """
        history = LoginHistory.objects.create(
            user=self.user,
            ip_address=None,
            user_agent=None
        )

        self.assertIsNone(history.ip_address)
        self.assertIsNone(history.user_agent)

    def test_login_time_default_is_set(self):
        """
        Regression: login_time must auto-populate
        """
        history = LoginHistory.objects.create(user=self.user)

        self.assertIsNotNone(history.login_time)
        self.assertLessEqual(history.login_time, timezone.now())

    def test_ordering_is_descending_by_login_time(self):
        """
        Regression: ordering must remain newest first
        """
        first = LoginHistory.objects.create(
            user=self.user,
            login_time=timezone.now() - timezone.timedelta(minutes=30)
        )
        second = LoginHistory.objects.create(user=self.user)

        logs = list(LoginHistory.objects.all())
        self.assertEqual(logs[0], second)
        self.assertEqual(logs[1], first)

    def test_string_representation_format_is_unchanged(self):
        """
        Regression: __str__ format should not change
        """
        history = LoginHistory.objects.create(user=self.user)
        value = str(history)

        self.assertIn("logged in at", value)
        self.assertIn(str(self.user), value)
