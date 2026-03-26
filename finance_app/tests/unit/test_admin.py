from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from finance_app.models import PaymentInformation
# from finance_app.admin import PaymentInformationAdmin


User = get_user_model()


class MockRequest:
    pass


class PaymentInformationAdminTest(TestCase):

    def setUp(self):
        self.site = AdminSite()
        # self.admin = PaymentInformationAdmin(PaymentInformation, self.site)

        self.user = User.objects.create_user(
            username="admin",
            password="adminpass"
        )

        self.payment = PaymentInformation.objects.create(
            user=self.user,
            payment_fees=50000,
            down_payment=20000,
            student_bonus=5000,
            plan=1,
            pricing_plan="A",
            payment_method="MPESA",
            contract_submitted_date="2026-03-20T10:30:00",
            client_signature="John Doe",
            company_rep="Brenda",
            client_date="2026-03-20"
        )

    def test_admin_display(self):
        self.assertEqual(self.payment.payment_fees, 50000)

    def test_admin_queryset(self):
        request = MockRequest()
        # queryset = self.admin.get_queryset(request)
        # self.assertEqual(queryset.count(), 1)