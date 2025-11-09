


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


from django.test import SimpleTestCase
from django.urls import reverse, resolve
from finance.views import Default_Payment_Fees_list, Default_Payment_Fees_create

class TestDefaultPaymentFeesURLs(SimpleTestCase):

    def test_default_payment_fees_list_url_resolves(self):
        url = reverse('Default_Payment_Fees_list')
        self.assertEqual(resolve(url).func, Default_Payment_Fees_list)

    def test_default_payment_fees_create_url_resolves(self):
        url = reverse('Default_Payment_Fees_create')
        self.assertEqual(resolve(url).func, Default_Payment_Fees_create)

    def test_default_payment_fees_list_url_matches_expected_path(self):
        url = reverse('Default_Payment_Fees_list')
        self.assertEqual(url, '/Default_Payment_Fees_list/')

    def test_default_payment_fees_create_url_matches_expected_path(self):
        url = reverse('Default_Payment_Fees_create')
        self.assertEqual(url, '/Default_Payment_Fees_create/')



from django.test import SimpleTestCase
from django.urls import reverse, resolve
from finance.views import Default_Payment_Fees_update

class DefaultPaymentFeesURLsTest(SimpleTestCase):

    def test_update_url_resolves(self):
        url = reverse('Default_Payment_Fees_update', kwargs={'pk': 1})
        self.assertEqual(resolve(url).func, Default_Payment_Fees_update)
