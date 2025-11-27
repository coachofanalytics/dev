from django.test import SimpleTestCase
from django.urls import reverse, resolve
from finance.views import PayslipConfig_list, Default_Payment_Fees_list, Default_Payment_Fees_create

class TestRegressionUrls(SimpleTestCase):

    # ================================
    # Regression Test for PayslipConfig List URL
    # ================================
    def test_payslip_config_list_url_resolves(self):
        """Test if the 'PayslipConfig_list' URL resolves correctly"""
        url = reverse('payslip_config_list')
        self.assertEqual(resolve(url).func, PayslipConfig_list)

    def test_payslip_config_list_url_reverse(self):
        """Test if reverse for 'payslip_config_list' generates the correct URL."""
        url = reverse('payslip_config_list')
        self.assertEqual(url, '/finance/PayslipConfig_list/')  # Ensure '/finance/' prefix is included

    # ================================
    # Regression Test for Default Payment Fees List URL
    # ================================
    def test_default_payment_fees_list_url_resolves(self):
        """Test if the 'Default_Payment_Fees_list' URL resolves correctly"""
        url = reverse('Default_Payment_Fees_list')
        self.assertEqual(resolve(url).func, Default_Payment_Fees_list)

    def test_default_payment_fees_list_url_reverse(self):
        """Test if reverse for 'Default_Payment_Fees_list' generates the correct URL."""
        url = reverse('Default_Payment_Fees_list')
        self.assertEqual(url, '/finance/Default_Payment_Fees_list/')  # Ensure '/finance/' prefix is included

    # ================================
    # Regression Test for Default Payment Fees Create URL
    # ================================
    def test_default_payment_fees_create_url_resolves(self):
        """Test if the 'Default_Payment_Fees_create' URL resolves correctly"""
        url = reverse('Default_Payment_Fees_create')
        self.assertEqual(resolve(url).func, Default_Payment_Fees_create)

    def test_default_payment_fees_create_url_reverse(self):
        """Test if reverse for 'Default_Payment_Fees_create' generates the correct URL."""
        url = reverse('Default_Payment_Fees_create')
        self.assertEqual(url, '/finance/Default_Payment_Fees_create/')  # Ensure '/finance/' prefix is included
