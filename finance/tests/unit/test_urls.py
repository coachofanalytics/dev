from django.test import SimpleTestCase
from django.urls import reverse, resolve
from finance.views import PaymentInformation_list


class TestPaymentInformationURLs(SimpleTestCase):
    """Test URL configuration for PaymentInformation views"""

    def test_paymentinformation_list_url_resolves(self):
        """Ensure the 'paymentinformation_list' URL name resolves to the correct view"""
        url = reverse('paymentinformation_list')
        self.assertEqual(resolve(url).func, PaymentInformation_list)

    def test_paymentinformation_list_url_exists_at_desired_location(self):
        """Ensure /finance/payments/ returns 200 OK"""
        response = self.client.get('/finance/payments/')
        self.assertEqual(response.status_code, 200)
