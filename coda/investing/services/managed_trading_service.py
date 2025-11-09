"""
Managed Trading Service
Core business logic for managing client options accounts

This service handles:
- Account creation and management
- Position entry and exit
- Fee calculations
- Performance tracking
- Risk validation
"""

import logging
from decimal import Decimal, InvalidOperation
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from ..models import (
    ManagedTradingAccount,
    OptionsPosition,
    TradingRule,
    TradingActivity,
    TradingSession
)
from .base_service import BaseInvestingService

logger = logging.getLogger(__name__)
User = get_user_model()


class ManagedTradingService(BaseInvestingService):
    MANAGED_INCOME_TARGET = Decimal(str(getattr(settings, 'MANAGED_INCOME_TARGET', '420')))
    SCENARIO_MAX_MULTIPLIER = Decimal('2')
    SCENARIO_STEP = Decimal('2500')
    """
    Service for managed options trading operations
    
    Provides methods for:
    - Creating and managing trading accounts
    - Entering and closing positions
    - Calculating fees
    - Generating account summaries
    """
    
    def create_managed_account(
        self, 
        client_user: User, 
        account_data: Dict
    ) -> ManagedTradingAccount:
        """
        Create new managed trading account
        
        Args:
            client_user: User instance (client)
            account_data: Dict with account parameters
                Required: account_name, initial_capital
                Optional: account_manager, fee_tier, management_fee_percentage,
                         performance_fee_percentage, etc.
        
        Returns:
            ManagedTradingAccount instance
        
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate user
            self._validate_user(client_user)
            
            # Validate initial capital
            initial_capital = Decimal(str(account_data.get('initial_capital', 0)))
            if initial_capital < Decimal('5000.00'):
                raise ValidationError('Minimum account size is $5,000')
            
            with transaction.atomic():
                # Generate account number
                account_number = self._generate_account_number()
                
                # Get account manager (defaults to current user if staff)
                account_manager = account_data.get('account_manager')
                
                # Create account
                account = ManagedTradingAccount.objects.create(
                    client=client_user,
                    account_name=account_data.get('account_name', f"{client_user.get_full_name()} - Options Account"),
                    account_number=account_number,
                    initial_capital=initial_capital,
                    current_balance=initial_capital,
                    cash_available=initial_capital,
                    cash_reserved=Decimal('0.00'),
                    high_water_mark=initial_capital,
                    account_manager=account_manager,
                    fee_tier=account_data.get('fee_tier', 'professional'),
                    management_fee_percentage=account_data.get('management_fee_percentage', Decimal('1.50')),
                    performance_fee_percentage=account_data.get('performance_fee_percentage', Decimal('20.00')),
                    performance_threshold=account_data.get('performance_threshold', Decimal('8.00')),
                    status='active',
                    activation_date=date.today()
                )
                
                # Create default trading rules
                self._create_default_trading_rules(account)
                
                # Log activity
                TradingActivity.objects.create(
                    managed_account=account,
                    activity_type='account_created',
                    description=f'Managed account created with ${account.initial_capital:,.2f}',
                    performed_by=account_manager,
                    data_snapshot={
                        'initial_capital': str(account.initial_capital),
                        'fee_tier': account.fee_tier,
                        'management_fee': str(account.management_fee_percentage),
                        'performance_fee': str(account.performance_fee_percentage)
                    }
                )
                
                logger.info(f"Created managed account {account.account_number} for {client_user.username}")
                
                return account
                
        except Exception as e:
            logger.error(f"Error creating managed account: {e}")
            raise ValidationError(f"Failed to create account: {str(e)}")
    
    def _generate_account_number(self) -> str:
        """Generate unique account number"""
        prefix = 'CODA-OPT'
        
        # Get count of existing accounts
        count = ManagedTradingAccount.objects.count() + 1
        
        # Format: CODA-OPT-001, CODA-OPT-002, etc.
        account_number = f"{prefix}-{count:03d}"
        
        # Ensure uniqueness
        while ManagedTradingAccount.objects.filter(account_number=account_number).exists():
            count += 1
            account_number = f"{prefix}-{count:03d}"
        
        return account_number
    
    def _create_default_trading_rules(self, account: ManagedTradingAccount):
        """
        Create standard trading rules for account
        
        Industry Standards:
        - Single position risk: 2-5% of total capital (we use 2% as conservative)
        - Total portfolio exposure: 15-25% of capital
        - Daily loss limit: 2% of capital
        """
        default_rules = [
            {
                'name': 'Max Position Size',
                'type': 'position_limit',
                'config': {
                    'max_position_size': float(account.max_position_risk),
                    'max_contracts': 3
                },
                'priority': 1
            },
            {
                'name': 'Position Sizing - % of Capital',
                'type': 'position_size_percentage',
                'config': {
                    'max_percentage_per_position': 2.0,  # Industry standard: 2-5%, we use 2%
                    'description': 'No single position can use more than 2% of total capital'
                },
                'priority': 1  # High priority - critical risk control
            },
            {
                'name': 'Total Portfolio Exposure',
                'type': 'exposure_limit',
                'config': {
                    'max_total_exposure_percentage': 15.0,  # 15% of total capital deployed
                    'description': 'Total capital deployed cannot exceed 15% of account value'
                },
                'priority': 1
            },
            {
                'name': 'Profit Target',
                'type': 'profit_target',
                'config': {
                    'target_percentage': 50,
                    'recommend_close': True
                },
                'priority': 2
            },
            {
                'name': 'Stop Loss',
                'type': 'stop_loss',
                'config': {
                    'loss_percentage': 200,
                    'auto_close': False,
                    'alert_on_hit': True
                },
                'priority': 1
            },
            {
                'name': 'Daily Loss Limit',
                'type': 'risk_limit',
                'config': {
                    'max_daily_loss': float(account.max_daily_loss),
                    'pause_trading_on_breach': True
                },
                'priority': 1
            },
            {
                'name': 'Expiration Management',
                'type': 'time_based',
                'config': {
                    'close_days_before_expiry': 5,
                    'auto_close': False,
                    'send_alert': True
                },
                'priority': 2
            }
        ]
        
        for rule_data in default_rules:
            TradingRule.objects.create(
                managed_account=account,
                rule_name=rule_data['name'],
                rule_type=rule_data['type'],
                rule_config=rule_data['config'],
                priority=rule_data['priority'],
                is_active=True
            )
    
    def create_position(
        self,
        account: ManagedTradingAccount,
        position_data: Dict,
        deduct_balance: bool = True
    ) -> OptionsPosition:
        """
        Create new options position
        
        Args:
            account: ManagedTradingAccount instance
            position_data: Dict with position details
                Required: symbol, strategy, positions (JSONField),
                         capital_required, premium_collected, max_profit, max_loss,
                         expiration_date
            deduct_balance: Whether to deduct balance immediately (default True)
                           Set to False for pending positions that require client approval
        
        Returns:
            OptionsPosition instance
        
        Raises:
            ValidationError: If validation fails or rules violated
        """
        try:
            with transaction.atomic():
                # Validate account status
                if account.status != 'active':
                    raise ValidationError('Account is not active')
                
                if not account.trading_enabled:
                    raise ValidationError('Trading is disabled for this account')
                
                # Validate buying power
                capital_required = Decimal(str(position_data['capital_required']))
                if capital_required > account.available_buying_power:
                    raise ValidationError(
                        f'Insufficient buying power. Available: ${account.available_buying_power:,.2f}'
                    )
                
                # Validate against trading rules
                self._validate_position_against_rules(account, position_data)
                
                entered_timestamp = timezone.now() if deduct_balance else None
                
                # Create position
                position = OptionsPosition.objects.create(
                    managed_account=account,
                    symbol=position_data['symbol'].upper(),
                    strategy=position_data['strategy'],
                    positions=position_data['positions'],
                    capital_required=capital_required,
                    premium_collected=Decimal(str(position_data['premium_collected'])),
                    max_profit=Decimal(str(position_data['max_profit'])),
                    max_loss=Decimal(str(position_data['max_loss'])),
                    position_delta=Decimal(str(position_data.get('position_delta', '0.0000'))),
                    position_theta=Decimal(str(position_data.get('position_theta', '0.0000'))),
                    position_gamma=Decimal(str(position_data.get('position_gamma', '0.0000'))),
                    position_vega=Decimal(str(position_data.get('position_vega', '0.0000'))),
                    expiration_date=position_data['expiration_date'],
                    notes=position_data.get('notes', ''),
                    status='open' if deduct_balance else 'pending',
                    entered_at=entered_timestamp,
                    entered_by=account.account_manager if deduct_balance else None
                )
                
                # Update account balances (only if not pending approval)
                if deduct_balance:
                    account.cash_reserved += capital_required
                    account.cash_available -= capital_required
                    account.save(update_fields=['cash_reserved', 'cash_available', 'updated_at'])
                    
                    # Log activity
                    TradingActivity.objects.create(
                        managed_account=account,
                        position=position,
                        activity_type='position_opened',
                        description=f'Opened {position.symbol} {position.get_strategy_display()} position',
                        performed_by=account.account_manager,
                        data_snapshot={
                            'symbol': position.symbol,
                            'strategy': position.strategy,
                            'capital_required': str(capital_required),
                            'premium_collected': str(position.premium_collected),
                            'expiration_date': str(position.expiration_date)
                        }
                    )
                    logger.info(f"Created and opened position {position.id} for account {account.account_number}")
                else:
                    logger.info(f"Created pending position {position.id} for account {account.account_number} (balance not deducted)")
                
                return position
                
        except Exception as e:
            logger.error(f"Error creating position: {e}")
            raise ValidationError(f"Failed to create position: {str(e)}")
    
    def confirm_auto_approved_entry(
        self,
        position: OptionsPosition,
        trader: Optional[User] = None,
    ) -> OptionsPosition:
        """
        Confirm that a previously auto-approved (pending) position is now live.
        
        Deducts capital, stamps entry metadata, and logs activity.
        """
        if position.status != 'pending':
            raise ValidationError('Only pending positions can be marked as entered.')
        
        try:
            with transaction.atomic():
                account = position.managed_account
                
                if position.capital_required > account.available_buying_power:
                    raise ValidationError(
                        f'Insufficient buying power. Available: ${account.available_buying_power:,.2f}'
                    )
                
                entry_time = timezone.now()
                
                position.status = 'open'
                if not position.approved_at:
                    position.approved_at = entry_time
                position.entered_at = entry_time
                position.entered_by = trader
                position.auto_approved = False
                position.requires_client_approval = False
                position.save(update_fields=[
                    'status',
                    'approved_at',
                    'entered_at',
                    'entered_by',
                    'auto_approved',
                    'requires_client_approval',
                    'updated_at',
                ])
                
                account.cash_reserved += position.capital_required
                account.cash_available -= position.capital_required
                account.save(update_fields=['cash_reserved', 'cash_available', 'updated_at'])
                
                TradingActivity.objects.create(
                    managed_account=account,
                    position=position,
                    activity_type='position_opened',
                    description=f'Trader confirmed entry for {position.symbol} position.',
                    performed_by=trader,
                    data_snapshot={
                        'symbol': position.symbol,
                        'capital_required': str(position.capital_required),
                        'premium_collected': str(position.premium_collected),
                        'auto_approved_at': str(position.auto_approved_at) if position.auto_approved_at else None,
                    }
                )
                
                logger.info(
                    "Confirmed entry for position %s on account %s",
                    position.id,
                    account.account_number,
                )
                
                return position
        except ValidationError:
            raise
        except Exception as exc:
            logger.error("Error confirming auto-approved entry: %s", exc)
            raise ValidationError(f"Failed to confirm position entry: {exc}")
    
    def _validate_position_against_rules(
        self,
        account: ManagedTradingAccount,
        position_data: Dict
    ):
        """
        Validate position against account trading rules
        
        Enforces:
        - Position size limits (absolute dollar amount)
        - Position size as % of capital (industry standard: 2-5%)
        - Total portfolio exposure limits
        """
        active_rules = account.trading_rules.filter(is_active=True)
        
        capital_required = Decimal(str(position_data['capital_required']))
        total_capital = account.initial_capital  # Use initial capital for % calculations
        
        for rule in active_rules:
            config = rule.rule_config
            
            # Position size limit (absolute)
            if rule.rule_type == 'position_limit':
                max_size = Decimal(str(config.get('max_position_size', 0)))
                if capital_required > max_size:
                    raise ValidationError(
                        f'Position size ${capital_required:,.2f} exceeds limit ${max_size:,.2f}'
                    )
            
            # Position size as % of capital (INDUSTRY STANDARD)
            elif rule.rule_type == 'position_size_percentage':
                max_percentage = Decimal(str(config.get('max_percentage_per_position', 2.0)))
                position_percentage = (capital_required / total_capital) * 100
                
                if position_percentage > max_percentage:
                    raise ValidationError(
                        f'Position size ${capital_required:,.2f} is {position_percentage:.2f}% of capital. '
                        f'Maximum allowed: {max_percentage}% (${(total_capital * max_percentage / 100):,.2f}). '
                        f'Industry standard: No single position should exceed 2-5% of total capital.'
                    )
            
            # Total portfolio exposure
            elif rule.rule_type == 'exposure_limit':
                # Calculate current + new exposure
                current_deployed = account.cash_reserved
                max_exposure_pct = Decimal(str(config.get('max_total_exposure_percentage', 15.0)))
                max_exposure_amount = (total_capital * max_exposure_pct) / 100
                
                new_total_deployed = current_deployed + capital_required
                new_exposure_pct = (new_total_deployed / total_capital) * 100
                
                if new_total_deployed > max_exposure_amount:
                    raise ValidationError(
                        f'Total capital deployed would be ${new_total_deployed:,.2f} ({new_exposure_pct:.2f}% of capital). '
                        f'Maximum allowed: {max_exposure_pct}% (${max_exposure_amount:,.2f}). '
                        f'Currently deployed: ${current_deployed:,.2f}. '
                        f'This position requires: ${capital_required:,.2f}.'
                    )
    
    def close_position(
        self,
        position: OptionsPosition,
        exit_data: Dict
    ) -> OptionsPosition:
        """
        Close options position
        
        Args:
            position: OptionsPosition instance
            exit_data: Dict with exit details
                Required: exit_price, exit_reason
                Optional: notes
        
        Returns:
            Updated OptionsPosition instance
        """
        try:
            with transaction.atomic():
                account = position.managed_account
                
                # Update position
                position.exit_date = date.today()
                position.exit_price = Decimal(str(exit_data['exit_price']))
                position.exit_reason = exit_data['exit_reason']
                position.status = 'closed'
                
                # Calculate realized P&L
                position.realized_pnl = position.premium_collected - position.exit_price
                position.unrealized_pnl = Decimal('0.00')
                
                # Append notes if provided
                if exit_data.get('notes'):
                    position.notes += f"\n\nExit Notes: {exit_data['notes']}"
                
                position.save()
                
                # Update account balances
                account.cash_reserved -= position.capital_required
                account.cash_available += position.capital_required
                account.current_balance += position.realized_pnl
                
                # Update performance tracking
                account.total_trades += 1
                if position.realized_pnl > 0:
                    account.winning_trades += 1
                else:
                    account.losing_trades += 1
                
                account.total_profit_loss += position.realized_pnl
                
                # Update high water mark if applicable
                if account.current_balance > account.high_water_mark:
                    account.high_water_mark = account.current_balance
                
                account.save(update_fields=[
                    'cash_reserved', 'cash_available', 'current_balance',
                    'total_trades', 'winning_trades', 'losing_trades',
                    'total_profit_loss', 'high_water_mark', 'updated_at'
                ])
                
                # Log activity
                TradingActivity.objects.create(
                    managed_account=account,
                    position=position,
                    activity_type='position_closed',
                    description=f'Closed {position.symbol} position - P&L: ${position.realized_pnl:,.2f}',
                    performed_by=account.account_manager,
                    data_snapshot={
                        'symbol': position.symbol,
                        'exit_price': str(position.exit_price),
                        'realized_pnl': str(position.realized_pnl),
                        'exit_reason': position.exit_reason,
                        'days_in_trade': position.days_in_trade
                    }
                )
                
                logger.info(f"Closed position {position.id} with P&L: ${position.realized_pnl}")
                
                return position
                
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            raise ValidationError(f"Failed to close position: {str(e)}")
    
    def calculate_fees(
        self,
        account: ManagedTradingAccount,
        period_start: date = None,
        period_end: date = None
    ) -> Dict:
        """
        Calculate fees for account based on fee tier
        
        Args:
            account: ManagedTradingAccount instance
            period_start: Start date for fee calculation (defaults to last calculation)
            period_end: End date for fee calculation (defaults to today)
        
        Returns:
            Dict with fee breakdown
        """
        if not period_end:
            period_end = date.today()
        
        if not period_start:
            period_start = account.last_fee_calculation_date or account.activation_date or period_end
        
        # Calculate based on fee tier
        if account.fee_tier == 'consultative':
            return self._calculate_consultative_fees(account, period_start, period_end)
        elif account.fee_tier == 'starter':
            return self._calculate_starter_fees(account)
        elif account.fee_tier == 'professional':
            return self._calculate_professional_fees(account)
        elif account.fee_tier == 'premium':
            return self._calculate_premium_fees(account)
        elif account.fee_tier == 'co_invest':
            return self._calculate_co_invest_fees(account)
        else:
            return self._calculate_custom_fees(account)
    
    def _calculate_consultative_fees(
        self,
        account: ManagedTradingAccount,
        period_start: date,
        period_end: date
    ) -> Dict:
        """Calculate fees for consultative tier"""
        # Session fees
        sessions_fee = account.sessions_completed_this_month * account.session_fee
        
        # Platform fee
        platform_fee = account.monthly_platform_fee
        
        # Performance bonus (10% of profit)
        month_profit = account.total_profit_loss
        performance_bonus = month_profit * Decimal('0.10') if month_profit > 0 else Decimal('0.00')
        
        total = sessions_fee + platform_fee + performance_bonus
        
        return {
            'fee_tier': 'consultative',
            'session_fees': sessions_fee,
            'platform_fee': platform_fee,
            'performance_bonus': performance_bonus,
            'total': total,
            'breakdown': f"{account.sessions_completed_this_month} sessions @ ${account.session_fee} + ${platform_fee} platform + ${performance_bonus} performance bonus",
            'period_start': period_start,
            'period_end': period_end
        }
    
    def _calculate_professional_fees(self, account: ManagedTradingAccount) -> Dict:
        """Calculate fees for professional tier (1.5% mgmt + 20% perf above 8% hurdle)"""
        # Annual management fee (prorated monthly)
        annual_mgmt = account.current_balance * (account.management_fee_percentage / Decimal('100'))
        monthly_mgmt = annual_mgmt / Decimal('12')
        
        # Performance fee (only if above high-water mark and hurdle)
        perf_fee = Decimal('0.00')
        if account.current_balance > account.high_water_mark:
            profit_above_hwm = account.current_balance - account.high_water_mark
            hurdle_amount = account.high_water_mark * (account.performance_threshold / Decimal('100'))
            
            if profit_above_hwm > hurdle_amount:
                excess_profit = profit_above_hwm - hurdle_amount
                perf_fee = excess_profit * (account.performance_fee_percentage / Decimal('100'))
        
        total = monthly_mgmt + perf_fee
        
        return {
            'fee_tier': 'professional',
            'management_fee': monthly_mgmt,
            'performance_fee': perf_fee,
            'total': total,
            'breakdown': f"${monthly_mgmt:.2f} mgmt + ${perf_fee:.2f} performance"
        }
    
    def _calculate_starter_fees(self, account: ManagedTradingAccount) -> Dict:
        """Calculate fees for starter tier (0% mgmt + 25% performance)"""
        # Performance fee only
        perf_fee = account.total_profit_loss * Decimal('0.25') if account.total_profit_loss > 0 else Decimal('0.00')
        
        return {
            'fee_tier': 'starter',
            'management_fee': Decimal('0.00'),
            'performance_fee': perf_fee,
            'total': perf_fee,
            'breakdown': f"25% of ${account.total_profit_loss:.2f} profit"
        }
    
    def _calculate_premium_fees(self, account: ManagedTradingAccount) -> Dict:
        """Calculate fees for premium tier (1% mgmt + 15% perf + $500 min)"""
        # Management fee
        annual_mgmt = account.current_balance * Decimal('0.01')
        monthly_mgmt = annual_mgmt / Decimal('12')
        
        # Performance fee
        perf_fee = account.total_profit_loss * Decimal('0.15') if account.total_profit_loss > 0 else Decimal('0.00')
        
        # Monthly minimum
        total = monthly_mgmt + perf_fee
        minimum = Decimal('500.00')
        
        if total < minimum:
            total = minimum
        
        return {
            'fee_tier': 'premium',
            'management_fee': monthly_mgmt,
            'performance_fee': perf_fee,
            'minimum_applied': total == minimum,
            'total': total,
            'breakdown': f"${monthly_mgmt:.2f} mgmt + ${perf_fee:.2f} perf (min $500)"
        }
    
    def _calculate_co_invest_fees(self, account: ManagedTradingAccount) -> Dict:
        """Calculate fees for co-investment tier (50/50 profit split)"""
        # 50% of profit
        coda_share = account.total_profit_loss * Decimal('0.50') if account.total_profit_loss > 0 else Decimal('0.00')
        
        return {
            'fee_tier': 'co_invest',
            'management_fee': Decimal('0.00'),
            'profit_share': coda_share,
            'total': coda_share,
            'breakdown': f"50% of ${account.total_profit_loss:.2f} profit"
        }
    
    def _calculate_custom_fees(self, account: ManagedTradingAccount) -> Dict:
        """Calculate fees for custom tier"""
        # Use default professional calculation
        return self._calculate_professional_fees(account)
    
    def get_account_summary(self, account: ManagedTradingAccount) -> Dict:
        """
        Generate comprehensive account summary
        
        Args:
            account: ManagedTradingAccount instance
        
        Returns:
            Dict with account summary data
        """
        open_positions = account.positions.filter(status='open')
        closed_positions = account.positions.filter(status='closed')
        
        # Calculate totals
        total_unrealized_pnl = sum([pos.unrealized_pnl for pos in open_positions])
        total_realized_pnl = sum([pos.realized_pnl for pos in closed_positions])
        
        # Recent activity
        recent_activity = account.activities.all()[:10]
        
        # Upcoming expirations
        upcoming_expirations = open_positions.filter(
            expiration_date__lte=date.today() + timedelta(days=7)
        ).order_by('expiration_date')
        
        # Calculate fees
        current_fees = self.calculate_fees(account)
        
        return {
            'account': account,
            'summary': {
                'account_number': account.account_number,
                'client_name': account.client.get_full_name(),
                'status': account.status,
                'fee_tier': account.get_fee_tier_display(),
                'current_balance': account.current_balance,
                'initial_capital': account.initial_capital,
                'total_profit_loss': account.total_profit_loss,
                'return_on_investment': account.return_on_investment,
                'available_buying_power': account.available_buying_power,
                'cash_reserved': account.cash_reserved,
                'risk_exposure': account.current_risk_exposure,
            },
            'performance': {
                'total_trades': account.total_trades,
                'winning_trades': account.winning_trades,
                'losing_trades': account.losing_trades,
                'win_rate': account.win_rate,
                'total_realized_pnl': total_realized_pnl,
                'total_unrealized_pnl': total_unrealized_pnl,
            },
            'positions': {
                'open_count': open_positions.count(),
                'open_positions': list(open_positions),
                'closed_count': closed_positions.count(),
                'recent_closed': list(closed_positions[:5]),
                'upcoming_expirations': list(upcoming_expirations),
            },
            'fees': current_fees,
            'activity': {
                'recent': list(recent_activity),
            },
            'income_summary': self.get_income_summary(account),
            'whales_timeline': self.get_whales_timeline(account),
        }

    # ------------------------------------------------------------------ #
    # Phase 3: Client managed outcomes helpers
    # ------------------------------------------------------------------ #

    def get_income_summary(self, account: ManagedTradingAccount, months: int = 3) -> Dict:
        """
        Aggregate managed-income metrics for client dashboard.
        """
        now = timezone.now()
        start_of_month = date(year=now.year, month=now.month, day=1)
        target_income = self.MANAGED_INCOME_TARGET

        def _to_decimal(value) -> Decimal:
            if value is None:
                return Decimal('0')
            if isinstance(value, Decimal):
                return value
            try:
                return Decimal(str(value))
            except (InvalidOperation, TypeError, ValueError):
                return Decimal('0')

        positions = account.positions.all()

        closed_this_month = positions.filter(
            status='closed',
            exit_date__gte=start_of_month
        )
        realized_income_mtd = _to_decimal(
            closed_this_month.aggregate(total=Sum('realized_pnl'))['total']
        )

        premium_this_month = _to_decimal(
            positions.filter(entry_date__gte=start_of_month).aggregate(total=Sum('premium_collected'))['total']
        )

        projected_income = realized_income_mtd + premium_this_month
        coverage_pct = Decimal('0')
        if target_income > 0:
            coverage_pct = (projected_income / target_income) * Decimal('100')

        coverage_pct_clamped = coverage_pct
        if coverage_pct_clamped > Decimal('100'):
            coverage_pct_clamped = Decimal('100')
        elif coverage_pct_clamped < Decimal('0'):
            coverage_pct_clamped = Decimal('0')

        target_gap = target_income - projected_income if target_income > projected_income else Decimal('0')

        history = []
        for offset in range(months):
            month_start = start_of_month - relativedelta(months=offset)
            month_end = month_start + relativedelta(months=1)

            month_realized = _to_decimal(
                positions.filter(
                    status='closed',
                    exit_date__gte=month_start,
                    exit_date__lt=month_end,
                ).aggregate(total=Sum('realized_pnl'))['total']
            )
            month_premium = _to_decimal(
                positions.filter(
                    entry_date__gte=month_start,
                    entry_date__lt=month_end,
                ).aggregate(total=Sum('premium_collected'))['total']
            )

            history.append({
                'period': month_start.strftime('%b %Y'),
                'realized_income': month_realized,
                'premium_collected': month_premium,
                'net_income': month_realized + month_premium,
            })

        history.reverse()

        base_capital = account.initial_capital or Decimal('0')
        income_per_dollar = Decimal('0')
        if base_capital > 0:
            income_per_dollar = projected_income / base_capital

        return {
            'target': target_income,
            'realized_income_mtd': realized_income_mtd,
            'expected_premium_mtd': premium_this_month,
            'projected_income': projected_income,
            'coverage_pct': coverage_pct,
            'coverage_pct_clamped': coverage_pct_clamped,
            'target_gap': target_gap,
            'history': history,
            'income_per_dollar': income_per_dollar,
            'base_capital': base_capital,
            'baseline_income': projected_income,
            'baseline_coverage_pct': coverage_pct,
        }

    def get_whales_timeline(self, account: ManagedTradingAccount, limit: int = 6) -> List[Dict]:
        """
        Return recent Unusual Whales datapoints for client timeline.
        """
        positions = account.positions.filter(
            api_response_data__has_key='unusual_whales'
        ).order_by('-entry_date')[:limit]

        timeline: List[Dict] = []
        for position in positions:
            whales_meta = position.api_response_data.get('unusual_whales') or {}
            if not whales_meta:
                continue
            timeline.append({
                'symbol': position.symbol,
                'status': position.get_status_display(),
                'entry_date': position.entry_date,
                'flow_score': whales_meta.get('flow_score'),
                'sentiment': whales_meta.get('sentiment'),
                'timing_signal': whales_meta.get('timing_signal'),
                'entry_window': whales_meta.get('entry_window'),
                'ai_score': getattr(position, 'ai_score', None),
            })
        return timeline

