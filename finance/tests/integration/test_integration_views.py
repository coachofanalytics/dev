from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees


class DefaultPaymentFeesIntegrationTest(TestCase):
    """
    Integration test for Default_Payment_Fees_list view.
    Checks URL, template rendering, and database integration together.
    """

    def setUp(self):
        self.client = Client()
        # Create multiple payment records
        Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )
        Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2500,
            job_plan_hours_per_month=180,
            student_down_payment_per_month=1700,
            student_bonus_payment_per_month=400
        )

    def test_integration_view_status_code(self):
        """Integration: Ensure view returns 200 OK."""
        url = reverse('Default_Payment_Fees_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_integration_template_used(self):
        """Integration: Correct template is rendered."""
        url = reverse('Default_Payment_Fees_list')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_list.html')

    def test_integration_context_and_data(self):
        """Integration: Context includes payments and data is correct."""
        url = reverse('Default_Payment_Fees_list')
        response = self.client.get(url)
        self.assertIn('payments', response.context)
        self.assertEqual(response.context['payments'].count(), 2)
        self.assertContains(response, "2000")
        self.assertContains(response, "2500")
        self.assertContains(response, "160")
        self.assertContains(response, "180")



from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees

class DefaultPaymentFeesIntegrationTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.list_url = reverse('Default_Payment_Fees_list')
        self.create_url = reverse('Default_Payment_Fees_create')

        # Create sample data
        Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )

    def test_list_view_integration(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2000")
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_list.html')

    def test_create_view_integration(self):
        data = {
            'job_down_payment_per_month': 2500,
            'job_plan_hours_per_month': 180,
            'student_down_payment_per_month': 1700,
            'student_bonus_payment_per_month': 400
        }
        response = self.client.post(self.create_url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2500")
        self.assertEqual(Default_Payment_Fees.objects.count(), 2)
