from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()
Invoice = apps.get_model('payments', 'Invoice')
Transaction = apps.get_model('payments', 'Transaction')
Wallet = apps.get_model('payments', 'Wallet')
UserSubscription = apps.get_model('payments', 'UserSubscription')
SubscriptionPlan = apps.get_model('payments', 'SubscriptionPlan')


class InvoiceTransactionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='fred', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)
        self.plan = SubscriptionPlan.objects.create(name='P', slug='p', description='d', price=Decimal('5.00'), duration_days=30)
        self.subscription = UserSubscription.objects.create(user=self.user, plan=self.plan)

    def test_invoice_auto_number_and_mark_paid(self):
        due = timezone.now()
        invoice = Invoice.objects.create(user=self.user, subscription=self.subscription, amount=Decimal('5.00'), due_date=due, description='test')
        self.assertTrue(invoice.invoice_number.startswith('INV-'))
        invoice.mark_as_paid()
        self.assertEqual(invoice.status, 'paid')
        self.assertIsNotNone(invoice.paid_date)

    def test_transaction_ids_and_mark_complete(self):
        invoice = Invoice.objects.create(user=self.user, subscription=self.subscription, amount=Decimal('5.00'), due_date=timezone.now(), description='t')
        txn = Transaction.objects.create(user=self.user, invoice=invoice, amount=Decimal('5.00'), transaction_type='invoice_payment', payment_gateway='stripe')
        self.assertTrue(txn.transaction_id.startswith('TXN-'))
        txn.mark_as_completed()
        self.assertEqual(txn.status, 'completed')
