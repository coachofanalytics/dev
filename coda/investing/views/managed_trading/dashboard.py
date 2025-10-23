"""
Staff Dashboard for Managed Options Trading

Central hub for staff/managers to access all managed trading functions.
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q, Avg
from decimal import Decimal
from datetime import date, timedelta

from ...models import ManagedTradingAccount, OptionsPosition, TradingActivity, TradingSession


@staff_member_required
def staff_dashboard(request):
    """
    Main dashboard for staff/managers
    
    Shows overview of all managed accounts, positions, and recent activities.
    Provides quick access to create accounts, positions, and manage trades.
    
    Permissions: Staff only
    """
    # Get all active accounts
    active_accounts = ManagedTradingAccount.objects.filter(
        status='active'
    ).select_related('client', 'account_manager')
    
    # Calculate key metrics
    total_accounts = active_accounts.count()
    total_aum = active_accounts.aggregate(total=Sum('current_balance'))['total'] or Decimal('0.00')
    total_pnl = active_accounts.aggregate(total=Sum('total_profit_loss'))['total'] or Decimal('0.00')
    
    # Position statistics
    open_positions = OptionsPosition.objects.filter(status='open')
    total_open_positions = open_positions.count()
    
    positions_by_status = OptionsPosition.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Recent activities (last 10)
    recent_activities = TradingActivity.objects.select_related(
        'managed_account', 'options_position'
    ).order_by('-created_at')[:10]
    
    # Accounts by tier
    tier_breakdown = {}
    for tier, tier_name in ManagedTradingAccount.FEE_TIER_CHOICES:
        count = active_accounts.filter(fee_tier=tier).count()
        if count > 0:
            tier_breakdown[tier_name] = count
    
    # Top performing accounts
    top_performers = active_accounts.order_by('-total_profit_loss')[:5]
    
    # Accounts needing attention (losing money)
    accounts_at_risk = active_accounts.filter(
        total_profit_loss__lt=0
    ).order_by('total_profit_loss')[:5]
    
    # Recent sessions (last 7 days)
    week_ago = date.today() - timedelta(days=7)
    recent_sessions = TradingSession.objects.filter(
        session_date__gte=week_ago
    ).select_related('managed_account', 'conducted_by').order_by('-session_date')[:5]
    
    # Expiring positions (next 7 days)
    next_week = date.today() + timedelta(days=7)
    expiring_soon = OptionsPosition.objects.filter(
        status='open',
        expiration_date__lte=next_week,
        expiration_date__gte=date.today()
    ).select_related('managed_account').order_by('expiration_date')[:10]
    
    # Calculate average ROI
    accounts_with_trades = active_accounts.filter(total_trades__gt=0)
    if accounts_with_trades.exists():
        avg_roi = sum([acc.return_on_investment for acc in accounts_with_trades]) / accounts_with_trades.count()
    else:
        avg_roi = Decimal('0.00')
    
    # Win rate across all accounts
    total_trades = active_accounts.aggregate(total=Sum('total_trades'))['total'] or 0
    winning_trades = active_accounts.aggregate(total=Sum('winning_trades'))['total'] or 0
    overall_win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    context = {
        # Summary metrics
        'total_accounts': total_accounts,
        'total_aum': total_aum,
        'total_pnl': total_pnl,
        'total_open_positions': total_open_positions,
        'avg_roi': avg_roi,
        'overall_win_rate': overall_win_rate,
        
        # Breakdowns
        'tier_breakdown': tier_breakdown,
        'positions_by_status': positions_by_status,
        
        # Lists
        'top_performers': top_performers,
        'accounts_at_risk': accounts_at_risk,
        'recent_activities': recent_activities,
        'recent_sessions': recent_sessions,
        'expiring_soon': expiring_soon,
        
        # Quick actions available
        'can_create_account': True,
        'can_create_position': True,
        'can_view_monitoring': True,
    }
    
    return render(request, 'investing/managed/staff_dashboard.html', context)

