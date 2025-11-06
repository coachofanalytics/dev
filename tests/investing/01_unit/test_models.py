"""
Unit tests for investing models

Tests individual model methods, properties, validation, and business logic.

Author: CODA Development Team
Created: November 6, 2025
Category: Unit Tests
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from investing.models import (
    ManagedTradingAccount,
    OptionsPosition,
    TradingSession,
    TradingRule,
    Investor_Information,
)
from accounts.choices import UserCategory

User = get_user_model()


class ManagedTradingAccountModelTest(TestCase):
    """Test ManagedTradingAccount model"""
    
    def setUp(self):
        """Set up test data"""
        # Create test investor
        self.investor = User.objects.create_user(
            username='investor_test',
            email='investor@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
            first_name='John',
            last_name='Investor'
        )
        
        # Create test staff member (account manager)
        self.manager = User.objects.create_user(
            username='manager_test',
            email='manager@test.com',
            password='password123',
            is_staff=True,
            is_active=True,
            first_name='Jane',
            last_name='Manager'
        )
        
        # Create test managed account
        self.account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_manager=self.manager,
            account_number='TEST001',
            account_name='Test Trading Account',
            broker='tastytrade',
            fee_tier='independent',
            initial_capital=Decimal('10000.00'),
            current_balance=Decimal('12000.00'),
            cash_available=Decimal('5000.00'),
            cash_reserved=Decimal('2000.00'),
            status='active',
        )
    
    def test_account_creation(self):
        """Test that managed account can be created with valid data"""
        self.assertEqual(self.account.account_number, 'TEST001')
        self.assertEqual(self.account.client, self.investor)
        self.assertEqual(self.account.account_manager, self.manager)
        self.assertEqual(self.account.initial_capital, Decimal('10000.00'))
        self.assertEqual(self.account.status, 'active')
    
    def test_account_str_method(self):
        """Test __str__ method returns expected format"""
        expected = f"{self.account.account_number} - {self.investor.get_full_name()}"
        self.assertEqual(str(self.account), expected)
    
    def test_available_buying_power_property(self):
        """Test available_buying_power property calculation"""
        # Test normal case
        buying_power = self.account.available_buying_power
        expected = Decimal('5000.00') - Decimal('2000.00')  # cash_available - cash_reserved
        self.assertEqual(buying_power, expected)
    
    def test_available_buying_power_with_none_values(self):
        """
        Test that available_buying_power handles None values gracefully
        
        Regression test for TypeError fixed on Nov 5, 2025:
        Bug: unsupported operand type(s) for -: 'NoneType' and 'decimal.Decimal'
        Fix: Added None checks in @property methods
        """
        # Create account with None values
        account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST002',
            account_name='Test Account with None',
            broker='tastytrade',
            fee_tier='independent',
            initial_capital=Decimal('10000.00'),
            current_balance=None,  # None value
            cash_available=None,   # None value
            cash_reserved=None,    # None value
            status='active',
        )
        
        # Should return Decimal('0.00') instead of raising TypeError
        buying_power = account.available_buying_power
        self.assertEqual(buying_power, Decimal('0.00'))
    
    def test_return_on_investment_property(self):
        """Test ROI calculation"""
        roi = self.account.return_on_investment
        # ROI = ((12000 - 10000) / 10000) * 100 = 20%
        expected = Decimal('20.00')
        self.assertEqual(roi, expected)
    
    def test_return_on_investment_with_none_balance(self):
        """Test that ROI handles None current_balance gracefully"""
        account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST003',
            account_name='Test Account',
            broker='tastytrade',
            fee_tier='independent',
            initial_capital=Decimal('10000.00'),
            current_balance=None,  # None value
            status='active',
        )
        
        roi = account.return_on_investment
        self.assertEqual(roi, Decimal('0.00'))
    
    def test_return_on_investment_with_zero_initial_capital(self):
        """Test that ROI handles zero initial_capital gracefully"""
        account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST004',
            account_name='Test Account',
            broker='tastytrade',
            fee_tier='independent',
            initial_capital=Decimal('0.00'),  # Zero
            current_balance=Decimal('5000.00'),
            status='active',
        )
        
        roi = account.return_on_investment
        self.assertEqual(roi, Decimal('0.00'))
    
    def test_current_risk_exposure_property(self):
        """Test current_risk_exposure calculation with positions"""
        # This property requires positions, which we'll test in integration tests
        # For now, test that it handles None current_balance
        account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST005',
            account_name='Test Account',
            broker='tastytrade',
            fee_tier='independent',
            initial_capital=Decimal('10000.00'),
            current_balance=None,  # None value
            status='active',
        )
        
        risk = account.current_risk_exposure
        self.assertEqual(risk, Decimal('0.00'))
    
    def test_broker_choices(self):
        """Test that only valid brokers are accepted"""
        valid_brokers = ['tastytrade', 'schwab', 'etrade', 'td_ameritrade', 'interactive_brokers', 'other']
        
        for broker in valid_brokers:
            account = ManagedTradingAccount(
                client=self.investor,
                account_number=f'TEST_{broker}',
                account_name=f'Test {broker}',
                broker=broker,
                fee_tier='independent',
                initial_capital=Decimal('10000.00'),
                status='active',
            )
            # Should not raise ValidationError
            account.full_clean()
    
    def test_fee_tier_choices(self):
        """Test that only valid fee tiers are accepted"""
        valid_tiers = ['independent', 'consultative', 'full_service']
        
        for tier in valid_tiers:
            account = ManagedTradingAccount(
                client=self.investor,
                account_number=f'TEST_{tier}',
                account_name=f'Test {tier}',
                broker='tastytrade',
                fee_tier=tier,
                initial_capital=Decimal('10000.00'),
                status='active',
            )
            # Should not raise ValidationError
            account.full_clean()
    
    def test_status_choices(self):
        """Test that only valid statuses are accepted"""
        valid_statuses = ['pending', 'active', 'paused', 'closed']
        
        for status in valid_statuses:
            account = ManagedTradingAccount(
                client=self.investor,
                account_number=f'TEST_{status}',
                account_name=f'Test {status}',
                broker='tastytrade',
                fee_tier='independent',
                initial_capital=Decimal('10000.00'),
                status=status,
            )
            # Should not raise ValidationError
            account.full_clean()


class OptionsPositionModelTest(TestCase):
    """Test OptionsPosition model"""
    
    def setUp(self):
        """Set up test data"""
        self.investor = User.objects.create_user(
            username='investor_test',
            email='investor@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
        )
        
        self.account = ManagedTradingAccount.objects.create(
            client=self.investor,
            account_number='TEST001',
            account_name='Test Account',
            broker='tastytrade',
            fee_tier='independent',
            initial_capital=Decimal('10000.00'),
            current_balance=Decimal('10000.00'),
            status='active',
        )
    
    def test_position_creation(self):
        """Test that options position can be created"""
        position = OptionsPosition.objects.create(
            managed_account=self.account,
            symbol='SPY',
            strategy='short_put',
            strike_price=Decimal('450.00'),
            expiration_date=date.today() + timedelta(days=30),
            contracts=1,
            premium_collected=Decimal('100.00'),
            status='open',
        )
        
        self.assertEqual(position.symbol, 'SPY')
        self.assertEqual(position.strategy, 'short_put')
        self.assertEqual(position.contracts, 1)
        self.assertEqual(position.status, 'open')
    
    def test_position_str_method(self):
        """Test __str__ method returns expected format"""
        position = OptionsPosition.objects.create(
            managed_account=self.account,
            symbol='SPY',
            strategy='short_put',
            strike_price=Decimal('450.00'),
            expiration_date=date.today() + timedelta(days=30),
            contracts=1,
            premium_collected=Decimal('100.00'),
            status='open',
        )
        
        # Should include symbol and strategy
        self.assertIn('SPY', str(position))
        self.assertIn('short_put', str(position))
    
    def test_strategy_choices(self):
        """Test that only valid strategies are accepted"""
        valid_strategies = [
            'short_put', 'short_call', 'covered_call', 
            'credit_spread', 'iron_condor', 'other'
        ]
        
        for strategy in valid_strategies:
            position = OptionsPosition(
                managed_account=self.account,
                symbol='SPY',
                strategy=strategy,
                strike_price=Decimal('450.00'),
                expiration_date=date.today() + timedelta(days=30),
                contracts=1,
                premium_collected=Decimal('100.00'),
                status='open',
            )
            # Should not raise ValidationError
            position.full_clean()


class InvestorInformationModelTest(TestCase):
    """Test Investor_Information model"""
    
    def setUp(self):
        """Set up test data"""
        self.investor = User.objects.create_user(
            username='investor_test',
            email='investor@test.com',
            password='password123',
            category=UserCategory.INVESTOR,
            is_active=True,
        )
    
    def test_investor_info_creation(self):
        """Test that investor information can be created"""
        info = Investor_Information.objects.create(
            investor=self.investor,
            amount_invested=Decimal('5000.00'),
            investment_type='equity',
            duration=12,
        )
        
        self.assertEqual(info.investor, self.investor)
        self.assertEqual(info.amount_invested, Decimal('5000.00'))
        self.assertEqual(info.investment_type, 'equity')
    
    def test_minimum_investment_validation(self):
        """Test that minimum investment of $1,000 is enforced"""
        info = Investor_Information(
            investor=self.investor,
            amount_invested=Decimal('500.00'),  # Below minimum
            investment_type='equity',
        )
        
        # Should raise ValidationError
        with self.assertRaises(ValidationError):
            info.full_clean()
    
    def test_revenue_share_percentage_validation(self):
        """Test that revenue share percentage is validated (0-50%)"""
        # Test max value (50%)
        info = Investor_Information(
            investor=self.investor,
            amount_invested=Decimal('5000.00'),
            investment_type='revenue_share',
            revenue_share_percentage=Decimal('50.00'),
        )
        info.full_clean()  # Should not raise
        
        # Test over max value (51%)
        info2 = Investor_Information(
            investor=self.investor,
            amount_invested=Decimal('5000.00'),
            investment_type='revenue_share',
            revenue_share_percentage=Decimal('51.00'),  # Over max
        )
        
        with self.assertRaises(ValidationError):
            info2.full_clean()
