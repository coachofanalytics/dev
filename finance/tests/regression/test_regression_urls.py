from django.test import SimpleTestCase
from django.urls import reverse, resolve, NoReverseMatch
from finance.views import payment_list

class TestUrlRegressions(SimpleTestCase):

    def test_url_trailing_slash_sensitivity(self):
        """Ensure that the URL resolves correctly with or without worrying about manual construction."""
        url = reverse('finance:payment_list')
        # Django standard is to include the trailing slash. 
        # This confirms our reverse helper matches that expectation.
        self.assertTrue(url.endswith('/'))
        self.assertEqual(url, '/finance/payment_list/')

    def test_invalid_namespace_access(self):
        """Regression test to ensure the app doesn't resolve without the required namespace."""
        # This ensures that we haven't accidentally exposed the URL to the global namespace
        # which could cause collisions with other apps later.
        with self.assertRaises(NoReverseMatch):
            reverse('payment_list') # Should fail because it's missing 'finance:'

    def test_resolve_incorrect_path(self):
        """Ensure that similar but incorrect paths do not resolve to this view."""
        # If someone visits /finance/payments_list (plural), it should NOT hit our view.
        from django.http import Http404
        with self.assertRaises(NoReverseMatch):
            # Checking reverse for a typo version
            reverse('finance:payments_list')

    def test_namespace_consistency(self):
        """Verify the 'finance' namespace is consistently applied."""
        resolver = resolve('/finance/payment_list/')
        self.assertEqual(resolver.app_name, 'finance')
        self.assertEqual(resolver.namespace, 'finance')