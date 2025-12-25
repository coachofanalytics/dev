from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from finance.models import PaymentInformation

User = get_user_model()

class PaymentTemplateRegressionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reg_view_user", password="password123")
        self.client = Client()
        self.client.login(username="reg_user", password="password123")
        self.url = reverse("finance:payment_list")

    def test_search_query_persistence_in_input(self):
        """Regression: Ensure the search term stays in the input box after clicking search."""
        search_term = "Visa_Special_Test"
        response = self.client.get(self.url, {"q": search_term})
        
        # Check if the value attribute of the input tag contains our search term
        expected_html = f'value="{search_term}"'
        self.assertContains(response, expected_html)

    def test_long_email_rendering(self):
        """Regression: Ensure very long emails don't break the table layout."""
        long_email = "very" + "long" * 10 + "@example.com"
        self.user.email = long_email
        self.user.save()
        
        PaymentInformation.objects.create(
            customer=self.user, payment_method="Cash",
            total_fees=100, down_payment=50, remaining_balance=50
        )
        
        response = self.client.get(self.url)
        self.assertContains(response, long_email)

    def test_pagination_on_last_page_links(self):
        """Regression: Ensure 'Next' and 'Last' links disappear on the final page."""
        # Create 12 records (2 pages of 10)
        for i in range(12):
            PaymentInformation.objects.create(
                customer=self.user, payment_method="Test",
                total_fees=10, down_payment=5, remaining_balance=5
            )
        
        # Go to page 2
        response = self.client.get(self.url, {"page": 2})
        
        # 'Next' and 'Last' should NOT be in the HTML
        self.assertNotContains(response, "Next")
        self.assertNotContains(response, "Last &raquo;")
        # 'Previous' and 'First' SHOULD be there
        self.assertContains(response, "Previous")
        self.assertContains(response, "&laquo; First")

    def test_html_escaping_in_search(self):
        """Regression: Ensure that malicious scripts in search query are escaped, not executed."""
        attack_script = "<script>alert('xss')</script>"
        response = self.client.get(self.url, {"q": attack_script})
        
        # Django should escape < to &lt;
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, attack_script)

    def test_zero_values_display(self):
        """Regression: Ensure 0 values are rendered as '0' and not left blank."""
        PaymentInformation.objects.create(
            customer=self.user, payment_method="Free",
            total_fees=0, down_payment=0, remaining_balance=0
        )
        response = self.client.get(self.url)
        # We expect to see 0 in the table cells
        self.assertContains(response, "<td>0</td>")