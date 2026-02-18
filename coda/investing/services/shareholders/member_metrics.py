"""
Member Metrics Service

Provides aggregation helpers for computing member contribution metrics.
All aggregations are read-only and computed from LedgerEntry records.

POLICY: By default, only APPROVED entries are counted in totals.
This can be adjusted via the include_submitted parameter.

Migrated to investing app - models imported from shareholders app.
"""

from decimal import Decimal
from typing import Dict, List, Optional
from django.db.models import Sum, Q, Count
import logging

# Models imported from original shareholders app (preserves DB ownership)
from investing.models_shareholders import Member, LedgerEntry, Deal

logger = logging.getLogger(__name__)


class MemberMetricsService:
    """Service for calculating member contribution metrics."""
    
    # Policy: What statuses count toward member totals
    DEFAULT_INCLUDED_STATUSES = ['APPROVED']  # Conservative: approved only
    PERMISSIVE_STATUSES = ['APPROVED', 'SUBMITTED']  # Include pending review
    
    def __init__(self, member: Member, include_submitted: bool = False):
        """
        Initialize service for a specific member.
        
        Args:
            member: The Member instance to calculate metrics for
            include_submitted: If True, include SUBMITTED status in totals (default: False)
        """
        self.member = member
        self.statuses = self.PERMISSIVE_STATUSES if include_submitted else self.DEFAULT_INCLUDED_STATUSES
    
    def get_cash_invested(self) -> Decimal:
        """Get total cash contributed (USD)."""
        total = LedgerEntry.objects.filter(
            contributor=self.member,
            tier='CASH',
            status__in=self.statuses
        ).aggregate(total=Sum('value_usd'))['total']
        return total or Decimal('0.00')
    
    def get_in_kind_value(self) -> Decimal:
        """Get total in-kind contribution value (USD)."""
        total = LedgerEntry.objects.filter(
            contributor=self.member,
            tier='IN_KIND',
            status__in=self.statuses
        ).aggregate(total=Sum('value_usd'))['total']
        return total or Decimal('0.00')
    
    def get_time_logged(self) -> Decimal:
        """Get total time logged (in hours or configured units)."""
        total = LedgerEntry.objects.filter(
            contributor=self.member,
            tier='TIME',
            status__in=self.statuses
        ).aggregate(total=Sum('internal_units_value'))['total']
        return total or Decimal('0.00')
    
    def get_work_units(self) -> Decimal:
        """Get total work units (points/deliverables)."""
        total = LedgerEntry.objects.filter(
            contributor=self.member,
            tier='WORK',
            status__in=self.statuses
        ).aggregate(total=Sum('internal_units_value'))['total']
        return total or Decimal('0.00')
    
    def get_all_metrics(self) -> Dict[str, Decimal]:
        """Get all contribution metrics in one call."""
        return {
            'cash_invested': self.get_cash_invested(),
            'in_kind_value': self.get_in_kind_value(),
            'time_logged': self.get_time_logged(),
            'work_units': self.get_work_units(),
        }
    
    def get_contribution_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get contribution history for this member.
        
        Args:
            limit: Maximum number of entries to return (default: all)
            
        Returns:
            List of contribution dicts with tier, date, status, value, tx_id
        """
        queryset = LedgerEntry.objects.filter(
            contributor=self.member
        ).order_by('-date', '-created_at')
        
        if limit:
            queryset = queryset[:limit]
        
        history = []
        for entry in queryset:
            history.append({
                'tx_id': entry.tx_id,
                'tier': entry.get_tier_display(),
                'tier_code': entry.tier,
                'asset_class': entry.asset_class,
                'internal_units': f"{entry.internal_units_value:,.0f} {entry.internal_units_label or ''}".strip(),
                'value_usd': float(entry.value_usd),
                'status': entry.get_status_display(),
                'status_code': entry.status,
                'date': entry.date.strftime('%Y-%m-%d'),
                'date_formatted': entry.date.strftime('%b %d, %Y'),
                'has_proof': entry.has_proof,
            })
        
        return history
    
    def get_contribution_count(self) -> int:
        """Get total number of contributions (all statuses)."""
        return LedgerEntry.objects.filter(contributor=self.member).count()
    
    def get_pending_count(self) -> int:
        """Get number of contributions pending approval."""
        return LedgerEntry.objects.filter(
            contributor=self.member,
            status='SUBMITTED'
        ).count()


def get_deal_member_summary(deal: Deal, include_submitted: bool = False) -> List[Dict]:
    """
    Get summary of all members in a deal with their aggregated metrics.
    
    Args:
        deal: The Deal instance
        include_submitted: If True, include SUBMITTED status in totals
        
    Returns:
        List of member summary dicts
    """
    from investing.services.shareholders.dashboard_service import EquityEstimationService
    
    members = Member.objects.filter(
        deal=deal,
        is_archived=False
    ).order_by('legal_name')
    
    # Calculate equity for all members using EquityEstimationService
    equity_service = EquityEstimationService(deal)
    equity_data = equity_service.calculate_equity_for_all_members()
    
    # Build equity lookup by member ID
    equity_by_member = {item['member'].id: item['equity_percentage'] for item in equity_data}
    
    summaries = []
    for member in members:
        service = MemberMetricsService(member, include_submitted=include_submitted)
        metrics = service.get_all_metrics()
        
        summaries.append({
            'id': member.id,
            'name': member.legal_name,
            'role': member.role_title or '',
            'type': member.get_member_type_display(),
            'type_code': member.member_type,
            'verified': member.verified,
            'email': member.email,
            'phone': member.phone or '',
            'joined_date': member.joined_date.strftime('%Y-%m-%d'),
            'cash_invested': float(metrics['cash_invested']),
            'in_kind_value': float(metrics['in_kind_value']),
            'time_logged': float(metrics['time_logged']),
            'work_units': float(metrics['work_units']),
            'contribution_count': service.get_contribution_count(),
            'pending_count': service.get_pending_count(),
            # Equity calculated from approved contributions with tier weights
            'equity_percentage': float(equity_by_member.get(member.id, Decimal('0.00'))),
            'profile_photo': member.profile_photo.url if member.profile_photo else None,
        })
    
    return summaries
