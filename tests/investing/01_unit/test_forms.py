"""
Unit tests for investing forms

Tests form validation, cleaning, field behavior, error messages, and user filtering.

Author: CODA Development Team
Created: November 6, 2025
Category: Unit Tests
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from investing.forms import (
    ManagedAccountForm,
    OptionsPositionForm,
    TradingSessionForm,
)
from investing.models import ManagedTradingAccount
from accounts.choices import UserCategory

User = get_user_model()


class ManagedAccountFormTest(TestCase):
    """Test ManagedAccountForm validation and user filtering"""
    
    def setUp(self):
        """Set up test data"""
        # Create investors (category=4)
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
        
        # Create inactive investor (should NOT appear in dropdowns)
        self.inactive_investor = User.objects.create_user(
            username='inactive_investor',
            email='inactive@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=False,  # INACTIVE
            first_name='Inactive',
            last_name='Investor'
        )
        
        # Create student (should NOT appear in investor dropdowns)
        self.student = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='password123',
            category=UserCategory.STUDENT,
            is_active=True,
            first_name='Student',
            last_name='User'
        )
        
        # Create staff members
        self.staff1 = User.objects.create_user(
            username='staff1',
            email='staff1@test.com',
            password='password123',
            is_staff=True,
            is_active=True,
            first_name='Manager',
            last_name='One'
        )
        
        self.staff2 = User.objects.create_user(
            username='staff2',
            email='staff2@test.com',
            password='password123',
            is_staff=True,
            is_active=True,
            first_name='Manager',
            last_name='Two'
        )
        
        # Create inactive staff (should NOT appear)
        self.inactive_staff = User.objects.create_user(
            username='inactive_staff',
            email='inactive_staff@test.com',
            password='password123',
            is_staff=True,
            is_active=False,  # INACTIVE
            first_name='Inactive',
            last_name='Staff'
        )
    
    def test_client_field_shows_only_active_investors(self):
        """
        Test that client field shows ONLY active investors
        
        This is a critical fix from Nov 5, 2025:
        - Before: All 100+ users appeared in dropdown
        - After: Only active investors (category=4, is_active=True)
        
        Expected: 2 investors (investor1, investor2)
        Should NOT include: inactive_investor, student, staff
        """
        form = ManagedAccountForm()
        client_queryset = form.fields['client'].queryset
        
        # Should have exactly 2 active investors
        self.assertEqual(client_queryset.count(), 2)
        
        # Should include active investors
        self.assertIn(self.investor1, client_queryset)
        self.assertIn(self.investor2, client_queryset)
        
        # Should NOT include inactive investor
        self.assertNotIn(self.inactive_investor, client_queryset)
        
        # Should NOT include student (wrong category)
        self.assertNotIn(self.student, client_queryset)
        
        # Should NOT include staff (wrong category)
        self.assertNotIn(self.staff1, client_queryset)
    
    def test_account_manager_field_shows_only_active_staff(self):
        """
        Test that account_manager field shows ONLY active staff
        
        Expected: 2 staff members (staff1, staff2)
        Should NOT include: inactive_staff, investors, students
        """
        form = ManagedAccountForm()
        manager_queryset = form.fields['account_manager'].queryset
        
        # Should have exactly 2 active staff
        self.assertEqual(manager_queryset.count(), 2)
        
        # Should include active staff
        self.assertIn(self.staff1, manager_queryset)
        self.assertIn(self.staff2, manager_queryset)
        
        # Should NOT include inactive staff
        self.assertNotIn(self.inactive_staff, manager_queryset)
        
        # Should NOT include investors (not staff)
        self.assertNotIn(self.investor1, manager_queryset)
        
        # Should NOT include students (not staff)
        self.assertNotIn(self.student, manager_queryset)
    
    def test_form_valid_with_correct_data(self):
        """Test that form accepts valid data"""
        form_data = {
            'client': self.investor1.id,
            'account_manager': self.staff1.id,
            'account_number': 'TEST001',
            'account_name': 'Test Trading Account',
            'broker': 'tastytrade',
            'fee_tier': 'balanced',
            'initial_capital': Decimal('10000.00'),
            'status': 'active',
        }
        
        form = ManagedAccountForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
    
    def test_form_invalid_with_missing_required_fields(self):
        """Test that form rejects data with missing required fields"""
        form_data = {
            'client': self.investor1.id,
            # Missing account_number, broker, fee_tier, etc.
        }
        
        form = ManagedAccountForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Check that required fields have errors
        self.assertIn('account_number', form.errors)
        self.assertIn('broker', form.errors)
    
    def test_form_empty_labels_are_descriptive(self):
        """Test that dropdown empty labels are clear and helpful"""
        form = ManagedAccountForm()
        
        # Client field should have descriptive empty label
        client_empty_label = form.fields['client'].empty_label
        self.assertIsNotNone(client_empty_label)
        self.assertIn('Client', client_empty_label)
        self.assertIn('Investor', client_empty_label)
        
        # Account Manager field should have descriptive empty label
        manager_empty_label = form.fields['account_manager'].empty_label
        self.assertIsNotNone(manager_empty_label)
        self.assertIn('Account Manager', manager_empty_label)
        self.assertIn('Staff', manager_empty_label)


class OptionsPositionFormTest(TestCase):
    """Test OptionsPositionForm validation"""
    
    def setUp(self):
        """Set up test data"""
        self.investor = User.objects.create_user(
            username='investor1',
            email='investor1@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
        )
        
        # Create active account
        self.active_account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='ACTIVE001',
            account_name='Active Account',
            broker='tastytrade',
            fee_tier='balanced',
            initial_capital=Decimal('10000.00'),
            status='active',
        )
        
        # Create paused account
        self.paused_account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='PAUSED001',
            account_name='Paused Account',
            broker='tastytrade',
            fee_tier='balanced',
            initial_capital=Decimal('10000.00'),
            status='paused',
        )
        
        # Create closed account (should NOT appear)
        self.closed_account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='CLOSED001',
            account_name='Closed Account',
            broker='tastytrade',
            fee_tier='balanced',
            initial_capital=Decimal('10000.00'),
            status='closed',
        )
    
    def test_managed_account_field_shows_only_active_and_paused(self):
        """
        Test that managed_account field shows ONLY active and paused accounts
        
        Positions can be opened on active accounts, and we need to see paused
        accounts to manage existing positions.
        """
        form = OptionsPositionForm()
        account_queryset = form.fields['managed_account'].queryset
        
        # Should have 2 accounts (active and paused)
        self.assertEqual(account_queryset.count(), 2)
        
        # Should include active account
        self.assertIn(self.active_account, account_queryset)
        
        # Should include paused account
        self.assertIn(self.paused_account, account_queryset)
        
        # Should NOT include closed account
        self.assertNotIn(self.closed_account, account_queryset)


class TradingSessionFormTest(TestCase):
    """Test TradingSessionForm validation"""
    
    def setUp(self):
        """Set up test data"""
        self.investor = User.objects.create_user(
            username='investor1',
            email='investor1@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
        )
        
        # Create independent account (should NOT appear in TradingSession form)
        self.independent_account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='IND001',
            account_name='Independent Account',
            broker='tastytrade',
            fee_tier='balanced',  # Balanced tier
            initial_capital=Decimal('10000.00'),
            status='active',
        )
        
        # Create consultative account (SHOULD appear)
        self.consultative_account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='CONS001',
            account_name='Consultative Account',
            broker='tastytrade',
            fee_tier='consultative',  # Consultative tier
            initial_capital=Decimal('10000.00'),
            status='active',
        )
        
        # Create consultative but closed account (should NOT appear)
        self.closed_consultative = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='CONS002',
            account_name='Closed Consultative',
            broker='tastytrade',
            fee_tier='consultative',
            initial_capital=Decimal('10000.00'),
            status='closed',  # Closed
        )
    
    def test_managed_account_field_shows_only_consultative_accounts(self):
        """
        Test that TradingSession form shows ONLY consultative tier accounts
        
        Trading sessions are only for consultative accounts (live trading with guidance).
        Independent accounts don't need sessions.
        """
        form = TradingSessionForm()
        account_queryset = form.fields['managed_account'].queryset
        
        # Should have 1 account (consultative + active)
        self.assertEqual(account_queryset.count(), 1)
        
        # Should include consultative account
        self.assertIn(self.consultative_account, account_queryset)
        
        # Should NOT include independent account
        self.assertNotIn(self.independent_account, account_queryset)
        
        # Should NOT include closed consultative
        self.assertNotIn(self.closed_consultative, account_queryset)
    
    def test_form_empty_label_is_descriptive(self):
        """Test that dropdown empty label is clear"""
        form = TradingSessionForm()
        
        empty_label = form.fields['managed_account'].empty_label
        self.assertIsNotNone(empty_label)
        self.assertIn('Consultative', empty_label)
