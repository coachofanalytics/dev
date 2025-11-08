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
from decimal import Decimal, InvalidOperation
import json
import logging

from celery.exceptions import OperationalError as CeleryOperationalError
try:  # Kombu may not distinguish from Celery on all installs
    from kombu.exceptions import OperationalError as KombuOperationalError
except Exception:  # pragma: no cover - kombu always present with Celery, but fail safe
    KombuOperationalError = CeleryOperationalError

from ...models import (
    SuggestedPosition,
    OptionsPosition,
    PositionBatch,
    ManagedTradingAccount,
    TradingRule,
    TradingActivity,
)
from ...services import PositionFetcherService, BatchApprovalService, ManagedTradingService
from ...services.unusual_whales_service import UnusualWhalesService
from ...services.position_ranking_service import PositionRankingService
from ...utils import build_preview_payloads
from ...tasks import managed_income_scheduler

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
    
    NEW (Phase 10A): Top 5 Recommended with multi-factor ranking
    """
    def _safe_number(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return value

    def _normalize_legs(legs_payload):
        if not legs_payload:
            return []
        normalized = []
        for leg in legs_payload:
            normalized.append({
                'type': leg.get('type') or leg.get('leg_type'),
                'direction': leg.get('direction'),
                'contracts': leg.get('contracts'),
                'strike': _safe_number(leg.get('strike')),
                'expiration': leg.get('expiration') or leg.get('expiry'),
                'premium': _safe_number(leg.get('premium')),
                'delta': _safe_number(leg.get('delta')),
                'theta': _safe_number(leg.get('theta')),
            })
        return normalized

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
    
    # ========== PHASE 10A: SMART POSITION RANKING ==========
    top_5_recommended = []
    all_ranked = []
    
    if pending.exists():
        try:
            ranker = PositionRankingService()
            all_ranked = ranker.rank_positions(pending)
            top_5_recommended = ranker.get_top_n(all_ranked, n=5)
            
            logger.info(f"🏆 Top 5 ranked: {[item['position'].symbol for item in top_5_recommended]}")
        except Exception as e:
            logger.error(f"Ranking error: {e}", exc_info=True)
            # Graceful degradation - continue without ranking
    # ========================================================
    
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
    
    # Heat map data (symbol & strategy concentration)
    heatmap_symbols_qs = pending.values('symbol').annotate(
        total_capital=Sum('capital_required'),
        avg_ai_score=Avg('ai_score'),
        avg_probability=Avg('probability_of_profit'),
        position_count=Count('id'),
    ).order_by('-total_capital')[:12]

    strategy_labels = dict(SuggestedPosition.STRATEGY_CHOICES)
    heatmap_strategies_qs = pending.values('strategy').annotate(
        total_capital=Sum('capital_required'),
        avg_probability=Avg('probability_of_profit'),
        position_count=Count('id'),
    ).order_by('-total_capital')

    heatmap_symbols = [
        {
            'symbol': item['symbol'],
            'total_capital': float(item['total_capital'] or 0),
            'avg_ai_score': float(item['avg_ai_score'] or 0),
            'avg_probability': float(item['avg_probability'] or 0),
            'position_count': item['position_count'],
        }
        for item in heatmap_symbols_qs
    ]

    heatmap_strategies = [
        {
            'strategy': item['strategy'],
            'strategy_label': strategy_labels.get(item['strategy'], item['strategy']),
            'total_capital': float(item['total_capital'] or 0),
            'avg_probability': float(item['avg_probability'] or 0),
            'position_count': item['position_count'],
        }
        for item in heatmap_strategies_qs
    ]

    heatmap_summary = None
    if heatmap_symbols or heatmap_strategies:
        total_capital = sum(item['total_capital'] for item in heatmap_symbols)
        heatmap_summary = {
            'total_capital': total_capital,
            'top_symbols': heatmap_symbols[:3],
            'top_strategies': heatmap_strategies[:2],
        }

    # Get active managed trading accounts for batch creation
    active_accounts = ManagedTradingAccount.objects.filter(
        status='active',
        trading_enabled=True
    ).prefetch_related('trading_rules', 'client').order_by('account_number')

    account_limits = {}
    for account in active_accounts:
        max_percentage = None
        max_absolute = None

        for rule in account.trading_rules.all():
            if not rule.is_active:
                continue

            config = rule.rule_config or {}
            if rule.rule_type == 'position_size_percentage':
                raw_pct = (
                    config.get('max_percentage_per_position')
                    or config.get('max_percentage')
                )
                if raw_pct is not None:
                    try:
                        max_percentage = Decimal(str(raw_pct))
                    except Exception:
                        logger.warning(
                            "Invalid max_percentage_per_position for account %s: %s",
                            account.account_number,
                            raw_pct,
                        )
            elif rule.rule_type == 'position_limit':
                raw_abs = config.get('max_position_size')
                if raw_abs is not None:
                    try:
                        max_absolute = Decimal(str(raw_abs))
                    except Exception:
                        logger.warning(
                            "Invalid max_position_size for account %s: %s",
                            account.account_number,
                            raw_abs,
                        )

        reference_capital = account.initial_capital or Decimal('0')
        max_dollar_from_pct = None
        if max_percentage is not None and reference_capital > 0:
            max_dollar_from_pct = (reference_capital * max_percentage) / Decimal('100')

        # Prefer explicit absolute rule over derived value
        effective_max_dollar = max_absolute or max_dollar_from_pct

        account_limits[str(account.id)] = {
            'account_number': account.account_number,
            'account_name': account.account_name,
            'client_name': account.client.get_full_name() if account.client else '',
            'reference_capital': float(reference_capital),
            'cash_available': float(account.cash_available or Decimal('0')),
            'max_percentage': float(max_percentage) if max_percentage is not None else None,
            'max_absolute': float(max_absolute) if max_absolute is not None else None,
            'derived_max_dollar': float(max_dollar_from_pct) if max_dollar_from_pct is not None else None,
            'effective_max_dollar': float(effective_max_dollar) if effective_max_dollar is not None else None,
        }
    
    preview_payloads = build_preview_payloads(pending, approved)

    context = {
        'pending_positions': pending,
        'approved_positions': approved,
        'rejected_positions': rejected,
        'stats': stats,
        'active_accounts': active_accounts,
        # Phase 10A: Ranking
        'top_5_recommended': top_5_recommended,
        'all_ranked_positions': all_ranked,
        'ranking_enabled': len(top_5_recommended) > 0,
        # Phase 1: Heatmap insights
        'heatmap_symbols': heatmap_symbols,
        'heatmap_strategies': heatmap_strategies,
        'heatmap_summary': heatmap_summary,
        'preview_payloads': preview_payloads,
        'account_limits': account_limits,
        'can_adjust_limits': request.user.is_superuser,
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

        uw_summary = None
        if suggested:
            uw_service = UnusualWhalesService()
            if uw_service.is_enabled():
                uw_summary = uw_service.apply_flow_to_suggestions(suggested)
        avg_prob = (
            sum(float(p.probability_of_profit) for p in suggested) / len(suggested)
            if suggested else 0
        )

        extra = ''
        if uw_summary and uw_summary.get('enriched'):
            extra = f" • UW signals on {uw_summary['enriched']} symbol(s)"
        elif uw_summary and uw_summary.get('symbols_requested'):
            extra = " • UW signals unavailable for fetched symbols"
        
        messages.success(
            request,
            f"✅ Fetched {len(suggested)} high-probability positions! Avg probability: {avg_prob:.1f}%" + extra
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
        uw_summary = None
        if suggested:
            uw_service = UnusualWhalesService()
            if uw_service.is_enabled():
                uw_summary = uw_service.apply_flow_to_suggestions(suggested)

        avg_prob = (
            sum(float(p.probability_of_profit) for p in suggested) / len(suggested)
            if suggested else 0
        )
        extra = ''
        if uw_summary and uw_summary.get('enriched'):
            extra = f" • UW signals on {uw_summary['enriched']} symbol(s)"
        elif uw_summary and uw_summary.get('symbols_requested'):
            extra = " • UW signals unavailable for fetched symbols"

        messages.success(
            request,
            f"✅ Fetched {len(suggested)} position(s). Avg probability: {avg_prob:.1f}%" + extra
        )
    except Exception as e:
        logger.error(f"Quick fetch error: {e}", exc_info=True)
        messages.error(request, f"❌ Fetch failed: {str(e)}")
    return redirect('investing:suggested_positions_list')


@staff_member_required
@require_POST
def trigger_managed_income_scheduler(request):
    if not request.user.is_superuser:
        messages.error(request, "❌ Only superusers can trigger the managed income scheduler.")
        return redirect('investing:suggested_positions_list')

    try:
        managed_income_scheduler.delay()
        messages.success(request, "✅ Managed income scheduler queued. Digest will send shortly.")
    except (CeleryOperationalError, KombuOperationalError, ConnectionError) as exc:
        logger.warning("Celery broker unavailable; running managed_income_scheduler inline. %s", exc)
        try:
            eager_result = managed_income_scheduler.apply(args=(), kwargs={})
            payload = getattr(eager_result, 'result', eager_result)
            if isinstance(payload, dict) and payload.get('success'):
                messages.success(
                    request,
                    "✅ Managed income scheduler ran inline (Celery unavailable). Digest will reflect the latest run.",
                )
            else:
                messages.warning(
                    request,
                    "⚠️ Scheduler ran inline but did not report success. Check logs for details.",
                )
        except Exception as inline_exc:  # pragma: no cover - safety net for unexpected errors
            logger.error("Managed income scheduler inline execution failed: %s", inline_exc, exc_info=True)
            messages.error(
                request,
                "❌ Scheduler trigger failed: Celery unavailable and inline run encountered an error.",
            )
    except Exception as exc:  # Catch any other errors and surface to user
        logger.error("Managed income scheduler trigger failed: %s", exc, exc_info=True)
        messages.error(request, f"❌ Scheduler trigger failed: {exc}")

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
@require_POST
def update_account_position_limit(request):
    """
    Superuser endpoint to adjust per-position capital limits for managed accounts.
    """
    if not request.user.is_superuser:
        messages.error(request, "❌ Only superusers can modify account risk limits.")
        return redirect('investing:suggested_positions_list')

    account_id = request.POST.get('account_id')
    if not account_id:
        messages.error(request, "❌ Missing account selection.")
        return redirect('investing:suggested_positions_list')

    account = get_object_or_404(ManagedTradingAccount, id=account_id)

    def _parse_decimal(value, field_name):
        if value is None or str(value).strip() == '':
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            messages.error(request, f"❌ Invalid number for {field_name}.")
            return None

    max_percentage = _parse_decimal(request.POST.get('max_percentage'), "max % per position")
    max_absolute = _parse_decimal(request.POST.get('max_absolute'), "max dollar per position")

    if max_percentage is None or max_percentage <= 0:
        messages.error(request, "❌ Max % per position must be greater than 0.")
        return redirect('investing:suggested_positions_list')

    if max_percentage > Decimal('100'):
        messages.error(request, "❌ Max % per position cannot exceed 100%.")
        return redirect('investing:suggested_positions_list')

    if max_absolute is None or max_absolute <= 0:
        reference_capital = account.initial_capital or Decimal('0')
        max_absolute = (reference_capital * max_percentage) / Decimal('100') if reference_capital else None

    if max_absolute is None or max_absolute <= 0:
        messages.error(request, "❌ Unable to derive a valid dollar cap. Please enter one manually.")
        return redirect('investing:suggested_positions_list')

    percentage_rule, _ = TradingRule.objects.get_or_create(
        managed_account=account,
        rule_type='position_size_percentage',
        defaults={
            'rule_name': 'Per-position capital cap',
            'rule_config': {},
            'priority': 5,
        }
    )
    percentage_rule.rule_config = {
        **(percentage_rule.rule_config or {}),
        'max_percentage_per_position': str(max_percentage),
    }
    percentage_rule.is_active = True
    percentage_rule.save(update_fields=['rule_config', 'is_active', 'updated_at'])

    absolute_rule, _ = TradingRule.objects.get_or_create(
        managed_account=account,
        rule_type='position_limit',
        defaults={
            'rule_name': 'Absolute position size cap',
            'rule_config': {},
            'priority': 6,
        }
    )
    absolute_rule.rule_config = {
        **(absolute_rule.rule_config or {}),
        'max_position_size': str(max_absolute),
    }
    absolute_rule.is_active = True
    absolute_rule.save(update_fields=['rule_config', 'is_active', 'updated_at'])

    TradingActivity.objects.create(
        managed_account=account,
        activity_type='rule_changed',
        description=f"Updated per-position cap to {max_percentage}% (${max_absolute:,.2f}).",
        performed_by=request.user,
        data_snapshot={
            'max_percentage_per_position': str(max_percentage),
            'max_position_size': str(max_absolute),
        }
    )

    messages.success(
        request,
        f"✅ Updated {account.account_number} limit to {max_percentage}% (${max_absolute:,.2f})."
    )
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


@staff_member_required
@require_POST
def accept_top_5(request):
    """
    PHASE 10A: Accept Top 5 Recommended Positions
    
    Auto-approves the top 5 ranked positions based on multi-factor ranking:
    - Whales (35%) + Earnings (25%) + ROC (20%) + DTE (20%)
    
    Returns JSON response with approved positions
    """
    try:
        # Get pending positions
        pending = SuggestedPosition.objects.filter(review_status='pending')
        
        if not pending.exists():
            return JsonResponse({
                'success': False,
                'message': 'No pending positions to rank'
            }, status=400)
        
        # Rank positions
        ranker = PositionRankingService()
        all_ranked = ranker.rank_positions(pending)
        top_5 = ranker.get_top_n(all_ranked, n=5)
        
        if not top_5:
            return JsonResponse({
                'success': False,
                'message': 'Ranking returned no results'
            }, status=400)
        
        # Approve top 5
        approved_positions = []
        with transaction.atomic():
            for item in top_5:
                position = item['position']
                
                # Approve with ranking details in notes
                ranking_notes = (
                    f"Auto-approved as Top {item['rank']} position "
                    f"(Score: {item['total_score']:.1f}/100)\n"
                    f"Ranking Breakdown:\n"
                    f"  🐋 Whales: {item['breakdown']['whales_score']:.1f}/100\n"
                    f"  📅 Earnings: {item['breakdown']['earnings_score']:.1f}/100\n"
                    f"  💰 ROC: {item['breakdown']['profit_score']:.1f}/100\n"
                    f"  ⏰ DTE: {item['breakdown']['dte_score']:.1f}/100\n"
                    f"Recommendation: {item['recommendation']}\n"
                    f"Reason: {item['selection_reason']}"
                )
                
                position.approve(request.user, notes=ranking_notes)
                
                approved_positions.append({
                    'symbol': position.symbol,
                    'strategy': position.get_strategy_display(),
                    'rank': item['rank'],
                    'score': float(item['total_score']),
                    'recommendation': item['recommendation']
                })
        
        logger.info(f"✅ Auto-approved top 5: {[p['symbol'] for p in approved_positions]}")
        
        return JsonResponse({
            'success': True,
            'message': f"✅ Approved top 5 positions!",
            'approved_count': len(approved_positions),
            'approved_positions': approved_positions
        })
    
    except Exception as e:
        logger.error(f"Accept Top 5 error: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f"Error: {str(e)}"
        }, status=500)

