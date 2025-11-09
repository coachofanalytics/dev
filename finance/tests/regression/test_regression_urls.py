from django.test import SimpleTestCase
from django.urls import reverse, resolve
from finance import views

class DefaultPaymentFeesRegressionURLTest(SimpleTestCase):
    """
    Regression test for Default_Payment_Fees_list URL.
    Ensures URL still resolves to the correct view.
    """

    def test_default_payment_fees_list_url_resolves(self):
        url = reverse('Default_Payment_Fees_list')
        # Adjust the actual path if your app is under /finance/
        self.assertEqual(url, '/finance/Default_Payment_Fees_list/')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.Default_Payment_Fees_list)




from django.test import SimpleTestCase
from django.urls import reverse, resolve
from finance.views import Default_Payment_Fees_list, Default_Payment_Fees_create

class DefaultPaymentFeesRegressionURLs(SimpleTestCase):

    def test_list_url_resolves(self):
        url = reverse('Default_Payment_Fees_list')
        self.assertEqual(resolve(url).func, Default_Payment_Fees_list)

    def test_create_url_resolves(self):
        url = reverse('Default_Payment_Fees_create')
        self.assertEqual(resolve(url).func, Default_Payment_Fees_create)




from django.test import TestCase, Client
from django.urls import reverse

class DefaultPaymentFeesRegressionURLs(TestCase):

    def setUp(self):
        self.client = Client()

    def test_list_url(self):
        url = reverse('Default_Payment_Fees_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_url(self):
        url = reverse('Default_Payment_Fees_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_url(self):
        from finance.models import Default_Payment_Fees
        payment = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )
        url = reverse('Default_Payment_Fees_update', kwargs={'pk': payment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
