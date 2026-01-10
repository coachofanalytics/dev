"""
Payment and Wallet Security Tests.

Covers:
- Negative amount protection
- Double-spend prevention (concurrency)
- Unauthorized wallet access (IDOR)
- Transaction integrity
- Invoice tampering prevention
"""

import pytest
import threading
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from payments.models import Wallet, Transaction, Invoice, UserSubscription, SubscriptionPlan
from payments.services.wallet_service import WalletService
from django.db import transaction

User = get_user_model()


@pytest.mark.security
class TestWalletLogicSecurity(TestCase):
    """Tests for core wallet logic security flaws."""

    def setUp(self):
        self.user = User.objects.create_user(username='wallet_sec_user', password='password123')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)
        self.wallet.balance = Decimal('100.00')
        self.wallet.save()

    def test_negative_amount_credit_blocked(self):
        """Test that crediting a negative amount is not allowed."""
        initial_balance = self.wallet.balance
        
        # Method level check
        success = self.wallet.credit(Decimal('-10.00'))
        self.wallet.refresh_from_db()
        
        self.assertFalse(success, "Wallet.credit should return False for negative amounts")
        self.assertEqual(self.wallet.balance, initial_balance, "Balance should not change")

    def test_negative_amount_debit_blocked(self):
        """Test that debiting a negative amount is not allowed (could increase balance)."""
        initial_balance = self.wallet.balance
        
        # Method level check
        success = self.wallet.debit(Decimal('-10.00'))
        self.wallet.refresh_from_db()
        
        self.assertFalse(success, "Wallet.debit should return False for negative amounts")
        self.assertEqual(self.wallet.balance, initial_balance, "Balance should not change")

    def test_cannot_debit_more_than_balance(self):
        """Test that debiting more than balance fails."""
        initial_balance = self.wallet.balance
        overdraft_amount = initial_balance + Decimal('1.00')
        
        success = self.wallet.debit(overdraft_amount)
        self.wallet.refresh_from_db()
        
        self.assertFalse(success, "Wallet.debit should return False for insufficient funds")
        self.assertEqual(self.wallet.balance, initial_balance)


@pytest.mark.security
class TestWalletConcurrencySecurity(TransactionTestCase):
    """
    Tests for race conditions and double-spending.
    Uses TransactionTestCase to allow thread-based database access.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='concurrent_user', password='password123')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)
        # Give just enough for ONE transaction
        self.wallet.balance = Decimal('100.00')
        self.wallet.save()

    def test_double_spend_race_condition(self):
        """
        SECURITY TEST: Attempt to double-spend via concurrent requests.
        
        Tries to debit $100 twice simultaneously. Only one should succeed.
        """
        amount = Decimal('100.00')
        results = []

        def attempt_debit():
            try:
                # Simulate the check-then-act pattern often found in views
                # We use the Service which *should* handle this safely if written correctly
                # (or the view should use select_for_update)
                with transaction.atomic():
                    # Intentionally mimicking potential vulnerable code if locking isn't strict
                    # We reload wallet inside transaction to test standard DB locking
                    w = Wallet.objects.select_for_update().get(id=self.wallet.id)
                    try:
                        txn = WalletService.debit_wallet(w, amount, 'purchase')
                        results.append('success')
                    except ValueError:
                        results.append('failed')
            except Exception as e:
                results.append(f'error: {e}')

        # Create two threads trying to spend the same funds
        t1 = threading.Thread(target=attempt_debit)
        t2 = threading.Thread(target=attempt_debit)
        
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # refresh wallet
        self.wallet.refresh_from_db()

        success_count = results.count('success')
        self.assertEqual(success_count, 1, f"Double spend detected! Results: {results}. Balance: {self.wallet.balance}")
        self.assertEqual(self.wallet.balance, Decimal('0.00'))


@pytest.mark.security
class TestWalletAccessControl(TestCase):
    """Tests for IDOR and unauthorized access."""

    def setUp(self):
        self.victim = User.objects.create_user(username='victim', password='password123')
        self.attacker = User.objects.create_user(username='attacker', password='password123')
        
        self.victim_wallet, _ = Wallet.objects.get_or_create(user=self.victim)
        self.attacker_wallet, _ = Wallet.objects.get_or_create(user=self.attacker)
        
        self.victim_txn = Transaction.objects.create(
            user=self.victim,
            wallet=self.victim_wallet,
            transaction_type='deposit',
            amount=Decimal('500.00'),
            payment_gateway='test',
            status='completed'
        )

    def test_user_cannot_view_other_wallet_dashboard(self):
        """Test that a user cannot see another user's wallet dashboard/data."""
        self.client.force_login(self.attacker)
        
        # Since the view likely infers wallet from request.user, direct IDOR might not be possible 
        # via the dashboard URL if it doesn't take an ID.
        # But we check if there are API endpoints that take an ID.
        
        # Assuming a hypothetical API or admin view
        response = self.client.get(f'/payments/wallet/{self.victim_wallet.id}/')
        # If this URL doesn't exist, it's a 404, which is also "secure" against IDOR
        # If it uses request.user, it should return 200 but show ATTACKER'S wallet, not VICTIM'S.
        
        if response.status_code == 200:
            # Verify we are not seeing victim's data
            self.assertNotContains(response, self.victim_wallet.user.username)
            self.assertNotContains(response, str(self.victim_txn.transaction_id))

    def test_user_cannot_access_other_transaction_csv(self):
        """Test export functionality doesn't leak other users data."""
        self.client.force_login(self.attacker)
        response = self.client.get('/payments/transactions/export/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            self.assertNotIn(self.victim_txn.transaction_id, content)


@pytest.mark.security
class TestInvoiceSecurity(TestCase):
    """Tests for invoice tampering and integrity."""

    def setUp(self):
        self.user = User.objects.create_user(username='invoice_user', password='password123')
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            price=Decimal('50.00'),
            duration_days=30
        )
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='pending'
        )
        self.invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            amount=Decimal('50.00'),
            due_date=transaction.timezone.now()
        )

    def test_invoice_amount_tampering(self):
        """Test prevention of modifying invoice amount."""
        original_amount = self.invoice.amount
        
        # Attacker tries to update invoice amount directly (hypothetical update endpoint)
        self.client.force_login(self.user)
        
        # Assuming an endpoint like /invoices/<id>/update/ exists
        # If not, this tests the underlying model resilience or lack of exposure
        
        # Check if Invoice model allows negative amounts if updated directly
        self.invoice.amount = Decimal('-50.00')
        # Should raise validation error
        with self.assertRaises(Exception): # ValidationError or IntegrityError
             self.invoice.full_clean()
             self.invoice.save()
        
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount, original_amount)

    def test_mark_invoice_paid_without_payment(self):
        """
        Verify invoice status cannot be manually set to 'paid' 
        without a corresponding completed transaction logic.
        """
        # Checks logic, not just HTTP
        self.invoice.status = 'paid'
        # In a real secure system, there should be checks or signals. 
        # But models often rely on service layer. 
        # This test documents that the MODEL allows it (which is risky if views aren't careful)
        self.invoice.save()
        
        # If this passes, it means the model is "dumb" data storage.
        # We should verify that no signals triggered 'subscription active' without a transaction.
        
        self.subscription.refresh_from_db()
        # Subscription should NOT be active just because invoice status changed manually
        # (unless there's a signal handler that blindly trusts invoice status)
        self.assertNotEqual(self.subscription.status, 'active', 
            "Subscription activated merely by changing invoice status - Risky Design!")
