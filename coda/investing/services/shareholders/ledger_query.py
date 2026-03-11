"""
Ledger Query Service

Provides server-side filtering, search, sorting, and pagination for ledger entries.
All queries are scoped to a specific deal for data isolation.

Migrated to investing app - models imported from shareholders app.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import date, timedelta
from django.db.models import Q, Sum, Count, QuerySet
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
import logging

# Models imported from original shareholders app (preserves DB ownership)
from investing.models_shareholders import Deal, LedgerEntry, Member

logger = logging.getLogger(__name__)


class LedgerQueryService:
    """
    Service for querying and filtering ledger entries with server-side operations.
    
    All methods are read-only and do not persist any changes.
    """
    
    # Tier mapping for display consistency
    TIER_DISPLAY = {
        'CASH': 'Cash Contribution',
        'IN_KIND': 'In-Kind Asset',
        'TIME': 'Time Logged',
        'WORK': 'Work Deliverable',
    }
    
    # Status mapping for display
    STATUS_DISPLAY = {
        'DRAFT': 'Draft',
        'SUBMITTED': 'Submitted for Review',
        'APPROVED': 'Approved',
        'REJECTED': 'Rejected',
        'IN_DISPUTE': 'In Dispute',
    }
    
    def __init__(self, deal: Deal):
        """
        Initialize service for a specific deal.
        
        Args:
            deal: The Deal instance to query ledger entries for
        """
        self.deal = deal
    
    def get_base_queryset(self) -> QuerySet:
        """
        Get base queryset scoped to current deal with common joins.
        
        Returns:
            QuerySet with select_related for efficient querying
        """
        return LedgerEntry.objects.filter(
            deal=self.deal
        ).select_related('contributor')
    
    def apply_filters(
        self,
        queryset: QuerySet,
        status: Optional[str] = None,
        tier: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        contributor_id: Optional[int] = None,
    ) -> QuerySet:
        """
        Apply filters to ledger queryset.
        
        Args:
            queryset: Base queryset to filter
            status: Status filter (APPROVED, SUBMITTED, IN_DISPUTE, etc.)
            tier: Tier filter (CASH, IN_KIND, TIME, WORK)
            date_from: Start date for date range filter
            date_to: End date for date range filter
            contributor_id: Filter by specific contributor
            
        Returns:
            Filtered QuerySet
        """
        if status and status != 'all':
            # Map display status to DB status
            status_map = {
                'Approved': 'APPROVED',
                'Pending': 'SUBMITTED',
                'In Dispute': 'IN_DISPUTE',
                'Rejected': 'REJECTED',
            }
            db_status = status_map.get(status, status.upper())
            queryset = queryset.filter(status=db_status)
        
        if tier and tier != 'all':
            # Map display tier to DB tier
            tier_map = {
                'Cash': 'CASH',
                'In-Kind': 'IN_KIND',
                'Time': 'TIME',
                'Work': 'WORK',
            }
            db_tier = tier_map.get(tier, tier.upper().replace('-', '_'))
            queryset = queryset.filter(tier=db_tier)
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        if contributor_id:
            queryset = queryset.filter(contributor_id=contributor_id)
        
        return queryset
    
    def apply_date_range_preset(
        self,
        queryset: QuerySet,
        preset: str,
    ) -> QuerySet:
        """
        Apply preset date range filter.
        
        Args:
            queryset: Base queryset to filter
            preset: One of 'last_30_days', 'last_quarter', 'year_to_date', 'all_time'
            
        Returns:
            Filtered QuerySet
        """
        today = timezone.now().date()
        
        if preset == 'last_30_days':
            date_from = today - timedelta(days=30)
            queryset = queryset.filter(date__gte=date_from)
        elif preset == 'last_quarter':
            # Calculate start of current quarter
            quarter_month = ((today.month - 1) // 3) * 3 + 1
            date_from = date(today.year, quarter_month, 1)
            queryset = queryset.filter(date__gte=date_from)
        elif preset == 'year_to_date':
            date_from = date(today.year, 1, 1)
            queryset = queryset.filter(date__gte=date_from)
        # 'all_time' requires no filtering
        
        return queryset
    
    def apply_search(
        self,
        queryset: QuerySet,
        search_term: str,
    ) -> QuerySet:
        """
        Apply search filter across multiple fields.
        
        Args:
            queryset: Base queryset to filter
            search_term: Search term to match against TX ID, contributor name, asset class
            
        Returns:
            Filtered QuerySet
        """
        if not search_term or not search_term.strip():
            return queryset
        
        search_term = search_term.strip()
        
        return queryset.filter(
            Q(tx_id__icontains=search_term) |
            Q(contributor__legal_name__icontains=search_term) |
            Q(asset_class__icontains=search_term) |
            Q(notes__icontains=search_term)
        )
    
    def apply_sorting(
        self,
        queryset: QuerySet,
        sort_by: str = 'date',
        sort_order: str = 'desc',
    ) -> QuerySet:
        """
        Apply sorting to queryset.
        
        Args:
            queryset: Base queryset to sort
            sort_by: Field to sort by (date, value, contributor, tier, status)
            sort_order: 'asc' or 'desc'
            
        Returns:
            Sorted QuerySet
        """
        sort_mapping = {
            'date': 'date',
            'value': 'value_usd',
            'contributor': 'contributor__legal_name',
            'tier': 'tier',
            'status': 'status',
            'tx_id': 'tx_id',
        }
        
        order_field = sort_mapping.get(sort_by, 'date')
        
        if sort_order == 'asc':
            return queryset.order_by(order_field, 'created_at')
        else:
            return queryset.order_by(f'-{order_field}', '-created_at')
    
    def paginate(
        self,
        queryset: QuerySet,
        page: int = 1,
        per_page: int = 25,
    ) -> Dict[str, Any]:
        """
        Paginate queryset.
        
        Args:
            queryset: QuerySet to paginate
            page: Page number (1-indexed)
            per_page: Items per page
            
        Returns:
            Dict with 'entries', 'page', 'total_pages', 'total_count', etc.
        """
        paginator = Paginator(queryset, per_page)
        
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        return {
            'entries': list(page_obj),
            'page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'per_page': per_page,
        }
    
    def get_filtered_entries(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        tier: Optional[str] = None,
        date_range: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        contributor_id: Optional[int] = None,
        sort_by: str = 'date',
        sort_order: str = 'desc',
        page: int = 1,
        per_page: int = 25,
    ) -> Dict[str, Any]:
        """
        Main query method combining all filtering, searching, sorting, and pagination.
        
        Args:
            search: Search term
            status: Status filter
            tier: Tier filter
            date_range: Date range preset (overrides date_from/date_to)
            date_from: Custom start date
            date_to: Custom end date
            contributor_id: Contributor filter
            sort_by: Sort field
            sort_order: Sort direction
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict with paginated entries and metadata
        """
        queryset = self.get_base_queryset()
        
        # Apply filters
        queryset = self.apply_filters(
            queryset,
            status=status,
            tier=tier,
            date_from=date_from,
            date_to=date_to,
            contributor_id=contributor_id,
        )
        
        # Apply date range preset if provided
        if date_range and date_range != 'all_time':
            queryset = self.apply_date_range_preset(queryset, date_range)
        
        # Apply search
        if search:
            queryset = self.apply_search(queryset, search)
        
        # Apply sorting
        queryset = self.apply_sorting(queryset, sort_by, sort_order)
        
        # Paginate
        result = self.paginate(queryset, page, per_page)
        
        # Format entries for template
        result['entries'] = self.format_entries_for_display(result['entries'])
        
        return result
    
    def format_entries_for_display(
        self,
        entries: List[LedgerEntry],
    ) -> List[Dict[str, Any]]:
        """
        Format ledger entries for template display.
        
        Args:
            entries: List of LedgerEntry instances
            
        Returns:
            List of dicts ready for template rendering
        """
        formatted = []
        
        for entry in entries:
            # Format internal units with label
            if entry.internal_units_label:
                internal_units = f"{entry.internal_units_value:,.0f} {entry.internal_units_label}"
            else:
                internal_units = f"{entry.internal_units_value:,.0f}"
            
            formatted.append({
                'id': entry.tx_id,
                'pk': entry.pk,
                'contributor_name': entry.contributor.legal_name,
                'contributor_id': entry.contributor.id,
                'tier': entry.get_tier_display(),
                'tier_code': entry.tier,
                'asset_class': entry.asset_class,
                'internal_units': internal_units,
                'internal_units_value': float(entry.internal_units_value),
                'internal_units_label': entry.internal_units_label or '',
                'value_usd': float(entry.value_usd),
                'status': entry.get_status_display(),
                'status_code': entry.status,
                'date': entry.date.strftime('%Y-%m-%d'),
                'date_formatted': entry.date.strftime('%b %d, %Y'),
                'notes': entry.notes or '',
                'has_proof': entry.has_proof,
                'currency': entry.currency,
                'exchange_rate': float(entry.exchange_rate),
                'tier_metadata': entry.tier_metadata or {},
            })
        
        return formatted
    
    def get_summary_stats(
        self,
        queryset: Optional[QuerySet] = None,
    ) -> Dict[str, Any]:
        """
        Calculate summary statistics for the current filtered view.
        
        Args:
            queryset: Optional pre-filtered queryset (uses base if None)
            
        Returns:
            Dict with total_volume_usd, approved_count, in_dispute_count
        """
        if queryset is None:
            queryset = self.get_base_queryset()
        
        # Total volume (APPROVED entries only — matches dashboard metric)
        total_volume = queryset.filter(
            status='APPROVED'
        ).aggregate(
            total=Sum('value_usd')
        )['total'] or Decimal('0.00')
        
        # Status counts
        approved_count = queryset.filter(status='APPROVED').count()
        in_dispute_count = queryset.filter(status='IN_DISPUTE').count()
        submitted_count = queryset.filter(status='SUBMITTED').count()
        
        return {
            'total_volume_usd': float(total_volume),
            'approved_count': approved_count,
            'in_dispute_count': in_dispute_count,
            'submitted_count': submitted_count,
            'pending_count': submitted_count,  # Alias
        }
    
    def get_entry_by_tx_id(self, tx_id: str) -> Optional[LedgerEntry]:
        """
        Get a single ledger entry by its transaction ID.
        
        Args:
            tx_id: Transaction ID (e.g., 'TX-1234')
            
        Returns:
            LedgerEntry or None if not found
        """
        try:
            return self.get_base_queryset().get(tx_id=tx_id)
        except LedgerEntry.DoesNotExist:
            return None
    
    def get_entry_detail(self, tx_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive detail for a single ledger entry.
        
        Args:
            tx_id: Transaction ID
            
        Returns:
            Dict with full entry details or None
        """
        entry = self.get_entry_by_tx_id(tx_id)
        if not entry:
            return None
        
        # Get evidence/attachments
        evidence = []
        for ev in entry.evidence.all():
            evidence.append({
                'id': ev.id,
                'file_url': ev.file.url if ev.file else None,
                'description': ev.description or '',
                'uploaded_at': ev.uploaded_at.strftime('%Y-%m-%d %H:%M'),
                'uploaded_by': ev.uploaded_by.get_full_name() if ev.uploaded_by else 'System',
            })
        
        # Get approval history
        approvals = []
        for approval in entry.approvals.all().order_by('-created_at'):
            approvals.append({
                'action': approval.get_action_display(),
                'approved_by': approval.approved_by.get_full_name() if approval.approved_by else 'System',
                'notes': approval.notes or '',
                'created_at': approval.created_at.strftime('%Y-%m-%d %H:%M'),
            })
        
        # Get dispute history
        disputes = []
        for dispute in entry.disputes.all().order_by('-created_at'):
            disputes.append({
                'status': dispute.get_status_display(),
                'reason': dispute.reason,
                'raised_by': dispute.raised_by.get_full_name() if dispute.raised_by else 'System',
                'created_at': dispute.created_at.strftime('%Y-%m-%d %H:%M'),
                'resolved_at': dispute.resolved_at.strftime('%Y-%m-%d %H:%M') if dispute.resolved_at else None,
                'resolution_notes': dispute.resolution_notes or '',
            })
        
        return {
            'id': entry.tx_id,
            'pk': entry.pk,
            'contributor_name': entry.contributor.legal_name,
            'contributor_id': entry.contributor.id,
            'contributor_email': entry.contributor.email,
            'contributor_type': entry.contributor.get_member_type_display(),
            'tier': entry.get_tier_display(),
            'tier_code': entry.tier,
            'asset_class': entry.asset_class,
            'internal_units_value': float(entry.internal_units_value),
            'internal_units_label': entry.internal_units_label or '',
            'value_usd': float(entry.value_usd),
            'currency': entry.currency,
            'exchange_rate': float(entry.exchange_rate),
            'status': entry.get_status_display(),
            'status_code': entry.status,
            'date': entry.date.strftime('%Y-%m-%d'),
            'date_formatted': entry.date.strftime('%B %d, %Y'),
            'notes': entry.notes or '',
            'has_proof': entry.has_proof,
            'evidence': evidence,
            'approvals': approvals,
            'disputes': disputes,
            'tier_metadata': entry.tier_metadata or {},
            'created_at': entry.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': entry.updated_at.strftime('%Y-%m-%d %H:%M'),
        }
    
    def get_all_for_export(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        tier: Optional[str] = None,
        date_range: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all filtered entries for CSV export (no pagination).
        
        Args:
            search: Search term
            status: Status filter
            tier: Tier filter
            date_range: Date range preset
            
        Returns:
            List of all matching entries formatted for export
        """
        queryset = self.get_base_queryset()
        
        # Apply filters
        queryset = self.apply_filters(queryset, status=status, tier=tier)
        
        if date_range and date_range != 'all_time':
            queryset = self.apply_date_range_preset(queryset, date_range)
        
        if search:
            queryset = self.apply_search(queryset, search)
        
        # Sort by date descending
        queryset = queryset.order_by('-date', '-created_at')
        
        return self.format_entries_for_display(list(queryset))
