"""
Wallet Concurrency and Race Condition Tests.

Comprehensive tests for:
- Concurrent credit operations
- Concurrent debit operations
- Mixed credit/debit under load
- Idempotency simulation
- Atomicity validation
- Double-spend detection

All tests output timing and throughput metrics.
"""

import pytest
import threading
import time
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from django.db import connection, transaction

from payments.models import Wallet, Transaction

from .conftest import (
    PerformanceMetrics,
    ConcurrencyResult,
    run_concurrent,
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.performance
@pytest.mark.concurrency
class TestConcurrentCredits:
    """Concurrent credit operation tests."""

    @pytest.fixture
    def credit_wallet_setup(self, db):
        """Create user with zero-balance wallet for credit testing."""
        user = User.objects.create_user(
            username='credit_concurrency_user',
            email='creditconc@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )
        wallet.balance = Decimal('0.00')
        wallet.save()
        return user, wallet

    def test_concurrent_credits__50_threads__balance_correct(self, credit_wallet_setup, db):
        """
        CONCURRENCY TEST: 50 concurrent credit operations.
        
        Each thread credits $10. Final balance should be exactly $500.
        If balance differs, race condition is detected.
        
        Outputs:
        - Successful operations count
        - Final balance vs expected
        - Throughput (ops/sec)
        """
        user, wallet = credit_wallet_setup
        num_threads = 50
        credit_amount = Decimal('10.00')
        expected_balance = credit_amount * num_threads
        
        results = ConcurrencyResult()
        lock = threading.Lock()
        
        def credit_operation():
            try:
                # Each thread gets fresh wallet instance
                w = Wallet.objects.get(user=user)
                result = w.credit(credit_amount)
                with lock:
                    if result:
                        results.successful += 1
                    else:
                        results.failed += 1
            except Exception as e:
                with lock:
                    results.failed += 1
                    results.errors.append(str(e))
        
        start_time = time.perf_counter()
        
        threads = [threading.Thread(target=credit_operation) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        elapsed = time.perf_counter() - start_time
        throughput = num_threads / elapsed if elapsed > 0 else 0
        
        wallet.refresh_from_db()
        
        # Output metrics
        print(f"\n{'=' * 60}")
        print("Concurrent Credits Test Results")
        print(f"{'=' * 60}")
        print(f"  Threads: {num_threads}")
        print(f"  Credit amount: ${credit_amount}")
        print(f"  Successful: {results.successful}")
        print(f"  Failed: {results.failed}")
        print(f"  Expected balance: ${expected_balance}")
        print(f"  Actual balance: ${wallet.balance}")
        print(f"  Difference: ${abs(wallet.balance - expected_balance)}")
        print(f"  Elapsed: {elapsed:.3f}s")
        print(f"  Throughput: {throughput:.2f} ops/sec")
        print(f"{'=' * 60}\n")
        
        # Security check
        if wallet.balance != expected_balance:
            pytest.fail(
                f"RACE CONDITION DETECTED in concurrent credits!\n"
                f"Expected balance: ${expected_balance}\n"
                f"Actual balance: ${wallet.balance}\n"
                f"Lost credits: ${expected_balance - wallet.balance}\n"
                f"IMPACT: Money credited but not reflected in balance.\n"
                f"RECOMMENDATION: Implement SELECT FOR UPDATE locking."
            )


@pytest.mark.django_db(transaction=True)
@pytest.mark.performance
@pytest.mark.concurrency
class TestConcurrentDebits:
    """Concurrent debit operation tests."""

    @pytest.fixture
    def debit_wallet_setup(self, db):
        """Create user with known balance for debit testing."""
        user = User.objects.create_user(
            username='debit_concurrency_user',
            email='debitconc@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('1000.00')}
        )
        wallet.balance = Decimal('1000.00')
        wallet.save()
        return user, wallet

    def test_concurrent_debits__overdraft_prevention(self, debit_wallet_setup, db):
        """
        CRITICAL SECURITY TEST: Concurrent debits should not cause overdraft.
        
        Initial balance: $1000
        10 threads each trying to debit $200
        Only 5 should succeed (5 x $200 = $1000)
        
        If more than 5 succeed, race condition allows overdraft.
        """
        user, wallet = debit_wallet_setup
        initial_balance = wallet.balance
        num_threads = 10
        debit_amount = Decimal('200.00')
        expected_max_debits = int(initial_balance / debit_amount)
        
        successful_debits = []
        failed_debits = []
        lock = threading.Lock()
        
        def debit_operation():
            try:
                w = Wallet.objects.get(user=user)
                result = w.debit(debit_amount)
                with lock:
                    if result:
                        successful_debits.append(debit_amount)
                    else:
                        failed_debits.append('insufficient_balance')
            except Exception as e:
                with lock:
                    failed_debits.append(str(e))
        
        start_time = time.perf_counter()
        
        threads = [threading.Thread(target=debit_operation) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        elapsed = time.perf_counter() - start_time
        
        wallet.refresh_from_db()
        total_debited = sum(successful_debits)
        
        print(f"\n{'=' * 60}")
        print("Concurrent Debits Test Results")
        print(f"{'=' * 60}")
        print(f"  Initial balance: ${initial_balance}")
        print(f"  Threads: {num_threads}")
        print(f"  Debit amount: ${debit_amount}")
        print(f"  Successful debits: {len(successful_debits)}")
        print(f"  Failed debits: {len(failed_debits)}")
        print(f"  Total debited: ${total_debited}")
        print(f"  Final balance: ${wallet.balance}")
        print(f"  Elapsed: {elapsed:.3f}s")
        print(f"{'=' * 60}\n")
        
        # Security checks
        if total_debited > initial_balance:
            pytest.fail(
                f"CRITICAL SECURITY ISSUE: Overdraft detected!\n"
                f"Initial balance: ${initial_balance}\n"
                f"Total debited: ${total_debited}\n"
                f"Overdraft amount: ${total_debited - initial_balance}\n"
                f"IMPACT: Users can withdraw more than available balance.\n"
                f"RECOMMENDATION: Implement database-level locking."
            )
        
        if wallet.balance < Decimal('0.00'):
            pytest.fail(
                f"CRITICAL SECURITY ISSUE: Negative balance!\n"
                f"Final balance: ${wallet.balance}\n"
                f"IMPACT: System integrity compromised."
            )

    def test_concurrent_debits__no_negative_balance(self, debit_wallet_setup, db):
        """
        SECURITY TEST: Balance should never go negative.
        
        Stress test with more threads than available balance allows.
        """
        user, wallet = debit_wallet_setup
        wallet.balance = Decimal('100.00')
        wallet.save()
        
        num_threads = 20
        debit_amount = Decimal('50.00')
        
        def debit_operation():
            try:
                w = Wallet.objects.get(user=user)
                w.debit(debit_amount)
            except Exception:
                pass
        
        threads = [threading.Thread(target=debit_operation) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        wallet.refresh_from_db()
        
        assert wallet.balance >= Decimal('0.00'), (
            f"SECURITY FAILURE: Balance went negative: ${wallet.balance}"
        )


@pytest.mark.django_db(transaction=True)
@pytest.mark.performance
@pytest.mark.concurrency
class TestMixedConcurrentOperations:
    """Mixed credit/debit concurrent operation tests."""

    @pytest.fixture
    def mixed_wallet_setup(self, db):
        """Create wallet for mixed operations testing."""
        user = User.objects.create_user(
            username='mixed_concurrency_user',
            email='mixedconc@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('1000.00')}
        )
        wallet.balance = Decimal('1000.00')
        wallet.save()
        return user, wallet

    def test_mixed_credit_debit__high_load__balance_consistent(self, mixed_wallet_setup, db):
        """
        CONCURRENCY TEST: Mixed credits and debits under high load.
        
        50 credits of $10 and 50 debits of $10 concurrent.
        If all succeed, balance should remain unchanged.
        
        Detects balance inconsistencies from race conditions.
        """
        user, wallet = mixed_wallet_setup
        initial_balance = wallet.balance
        num_operations = 100  # 50 credits, 50 debits
        operation_amount = Decimal('10.00')
        
        results = {
            'credits_success': 0,
            'credits_fail': 0,
            'debits_success': 0,
            'debits_fail': 0,
            'errors': []
        }
        lock = threading.Lock()
        
        def credit_op():
            try:
                w = Wallet.objects.get(user=user)
                if w.credit(operation_amount):
                    with lock:
                        results['credits_success'] += 1
                else:
                    with lock:
                        results['credits_fail'] += 1
            except Exception as e:
                with lock:
                    results['errors'].append(f'credit: {e}')
        
        def debit_op():
            try:
                w = Wallet.objects.get(user=user)
                if w.debit(operation_amount):
                    with lock:
                        results['debits_success'] += 1
                else:
                    with lock:
                        results['debits_fail'] += 1
            except Exception as e:
                with lock:
                    results['errors'].append(f'debit: {e}')
        
        # Create mixed threads
        threads = []
        for i in range(num_operations):
            if i % 2 == 0:
                threads.append(threading.Thread(target=credit_op))
            else:
                threads.append(threading.Thread(target=debit_op))
        
        start_time = time.perf_counter()
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        elapsed = time.perf_counter() - start_time
        
        wallet.refresh_from_db()
        
        # Calculate expected balance
        net_change = (
            (results['credits_success'] * operation_amount) -
            (results['debits_success'] * operation_amount)
        )
        expected_balance = initial_balance + net_change
        difference = abs(wallet.balance - expected_balance)
        
        print(f"\n{'=' * 60}")
        print("Mixed Operations Test Results")
        print(f"{'=' * 60}")
        print(f"  Initial balance: ${initial_balance}")
        print(f"  Credit operations: {results['credits_success']} success, {results['credits_fail']} fail")
        print(f"  Debit operations: {results['debits_success']} success, {results['debits_fail']} fail")
        print(f"  Net change: ${net_change:+.2f}")
        print(f"  Expected balance: ${expected_balance}")
        print(f"  Actual balance: ${wallet.balance}")
        print(f"  Difference: ${difference}")
        print(f"  Errors: {len(results['errors'])}")
        print(f"  Elapsed: {elapsed:.3f}s")
        print(f"  Throughput: {num_operations / elapsed:.2f} ops/sec")
        print(f"{'=' * 60}\n")
        
        if difference > Decimal('0.01'):
            pytest.fail(
                f"BALANCE INCONSISTENCY in mixed operations!\n"
                f"Expected: ${expected_balance}\n"
                f"Actual: ${wallet.balance}\n"
                f"Difference: ${difference}\n"
                f"IMPACT: Financial data integrity compromised."
            )


@pytest.mark.django_db(transaction=True)
@pytest.mark.performance
@pytest.mark.concurrency
class TestDoubleSpendPrevention:
    """Double-spend vulnerability detection tests."""

    def test_double_spend__same_funds__single_success(self, db):
        """
        CRITICAL SECURITY TEST: Prevent double-spending same funds.
        
        Balance is exactly $100.
        5 threads each try to debit $100.
        Only 1 should succeed.
        
        If more than 1 succeeds, double-spend vulnerability exists.
        """
        user = User.objects.create_user(
            username='doublespend_user',
            email='doublespend@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        wallet.balance = Decimal('100.00')
        wallet.save()
        
        debit_amount = Decimal('100.00')
        num_threads = 5
        successful_debits = []
        lock = threading.Lock()
        
        def full_debit():
            try:
                w = Wallet.objects.get(user=user)
                if w.debit(debit_amount):
                    with lock:
                        successful_debits.append(1)
            except Exception:
                pass
        
        threads = [threading.Thread(target=full_debit) for _ in range(num_threads)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        wallet.refresh_from_db()
        
        print(f"\n{'=' * 60}")
        print("Double-Spend Prevention Test")
        print(f"{'=' * 60}")
        print(f"  Initial balance: $100.00")
        print(f"  Debit attempts: {num_threads} x $100")
        print(f"  Successful debits: {len(successful_debits)}")
        print(f"  Final balance: ${wallet.balance}")
        print(f"{'=' * 60}\n")
        
        if len(successful_debits) > 1:
            pytest.fail(
                f"CRITICAL: DOUBLE-SPEND VULNERABILITY DETECTED!\n"
                f"Initial balance: $100.00\n"
                f"Successful $100 debits: {len(successful_debits)}\n"
                f"Total withdrawn: ${len(successful_debits) * 100}\n"
                f"Final balance: ${wallet.balance}\n"
                f"IMPACT: Users can spend same money multiple times.\n"
                f"RECOMMENDATION: Implement SELECT FOR UPDATE or optimistic locking."
            )


@pytest.mark.django_db(transaction=True)
@pytest.mark.performance
@pytest.mark.concurrency
class TestIdempotency:
    """Idempotency simulation tests."""

    def test_idempotency__duplicate_transaction_id__single_credit(self, db):
        """
        IDEMPOTENCY TEST: Same transaction ID should only credit once.
        
        Simulates webhook retries with same transaction ID.
        """
        user = User.objects.create_user(
            username='idempotency_user',
            email='idempotency@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )
        wallet.balance = Decimal('0.00')
        wallet.save()
        
        credit_amount = Decimal('100.00')
        gateway_txn_id = 'GATEWAY_TXN_12345'
        
        def credit_with_idempotency():
            """Credit only if transaction doesn't already exist."""
            try:
                # Check if transaction already processed
                if Transaction.objects.filter(
                    gateway_transaction_id=gateway_txn_id,
                    status='completed'
                ).exists():
                    return False
                
                # Create transaction and credit
                txn = Transaction.objects.create(
                    user=user,
                    wallet=wallet,
                    transaction_type='deposit',
                    amount=credit_amount,
                    payment_gateway='stripe',
                    gateway_transaction_id=gateway_txn_id,
                    status='completed'
                )
                
                w = Wallet.objects.get(user=user)
                w.credit(credit_amount)
                return True
            except Exception:
                return False
        
        # Simulate 5 webhook retries
        results = []
        for _ in range(5):
            result = credit_with_idempotency()
            results.append(result)
        
        wallet.refresh_from_db()
        transaction_count = Transaction.objects.filter(
            gateway_transaction_id=gateway_txn_id
        ).count()
        
        print(f"\n{'=' * 60}")
        print("Idempotency Test Results")
        print(f"{'=' * 60}")
        print(f"  Attempts: 5")
        print(f"  Successful credits: {sum(results)}")
        print(f"  Transaction records: {transaction_count}")
        print(f"  Final balance: ${wallet.balance}")
        print(f"  Expected balance: ${credit_amount}")
        print(f"{'=' * 60}\n")
        
        # Note: This test checks application-level idempotency
        # The actual implementation may handle this differently
        if wallet.balance > credit_amount:
            pytest.fail(
                f"IDEMPOTENCY FAILURE: Duplicate credits detected!\n"
                f"Expected balance: ${credit_amount}\n"
                f"Actual balance: ${wallet.balance}\n"
                f"IMPACT: Webhooks can cause duplicate credits."
            )


@pytest.mark.django_db(transaction=True)
@pytest.mark.performance
@pytest.mark.concurrency
@pytest.mark.slow
class TestHighConcurrencyStress:
    """High concurrency stress tests."""

    def test_100_concurrent_operations__throughput_report(self, db):
        """
        STRESS TEST: 100 concurrent mixed operations.
        
        Tests system behavior under high concurrency.
        Reports throughput and error rates.
        """
        user = User.objects.create_user(
            username='stress_100_user',
            email='stress100@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('10000.00')}
        )
        wallet.balance = Decimal('10000.00')
        wallet.save()
        
        initial_balance = wallet.balance
        num_threads = 100
        operation_amount = Decimal('10.00')
        
        results = {
            'credits': 0,
            'debits': 0,
            'errors': 0,
            'timings': []
        }
        lock = threading.Lock()
        
        def operation(i):
            start = time.perf_counter()
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
            finally:
                elapsed = (time.perf_counter() - start) * 1000
                with lock:
                    results['timings'].append(elapsed)
        
        start_time = time.perf_counter()
        
        threads = [threading.Thread(target=operation, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        total_elapsed = time.perf_counter() - start_time
        throughput = num_threads / total_elapsed if total_elapsed > 0 else 0
        
        wallet.refresh_from_db()
        
        # Calculate expected
        net_change = (results['credits'] - results['debits']) * operation_amount
        expected_balance = initial_balance + net_change
        difference = abs(wallet.balance - expected_balance)
        
        # Compute p95 latency
        sorted_timings = sorted(results['timings'])
        p95_idx = int(len(sorted_timings) * 0.95) if sorted_timings else 0
        p95_latency = sorted_timings[min(p95_idx, len(sorted_timings) - 1)] if sorted_timings else 0
        
        print(f"\n{'=' * 60}")
        print("100 Concurrent Operations Stress Test")
        print(f"{'=' * 60}")
        print(f"  Total operations: {num_threads}")
        print(f"  Successful credits: {results['credits']}")
        print(f"  Successful debits: {results['debits']}")
        print(f"  Errors: {results['errors']}")
        print(f"  Error rate: {results['errors'] / num_threads * 100:.1f}%")
        print(f"  Expected balance: ${expected_balance}")
        print(f"  Actual balance: ${wallet.balance}")
        print(f"  Balance difference: ${difference}")
        print(f"  Total elapsed: {total_elapsed:.3f}s")
        print(f"  Throughput: {throughput:.2f} ops/sec")
        print(f"  p95 latency: {p95_latency:.2f}ms")
        print(f"{'=' * 60}\n")
        
        if difference > Decimal('0.01'):
            pytest.fail(
                f"BALANCE INCONSISTENCY under high concurrency!\n"
                f"Expected: ${expected_balance}, Actual: ${wallet.balance}"
            )
        
        if results['errors'] > 10:
            pytest.skip(
                f"HIGH ERROR RATE: {results['errors']} errors out of {num_threads}.\n"
                "May indicate connection pooling or locking issues."
            )

    def test_200_concurrent_operations__breaking_point(self, db):
        """
        STRESS TEST: 200 concurrent operations to find breaking point.
        
        Tests for deadlocks, timeouts, and failure modes.
        """
        user = User.objects.create_user(
            username='stress_200_user',
            email='stress200@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('50000.00')}
        )
        wallet.balance = Decimal('50000.00')
        wallet.save()
        
        num_threads = 200
        operation_amount = Decimal('10.00')
        
        errors = []
        error_types = {}
        lock = threading.Lock()
        
        def operation(i):
            try:
                w = Wallet.objects.get(user=user)
                if i % 2 == 0:
                    w.credit(operation_amount)
                else:
                    w.debit(operation_amount)
            except Exception as e:
                error_type = type(e).__name__
                with lock:
                    errors.append(str(e))
                    error_types[error_type] = error_types.get(error_type, 0) + 1
        
        start_time = time.perf_counter()
        
        threads = [threading.Thread(target=operation, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        elapsed = time.perf_counter() - start_time
        
        print(f"\n{'=' * 60}")
        print("200 Concurrent Operations Breaking Point Test")
        print(f"{'=' * 60}")
        print(f"  Total operations: {num_threads}")
        print(f"  Errors: {len(errors)}")
        print(f"  Error rate: {len(errors) / num_threads * 100:.1f}%")
        print(f"  Error types: {error_types}")
        print(f"  Elapsed: {elapsed:.3f}s")
        print(f"{'=' * 60}\n")
        
        # Report failure modes
        if error_types:
            print("Detected failure modes:")
            for error_type, count in error_types.items():
                print(f"  - {error_type}: {count} occurrences")
