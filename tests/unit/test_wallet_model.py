from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()
Wallet = apps.get_model('payments', 'Wallet')


class WalletModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_fields_and_defaults(self):
        self.assertEqual(self.wallet.balance, Decimal('0.00'))
        self.assertEqual(self.wallet.currency, 'USD')
        self.assertTrue(self.wallet.is_active)

    def test_credit_increases_balance(self):
        ok = self.wallet.credit(10)
        self.wallet.refresh_from_db()
        self.assertTrue(ok)
        self.assertEqual(self.wallet.balance, Decimal('10.00'))

    def test_debit_with_sufficient_balance(self):
        self.wallet.credit(20)
        ok = self.wallet.debit(5)
        self.wallet.refresh_from_db()
        self.assertTrue(ok)
        self.assertEqual(self.wallet.balance, Decimal('15.00'))

    def test_debit_insufficient_balance(self):
        ok = self.wallet.debit(1000)
        self.assertFalse(ok)

    def test_has_sufficient_balance(self):
        self.wallet.credit(7.5)
        self.assertTrue(self.wallet.has_sufficient_balance(7.5))
        self.assertFalse(self.wallet.has_sufficient_balance(10))
