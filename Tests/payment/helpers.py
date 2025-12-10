"""
Test helpers and factories for payment tests.

This file contains small helper functions to create test users, wallets,
invoices and transactions used across unit/integration/e2e tests.
Keep helpers minimal and deterministic so tests are easy to reason about.
"""
from django.contrib.auth.models import User
from payments.models import Wallet, Transaction, Invoice
from decimal import Decimal
from django.utils import timezone


def create_user(username='testuser', email='test@example.com', password='password'):
    """Create and return a simple user for tests."""
    user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
    if not user.has_usable_password():
        user.set_password(password)
        user.save()
    return user


def create_wallet_for_user(user, balance=Decimal('0.00'), currency='USD'):
    """Create or return a wallet for `user` with a given balance."""
    wallet, _ = Wallet.objects.get_or_create(user=user, defaults={'balance': balance, 'currency': currency})
    wallet.balance = Decimal(str(balance))
    wallet.save()
    return wallet


def create_invoice(user, amount=Decimal('10.00'), currency='USD', description='Test invoice'):
    """Create and return an invoice object for tests."""
    due = timezone.now() + timezone.timedelta(days=7)
    invoice = Invoice.objects.create(user=user, amount=Decimal(str(amount)), currency=currency, due_date=due, description=description)
    return invoice


def create_transaction(user, wallet=None, invoice=None, amount=Decimal('10.00'), gateway='stripe', status='pending', tx_type='deposit', gateway_id='GATEWAY-TEST-1'):
    """Create and return a Transaction with predictable id and metadata."""
    txn = Transaction.objects.create(
        user=user,
        wallet=wallet,
        invoice=invoice,
        transaction_type=tx_type,
        amount=Decimal(str(amount)),
        currency='USD',
        payment_gateway=gateway,
        gateway_transaction_id=gateway_id,
        status=status,
        metadata={}
    )
    return txn
