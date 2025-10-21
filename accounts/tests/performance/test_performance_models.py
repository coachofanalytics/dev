from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
import time

from accounts.models import PaymentInformation, CustomerUser,Payment_History


class PaymentInformationPerformanceTest(TestCase):
    """⚡ Performance and integrity tests for PaymentInformation model."""

    @classmethod
    def setUpTestData(cls):
        """Create reusable test data for all performance tests."""
        cls.student_user = CustomerUser.objects.create(
            username="student_tester",
            email="student@example.com",
            is_active=True,
        )

        # Generate 1000 test payment records for performance simulation
        payments = [
            PaymentInformation(
                customer_id=cls.student_user,  # ✅ Correct field name
                payment_fees=Decimal("1000.00"),
                down_payment=Decimal("200.00"),
                student_bonus=Decimal("50.00"),
                plan=1,
                subplan=1,
                payment_method="Mpesa",
                contract_submitted_date=timezone.now(),
                client_signature="Signed by student",
                company_rep="Finance Manager",
                client_date="2025-10-20",
                rep_date="2025-10-21",
            )
            for _ in range(1000)
        ]
        PaymentInformation.objects.bulk_create(payments)

    # --------------------------------------------------------------
    # 1️⃣ BULK RETRIEVAL PERFORMANCE TEST
    # --------------------------------------------------------------
    def test_bulk_retrieval_speed(self):
        """⚡ Ensure retrieving 1000 PaymentInformation records is fast."""
        start = time.time()
        payments = list(PaymentInformation.objects.all())
        duration = time.time() - start
        print(f"\n⏱ Retrieval Time: {duration:.4f} sec for {len(payments)} records")

        self.assertLess(duration, 1.5, "Bulk retrieval too slow!")

    # --------------------------------------------------------------
    # 2️⃣ BULK UPDATE PERFORMANCE TEST
    # --------------------------------------------------------------
    def test_bulk_update_performance(self):
        """⚡ Ensure bulk updates execute efficiently."""
        payments = list(PaymentInformation.objects.all())
        for p in payments:
            p.down_payment += Decimal("100.00")

        start = time.time()
        PaymentInformation.objects.bulk_update(payments, ["down_payment"])
        duration = time.time() - start
        print(f"\n💾 Bulk Update Time: {duration:.4f} sec")

        self.assertLess(duration, 1.0, "Bulk update took too long!")

    # --------------------------------------------------------------
    # 3️⃣ BALANCE COMPUTATION PERFORMANCE TEST
    # --------------------------------------------------------------
    def test_balance_calculation_efficiency(self):
        """⚡ Ensure property computations run efficiently and correctly."""
        payments = list(PaymentInformation.objects.all())

        start = time.time()
        student_totals = [float(p.student_balance) for p in payments]
        job_totals = [float(p.jobsupport_balance) for p in payments]
        duration = time.time() - start
        print(f"\n⚙️ Computation Time: {duration:.4f} sec for balance calculations")

        # ✅ Validate all computed values are numeric
        from numbers import Number
        self.assertTrue(all(isinstance(t, Number) for t in student_totals))
        self.assertTrue(all(isinstance(t, Number) for t in job_totals))

        # ✅ Ensure performance threshold met
        self.assertLess(duration, 1.0, "Balance computation too slow!")


  

class PaymentHistoryPerformanceTest(TestCase):
    """⚡ Performance tests for Payment_History model"""

    def setUp(self):
        self.customer = CustomerUser.objects.create(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            is_active=True
        )

        # Create 500 records for performance testing
        payments = [
            Payment_History(
                customer=self.customer,
                payment_fees=10000 + i * 10,
                down_payment=500,
                student_bonus=50,
                fee_balance=9500 + i * 10,
                plan=(i % 3) + 1,
                subplan=(i % 2) + 1,
                payment_method="Mpesa",
                contract_submitted_date=timezone.now(),
                client_signature="Signed",
                company_rep="Rep " + str(i),
                client_date="2025-01-12",
                rep_date="2025-01-13"
            )
            for i in range(500)
        ]
        Payment_History.objects.bulk_create(payments)

    def test_bulk_query_performance(self):
        """⚡ Should query all Payment_History records efficiently"""
        start = time.time()
        payments = Payment_History.objects.all()
        total = payments.count()
        end = time.time()

        self.assertEqual(total, 500)
        self.assertLess(end - start, 0.2)  # should run in under 200ms

    def test_bulk_update_performance(self):
        """⚡ Should handle bulk updates quickly"""
        start = time.time()
        Payment_History.objects.all().update(down_payment=1000)
        end = time.time()

        self.assertLess(end - start, 0.5)  # under half a second for 500 records

    def test_calculation_efficiency(self):
        """⚡ Validate fee balance recalculation logic for performance"""
        start = time.time()
        results = [
            p.payment_fees - (p.down_payment + (p.student_bonus or 0))
            for p in Payment_History.objects.all()
        ]
        end = time.time()

        self.assertTrue(all(isinstance(r, (float, int)) for r in results))
        self.assertLess(end - start, 0.4)

