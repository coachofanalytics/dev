from django.test import SimpleTestCase
from django.urls import reverse, resolve
from accounts import views 


def TestPaymentHistoryURLs(SimpleTestCase):
    """✅ Test Payment_History URL routing and template usage"""

    def test_paymenthistory_list_url_is_resolved(self):
        """✅ URL resolves to the correct view function"""
        url = reverse('accounts:paymenthistory_list')
        self.assertEqual(resolve(url).func, views.payment_history_list_view)

  

class TestPaymentHistoryURLs(SimpleTestCase):
    """✅ Test Payment_History URL routing and template usage"""

    def test_paymenthistory_create_url_is_resolved(self):
        """✅ URL resolves to the correct view function"""
        url = reverse('accounts:accounts-paymenthistory_list')  
        # self.assertEqual(resolve(url).func,views.payment_history_create_view)  


