from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User

from payments.models import Wallet, Transaction


class TransactionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='txn_user', password='pass')
        # Some projects auto-create a Wallet via signals; use get_or_create to avoid unique constraint errors
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user, defaults={'balance': Decimal('50.00'), 'currency': 'USD'})

    def test_transaction_save_generates_transaction_id(self):
        tx = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('10.00'),
            currency='USD',
            payment_gateway='wallet',
            status='pending'
        )

        self.assertIsNotNone(tx.transaction_id)
        self.assertTrue(tx.transaction_id.startswith('TXN-'))

    def test_mark_as_completed_and_failed(self):
        tx = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='subscription_payment',
            amount=Decimal('20.00'),
            currency='USD',
            payment_gateway='stripe',
            status='pending'
        )

        tx.mark_as_completed()
        tx.refresh_from_db()
        self.assertEqual(tx.status, 'completed')

        tx.mark_as_failed(reason='declined')
        tx.refresh_from_db()
        self.assertEqual(tx.status, 'failed')
        self.assertIn('failure_reason', tx.metadata)
