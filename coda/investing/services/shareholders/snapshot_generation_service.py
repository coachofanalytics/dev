"""
Snapshot Generation Service

Generates equity snapshots from approved ledger entries with proper tier weighting
and member equity calculations.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from django.db.models import Sum
from django.utils import timezone
import hashlib
import json
import logging

from investing.models import (
    Deal, DealWeights, Member, LedgerEntry,
    EquitySnapshot, EquitySnapshotLine
)

logger = logging.getLogger(__name__)


class SnapshotGenerationService:
    """
    Service for generating immutable equity snapshots from current ledger state.
    """
    
    def __init__(self, deal: Deal):
        """
        Initialize service for a specific deal.
        
        Args:
            deal: The Deal instance to generate snapshot for
        """
        self.deal = deal
        self.weights = deal.weights.filter(is_active=True).first()
    
    def generate_snapshot(
        self,
        version_id: str,
        period_start: date,
        period_end: date,
        created_by=None,
        dispute_window_days: int = 7,
        notes: str = None
    ) -> EquitySnapshot:
        """
        Generate a complete equity snapshot for the deal.
        
        Args:
            version_id: Unique version identifier (e.g., 'v1.2-q3')
            period_start: Start date of snapshot period
            period_end: End date of snapshot period
            created_by: User creating the snapshot
            dispute_window_days: Days before auto-lock
            notes: Optional notes
            
        Returns:
            Created EquitySnapshot instance with all lines
        """
        # Get active members
        members = Member.objects.filter(
            deal=self.deal,
            is_archived=False
        ).order_by('legal_name')
        
        # Calculate member contributions and equity
        member_data = []
        total_weighted = Decimal('0.00')
        
        for member in members:
            contributions = self._get_member_contributions(member, period_end)
            weighted_total = self._calculate_weighted_contribution(contributions)
            
            member_data.append({
                'member': member,
                'contributions': contributions,
                'weighted_total': weighted_total,
            })
            
            total_weighted += weighted_total
        
        # Calculate equity percentages
        for item in member_data:
            if total_weighted > 0:
                item['equity_percentage'] = (
                    (item['weighted_total'] / total_weighted) * Decimal('100.00')
                ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                item['equity_percentage'] = Decimal('0.00')
        
        # Create snapshot
        snapshot = EquitySnapshot.objects.create(
            deal=self.deal,
            version_id=version_id,
            period_start=period_start,
            period_end=period_end,
            snapshot_date=date.today(),
            status='DRAFT',
            is_locked=False,
            dispute_window_days=dispute_window_days,
            members_count=len(member_data),
            created_by=created_by,
            notes=notes,
        )
        
        # Create snapshot lines
        total_cash = Decimal('0.00')
        total_inkind = Decimal('0.00')
        total_time = Decimal('0.00')
        total_work = Decimal('0.00')
        
        for item in member_data:
            member = item['member']
            contributions = item['contributions']
            
            EquitySnapshotLine.objects.create(
                snapshot=snapshot,
                member=member,
                cash_usd=contributions['CASH'],
                inkind_usd=contributions['IN_KIND'],
                time_usd=contributions['TIME'],
                work_usd=contributions['WORK'],
                weighted_total_usd=item['weighted_total'],
                equity_percentage=item['equity_percentage'],
                member_name=member.legal_name,
                member_type=member.member_type,
                member_role=member.role_title or '',
            )
            
            total_cash += contributions['CASH']
            total_inkind += contributions['IN_KIND']
            total_time += contributions['TIME']
            total_work += contributions['WORK']
        
        # Update snapshot totals
        snapshot.total_cash_usd = total_cash
        snapshot.total_inkind_usd = total_inkind
        snapshot.total_time_usd = total_time
        snapshot.total_work_usd = total_work
        snapshot.total_valuation_usd = total_weighted
        
        # Generate checksum
        snapshot.checksum = self._generate_checksum(snapshot)
        snapshot.save()
        
        logger.info(f"Generated snapshot {version_id} with {len(member_data)} members")
        
        return snapshot
    
    def _get_member_contributions(self, member: Member, as_of_date: date) -> dict:
        """
        Get member's approved contributions by tier up to a specific date.
        
        Args:
            member: Member instance
            as_of_date: Cut-off date for contributions
            
        Returns:
            Dict with CASH, IN_KIND, TIME, WORK values in USD
        """
        # Query approved entries up to date
        approved_entries = LedgerEntry.objects.filter(
            deal=self.deal,
            contributor=member,
            status='APPROVED',
            date__lte=as_of_date
        )
        
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
    
    def _calculate_weighted_contribution(self, contributions: dict) -> Decimal:
        """
        Apply tier weights to raw contribution values.
        
        Args:
            contributions: Dict with CASH, IN_KIND, TIME, WORK values
            
        Returns:
            Weighted total
        """
        if not self.weights:
            # Use default weights if not configured
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
        
        weighted_total = Decimal('0.00')
        for tier, value in contributions.items():
            weight_pct = weights.get(tier, Decimal('0.00'))
            weighted_value = value * (weight_pct / Decimal('100.00'))
            weighted_total += weighted_value
        
        return weighted_total
    
    def _generate_checksum(self, snapshot: EquitySnapshot) -> str:
        """
        Generate deterministic SHA-256 checksum for snapshot data.
        
        Args:
            snapshot: EquitySnapshot instance with lines loaded
            
        Returns:
            Hexadecimal checksum string
        """
        # Get all snapshot lines sorted deterministically
        lines = snapshot.lines.all().order_by('member__id', 'member_name')
        
        # Build checksum data
        checksum_data = {
            'version_id': snapshot.version_id,
            'snapshot_date': snapshot.snapshot_date.isoformat(),
            'members_count': snapshot.members_count,
            'total_valuation_usd': str(snapshot.total_valuation_usd),
            'lines': [
                {
                    'member_id': line.member.id,
                    'member_name': line.member_name,
                    'cash_usd': str(line.cash_usd),
                    'inkind_usd': str(line.inkind_usd),
                    'time_usd': str(line.time_usd),
                    'work_usd': str(line.work_usd),
                    'equity_percentage': str(line.equity_percentage),
                }
                for line in lines
            ]
        }
        
        # Generate SHA-256 hash
        data_string = json.dumps(checksum_data, sort_keys=True)
        checksum = hashlib.sha256(data_string.encode('utf-8')).hexdigest()
        
        # Return abbreviated format matching UI (0x...XX)
        return f"0x{checksum[:2]}...{checksum[-2:]}"
    
    def auto_lock_expired_snapshots(self):
        """
        Auto-lock snapshots that have passed their dispute window.
        
        Returns:
            List of locked snapshot IDs
        """
        today = date.today()
        
        # Find unlocked snapshots past auto-lock date
        expired_snapshots = EquitySnapshot.objects.filter(
            deal=self.deal,
            is_locked=False,
            auto_lock_date__lte=today
        )
        
        locked_ids = []
        for snapshot in expired_snapshots:
            snapshot.is_locked = True
            snapshot.status = 'FINALIZED'
            snapshot.locked_at = timezone.now()
            snapshot.save()
            locked_ids.append(snapshot.id)
            
            logger.info(f"Auto-locked snapshot {snapshot.version_id}")
        
        return locked_ids
