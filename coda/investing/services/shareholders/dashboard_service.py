"""
Shareholders Management System - Business Logic Services

This module provides read-only calculation services for the Shareholders app.
No persistence operations - all calculations are performed on-demand from database state.

Phase Scope:
- Dashboard equity estimation (read-only)
- Weighted contribution aggregation
- Safe division-by-zero handling

Migrated to investing app - models imported from shareholders app.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional
from django.db.models import Sum, Q
import logging

# Models imported from original shareholders app (preserves DB ownership)
from investing.models import Deal, Member, LedgerEntry, DealWeights

logger = logging.getLogger(__name__)


class EquityEstimationService:
    """
    Read-only service for estimating member equity percentages based on
    approved contributions and configured tier weights.
    
    This is a LIVE ESTIMATION only - no persistence, no snapshots yet.
    """
    
    def __init__(self, deal: Deal):
        """
        Initialize service for a specific deal.
        
        Args:
            deal: The Deal instance to calculate equity for
        """
        self.deal = deal
        self.weights = deal.weights.filter(is_active=True).first()
        
        # Validate weights if they exist
        if self.weights:
            self._validate_weights()
    
    def _validate_weights(self) -> bool:
        """
        Validate that weights sum to 100%.
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not self.weights:
            logger.warning(f"No active weights configured for deal {self.deal.slug}")
            return False
        
        total = (
            self.weights.cash_weight +
            self.weights.in_kind_weight +
            self.weights.time_weight +
            self.weights.work_weight
        )
        
        is_valid = abs(total - Decimal('100.00')) < Decimal('0.01')
        
        if not is_valid:
            logger.warning(
                f"Weights for deal {self.deal.slug} do not sum to 100%. "
                f"Total: {total}%"
            )
        
        return is_valid
    
    def get_member_contributions(self, member: Member) -> Dict[str, Decimal]:
        """
        Aggregate approved contributions by tier for a single member.
        
        Args:
            member: The Member to aggregate for
            
        Returns:
            Dict with tier keys (CASH, IN_KIND, TIME, WORK) and USD values
        """
        # Query all approved entries for this member
        approved_entries = LedgerEntry.objects.filter(
            deal=self.deal,
            contributor=member,
            status='APPROVED'
        )
        
        # Aggregate by tier
        cash_total = approved_entries.filter(
            tier='CASH'
        ).aggregate(total=Sum('value_usd'))['total'] or Decimal('0.00')
        
        inkind_total = approved_entries.filter(
            tier='IN_KIND'
        ).aggregate(total=Sum('value_usd'))['total'] or Decimal('0.00')
        
        time_total = approved_entries.filter(
            tier='TIME'
        ).aggregate(total=Sum('value_usd'))['total'] or Decimal('0.00')
        
        work_total = approved_entries.filter(
            tier='WORK'
        ).aggregate(total=Sum('value_usd'))['total'] or Decimal('0.00')
        
        return {
            'CASH': cash_total,
            'IN_KIND': inkind_total,
            'TIME': time_total,
            'WORK': work_total,
        }
    
    def calculate_weighted_contribution(self, contributions: Dict[str, Decimal]) -> Decimal:
        """
        Apply tier weights to raw contribution values.
        
        Args:
            contributions: Dict with CASH, IN_KIND, TIME, WORK values
            
        Returns:
            Weighted total (sum of tier_value * tier_weight)
        """
        if not self.weights:
            # Fallback: use default weights if not configured
            weights = {
                'CASH': Decimal('55.00'),
                'IN_KIND': Decimal('20.00'),
                'TIME': Decimal('10.00'),
                'WORK': Decimal('15.00'),
            }
        else:
            weights = {
                'CASH': self.weights.cash_weight,
                'IN_KIND': self.weights.in_kind_weight,
                'TIME': self.weights.time_weight,
                'WORK': self.weights.work_weight,
            }
        
        # Calculate weighted sum
        weighted_total = Decimal('0.00')
        for tier, value in contributions.items():
            weight_pct = weights.get(tier, Decimal('0.00'))
            # Apply weight as percentage (divide by 100)
            weighted_value = value * (weight_pct / Decimal('100.00'))
            weighted_total += weighted_value
        
        return weighted_total
    
    def estimate_equity_percentage(
        self,
        member_weighted_total: Decimal,
        pool_weighted_total: Decimal
    ) -> Decimal:
        """
        Calculate equity percentage with safe division.
        
        Args:
            member_weighted_total: Member's weighted contribution
            pool_weighted_total: Total weighted pool across all members
            
        Returns:
            Equity percentage (0-100), or 0.00 if pool is zero
        """
        if pool_weighted_total <= Decimal('0.00'):
            return Decimal('0.00')
        
        # Calculate percentage
        percentage = (member_weighted_total / pool_weighted_total) * Decimal('100.00')
        
        # Round to 2 decimal places
        return percentage.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_equity_for_all_members(self) -> List[Dict]:
        """
        Calculate estimated equity for all active members in the deal.
        
        Returns:
            List of dicts with member data and equity estimates:
            [
                {
                    'member': Member instance,
                    'contributions': {CASH: x, IN_KIND: y, ...},
                    'weighted_total': Decimal,
                    'equity_percentage': Decimal,
                },
                ...
            ]
        """
        members = Member.objects.filter(
            deal=self.deal,
            is_archived=False
        ).order_by('legal_name')
        
        results = []
        
        # First pass: calculate weighted totals for each member
        for member in members:
            contributions = self.get_member_contributions(member)
            weighted_total = self.calculate_weighted_contribution(contributions)
            
            results.append({
                'member': member,
                'contributions': contributions,
                'weighted_total': weighted_total,
                'equity_percentage': Decimal('0.00'),  # Will calculate after pool total
            })
        
        # Calculate total weighted pool
        pool_total = sum(r['weighted_total'] for r in results)
        
        # Second pass: calculate equity percentages
        for result in results:
            result['equity_percentage'] = self.estimate_equity_percentage(
                result['weighted_total'],
                pool_total
            )
        
        # Sort by equity percentage (descending)
        results.sort(key=lambda x: x['equity_percentage'], reverse=True)
        
        return results
    
    def get_dashboard_cap_table(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get formatted cap table data for dashboard display.
        
        Args:
            limit: Optional limit on number of members to return
            
        Returns:
            List of dicts formatted for template rendering
        """
        equity_data = self.calculate_equity_for_all_members()
        
        if limit:
            equity_data = equity_data[:limit]
        
        cap_table = []
        for item in equity_data:
            member = item['member']
            contributions = item['contributions']
            
            cap_table.append({
                'id': member.id,
                'name': member.legal_name,
                'role': member.role_title or '',
                'type': member.member_type,
                'cash_invested': contributions['CASH'],
                'equity_percentage': item['equity_percentage'],
            })
        
        return cap_table
    
    def get_weights_validation_status(self) -> Dict:
        """
        Get current weights and validation status.
        
        Returns:
            Dict with weights and validation info
        """
        if not self.weights:
            return {
                'configured': False,
                'valid': False,
                'warning': 'No weights configured for this deal',
                'weights': None,
            }
        
        total = (
            self.weights.cash_weight +
            self.weights.in_kind_weight +
            self.weights.time_weight +
            self.weights.work_weight
        )
        
        is_valid = abs(total - Decimal('100.00')) < Decimal('0.01')
        
        return {
            'configured': True,
            'valid': is_valid,
            'warning': None if is_valid else f'Weights sum to {total}%, not 100%',
            'weights': {
                'cash': self.weights.cash_weight,
                'in_kind': self.weights.in_kind_weight,
                'time': self.weights.time_weight,
                'work': self.weights.work_weight,
                'total': total,
            },
        }


def get_dashboard_metrics(deal: Deal) -> Dict:
    """
    Aggregate all dashboard metrics for a deal.
    
    This is the main service function called by the dashboard view.
    
    Args:
        deal: The Deal to get metrics for
        
    Returns:
        Dict with all dashboard data ready for template context
    """
    # Initialize equity service
    equity_service = EquityEstimationService(deal)
    
    # Get deal config
    config = getattr(deal, 'config', None)
    
    # Stats Card: Active Members
    active_members_count = Member.objects.filter(
        deal=deal,
        is_archived=False
    ).count()
    
    # Stats Card: Total Amount Invested (ALL tiers, APPROVED only)
    total_cash_approved = LedgerEntry.objects.filter(
        deal=deal,
        status='APPROVED'
    ).aggregate(total=Sum('value_usd'))['total'] or Decimal('0.00')
    
    # Stats Card: Pending Approvals (SUBMITTED status)
    pending_approvals_count = LedgerEntry.objects.filter(
        deal=deal,
        status='SUBMITTED'
    ).count()
    
    # Stats Card: Next Snapshot (always calculate dynamically — stored date can go stale)
    from investing.services.shareholders.deal_config_service import DealConfigService
    from django.utils import timezone
    config_service = DealConfigService(deal)
    next_snapshot_date = config_service.calculate_next_snapshot_date()
    # Fallback: use stored date if config is MANUAL / frequency not set
    if next_snapshot_date is None:
        next_snapshot_date = config.next_snapshot_date if config else None
    if next_snapshot_date:
        days_until = (next_snapshot_date - timezone.now().date()).days
        snapshot_display = f"{days_until}d" if days_until > 0 else "Today"
        snapshot_date_formatted = next_snapshot_date.strftime('%b %d, %Y')
    else:
        snapshot_display = "—"
        snapshot_date_formatted = "Not scheduled"
    
    # FX Rate (live, via CurrencyConverter — 1-hour cached)
    from investing.services.shareholders.deal_config_service import DealConfigService
    fx_peg_rate = DealConfigService.get_live_fx_rate(config)
    
    # Equity Cap Table (top 4 for dashboard)
    cap_table = equity_service.get_dashboard_cap_table(limit=4)
    
    # Weights validation
    weights_status = equity_service.get_weights_validation_status()
    
    return {
        # Stats cards
        'active_members': active_members_count,
        'total_cash_invested': total_cash_approved,
        'pending_approvals': pending_approvals_count,
        'snapshot_display': snapshot_display,
        'snapshot_date': snapshot_date_formatted,
        'fx_peg_rate': fx_peg_rate,
        
        # Cap table
        'members_data': cap_table,
        
        # Weights
        'weights_status': weights_status,
        'cash_weight': weights_status['weights']['cash'] if weights_status['configured'] else Decimal('55.00'),
        'inkind_weight': weights_status['weights']['in_kind'] if weights_status['configured'] else Decimal('20.00'),
        'time_weight': weights_status['weights']['time'] if weights_status['configured'] else Decimal('10.00'),
        'work_weight': weights_status['weights']['work'] if weights_status['configured'] else Decimal('15.00'),
    }
