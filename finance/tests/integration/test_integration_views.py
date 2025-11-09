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




from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees
from django.contrib.messages import get_messages

class DefaultPaymentFeesIntegrationTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        # Create an initial payment object
        self.payment = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )
        # URLs
        self.list_url = reverse('Default_Payment_Fees_list')
        self.create_url = reverse('Default_Payment_Fees_create')
        self.update_url = reverse('Default_Payment_Fees_update', kwargs={'pk': self.payment.pk})

    # -------- List View --------
    def test_list_view_displays_payments(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.payment.job_down_payment_per_month)
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_list.html')

    # -------- Create View --------
    def test_create_view_post_valid_data(self):
        data = {
            'job_down_payment_per_month': 2500,
            'job_plan_hours_per_month': 180,
            'student_down_payment_per_month': 1700,
            'student_bonus_payment_per_month': 400
        }
        response = self.client.post(self.create_url, data, follow=True)
        self.assertEqual(Default_Payment_Fees.objects.count(), 2)  # initial + new
        new_payment = Default_Payment_Fees.objects.last()
        self.assertEqual(new_payment.job_down_payment_per_month, 2500)
        self.assertRedirects(response, self.list_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Default_Payment_Fees successfully')

    # -------- Update View --------
    def test_update_view_post_valid_data(self):
        data = {
            'job_down_payment_per_month': 3000,
            'job_plan_hours_per_month': 200,
            'student_down_payment_per_month': 1800,
            'student_bonus_payment_per_month': 500
        }
        response = self.client.post(self.update_url, data, follow=True)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.job_down_payment_per_month, 3000)
        self.assertEqual(self.payment.job_plan_hours_per_month, 200)
        self.assertRedirects(response, self.list_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Default_Payment_Fees successfully')
