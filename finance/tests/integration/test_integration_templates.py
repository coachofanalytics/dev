from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees


class DefaultPaymentFeesIntegrationTemplateTest(TestCase):
    """
    Integration test for Default_Payment_Fees_list template.
    Checks that the template renders correctly with database data.
    """

    def setUp(self):
        self.client = Client()
        # Create test data
        Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )
        Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2500,
            job_plan_hours_per_month=180,
            student_down_payment_per_month=1700,
            student_bonus_payment_per_month=400
        )

    def test_template_renders_correctly(self):
        """Ensure template is used and renders successfully"""
        url = reverse('Default_Payment_Fees_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_list.html')

    def test_template_displays_data(self):
        """Ensure that the template actually displays data from the database"""
        url = reverse('Default_Payment_Fees_list')
        response = self.client.get(url)
        self.assertContains(response, "2000")
        self.assertContains(response, "2500")
        self.assertContains(response, "160")
        self.assertContains(response, "180")

    def test_context_includes_payments(self):
        """Ensure that the context contains the 'payments' variable with correct count"""
        url = reverse('Default_Payment_Fees_list')
        response = self.client.get(url)
        self.assertIn('payments', response.context)
        self.assertEqual(response.context['payments'].count(), 2)


from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees

class DefaultPaymentFeesIntegrationTemplates(TestCase):

    def setUp(self):
        self.client = Client()
        self.list_url = reverse('Default_Payment_Fees_list')
        self.create_url = reverse('Default_Payment_Fees_create')

    def test_list_template_used(self):
        response = self.client.get(self.list_url)
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_list.html')

    def test_create_template_used(self):
        response = self.client.get(self.create_url)
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_create.html')
