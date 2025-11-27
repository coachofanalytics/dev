from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from finance.models import Default_Payment_Fees, PayslipConfig
from finance.forms import Default_Payment_Fees_form

# ------------------------- 
# Test List View 
# -------------------------
class DefaultPaymentFeesListViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        # Create some sample data for Default_Payment_Fees
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
        self.assertEqual(str(messages[0]), 'create successfully')  # Updated success message

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


# ------------------------- 
# Test Update View 
# -------------------------
class DefaultPaymentFeesUpdateViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.payment = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )
        self.url = reverse('Default_Payment_Fees_update', kwargs={'pk': self.payment.pk})

    def test_update_view_get_request(self):
        """GET request should return 200 and contain the form"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], Default_Payment_Fees_form)
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_update.html')

    def test_update_view_post_valid_data(self):
        """POST valid data should update the object"""
        data = {
            'job_down_payment_per_month': 2500,
            'job_plan_hours_per_month': 180,
            'student_down_payment_per_month': 1700,
            'student_bonus_payment_per_month': 400
        }
        response = self.client.post(self.url, data, follow=True)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.job_down_payment_per_month, 2500)
        self.assertEqual(self.payment.job_plan_hours_per_month, 180)
        self.assertRedirects(response, reverse('Default_Payment_Fees_list'))

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'update successfully')  # Updated success message

    def test_update_view_post_invalid_data(self):
        """POST invalid data should not update and render form errors"""
        data = {
            'job_down_payment_per_month': '',  # invalid
            'job_plan_hours_per_month': 180,
            'student_down_payment_per_month': 1700,
            'student_bonus_payment_per_month': 400
        }
        response = self.client.post(self.url, data)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.job_down_payment_per_month, 2000)  # unchanged
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)


# ------------------------- 
# Test Delete View 
# -------------------------
import pytest
from django.urls import reverse
from django.contrib.messages import get_messages
from finance.models import Default_Payment_Fees

@pytest.mark.django_db
class TestDefaultPaymentFeesDeleteView:

    def test_get_delete_view_renders_template(self, client):
        # Create a payment fee object
        payment = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )

        url = reverse("Default_Payment_Fees_delete", args=[payment.pk])
        response = client.get(url)

        # Check that the page renders correctly
        assert response.status_code == 200
        assert "finance/Default_Payment_Fees_delete.html" in [
            t.name for t in response.templates
        ]
        assert b"Test Fee" in response.content

    def test_post_delete_view_deletes_object_and_redirects(self, client):
        # Create a payment fee object
        payment = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )

        url = reverse("Default_Payment_Fees_delete", args=[payment.pk])
        response = client.post(url, follow=True)

        # After deletion, object should not exist
        assert not Default_Payment_Fees.objects.filter(pk=payment.pk).exists()

        # Should redirect to the list page
        assert response.redirect_chain
        assert response.redirect_chain[-1][0].endswith(reverse("Default_Payment_Fees_list"))
        assert response.status_code == 200

        # Check that the success message appears
        messages = list(get_messages(response.wsgi_request))
        assert any("Delete successfully" in str(m) for m in messages)


# ------------------------- 
# Test PayslipConfig List View 
# -------------------------
class PayslipConfigListViewTest(TestCase):

    def setUp(self):
        # Create some sample PayslipConfig records
        self.payslip1 = PayslipConfig.objects.create(
            loan_status=True,
            loan_amount=2000,
            loan_repayment_percentage=10.00,
            laptop_status=True,
            lb_amount=1200,
            ls_amount=1000,
            ls_max_limit=3000,
            rp_starting_period="6 months",
            rp_starting_amount=100,
            rp_increment_percentage=5.00
        )
        self.payslip2 = PayslipConfig.objects.create(
            loan_status=False,
            loan_amount=2500,
            loan_repayment_percentage=12.00,
            laptop_status=False,
            lb_amount=1500,
            ls_amount=1200,
            ls_max_limit=5000,
            rp_starting_period="12 months",
            rp_starting_amount=200,
            rp_increment_percentage=3.00
        )
        self.url = reverse('payslip_config_list')  # Make sure this matches your URL pattern

    def test_payslip_config_list_view(self):
        """Test that the PayslipConfig list view displays the correct data."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/payslips.html')  # Ensure the correct template is used
        self.assertContains(response, str(self.payslip1.loan_amount))
        self.assertContains(response, str(self.payslip2.rp_starting_amount))
