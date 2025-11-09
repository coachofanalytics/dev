


from django.test import SimpleTestCase
from django.urls import reverse, resolve
from finance import views


class TestDefaultPaymentFeesUrls(SimpleTestCase):

    def test_default_payment_fees_list_reverse(self):
        url = reverse('Default_Payment_Fees_list')
        # ✅ Since your app is included under /finance/
        self.assertEqual(url, '/finance/Default_Payment_Fees_list/')

    def test_default_payment_fees_list_resolves(self):
        resolver = resolve('/finance/Default_Payment_Fees_list/')
        self.assertEqual(resolver.func, views.Default_Payment_Fees_list)


