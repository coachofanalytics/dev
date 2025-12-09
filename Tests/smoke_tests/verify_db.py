"""Simple DB verification helpers for smoke tests.

Run to inspect key payment-related rows: PaymentGatewayConfig, last Transactions and Wallet balances for a test user.

Usage:
  python Tests/smoke_tests/verify_db.py --user test@example.com

"""
import os
import sys
import argparse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# Ensure project root is on sys.path so `config` package can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import django
django.setup()

from django.contrib.auth import get_user_model
from payments.models import PaymentGatewayConfig, Transaction, Wallet


def main(email=None):
    print('\nPaymentGatewayConfig rows:')
    for row in PaymentGatewayConfig.objects.all().values('gateway_name','is_active','is_test_mode','config_data'):
        print(' -', row)

    if not email:
        print('\nNo user email provided. Provide `--user email@example.com` to check transactions and wallet.')
        return

    User = get_user_model()
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        print(f'User with email {email} not found in DB.')
        return

    print(f'\nUser: {user.email} (id={user.id})')
    try:
        w = Wallet.objects.get(user=user)
        print('Wallet balance:', w.balance)
    except Wallet.DoesNotExist:
        print('No wallet found for user (it may be auto-created on first use).')

    print('\nLast 10 transactions:')
    for tx in Transaction.objects.filter(user=user).order_by('-created')[:10]:
        print(f' - {tx.pk} | {tx.kind} | {tx.amount} | {tx.status} | {tx.created}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', help='Email of user to inspect')
    args = parser.parse_args()
    main(email=args.user)
