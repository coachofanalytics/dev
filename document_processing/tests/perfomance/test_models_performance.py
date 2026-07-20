"""Performance tests for the Document Processing portal models.

These tests assert that common model operations (bulk creation, querying,
related-name traversal, token generation) stay within acceptable time
budgets so regressions in query volume or save() overhead are caught early.
"""
import time

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from document_processing.models import (
    Application,
    Payment,
    GeneratedDocument,
    DataAccessLog,
)

User = get_user_model()

# Generous time budgets (seconds) for the SQLite test DB.
BULK_BUDGET = 5.0
QUERY_BUDGET = 1.0
SAVE_BUDGET = 1.0


def _make_user(username):
    return User.objects.create_user(username=username, password="password123")


def _make_application(user, idx=0, **kwargs):
    defaults = dict(
        user=user,
        service="passport",
        first_name=f"User{idx}",
        last_name="Test",
        id_number=f"12345{idx % 10}",
        district="gasabo",
        sub_county="Kimironko",
        reason="lost",
        status="submitted",
    )
    defaults.update(kwargs)
    return Application.objects.create(**defaults)


class ApplicationPerformanceTest(TestCase):
    """Performance tests for the Application model."""

    def setUp(self):
        self.user = _make_user("perf_app_user")

    def test_bulk_create_performance(self):
        apps = [
            Application(
                user=self.user,
                service="passport",
                first_name=f"User{i}",
                last_name="Test",
                id_number=f"ID{i:06d}",
                district="gasabo",
                sub_county="Kimironko",
                reason="lost",
            )
            for i in range(1000)
        ]
        start = time.time()
        Application.objects.bulk_create(apps)
        duration = time.time() - start
        self.assertEqual(Application.objects.count(), 1000)
        self.assertLess(duration, BULK_BUDGET)

    def test_individual_save_performance(self):
        start = time.time()
        for i in range(200):
            _make_application(self.user, idx=i)
        duration = time.time() - start
        self.assertEqual(Application.objects.count(), 200)
        self.assertLess(duration, SAVE_BUDGET * 5)

    def test_filtered_query_performance(self):
        for i in range(500):
            _make_application(self.user, idx=i, status="submitted" if i % 2 else "draft")
        start = time.time()
        list(Application.objects.filter(user=self.user, status="submitted"))
        duration = time.time() - start
        self.assertLess(duration, QUERY_BUDGET)

    def test_application_number_generation_is_unique_under_load(self):
        numbers = set()
        start = time.time()
        for i in range(300):
            app = _make_application(self.user, idx=i)
            numbers.add(app.application_number)
        duration = time.time() - start
        self.assertEqual(len(numbers), 300)
        self.assertLess(duration, SAVE_BUDGET * 5)

    def test_service_fee_property_performance(self):
        app = _make_application(self.user, service="national_id_replacement")
        start = time.time()
        for _ in range(1000):
            _ = app.service_fee
        duration = time.time() - start
        self.assertLess(duration, QUERY_BUDGET)


class PaymentPerformanceTest(TestCase):
    """Performance tests for the Payment model."""

    def setUp(self):
        self.user = _make_user("perf_pay_user")
        self.app = _make_application(self.user)

    def test_bulk_create_payments_performance(self):
        payments = [
            Payment(
                application=self.app,
                method="mtn",
                amount=4500,
                bill_id=f"BILL-{i:06d}",
            )
            for i in range(1000)
        ]
        start = time.time()
        Payment.objects.bulk_create(payments)
        duration = time.time() - start
        self.assertEqual(Payment.objects.count(), 1000)
        self.assertLess(duration, BULK_BUDGET)

    def test_related_payments_query_performance(self):
        for i in range(500):
            Payment.objects.create(
                application=self.app,
                method="mtn",
                amount=4500,
                bill_id=f"BILL-Q-{i:06d}",
            )
        start = time.time()
        list(self.app.payments.all())
        duration = time.time() - start
        self.assertLess(duration, QUERY_BUDGET)


class GeneratedDocumentPerformanceTest(TestCase):
    """Performance tests for the GeneratedDocument model."""

    def setUp(self):
        self.user = _make_user("perf_doc_user")
        self.app = _make_application(self.user)

    def test_bulk_create_documents_performance(self):
        docs = [
            GeneratedDocument(
                application=self.app,
                title=f"Doc {i}",
                file=f"documents/doc_{i}.pdf",
            )
            for i in range(1000)
        ]
        start = time.time()
        GeneratedDocument.objects.bulk_create(docs)
        duration = time.time() - start
        self.assertEqual(GeneratedDocument.objects.count(), 1000)
        self.assertLess(duration, BULK_BUDGET)

    def test_secure_token_generation_performance(self):
        start = time.time()
        for i in range(300):
            GeneratedDocument.objects.create(
                application=self.app,
                title=f"Doc {i}",
                file=f"documents/d_{i}.pdf",
            )
        duration = time.time() - start
        self.assertLess(duration, SAVE_BUDGET * 5)

    def test_is_token_valid_property_performance(self):
        doc = GeneratedDocument.objects.create(
            application=self.app, title="Doc", file="documents/d.pdf"
        )
        start = time.time()
        for _ in range(1000):
            _ = doc.is_token_valid
        duration = time.time() - start
        self.assertLess(duration, QUERY_BUDGET)


class DataAccessLogPerformanceTest(TestCase):
    """Performance tests for the DataAccessLog model."""

    def setUp(self):
        self.user = _make_user("perf_log_user")

    def test_bulk_create_logs_performance(self):
        logs = [
            DataAccessLog(
                user=self.user,
                institution="Inst",
                data_accessed=f"data-{i}",
                purpose="perf",
                access_type="view",
            )
            for i in range(2000)
        ]
        start = time.time()
        DataAccessLog.objects.bulk_create(logs)
        duration = time.time() - start
        self.assertEqual(DataAccessLog.objects.count(), 2000)
        self.assertLess(duration, BULK_BUDGET)

    def test_log_access_classmethod_performance(self):
        start = time.time()
        for i in range(500):
            DataAccessLog.log_access(
                user=self.user,
                institution="Inst",
                data_accessed=f"data-{i}",
                purpose="perf",
                access_type="view",
            )
        duration = time.time() - start
        self.assertLess(duration, SAVE_BUDGET * 5)

    def test_filtered_log_query_performance(self):
        for i in range(1000):
            DataAccessLog.log_access(
                user=self.user,
                institution=f"Inst-{i % 5}",
                data_accessed=f"data-{i}",
                purpose="perf",
                access_type="view",
            )
        start = time.time()
        list(DataAccessLog.objects.filter(user=self.user, institution="Inst-1"))
        duration = time.time() - start
        self.assertLess(duration, QUERY_BUDGET)
