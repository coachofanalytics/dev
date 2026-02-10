"""
Deal Configuration Service

Manages governance settings for deals including FX policy, weights, valuation rates,
approval requirements, and snapshot policies.
"""

from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
import logging

from investing.models_shareholders import (
    Deal, DealConfig, DealWeights, ValuationRate, LedgerAuditLog
)

logger = logging.getLogger(__name__)


class DealConfigService:
    """
    Service for managing deal configuration and governance settings.
    """
    
    def __init__(self, deal: Deal):
        """
        Initialize service for a specific deal.
        
        Args:
            deal: The Deal instance
        """
        self.deal = deal
    
    def get_or_create_config(self) -> DealConfig:
        """
        Get existing config or create default one.
        
        Returns:
            DealConfig instance
        """
        config, created = DealConfig.objects.get_or_create(
            deal=self.deal,
            defaults={
                'base_currency': 'USD',
                'fx_mode': 'PEGGED',
                'fx_peg_rate': Decimal('127.0000'),
                'time_rate': Decimal('50.00'),
                'work_rate': Decimal('100.00'),
                'inkind_valuation_mode': 'MANUAL',
                'dispute_window_days': 7,
                'require_approval_cash': True,
                'require_approval_inkind': True,
                'require_approval_time': False,
                'require_approval_work': False,
                'snapshot_frequency': 'MONTHLY',
                'snapshot_day': 1,
                'auto_lock_snapshots': True,
            }
        )
        
        if created:
            logger.info(f"Created default config for deal {self.deal.name}")
        
        return config
    
    def get_or_create_weights(self) -> DealWeights:
        """
        Get active weights or create default set.
        
        Returns:
            Active DealWeights instance
        """
        active_weights = DealWeights.objects.filter(
            deal=self.deal,
            is_active=True
        ).first()
        
        if active_weights:
            return active_weights
        
        # Create default weights
        weights = DealWeights.objects.create(
            deal=self.deal,
            cash_weight=Decimal('55.00'),
            in_kind_weight=Decimal('20.00'),
            time_weight=Decimal('10.00'),
            work_weight=Decimal('15.00'),
            is_active=True,
            effective_date=date.today()
        )
        
        logger.info(f"Created default weights for deal {self.deal.name}")
        return weights
    
    @transaction.atomic
    def update_config(
        self,
        config_data: dict,
        user=None,
        ip_address: str = None
    ) -> DealConfig:
        """
        Update deal configuration with validation.
        
        Args:
            config_data: Dictionary of config fields to update
            user: User performing the update
            ip_address: IP address for audit
            
        Returns:
            Updated DealConfig instance
            
        Raises:
            ValidationError: If validation fails
        """
        config = self.get_or_create_config()
        
        # Store old values for audit
        old_values = {}
        
        # Update FX & Currency fields
        if 'fx_mode' in config_data:
            old_values['fx_mode'] = config.fx_mode
            config.fx_mode = config_data['fx_mode']
        
        if 'fx_peg_rate' in config_data:
            old_values['fx_peg_rate'] = str(config.fx_peg_rate)
            config.fx_peg_rate = Decimal(str(config_data['fx_peg_rate']))
        
        # Update Valuation Rules
        if 'time_rate' in config_data:
            old_values['time_rate'] = str(config.time_rate)
            config.time_rate = Decimal(str(config_data['time_rate']))
        
        if 'work_rate' in config_data:
            old_values['work_rate'] = str(config.work_rate)
            config.work_rate = Decimal(str(config_data['work_rate']))
        
        if 'inkind_valuation_mode' in config_data:
            old_values['inkind_valuation_mode'] = config.inkind_valuation_mode
            config.inkind_valuation_mode = config_data['inkind_valuation_mode']
        
        # Update Approval & Dispute Policy
        if 'dispute_window_days' in config_data:
            old_values['dispute_window_days'] = config.dispute_window_days
            config.dispute_window_days = int(config_data['dispute_window_days'])
        
        if 'require_approval_cash' in config_data:
            config.require_approval_cash = bool(config_data['require_approval_cash'])
        
        if 'require_approval_inkind' in config_data:
            config.require_approval_inkind = bool(config_data['require_approval_inkind'])
        
        if 'require_approval_time' in config_data:
            config.require_approval_time = bool(config_data['require_approval_time'])
        
        if 'require_approval_work' in config_data:
            config.require_approval_work = bool(config_data['require_approval_work'])
        
        # Update Snapshot Policy
        if 'snapshot_frequency' in config_data:
            old_values['snapshot_frequency'] = config.snapshot_frequency
            config.snapshot_frequency = config_data['snapshot_frequency']
        
        if 'snapshot_day' in config_data:
            old_values['snapshot_day'] = config.snapshot_day
            config.snapshot_day = int(config_data['snapshot_day'])
        
        if 'auto_lock_snapshots' in config_data:
            config.auto_lock_snapshots = bool(config_data['auto_lock_snapshots'])
        
        # Validate and save
        config.full_clean()
        config.save()
        
        # Create audit log entry (reuse LedgerAuditLog or create specific ConfigAuditLog)
        # For now, log to standard logging
        logger.info(
            f"Updated config for deal {self.deal.name} by {user}. "
            f"Changed fields: {list(old_values.keys())}"
        )
        
        return config
    
    @transaction.atomic
    def update_weights(
        self,
        weights_data: dict,
        user=None,
        ip_address: str = None
    ) -> DealWeights:
        """
        Update deal contribution weights with validation.
        
        Args:
            weights_data: Dict with cash_weight, inkind_weight, time_weight, work_weight
            user: User performing the update
            ip_address: IP address for audit
            
        Returns:
            New active DealWeights instance
            
        Raises:
            ValidationError: If weights don't sum to 100%
        """
        # Validate weight sum
        cash = Decimal(str(weights_data.get('cash_weight', 0)))
        inkind = Decimal(str(weights_data.get('inkind_weight', 0)))
        time = Decimal(str(weights_data.get('time_weight', 0)))
        work = Decimal(str(weights_data.get('work_weight', 0)))
        
        total = cash + inkind + time + work
        
        if abs(total - Decimal('100.00')) > Decimal('0.01'):
            raise ValidationError(
                f"Weights must sum to 100%. Current sum: {total}%"
            )
        
        # Create new weight set (automatically deactivates old ones)
        weights = DealWeights.objects.create(
            deal=self.deal,
            cash_weight=cash,
            in_kind_weight=inkind,
            time_weight=time,
            work_weight=work,
            is_active=True,
            effective_date=date.today()
        )
        
        logger.info(
            f"Created new weights for deal {self.deal.name} by {user}. "
            f"Cash: {cash}%, InKind: {inkind}%, Time: {time}%, Work: {work}%"
        )
        
        return weights
    
    def requires_approval(self, tier: str) -> bool:
        """
        Check if a contribution tier requires approval.
        
        Args:
            tier: Tier name (CASH, IN_KIND, TIME, WORK)
            
        Returns:
            True if approval required
        """
        config = self.get_or_create_config()
        
        tier_map = {
            'CASH': config.require_approval_cash,
            'IN_KIND': config.require_approval_inkind,
            'TIME': config.require_approval_time,
            'WORK': config.require_approval_work,
        }
        
        return tier_map.get(tier, True)  # Default to requiring approval
    
    def get_valuation_rate(self, tier: str) -> Decimal:
        """
        Get the current valuation rate for a tier.
        
        Args:
            tier: Tier name (TIME or WORK)
            
        Returns:
            Rate per unit in USD
        """
        config = self.get_or_create_config()
        
        if tier == 'TIME':
            return config.time_rate
        elif tier == 'WORK':
            return config.work_rate
        else:
            return Decimal('0.00')
    
    def calculate_next_snapshot_date(self) -> date:
        """
        Calculate the next scheduled snapshot date based on frequency.
        
        Returns:
            Next snapshot date
        """
        config = self.get_or_create_config()
        today = date.today()
        
        if config.snapshot_frequency == 'MONTHLY':
            # Next month on snapshot_day
            if today.day < config.snapshot_day:
                # This month
                next_date = date(today.year, today.month, config.snapshot_day)
            else:
                # Next month
                if today.month == 12:
                    next_date = date(today.year + 1, 1, config.snapshot_day)
                else:
                    next_date = date(today.year, today.month + 1, config.snapshot_day)
        
        elif config.snapshot_frequency == 'QUARTERLY':
            # Next quarter on snapshot_day
            current_month = today.month
            next_quarter_month = ((current_month - 1) // 3 + 1) * 3 + 1
            
            if next_quarter_month > 12:
                next_date = date(today.year + 1, 1, config.snapshot_day)
            else:
                next_date = date(today.year, next_quarter_month, config.snapshot_day)
        
        else:  # MANUAL
            next_date = None
        
        return next_date
