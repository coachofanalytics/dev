"""
Position Management Views

Views for creating, closing, and managing options positions.
"""

import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
import json

from ...models import ManagedTradingAccount, OptionsPosition
from ...forms import OptionsPositionForm, ClosePositionForm, QuickPositionEntryForm
from ...forms_enhanced import MultiLegOptionsForm, OptionPlayIntegrationForm
from ...services import ManagedTradingService, OptionsMonitoringService, BrokerAPIService
from ...models import TradingActivity


logger = logging.getLogger(__name__)


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
        form_type = request.POST.get('form_type', 'multi_leg')
        print(f"DEBUG: POST request received, form_type: {form_type}")
        print(f"DEBUG: POST data keys: {list(request.POST.keys())}")
        
        if form_type == 'quick':
            form = QuickPositionEntryForm(request.POST)
        elif form_type == 'multi_leg':
            form = MultiLegOptionsForm(request.POST)
        else:
            form = OptionsPositionForm(request.POST)
        
        if form.is_valid():
            print(f"DEBUG: Form is valid, processing {form_type} form...")
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
                elif form_type == 'multi_leg':
                    # Build position data from multi-leg form
                    account = form.cleaned_data['managed_account']
                    
                    # Build legs array
                    legs = []
                    leg1 = {
                        'type': form.cleaned_data['leg1_type'],
                        'strike': float(form.cleaned_data['leg1_strike']),
                        'contracts': form.cleaned_data['leg1_contracts'],
                        'premium': float(form.cleaned_data['leg1_premium']),
                        'delta': float(form.cleaned_data.get('delta', 0)),
                        'theta': float(form.cleaned_data.get('theta', 0)),
                    }
                    legs.append(leg1)
                    
                    # Add second leg if present
                    leg2_type = form.cleaned_data.get('leg2_type')
                    leg2_strike = form.cleaned_data.get('leg2_strike')
                    leg2_contracts = form.cleaned_data.get('leg2_contracts')
                    leg2_premium = form.cleaned_data.get('leg2_premium')
                    
                    if leg2_type and leg2_strike and leg2_contracts and leg2_premium:
                        leg2 = {
                            'type': leg2_type,
                            'strike': float(leg2_strike),
                            'contracts': int(leg2_contracts),
                            'premium': float(leg2_premium),
                            'delta': 0,  # Will be calculated
                            'theta': 0,  # Will be calculated
                        }
                        legs.append(leg2)
                    
                    # Calculate metrics
                    capital_required = Decimal(str(form.calculate_capital_required(form.cleaned_data)))
                    
                    # Calculate premium collected and paid with safety checks
                    premium_collected = Decimal('0.00')
                    premium_paid = Decimal('0.00')
                    for leg in legs:
                        premium = Decimal(str(leg.get('premium', 0)))
                        contracts = Decimal(str(leg.get('contracts', 0)))
                        if 'short' in leg['type']:
                            premium_collected += premium * contracts * 100
                        elif 'long' in leg['type']:
                            premium_paid += premium * contracts * 100
                    
                    net_credit = premium_collected - premium_paid
                    
                    position_data = {
                        'symbol': form.cleaned_data['symbol'],
                        'strategy': form.cleaned_data['strategy'],
                        'positions': legs,
                        'capital_required': capital_required,
                        'premium_collected': net_credit,
                        'max_profit': net_credit,
                        'max_loss': capital_required - net_credit,
                        'position_delta': form.cleaned_data.get('delta', Decimal('0.0000')),
                        'position_theta': form.cleaned_data.get('theta', Decimal('0.0000')),
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
                print(f"DEBUG: About to create position with data: {position_data}")
                print(f"DEBUG: Account: {account.account_number}, Available: ${account.available_buying_power}")
                
                position = service.create_position(account, position_data)
                
                print(f"DEBUG: Position created successfully: {position.id}")
                
                messages.success(
                    request,
                    f'✓ Position created: {position.symbol} {position.get_strategy_display()} - Premium: ${position.premium_collected:,.2f}'
                )
                return redirect('investing:managed_account_detail', account_id=account.id)
                
            except Exception as e:
                print(f"DEBUG: Exception during position creation: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'Error creating position: {str(e)}')
        else:
            print(f"DEBUG: Form is NOT valid. Errors: {form.errors}")
            print(f"DEBUG: Non-field errors: {form.non_field_errors()}")
            for field, errors in form.errors.items():
                print(f"DEBUG: {field}: {errors}")
    else:
        # Initialize form with account if provided
        initial = {'managed_account': account} if account else {}
        form = MultiLegOptionsForm(initial=initial)
    
    context = {
        'form': form,
        'account': account,
        'title': 'Create Position',
        'form_type': 'multi_leg'
    }
    
    return render(request, 'investing/managed/create_position_enhanced.html', context)


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
@require_POST
def mark_position_entered(request, position_id):
    """
    Confirm that a pending auto-approved position has been executed by the trading desk.
    """
    position = get_object_or_404(
        OptionsPosition.objects.select_related('managed_account'),
        id=position_id
    )

    service = ManagedTradingService()
    try:
        service.confirm_auto_approved_entry(position, request.user)
        messages.success(
            request,
            f'✅ {position.symbol} marked as entered. Capital reserved and position is now live.'
        )
    except ValidationError as exc:
        messages.error(request, str(exc))
    except Exception as exc:
        logger.exception("Failed to confirm position entry: %s", exc)
        messages.error(request, f'Unexpected error: {exc}')

    return redirect('investing:managed_position_detail', position_id=position.id)


@staff_member_required
def edit_position(request, position_id):
    """
    Edit existing options position
    
    Allows modifying position details before or after entry
    Permissions: Staff only
    """
    position = get_object_or_404(
        OptionsPosition.objects.select_related('managed_account'),
        id=position_id
    )
    
    if position.status == 'closed':
        messages.warning(request, 'Cannot edit closed positions')
        return redirect('investing:managed_position_detail', position_id=position.id)
    
    if request.method == 'POST':
        form = OptionsPositionForm(request.POST, instance=position)
        if form.is_valid():
            try:
                updated_position = form.save()
                messages.success(request, f'✓ Position updated: {updated_position.symbol}')
                return redirect('investing:managed_account_detail', account_id=position.managed_account.id)
            except Exception as e:
                messages.error(request, f'Error updating position: {str(e)}')
    else:
        form = OptionsPositionForm(instance=position)
    
    context = {
        'form': form,
        'position': position,
        'account': position.managed_account,
        'title': f'Edit Position - {position.symbol}'
    }
    
    return render(request, 'investing/managed/edit_position.html', context)


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
    
    # Get related activity (including P&L adjustments)
    activity = position.activities.all().order_by('-created_at')[:20]
    
    context = {
        'position': position,
        'account': account,
        'evaluation': evaluation,
        'activity': activity,
        'is_manager': request.user.is_staff or account.account_manager == request.user,
        'title': f'{position.symbol} Position Detail'
    }
    
    return render(request, 'investing/managed/position_detail.html', context)


@staff_member_required
def sync_broker_positions(request, account_id):
    """
    Trigger a broker sync for the specified managed trading account.
    """
    account = get_object_or_404(
        ManagedTradingAccount.objects.select_related('broker_connection', 'client'),
        id=account_id
    )

    service = BrokerAPIService()
    try:
        result = service.sync_positions(account, performed_by=request.user)
        messages.success(
            request,
            (
                f"Broker sync completed for {account.account_number}. "
                f"{result['created']} created, {result['updated']} updated, {result['skipped']} skipped."
            )
        )
    except ValidationError as exc:
        messages.error(request, str(exc))
    except NotImplementedError as exc:
        messages.warning(request, str(exc))
    except Exception as exc:  # pragma: no cover - unexpected broker failure
        logger.exception("Broker sync failed for account %s", account.account_number)
        messages.error(request, f"Unexpected error during broker sync: {exc}")

    return redirect('investing:managed_account_detail', account_id=account.id)


@staff_member_required
@require_POST
def adjust_position_pnl(request, position_id):
    """
    Manually adjust position P&L (Staff only)
    
    Used for:
    - Early exits at different prices
    - Manual corrections
    - Adjusted positions
    
    Logs all changes with reason for audit trail
    """
    from ...models import TradingActivity
    from decimal import Decimal
    
    position = get_object_or_404(OptionsPosition, id=position_id)
    account = position.managed_account
    
    try:
        # Get adjustment data
        adjustment_type = request.POST.get('adjustment_type')  # 'premium' or 'exit'
        new_value = Decimal(request.POST.get('new_value', '0'))
        reason = request.POST.get('reason', '').strip()
        
        if not reason:
            messages.error(request, 'Reason for adjustment is required')
            return redirect('investing:managed_position_detail', position_id=position_id)
        
        # Calculate old P&L
        old_pnl = position.unrealized_pnl if position.status == 'open' else position.realized_pnl
        
        # Apply adjustment
        if adjustment_type == 'premium':
            old_premium = position.premium_collected
            position.premium_collected = new_value
            field_changed = 'Premium Collected'
            old_val = old_premium
        elif adjustment_type == 'exit':
            old_exit = position.exit_premium or Decimal('0')
            position.exit_premium = new_value
            field_changed = 'Exit Premium'
            old_val = old_exit
        else:
            messages.error(request, 'Invalid adjustment type')
            return redirect('investing:managed_position_detail', position_id=position_id)
        
        position.save()
        
        # Calculate new P&L
        new_pnl = position.unrealized_pnl if position.status == 'open' else position.realized_pnl
        
        # Log the adjustment
        TradingActivity.objects.create(
            managed_account=account,
            position=position,
            activity_type='pnl_adjusted',
            description=(
                f"P&L manually adjusted by {request.user.get_full_name()}. "
                f"{field_changed}: ${old_val:,.2f} → ${new_value:,.2f}. "
                f"P&L changed: ${old_pnl:,.2f} → ${new_pnl:,.2f}. "
                f"Reason: {reason}"
            ),
            performed_by=request.user,
            data_snapshot={
                'field_changed': field_changed,
                'old_value': str(old_val),
                'new_value': str(new_value),
                'old_pnl': str(old_pnl),
                'new_pnl': str(new_pnl),
                'reason': reason,
                'position_status': position.status
            }
        )
        
        messages.success(
            request,
            f"✅ P&L adjusted successfully. {field_changed} updated from ${old_val:,.2f} to ${new_value:,.2f}. "
            f"New P&L: ${new_pnl:,.2f}"
        )
        
    except Exception as e:
        messages.error(request, f'Error adjusting P&L: {str(e)}')
    
    return redirect('investing:managed_position_detail', position_id=position_id)

