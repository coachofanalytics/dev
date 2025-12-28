# accounts/tests/test_integration_model.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Payment_History

User = get_user_model()


class PaymentHistoryIntegrationTest(TestCase):

    def test_user_payment_history_relationship(self):
        user = User.objects.create_user(
            username="integrationuser",
            email="integration@example.com",
            password="password123"
        )

        Payment_History.objects.create(
            customer=user,
            payment_fees=4000,
            down_payment=500,
            plan=1,
            payment_method="Card",
            client_signature="Client",
            company_rep="Company"
        )

        self.assertEqual(user.payment_history.count(), 1)
