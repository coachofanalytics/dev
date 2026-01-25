from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from finance.models import Default_Payment_Fees


class DefaultPaymentFeesIntegrationTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.payment = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )
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
        self.assertEqual(Default_Payment_Fees.objects.count(), 2)
        self.assertRedirects(response, self.list_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("successfully" in str(m) for m in messages))

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
        self.assertTrue(any("successfully" in str(m) for m in messages))

    # -------- Delete View --------
    def test_delete_view_deletes_payment_and_redirects(self):
        delete_url = reverse('Default_Payment_Fees_delete', kwargs={'pk': self.payment.pk})
        self.assertTrue(Default_Payment_Fees.objects.filter(pk=self.payment.pk).exists())
        response = self.client.post(delete_url, follow=True)
        self.assertFalse(Default_Payment_Fees.objects.filter(pk=self.payment.pk).exists())
        self.assertRedirects(response, self.list_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Delete successfully" in str(m) for m in messages))





from django.test import TestCase
from django.urls import reverse

class DefaultPaymentFeesViewTest(TestCase):

    def test_default_payment_fees_list_view(self):
        """Test if the Default Payment Fees list view works correctly."""
        url = reverse('Default_Payment_Fees_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_list.html')
