"""
Snapshot Query Service

Provides server-side filtering, search, sorting, and pagination for snapshots.
"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import date, timedelta
from django.db.models import Q, QuerySet
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
import logging

from investing.models import Deal, EquitySnapshot

logger = logging.getLogger(__name__)


class SnapshotQueryService:
    """
    Service for querying and filtering snapshots with server-side operations.
    """
    
    # Status mapping for display
    STATUS_DISPLAY = {
        'DRAFT': 'Draft',
        'LOCKED': 'Locked',
        'FINALIZED': 'Finalized',
    }
    
    def __init__(self, deal: Deal):
        """
        Initialize service for a specific deal.
        
        Args:
            deal: The Deal instance to query snapshots for
        """
        self.deal = deal
    
    def get_base_queryset(self) -> QuerySet:
        """
        Get base queryset scoped to current deal with prefetching.
        
        Returns:
            QuerySet with select_related for efficient querying
        """
        return EquitySnapshot.objects.filter(
            deal=self.deal
        ).prefetch_related('lines').select_related('created_by', 'locked_by')
    
    def get_filtered_snapshots(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        is_locked: Optional[bool] = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Dict:
        """
        Get filtered and paginated snapshots.
        
        Args:
            search: Search term for version_id or notes
            status: Status filter (DRAFT, LOCKED, FINALIZED)
            date_from: Start date filter
            date_to: End date filter
            is_locked: Filter by locked status
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict with snapshots, pagination info, and filter state
        """
        queryset = self.get_base_queryset()
        
        # Apply search
        if search:
            queryset = queryset.filter(
                Q(version_id__icontains=search) |
                Q(notes__icontains=search)
            )
        
        # Apply status filter
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        # Apply locked filter
        if is_locked is not None:
            queryset = queryset.filter(is_locked=is_locked)
        
        # Apply date range filter
        if date_from:
            queryset = queryset.filter(snapshot_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(snapshot_date__lte=date_to)
        
        # Order by snapshot date (newest first)
        queryset = queryset.order_by('-snapshot_date', '-created_at')
        
        # Paginate
        paginator = Paginator(queryset, per_page)
        
        try:
            snapshots_page = paginator.page(page)
        except PageNotAnInteger:
            snapshots_page = paginator.page(1)
        except EmptyPage:
            snapshots_page = paginator.page(paginator.num_pages)
        
        return {
            'snapshots': snapshots_page.object_list,
            'page': snapshots_page.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': snapshots_page.has_next(),
            'has_previous': snapshots_page.has_previous(),
            'per_page': per_page,
        }
    
    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics for snapshots.
        
        Returns:
            Dict with counts and metrics
        """
        all_snapshots = self.get_base_queryset()
        
        total_count = all_snapshots.count()
        locked_count = all_snapshots.filter(is_locked=True).count()
        draft_count = all_snapshots.filter(status='DRAFT').count()
        
        # Get latest finalized snapshot
        latest_finalized = all_snapshots.filter(
            status='FINALIZED'
        ).order_by('-snapshot_date').first()
        
        # Get next scheduled (based on auto_lock_date)
        today = date.today()
        next_scheduled = all_snapshots.filter(
            is_locked=False,
            auto_lock_date__gt=today
        ).order_by('auto_lock_date').first()
        
        return {
            'total_count': total_count,
            'locked_count': locked_count,
            'draft_count': draft_count,
            'latest_finalized': latest_finalized,
            'latest_finalized_date': latest_finalized.snapshot_date if latest_finalized else None,
            'next_scheduled': next_scheduled,
            'next_scheduled_date': next_scheduled.auto_lock_date if next_scheduled else None,
            'next_scheduled_days': (
                (next_scheduled.auto_lock_date - today).days 
                if next_scheduled and next_scheduled.auto_lock_date 
                else 0
            ),
        }
    
    def get_snapshot_by_id(self, snapshot_id: int) -> Optional[EquitySnapshot]:
        """
        Get a specific snapshot by ID with all related data.
        
        Args:
            snapshot_id: Snapshot ID
            
        Returns:
            EquitySnapshot instance or None
        """
        try:
            return self.get_base_queryset().prefetch_related(
                'lines__member'
            ).get(id=snapshot_id)
        except EquitySnapshot.DoesNotExist:
            return None
    
    def get_snapshot_by_version(self, version_id: str) -> Optional[EquitySnapshot]:
        """
        Get a specific snapshot by version ID.
        
        Args:
            version_id: Version identifier
            
        Returns:
            EquitySnapshot instance or None
        """
        try:
            return self.get_base_queryset().prefetch_related(
                'lines__member'
            ).get(version_id=version_id)
        except EquitySnapshot.DoesNotExist:
            return None
    
    def generate_next_version_id(self, prefix: str = 'v') -> str:
        """
        Generate the next sequential version ID for the deal.
        
        Args:
            prefix: Version prefix (default 'v')
            
        Returns:
            Next version ID (e.g., 'v1.1', 'v1.2')
        """
        # Get all snapshots ordered by version
        snapshots = self.get_base_queryset().order_by('-created_at')
        
        if not snapshots.exists():
            return f"{prefix}1.0-genesis"
        
        # Get latest snapshot
        latest = snapshots.first()
        latest_version = latest.version_id
        
        # Extract numeric version if possible
        import re
        match = re.search(r'v?(\d+)\.(\d+)', latest_version)
        
        if match:
            major = int(match.group(1))
            minor = int(match.group(2)) + 1
            return f"{prefix}{major}.{minor}"
        else:
            # Fallback to count-based
            count = snapshots.count()
            return f"{prefix}1.{count}"
