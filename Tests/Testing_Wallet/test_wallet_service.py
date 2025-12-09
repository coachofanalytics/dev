from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User

from payments.models import Wallet, Transaction
from payments.services.wallet_service import WalletService


class WalletServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        # Some projects auto-create a Wallet via signals; use get_or_create to avoid unique constraint errors
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user, defaults={'balance': Decimal('0.00'), 'currency': 'USD'})

    def test_credit_wallet_creates_transaction_and_updates_balance(self):
        amount = Decimal('25.50')
        tx = WalletService.credit_wallet(self.wallet, amount, transaction_type='deposit', metadata={'note': 'test deposit'})

        # Refresh wallet from DB
        self.wallet.refresh_from_db()

        self.assertEqual(self.wallet.balance, amount)
        self.assertIsInstance(tx, Transaction)
        self.assertEqual(tx.amount, amount)
        self.assertEqual(tx.transaction_type, 'deposit')
        self.assertEqual(tx.payment_gateway, 'wallet')
        self.assertEqual(tx.status, 'completed')

    def test_debit_wallet_creates_transaction_and_updates_balance(self):
        # Seed wallet with funds
        WalletService.credit_wallet(self.wallet, Decimal('100.00'), transaction_type='deposit')

        amount = Decimal('40.75')
        tx = WalletService.debit_wallet(self.wallet, amount, transaction_type='withdrawal', metadata={'note': 'test withdraw'})

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('59.25'))
        self.assertIsInstance(tx, Transaction)
        self.assertEqual(tx.amount, amount)
        self.assertEqual(tx.transaction_type, 'withdrawal')
        self.assertEqual(tx.status, 'completed')

    def test_debit_wallet_raises_on_insufficient_balance(self):
        # Wallet has zero balance
        with self.assertRaises(ValueError):
            WalletService.debit_wallet(self.wallet, Decimal('10.00'), transaction_type='withdrawal')

        # Ensure no transaction was created
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 0)

    def test_get_balance_and_check_sufficient(self):
        WalletService.credit_wallet(self.wallet, Decimal('15.00'), transaction_type='deposit')
        self.wallet.refresh_from_db()

        bal = WalletService.get_balance(self.wallet)
        self.assertEqual(bal, Decimal('15.00'))

        self.assertTrue(WalletService.check_sufficient_balance(self.wallet, Decimal('5.00')))
        self.assertFalse(WalletService.check_sufficient_balance(self.wallet, Decimal('20.00')))
