"""
Client Portal Views

Read-only views for clients to monitor their managed trading accounts.
"""

from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from datetime import date, timedelta

from ...models import ManagedTradingAccount, OptionsPosition
from ...services import ManagedTradingService


@login_required
def client_portal(request):
    """
    Client portal - view all their managed accounts
    
    Permissions: Authenticated users viewing their own accounts
    """
    # Get all managed accounts for this client
    accounts = ManagedTradingAccount.objects.filter(
        client=request.user
    ).select_related('account_manager').annotate(
        open_positions_count=Count('positions', filter=Q(positions__status='open'))
    ).order_by('-created_at')
    
    # Calculate totals across all accounts
    total_invested = sum([acc.initial_capital for acc in accounts])
    total_current_value = sum([acc.current_balance for acc in accounts])
    total_pnl = sum([acc.total_profit_loss for acc in accounts])
    
    # Get overall stats
    total_open_positions = sum([
        acc.positions.filter(status='open').count() 
        for acc in accounts
    ])
    
    context = {
        'accounts': accounts,
        'total_invested': total_invested,
        'total_current_value': total_current_value,
        'total_pnl': total_pnl,
        'total_open_positions': total_open_positions,
        'has_accounts': accounts.count() > 0,
        'title': 'My Managed Accounts'
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
    scenario_defaults = {
        'current_capital': float(base_capital),
        'min_capital': float(base_capital),
        'max_capital': float(base_capital * service.SCENARIO_MAX_MULTIPLIER) if base_capital > 0 else float(service.SCENARIO_STEP),
        'step': float(service.SCENARIO_STEP),
        'income_per_dollar': float(income_summary.get('income_per_dollar') or Decimal('0')),
        'target_income': float(income_summary.get('target') or Decimal('0')),
    }

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

