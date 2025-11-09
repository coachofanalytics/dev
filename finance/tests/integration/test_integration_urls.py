from django.test import SimpleTestCase
from django.urls import reverse, resolve
from finance import views


class DefaultPaymentFeesIntegrationURLs(SimpleTestCase):
    """
    Integration test for URLs in the finance app.
    Ensures URL patterns resolve to the correct views.
    """

    def test_default_payment_fees_list_url_resolves(self):
        url = reverse('Default_Payment_Fees_list')
        # Adjust the actual path if your app is included under /finance/
        self.assertEqual(url, '/finance/Default_Payment_Fees_list/')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.Default_Payment_Fees_list)

    # Add more integration URL tests here if you have other views
    # Example:
    # def test_paymentinformation_list_url_resolves(self):
    #     url = reverse('paymentinformation_list')
    #     self.assertEqual(url, '/finance/payments/')
    #     resolver = resolve(url)
    #     self.assertEqual(resolver.func, views.paymentinformation_list)
