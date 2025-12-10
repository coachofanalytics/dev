import os
import time
import threading
from django.test import TestCase
from decimal import Decimal
from tests.payment.helpers import create_user, create_wallet_for_user, create_transaction
from payments import webhooks


class TestConcurrentPayments(TestCase):
    """
    Lightweight performance test that simulates concurrent webhook callbacks.

    This is NOT a substitute for a proper load test tool. It provides a
    simple way to assert that concurrent updates do not corrupt balances.
    Skipped by default unless `RUN_LOAD_TESTS` environment variable is set.
    """

    def setUp(self):
        self.run_load = os.environ.get('RUN_LOAD_TESTS') in ('1', 'true', 'True')
        self.user = create_user('perf_user')
        self.wallet = create_wallet_for_user(self.user, balance=Decimal('0.00'))

    def test_concurrent_stripe_callbacks(self):
        if not self.run_load:
            self.skipTest('Load tests disabled; set RUN_LOAD_TESTS=1 to enable')

        # Create multiple pending transactions that will be completed concurrently
        txns = []
        for i in range(10):
            txns.append(create_transaction(self.user, wallet=self.wallet, amount=Decimal('1.00'), gateway='stripe', gateway_id=f'concurrent_pi_{i}'))

        def call_handler(gid):
            webhooks.handle_stripe_payment_success({'id': gid, 'metadata': {}, 'amount': 100})

        threads = [threading.Thread(target=call_handler, args=(txn.gateway_transaction_id,)) for txn in txns]
        start = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        duration = time.time() - start

        # All transactions should be completed and wallet balance updated
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('10.00'))
        # Basic performance expectation (not strict): must finish within 30s
        self.assertLess(duration, 30.0)
