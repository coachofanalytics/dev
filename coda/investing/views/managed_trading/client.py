"""
Client Portal Views

Read-only views for clients to monitor their managed trading accounts.
"""

from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from datetime import date, timedelta
import logging

from ...models import ManagedTradingAccount, OptionsPosition, SuggestedPosition, TradingActivity
from ...services import ManagedTradingService
from ...services.position_ranking_service import PositionRankingService
from ...services.portfolio_preset_service import PortfolioPresetBuilder
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@login_required
def client_portal(request):
    """
    Client portal - view all their managed accounts
    
    Permissions: Authenticated users viewing their own accounts
    """
    # Get all managed accounts for this client
    accounts_queryset = ManagedTradingAccount.objects.filter(
        client=request.user
    ).select_related('account_manager').annotate(
        open_positions_count=Count('positions', filter=Q(positions__status='open'))
    ).order_by('-created_at')
    accounts = list(accounts_queryset)
    
    # Calculate totals across all accounts
    total_invested = sum(
        (acc.initial_capital or Decimal('0.00')) for acc in accounts
    )
    total_current_value = sum(
        (acc.current_balance or Decimal('0.00')) for acc in accounts
    )
    total_pnl = sum(
        (acc.total_profit_loss or Decimal('0.00')) for acc in accounts
    )
    
    # Get overall stats
    total_open_positions = sum([
        getattr(acc, 'open_positions_count', 0) or 0
        for acc in accounts
    ])
    
    ranker = PositionRankingService()
    auto_metrics = ranker.get_auto_approval_metrics()
    if not auto_metrics.get('total'):
        auto_metrics = None

    # Public preview of portfolio presets (read-only; no deploy)
    portfolio_presets_public = []
    pending = SuggestedPosition.objects.filter(review_status='pending')
    if pending.exists():
        try:
            ranked = ranker.rank_positions(pending)
            builder = PortfolioPresetBuilder()
            portfolio_presets_public = builder.build_presets(pending, pre_ranked=ranked)
        except Exception:
            portfolio_presets_public = []

    tier_matrix = [
        {
            'code': 'starter',
            'name': 'Starter',
            'status': 'Available',
            'monthly_target': 300,
            'monthly_fee': 99,
            'net_potential': 300 - 99,  # $201/mo
            'fee_structure': '$99/mo + 15% of profits above 5% hurdle',
            'performance_fee_note': '15% of profits above 5% annual return hurdle',
            'capital_profile': '~$10K Core Income Focus',
            'capital_requirement': 10000,
            'data_access': 'Basic email alerts with signals',
            'automation': 'No automation - signals only',
            'service_model': 'SIGNAL-ONLY (SELF-SERVICE)',
            'service_description': 'Basic signals delivered, you do everything yourself',
            'includes': [
                'Email alerts with trading signals',
                'Basic portfolio suggestions',
                'You select, execute & manage all positions',
                'You monitor all risk',
                'Email support only',
            ],
        },
        {
            'code': 'balanced',
            'name': 'Balanced 900',
            'status': 'Available',
            'monthly_target': 900,
            'monthly_fee': 249,
            'net_potential': 900 - 249,  # $651/mo
            'fee_structure': '$249/mo + 12% of profits above 6% hurdle',
            'performance_fee_note': '12% of profits above 6% annual return hurdle',
            'capital_profile': '60% Core · 30% Momentum · 10% Events',
            'capital_requirement': 25000,
            'data_access': 'OptionPlay automation, UW trial weeks',
            'automation': 'Auto-ranked portfolio sleeves + SMS alerts',
            'service_model': 'AUTOMATED SIGNALS (SELF-SERVICE)',
            'service_description': 'Auto-ranked sleeves delivered to you, you execute & manage positions',
            'includes': [
                'Auto-ranked portfolio sleeves delivered to you',
                'SMS/WhatsApp alerts when new signals ready',
                'Automated refresh (2x daily feed)',
                'You execute & manage all positions yourself',
                'Balanced sleeve auto-refresh',
                'Monthly sleeve performance report',
                'Standard support',
            ],
        },
        {
            'code': 'elite',
            'name': 'Elite 1500',
            'status': 'Available',
            'monthly_target': 1500,  # Reduced from 1800
            'monthly_fee': 399,
            'net_potential': 1500 - 399,  # $1101/mo
            'fee_structure': '$399/mo + 14% of profits above 5% hurdle',  # Reduced from 18%
            'performance_fee_note': '14% of profits above 5% annual return hurdle',
            'capital_profile': '50% Core · 30% Momentum · 20% Event / Earnings',
            'capital_requirement': 50000,
            'data_access': 'Continuous UW Pro + premium alert channel',
            'automation': 'Full automation + CODA oversight',
            'service_model': 'AUTOMATION + CODA OVERSIGHT',
            'service_description': 'Automation + CODA monitors your positions (you execute & manage)',
            'includes': [
                'Premium signals + full automation',
                'CODA monitors your positions (not managing)',
                'Risk alerts & recommendations from CODA',
                'You execute trades, CODA watches & advises',
                'Priority support + weekly reviews',
                'Auto-entry capability (when broker API ready)',
                'Premium WhatsApp alerts',
            ],
        },
        {
            'code': 'consultative',
            'name': 'Consultative 1800',
            'status': 'Premium',  # Changed from 'Grandfathered'
            'monthly_target': 1800,  # Increased from 420
            'monthly_fee': 420,
            'net_potential': 1800 - 420,  # $1380/mo
            'fee_structure': '$420/mo + 10% of profits above 8% hurdle',
            'performance_fee_note': '10% of profits above 8% annual return hurdle',
            'capital_profile': '50% Core · 30% Momentum · 20% Event / Earnings',
            'capital_requirement': 75000,  # Increased from 25000
            'data_access': 'Continuous UW Pro + premium alert channel',
            'automation': 'Full automation + full management',
            'service_model': 'FULL AUTOMATION + FULL MANAGEMENT',  # Key differentiator
            'service_description': 'CODA sets, executes & manages everything - completely hands-off',
            'includes': [
                'CODA sets all positions (fully automated)',
                'CODA executes positions (when broker API ready)',
                'CODA manages all positions (full lifecycle)',
                'CODA monitors risk 24/7 (full risk management)',
                'Completely hands-off for client',
                'Dedicated account manager',
                'Premium WhatsApp alerts',
                'Weekly performance reports',
                'No coaching sessions - pure managed trading',
                '10% performance fee only on profits above 8% hurdle',
            ],
        },
    ]

    client_tiers = {acc.fee_tier for acc in accounts}
    tier_lookup = {tier['code']: tier for tier in tier_matrix}
    primary_tier_code = accounts[0].fee_tier if accounts else 'starter'
    
    # Determine upgrade path (progressive upgrade)
    upgrade_pitch = None
    target_code = None
    tier_order = ['starter', 'balanced', 'elite', 'consultative']
    if primary_tier_code in tier_order:
        current_index = tier_order.index(primary_tier_code)
        if current_index < len(tier_order) - 1:
            target_code = tier_order[current_index + 1]

    if target_code:
        upgrade_pitch = {
            'current': tier_lookup.get(primary_tier_code),
            'target': tier_lookup.get(target_code),
            'auto_metrics': auto_metrics,
        }
    
    # Client analytics (Phase 4) - performance metrics for their accounts
    client_analytics = None
    if accounts:
        try:
            from datetime import timedelta
            cutoff_date = timezone.now() - timedelta(days=90)
            
            # Get closed positions for all client accounts
            closed_positions = OptionsPosition.objects.filter(
                managed_account__in=accounts,
                status='closed',
                entry_date__gte=cutoff_date.date(),
            ).select_related('outcome_history', 'source_suggestion')
            
            total_closed = closed_positions.count()
            winning_positions = closed_positions.filter(
                outcome_history__was_profitable=True
            ).count() if total_closed > 0 else 0
            
            win_rate = (winning_positions / total_closed * 100) if total_closed > 0 else None
            
            # Calculate avg P&L
            from django.db.models import Avg
            avg_result = closed_positions.aggregate(
                avg_pnl=Avg('outcome_history__actual_return_amount')
            )
            avg_pnl = avg_result.get('avg_pnl')
            
            # Position count by tier
            tier_breakdown = {}
            for pos in closed_positions:
                if hasattr(pos, 'source_suggestion') and pos.source_suggestion:
                    tier = pos.source_suggestion.signal_tier or 'unknown'
                    tier_breakdown[tier] = tier_breakdown.get(tier, 0) + 1
            
            client_analytics = {
                'total_closed_positions': total_closed,
                'winning_positions': winning_positions,
                'losing_positions': total_closed - winning_positions,
                'win_rate': win_rate,
                'avg_pnl': avg_pnl,
                'tier_breakdown': tier_breakdown,
            }
        except Exception as e:
            logger.error(f"Error calculating client analytics: {e}", exc_info=True)
            client_analytics = None

    context = {
        'accounts': accounts,
        'total_invested': total_invested,
        'total_current_value': total_current_value,
        'total_pnl': total_pnl,
        'total_open_positions': total_open_positions,
        'has_accounts': bool(accounts),
        'title': 'My Managed Accounts',
        'auto_metrics': auto_metrics,
        'tier_matrix': tier_matrix,
        'client_tiers': client_tiers,
        'upgrade_pitch': upgrade_pitch,
        'portfolio_presets_public': portfolio_presets_public,
        'client_analytics': client_analytics,
    }
    
    return render(request, 'investing/managed/client_portal.html', context)


@login_required
def client_account_detail(request, account_id):
    """
    Client view of their specific managed account
    
    Read-only view with performance charts and position details
    Permissions: Client (owner) only
    """
    account = get_object_or_404(
        ManagedTradingAccount.objects.select_related('account_manager'),
        id=account_id
    )
    
    # Permission check - must be the account owner
    if account.client != request.user:
        messages.error(request, 'You do not have permission to view this account')
        return redirect('investing:client_portal')
    
    # Get account summary
    service = ManagedTradingService()
    summary = service.get_account_summary(account)
    
    # Get open and recent closed positions
    open_positions = summary['positions']['open_positions']
    recent_closed = summary['positions']['recent_closed']
    
    # Get recent activity (filtered for client-relevant items)
    recent_activity = [
        activity for activity in summary['activity']['recent']
        if activity.activity_type in [
            'position_opened',
            'position_closed',
            'session_completed'
        ]
    ][:5]
    
    # Check if consultative tier
    if account.fee_tier == 'consultative':
        recent_sessions = account.sessions.all()[:5]
        sessions_this_month = account.sessions_completed_this_month
        sessions_remaining = account.sessions_per_month - sessions_this_month
    else:
        recent_sessions = []
        sessions_this_month = 0
        sessions_remaining = 0
    
    income_summary = summary['income_summary']
    whales_timeline = summary['whales_timeline']

    base_capital = income_summary.get('base_capital') or Decimal('0')
    scenario_step = service.SCENARIO_STEP
    min_capital = base_capital - scenario_step
    if min_capital < Decimal('0'):
        min_capital = Decimal('0')
    max_capital = base_capital * service.SCENARIO_MAX_MULTIPLIER
    if max_capital <= base_capital:
        max_capital = base_capital + scenario_step
    scenario_defaults = {
        'current_capital': float(base_capital),
        'min_capital': float(min_capital),
        'max_capital': float(max_capital),
        'step': float(scenario_step),
        'income_per_dollar': float(income_summary.get('income_per_dollar') or Decimal('0')),
        'target_income': float(income_summary.get('target') or Decimal('0')),
        'baseline_income': float(income_summary.get('baseline_income') or Decimal('0')),
        'baseline_coverage_pct': float(income_summary.get('baseline_coverage_pct') or Decimal('0')),
        'target_gap': float(income_summary.get('target_gap') or Decimal('0')),
    }
    scenario_defaults['slider_disabled'] = scenario_defaults['min_capital'] == scenario_defaults['max_capital']

    context = {
        'account': account,
        'summary': summary,
        'open_positions': open_positions,
        'recent_closed': recent_closed,
        'recent_activity': recent_activity,
        'recent_sessions': recent_sessions,
        'sessions_this_month': sessions_this_month,
        'sessions_remaining': sessions_remaining,
        'is_consultative': account.fee_tier == 'consultative',
        'income_summary': income_summary,
        'whales_timeline': whales_timeline,
        'scenario_defaults': scenario_defaults,
        'title': f'My Account - {account.account_number}'
    }
    
    return render(request, 'investing/managed/client_account_detail.html', context)


@login_required
@require_POST
def request_portfolio_review(request):
    """
    Consultative clients can request a portfolio review from their account manager.
    Creates a lightweight activity log entry for staff to see.
    """
    account_id = request.POST.get('account_id')
    if not account_id:
        return JsonResponse({'error': 'Missing account_id'}, status=400)
    
    account = get_object_or_404(
        ManagedTradingAccount.objects.select_related('account_manager'),
        id=account_id,
        client=request.user
    )
    
    # Only allow consultative tier clients
    if account.fee_tier != 'consultative':
        return JsonResponse({'error': 'This feature is only available for Consultative tier clients'}, status=403)
    
    # Get client's primary account for context
    preset_code = request.POST.get('preset_code', 'unknown')
    
    # Create activity log entry
    activity = TradingActivity.objects.create(
        managed_account=account,
        activity_type='client_review_requested',
        description=f"Client requested portfolio review for {preset_code} preset. Client would like staff to evaluate preset ideas and discuss potential positions.",
        data_snapshot={
            'preset_code': preset_code,
            'requested_by': request.user.get_full_name() or request.user.username,
            'requested_at': timezone.now().isoformat(),
        },
        performed_by=request.user,
        timestamp=timezone.now()
    )
    
    account_manager_name = account.account_manager.get_full_name() if account.account_manager else 'TBD'
    
    return JsonResponse({
        'success': True,
        'message': f'Review request submitted successfully. Your account manager ({account_manager_name}) will review your request and contact you soon.',
        'activity_id': activity.id,
        'account_manager': account_manager_name
    })

