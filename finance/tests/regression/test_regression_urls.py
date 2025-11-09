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
