from django.test import SimpleTestCase
from django.urls import reverse, resolve
from finance.views import payment_list

class TestUrls(SimpleTestCase):

    def test_payment_list_url_is_resolved(self):
        """
        Verify that the 'finance:payment_list' URL name resolves 
        to the correct payment_list view function.
        """
        # Reverse the name to get the path
        url = reverse('finance:payment_list')
        
        # Resolve the path back to the view
        resolved_view = resolve(url)
        
        # Check if the resolved function is our actual view function
        self.assertEqual(resolved_view.func, payment_list)

    def test_payment_list_url_name_is_correct(self):
        """
        Verify that the URL path matches the expected prefixed path.
        """
        url = reverse('finance:payment_list')
        
        # We updated this to include the '/finance/' prefix discovered in your error
        self.assertEqual(url, '/finance/payment_list/')