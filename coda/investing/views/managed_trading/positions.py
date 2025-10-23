"""
Position Management Views

Views for creating, closing, and managing options positions.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from decimal import Decimal
from datetime import date
import json

from ...models import ManagedTradingAccount, OptionsPosition
from ...forms import OptionsPositionForm, ClosePositionForm, QuickPositionEntryForm
from ...services import ManagedTradingService, OptionsMonitoringService


@staff_member_required
def create_position(request, account_id=None):
    """
    Create new options position
    
    Supports both full form and quick entry form
    Permissions: Staff only
    """
    account = None
    if account_id:
        account = get_object_or_404(ManagedTradingAccount, id=account_id)
        
        # Check if account is active
        if account.status != 'active':
            messages.warning(request, f'Account {account.account_number} is not active')
            return redirect('investing:managed_account_detail', account_id=account.id)
    
    if request.method == 'POST':
        # Determine which form was submitted
        form_type = request.POST.get('form_type', 'quick')
        
        if form_type == 'quick':
            form = QuickPositionEntryForm(request.POST)
        else:
            form = OptionsPositionForm(request.POST)
        
        if form.is_valid():
            service = ManagedTradingService()
            try:
                if form_type == 'quick':
                    # Build position data from quick form
                    account = form.cleaned_data['account']
                    
                    position_data = {
                        'symbol': form.cleaned_data['symbol'],
                        'strategy': form.cleaned_data['strategy'],
                        'positions': [{
                            'type': form.cleaned_data['strategy'],
                            'strike': float(form.cleaned_data['strike_price']),
                            'contracts': form.cleaned_data['contracts'],
                            'premium': float(form.cleaned_data['premium']),
                            'delta': float(form.cleaned_data.get('delta', 0)),
                        }],
                        'capital_required': form.cleaned_data['capital_required'],
                        'premium_collected': form.cleaned_data['premium'],
                        'max_profit': form.cleaned_data['premium'],
                        'max_loss': form.cleaned_data['capital_required'] - form.cleaned_data['premium'],
                        'position_delta': form.cleaned_data.get('delta', Decimal('0.0000')),
                        'position_theta': Decimal('0.0000'),
                        'expiration_date': form.cleaned_data['expiration_date'],
                        'notes': form.cleaned_data.get('notes', '')
                    }
                else:
                    # Use full form data
                    account = form.cleaned_data['managed_account']
                    position_data = {
                        'symbol': form.cleaned_data['symbol'],
                        'strategy': form.cleaned_data['strategy'],
                        'positions': json.loads(form.cleaned_data['positions']) if isinstance(form.cleaned_data['positions'], str) else form.cleaned_data['positions'],
                        'capital_required': form.cleaned_data['capital_required'],
                        'premium_collected': form.cleaned_data['premium_collected'],
                        'max_profit': form.cleaned_data['max_profit'],
                        'max_loss': form.cleaned_data['max_loss'],
                        'position_delta': form.cleaned_data['position_delta'],
                        'position_theta': form.cleaned_data['position_theta'],
                        'position_gamma': form.cleaned_data['position_gamma'],
                        'position_vega': form.cleaned_data['position_vega'],
                        'expiration_date': form.cleaned_data['expiration_date'],
                        'notes': form.cleaned_data.get('notes', '')
                    }
                
                # Create position using service
                position = service.create_position(account, position_data)
                
                messages.success(
                    request,
                    f'✓ Position created: {position.symbol} {position.get_strategy_display()} - Premium: ${position.premium_collected:,.2f}'
                )
                return redirect('investing:managed_account_detail', account_id=account.id)
                
            except Exception as e:
                messages.error(request, f'Error creating position: {str(e)}')
    else:
        # Initialize form with account if provided
        initial = {'account': account} if account else {}
        form = QuickPositionEntryForm(initial=initial)
    
    context = {
        'form': form,
        'account': account,
        'title': 'Create Position',
        'form_type': 'quick'
    }
    
    return render(request, 'investing/managed/create_position.html', context)


@staff_member_required
def close_position(request, position_id):
    """
    Close options position
    
    Calculates final P&L and updates account balance
    Permissions: Staff only
    """
    position = get_object_or_404(
        OptionsPosition.objects.select_related('managed_account'),
        id=position_id
    )
    
    if position.status != 'open':
        messages.warning(request, f'Position is already {position.status}')
        return redirect('investing:position_detail', position_id=position.id)
    
    if request.method == 'POST':
        form = ClosePositionForm(request.POST)
        if form.is_valid():
            service = ManagedTradingService()
            try:
                exit_data = {
                    'exit_price': form.cleaned_data['exit_price'],
                    'exit_reason': form.cleaned_data['exit_reason'],
                    'notes': form.cleaned_data.get('notes', '')
                }
                
                # Close position using service
                updated_position = service.close_position(position, exit_data)
                
                pnl_class = 'success' if updated_position.realized_pnl > 0 else 'danger'
                messages.success(
                    request,
                    f'✓ Position closed: {updated_position.symbol} - P&L: ${updated_position.realized_pnl:,.2f}',
                    extra_tags=pnl_class
                )
                return redirect('investing:managed_account_detail', account_id=position.managed_account.id)
                
            except Exception as e:
                messages.error(request, f'Error closing position: {str(e)}')
    else:
        # Suggest exit price (current value or 0 if not set)
        suggested_exit = position.current_value if position.current_value > 0 else position.premium_collected * Decimal('0.50')
        form = ClosePositionForm(initial={'exit_price': suggested_exit})
    
    context = {
        'form': form,
        'position': position,
        'account': position.managed_account,
        'title': f'Close Position - {position.symbol}'
    }
    
    return render(request, 'investing/managed/close_position.html', context)


@staff_member_required
def positions_list(request):
    """
    List all positions across all accounts
    
    Can filter by account, status, or show positions requiring action
    Permissions: Staff only
    """
    # Get filter parameters
    account_id = request.GET.get('account')
    status_filter = request.GET.get('status', 'open')
    show_alerts = request.GET.get('alerts', 'false') == 'true'
    
    # Base queryset
    positions = OptionsPosition.objects.select_related(
        'managed_account__client'
    ).order_by('-entry_date')
    
    # Apply filters
    if account_id:
        positions = positions.filter(managed_account_id=account_id)
    
    if status_filter and status_filter != 'all':
        positions = positions.filter(status=status_filter)
    
    # Get positions requiring action if requested
    positions_with_alerts = []
    if show_alerts:
        service = OptionsMonitoringService()
        for account in ManagedTradingAccount.objects.filter(status='active'):
            action_items = service.get_positions_requiring_action(account)
            positions_with_alerts.extend(action_items)
        
        # Extract position IDs
        alert_position_ids = [item['position'].id for item in positions_with_alerts]
        positions = positions.filter(id__in=alert_position_ids)
    
    # Get account list for filter dropdown
    accounts = ManagedTradingAccount.objects.filter(
        status__in=['active', 'paused']
    ).select_related('client')
    
    context = {
        'positions': positions[:100],  # Limit to 100 for performance
        'accounts': accounts,
        'current_account': account_id,
        'current_status': status_filter,
        'show_alerts': show_alerts,
        'positions_with_alerts': positions_with_alerts if show_alerts else [],
        'title': 'Positions' + (' - Action Required' if show_alerts else '')
    }
    
    return render(request, 'investing/managed/positions_list.html', context)


@login_required
def position_detail(request, position_id):
    """
    View detailed position information
    
    Permissions: Staff, account manager, or client (owner)
    """
    position = get_object_or_404(
        OptionsPosition.objects.select_related('managed_account__client', 'managed_account__account_manager'),
        id=position_id
    )
    
    account = position.managed_account
    
    # Permission check
    if not (request.user.is_staff or 
            account.account_manager == request.user or 
            account.client == request.user):
        messages.error(request, 'You do not have permission to view this position')
        return redirect('investing:home')
    
    # Get exit recommendation
    service = OptionsMonitoringService()
    evaluation = service.evaluate_exit_criteria(position)
    
    # Get related activity
    activity = position.activities.all()[:10]
    
    context = {
        'position': position,
        'account': account,
        'evaluation': evaluation,
        'activity': activity,
        'is_manager': request.user.is_staff or account.account_manager == request.user,
        'title': f'{position.symbol} Position Detail'
    }
    
    return render(request, 'investing/managed/position_detail.html', context)

