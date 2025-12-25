from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from finance.models import PaymentInformation 

User = get_user_model()

class PaymentListViewTests(TestCase):
    def setUp(self):
        # 1. Create a test user
        self.user = User.objects.create_user(
            username="testuser", 
            password="password123", 
            email="test@example.com"
        )
        self.client = Client()
        
        # FIX: Added 'finance:' namespace to the URL name
        self.url = reverse("finance:payment_list")

        # 2. Create 15 payment records (to test pagination and search)
        for i in range(15):
            PaymentInformation.objects.create(
                customer=self.user,
                payment_method=f"Method {i}",
                total_fees=1000,
                down_payment=500,
                remaining_balance=500
            )

    def test_redirect_if_not_logged_in(self):
        """Verify that unauthenticated users are redirected to login."""
        response = self.client.get(self.url)
        # We check status 302 (Redirect) instead of a hardcoded path 
        # to avoid failures if your LOGIN_URL differs from the default.
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_view_accessible_logged_in(self):
        """Verify the page loads successfully for logged-in users."""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "finance/payment_list.html")

    def test_search_by_username(self):
        """Test search filter for usernames."""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.url, {"q": "testuser"})
        # Should show 10 items (Page 1 limit)
        self.assertEqual(len(response.context["page_obj"]), 10)
        # Should find 15 total items in the paginator
        self.assertEqual(response.context["page_obj"].paginator.count, 15)

    def test_search_by_payment_method(self):
        """Test search filter for payment method."""
        self.client.login(username="testuser", password="password123")
        # Search for 'Method 1' which matches 'Method 1', 'Method 10', 'Method 11', etc.
        response = self.client.get(self.url, {"q": "Method 1"})
        self.assertGreaterEqual(response.context["page_obj"].paginator.count, 6)

    def test_pagination_limit(self):
        """Verify 10 items per page limit."""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_pagination_invalid_page(self):
        """Verify invalid page returns page 1."""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.url, {"page": "abc"})
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_pagination_out_of_range(self):
        """Verify out of range page returns the last page."""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.url, {"page": "999"})
        last_page = response.context["page_obj"].paginator.num_pages
        self.assertEqual(response.context["page_obj"].number, last_page)

    def test_empty_search_results(self):
        """Verify display when no matches found."""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.url, {"q": "nonexistent_query_xyz"})
        self.assertEqual(len(response.context["page_obj"]), 0)
        self.assertContains(response, "No payment records found.")