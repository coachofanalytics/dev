from django.test import SimpleTestCase, TestCase, Client
from django.urls import reverse, resolve
from finance.views import (
    Default_Payment_Fees_list,
    Default_Payment_Fees_create,
    Default_Payment_Fees_update,
    Default_Payment_Fees_delete,
    Default_Payment_Fees_detail,
)
from finance.models import Default_Payment_Fees


class DefaultPaymentFeesRegressionURLResolution(SimpleTestCase):
    """
    Regression tests to ensure URL names still resolve to the correct views.
    """

    def test_list_url_resolves_correctly(self):
        url = reverse("Default_Payment_Fees_list")
        resolver = resolve(url)
        self.assertEqual(resolver.func, Default_Payment_Fees_list)

    def test_create_url_resolves_correctly(self):
        url = reverse("Default_Payment_Fees_create")
        resolver = resolve(url)
        self.assertEqual(resolver.func, Default_Payment_Fees_create)

    def test_update_url_resolves_correctly(self):
        url = reverse("Default_Payment_Fees_update", kwargs={"pk": 1})
        resolver = resolve(url)
        self.assertEqual(resolver.func, Default_Payment_Fees_update)

    def test_delete_url_resolves_correctly(self):
        url = reverse("Default_Payment_Fees_delete", kwargs={"pk": 1})
        resolver = resolve(url)
        self.assertEqual(resolver.func, Default_Payment_Fees_delete)

    def test_detail_url_resolves_correctly(self):
        url = reverse("Default_Payment_Fees_detail", kwargs={"pk": 1})
        resolver = resolve(url)
        self.assertEqual(resolver.func, Default_Payment_Fees_detail)


class DefaultPaymentFeesRegressionURLResponses(TestCase):
    """
    Regression tests to ensure URLs still return expected HTTP responses.
    """

    def setUp(self):
        self.client = Client()
        # Create a dummy object to use in update/delete/detail tests
        self.payment = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300,
        )

    def test_list_url_returns_200(self):
        url = reverse("Default_Payment_Fees_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_url_returns_200(self):
        url = reverse("Default_Payment_Fees_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_url_returns_200(self):
        url = reverse("Default_Payment_Fees_update", kwargs={"pk": self.payment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_url_returns_200(self):
        url = reverse("Default_Payment_Fees_delete", kwargs={"pk": self.payment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_detail_url_returns_200_and_contains_data(self):
        url = reverse("Default_Payment_Fees_detail", kwargs={"pk": self.payment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Ensure the response contains the payment data
        self.assertContains(response, str(self.payment.job_down_payment_per_month))
        self.assertContains(response, str(self.payment.job_plan_hours_per_month))
        self.assertContains(response, str(self.payment.student_down_payment_per_month))
        self.assertContains(response, str(self.payment.student_bonus_payment_per_month))
