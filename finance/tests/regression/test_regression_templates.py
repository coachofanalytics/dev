from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees


class DefaultPaymentFeesRegressionTemplates(TestCase):
    """
    Regression tests to ensure templates render and contain expected UI text.
    """

    def setUp(self):
        self.client = Client()
        self.payment = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300,
        )
        self.list_url = reverse("Default_Payment_Fees_list")
        self.create_url = reverse("Default_Payment_Fees_create")
        self.update_url = reverse("Default_Payment_Fees_update", kwargs={"pk": self.payment.pk})
        self.delete_url = reverse("Default_Payment_Fees_delete", kwargs={"pk": self.payment.pk})

    # ---------- LIST ----------
    def test_list_template_contains_table_headers(self):
        """Ensure the list template still displays expected table headers"""
        response = self.client.get(self.list_url)
        self.assertTemplateUsed(response, "finance/Default_Payment_Fees_list.html")
        self.assertContains(response, "job_down_payment_per_month")
        self.assertContains(response, "student_bonus_payment_per_month")

    # ---------- CREATE ----------
    def test_create_template_contains_form_fields(self):
        """Ensure create template still shows correct input fields"""
        response = self.client.get(self.create_url)
        self.assertTemplateUsed(response, "finance/Default_Payment_Fees_create.html")
        self.assertContains(response, "job_down_payment_per_month")
        self.assertContains(response, "student_down_payment_per_month")

    # ---------- UPDATE ----------
    def test_update_template_contains_existing_values(self):
        """Ensure update template still preloads object data"""
        response = self.client.get(self.update_url)
        self.assertTemplateUsed(response, "finance/Default_Payment_Fees_update.html")
        self.assertContains(response, "2000")
        self.assertContains(response, "160")

    # ---------- DELETE ----------
    def test_delete_template_displays_confirmation_text(self):
        """Ensure delete confirmation page displays expected message"""
        response = self.client.get(self.delete_url)
        self.assertTemplateUsed(response, "finance/Default_Payment_Fees_delete.html")
        self.assertContains(response, "Are you sure")
        self.assertContains(response, "Delete")
