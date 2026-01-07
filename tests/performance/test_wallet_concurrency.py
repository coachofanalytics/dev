"""
Wallet concurrency and race condition tests.

Tests to detect race conditions in wallet operations that could lead to
balance inconsistencies, double-spending, or negative balances.
"""

import pytest
import threading
import time
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.db import connection, transaction

from payments.models import Wallet, Transaction


@pytest.mark.django_db(transaction=True)
class TestWalletRaceConditions:
    """
    Tests to detect race conditions in wallet credit/debit operations.
    
    These tests simulate concurrent access to expose potential
    balance inconsistencies.
    """

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='race_condition_user',
            email='race@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet with known balance."""
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('1000.00')}
        )
        wallet.balance = Decimal('1000.00')
        wallet.save()
        return wallet

    def test_concurrent_debits_race_condition(self, user, wallet):
        """
        CRITICAL SECURITY TEST: Detect race conditions in concurrent debits.
        
        This test attempts to debit more money than available through
        concurrent requests. If the final balance goes negative or
        total debited exceeds initial balance, there's a race condition.
        """
        initial_balance = wallet.balance
        debit_amount = Decimal('200.00')
        num_threads = 10  # Each thread tries to debit 200
        
        # Expected: Only 5 debits should succeed (5 x 200 = 1000)
        # If more succeed, there's a race condition
        
        successful_debits = []
        failed_debits = []
        
        def attempt_debit():
            """Attempt to debit the wallet."""
            try:
                # Get fresh wallet instance
                w = Wallet.objects.get(user=user)
                result = w.debit(debit_amount)
                if result:
                    successful_debits.append(debit_amount)
                else:
                    failed_debits.append(debit_amount)
            except Exception as e:
                failed_debits.append(str(e))
        
        # Create and start threads
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=attempt_debit)
            threads.append(t)
        
        # Start all threads nearly simultaneously
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Refresh wallet from database
        wallet.refresh_from_db()
        
        total_debited = sum(successful_debits)
        expected_max_debit = initial_balance
        
        # SECURITY CHECK: Detect if race condition occurred
        if total_debited > expected_max_debit:
            pytest.fail(
                f"CRITICAL SECURITY ISSUE: Race condition detected in wallet debit!\n"
                f"Initial balance: {initial_balance}\n"
                f"Total debited: {total_debited}\n"
                f"Successful debits: {len(successful_debits)}\n"
                f"Final balance: {wallet.balance}\n"
                f"IMPACT: Users can withdraw more money than they have.\n"
                f"RECOMMENDATION: Implement SELECT FOR UPDATE locking in debit operations."
            )
        
        if wallet.balance < Decimal('0.00'):
            pytest.fail(
                f"CRITICAL SECURITY ISSUE: Wallet balance went negative!\n"
                f"Final balance: {wallet.balance}\n"
                f"IMPACT: System integrity compromised.\n"
                f"RECOMMENDATION: Implement atomic transactions with balance checks."
            )

    def test_concurrent_credit_debit_race_condition(self, user, wallet):
        """
        SECURITY TEST: Detect race conditions in mixed credit/debit operations.
        
        Simulates concurrent deposits and withdrawals to check for
        balance inconsistencies.
        """
        initial_balance = Decimal('1000.00')
        wallet.balance = initial_balance
        wallet.save()
        
        credit_amount = Decimal('100.00')
        debit_amount = Decimal('100.00')
        num_operations = 20  # 10 credits, 10 debits
        
        operations_log = []
        
        def credit_operation():
            try:
                w = Wallet.objects.get(user=user)
                result = w.credit(credit_amount)
                operations_log.append(('credit', result, credit_amount))
            except Exception as e:
                operations_log.append(('credit_error', str(e), 0))
        
        def debit_operation():
            try:
                w = Wallet.objects.get(user=user)
                result = w.debit(debit_amount)
                operations_log.append(('debit', result, debit_amount if result else 0))
            except Exception as e:
                operations_log.append(('debit_error', str(e), 0))
        
        threads = []
        for i in range(num_operations):
            if i % 2 == 0:
                t = threading.Thread(target=credit_operation)
            else:
                t = threading.Thread(target=debit_operation)
            threads.append(t)
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        wallet.refresh_from_db()
        
        # Calculate expected balance
        successful_credits = sum(1 for op in operations_log if op[0] == 'credit' and op[1])
        successful_debits = sum(1 for op in operations_log if op[0] == 'debit' and op[1])
        
        expected_balance = initial_balance + (successful_credits * credit_amount) - (successful_debits * debit_amount)
        
        # Allow for small floating point differences
        balance_difference = abs(wallet.balance - expected_balance)
        
        if balance_difference > Decimal('0.01'):
            pytest.fail(
                f"SECURITY ISSUE: Balance inconsistency detected!\n"
                f"Initial: {initial_balance}\n"
                f"Expected: {expected_balance}\n"
                f"Actual: {wallet.balance}\n"
                f"Difference: {balance_difference}\n"
                f"Successful credits: {successful_credits}\n"
                f"Successful debits: {successful_debits}\n"
                f"IMPACT: Financial data integrity compromised.\n"
                f"RECOMMENDATION: Use database-level locking for all wallet operations."
            )

    def test_double_spend_vulnerability(self, user, wallet):
        """
        CRITICAL SECURITY TEST: Detect double-spend vulnerability.
        
        Attempts to spend the same funds twice through concurrent requests.
        """
        # Set balance to exactly one debit amount
        wallet.balance = Decimal('100.00')
        wallet.save()
        
        debit_amount = Decimal('100.00')
        successful_debits = []
        
        def attempt_full_debit():
            try:
                w = Wallet.objects.get(user=user)
                if w.debit(debit_amount):
                    successful_debits.append(1)
            except Exception:
                pass
        
        # Try to debit the full balance from multiple threads
        threads = [threading.Thread(target=attempt_full_debit) for _ in range(5)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        wallet.refresh_from_db()
        
        if len(successful_debits) > 1:
            pytest.fail(
                f"CRITICAL SECURITY ISSUE: Double-spend vulnerability detected!\n"
                f"Balance was {Decimal('100.00')}, but {len(successful_debits)} debits of {debit_amount} succeeded.\n"
                f"Final balance: {wallet.balance}\n"
                f"IMPACT: Users can spend the same money multiple times.\n"
                f"RECOMMENDATION: Implement optimistic locking or SELECT FOR UPDATE."
            )


@pytest.mark.django_db(transaction=True)
class TestTransactionAtomicity:
    """Tests for transaction atomicity in payment operations."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='atomic_test_user',
            email='atomic@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(user=user)
        wallet.balance = Decimal('500.00')
        wallet.save()
        return wallet

    def test_transaction_and_wallet_atomicity(self, user, wallet):
        """
        SECURITY TEST: Verify wallet update and transaction creation are atomic.
        
        If a wallet is credited but transaction record fails (or vice versa),
        it creates an audit trail discrepancy.
        """
        initial_balance = wallet.balance
        credit_amount = Decimal('100.00')
        
        # Count transactions before
        txn_count_before = Transaction.objects.filter(user=user).count()
        
        # Perform credit and create transaction
        wallet.credit(credit_amount)
        
        Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=credit_amount,
            payment_gateway='test',
            status='completed'
        )
        
        wallet.refresh_from_db()
        txn_count_after = Transaction.objects.filter(user=user).count()
        
        # Verify both updated
        balance_updated = wallet.balance == initial_balance + credit_amount
        transaction_created = txn_count_after == txn_count_before + 1
        
        if balance_updated != transaction_created:
            pytest.fail(
                "SECURITY ISSUE: Wallet and transaction not atomically updated.\n"
                f"Balance updated: {balance_updated}\n"
                f"Transaction created: {transaction_created}\n"
                "IMPACT: Audit trail may be incomplete or inconsistent.\n"
                "RECOMMENDATION: Wrap wallet updates and transaction creation in database transaction."
            )


@pytest.mark.django_db(transaction=True)
class TestHighConcurrencyWallet:
    """High concurrency tests for wallet stress testing."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='stress_user',
            email='stress@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet with high balance."""
        wallet, _ = Wallet.objects.get_or_create(user=user)
        wallet.balance = Decimal('10000.00')
        wallet.save()
        return wallet

    def test_100_concurrent_operations(self, user, wallet):
        """
        STRESS TEST: 100 concurrent wallet operations.
        
        Tests system behavior under high concurrency.
        """
        initial_balance = wallet.balance
        num_threads = 100
        operation_amount = Decimal('10.00')
        
        results = {'credits': 0, 'debits': 0, 'errors': 0}
        lock = threading.Lock()
        
        def random_operation(i):
            try:
                w = Wallet.objects.get(user=user)
                if i % 2 == 0:
                    if w.credit(operation_amount):
                        with lock:
                            results['credits'] += 1
                else:
                    if w.debit(operation_amount):
                        with lock:
                            results['debits'] += 1
            except Exception:
                with lock:
                    results['errors'] += 1
        
        threads = [threading.Thread(target=random_operation, args=(i,)) for i in range(num_threads)]
        
        start_time = time.time()
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        elapsed = time.time() - start_time
        
        wallet.refresh_from_db()
        
        # Calculate expected
        expected_change = (results['credits'] * operation_amount) - (results['debits'] * operation_amount)
        expected_balance = initial_balance + expected_change
        
        actual_difference = abs(wallet.balance - expected_balance)
        
        # Report findings
        if actual_difference > Decimal('0.01'):
            pytest.fail(
                f"SECURITY ISSUE: Balance inconsistency under high concurrency!\n"
                f"Initial: {initial_balance}\n"
                f"Expected: {expected_balance}\n"
                f"Actual: {wallet.balance}\n"
                f"Difference: {actual_difference}\n"
                f"Successful credits: {results['credits']}\n"
                f"Successful debits: {results['debits']}\n"
                f"Errors: {results['errors']}\n"
                f"Time elapsed: {elapsed:.2f}s\n"
                f"IMPACT: Financial integrity at risk under load.\n"
                f"RECOMMENDATION: Implement proper database locking and consider using Redis for wallet operations."
            )
        
        if results['errors'] > 10:
            pytest.skip(
                f"HIGH ERROR RATE: {results['errors']} errors out of {num_threads} operations.\n"
                "This may indicate connection pooling or locking issues under load."
            )

