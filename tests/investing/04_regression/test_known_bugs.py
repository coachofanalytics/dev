"""
Regression tests for investing known bugs

Tests that previously fixed bugs do not reappear.

Author: CODA Development Team
Created: November 6, 2025
Category: Regression Tests
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal

from investing.models import ManagedTradingAccount, OptionsPosition
from accounts.choices import UserCategory

User = get_user_model()


class BugFix_20251105_NoneTypeError_Test(TestCase):
    """
    Regression test for TypeError with None values in ManagedTradingAccount
    
    Bug: unsupported operand type(s) for -: 'NoneType' and 'decimal.Decimal'
    Date Reported: November 5, 2025
    Location: /admin/investing/managedtradingaccount/add/
    Date Fixed: November 5, 2025
    
    Problem:
        When creating a new ManagedTradingAccount in Django admin, the @property
        methods (available_buying_power, current_risk_exposure, return_on_investment)
        were attempting arithmetic operations on None values, causing TypeError.
    
    Fix:
        Added None checks in all @property methods to return Decimal('0.00')
        when encountering None values.
    
    Files Changed:
        - coda/investing/models.py (ManagedTradingAccount class)
    """
    
    def setUp(self):
        """Set up test data"""
        self.investor = User.objects.create_user(
            username='investor_test',
            email='investor@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
        )
    
    def test_available_buying_power_handles_none_cash_available(self):
        """Test that available_buying_power returns 0 when cash_available is None"""
        account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST001',
            account_name='Test Account',
            broker='tastytrade',
            fee_tier='balanced',
            initial_capital=Decimal('10000.00'),
            cash_available=None,  # None value
            cash_reserved=Decimal('1000.00'),
            status='active',
        )
        
        # Should not raise TypeError
        buying_power = account.available_buying_power
        self.assertEqual(buying_power, Decimal('0.00'))
    
    def test_available_buying_power_handles_none_cash_reserved(self):
        """Test that available_buying_power returns 0 when cash_reserved is None"""
        account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST002',
            account_name='Test Account',
            broker='tastytrade',
            fee_tier='balanced',
            initial_capital=Decimal('10000.00'),
            cash_available=Decimal('5000.00'),
            cash_reserved=None,  # None value
            status='active',
        )
        
        # Should not raise TypeError
        buying_power = account.available_buying_power
        self.assertEqual(buying_power, Decimal('0.00'))
    
    def test_available_buying_power_handles_both_none(self):
        """Test that available_buying_power returns 0 when both values are None"""
        account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST003',
            account_name='Test Account',
            broker='tastytrade',
            fee_tier='balanced',
            initial_capital=Decimal('10000.00'),
            cash_available=None,  # None
            cash_reserved=None,   # None
            status='active',
        )
        
        # Should not raise TypeError
        buying_power = account.available_buying_power
        self.assertEqual(buying_power, Decimal('0.00'))
    
    def test_return_on_investment_handles_none_current_balance(self):
        """Test that ROI returns 0 when current_balance is None"""
        account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST004',
            account_name='Test Account',
            broker='tastytrade',
            fee_tier='balanced',
            initial_capital=Decimal('10000.00'),
            current_balance=None,  # None value
            status='active',
        )
        
        # Should not raise TypeError
        roi = account.return_on_investment
        self.assertEqual(roi, Decimal('0.00'))
    
    def test_return_on_investment_handles_none_initial_capital(self):
        """Test that ROI returns 0 when initial_capital is None"""
        account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST005',
            account_name='Test Account',
            broker='tastytrade',
            fee_tier='balanced',
            initial_capital=None,  # None value
            current_balance=Decimal('12000.00'),
            status='active',
        )
        
        # Should not raise TypeError
        roi = account.return_on_investment
        self.assertEqual(roi, Decimal('0.00'))
    
    def test_return_on_investment_handles_zero_initial_capital(self):
        """Test that ROI returns 0 when initial_capital is 0 (division by zero)"""
        account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST006',
            account_name='Test Account',
            broker='tastytrade',
            fee_tier='balanced',
            initial_capital=Decimal('0.00'),  # Zero
            current_balance=Decimal('5000.00'),
            status='active',
        )
        
        # Should not raise ZeroDivisionError
        roi = account.return_on_investment
        self.assertEqual(roi, Decimal('0.00'))
    
    def test_current_risk_exposure_handles_none_current_balance(self):
        """Test that current_risk_exposure returns 0 when current_balance is None"""
        account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST007',
            account_name='Test Account',
            broker='tastytrade',
            fee_tier='balanced',
            initial_capital=Decimal('10000.00'),
            current_balance=None,  # None value
            status='active',
        )
        
        # Should not raise TypeError
        risk = account.current_risk_exposure
        self.assertEqual(risk, Decimal('0.00'))
    
    def test_current_risk_exposure_handles_zero_current_balance(self):
        """Test that current_risk_exposure returns 0 when current_balance is 0"""
        account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST008',
            account_name='Test Account',
            broker='tastytrade',
            fee_tier='balanced',
            initial_capital=Decimal('10000.00'),
            current_balance=Decimal('0.00'),  # Zero
            status='active',
        )
        
        # Should not raise ZeroDivisionError
        risk = account.current_risk_exposure
        self.assertEqual(risk, Decimal('0.00'))


class BugFix_20251105_NoReverseMatch_OptionList_Test(TestCase):
    """
    Regression test for NoReverseMatch error in option list template
    
    Bug: Reverse for 'option_list' with keyword arguments '{'title': ''}' not found
    Date Reported: November 5, 2025
    Location: /investing/options/shortputdata/
    Date Fixed: November 5, 2025
    
    Problem:
        The OptionListView was setting context['title'] but not context['subtitle'].
        The template expected both variables, causing NoReverseMatch when trying to
        reverse URL with empty subtitle.
    
    Fix:
        Added subtitle to context in OptionListView.get_context_data()
    
    Files Changed:
        - coda/investing/views_legacy.py (OptionListView)
    """
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='test_user',
            email='test@test.com',
            password='password123',
            is_staff=True,
            is_active=True,
        )
    
    def test_option_list_view_includes_subtitle_in_context(self):
        """Test that option list view includes subtitle in context"""
        self.client.login(username='test_user', password='password123')
        
        # Access the view
        response = self.client.get('/investing/options/shortputdata/')
        
        # Should not raise NoReverseMatch
        self.assertEqual(response.status_code, 200)
        
        # Should have both title and subtitle in context
        self.assertIn('title', response.context)
        self.assertIn('subtitle', response.context)
        
        # subtitle should match title
        self.assertEqual(response.context['title'], response.context['subtitle'])


class BugFix_20251105_NoReverseMatch_ClientPortal_Test(TestCase):
    """
    Regression test for NoReverseMatch error in application detail template
    
    Bug: Reverse for 'managed_client_portal' not found
    Date Reported: November 5, 2025
    Location: /investing/managed/onboarding/application/1/
    Date Fixed: November 5, 2025
    
    Problem:
        The template was trying to reverse 'investing:managed_client_portal',
        but the actual URL name was 'investing:client_portal'.
    
    Fix:
        Updated template to use correct URL name: 'investing:client_portal'
    
    Files Changed:
        - coda/investing/templates/investing/onboarding/application_detail.html
    """
    
    def test_client_portal_url_name_is_correct(self):
        """Test that client_portal URL name can be reversed"""
        # This should not raise NoReverseMatch
        url = reverse('investing:client_portal')
        self.assertIsNotNone(url)
        self.assertIn('client-portal', url)


class BugFix_20251105_UploadRedirectToAdmin_Test(TestCase):
    """
    Regression test for upload functionality redirect to admin
    
    Bug: Upload CSV page showed Django admin login instead of upload interface
    Date Reported: November 5, 2025
    Location: https://www.codanalytics.net/investing/managed/staff/upload-csv/
    Date Fixed: November 5, 2025
    
    Problem:
        The view used @staff_member_required decorator, which redirects to
        Django admin login (/admin/login/) if user is not a staff member.
        This was not a bug per se, but required proper staff authentication.
    
    Fix:
        Documented that staff login is required. View works correctly when
        logged in as staff member.
    
    Resolution:
        This is expected behavior. Staff-only views require staff authentication.
        Test ensures that the view is accessible to staff members.
    """
    
    def setUp(self):
        """Set up test client and users"""
        self.client = Client()
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff_test',
            email='staff@test.com',
            password='password123',
            is_staff=True,
            is_active=True,
        )
        
        # Create non-staff user
        self.regular_user = User.objects.create_user(
            username='regular_test',
            email='regular@test.com',
            password='password123',
            is_staff=False,
            is_active=True,
            category=UserCategory.INVESTOR,
        )
    
    def test_upload_csv_view_requires_staff_authentication(self):
        """Test that upload CSV view requires staff authentication"""
        # Test unauthenticated access (should redirect)
        response = self.client.get('/investing/managed/staff/upload-csv/')
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Test non-staff access (should redirect to admin login)
        self.client.login(username='regular_test', password='password123')
        response = self.client.get('/investing/managed/staff/upload-csv/')
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertIn('/admin/login/', response.url)
    
    def test_upload_csv_view_accessible_to_staff(self):
        """Test that staff members can access upload CSV view"""
        self.client.login(username='staff_test', password='password123')
        
        response = self.client.get('/investing/managed/staff/upload-csv/')
        
        # Staff should get 200 OK (or appropriate response)
        self.assertIn(response.status_code, [200, 301, 302])
        
        # If redirected, should NOT be to admin login
        if response.status_code in [301, 302]:
            self.assertNotIn('/admin/login/', response.url)
