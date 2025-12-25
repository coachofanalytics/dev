

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from finance.models import PaymentInformation

User = get_user_model()

class PaymentRegressionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reg_user", password="password123")
        self.client = Client()
        self.client.login(username="reg_user", password="password123")
        # Ensure this matches your finance app's URL name
        self.url = reverse("finance:payment_list")

    def test_search_with_special_characters(self):
        """Ensure search doesn't crash with special characters."""
        PaymentInformation.objects.create(
            customer=self.user,
            payment_method="Visa' OR '1'='1", 
            total_fees=100, down_payment=50, remaining_balance=50
        )
        special_chars = ["'", ";", "%", "--"]
        for char in special_chars:
            response = self.client.get(self.url, {"q": char})
            self.assertEqual(response.status_code, 200)

    def test_empty_search_query_whitespace(self):
        """Ensure whitespace-only search is treated as empty."""
        PaymentInformation.objects.create(
            customer=self.user, payment_method="Cash",
            total_fees=100, down_payment=100, remaining_balance=0
        )
        response = self.client.get(self.url, {"q": "   "}) 
        self.assertEqual(len(response.context["page_obj"]), 1)

    def test_page_zero_or_negative(self):
        """
        Verify that page=0 or negative numbers are handled.
        Your view logic returns the LAST page for EmptyPage/Out of range.
        """
        # Create 12 records = 2 pages (10 per page)
        for i in range(12):
            PaymentInformation.objects.create(
                customer=self.user, payment_method="Test",
                total_fees=10, down_payment=5, remaining_balance=5
            )
        
        # Testing page 0 (Paginator treats this as EmptyPage)
        response_zero = self.client.get(self.url, {"page": "0"})
        # Your view logic: except EmptyPage -> return paginator.num_pages (which is 2)
        self.assertEqual(response_zero.context["page_obj"].number, 2)
        
        # Testing negative page (Paginator treats this as EmptyPage)
        response_neg = self.client.get(self.url, {"page": "-1"})
        self.assertEqual(response_neg.context["page_obj"].number, 2)

    def test_page_not_an_integer(self):
        """Verify that non-integers return the FIRST page per your view logic."""
        response = self.client.get(self.url, {"page": "abc"})
        # Your view logic: except PageNotAnInteger -> return page 1
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_extremely_long_search_query(self):
        """Ensure very long strings don't cause a 500 error."""
        long_query = "a" * 1000
        response = self.client.get(self.url, {"q": long_query})
        self.assertEqual(response.status_code, 200)