from django.test import TestCase, Client
from django.urls import reverse
from finance.models import Default_Payment_Fees


class DefaultPaymentFeesRegressionTemplates(TestCase):
    """
    Regression tests to ensure templates render and contain expected UI text.
    """

    def setUp(self):
        self.client = Client()
        # Create a dummy Default_Payment_Fees object for testing
        self.payment = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300,
        )
        self.list_url = reverse("Default_Payment_Fees_list")
        self.create_url = reverse("Default_Payment_Fees_create")
        self.update_url = reverse("Default_Payment_Fees_update", kwargs={"pk": self.payment.pk})
        self.delete_url = reverse("Default_Payment_Fees_delete", kwargs={"pk": self.payment.pk})
        self.detail_url = reverse("Default_Payment_Fees_detail", kwargs={"pk": self.payment.pk})

    # ---------- LIST ----------
    def test_list_template_contains_table_headers(self):
        """Ensure the Default Payment Fees list template contains the correct table headers."""
        response = self.client.get(self.list_url)
        self.assertTemplateUsed(response, "finance/Default_Payment_Fees_list.html")
        self.assertContains(response, "Job Down Payment (Per Month)")
        self.assertContains(response, "Job Plan Hours (Per Month)")
        self.assertContains(response, "Student Down Payment (Per Month)")
        self.assertContains(response, "Student Bonus Payment (Per Month)")

    def test_list_template_contains_payment_data(self):
        """Ensure the list template renders the correct payment data."""
        response = self.client.get(self.list_url)
        self.assertTemplateUsed(response, "finance/Default_Payment_Fees_list.html")
        self.assertContains(response, str(self.payment.job_down_payment_per_month))
        self.assertContains(response, str(self.payment.job_plan_hours_per_month))
        self.assertContains(response, str(self.payment.student_down_payment_per_month))
        self.assertContains(response, str(self.payment.student_bonus_payment_per_month))

    # ---------- CREATE ----------
    def test_create_template_contains_form_fields(self):
        """Ensure the Default Payment Fees create template contains the form fields."""
        response = self.client.get(self.create_url)
        self.assertTemplateUsed(response, "finance/Default_Payment_Fees_create.html")
        self.assertContains(response, "job_down_payment_per_month")
        self.assertContains(response, "student_down_payment_per_month")

    # ---------- UPDATE ----------
    def test_update_template_contains_existing_values(self):
        """Ensure the Default Payment Fees update template contains existing values for fields."""
        response = self.client.get(self.update_url)
        self.assertTemplateUsed(response, "finance/Default_Payment_Fees_update.html")
        self.assertContains(response, "2000")
        self.assertContains(response, "160")

    # ---------- DELETE ----------
    def test_delete_template_displays_confirmation_text(self):
        """Ensure the Default Payment Fees delete template displays confirmation text."""
        response = self.client.get(self.delete_url)
        self.assertTemplateUsed(response, "finance/Default_Payment_Fees_delete.html")
        self.assertContains(response, "Are you sure")
        self.assertContains(response, "Delete")

    # ---------- DETAIL ----------
    def test_detail_template_displays_payment_data(self):
        """Ensure the Default Payment Fees detail template renders the correct payment data."""
        response = self.client.get(self.detail_url)
        self.assertTemplateUsed(response, "finance/Default_Payment_Fees_detail.html")
        self.assertContains(response, "2000")
        self.assertContains(response, "160")
        self.assertContains(response, "1500")
        self.assertContains(response, "300")
        # Check for Edit/Delete/Back buttons
        self.assertContains(response, "Edit")
        self.assertContains(response, "Delete")
        self.assertContains(response, "Back")


class DefaultPaymentFeesRegressionTemplateTest(TestCase):

    def setUp(self):
        self.client = Client()
        # Create a sample Default Payment Fees object for testing
        self.payment_fee = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=2000,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=1500,
            student_bonus_payment_per_month=300
        )

    def test_list_template_contains_table_headers(self):
        """Ensure the list template renders table headers correctly."""
        url = reverse("Default_Payment_Fees_list")
        response = self.client.get(url)
        
        # Check that table headers are rendered
        self.assertContains(response, 'Job Down Payment (Per Month)')
        self.assertContains(response, 'Job Plan Hours (Per Month)')
        self.assertContains(response, 'Student Down Payment (Per Month)')
        self.assertContains(response, 'Student Bonus Payment (Per Month)')

    def test_list_template_contains_payment_data(self):
        """Ensure the list template contains the payment data correctly."""
        url = reverse("Default_Payment_Fees_list")
        response = self.client.get(url)
        
        # Ensure the payment data is included in the table
        self.assertContains(response, str(self.payment_fee.job_down_payment_per_month))
        self.assertContains(response, str(self.payment_fee.job_plan_hours_per_month))
        self.assertContains(response, str(self.payment_fee.student_down_payment_per_month))
        self.assertContains(response, str(self.payment_fee.student_bonus_payment_per_month))

    # ================================
    # Test for Default Payment Fees Create Template
    # ================================
    def test_default_payment_fees_create_template(self):
        """Test if the correct template is used for Default Payment Fees create view."""
        url = reverse("Default_Payment_Fees_create")  # This should match your URL pattern
        response = self.client.get(url)

        # Check if the correct template is used
        self.assertTemplateUsed(response, 'finance/Default_Payment_Fees_create.html')  # Ensure this matches the template used in your view

    # ================================
    # Test for Default Payment Fees Update Template
    # ================================
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
