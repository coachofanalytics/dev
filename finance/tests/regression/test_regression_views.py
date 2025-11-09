from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees

class DefaultPaymentFeesRegressionViewTest(TestCase):
    """
    Regression test for Default_Payment_Fees_list view.
    Ensures view continues to work correctly after changes.
    """

    def setUp(self):
        self.client = Client()
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

    def test_view_status_code(self):
        url = reverse('Default_Payment_Fees_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        url = reverse('Default_Payment_Fees_list')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_list.html')

    def test_view_context_data(self):
        url = reverse('Default_Payment_Fees_list')
        response = self.client.get(url)
        self.assertIn('payments', response.context)
        self.assertEqual(response.context['payments'].count(), 2)




from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees

class DefaultPaymentFeesRegressionViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.list_url = reverse('Default_Payment_Fees_list')
        self.create_url = reverse('Default_Payment_Fees_create')

        # Seed initial data
        Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )

    def test_list_view_regression(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2000")

    def test_create_view_regression(self):
        data = {
            'job_down_payment_per_month': 2500,
            'job_plan_hours_per_month': 180,
            'student_down_payment_per_month': 1700,
            'student_bonus_payment_per_month': 400
        }
        response = self.client.post(self.create_url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Default_Payment_Fees.objects.count(), 2)
        self.assertContains(response, "2500")





from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees
from finance.forms import Default_Payment_Fees_form
from django.contrib.messages import get_messages

class DefaultPaymentFeesRegressionViews(TestCase):

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

    def test_list_view(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('payments', response.context)

    def test_create_view(self):
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
        self.assertEqual(str(messages[0]), 'Default_Payment_Fees successfully')

    def test_update_view(self):
        data = {
            'job_down_payment_per_month': 3000,
            'job_plan_hours_per_month': 170,
            'student_down_payment_per_month': 1600,
            'student_bonus_payment_per_month': 350
        }
        response = self.client.post(self.update_url, data, follow=True)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.job_down_payment_per_month, 3000)
        self.assertRedirects(response, self.list_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Default_Payment_Fees successfully')
