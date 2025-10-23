"""
Monitoring & Alerts Views

Views for monitoring positions, generating alerts, and risk management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q
from datetime import date, timedelta

from ...models import ManagedTradingAccount, OptionsPosition, RiskAlert
from ...services import OptionsMonitoringService


@staff_member_required
def monitor_dashboard(request):
    """
    Main monitoring dashboard for all accounts
    
    Shows:
    - Accounts with critical alerts
    - Positions requiring action
    - Risk exposure summary
    - Upcoming expirations
    
    Permissions: Staff only
    """
    service = OptionsMonitoringService()
    
    # Monitor all accounts
    alerts_summary = service.monitor_all_accounts()
    
    # Get accounts with open positions
    active_accounts = ManagedTradingAccount.objects.filter(
        status='active'
    ).select_related('client', 'account_manager').prefetch_related('positions')
    
    # Get positions expiring soon
    expiring_soon = OptionsPosition.objects.filter(
        status='open',
        expiration_date__lte=date.today() + timedelta(days=7),
        expiration_date__gte=date.today()
    ).select_related('managed_account').order_by('expiration_date')
    
    # Get accounts by risk level
    high_risk_accounts = [
        acc for acc in active_accounts 
        if acc.current_risk_exposure > acc.max_total_risk * Decimal('0.8')
    ]
    
    context = {
        'alerts_summary': alerts_summary,
        'active_accounts': active_accounts,
        'expiring_soon': expiring_soon,
        'high_risk_accounts': high_risk_accounts,
        'critical_count': len(alerts_summary.get('critical', [])),
        'high_count': len(alerts_summary.get('high', [])),
        'title': 'Monitoring Dashboard'
    }
    
    return render(request, 'investing/managed/monitor_dashboard.html', context)


@staff_member_required
def account_alerts(request, account_id):
    """
    View alerts for specific account
    
    Shows all current alerts with recommendations
    Permissions: Staff only
    """
    account = get_object_or_404(
        ManagedTradingAccount.objects.select_related('client'),
        id=account_id
    )
    
    service = OptionsMonitoringService()
    
    # Get all alerts for this account
    alerts = service.monitor_account(account)
    
    # Categorize alerts by severity
    critical_alerts = [a for a in alerts if a['severity'] == 'critical']
    high_alerts = [a for a in alerts if a['severity'] == 'high']
    medium_alerts = [a for a in alerts if a['severity'] == 'medium']
    
    # Get positions requiring action
    positions_requiring_action = service.get_positions_requiring_action(account)
    
    context = {
        'account': account,
        'alerts': alerts,
        'critical_alerts': critical_alerts,
        'high_alerts': high_alerts,
        'medium_alerts': medium_alerts,
        'positions_requiring_action': positions_requiring_action,
        'has_critical': len(critical_alerts) > 0,
        'title': f'Alerts - {account.account_number}'
    }
    
    return render(request, 'investing/managed/account_alerts.html', context)

