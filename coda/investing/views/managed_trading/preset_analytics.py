"""
Preset Performance Analytics Views

Phase 4: Analytics & Feedback Loop
Staff dashboard showing preset/sleeve and signal tier performance.
"""

import logging
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Sum, Avg, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from decimal import Decimal

from ...services import PresetPerformanceAnalytics, SignalTierAnalytics
from ...models import OptionsPosition, SuggestedPosition, OptionsPositionHistory

logger = logging.getLogger(__name__)


@staff_member_required
def preset_analytics_dashboard(request):
    """
    Staff analytics dashboard showing preset and signal tier performance.
    
    Displays:
    - Preset-level metrics (Core Income, Balanced, Apex)
    - Signal tier metrics (Apex, Strong, Watchlist)
    - Conversion rates (suggestion → position)
    - Win rates and average returns
    """
    days_back = int(request.GET.get('days', 90))
    preset_filter = request.GET.get('preset')
    tier_filter = request.GET.get('tier')
    
    # Preset analytics
    preset_analytics = PresetPerformanceAnalytics()
    preset_performance = preset_analytics.get_preset_performance(
        days_back=days_back,
        preset_code=preset_filter
    )
    
    # Signal tier analytics
    tier_analytics = SignalTierAnalytics()
    tier_performance = tier_analytics.get_tier_performance(
        days_back=days_back,
        tier=tier_filter
    )
    
    # Overall stats
    total_suggestions = SuggestedPosition.objects.filter(
        created_at__gte=preset_performance['cutoff_date']
    ).count()
    
    total_positions = OptionsPosition.objects.filter(
        source_suggestion__isnull=False,
        entry_date__gte=preset_performance['cutoff_date']
    ).count()
    
    closed_positions = OptionsPosition.objects.filter(
        source_suggestion__isnull=False,
        status='closed',
        entry_date__gte=preset_performance['cutoff_date']
    )
    
    total_closed = closed_positions.count()
    winning_positions = closed_positions.filter(
        outcome_history__was_profitable=True
    ).count() if total_closed > 0 else 0
    
    overall_win_rate = (
        (winning_positions / total_closed * 100) if total_closed > 0 else None
    )
    
    overall_avg_pnl = None
    if total_closed > 0:
        avg_result = closed_positions.aggregate(
            avg_pnl=Avg('outcome_history__actual_return_amount')
        )
        overall_avg_pnl = avg_result['avg_pnl']
    
    context = {
        'title': 'Preset & Signal Tier Analytics',
        'days_back': days_back,
        'preset_filter': preset_filter,
        'tier_filter': tier_filter,
        'preset_performance': preset_performance,
        'tier_performance': tier_performance,
        'overall_stats': {
            'total_suggestions': total_suggestions,
            'total_positions': total_positions,
            'conversion_rate': (total_positions / total_suggestions * 100) if total_suggestions > 0 else 0,
            'closed_positions': total_closed,
            'winning_positions': winning_positions,
            'overall_win_rate': overall_win_rate,
            'overall_avg_pnl': overall_avg_pnl,
        },
    }
    
    return render(request, 'investing/staff/preset_analytics_dashboard.html', context)


@staff_member_required
@require_POST
def add_position_feedback(request, position_id):
    """
    Add staff feedback/annotation to a closed position's outcome history.
    
    POST params:
    - feedback: Text feedback/notes
    """
    position = get_object_or_404(OptionsPosition, id=position_id)
    
    if position.status != 'closed':
        return JsonResponse({'error': 'Position must be closed to add feedback'}, status=400)
    
    if not hasattr(position, 'outcome_history'):
        return JsonResponse({'error': 'Position outcome history not found'}, status=404)
    
    feedback_text = request.POST.get('feedback', '').strip()
    if not feedback_text:
        return JsonResponse({'error': 'Feedback text is required'}, status=400)
    
    history = position.outcome_history
    history.staff_feedback = feedback_text
    history.feedback_added_by = request.user
    history.feedback_added_at = timezone.now()
    history.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Feedback added successfully',
        'feedback': feedback_text,
        'added_by': request.user.get_full_name() or request.user.username,
        'added_at': history.feedback_added_at.isoformat(),
    })

