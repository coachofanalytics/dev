from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from finance.models import PaymentInformation

User = get_user_model()

class PaymentTemplateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tempuser", password="password123")
        self.client = Client()
        self.client.login(username="tempuser", password="password123")
        self.url = reverse("finance:payment_list")

    def test_template_structure(self):
        """Verify essential UI elements are present in the HTML."""
        response = self.client.get(self.url)
        
        # Check for page title and header
        self.assertContains(response, "<h2>Payment Information</h2>")
        
        # Check for the search form and input name
        self.assertContains(response, '<form method="get"')
        self.assertContains(response, 'name="q"')
        
        # Check for table headers
        self.assertContains(response, "<th>Customer</th>")
        self.assertContains(response, "<th>Status</th>")

    def test_status_badge_logic_rendering(self):
        """Verify that 'Pending' and 'Paid' badges render based on balance."""
        # 1. Create a Pending payment (balance > 0)
        PaymentInformation.objects.create(
            customer=self.user,
            payment_method="Visa",
            total_fees=1000,
            down_payment=200,
            remaining_balance=800
        )
        # 2. Create a Paid payment (balance = 0)
        PaymentInformation.objects.create(
            customer=self.user,
            payment_method="Cash",
            total_fees=500,
            down_payment=500,
            remaining_balance=0
        )

        response = self.client.get(self.url)

        # Check for correct Bootstrap classes and labels
        self.assertContains(response, '<span class="badge bg-warning">Pending</span>')
        self.assertContains(response, '<span class="badge bg-success">Paid</span>')

    def test_empty_state_rendering(self):
        """Verify that the empty state message shows when no records exist."""
        # Clear any existing records
        PaymentInformation.objects.all().delete()
        
        response = self.client.get(self.url)
        self.assertContains(response, "No payment records found.")

    def test_pagination_links_contain_query(self):
        """Verify that pagination links preserve the search query 'q'."""
        # Create enough records to trigger pagination
        for i in range(15):
            PaymentInformation.objects.create(
                customer=self.user, 
                payment_method="Test",
                total_fees=10, down_payment=5, remaining_balance=5
            )
        
        # Search for 'Test'
        response = self.client.get(self.url, {"q": "Test", "page": 1})
        
        # The 'Next' link should include the search query so it isn't lost
        self.assertContains(response, 'href="?q=Test&page=2"')