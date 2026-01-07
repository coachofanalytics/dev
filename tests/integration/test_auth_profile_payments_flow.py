from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone
from types import SimpleNamespace

User = get_user_model()
Wallet = apps.get_model('payments', 'Wallet')
SubscriptionPlan = apps.get_model('payments', 'SubscriptionPlan')
UserSubscription = apps.get_model('payments', 'UserSubscription')
Invoice = apps.get_model('payments', 'Invoice')
Transaction = apps.get_model('payments', 'Transaction')


class AuthProfilePaymentsIntegration(TestCase):
    def test_end_to_end_subscription_and_invoice_payment(self):
        user = User.objects.create_user(username='intuser', password='p')
        # Some test environments disable automatic profile creation; place a
        # lightweight in-memory profile in the related-object cache so that
        # attribute access won't hit the DB.
        user._state.fields_cache['profile'] = SimpleNamespace(user=user)
        # create wallet
        wallet, _ = Wallet.objects.get_or_create(user=user)
        plan = SubscriptionPlan.objects.create(name='Pro', slug='pro', description='desc', price=Decimal('20.00'), duration_days=30)
        sub = UserSubscription.objects.create(user=user, plan=plan)
        # create invoice and transaction
        invoice = Invoice.objects.create(user=user, subscription=sub, amount=Decimal('20.00'), due_date=timezone.now(), description='sub')
        txn = Transaction.objects.create(user=user, invoice=invoice, amount=Decimal('20.00'), transaction_type='invoice_payment', payment_gateway='wallet')
        # simulate wallet credit then complete txn
        wallet.credit(Decimal('50.00'))
        self.assertTrue(wallet.has_sufficient_balance(Decimal('20.00')))
        # debit
        ok = wallet.debit(Decimal('20.00'))
        self.assertTrue(ok)
        txn.mark_as_completed()
        invoice.mark_as_paid()
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')
