"""
Staff Views for Position Suggestions

Views for staff to review, edit, and approve auto-fetched positions
before sending to clients for batch approval.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json
import logging

from ...models import SuggestedPosition, OptionsPosition, PositionBatch, ManagedTradingAccount
from ...services import PositionFetcherService, BatchApprovalService, ManagedTradingService

logger = logging.getLogger(__name__)


@staff_member_required
def suggested_positions_list(request):
    """
    Staff dashboard: View all auto-fetched positions pending review
    
    Shows table of suggestions with:
    - Source (OptionPlay/Thinkorswim)
    - Position details (symbol, strategy, probability)
    - Financial metrics (premium, P&L)
    - Review status
    - Actions (Edit, Approve, Reject)
    """
    # Get all pending suggestions (sorted by AI score first!)
    pending = SuggestedPosition.objects.filter(
        review_status='pending'
    ).order_by('-ai_score', '-probability_of_profit', '-fetched_at')
    
    # Get approved suggestions not yet converted to batch
    approved = SuggestedPosition.objects.filter(
        review_status__in=['approved', 'modified'],
        created_position__isnull=True  # Not yet converted
    ).order_by('-ai_score', '-probability_of_profit')
    
    # Get recently rejected (last 7 days)
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)
    rejected = SuggestedPosition.objects.filter(
        review_status='rejected',
        reviewed_at__gte=week_ago
    ).order_by('-reviewed_at')
    
    # Statistics
    from django.db.models import Avg, Sum, Count, Q
    
    stats = {
        'total_pending': pending.count(),
        'total_approved': approved.count(),
        'total_rejected': rejected.count(),
        'avg_probability': pending.aggregate(avg=Avg('probability_of_profit'))['avg'] or 0,
        'total_premium': pending.aggregate(sum=Sum('premium_collected'))['sum'] or 0,
        # AI Scoring Stats
        'avg_ai_score': pending.aggregate(avg=Avg('ai_score'))['avg'] or 0,
        'top_score': pending.aggregate(max=Avg('ai_score'))['max'] or 0,
        'excellent_count': pending.filter(ai_rating='EXCELLENT').count(),
        'good_count': pending.filter(ai_rating='GOOD').count(),
    }
    
    # Get active managed trading accounts for batch creation
    active_accounts = ManagedTradingAccount.objects.filter(
        status='active',
        trading_enabled=True
    ).order_by('account_number')
    
    context = {
        'pending_positions': pending,
        'approved_positions': approved,
        'rejected_positions': rejected,
        'stats': stats,
        'active_accounts': active_accounts,
    }
    return render(request, 'investing/staff/suggested_positions.html', context)


@staff_member_required
@require_POST
def fetch_positions_now(request):
    """
    Manual trigger: Fetch positions from APIs right now
    
    POST params:
    - source: 'auto', 'optionplay', or 'thinkorswim'
    - probability_min: int (default 70)
    - premium_min: int (default 100)
    - dte_min: int (default 30)
    - dte_max: int (default 60)
    """
    try:
        # Parse filters from POST data
        filters = {
            'probability_min': int(request.POST.get('probability_min', 70)),
            'premium_min': int(request.POST.get('premium_min', 100)),
            'dte_min': int(request.POST.get('dte_min', 30)),
            'dte_max': int(request.POST.get('dte_max', 60)),
            'strategies': [
                'bull_put_spread',
                'bear_call_spread',
                'bull_call_spread',
                'bear_put_spread'
            ],
            'max_positions': int(request.POST.get('max_positions', 5))
        }
        
        # Parse symbols if provided
        symbols_str = request.POST.get('symbols', '').strip()
        if symbols_str:
            filters['symbols'] = [s.strip().upper() for s in symbols_str.split(',')]
        
        # Fetch positions
        fetcher = PositionFetcherService()
        suggested = fetcher.fetch_high_probability_positions(filters)
        
        messages.success(
            request,
            f"✅ Fetched {len(suggested)} high-probability positions! "
            f"Average probability: {sum(float(p.probability_of_profit) for p in suggested) / len(suggested) if suggested else 0:.1f}%"
        )
        
    except Exception as e:
        logger.error(f"Position fetch error: {e}", exc_info=True)
        messages.error(request, f"❌ Fetch failed: {str(e)}")
    
    return redirect('investing:suggested_positions_list')


@staff_member_required
def fetch_positions_quick(request):
    """
    Quick GET trigger to fetch positions with default filters.
    Useful fallback when modal submit is unavailable.
    """
    try:
        fetcher = PositionFetcherService()
        default_filters = fetcher._get_default_filters()
        suggested = fetcher.fetch_high_probability_positions(default_filters)
        avg_prob = (
            sum(float(p.probability_of_profit) for p in suggested) / len(suggested)
            if suggested else 0
        )
        messages.success(
            request,
            f"✅ Fetched {len(suggested)} position(s). Avg probability: {avg_prob:.1f}%"
        )
    except Exception as e:
        logger.error(f"Quick fetch error: {e}", exc_info=True)
        messages.error(request, f"❌ Fetch failed: {str(e)}")
    return redirect('investing:suggested_positions_list')

@staff_member_required
def review_position(request, suggestion_id):
    """
    Review/edit a single suggested position
    
    GET: Show position details
    POST: Save edits and update review status
    """
    suggestion = get_object_or_404(SuggestedPosition, id=suggestion_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            suggestion.approve(request.user, notes=request.POST.get('notes', ''))
            messages.success(request, f"✅ Approved: {suggestion.symbol} {suggestion.strategy}")
        
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', 'Rejected by staff')
            suggestion.reject(request.user, reason)
            messages.warning(request, f"❌ Rejected: {suggestion.symbol} {suggestion.strategy}")
        
        elif action == 'modify':
            # Parse modified fields
            try:
                updated_data = {}
                
                # Update position legs if modified
                if 'positions' in request.POST:
                    updated_data['positions'] = json.loads(request.POST['positions'])
                
                # Update financial metrics if modified
                for field in ['premium_collected', 'capital_required', 'max_profit', 'max_loss', 'breakeven']:
                    if field in request.POST and request.POST[field]:
                        updated_data[field] = Decimal(request.POST[field])
                
                # Update Greeks if modified
                for field in ['position_delta', 'position_theta', 'position_gamma', 'position_vega']:
                    if field in request.POST and request.POST[field]:
                        updated_data[field] = Decimal(request.POST[field])
                
                notes = request.POST.get('modification_notes', '')
                suggestion.modify(request.user, updated_data, notes)
                
                messages.success(request, f"✅ Modified & Approved: {suggestion.symbol} {suggestion.strategy}")
            
            except Exception as e:
                messages.error(request, f"❌ Modification error: {str(e)}")
                logger.error(f"Position modification error: {e}", exc_info=True)
        
        return redirect('investing:suggested_positions_list')
    
    # GET: Show position details
    context = {
        'suggestion': suggestion,
        'legs': suggestion.positions if isinstance(suggestion.positions, list) else [],
    }
    return render(request, 'investing/staff/review_position.html', context)


@staff_member_required
@require_POST
def create_batch_from_suggestions(request):
    """
    Convert approved SuggestedPositions to OptionsPositions and create PositionBatch
    
    POST params:
    - suggestion_ids: Comma-separated IDs of approved suggestions
    - account_id: Target ManagedTradingAccount ID
    """
    try:
        # Parse selected suggestion IDs
        suggestion_ids = request.POST.get('suggestion_ids', '').split(',')
        suggestion_ids = [int(sid.strip()) for sid in suggestion_ids if sid.strip()]
        
        if not suggestion_ids:
            messages.error(request, "❌ No positions selected")
            return redirect('investing:suggested_positions_list')
        
        # Get target account
        account_id = request.POST.get('account_id')
        if not account_id:
            messages.error(request, "❌ No target account selected")
            return redirect('investing:suggested_positions_list')
        
        account = get_object_or_404(ManagedTradingAccount, id=account_id)
        
        # Get approved suggestions
        suggestions = SuggestedPosition.objects.filter(
            id__in=suggestion_ids,
            review_status__in=['approved', 'modified']
        )
        
        if not suggestions.exists():
            messages.error(request, "❌ No approved positions found")
            return redirect('investing:suggested_positions_list')
        
        # Convert suggestions to actual positions
        with transaction.atomic():
            created_positions = []
            trading_service = ManagedTradingService()
            
            for suggestion in suggestions:
                # Prepare position data for ManagedTradingService
                position_data = {
                    'symbol': suggestion.symbol,
                    'strategy': suggestion.strategy,
                    'positions': suggestion.positions,
                    'expiration_date': suggestion.expiration_date,
                    'capital_required': float(suggestion.capital_required),
                    'premium_collected': float(suggestion.premium_collected),
                    'max_profit': float(suggestion.max_profit),
                    'max_loss': float(suggestion.max_loss),
                    'position_delta': float(suggestion.position_delta),
                    'position_theta': float(suggestion.position_theta),
                    'position_gamma': float(suggestion.position_gamma),
                    'position_vega': float(suggestion.position_vega),
                    'notes': f"Auto-fetched from {suggestion.get_source_display()}. {suggestion.ai_reasoning}"
                }
                
                # Create OptionsPosition using existing service (don't deduct balance yet)
                position = trading_service.create_position(account, position_data, deduct_balance=False)
                
                # Set position to pending for batch approval
                position.status = 'pending'
                position.requires_client_approval = True
                position.save()
                
                # Link suggestion to created position
                suggestion.created_position = position
                suggestion.review_status = 'converted'
                suggestion.save()
                
                created_positions.append(position)
            
            # Create PositionBatch from created positions
            batch_service = BatchApprovalService()
            batch = batch_service.create_weekly_batch(account)
            
            if batch:
                messages.success(
                    request,
                    f"✅ Created batch {batch.batch_number} with {len(created_positions)} positions! "
                    f"Client has 24 hours to approve."
                )
            else:
                messages.warning(
                    request,
                    f"✅ Created {len(created_positions)} positions, but batch creation failed. "
                    f"Positions are pending in account."
                )
    
    except Exception as e:
        logger.error(f"Batch creation error: {e}", exc_info=True)
        messages.error(request, f"❌ Error creating batch: {str(e)}")
    
    return redirect('investing:suggested_positions_list')


@staff_member_required
def ajax_approve_position(request, suggestion_id):
    """AJAX endpoint: Quick approve a position"""
    try:
        if request.method == 'POST':
            suggestion = get_object_or_404(SuggestedPosition, id=suggestion_id)
            notes = request.POST.get('notes', '')
            suggestion.approve(request.user, notes)
            
            return JsonResponse({
                'success': True,
                'message': f'Approved {suggestion.symbol} {suggestion.strategy}'
            })
        
        return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
    except Exception as e:
        logger.error(f"Approval error: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_member_required
def ajax_reject_position(request, suggestion_id):
    """AJAX endpoint: Quick reject a position"""
    if request.method == 'POST':
        suggestion = get_object_or_404(SuggestedPosition, id=suggestion_id)
        reason = request.POST.get('reason', 'Rejected by staff')
        suggestion.reject(request.user, reason)
        
        return JsonResponse({
            'success': True,
            'message': f'Rejected {suggestion.symbol} {suggestion.strategy}'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


# Add missing import at top
from django.db import models

