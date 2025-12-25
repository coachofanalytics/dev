from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from finance.models import PaymentInformation

User = get_user_model()

class PaymentIntegrationTests(TestCase):
    def setUp(self):
        # Setup users
        self.user = User.objects.create_user(username="finance_staff", password="password123")
        self.other_user = User.objects.create_user(username="other_customer", email="other@test.com")
        self.client = Client()
        self.url = reverse("finance:payment_list")

        # Create a mix of data to test complex filtering
        # 5 records for 'finance_staff' using 'PayPal'
        for i in range(5):
            PaymentInformation.objects.create(
                customer=self.user,
                payment_method="PayPal",
                total_fees=100, down_payment=50, remaining_balance=50
            )
        
        # 12 records for 'other_customer' using 'Stripe'
        for i in range(12):
            PaymentInformation.objects.create(
                customer=self.other_user,
                payment_method="Stripe",
                total_fees=200, down_payment=200, remaining_balance=0
            )

    def test_full_search_and_pagination_workflow(self):
        """
        Integration: Search for 'Stripe' (12 results), 
        verify page 1 has 10 items, and page 2 has 2 items.
        """
        self.client.login(username="finance_staff", password="password123")

        # 1. Perform Search
        response = self.client.get(self.url, {"q": "Stripe"})
        self.assertEqual(response.status_code, 200)
        
        # 2. Verify Page 1
        page_1 = response.context["page_obj"]
        self.assertEqual(len(page_1), 10)
        self.assertTrue(page_1.has_next())
        self.assertContains(response, "other_customer")
        self.assertNotContains(response, "PayPal") # PayPal should be filtered out

        # 3. Navigate to Page 2
        response_page_2 = self.client.get(self.url, {"q": "Stripe", "page": 2})
        page_2 = response_page_2.context["page_obj"]
        self.assertEqual(len(page_2), 2)
        self.assertFalse(page_2.has_next())

    def test_search_by_email_integration(self):
        """Integration: Verify searching by user email returns correct joined data."""
        self.client.login(username="finance_staff", password="password123")
        
        # Search by email of the 'other_user'
        response = self.client.get(self.url, {"q": "other@test.com"})
        
        # Should find all 12 'Stripe' records
        self.assertEqual(response.context["page_obj"].paginator.count, 12)
        self.assertContains(response, "Stripe")

    def test_unauthorized_access_interception(self):
        """Integration: Ensure the login_required decorator redirects and then allows access after login."""
        # 1. Try to access without login
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        
        # 2. Login
        self.client.login(username="finance_staff", password="password123")
        
        # 3. Access again
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)