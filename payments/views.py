from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum
from decimal import Decimal
from django_ratelimit.decorators import ratelimit

from .models import Wallet, Transaction, SubscriptionPlan, UserSubscription, Invoice
from .forms import DepositForm, MPesaDepositForm, StripePaymentMethodForm
from .services import PaymentGatewayFactory


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
                    transaction.status = 'completed'
                    transaction.external_reference = payment_result.get('transaction_id')
                    transaction.save()
                    wallet.balance += deposit_amount_decimal
                    wallet.save()

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
                    messages.error(request, payment_result.get('error_message', 'Payment processing failed. Please try again.'))
                    return redirect('payments:deposit_stripe')

            except Exception as e:
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
            transaction.status = 'completed'
            transaction.external_reference = paypal_payment_id
            transaction.save()

            wallet.balance += transaction.amount
            wallet.save()

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
            transaction_reference=transaction.external_reference,
        )

        if status_result['success']:
            current_status = status_result.get('status')

            if current_status == 'completed' and transaction.status == 'pending':
                transaction.status = 'completed'
                transaction.save()

                wallet = transaction.wallet
                wallet.balance += transaction.amount
                wallet.save()

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
