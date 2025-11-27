from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees


class DefaultPaymentFeesRegressionViews(TestCase):
    """
    Regression tests for Default_Payment_Fees views.
    Ensures existing view behaviors remain stable after future changes.
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
        self.detail_url = reverse("Default_Payment_Fees_detail", kwargs={"pk": self.payment.pk})

    # ---------- LIST VIEW ----------
    def test_regression_list_returns_status_200(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2000")

    # ---------- CREATE VIEW ----------
    def test_regression_create_redirects_on_success(self):
        data = {
            "job_down_payment_per_month": 2500,
            "job_plan_hours_per_month": 180,
            "student_down_payment_per_month": 1700,
            "student_bonus_payment_per_month": 400,
        }
        response = self.client.post(self.create_url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Default_Payment_Fees.objects.count(), 2)
        self.assertRedirects(response, self.list_url)

    # ---------- UPDATE VIEW ----------
    def test_regression_update_modifies_existing_object(self):
        data = {
            "job_down_payment_per_month": 3200,
            "job_plan_hours_per_month": 210,
            "student_down_payment_per_month": 1900,
            "student_bonus_payment_per_month": 600,
        }
        response = self.client.post(self.update_url, data, follow=True)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.job_down_payment_per_month, 3200)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.list_url)

    # ---------- DELETE VIEW ----------
    def test_regression_delete_removes_object(self):
        response = self.client.post(self.delete_url, follow=True)
        self.assertFalse(Default_Payment_Fees.objects.filter(pk=self.payment.pk).exists())
        self.assertRedirects(response, self.list_url)

    # ---------- DETAIL VIEW ----------
    def test_regression_detail_returns_status_200_and_contains_data(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.payment.job_down_payment_per_month))
        self.assertContains(response, str(self.payment.job_plan_hours_per_month))
        self.assertContains(response, str(self.payment.student_down_payment_per_month))
        self.assertContains(response, str(self.payment.student_bonus_payment_per_month))





from django.test import TestCase
from django.urls import reverse
from finance.models import Default_Payment_Fees, PayslipConfig

class TestRegressionViews(TestCase):

    # ================================
    # Regression Test for PayslipConfig List View
    # ================================
    def test_payslip_config_list_view(self):
        """Ensure PayslipConfig list view still works after recent changes."""
        # Create sample data
        PayslipConfig.objects.create(
            loan_status=True,
            loan_amount=2000,
            loan_repayment_percentage=10.00,
            laptop_status=True,
            lb_amount=1200,
            ls_amount=1000,
            ls_max_limit=3000,
            rp_starting_period="6 months",
            rp_starting_amount=100,
            rp_increment_percentage=5.00
        )

        # Send GET request to the view
        url = reverse('payslip_config_list')  # This should match your URL pattern
        response = self.client.get(url)

        # Assert status code
        self.assertEqual(response.status_code, 200)
        # Assert the correct template is used
        self.assertTemplateUsed(response, 'finance/payslips.html')
        # Assert content is rendered correctly
        self.assertContains(response, "2000")
        self.assertContains(response, "5.00")
    
    # ================================
    # Regression Test for Default Payment Fees List View
    # ================================
    def test_default_payment_fees_list_view(self):
        """Ensure Default Payment Fees list view still works after recent changes."""
        # Create sample data
        Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )

        # Send GET request to the view
        url = reverse('Default_Payment_Fees_list')  # This should match your URL pattern
        response = self.client.get(url)

        # Assert status code
        self.assertEqual(response.status_code, 200)
        # Assert the correct template is used
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_list.html')
        # Assert content is rendered correctly
        self.assertContains(response, "2000")
        self.assertContains(response, "1500")
