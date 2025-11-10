from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees


class DefaultPaymentFeesTemplateIntegrationTest(TestCase):
    """
    Integration tests to ensure all Default_Payment_Fees templates render correctly.
    """

    def setUp(self):
        self.client = Client()
        # Create a sample object for update and delete views
        self.payment = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )
        self.list_url = reverse("Default_Payment_Fees_list")
        self.create_url = reverse("Default_Payment_Fees_create")
        self.update_url = reverse("Default_Payment_Fees_update", kwargs={"pk": self.payment.pk})
        self.delete_url = reverse("Default_Payment_Fees_delete", kwargs={"pk": self.payment.pk})

    def test_list_view_uses_correct_template(self):
        response = self.client.get(self.list_url)
        self.assertTemplateUsed(response, "finance/Default_Payment_Fees_list.html")

    def test_create_view_uses_correct_template(self):
        response = self.client.get(self.create_url)
        self.assertTemplateUsed(response, "finance/Default_Payment_Fees_create.html")

    def test_update_view_uses_correct_template(self):
        response = self.client.get(self.update_url)
        self.assertTemplateUsed(response, "finance/Default_Payment_Fees_update.html")

    def test_delete_view_uses_correct_template(self):
        response = self.client.get(self.delete_url)
        self.assertTemplateUsed(response, "finance/Default_Payment_Fees_delete.html")
