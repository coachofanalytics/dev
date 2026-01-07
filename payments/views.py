from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum
from django.db import transaction as db_transaction
from decimal import Decimal
from django_ratelimit.decorators import ratelimit

from .models import Wallet, Transaction, SubscriptionPlan, UserSubscription, Invoice
from .forms import DepositForm, MPesaDepositForm, StripePaymentMethodForm
from .services import PaymentGatewayFactory


def get_client_ip(request):
    """Extract client IP address from request for activity logging."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def get_user_agent(request):
    """Extract user agent from request for activity logging."""
    return request.META.get('HTTP_USER_AGENT', '')[:500]


@login_required
def wallet_dashboard(request):
    from .services import CurrencyConversionService
    from django.utils import timezone

    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user, balance=Decimal("0.00"))

    recent_transactions = Transaction.objects.filter(
        wallet=wallet
    ).order_by("-created_at")

    total_deposited = Transaction.objects.filter(
        wallet=wallet,
        transaction_type="deposit",
        status="completed"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    total_spent = Transaction.objects.filter(
        wallet=wallet,
        transaction_type="purchase",
        status="completed"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # Get user's preferred currency view (default: USD)
    selected_currency = request.session.get('currency_view', 'USD')

    # Fetch current exchange rates
    usd_to_kes_rate = CurrencyConversionService.get_exchange_rate('USD', 'KES') or Decimal('150.00')
    kes_to_usd_rate = CurrencyConversionService.get_exchange_rate('KES', 'USD') or Decimal('0.0067')

    # Calculate balances in both currencies
    if wallet.currency == 'USD':
        balance_in_usd = wallet.balance
        balance_in_kes = (wallet.balance * usd_to_kes_rate).quantize(Decimal('0.01'))
    else:  # wallet.currency == 'KES'
        balance_in_kes = wallet.balance
        balance_in_usd = (wallet.balance * kes_to_usd_rate).quantize(Decimal('0.01'))

    # Convert totals to selected currency
    if wallet.currency == 'USD':
        if selected_currency == 'KES':
            total_deposited_display = (total_deposited * usd_to_kes_rate).quantize(Decimal('0.01'))
            total_spent_display = (total_spent * usd_to_kes_rate).quantize(Decimal('0.01'))
        else:
            total_deposited_display = total_deposited
            total_spent_display = total_spent
    else:  # wallet.currency == 'KES'
        if selected_currency == 'USD':
            total_deposited_display = (total_deposited * kes_to_usd_rate).quantize(Decimal('0.01'))
            total_spent_display = (total_spent * kes_to_usd_rate).quantize(Decimal('0.01'))
        else:
            total_deposited_display = total_deposited
            total_spent_display = total_spent

    context = {
        "wallet": wallet,
        "recent_transactions": recent_transactions,
        "total_deposited": total_deposited_display,
        "total_spent": total_spent_display,
        "selected_currency": selected_currency,
        "balance_in_usd": balance_in_usd,
        "balance_in_kes": balance_in_kes,
        "usd_to_kes_rate": usd_to_kes_rate,
        "kes_to_usd_rate": kes_to_usd_rate,
        "rate_updated_at": timezone.now(),
    }

    return render(request, "payments/wallet_dashboard.html", context)



@login_required
@require_http_methods(["POST"])
def toggle_currency_view(request):
    """Toggle user's currency view preference (USD/KES)"""
    import json
    from .services import CurrencyConversionService
    
    try:
        # Parse JSON body
        data = json.loads(request.body)
        currency = data.get('currency', 'USD')
    except (json.JSONDecodeError, KeyError):
        # Fallback to POST data
        currency = request.POST.get('currency', 'USD')
    
    if currency not in ['USD', 'KES']:
        return JsonResponse({'success': False, 'error': 'Invalid currency'}, status=400)
    
    # Update session
    request.session['currency_view'] = currency
    
    # Get user's wallet
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user, balance=Decimal("0.00"))
    
    # Get totals
    total_deposited = Transaction.objects.filter(
        wallet=wallet,
        transaction_type="deposit",
        status="completed"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    total_spent = Transaction.objects.filter(
        wallet=wallet,
        transaction_type="purchase",
        status="completed"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    
    # Fetch current exchange rates
    usd_to_kes_rate = CurrencyConversionService.get_exchange_rate('USD', 'KES') or Decimal('150.00')
    kes_to_usd_rate = CurrencyConversionService.get_exchange_rate('KES', 'USD') or Decimal('0.0067')
    
    # Calculate balances in both currencies
    if wallet.currency == 'USD':
        balance_in_usd = wallet.balance
        balance_in_kes = (wallet.balance * usd_to_kes_rate).quantize(Decimal('0.01'))
    else:  # wallet.currency == 'KES'
        balance_in_kes = wallet.balance
        balance_in_usd = (wallet.balance * kes_to_usd_rate).quantize(Decimal('0.01'))
    
    # Convert totals to selected currency
    if wallet.currency == 'USD':
        if currency == 'KES':
            total_deposited_display = (total_deposited * usd_to_kes_rate).quantize(Decimal('0.01'))
            total_spent_display = (total_spent * usd_to_kes_rate).quantize(Decimal('0.01'))
        else:
            total_deposited_display = total_deposited
            total_spent_display = total_spent
    else:  # wallet.currency == 'KES'
        if currency == 'USD':
            total_deposited_display = (total_deposited * kes_to_usd_rate).quantize(Decimal('0.01'))
            total_spent_display = (total_spent * kes_to_usd_rate).quantize(Decimal('0.01'))
        else:
            total_deposited_display = total_deposited
            total_spent_display = total_spent
    
    return JsonResponse({
        'success': True,
        'currency': currency,
        'selected_currency': currency,
        'message': f'Currency view changed to {currency}',
        'balance_in_usd': str(balance_in_usd),
        'balance_in_kes': str(balance_in_kes),
        'total_deposited': str(total_deposited_display),
        'total_spent': str(total_spent_display),
        'usd_to_kes_rate': str(usd_to_kes_rate),
        'kes_to_usd_rate': str(kes_to_usd_rate),
    })

@login_required
def transaction_history(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user, balance=Decimal('0.00'))

    transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')

    transaction_type = request.GET.get('type')
    if transaction_type in ['deposit', 'purchase', 'refund']:
        transactions = transactions.filter(transaction_type=transaction_type)

    status = request.GET.get('status')
    if status in ['pending', 'completed', 'failed']:
        transactions = transactions.filter(status=status)

    gateway = request.GET.get('gateway')
    if gateway:
        transactions = transactions.filter(payment_gateway=gateway)

    context = {
        'transactions': transactions,
        'wallet': wallet,
        'selected_type': transaction_type,
        'selected_status': status,
        'selected_gateway': gateway,
    }

    return render(request, 'payments/transaction_history.html', context)


@login_required
def export_transactions(request):
    """Export transactions to CSV file."""
    import csv
    from django.http import HttpResponse

    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        messages.error(request, 'Wallet not found.')
        return redirect('payments:transaction_history')

    transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')

    # Apply filters from query parameters
    transaction_type = request.GET.get('type')
    if transaction_type in ['deposit', 'purchase', 'refund']:
        transactions = transactions.filter(transaction_type=transaction_type)

    status = request.GET.get('status')
    if status in ['pending', 'completed', 'failed']:
        transactions = transactions.filter(status=status)

    gateway = request.GET.get('gateway')
    if gateway:
        transactions = transactions.filter(payment_gateway=gateway)

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['Transaction ID', 'Date', 'Type', 'Amount', 'Currency', 'Gateway', 'Status', 'Reference'])

    for txn in transactions:
        writer.writerow([
            txn.transaction_id,
            txn.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            txn.transaction_type,
            str(txn.amount),
            txn.currency,
            txn.payment_gateway,
            txn.status,
            txn.gateway_transaction_id or ''
        ])

    # Log the export
    from .services import WalletSecurityService
    WalletSecurityService.log_activity(
        user=request.user,
        action_type='settings_change',
        description=f'Exported {transactions.count()} transactions to CSV',
        wallet=wallet,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        metadata={'count': transactions.count(), 'filters': {'type': transaction_type, 'status': status, 'gateway': gateway}}
    )

    return response


@login_required
def deposit_initiate(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user, balance=Decimal('0.00'))

    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            deposit_amount = form.cleaned_data['amount']
            payment_method = form.cleaned_data['payment_method']

            request.session['deposit_amount'] = str(deposit_amount)
            request.session['deposit_gateway'] = payment_method

            if payment_method == 'stripe':
                return redirect('payments:deposit_stripe')
            elif payment_method == 'paypal':
                return redirect('payments:deposit_paypal')
            elif payment_method == 'mpesa':
                return redirect('payments:deposit_mpesa')
            else:
                messages.error(request, 'Invalid payment method selected.')
                return redirect('payments:deposit_initiate')
    else:
        form = DepositForm()

    context = {
        'form': form,
        'wallet': wallet,
    }

    return render(request, 'payments/deposit_initiate.html', context)


@login_required
@ratelimit(key='user', rate='20/h', method='POST')
def deposit_stripe(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user, balance=Decimal('0.00'))

    deposit_amount = request.session.get('deposit_amount')

    if not deposit_amount:
        messages.error(request, 'Deposit amount not found in session.')
        return redirect('payments:deposit_initiate')

    if request.method == 'POST':
        form = StripePaymentMethodForm(request.POST)
        if form.is_valid():
            try:
                deposit_amount_decimal = Decimal(deposit_amount)
                payment_gateway = PaymentGatewayFactory.create_gateway('stripe')

                transaction = Transaction.objects.create(
                    user=request.user,
                    wallet=wallet,
                    amount=deposit_amount_decimal,
                    transaction_type='deposit',
                    payment_gateway='stripe',
                    status='pending',
                    gateway_transaction_id=None,
                )

                # Log deposit initiation
                from .services import WalletSecurityService
                WalletSecurityService.log_activity(
                    user=request.user,
                    action_type='deposit',
                    description=f'Stripe deposit initiated: {settings.DEFAULT_CURRENCY} {deposit_amount_decimal}',
                    wallet=wallet,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    metadata={'gateway': 'stripe', 'amount': str(deposit_amount_decimal), 'transaction_id': transaction.id}
                )

                payment_result = payment_gateway.process_payment(
                    amount=deposit_amount_decimal,
                    currency=settings.DEFAULT_CURRENCY,
                    token=form.cleaned_data['payment_method_id'],
                    description=f'Wallet deposit - User {request.user.id}',
                    metadata={
                        'user_id': request.user.id,
                        'transaction_id': transaction.id,
                        'wallet_id': wallet.id,
                    }
                )
                
                # Add subscription info to transaction metadata if present in session
                if 'subscription_plan_id' in request.session:
                    transaction.metadata['subscription_plan_id'] = request.session['subscription_plan_id']
                if 'subscription_renewal_id' in request.session:
                    transaction.metadata['subscription_renewal_id'] = request.session['subscription_renewal_id']
                transaction.save()

                if payment_result['success']:
                    # Use atomic transaction with row locking for balance update
                    with db_transaction.atomic():
                        # Lock wallet row to prevent race conditions
                        locked_wallet = Wallet.objects.select_for_update().get(id=wallet.id)
                        transaction.status = 'completed'
                        transaction.gateway_transaction_id = payment_result.get('transaction_id')
                        transaction.save()
                        locked_wallet.balance += deposit_amount_decimal
                        locked_wallet.save()

                    # Log successful deposit
                    WalletSecurityService.log_activity(
                        user=request.user,
                        action_type='deposit',
                        description=f'Stripe deposit completed: {settings.DEFAULT_CURRENCY} {deposit_amount_decimal}',
                        wallet=locked_wallet,
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        metadata={'gateway': 'stripe', 'amount': str(deposit_amount_decimal), 'status': 'completed'}
                    )

                    # Check if this was for a subscription
                    is_subscription = 'subscription_plan_id' in request.session or 'subscription_renewal_id' in request.session

                    if 'deposit_amount' in request.session:
                        del request.session['deposit_amount']
                    if 'deposit_gateway' in request.session:
                        del request.session['deposit_gateway']

                    if is_subscription:
                        messages.success(request, 'Payment successful! Activating your subscription...')
                        return redirect('payments:subscription_payment_complete')
                    else:
                        messages.success(request, f'Deposit of {settings.DEFAULT_CURRENCY} {deposit_amount_decimal} successful!')
                        return redirect('payments:wallet_dashboard')
                else:
                    transaction.status = 'failed'
                    transaction.save()

                    # Log failed deposit
                    WalletSecurityService.log_activity(
                        user=request.user,
                        action_type='failed_attempt',
                        description=f'Stripe deposit failed: {settings.DEFAULT_CURRENCY} {deposit_amount_decimal}',
                        wallet=wallet,
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        metadata={'gateway': 'stripe', 'amount': str(deposit_amount_decimal), 'error': payment_result.get('error_message', 'Unknown error')},
                        is_suspicious=False
                    )

                    messages.error(request, payment_result.get('error_message', 'Payment processing failed. Please try again.'))
                    return redirect('payments:deposit_stripe')

            except Exception as e:
                # Log exception
                WalletSecurityService.log_activity(
                    user=request.user,
                    action_type='failed_attempt',
                    description=f'Stripe deposit error: {str(e)}',
                    wallet=wallet,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    metadata={'gateway': 'stripe', 'error': str(e)},
                    is_suspicious=True
                )
                messages.error(request, f'An error occurred: {str(e)}')
                return redirect('payments:deposit_stripe')
    else:
        form = StripePaymentMethodForm()

    context = {
        'form': form,
        'amount': deposit_amount,
        'wallet': wallet,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }

    return render(request, 'payments/deposit_stripe.html', context)


@login_required
@ratelimit(key='user', rate='20/h', method='POST')
def deposit_paypal(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user, balance=Decimal('0.00'))

    deposit_amount = request.session.get('deposit_amount')

    if not deposit_amount:
        messages.error(request, 'Deposit amount not found in session.')
        return redirect('payments:deposit_initiate')

    try:
        deposit_amount_decimal = Decimal(deposit_amount)
        payment_gateway = PaymentGatewayFactory.create_gateway('paypal')

        transaction = Transaction.objects.create(
            user=request.user,
            wallet=wallet,
            amount=deposit_amount_decimal,
            transaction_type='deposit',
            payment_gateway='paypal',
            status='pending',
            gateway_transaction_id=None,
        )

        # Log PayPal deposit initiation
        from .services import WalletSecurityService
        WalletSecurityService.log_activity(
            user=request.user,
            action_type='deposit',
            description=f'PayPal deposit initiated: {settings.DEFAULT_CURRENCY} {deposit_amount_decimal}',
            wallet=wallet,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            metadata={'gateway': 'paypal', 'amount': str(deposit_amount_decimal), 'transaction_id': transaction.id}
        )

        request.session['paypal_transaction_id'] = transaction.id

        return_url = request.build_absolute_uri('payments:deposit_paypal_execute')
        cancel_url = request.build_absolute_uri('payments:deposit_paypal_cancel')

        payment_result = payment_gateway.process_payment(
            amount=deposit_amount_decimal,
            currency=settings.DEFAULT_CURRENCY,
            metadata={
                'description': f'Wallet deposit - User {request.user.id}',
                'return_url': return_url,
                'cancel_url': cancel_url,
                'user_id': request.user.id,
                'transaction_id': transaction.id,
                'wallet_id': wallet.id,
            }
        )

        if payment_result['success']:
            return redirect(payment_result['approval_url'])
        else:
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, payment_result.get('error_message', 'Failed to initiate PayPal payment.'))
            return redirect('payments:deposit_initiate')

    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('payments:deposit_initiate')


@login_required
def deposit_paypal_execute(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        messages.error(request, 'Wallet not found.')
        return redirect('payments:wallet_dashboard')

    paypal_payment_id = request.GET.get('paymentId')
    paypal_payer_id = request.GET.get('PayerID')
    transaction_id = request.session.get('paypal_transaction_id')

    if not paypal_payment_id or not paypal_payer_id or not transaction_id:
        messages.error(request, 'Invalid PayPal callback parameters.')
        return redirect('payments:wallet_dashboard')

    try:
        transaction = get_object_or_404(Transaction, id=transaction_id, wallet=wallet)
        payment_gateway = PaymentGatewayFactory.create_gateway('paypal')

        payment_result = payment_gateway.execute_payment(
            payment_id=paypal_payment_id,
            payer_id=paypal_payer_id,
        )

        if payment_result['success']:
            # Use atomic transaction with row locking for balance update
            with db_transaction.atomic():
                locked_wallet = Wallet.objects.select_for_update().get(id=wallet.id)
                transaction.status = 'completed'
                transaction.gateway_transaction_id = paypal_payment_id
                transaction.save()
                locked_wallet.balance += transaction.amount
                locked_wallet.save()

            # Log successful PayPal deposit
            from .services import WalletSecurityService
            WalletSecurityService.log_activity(
                user=request.user,
                action_type='deposit',
                description=f'PayPal deposit completed: {settings.DEFAULT_CURRENCY} {transaction.amount}',
                wallet=locked_wallet,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                metadata={'gateway': 'paypal', 'amount': str(transaction.amount), 'status': 'completed'}
            )

            # Check if this was for a subscription
            is_subscription = 'subscription_plan_id' in request.session or 'subscription_renewal_id' in request.session

            if 'paypal_transaction_id' in request.session:
                del request.session['paypal_transaction_id']
            if 'deposit_amount' in request.session:
                del request.session['deposit_amount']
            if 'deposit_gateway' in request.session:
                del request.session['deposit_gateway']

            if is_subscription:
                messages.success(request, 'Payment successful! Activating your subscription...')
                return redirect('payments:subscription_payment_complete')
            else:
                messages.success(request, f'Deposit of {settings.DEFAULT_CURRENCY} {transaction.amount} successful!')
                return redirect('payments:wallet_dashboard')
        else:
            transaction.status = 'failed'
            transaction.save()

            # Log failed PayPal deposit
            from .services import WalletSecurityService
            WalletSecurityService.log_activity(
                user=request.user,
                action_type='failed_attempt',
                description=f'PayPal deposit failed: {settings.DEFAULT_CURRENCY} {transaction.amount}',
                wallet=wallet,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                metadata={'gateway': 'paypal', 'amount': str(transaction.amount), 'error': payment_result.get('error_message', 'Unknown error')}
            )

            messages.error(request, payment_result.get('error_message', 'Payment execution failed.'))
            return redirect('payments:deposit_initiate')

    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('payments:wallet_dashboard')


@login_required
def deposit_paypal_cancel(request):
    transaction_id = request.session.get('paypal_transaction_id')

    if transaction_id:
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            transaction.status = 'failed'
            transaction.save()
        except Transaction.DoesNotExist:
            pass

        if 'paypal_transaction_id' in request.session:
            del request.session['paypal_transaction_id']

    if 'deposit_amount' in request.session:
        del request.session['deposit_amount']
    if 'deposit_gateway' in request.session:
        del request.session['deposit_gateway']

    messages.warning(request, 'PayPal payment was cancelled.')
    return redirect('payments:deposit_initiate')


@login_required
@ratelimit(key='user', rate='20/h', method='POST')
def deposit_mpesa(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user, balance=Decimal('0.00'))

    deposit_amount = request.session.get('deposit_amount')

    if not deposit_amount:
        messages.error(request, 'Deposit amount not found in session.')
        return redirect('payments:deposit_initiate')

    if request.method == 'POST':
        form = MPesaDepositForm(request.POST)
        if form.is_valid():
            try:
                deposit_amount_decimal = Decimal(deposit_amount)
                phone_number = form.cleaned_data['phone_number']

                payment_gateway = PaymentGatewayFactory.create_gateway('mpesa')

                transaction = Transaction.objects.create(
                    user=request.user,
                    wallet=wallet,
                    amount=deposit_amount_decimal,
                    transaction_type='deposit',
                    payment_gateway='mpesa',
                    status='pending',
                    gateway_transaction_id=phone_number,
                )

                # Log M-Pesa deposit initiation
                from .services import WalletSecurityService
                WalletSecurityService.log_activity(
                    user=request.user,
                    action_type='deposit',
                    description=f'M-Pesa deposit initiated: {settings.DEFAULT_CURRENCY} {deposit_amount_decimal}',
                    wallet=wallet,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    metadata={'gateway': 'mpesa', 'amount': str(deposit_amount_decimal), 'phone': phone_number[-4:]}
                )

                request.session['mpesa_transaction_id'] = transaction.id
                request.session['mpesa_phone_number'] = phone_number

                stk_result = payment_gateway.process_payment(
                    amount=deposit_amount_decimal,
                    currency=settings.DEFAULT_CURRENCY,
                    metadata={
                        'phone_number': phone_number,
                        'reference': f'WALLET-{transaction.id}',
                        'description': f'Wallet deposit - User {request.user.id}',
                    }
                )

                if stk_result['success']:
                    messages.success(request, 'M-Pesa STK Push sent. Please complete the payment on your phone.')
                    return redirect('payments:deposit_mpesa_status')
                else:
                    transaction.status = 'failed'
                    transaction.save()
                    messages.error(request, stk_result.get('error_message', 'Failed to initiate M-Pesa payment.'))
                    return redirect('payments:deposit_mpesa')

            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
                return redirect('payments:deposit_mpesa')
    else:
        form = MPesaDepositForm()

    context = {
        'form': form,
        'amount': deposit_amount,
        'wallet': wallet,
    }

    return render(request, 'payments/deposit_mpesa.html', context)


@login_required
def deposit_mpesa_status(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        messages.error(request, 'Wallet not found.')
        return redirect('payments:wallet_dashboard')

    transaction_id = request.session.get('mpesa_transaction_id')
    phone_number = request.session.get('mpesa_phone_number')

    if not transaction_id:
        messages.error(request, 'M-Pesa transaction not found.')
        return redirect('payments:deposit_initiate')

    try:
        transaction = get_object_or_404(Transaction, id=transaction_id, wallet=wallet)
    except:
        messages.error(request, 'Transaction not found.')
        return redirect('payments:wallet_dashboard')

    context = {
        'transaction': transaction,
        'phone_number': phone_number,
        'wallet': wallet,
    }

    return render(request, 'payments/deposit_mpesa_status.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def check_mpesa_status(request):
    transaction_id = request.GET.get('transaction_id') or request.POST.get('transaction_id')

    if not transaction_id:
        return JsonResponse({
            'success': False,
            'error': 'Transaction ID not provided',
        }, status=400)

    try:
        transaction = Transaction.objects.get(
            id=transaction_id,
            wallet__user=request.user,
            payment_gateway='mpesa',
        )
    except Transaction.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Transaction not found',
        }, status=404)

    try:
        payment_gateway = PaymentGatewayFactory.create_gateway('mpesa')

        status_result = payment_gateway.check_payment_status(
            transaction_reference=transaction.gateway_transaction_id,
        )

        if status_result['success']:
            current_status = status_result.get('status')

            if current_status == 'completed' and transaction.status == 'pending':
                # Use atomic transaction with row locking for balance update
                with db_transaction.atomic():
                    locked_wallet = Wallet.objects.select_for_update().get(id=transaction.wallet.id)
                    transaction.status = 'completed'
                    transaction.save()
                    locked_wallet.balance += transaction.amount
                    locked_wallet.save()

                # Log successful M-Pesa deposit
                from .services import WalletSecurityService
                WalletSecurityService.log_activity(
                    user=request.user,
                    action_type='deposit',
                    description=f'M-Pesa deposit completed: {settings.DEFAULT_CURRENCY} {transaction.amount}',
                    wallet=locked_wallet,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    metadata={'gateway': 'mpesa', 'amount': str(transaction.amount), 'status': 'completed'}
                )

                if 'mpesa_transaction_id' in request.session:
                    del request.session['mpesa_transaction_id']
                if 'mpesa_phone_number' in request.session:
                    del request.session['mpesa_phone_number']
                if 'deposit_amount' in request.session:
                    del request.session['deposit_amount']
                if 'deposit_gateway' in request.session:
                    del request.session['deposit_gateway']

            return JsonResponse({
                'success': True,
                'status': transaction.status,
                'amount': str(transaction.amount),
                'currency': settings.DEFAULT_CURRENCY,
            })
        else:
            return JsonResponse({
                'success': False,
                'error': status_result.get('error_message', 'Failed to check payment status'),
            }, status=500)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}',
        }, status=500)


# ============================================================================
# SUBSCRIPTION VIEWS
# ============================================================================

@login_required
def subscription_plans(request):
    """List all available subscription plans"""
    # Filter plans by user's category (category-specific)
    user_category = request.user.profile.category if hasattr(request.user, 'profile') and request.user.profile.category else None
    
    if user_category:
        plans = SubscriptionPlan.objects.filter(is_active=True, category=user_category)
    else:
        plans = SubscriptionPlan.objects.filter(is_active=True)
    
    # Get user's current active subscriptions
    user_subscriptions = UserSubscription.objects.filter(
        user=request.user,
        status='active'
    ).values_list('plan_id', flat=True)
    
    # Check if user has any active subscription
    has_active_subscription = UserSubscription.objects.filter(
        user=request.user,
        status='active'
    ).exists()
    
    context = {
        'plans': plans,
        'user_subscriptions': list(user_subscriptions),
        'has_active_subscription': has_active_subscription,
    }
    
    return render(request, 'payments/subscription_plans.html', context)


@login_required
def subscription_detail(request, plan_id):
    """View details of a specific subscription plan"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Check if user already has an active subscription to any plan
    has_active_subscription = UserSubscription.objects.filter(
        user=request.user,
        status='active'
    ).exists()
    
    # Check if user has this specific plan
    has_this_subscription = UserSubscription.objects.filter(
        user=request.user,
        plan=plan,
        status='active'
    ).exists()
    
    context = {
        'plan': plan,
        'wallet': wallet,
        'has_active_subscription': has_active_subscription,
        'has_this_subscription': has_this_subscription,
    }
    
    return render(request, 'payments/subscription_detail.html', context)


@login_required
@login_required
def subscription_purchase(request, plan_id):
    """Purchase a subscription plan"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Check if user already has ANY active subscription (block new purchase)
    existing_subscription = UserSubscription.objects.filter(
        user=request.user,
        status='active'
    ).first()
    
    if existing_subscription:
        messages.warning(request, 'You already have an active subscription. Please cancel it before purchasing a new one.')
        return redirect('payments:my_subscriptions')
    
    if request.method == 'POST':
        from .forms import SubscriptionPaymentForm
        form = SubscriptionPaymentForm(request.POST, wallet_balance=wallet.balance, plan_price=plan.price)
        
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']

            # Handle wallet payment
            if payment_method == 'wallet':
                if wallet.balance >= plan.price:
                    # Check spending limits before processing
                    from .services import WalletSecurityService
                    is_allowed, limit_message = WalletSecurityService.check_spending_limits(wallet, plan.price)
                    if not is_allowed:
                        messages.error(request, f'Transaction blocked: {limit_message}')
                        return redirect('payments:subscription_purchase', plan_id=plan_id)

                    # Debit wallet
                    wallet.debit(plan.price)

                    # Create transaction
                    transaction = Transaction.objects.create(
                        user=request.user,
                        wallet=wallet,
                        transaction_type='subscription_payment',
                        amount=plan.price,
                        currency=settings.PAYMENT_CURRENCY,
                        payment_gateway='wallet',
                        status='completed',
                        metadata={'plan_id': plan.id, 'plan_name': plan.name}
                    )
                    
                    # Create and activate subscription
                    subscription = UserSubscription.objects.create(
                        user=request.user,
                        plan=plan,
                        payment_method='wallet',
                        status='pending'
                    )
                    subscription.activate()

                    # Log subscription purchase
                    WalletSecurityService.log_activity(
                        user=request.user,
                        action_type='payment',
                        description=f'Subscription purchased: {plan.name} for {settings.PAYMENT_CURRENCY} {plan.price}',
                        wallet=wallet,
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        metadata={'plan_id': plan.id, 'plan_name': plan.name, 'amount': str(plan.price)}
                    )

                    # Create invoice
                    Invoice.objects.create(
                        user=request.user,
                        subscription=subscription,
                        amount=plan.price,
                        currency=settings.PAYMENT_CURRENCY,
                        status='paid',
                        due_date=timezone.now(),
                        paid_date=timezone.now(),
                        description=f'Subscription to {plan.name}'
                    )

                    messages.success(request, f'Successfully subscribed to {plan.name}!')
                    return redirect('payments:my_subscriptions')
                else:
                    messages.error(request, 'Insufficient wallet balance. Please choose another payment method.')
                    return redirect('payments:subscription_purchase', plan_id=plan_id)
            
            # Handle other payment methods
            else:
                # Store subscription purchase info in session
                request.session['subscription_plan_id'] = plan_id
                request.session['subscription_payment_method'] = payment_method
                request.session['subscription_amount'] = str(plan.price)
                
                # Redirect to appropriate payment gateway
                if payment_method == 'stripe':
                    return redirect('payments:deposit_stripe')
                elif payment_method == 'paypal':
                    return redirect('payments:deposit_paypal')
                elif payment_method == 'mpesa':
                    return redirect('payments:deposit_mpesa')
    else:
        from .forms import SubscriptionPaymentForm
        form = SubscriptionPaymentForm(wallet_balance=wallet.balance, plan_price=plan.price)
    
    context = {
        'plan': plan,
        'wallet': wallet,
        'form': form,
    }
    
    return render(request, 'payments/subscription_purchase.html', context)


@login_required
def my_subscriptions(request):
    """View user's subscriptions"""
    active_subscriptions = UserSubscription.objects.filter(
        user=request.user,
        status='active'
    ).select_related('plan')
    
    expired_subscriptions = UserSubscription.objects.filter(
        user=request.user,
        status__in=['expired', 'cancelled']
    ).select_related('plan').order_by('-end_date')[:10]
    
    context = {
        'active_subscriptions': active_subscriptions,
        'expired_subscriptions': expired_subscriptions,
    }
    
    return render(request, 'payments/my_subscriptions.html', context)


@login_required
def subscription_cancel(request, subscription_id):
    """Cancel a subscription"""
    subscription = get_object_or_404(
        UserSubscription,
        id=subscription_id,
        user=request.user,
        status='active'
    )

    if request.method == 'POST':
        subscription.cancel()

        # Log subscription cancellation
        from .services import WalletSecurityService
        try:
            wallet = Wallet.objects.get(user=request.user)
            WalletSecurityService.log_activity(
                user=request.user,
                action_type='settings_change',
                description=f'Subscription cancelled: {subscription.plan.name}',
                wallet=wallet,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                metadata={'plan_id': subscription.plan.id, 'plan_name': subscription.plan.name, 'action': 'cancelled'}
            )
        except Wallet.DoesNotExist:
            pass

        messages.success(request, f'Successfully cancelled subscription to {subscription.plan.name}.')
        return redirect('payments:my_subscriptions')
    
    context = {
        'subscription': subscription,
    }
    
    return render(request, 'payments/subscription_cancel.html', context)




@login_required
def subscription_renew(request, subscription_id):
    """Renew an expired or expiring subscription"""
    subscription = get_object_or_404(
        UserSubscription,
        id=subscription_id,
        user=request.user
    )
    
    plan = subscription.plan
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Check if user has another active subscription
    other_active = UserSubscription.objects.filter(
        user=request.user,
        status='active'
    ).exclude(id=subscription_id).exists()
    
    if other_active:
        messages.warning(request, 'You already have an active subscription. Please cancel it before renewing.')
        return redirect('payments:my_subscriptions')
    
    if request.method == 'POST':
        from .forms import SubscriptionPaymentForm
        form = SubscriptionPaymentForm(request.POST, wallet_balance=wallet.balance, plan_price=plan.price)
        
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            
            # Handle wallet payment
            if payment_method == 'wallet':
                if wallet.balance >= plan.price:
                    # Debit wallet
                    wallet.debit(plan.price)
                    
                    # Create transaction
                    Transaction.objects.create(
                        user=request.user,
                        wallet=wallet,
                        transaction_type='subscription_payment',
                        amount=plan.price,
                        currency=settings.PAYMENT_CURRENCY,
                        payment_gateway='wallet',
                        status='completed',
                        metadata={'plan_id': plan.id, 'plan_name': plan.name, 'renewal': True}
                    )
                    
                    # Reactivate subscription
                    subscription.status = 'active'
                    subscription.activate()
                    
                    # Create invoice
                    Invoice.objects.create(
                        user=request.user,
                        subscription=subscription,
                        amount=plan.price,
                        currency=settings.PAYMENT_CURRENCY,
                        status='paid',
                        due_date=timezone.now(),
                        paid_date=timezone.now(),
                        description=f'Renewal of subscription to {plan.name}'
                    )
                    
                    messages.success(request, f'Successfully renewed subscription to {plan.name}!')
                    return redirect('payments:my_subscriptions')
                else:
                    messages.error(request, 'Insufficient wallet balance. Please choose another payment method.')
            
            # Handle other payment methods
            else:
                # Store renewal info in session
                request.session['subscription_renewal_id'] = subscription_id
                request.session['subscription_payment_method'] = payment_method
                request.session['subscription_amount'] = str(plan.price)
                
                # Redirect to appropriate payment gateway
                if payment_method == 'stripe':
                    return redirect('payments:deposit_stripe')
                elif payment_method == 'paypal':
                    return redirect('payments:deposit_paypal')
                elif payment_method == 'mpesa':
                    return redirect('payments:deposit_mpesa')
    else:
        from .forms import SubscriptionPaymentForm
        form = SubscriptionPaymentForm(wallet_balance=wallet.balance, plan_price=plan.price)
    
    context = {
        'subscription': subscription,
        'plan': plan,
        'wallet': wallet,
        'form': form,
        'is_renewal': True,
    }
    
    return render(request, 'payments/subscription_purchase.html', context)


@login_required
def subscription_payment_complete(request):
    """Complete subscription after successful gateway payment"""
    # Check if there's a subscription purchase in session
    plan_id = request.session.get('subscription_plan_id')
    renewal_id = request.session.get('subscription_renewal_id')
    payment_method = request.session.get('subscription_payment_method')
    
    if not (plan_id or renewal_id) or not payment_method:
        messages.error(request, 'Invalid subscription payment session.')
        return redirect('payments:subscription_plans')
    
    try:
        if renewal_id:
            # Handle renewal
            subscription = UserSubscription.objects.get(id=renewal_id, user=request.user)
            subscription.status = 'active'
            subscription.payment_method = payment_method
            subscription.activate()
            
            # Create invoice
            Invoice.objects.create(
                user=request.user,
                subscription=subscription,
                amount=subscription.plan.price,
                currency=settings.PAYMENT_CURRENCY,
                status='paid',
                due_date=timezone.now(),
                paid_date=timezone.now(),
                description=f'Renewal of subscription to {subscription.plan.name}'
            )
            
            messages.success(request, f'Successfully renewed subscription to {subscription.plan.name}!')
        else:
            # Handle new subscription
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            
            # Create and activate subscription
            subscription = UserSubscription.objects.create(
                user=request.user,
                plan=plan,
                payment_method=payment_method,
                status='pending'
            )
            subscription.activate()
            
            # Create invoice
            Invoice.objects.create(
                user=request.user,
                subscription=subscription,
                amount=plan.price,
                currency=settings.PAYMENT_CURRENCY,
                status='paid',
                due_date=timezone.now(),
                paid_date=timezone.now(),
                description=f'Subscription to {plan.name}'
            )
            
            messages.success(request, f'Successfully subscribed to {plan.name}!')
        
        # Clear session data
        request.session.pop('subscription_plan_id', None)
        request.session.pop('subscription_renewal_id', None)
        request.session.pop('subscription_payment_method', None)
        request.session.pop('subscription_amount', None)
        
        return redirect('payments:my_subscriptions')
        
    except (SubscriptionPlan.DoesNotExist, UserSubscription.DoesNotExist):
        messages.error(request, 'Subscription not found.')
        return redirect('payments:subscription_plans')
# ============================================================================
# CASHAPP DEPOSIT VIEWS
# ============================================================================

@login_required
@ratelimit(key='user', rate='20/h', method='POST')
def deposit_cashapp(request):
    """Handle CashApp (Square) deposit"""
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user, balance=Decimal('0.00'))

    deposit_amount = request.session.get('deposit_amount')

    if not deposit_amount:
        messages.error(request, 'Deposit amount not found in session.')
        return redirect('payments:deposit_initiate')

    if request.method == 'POST':
        source_id = request.POST.get('source_id')  # From Square Web Payment SDK

        if not source_id:
            messages.error(request, 'Payment information is required.')
            return redirect('payments:deposit_cashapp')

        try:
            deposit_amount_decimal = Decimal(deposit_amount)
            payment_gateway = PaymentGatewayFactory.create_gateway('cashapp')

            if not payment_gateway:
                messages.error(request, 'CashApp payment is currently unavailable.')
                return redirect('payments:deposit_initiate')

            # Create transaction record
            transaction = Transaction.objects.create(
                user=request.user,
                wallet=wallet,
                amount=deposit_amount_decimal,
                transaction_type='deposit',
                payment_gateway='cashapp',
                status='pending',
                gateway_transaction_id=None,
            )

            # Process payment
            payment_result = payment_gateway.process_payment(
                amount=deposit_amount_decimal,
                currency=settings.DEFAULT_CURRENCY,
                metadata={
                    'user_id': request.user.id,
                    'transaction_id': transaction.id,
                    'wallet_id': wallet.id,
                    'source_id': source_id,
                    'reference_id': f'DEPOSIT-{transaction.transaction_id}',
                    'description': f'Wallet deposit - User {request.user.id}',
                }
            )

            if payment_result['success']:
                transaction.status = 'completed'
                transaction.gateway_transaction_id = payment_result.get('transaction_id')
                transaction.metadata = payment_result.get('data', {})
                transaction.save()

                wallet.balance += deposit_amount_decimal
                wallet.save()

                if 'deposit_amount' in request.session:
                    del request.session['deposit_amount']
                if 'deposit_gateway' in request.session:
                    del request.session['deposit_gateway']

                messages.success(request, f'Deposit of {settings.DEFAULT_CURRENCY} {deposit_amount_decimal} successful via CashApp!')
                return redirect('payments:wallet_dashboard')
            else:
                transaction.status = 'failed'
                transaction.metadata = {'error': payment_result.get('message')}
                transaction.save()
                messages.error(request, payment_result.get('message', 'Payment processing failed. Please try again.'))
                return redirect('payments:deposit_cashapp')

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('payments:deposit_cashapp')

    context = {
        'amount': deposit_amount,
        'wallet': wallet,
        'cashapp_app_id': settings.CASHAPP_APP_ID,
        'cashapp_location_id': settings.CASHAPP_LOCATION_ID,
    }

    return render(request, 'payments/deposit_cashapp.html', context)


# ============================================================================
# VENMO DEPOSIT VIEWS
# ============================================================================

@login_required
@ratelimit(key='user', rate='20/h', method='POST')
def deposit_venmo(request):
    """Handle Venmo (Braintree) deposit"""
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user, balance=Decimal('0.00'))

    deposit_amount = request.session.get('deposit_amount')

    if not deposit_amount:
        messages.error(request, 'Deposit amount not found in session.')
        return redirect('payments:deposit_initiate')

    # Get Braintree client token for frontend
    payment_gateway = PaymentGatewayFactory.create_gateway('venmo')
    client_token = None

    if payment_gateway:
        token_result = payment_gateway.generate_client_token()
        if token_result['success']:
            client_token = token_result['client_token']

    if request.method == 'POST':
        payment_method_nonce = request.POST.get('payment_method_nonce')  # From Braintree Drop-in

        if not payment_method_nonce:
            messages.error(request, 'Payment information is required.')
            return redirect('payments:deposit_venmo')

        try:
            deposit_amount_decimal = Decimal(deposit_amount)

            if not payment_gateway:
                messages.error(request, 'Venmo payment is currently unavailable.')
                return redirect('payments:deposit_initiate')

            # Create transaction record
            transaction = Transaction.objects.create(
                user=request.user,
                wallet=wallet,
                amount=deposit_amount_decimal,
                transaction_type='deposit',
                payment_gateway='venmo',
                status='pending',
                gateway_transaction_id=None,
            )

            # Process payment
            payment_result = payment_gateway.process_payment(
                amount=deposit_amount_decimal,
                currency=settings.DEFAULT_CURRENCY,
                metadata={
                    'user_id': request.user.id,
                    'transaction_id': transaction.id,
                    'wallet_id': wallet.id,
                    'payment_method_nonce': payment_method_nonce,
                    'order_id': f'DEPOSIT-{transaction.transaction_id}',
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                }
            )

            if payment_result['success']:
                transaction.status = 'completed'
                transaction.gateway_transaction_id = payment_result.get('transaction_id')
                transaction.metadata = payment_result.get('data', {})
                transaction.save()

                wallet.balance += deposit_amount_decimal
                wallet.save()

                if 'deposit_amount' in request.session:
                    del request.session['deposit_amount']
                if 'deposit_gateway' in request.session:
                    del request.session['deposit_gateway']

                messages.success(request, f'Deposit of {settings.DEFAULT_CURRENCY} {deposit_amount_decimal} successful via Venmo!')
                return redirect('payments:wallet_dashboard')
            else:
                transaction.status = 'failed'
                transaction.metadata = {'error': payment_result.get('message')}
                transaction.save()
                messages.error(request, payment_result.get('message', 'Payment processing failed. Please try again.'))
                return redirect('payments:deposit_venmo')

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('payments:deposit_venmo')

    context = {
        'amount': deposit_amount,
        'wallet': wallet,
        'client_token': client_token,
    }

    return render(request, 'payments/deposit_venmo.html', context)


# =============================================================================
# USER ANALYTICS VIEWS
# =============================================================================

@login_required
def financial_insights(request):
    """
    Display financial insights and analytics for the user.
    Shows deposits, spending summaries, monthly breakdown, and trends.
    """
    from .services import FinancialAnalyticsService
    from .models import Wallet

    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user, balance=Decimal("0.00"))

    # Get time period from request (default 30 days)
    days = int(request.GET.get('days', 30))
    if days not in [7, 30, 90, 180, 365]:
        days = 30

    # Get financial summary
    summary = FinancialAnalyticsService.get_user_summary(request.user, days=days)

    # Get monthly breakdown (last 6 months)
    monthly_breakdown = FinancialAnalyticsService.get_monthly_breakdown(request.user, months=6)

    # Get transaction breakdown by type
    type_breakdown = FinancialAnalyticsService.get_transaction_breakdown_by_type(request.user, days=days)

    # Get payment method breakdown
    method_breakdown = FinancialAnalyticsService.get_payment_method_breakdown(request.user, days=days)

    context = {
        'wallet': wallet,
        'summary': summary,
        'monthly_breakdown': monthly_breakdown,
        'type_breakdown': type_breakdown,
        'method_breakdown': method_breakdown,
        'selected_days': days,
        'period_options': [
            {'value': 7, 'label': 'Last 7 days'},
            {'value': 30, 'label': 'Last 30 days'},
            {'value': 90, 'label': 'Last 3 months'},
            {'value': 180, 'label': 'Last 6 months'},
            {'value': 365, 'label': 'Last year'},
        ],
    }

    return render(request, 'payments/financial_insights.html', context)


@login_required
def activity_log(request):
    """
    Display wallet activity log for the user.
    Shows all actions taken on the wallet for security audit.
    """
    from .services import WalletSecurityService
    from .models import WalletActivityLog, Wallet

    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = None

    # Get filter parameters
    days = int(request.GET.get('days', 30))
    action_type = request.GET.get('type', None)

    if days not in [7, 30, 90, 180]:
        days = 30

    # Get activity logs
    activity_logs = WalletSecurityService.get_user_activity_log(
        user=request.user,
        days=days,
        action_type=action_type if action_type else None
    )

    # Get available action types for filter
    action_types = WalletActivityLog.ACTION_TYPES

    context = {
        'wallet': wallet,
        'activity_logs': activity_logs,
        'action_types': action_types,
        'selected_days': days,
        'selected_type': action_type,
        'period_options': [
            {'value': 7, 'label': 'Last 7 days'},
            {'value': 30, 'label': 'Last 30 days'},
            {'value': 90, 'label': 'Last 3 months'},
            {'value': 180, 'label': 'Last 6 months'},
        ],
    }

    return render(request, 'payments/activity_log.html', context)


@login_required
def spending_limits(request):
    """
    View and manage spending limits for the user's wallet.
    """
    from .services import WalletSecurityService
    from .models import Wallet, WalletSpendingLimit

    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user, balance=Decimal("0.00"))

    if request.method == 'POST':
        limit_type = request.POST.get('limit_type')
        amount = request.POST.get('amount')

        if limit_type and amount:
            try:
                amount_decimal = Decimal(amount)
                if amount_decimal > 0:
                    WalletSecurityService.set_spending_limit(
                        wallet=wallet,
                        limit_type=limit_type,
                        amount=amount_decimal,
                        set_by=request.user
                    )
                    messages.success(request, f'{limit_type.title()} spending limit set to ${amount_decimal}')
                else:
                    messages.error(request, 'Amount must be greater than 0')
            except (ValueError, TypeError):
                messages.error(request, 'Invalid amount specified')

        return redirect('payments:spending_limits')

    # Get current limits
    current_limits = WalletSpendingLimit.objects.filter(wallet=wallet, is_active=True)
    limits_dict = {limit.limit_type: limit for limit in current_limits}

    # Get default limits for display
    default_limits = {
        'daily': WalletSecurityService.DEFAULT_DAILY_LIMIT,
        'weekly': WalletSecurityService.DEFAULT_WEEKLY_LIMIT,
        'monthly': WalletSecurityService.DEFAULT_MONTHLY_LIMIT,
        'per_transaction': WalletSecurityService.DEFAULT_PER_TRANSACTION_LIMIT,
    }

    # Calculate current usage
    from django.utils import timezone
    from datetime import timedelta

    daily_spent = WalletSecurityService._get_spent_amount(wallet, days=1)
    weekly_spent = WalletSecurityService._get_spent_amount(wallet, days=7)
    monthly_spent = WalletSecurityService._get_spent_amount(wallet, days=30)

    context = {
        'wallet': wallet,
        'limits_dict': limits_dict,
        'default_limits': default_limits,
        'limit_types': WalletSpendingLimit.LIMIT_TYPES,
        'usage': {
            'daily': daily_spent,
            'weekly': weekly_spent,
            'monthly': monthly_spent,
        },
    }

    return render(request, 'payments/spending_limits.html', context)


@login_required
def user_disputes(request):
    """
    View user's payment disputes.
    """
    from .models import PaymentDispute

    disputes = PaymentDispute.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'disputes': disputes,
    }

    return render(request, 'payments/user_disputes.html', context)


@login_required
def create_dispute(request, transaction_id):
    """
    Create a new payment dispute with file upload support and notifications.
    """
    from .models import Transaction, PaymentDispute
    from .services.notification_service import PaymentNotificationService
    import os

    transaction = get_object_or_404(Transaction, transaction_id=transaction_id, user=request.user)

    # Check if dispute already exists
    if PaymentDispute.objects.filter(transaction=transaction).exists():
        messages.error(request, 'A dispute already exists for this transaction.')
        return redirect('payments:user_disputes')

    if request.method == 'POST':
        reason = request.POST.get('reason')
        description = request.POST.get('description')
        evidence_files = request.FILES.getlist('evidence_files')

        if reason and description:
            # Create the dispute
            dispute = PaymentDispute.objects.create(
                user=request.user,
                transaction=transaction,
                reason=reason,
                description=description,
                amount_disputed=transaction.amount,
            )

            # Handle file uploads
            if evidence_files:
                from django.core.files.storage import default_storage
                from django.conf import settings
                import uuid

                uploaded_paths = []
                for file in evidence_files:
                    # Generate unique filename
                    file_ext = os.path.splitext(file.name)[1]
                    unique_filename = f"dispute_{dispute.dispute_id}_{uuid.uuid4().hex[:8]}{file_ext}"
                    file_path = f"disputes/{dispute.dispute_id}/{unique_filename}"

                    # Save file
                    saved_path = default_storage.save(file_path, file)
                    uploaded_paths.append(saved_path)

                # Store file paths in dispute
                dispute.evidence_files = ','.join(uploaded_paths)
                dispute.save(update_fields=['evidence_files'])

            # Send notifications
            # 1. Notify user
            PaymentNotificationService.send_dispute_created_notification_to_user(
                user=request.user,
                dispute_id=dispute.dispute_id,
                transaction_id=transaction.transaction_id,
                amount=dispute.amount_disputed,
                priority=dispute.priority,
                sla_deadline=dispute.sla_deadline
            )

            # 2. Notify staff
            PaymentNotificationService.send_dispute_created_notification_to_staff(
                dispute_id=dispute.dispute_id,
                user_email=request.user.email,
                transaction_id=transaction.transaction_id,
                amount=dispute.amount_disputed,
                reason=dispute.get_reason_display(),
                priority=dispute.priority,
                sla_deadline=dispute.sla_deadline
            )

            messages.success(
                request,
                f'Dispute {dispute.dispute_id} created successfully. '
                f'Priority: {dispute.get_priority_display()}. '
                f'Expected resolution by {dispute.sla_deadline.strftime("%B %d, %Y")}.'
            )
            return redirect('payments:user_disputes')
        else:
            messages.error(request, 'Please provide a reason and description.')

    context = {
        'transaction': transaction,
        'reason_choices': PaymentDispute.REASON_CHOICES,
    }

    return render(request, 'payments/create_dispute.html', context)


# =============================================================================
# STAFF/ADMIN ANALYTICS VIEWS
# =============================================================================

@login_required
def staff_analytics_dashboard(request):
    """
    Staff analytics dashboard with comprehensive payment metrics.
    """
    if not hasattr(request.user, 'staff') or not request.user.staff.is_active:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('payments:wallet_dashboard')

    from .services import FinancialAnalyticsService

    # Get dashboard stats
    stats = FinancialAnalyticsService.get_admin_dashboard_stats()

    # Get subscription analytics
    subscription_stats = FinancialAnalyticsService.get_subscription_analytics()

    # Get revenue data for charts (last 30 days)
    revenue_data = FinancialAnalyticsService.get_revenue_by_period('daily', count=30)

    # Get monthly revenue for comparison
    monthly_revenue = FinancialAnalyticsService.get_revenue_by_period('monthly', count=12)

    context = {
        'stats': stats,
        'subscription_stats': subscription_stats,
        'revenue_data': revenue_data,
        'monthly_revenue': monthly_revenue,
    }

    return render(request, 'payments/staff/analytics_dashboard.html', context)


@login_required
def staff_fraud_alerts(request):
    """
    Staff view to manage fraud alerts.
    """
    if not hasattr(request.user, 'staff') or not request.user.staff.is_active:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('payments:wallet_dashboard')

    from .models import FraudAlert
    from .services import WalletSecurityService

    # Get filter parameters
    status_filter = request.GET.get('status', 'pending')
    alert_type_filter = request.GET.get('type', None)

    # Build query
    alerts = FraudAlert.objects.all().order_by('-created_at')

    if status_filter and status_filter != 'all':
        alerts = alerts.filter(status=status_filter)

    if alert_type_filter:
        alerts = alerts.filter(alert_type=alert_type_filter)

    # Get counts by status
    status_counts = {
        'pending': FraudAlert.objects.filter(status='pending').count(),
        'investigating': FraudAlert.objects.filter(status='investigating').count(),
        'resolved': FraudAlert.objects.filter(status='resolved').count(),
        'false_positive': FraudAlert.objects.filter(status='false_positive').count(),
        'confirmed_fraud': FraudAlert.objects.filter(status='confirmed_fraud').count(),
    }

    context = {
        'alerts': alerts[:100],  # Limit to 100 for performance
        'status_counts': status_counts,
        'selected_status': status_filter,
        'selected_type': alert_type_filter,
        'alert_types': FraudAlert.ALERT_TYPES,
        'status_choices': FraudAlert.STATUS_CHOICES,
    }

    return render(request, 'payments/staff/fraud_alerts.html', context)


@login_required
def staff_resolve_fraud_alert(request, alert_id):
    """
    Resolve a fraud alert.
    """
    if not hasattr(request.user, 'staff') or not request.user.staff.is_active:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('payments:wallet_dashboard')

    from .models import FraudAlert
    from .services import WalletSecurityService

    alert = get_object_or_404(FraudAlert, id=alert_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        resolution_notes = request.POST.get('resolution_notes', '')

        if new_status in dict(FraudAlert.STATUS_CHOICES):
            WalletSecurityService.resolve_fraud_alert(
                alert=alert,
                status=new_status,
                reviewed_by=request.user,
                resolution_notes=resolution_notes
            )
            messages.success(request, f'Fraud alert resolved as {new_status}.')
        else:
            messages.error(request, 'Invalid status selected.')

        return redirect('payments:staff_fraud_alerts')

    context = {
        'alert': alert,
        'status_choices': FraudAlert.STATUS_CHOICES,
    }

    return render(request, 'payments/staff/resolve_fraud_alert.html', context)


@login_required
def staff_disputes(request):
    """
    Staff view to manage payment disputes.
    """
    if not hasattr(request.user, 'staff') or not request.user.staff.is_active:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('payments:wallet_dashboard')

    from .models import PaymentDispute

    # Get filter parameters
    status_filter = request.GET.get('status', 'all')

    # Build query
    disputes = PaymentDispute.objects.all().order_by('-created_at')

    if status_filter and status_filter != 'all':
        disputes = disputes.filter(status=status_filter)

    # Get counts by status
    status_counts = {
        'open': PaymentDispute.objects.filter(status='open').count(),
        'under_review': PaymentDispute.objects.filter(status='under_review').count(),
        'resolved_favor_user': PaymentDispute.objects.filter(status='resolved_favor_user').count(),
        'resolved_favor_merchant': PaymentDispute.objects.filter(status='resolved_favor_merchant').count(),
        'closed': PaymentDispute.objects.filter(status='closed').count(),
    }

    context = {
        'disputes': disputes[:100],
        'status_counts': status_counts,
        'selected_status': status_filter,
        'status_choices': PaymentDispute.STATUS_CHOICES,
    }

    return render(request, 'payments/staff/disputes.html', context)


@login_required
def staff_resolve_dispute(request, dispute_id):
    """
    Resolve a payment dispute with status change notifications.
    """
    if not hasattr(request.user, 'staff') or not request.user.staff.is_active:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('payments:wallet_dashboard')

    from .models import PaymentDispute
    from .services.notification_service import PaymentNotificationService
    from django.utils import timezone

    dispute = get_object_or_404(PaymentDispute, id=dispute_id)

    if request.method == 'POST':
        old_status = dispute.status
        new_status = request.POST.get('status')
        resolution_notes = request.POST.get('resolution_notes', '')
        refund_amount = request.POST.get('refund_amount', '0')

        if new_status in dict(PaymentDispute.STATUS_CHOICES):
            dispute.status = new_status
            dispute.resolution_notes = resolution_notes
            dispute.resolved_at = timezone.now()

            try:
                dispute.amount_refunded = Decimal(refund_amount)
            except:
                dispute.amount_refunded = Decimal('0.00')

            if not dispute.assigned_to:
                dispute.assigned_to = request.user

            dispute.save()

            # Send status change notification to user
            if old_status != new_status:
                PaymentNotificationService.send_dispute_status_change_notification(
                    user=dispute.user,
                    dispute_id=dispute.dispute_id,
                    old_status=old_status,
                    new_status=new_status,
                    resolution_notes=resolution_notes
                )

            messages.success(
                request,
                f'Dispute {dispute.dispute_id} resolved. User has been notified via email.'
            )
        else:
            messages.error(request, 'Invalid status selected.')

        return redirect('payments:staff_disputes')

    context = {
        'dispute': dispute,
        'status_choices': PaymentDispute.STATUS_CHOICES,
    }

    return render(request, 'payments/staff/resolve_dispute.html', context)


@login_required
def staff_transactions(request):
    """
    Staff view for transaction monitoring.
    """
    if not hasattr(request.user, 'staff') or not request.user.staff.is_active:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('payments:wallet_dashboard')

    from .models import Transaction
    from django.utils import timezone
    from datetime import timedelta

    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    gateway_filter = request.GET.get('gateway', 'all')
    days_filter = int(request.GET.get('days', 7))

    if days_filter not in [1, 7, 30, 90]:
        days_filter = 7

    # Build query
    start_date = timezone.now() - timedelta(days=days_filter)
    transactions = Transaction.objects.filter(created_at__gte=start_date).order_by('-created_at')

    if status_filter and status_filter != 'all':
        transactions = transactions.filter(status=status_filter)

    if gateway_filter and gateway_filter != 'all':
        transactions = transactions.filter(payment_gateway=gateway_filter)

    # Get summary stats
    total_volume = transactions.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')

    failed_count = transactions.filter(status='failed').count()
    pending_count = transactions.filter(status='pending').count()

    context = {
        'transactions': transactions[:200],
        'selected_status': status_filter,
        'selected_gateway': gateway_filter,
        'selected_days': days_filter,
        'total_volume': total_volume,
        'failed_count': failed_count,
        'pending_count': pending_count,
        'status_choices': Transaction.STATUS_CHOICES,
        'gateway_choices': Transaction.GATEWAY_CHOICES,
        'days_options': [
            {'value': 1, 'label': 'Today'},
            {'value': 7, 'label': 'Last 7 days'},
            {'value': 30, 'label': 'Last 30 days'},
            {'value': 90, 'label': 'Last 90 days'},
        ],
    }

    return render(request, 'payments/staff/transactions.html', context)


# ============================================================================
# PDF RECEIPT DOWNLOAD VIEWS
# ============================================================================

@login_required
@ratelimit(key='user', rate='5/m', method='GET')
def download_transaction_receipt(request, transaction_id):
    """
    Download PDF receipt for a transaction.
    
    Only allows downloads for completed transactions that belong to the user.
    Rate limited to 5 downloads per minute per user.
    """
    from django.http import HttpResponse, Http404
    from django.core.exceptions import PermissionDenied
    from .services.pdf_service import PDFReceiptService
    from .models import WalletActivityLog
    
    try:
        # Get transaction
        transaction = Transaction.objects.select_related('user').get(
            transaction_id=transaction_id
        )
        
        # Verify ownership
        if transaction.user != request.user and not request.user.is_staff:
            raise PermissionDenied("You don't have permission to access this receipt.")
        
        # Only allow downloads for completed or refunded transactions
        if transaction.status not in ['completed', 'refunded']:
            raise PermissionDenied("Receipts are only available for completed transactions.")
        
        # Generate PDF
        pdf_buffer = PDFReceiptService.generate_transaction_receipt(transaction_id)
        
        # Log the download for audit
        WalletActivityLog.objects.create(
            user=request.user,
            action_type='settings_change',
            description=f'Downloaded receipt for transaction {transaction_id}',
            ip_address=request.META.get('REMOTE_ADDR'),
            metadata={'transaction_id': transaction_id}
        )
        
        # Create HTTP response with PDF
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{transaction_id}.pdf"'
        
        return response
        
    except Transaction.DoesNotExist:
        raise Http404("Transaction not found")


@login_required
@ratelimit(key='user', rate='5/m', method='GET')
def download_invoice_pdf(request, invoice_id):
    """
    Download PDF for an invoice.
    
    Only allows downloads for invoices that belong to the user.
    Rate limited to 5 downloads per minute per user.
    """
    from django.http import HttpResponse, Http404
    from django.core.exceptions import PermissionDenied
    from .services.pdf_service import PDFReceiptService
    from .models import WalletActivityLog
    
    try:
        # Get invoice
        invoice = Invoice.objects.select_related('user').get(id=invoice_id)
        
        # Verify ownership
        if invoice.user != request.user and not request.user.is_staff:
            raise PermissionDenied("You don't have permission to access this invoice.")
        
        # Generate PDF
        pdf_buffer = PDFReceiptService.generate_invoice_pdf(invoice_id)
        
        # Log the download for audit
        WalletActivityLog.objects.create(
            user=request.user,
            action_type='settings_change',
            description=f'Downloaded invoice {invoice.invoice_number}',
            ip_address=request.META.get('REMOTE_ADDR'),
            metadata={'invoice_id': invoice_id, 'invoice_number': invoice.invoice_number}
        )
        
        # Create HTTP response with PDF
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
        
        return response
        
    except Invoice.DoesNotExist:
        raise Http404("Invoice not found")
