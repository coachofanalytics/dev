from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from finance.models import Default_Payment_Fees
from finance.forms import Default_Payment_Fees_form

# -------------------------
# Test List View
# -------------------------
class DefaultPaymentFeesListViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        # Create some sample data
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

    def test_list_view_status_code(self):
        """Check if the list view loads successfully"""
        response = self.client.get(reverse('Default_Payment_Fees_list'))
        self.assertEqual(response.status_code, 200)

    def test_list_view_template_used(self):
        """Ensure the correct template is used"""
        response = self.client.get(reverse('Default_Payment_Fees_list'))
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_list.html')

    def test_list_view_context_data(self):
        """Ensure 'payments' is in context and contains correct count"""
        response = self.client.get(reverse('Default_Payment_Fees_list'))
        self.assertIn('payments', response.context)
        self.assertEqual(response.context['payments'].count(), 2)

    def test_list_view_displays_fee_values(self):
        """Ensure the rendered HTML contains specific fee data"""
        response = self.client.get(reverse('Default_Payment_Fees_list'))
        self.assertContains(response, "2000")
        self.assertContains(response, "2500")
        self.assertContains(response, "160")
        self.assertContains(response, "180")

# -------------------------
# Test Create View
# -------------------------
class DefaultPaymentFeesCreateViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('Default_Payment_Fees_create')

    def test_create_view_get_request(self):
        """Test GET request returns status 200 and form in context"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], Default_Payment_Fees_form)
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_create.html')

    def test_create_view_post_valid_data(self):
        """Test POST request with valid data creates a new Default_Payment_Fees"""
        data = {
            'job_down_payment_per_month': 2000,
            'job_plan_hours_per_month': 160,
            'student_down_payment_per_month': 1500,
            'student_bonus_payment_per_month': 300
        }
        response = self.client.post(self.url, data, follow=True)
        
        # Check that the object was created
        self.assertEqual(Default_Payment_Fees.objects.count(), 1)
        obj = Default_Payment_Fees.objects.first()
        self.assertEqual(obj.job_down_payment_per_month, 2000)
        self.assertEqual(obj.job_plan_hours_per_month, 160)

        # Check redirect
        self.assertRedirects(response, reverse('Default_Payment_Fees_list'))

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Default_Payment_Fees successfully')

    def test_create_view_post_invalid_data(self):
        """Test POST request with invalid data returns form errors"""
        data = {
            'job_down_payment_per_month': '',  # Missing required field
            'job_plan_hours_per_month': 160,
            'student_down_payment_per_month': 1500,
            'student_bonus_payment_per_month': 300
        }
        response = self.client.post(self.url, data)
        
        # Form should not save
        self.assertEqual(Default_Payment_Fees.objects.count(), 0)

        # Should render the form again with errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_create.html')
        self.assertTrue(response.context['form'].errors)
