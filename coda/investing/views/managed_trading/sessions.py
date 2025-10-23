"""
Session Management Views

Views for managing coaching sessions (consultative tier accounts).
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from datetime import datetime

from ...models import ManagedTradingAccount, TradingSession, TradingActivity
from ...forms import TradingSessionForm


@staff_member_required
def create_session(request, account_id):
    """
    Record trading session for consultative tier account
    
    Permissions: Staff only
    """
    account = get_object_or_404(ManagedTradingAccount, id=account_id)
    
    # Verify account is on consultative tier
    if account.fee_tier != 'consultative':
        messages.warning(
            request,
            f'Account {account.account_number} is on {account.get_fee_tier_display()} tier, not consultative'
        )
        return redirect('investing:managed_account_detail', account_id=account.id)
    
    if request.method == 'POST':
        form = TradingSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.managed_account = account
            session.save()
            form.save_m2m()  # Save many-to-many relationships (positions_reviewed)
            
            # Update account session counters
            account.sessions_completed_this_month += 1
            account.total_sessions_completed += 1
            account.save(update_fields=[
                'sessions_completed_this_month',
                'total_sessions_completed',
                'updated_at'
            ])
            
            # Log activity
            TradingActivity.objects.create(
                managed_account=account,
                activity_type='session_completed',
                description=f'{session.get_session_type_display()} session completed - {session.session_duration_minutes} minutes',
                performed_by=request.user,
                data_snapshot={
                    'session_type': session.session_type,
                    'duration': session.session_duration_minutes,
                    'fee_charged': str(session.fee_charged),
                    'topics': session.topics_discussed[:200]
                }
            )
            
            messages.success(
                request,
                f'✓ Session recorded - Fee: ${session.fee_charged}'
            )
            return redirect('investing:managed_account_detail', account_id=account.id)
    else:
        # Pre-fill with account and defaults
        initial = {
            'managed_account': account,
            'session_date': datetime.now(),
            'fee_charged': account.session_fee
        }
        form = TradingSessionForm(initial=initial)
    
    context = {
        'form': form,
        'account': account,
        'sessions_this_month': account.sessions_completed_this_month,
        'sessions_remaining': account.sessions_per_month - account.sessions_completed_this_month,
        'title': 'Record Session'
    }
    
    return render(request, 'investing/managed/create_session.html', context)


@login_required
def sessions_list(request, account_id):
    """
    List all sessions for an account
    
    Permissions: Staff, account manager, or client (owner)
    """
    account = get_object_or_404(ManagedTradingAccount, id=account_id)
    
    # Permission check
    if not (request.user.is_staff or 
            account.account_manager == request.user or 
            account.client == request.user):
        messages.error(request, 'You do not have permission to view these sessions')
        return redirect('investing:home')
    
    # Get all sessions for this account
    sessions = account.sessions.all().prefetch_related('positions_reviewed')
    
    # Calculate billing summary
    total_sessions = sessions.count()
    total_fees = sum([s.fee_charged for s in sessions])
    billed_sessions = sessions.filter(is_billed=True).count()
    unbilled_sessions = total_sessions - billed_sessions
    unbilled_fees = sum([s.fee_charged for s in sessions.filter(is_billed=False)])
    
    context = {
        'account': account,
        'sessions': sessions,
        'total_sessions': total_sessions,
        'total_fees': total_fees,
        'billed_sessions': billed_sessions,
        'unbilled_sessions': unbilled_sessions,
        'unbilled_fees': unbilled_fees,
        'is_manager': request.user.is_staff or account.account_manager == request.user,
        'title': f'Sessions - {account.account_number}'
    }
    
    return render(request, 'investing/managed/sessions_list.html', context)

