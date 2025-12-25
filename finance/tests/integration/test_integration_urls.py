from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class PaymentURLIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="url_tester", password="password123")
        self.client = Client()
        self.url = reverse("finance:payment_list")

    def test_payment_list_route_delivery(self):
        """
        Integration: Test the full trip from URL to View to Template.
        Checks that the URL actually delivers a 200 OK with the right content.
        """
        self.client.login(username="url_tester", password="password123")
        response = self.client.get(self.url)
        
        # Verify the route successfully reached the view and returned the correct template
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Payment Information")

    def test_url_query_parameter_integration(self):
        """
        Integration: Verify that the URL router correctly passes GET parameters 
        to the view logic.
        """
        self.client.login(username="url_tester", password="password123")
        # Access URL with complex query params
        response = self.client.get(self.url, {"q": "visa", "page": "1"})
        
        self.assertEqual(response.status_code, 200)
        # Verify the view received 'q' and passed it back to the template context
        self.assertEqual(response.context["q"], "visa")

    def test_login_redirect_integration(self):
        """
        Integration: Verify that the URL routing interacts correctly with 
        the Authentication Middleware.
        """
        # No login performed
        response = self.client.get(self.url, follow=True)
        
        # Verify that the URL routing logic and middleware collaborated 
        # to land the user on the login page.
        last_url, status_code = response.redirect_chain[-1]
        self.assertIn("login", last_url)
        self.assertEqual(status_code, 302)