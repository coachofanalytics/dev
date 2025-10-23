"""
Managed Trading Account Views

Views for managing client trading accounts including creation,
detail views, and account management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from decimal import Decimal

from ...models import ManagedTradingAccount, OptionsPosition
from ...forms import ManagedAccountForm
from ...services import ManagedTradingService


@staff_member_required
def managed_accounts_list(request):
    """
    List all managed trading accounts with summary statistics
    
    Permissions: Staff only
    """
    accounts = ManagedTradingAccount.objects.filter(
        status__in=['active', 'paused']
    ).select_related('client', 'account_manager').annotate(
        open_positions_count=Count('positions', filter=Q(positions__status='open'))
    ).order_by('-created_at')
    
    # Calculate aggregated statistics
    total_aum = accounts.aggregate(
        total=Sum('current_balance')
    )['total'] or Decimal('0.00')
    
    total_pnl = accounts.aggregate(
        total=Sum('total_profit_loss')
    )['total'] or Decimal('0.00')
    
    total_positions = OptionsPosition.objects.filter(
        managed_account__in=accounts,
        status='open'
    ).count()
    
    # Accounts by fee tier
    tier_breakdown = {}
    for tier, tier_name in ManagedTradingAccount.FEE_TIER_CHOICES:
        count = accounts.filter(fee_tier=tier).count()
        if count > 0:
            tier_breakdown[tier_name] = count
    
    context = {
        'accounts': accounts,
        'total_aum': total_aum,
        'total_pnl': total_pnl,
        'total_positions': total_positions,
        'tier_breakdown': tier_breakdown,
        'title': 'Managed Trading Accounts'
    }
    
    return render(request, 'investing/managed/accounts_list.html', context)


@staff_member_required
def create_managed_account(request):
    """
    Create new managed trading account
    
    Permissions: Staff only
    """
    if request.method == 'POST':
        form = ManagedAccountForm(request.POST)
        if form.is_valid():
            service = ManagedTradingService()
            try:
                # Prepare account data from form
                account_data = {
                    'account_name': form.cleaned_data['account_name'],
                    'initial_capital': form.cleaned_data['initial_capital'],
                    'account_manager': form.cleaned_data.get('account_manager') or request.user,
                    'fee_tier': form.cleaned_data['fee_tier'],
                    'management_fee_percentage': form.cleaned_data['management_fee_percentage'],
                    'performance_fee_percentage': form.cleaned_data['performance_fee_percentage'],
                    'performance_threshold': form.cleaned_data['performance_threshold'],
                }
                
                # Create account using service
                account = service.create_managed_account(
                    client_user=form.cleaned_data['client'],
                    account_data=account_data
                )
                
                messages.success(
                    request,
                    f'✓ Account {account.account_number} created successfully for {account.client.get_full_name()}'
                )
                return redirect('investing:managed_account_detail', account_id=account.id)
                
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
    else:
        # Pre-fill account manager with current user
        form = ManagedAccountForm(initial={'account_manager': request.user})
    
    context = {
        'form': form,
        'title': 'Create Managed Account'
    }
    
    return render(request, 'investing/managed/create_account.html', context)


@login_required
def managed_account_detail(request, account_id):
    """
    View detailed account information including positions, performance, and alerts
    
    Permissions: 
    - Staff members (full access)
    - Account manager (full access)
    - Client (read-only access to their own account)
    """
    account = get_object_or_404(
        ManagedTradingAccount.objects.select_related('client', 'account_manager'),
        id=account_id
    )
    
    # Permission check
    is_staff = request.user.is_staff
    is_manager = account.account_manager == request.user
    is_client = account.client == request.user
    
    if not (is_staff or is_manager or is_client):
        messages.error(request, 'You do not have permission to view this account')
        return redirect('investing:home')
    
    # Get comprehensive account summary using service
    service = ManagedTradingService()
    summary = service.get_account_summary(account)
    
    # Get positions with recent activity
    open_positions = summary['positions']['open_positions']
    recent_closed = summary['positions']['recent_closed']
    upcoming_expirations = summary['positions']['upcoming_expirations']
    
    # Get recent activity
    recent_activity = summary['activity']['recent']
    
    # Calculate additional metrics
    has_alerts = any(
        pos.days_to_expiration <= 5 
        for pos in open_positions 
        if pos.status == 'open'
    )
    
    context = {
        'account': account,
        'summary': summary,
        'open_positions': open_positions,
        'recent_closed': recent_closed,
        'upcoming_expirations': upcoming_expirations,
        'recent_activity': recent_activity,
        'has_alerts': has_alerts,
        'is_manager': is_manager or is_staff,
        'is_client': is_client,
        'is_consultative': account.fee_tier == 'consultative',
        'title': f'Account {account.account_number}'
    }
    
    return render(request, 'investing/managed/account_detail.html', context)

