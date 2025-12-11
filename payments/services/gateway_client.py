from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging

from payments.utils.idempotency import reserve_idempotency_key, get_idempotency_response, mark_idempotency_used
from payments.models import Transaction, Wallet

logger = logging.getLogger(__name__)


def _sanitize_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    # Remove any potential PANs or sensitive fields before storing
    safe = dict(resp)
    for k in list(safe.keys()):
        if 'pan' in k.lower() or 'number' in k.lower() or 'cvv' in k.lower():
            safe.pop(k, None)
    return safe


def process_stripe_payment(user, amount: Decimal, currency: str = 'USD', idempotency_key: Optional[str] = None) -> Dict[str, Any]:
    """Process a payment via Stripe with idempotency and atomic DB updates.

    Returns a dict with gateway response.
    """
    # Check previous idempotent response
    if idempotency_key:
        prev = get_idempotency_response(idempotency_key)
        if prev:
            return prev

    reserve = None
    if idempotency_key:
        reserve = reserve_idempotency_key(idempotency_key, user)

    # Create transaction and lock wallet
    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().filter(user=user).first()
        txn = Transaction.objects.create(user=user, wallet=wallet, amount=amount, currency=currency, transaction_type='deposit', payment_gateway='stripe', status='pending')

    # Call Stripe SDK
    try:
        import stripe
        opts = None
        if idempotency_key:
            opts = {'idempotency_key': idempotency_key}
        # create PaymentIntent
        pi = stripe.PaymentIntent.create(amount=int(amount * 100), currency=currency.lower(), **({'metadata': {'transaction_id': txn.transaction_id}} if txn else {}), request_options=stripe.request.RequestOptions(idempotency_key=idempotency_key) if idempotency_key else None)
        safe = _sanitize_response(pi)
        # mark transaction completed
        with transaction.atomic():
            txn.gateway_transaction_id = getattr(pi, 'id', None) or pi.get('id')
            txn.metadata = safe
            txn.status = 'completed'
            txn.save()
        if idempotency_key:
            mark_idempotency_used(idempotency_key, safe)
        return safe
    except Exception as e:
        logger.exception('Stripe payment failed')
        with transaction.atomic():
            txn.mark_as_failed(reason=str(e))
        raise


def process_paypal_payment(user, amount: Decimal, currency: str = 'USD', idempotency_key: Optional[str] = None) -> Dict[str, Any]:
    """Process PayPal order creation/capture with idempotency and atomic DB updates.

    This is a thin wrapper; the underlying PayPal SDK or HTTP client should be used by callers.
    """
    if idempotency_key:
        prev = get_idempotency_response(idempotency_key)
        if prev:
            return prev

    if idempotency_key:
        reserve_idempotency_key(idempotency_key, user)

    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().filter(user=user).first()
        txn = Transaction.objects.create(user=user, wallet=wallet, amount=amount, currency=currency, transaction_type='deposit', payment_gateway='paypal', status='pending')

    try:
        import paypalrestsdk
        paypalrestsdk.configure({})
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{"amount": {"total": f"{amount:.2f}", "currency": currency}}],
            "redirect_urls": {"return_url": "https://example.com/paypal/return", "cancel_url": "https://example.com/paypal/cancel"}
        })
        created = payment.create()
        safe = _sanitize_response(payment.to_dict() if hasattr(payment, 'to_dict') else {})
        with transaction.atomic():
            txn.gateway_transaction_id = getattr(payment, 'id', None) or safe.get('id')
            txn.metadata = safe
            txn.status = 'completed' if created else 'failed'
            txn.save()
        if idempotency_key:
            mark_idempotency_used(idempotency_key, safe)
        return safe
    except Exception as e:
        logger.exception('PayPal payment failed')
        with transaction.atomic():
            txn.mark_as_failed(reason=str(e))
        raise
