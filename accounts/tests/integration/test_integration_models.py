# accounts/tests/test_integration_model.py

from django.test import TestCase
from accounts.models import CustomerUser, Payment_Historyy


class PaymentHistoryIntegrationTest(TestCase):

    def test_customer_relationship(self):
        customer = CustomerUser.objects.create(
            username="integration_user",
            email="integration@example.com",
            password="password123"
        )

        Payment_Historyy.objects.create(
            customer=customer,
            payment_fees=3000,
            down_payment=500,
            plan=1,
            payment_method="Mobile Money",
            client_signature="Client",
            company_rep="Rep"
        )

        # Fetch data via reverse relationship
        records = customer.payment_historyy_set.all()

        self.assertEqual(records.count(), 1)
        self.assertEqual(records.first().payment_method, "Mobile Money")
        self.assertEqual(records.first().customer.email, "integration@example.com")
