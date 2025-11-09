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
