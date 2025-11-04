"""
API endpoints for bulk actions on suggested positions

Provides quick automation for staff review workflow.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from decimal import Decimal
import json
import logging

from ...models import SuggestedPosition
from ...services.auto_approval_service import AutoApprovalService

logger = logging.getLogger(__name__)


@staff_member_required
@require_http_methods(["POST"])
def bulk_approve_excellent(request):
    """
    AJAX endpoint: Bulk approve EXCELLENT positions and distribute to accounts
    
    POST body:
        {
            "min_score": 95,
            "top_n": 6,
            "auto_distribute": true
        }
    
    Returns:
        {
            "success": true,
            "approved_count": 10,
            "distributed_count": 6,
            "batch_count": 3,
            "notifications_sent": 3,
            "pending_remaining": 2,
            "approved_total": 10
        }
    """
    try:
        # Parse request body
        data = json.loads(request.body) if request.body else {}
        min_score = data.get('min_score', 95)
        top_n = data.get('top_n', 6)
        auto_distribute = data.get('auto_distribute', True)
        
        logger.info("=" * 80)
        logger.info(f"🤖 BULK APPROVE API: Min Score {min_score}, Top {top_n}, Distribute: {auto_distribute}")
        logger.info("=" * 80)
        
        # Find pending positions with score >= threshold
        pending_positions = SuggestedPosition.objects.filter(
            review_status='pending',
            ai_score__gte=min_score
        ).order_by('-ai_score')
        
        pending_count = pending_positions.count()
        
        if pending_count == 0:
            return JsonResponse({
                'success': False,
                'message': f'No pending positions found with score ≥{min_score}'
            })
        
        logger.info(f"📊 Found {pending_count} EXCELLENT positions to approve")
        
        # Get their IDs
        suggestion_ids = list(pending_positions.values_list('id', flat=True))
        
        # Run auto-approval pipeline
        auto_service = AutoApprovalService()
        
        with transaction.atomic():
            pipeline_result = auto_service.run_full_pipeline(
                suggestion_ids=suggestion_ids,
                staff_user=request.user,
                auto_distribute=auto_distribute,
                notify_clients=True,
                top_n=top_n  # Pass top_n parameter
            )
        
        approved_count = len(pipeline_result['approval_result']['approved'])
        distributed_count = pipeline_result['distribution_result'].get('total_distributed', 0)
        batch_count = pipeline_result['batch_result'].get('batch_count', 0)
        notifications_sent = pipeline_result.get('notifications_sent', 0)
        
        # Get updated counts
        pending_remaining = SuggestedPosition.objects.filter(review_status='pending').count()
        approved_total = SuggestedPosition.objects.filter(review_status='approved').count()
        
        logger.info(f"✅ Bulk approval complete: {approved_count} approved, {distributed_count} distributed")
        logger.info("=" * 80)
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully approved {approved_count} positions',
            'approved_count': approved_count,
            'distributed_count': distributed_count,
            'batch_count': batch_count,
            'notifications_sent': notifications_sent,
            'pending_remaining': pending_remaining,
            'approved_total': approved_total
        })
        
    except Exception as e:
        logger.error(f"❌ Bulk approval error: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

