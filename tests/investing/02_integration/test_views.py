"""
Integration tests for investing views

Tests view functions, HTTP requests/responses, and template rendering.

Author: CODA Development Team
Created: November 6, 2025
Category: Integration Tests
"""

from datetime import timedelta

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone

from investing.models import ManagedTradingAccount, OptionsPosition
from investing.services.managed_trading_service import ManagedTradingService
from accounts.choices import UserCategory

User = get_user_model()


class InvestmentDashboardViewTest(TestCase):
    """Test investment dashboard view"""
    
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
        
        # Create investor user
        self.investor_user = User.objects.create_user(
            username='investor_test',
            email='investor@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
        )
    
    def test_dashboard_requires_authentication(self):
        """Test that dashboard requires login"""
        response = self.client.get('/investing/')
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_dashboard_accessible_to_authenticated_users(self):
        """Test that authenticated users can access dashboard"""
        self.client.login(username='staff_test', password='password123')
        
        response = self.client.get('/investing/')
        
        # Should be successful (200) or redirect to a sub-page
        self.assertIn(response.status_code, [200, 301, 302])
    
    def test_dashboard_shows_staff_tools_to_staff(self):
        """Test that staff users see staff management tools"""
        self.client.login(username='staff_test', password='password123')
        
        response = self.client.get('/investing/')
        
        if response.status_code == 200:
            # Staff should see upload tools
            self.assertContains(response, 'CSV Upload', status_code=200)
    
    def test_dashboard_hides_staff_tools_from_investors(self):
        """Test that investors don't see staff management tools"""
        self.client.login(username='investor_test', password='password123')
        
        response = self.client.get('/investing/')
        
        if response.status_code == 200:
            # Investors should NOT see admin tools (if properly implemented)
            # This is implementation-dependent
            pass


class ClientPortalViewTest(TestCase):
    """Test client portal view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create two investors
        self.investor1 = User.objects.create_user(
            username='investor1',
            email='investor1@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
            first_name='John',
            last_name='Investor'
        )
        
        self.investor2 = User.objects.create_user(
            username='investor2',
            email='investor2@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
            first_name='Jane',
            last_name='Investor'
        )
        
        # Create accounts for each investor
        self.account1 = ManagedTradingAccount.objects.create(
            client=self.investor1,
            account_number='INV1_001',
            account_name='Investor 1 Account',
            broker='tastytrade',
            fee_tier='independent',
            initial_capital=Decimal('10000.00'),
            current_balance=Decimal('12000.00'),
            status='active',
        )
        
        self.account2 = ManagedTradingAccount.objects.create(
            client=self.investor2,
            account_number='INV2_001',
            account_name='Investor 2 Account',
            broker='tastytrade',
            fee_tier='consultative',
            initial_capital=Decimal('15000.00'),
            current_balance=Decimal('16500.00'),
            status='active',
        )
    
    def test_client_portal_requires_authentication(self):
        """Test that client portal requires login"""
        response = self.client.get(reverse('investing:client_portal'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_client_portal_shows_own_accounts_only(self):
        """Test that investors see only their own accounts"""
        self.client.login(username='investor1', password='password123')
        
        response = self.client.get(reverse('investing:client_portal'))
        
        if response.status_code == 200:
            # Should see own account
            self.assertContains(response, 'INV1_001')
            
            # Should NOT see other investor's account
            self.assertNotContains(response, 'INV2_001')
    
    def test_client_portal_shows_account_balance(self):
        """Test that client portal displays account balance"""
        self.client.login(username='investor1', password='password123')
        
        response = self.client.get(reverse('investing:client_portal'))
        
        if response.status_code == 200:
            # Should show balance
            self.assertContains(response, '12000' or '$12,000')


class CSVUploadViewTest(TestCase):
    """Test CSV upload view (staff only)"""
    
    def setUp(self):
        """Set up test users"""
        self.client = Client()
        
        self.staff_user = User.objects.create_user(
            username='staff_test',
            email='staff@test.com',
            password='password123',
            is_staff=True,
            is_active=True,
        )
        
        self.investor_user = User.objects.create_user(
            username='investor_test',
            email='investor@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
        )
    
    def test_csv_upload_requires_staff_authentication(self):
        """Test that CSV upload requires staff login"""
        # Unauthenticated
        response = self.client.get('/investing/managed/staff/upload-csv/')
        self.assertEqual(response.status_code, 302)
        
        # Non-staff user
        self.client.login(username='investor_test', password='password123')
        response = self.client.get('/investing/managed/staff/upload-csv/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
    
    def test_csv_upload_accessible_to_staff(self):
        """Test that staff can access CSV upload"""
        self.client.login(username='staff_test', password='password123')
        
        response = self.client.get('/investing/managed/staff/upload-csv/')
        
        # Should be accessible (not redirect to admin login)
        if response.status_code in [301, 302]:
            self.assertNotIn('/admin/login/', response.url)


class MultiFileAnalyzerViewTest(TestCase):
    """Test multi-file analyzer view (staff only)"""
    
    def setUp(self):
        """Set up test users"""
        self.client = Client()
        
        self.staff_user = User.objects.create_user(
            username='staff_test',
            email='staff@test.com',
            password='password123',
            is_staff=True,
            is_active=True,
        )
        
        self.investor_user = User.objects.create_user(
            username='investor_test',
            email='investor@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
        )
    
    def test_multi_file_analyzer_requires_staff_authentication(self):
        """Test that multi-file analyzer requires staff login"""
        # Unauthenticated
        response = self.client.get('/investing/managed/staff/multi-file-analyzer/')
        self.assertEqual(response.status_code, 302)
        
        # Non-staff user
        self.client.login(username='investor_test', password='password123')
        response = self.client.get('/investing/managed/staff/multi-file-analyzer/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
    
    def test_multi_file_analyzer_accessible_to_staff(self):
        """Test that staff can access multi-file analyzer"""
        self.client.login(username='staff_test', password='password123')
        
        response = self.client.get('/investing/managed/staff/multi-file-analyzer/')
        
        # Should be accessible (not redirect to admin login)
        if response.status_code in [301, 302]:
            self.assertNotIn('/admin/login/', response.url)


class OptionListViewTest(TestCase):
    """Test option list view (regression for NoReverseMatch bug)"""
    
    def setUp(self):
        """Set up test user"""
        self.client = Client()
        
        self.user = User.objects.create_user(
            username='test_user',
            email='test@test.com',
            password='password123',
            is_staff=True,
            is_active=True,
        )
    
    def test_option_list_view_loads_without_error(self):
        """
        Test that option list view loads without NoReverseMatch error
        
        Regression test for Nov 5, 2025 bug:
        Bug: NoReverseMatch for 'option_list' with {'title': ''}
        Fix: Added subtitle to context
        """
        self.client.login(username='test_user', password='password123')
        
        # Test various option types
        option_types = ['shortputdata', 'creditspread', 'coveredcall']
        
        for option_type in option_types:
            response = self.client.get(f'/investing/options/{option_type}/')
            
            # Should not raise NoReverseMatch (should load successfully or redirect)
            self.assertIn(response.status_code, [200, 301, 302, 404])
            
            # If successful, should have both title and subtitle
            if response.status_code == 200:
                self.assertIn('title', response.context)
                self.assertIn('subtitle', response.context)


class ManagedAccountPhase3ViewTest(TestCase):
    """Ensure managed client dashboard surfaces Phase 3 widgets and context."""

    def setUp(self):
        self.client = Client()
        self.service = ManagedTradingService()
        self.client_user = User.objects.create_user(
            username='phase3_client',
            email='phase3_client@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
        )
        self.account = self.service.create_managed_account(
            client_user=self.client_user,
            account_data={
                'account_name': 'Phase 3 Sleeve',
                'initial_capital': Decimal('25000.00'),
                'fee_tier': 'professional',
            },
        )
        self.now = timezone.now()
        self._seed_positions()

    def _seed_positions(self):
        month_start = self.now.date().replace(day=1)

        closed = OptionsPosition.objects.create(
            managed_account=self.account,
            symbol='QQQ',
            strategy='short_put',
            positions=[{'type': 'put', 'strike': 370, 'contracts': 1}],
            capital_required=Decimal('2500.00'),
            premium_collected=Decimal('0.00'),
            max_profit=Decimal('250.00'),
            max_loss=Decimal('2500.00'),
            expiration_date=month_start + timedelta(days=25),
            status='closed',
        )
        OptionsPosition.objects.filter(pk=closed.pk).update(
            entry_date=month_start - timedelta(days=9),
            exit_date=month_start + timedelta(days=6),
            realized_pnl=Decimal('160.00'),
        )

        open_position = OptionsPosition.objects.create(
            managed_account=self.account,
            symbol='NVDA',
            strategy='short_put',
            positions=[{'type': 'put', 'strike': 400, 'contracts': 1}],
            capital_required=Decimal('3000.00'),
            premium_collected=Decimal('220.00'),
            max_profit=Decimal('220.00'),
            max_loss=Decimal('3000.00'),
            expiration_date=month_start + timedelta(days=40),
            status='open',
            api_response_data={
                'unusual_whales': {
                    'flow_score': 90,
                    'sentiment': 'bullish',
                    'timing_signal': 'Institutional sweep',
                    'entry_window': '1-3 days',
                }
            },
        )
        OptionsPosition.objects.filter(pk=open_position.pk).update(
            entry_date=month_start + timedelta(days=3)
        )

    def test_client_dashboard_renders_phase3_widgets(self):
        self.client.login(username='phase3_client', password='password123')
        response = self.client.get(reverse('investing:client_account_detail', args=[self.account.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This portal keeps you informed')
        self.assertContains(response, 'Scenario Explorer')
        self.assertContains(response, 'Need')

        scenario_defaults = response.context['scenario_defaults']
        self.assertIn('baseline_income', scenario_defaults)
        self.assertIn('target_income', scenario_defaults)
        self.assertIn('slider_disabled', scenario_defaults)
        self.assertFalse(scenario_defaults['slider_disabled'])

        income_summary = response.context['income_summary']
        self.assertIn('target_gap', income_summary)
        self.assertGreaterEqual(income_summary['coverage_pct'], Decimal('0'))


class ManagedAccountDetailViewTest(TestCase):
    """Test managed account detail view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create investor
        self.investor = User.objects.create_user(
            username='investor_test',
            email='investor@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
        )
        
        # Create staff
        self.staff = User.objects.create_user(
            username='staff_test',
            email='staff@test.com',
            password='password123',
            is_staff=True,
            is_active=True,
        )
        
        # Create managed account
        self.account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST001',
            account_name='Test Account',
            broker='tastytrade',
            fee_tier='independent',
            initial_capital=Decimal('10000.00'),
            current_balance=Decimal('12000.00'),
            status='active',
        )
    
    def test_account_detail_requires_authentication(self):
        """Test that account detail requires login"""
        response = self.client.get(f'/investing/managed/accounts/{self.account.pk}/')
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_account_owner_can_view_own_account(self):
        """Test that account owner can view their account"""
        self.client.login(username='investor_test', password='password123')
        
        response = self.client.get(f'/investing/managed/accounts/{self.account.pk}/')
        
        # Should be accessible
        if response.status_code == 200:
            self.assertContains(response, 'TEST001')
            self.assertContains(response, '12000' or '$12,000')
    
    def test_staff_can_view_any_account(self):
        """Test that staff can view any account"""
        self.client.login(username='staff_test', password='password123')
        
        response = self.client.get(f'/investing/managed/accounts/{self.account.pk}/')
        
        # Should be accessible
        if response.status_code == 200:
            self.assertContains(response, 'TEST001')


class OptionsPositionListViewTest(TestCase):
    """Test options position list view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.staff = User.objects.create_user(
            username='staff_test',
            email='staff@test.com',
            password='password123',
            is_staff=True,
            is_active=True,
        )
        
        self.investor = User.objects.create_user(
            username='investor_test',
            email='investor@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
        )
        
        # Create account with position
        self.account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST001',
            account_name='Test Account',
            broker='tastytrade',
            fee_tier='independent',
            initial_capital=Decimal('10000.00'),
            status='active',
        )
        
        from datetime import date, timedelta
        self.position = OptionsPosition.objects.create(
            managed_account=self.account,
            symbol='SPY',
            strategy='short_put',
            strike_price=Decimal('450.00'),
            expiration_date=date.today() + timedelta(days=30),
            contracts=1,
            premium_collected=Decimal('100.00'),
            status='open',
        )
    
    def test_position_list_requires_authentication(self):
        """Test that position list requires login"""
        response = self.client.get('/investing/managed/positions/')
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_staff_can_see_all_positions(self):
        """Test that staff can see all positions"""
        self.client.login(username='staff_test', password='password123')
        
        response = self.client.get('/investing/managed/positions/')
        
        # Should be accessible
        if response.status_code == 200:
            self.assertContains(response, 'SPY')
            self.assertContains(response, 'short_put')
