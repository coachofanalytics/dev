from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees


class DefaultPaymentFeesTemplateTest(TestCase):
    """Tests to verify that the Default Payment Fees template renders correctly."""

    def setUp(self):
        self.client = Client()
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

    def test_template_used(self):
        """Ensure the correct template is used."""
        response = self.client.get(reverse('Default_Payment_Fees_list'))
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_list.html')

    def test_template_displays_fee_data(self):
        """Check that the template actually displays fee data."""
        response = self.client.get(reverse('Default_Payment_Fees_list'))
        self.assertContains(response, "2000")
        self.assertContains(response, "2500")
        self.assertContains(response, "160")
        self.assertContains(response, "180")

    def test_template_context_data(self):
        """Ensure the context includes the 'payments' variable."""
        response = self.client.get(reverse('Default_Payment_Fees_list'))
        self.assertIn('payments', response.context)
        self.assertEqual(response.context['payments'].count(), 2)




class TestDefaultPaymentFeesTemplates(TestCase):

    def setUp(self):
        self.client = Client()
        # Create sample data for list view
        Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )

    def test_list_view_uses_correct_template(self):
        """List view should use the Default_Payment_Fees_list.html template"""
        response = self.client.get(reverse('Default_Payment_Fees_list'))
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_list.html')

    def test_create_view_uses_correct_template(self):
        """Create view should use the Default_Payment_Fees_create.html template"""
        response = self.client.get(reverse('Default_Payment_Fees_create'))
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_create.html')



from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees

class DefaultPaymentFeesUpdateTemplateTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.payment = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )
        self.url = reverse('Default_Payment_Fees_update', kwargs={'pk': self.payment.pk})

    def test_template_renders_update_form(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_update.html')
        self.assertContains(response, 'job_down_payment_per_month')
        self.assertContains(response, 'job_plan_hours_per_month')
        self.assertContains(response, 'student_down_payment_per_month')
        self.assertContains(response, 'student_bonus_payment_per_month')




from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees

class DefaultPaymentFeesDeleteTemplateTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.payment = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )
        self.url = reverse('Default_Payment_Fees_delete', kwargs={'pk': self.payment.id})

    def test_delete_template_contains_correct_html(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Are you sure you want to delete")
        self.assertContains(response, "Yes, Delete")
        self.assertContains(response, "Cancel")



from django.test import TestCase
from django.urls import reverse
from finance.models import Default_Payment_Fees, PayslipConfig

class TestTemplates(TestCase):

    def test_payslip_config_list_template(self):
        """Test if the correct template is used for PayslipConfig list view."""
        # Create some sample data
        PayslipConfig.objects.create(
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

        url = reverse('payslip_config_list')  # This should match your URL pattern
        response = self.client.get(url)

        # Check if the correct template is used
        self.assertTemplateUsed(response, 'finance/payslips.html')  # Ensure this matches the template used in your view

    def test_default_payment_fees_list_template(self):
        """Test if the correct template is used for Default Payment Fees list view."""
        # Create some sample data
        Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )

        url = reverse('Default_Payment_Fees_list')  # This should match your URL pattern
        response = self.client.get(url)

        # Check if the correct template is used
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_list.html')  # Ensure this matches the template used in your view

    def test_default_payment_fees_create_template(self):
        """Test if the correct template is used for Default Payment Fees create view."""
        url = reverse('Default_Payment_Fees_create')  # This should match your URL pattern
        response = self.client.get(url)

        # Check if the correct template is used
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_create.html')  # Ensure this matches the template used in your view

    def test_default_payment_fees_update_template(self):
        """Test if the correct template is used for Default Payment Fees update view."""
        # Create a sample Default Payment Fee object to test update view
        payment_fee = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )

        url = reverse('Default_Payment_Fees_update', kwargs={'pk': payment_fee.pk})  # This should match your URL pattern
        response = self.client.get(url)

        # Check if the correct template is used
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_update.html')  # Ensure this matches the template used in your view

