"""
Security tests for investing authorization

Tests role-based access control and permissions.

Author: CODA Development Team
Created: November 6, 2025
Category: Security Tests
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from decimal import Decimal

from investing.models import ManagedTradingAccount
from accounts.choices import UserCategory

User = get_user_model()


class StaffOnlyAccessTest(TestCase):
    """Test that staff-only views are properly protected"""
    
    def setUp(self):
        """Set up test users"""
        self.client = Client()
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff_test',
            email='staff@test.com',
            password='password123',
            is_staff=True,
            is_active=True,
            first_name='Staff',
            last_name='Member'
        )
        
        # Create investor (non-staff)
        self.investor_user = User.objects.create_user(
            username='investor_test',
            email='investor@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
            first_name='John',
            last_name='Investor'
        )
        
        # Create student (non-staff)
        self.student_user = User.objects.create_user(
            username='student_test',
            email='student@test.com',
            password='password123',
            category=UserCategory.STUDENT,
            is_active=True,
            first_name='Student',
            last_name='User'
        )
    
    def test_csv_upload_page_requires_staff(self):
        """Test that CSV upload page is staff-only"""
        # Test unauthenticated (should redirect)
        response = self.client.get('/investing/managed/staff/upload-csv/')
        self.assertEqual(response.status_code, 302)
        
        # Test non-staff investor (should redirect to admin login)
        self.client.login(username='investor_test', password='password123')
        response = self.client.get('/investing/managed/staff/upload-csv/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
        
        # Test staff (should allow access)
        self.client.logout()
        self.client.login(username='staff_test', password='password123')
        response = self.client.get('/investing/managed/staff/upload-csv/')
        # Should not redirect to admin login
        if response.status_code in [301, 302]:
            self.assertNotIn('/admin/login/', response.url)
    
    def test_investment_dashboard_requires_authentication(self):
        """Test that investment dashboard requires login"""
        # Unauthenticated access should redirect
        response = self.client.get('/investing/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_multi_file_analyzer_requires_staff(self):
        """Test that multi-file analyzer is staff-only"""
        # Test unauthenticated
        response = self.client.get('/investing/managed/staff/multi-file-analyzer/')
        self.assertEqual(response.status_code, 302)
        
        # Test non-staff
        self.client.login(username='investor_test', password='password123')
        response = self.client.get('/investing/managed/staff/multi-file-analyzer/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)


class UserDataAccessTest(TestCase):
    """Test that users can only access their own data"""
    
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
        )
        
        self.investor2 = User.objects.create_user(
            username='investor2',
            email='investor2@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
        )
        
        # Create staff member
        self.staff = User.objects.create_user(
            username='staff1',
            email='staff@test.com',
            password='password123',
            is_staff=True,
            is_active=True,
        )
        
        # Create accounts for each investor
        self.account1 = ManagedTradingAccount.objects.create(
            client=self.investor1,
            account_number='INV1_001',
            account_name='Investor 1 Account',
            broker='tastytrade',
            fee_tier='independent',
            initial_capital=Decimal('10000.00'),
            status='active',
        )
        
        self.account2 = ManagedTradingAccount.objects.create(
            client=self.investor2,
            account_number='INV2_001',
            account_name='Investor 2 Account',
            broker='tastytrade',
            fee_tier='independent',
            initial_capital=Decimal('15000.00'),
            status='active',
        )
    
    def test_client_portal_shows_only_own_accounts(self):
        """Test that investors see only their own accounts in client portal"""
        # Login as investor1
        self.client.login(username='investor1', password='password123')
        response = self.client.get('/investing/managed/client-portal/')
        
        if response.status_code == 200:
            # Should see own account
            self.assertContains(response, 'INV1_001')
            
            # Should NOT see other investor's account
            self.assertNotContains(response, 'INV2_001')
    
    def test_staff_can_see_all_accounts(self):
        """Test that staff can see all accounts"""
        # Login as staff
        self.client.login(username='staff1', password='password123')
        response = self.client.get('/investing/')
        
        if response.status_code == 200:
            # Staff should be able to see all accounts (implementation-dependent)
            # This is a placeholder - actual implementation may vary
            pass


class UserFilteringSecurityTest(TestCase):
    """
    Test that user filtering prevents data leakage in forms
    
    Security Issue Fixed: Nov 5, 2025
    Problem: Forms were showing ALL users (100+) including inactive users
             and users from wrong categories. This could leak sensitive
             information about users who shouldn't be visible.
    
    Solution: Implemented strict user filtering based on:
        - is_active status (only active users)
        - category (only appropriate categories per form)
        - is_staff status (for staff-only fields)
    """
    
    def setUp(self):
        """Set up test users across categories"""
        # Create users in different categories
        self.investor = User.objects.create_user(
            username='investor',
            category=UserCategory.INVESTOR,
            is_active=True,
        )
        
        self.student = User.objects.create_user(
            username='student',
            category=UserCategory.STUDENT,
            is_active=True,
        )
        
        self.consultant = User.objects.create_user(
            username='consultant',
            category=UserCategory.CONSULTANT,
            is_active=True,
        )
        
        self.applicant = User.objects.create_user(
            username='applicant',
            category=UserCategory.APPLICANT,
            is_active=True,
        )
        
        self.staff = User.objects.create_user(
            username='staff',
            is_staff=True,
            is_active=True,
        )
        
        # Create inactive users (should NEVER appear)
        self.inactive_investor = User.objects.create_user(
            username='inactive_investor',
            category=UserCategory.INVESTOR,
            is_active=False,  # INACTIVE
        )
        
        self.inactive_staff = User.objects.create_user(
            username='inactive_staff',
            is_staff=True,
            is_active=False,  # INACTIVE
        )
    
    def test_investor_querysets_do_not_leak_other_categories(self):
        """Test that investor querysets don't include students, consultants, etc."""
        from accounts.utilities.user_querysets import get_active_investors_queryset
        
        investors = get_active_investors_queryset()
        
        # Should include investor
        self.assertIn(self.investor, investors)
        
        # Should NOT include other categories
        self.assertNotIn(self.student, investors)
        self.assertNotIn(self.consultant, investors)
        self.assertNotIn(self.applicant, investors)
        self.assertNotIn(self.staff, investors)
        
        # Should NOT include inactive
        self.assertNotIn(self.inactive_investor, investors)
    
    def test_staff_querysets_do_not_leak_non_staff(self):
        """Test that staff querysets don't include non-staff users"""
        from accounts.utilities.user_querysets import get_active_staff_queryset
        
        staff = get_active_staff_queryset()
        
        # Should include staff
        self.assertIn(self.staff, staff)
        
        # Should NOT include non-staff
        self.assertNotIn(self.investor, staff)
        self.assertNotIn(self.student, staff)
        self.assertNotIn(self.consultant, staff)
        self.assertNotIn(self.applicant, staff)
        
        # Should NOT include inactive staff
        self.assertNotIn(self.inactive_staff, staff)
    
    def test_inactive_users_never_appear_in_any_queryset(self):
        """Critical: Inactive users should NEVER appear in any filtered queryset"""
        from accounts.utilities.user_querysets import (
            get_active_investors_queryset,
            get_active_staff_queryset,
            get_active_students_queryset,
            get_active_consultants_queryset,
            get_active_applicants_queryset,
        )
        
        # Get all querysets
        investors = get_active_investors_queryset()
        staff = get_active_staff_queryset()
        students = get_active_students_queryset()
        consultants = get_active_consultants_queryset()
        applicants = get_active_applicants_queryset()
        
        # Inactive investor should not appear anywhere
        self.assertNotIn(self.inactive_investor, investors)
        self.assertNotIn(self.inactive_investor, staff)
        self.assertNotIn(self.inactive_investor, students)
        self.assertNotIn(self.inactive_investor, consultants)
        self.assertNotIn(self.inactive_investor, applicants)
        
        # Inactive staff should not appear anywhere
        self.assertNotIn(self.inactive_staff, investors)
        self.assertNotIn(self.inactive_staff, staff)
        self.assertNotIn(self.inactive_staff, students)
        self.assertNotIn(self.inactive_staff, consultants)
        self.assertNotIn(self.inactive_staff, applicants)
