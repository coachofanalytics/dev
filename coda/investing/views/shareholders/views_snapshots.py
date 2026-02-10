"""
Additional Snapshot View Endpoints

Snapshot lock, export, and detail views separated for modularity.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
import logging

from core.permissions import require_admin
from investing.models_shareholders import EquitySnapshot
from investing.services.shareholders.snapshot_query_service import SnapshotQueryService
from investing.services.shareholders.snapshot_lock_service import SnapshotLockService
from investing.services.shareholders.snapshot_export_service import SnapshotExportService
from investing.services.shareholders.audit_service import get_client_ip

logger = logging.getLogger(__name__)


def get_active_deal():
    """Get the currently active deal"""
    from investing.models_shareholders import Deal
    return Deal.objects.filter(is_active=True).first()


@login_required
@require_admin
@require_POST
def snapshot_lock(request, snapshot_id):
    """
    Lock a snapshot, making it immutable.
    
    URL: POST /investing/shareholders/snapshots/<id>/lock/
    """
    try:
        deal = get_active_deal()
        if not deal:
            messages.error(request, "No active deal found.")
            return redirect('shareholders:snapshots_view')
        
        # Get snapshot
        query_service = SnapshotQueryService(deal)
        snapshot = query_service.get_snapshot_by_id(snapshot_id)
        
        if not snapshot:
            raise Http404("Snapshot not found")
        
        # Lock snapshot
        SnapshotLockService.lock_snapshot(
            snapshot=snapshot,
            locked_by=request.user,
            force=request.POST.get('force', 'false').lower() == 'true',
            ip_address=get_client_ip(request)
        )
        
        messages.success(request, f"Snapshot {snapshot.version_id} locked successfully.")
        return redirect('shareholders:snapshots_view')
        
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect('shareholders:snapshots_view')
    except Exception as e:
        logger.error(f"Error locking snapshot: {str(e)}")
        messages.error(request, f"Error locking snapshot: {str(e)}")
        return redirect('shareholders:snapshots_view')


@login_required
@require_admin
def snapshot_detail(request, snapshot_id):
    """
    View detailed snapshot with member breakdown.
    
    URL: GET /investing/shareholders/snapshots/<id>/
    """
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found.")
            return redirect('shareholders:snapshots_view')
        
        # Get snapshot with lines
        query_service = SnapshotQueryService(deal)
        snapshot = query_service.get_snapshot_by_id(snapshot_id)
        
        if not snapshot:
            raise Http404("Snapshot not found")
        
        # Log view
        SnapshotLockService.log_snapshot_view(
            snapshot=snapshot,
            viewed_by=request.user,
            ip_address=get_client_ip(request)
        )
        
        # Get snapshot lines
        lines = snapshot.lines.all().order_by('-equity_percentage', 'member_name')
        
        # Format for template
        members_data = []
        for line in lines:
            members_data.append({
                'member_name': line.member_name,
                'member_type': line.member_type,
                'role': line.member_role or '',
                'cash_usd': line.cash_usd,
                'inkind_usd': line.inkind_usd,
                'time_usd': line.time_usd,
                'work_usd': line.work_usd,
                'weighted_total_usd': line.weighted_total_usd,
                'equity_percentage': line.equity_percentage,
            })
        
        context = {
            'title': f'Snapshot {snapshot.version_id}',
            'page_title': f'Snapshot Detail - {snapshot.version_id}',
            'user': request.user,
            'deal': deal,
            'snapshot': snapshot,
            'members_data': members_data,
            'can_lock': snapshot.can_be_locked,
            'days_until_lock': snapshot.days_until_auto_lock,
        }
        
        return render(request, 'investing/shareholders/shareholders_snapshot_detail.html', context)
        
    except Http404:
        messages.error(request, "Snapshot not found.")
        return redirect('shareholders:snapshots_view')
    except Exception as e:
        logger.error(f"Error viewing snapshot detail: {str(e)}")
        messages.error(request, f"Error loading snapshot: {str(e)}")
        return redirect('shareholders:snapshots_view')


@login_required
@require_admin
def snapshots_export_csv(request):
    """
    Export filtered snapshots list to CSV.
    
    URL: GET /investing/shareholders/snapshots/export/
    """
    try:
        deal = get_active_deal()
        if not deal:
            messages.error(request, "No active deal found.")
            return redirect('shareholders:snapshots_view')
        
        # Get filter parameters (same as list view)
        search = request.GET.get('search', '').strip()
        status = request.GET.get('status', 'all')
        
        # Get filtered snapshots (no pagination for export)
        query_service = SnapshotQueryService(deal)
        result = query_service.get_filtered_snapshots(
            search=search,
            status=status if status != 'all' else None,
            page=1,
            per_page=1000,  # Large limit for export
        )
        
        # Export to CSV
        response = SnapshotExportService.export_snapshot_list_csv(
            result['snapshots']
        )
        
        # Log exports for first snapshot (sample)
        if result['snapshots']:
            SnapshotLockService.log_snapshot_export(
                snapshot=result['snapshots'][0],
                exported_by=request.user,
                export_format='CSV',
                ip_address=get_client_ip(request)
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting snapshots: {str(e)}")
        messages.error(request, f"Error exporting snapshots: {str(e)}")
        return redirect('shareholders:snapshots_view')


@login_required
@require_admin
def snapshot_export_detail_csv(request, snapshot_id):
    """
    Export single snapshot detail to CSV.
    
    URL: GET /investing/shareholders/snapshots/<id>/export/
    """
    try:
        deal = get_active_deal()
        if not deal:
            messages.error(request, "No active deal found.")
            return redirect('shareholders:snapshots_view')
        
        # Get snapshot
        query_service = SnapshotQueryService(deal)
        snapshot = query_service.get_snapshot_by_id(snapshot_id)
        
        if not snapshot:
            raise Http404("Snapshot not found")
        
        # Export to CSV
        response = SnapshotExportService.export_snapshot_detail_csv(snapshot)
        
        # Log export
        SnapshotLockService.log_snapshot_export(
            snapshot=snapshot,
            exported_by=request.user,
            export_format='CSV',
            ip_address=get_client_ip(request)
        )
        
        return response
        
    except Http404:
        messages.error(request, "Snapshot not found.")
        return redirect('shareholders:snapshots_view')
    except Exception as e:
        logger.error(f"Error exporting snapshot detail: {str(e)}")
        messages.error(request, f"Error exporting snapshot: {str(e)}")
        return redirect('shareholders:snapshots_view')
