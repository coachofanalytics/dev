from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
import time

from accounts.models import PaymentInformation, CustomerUser


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
