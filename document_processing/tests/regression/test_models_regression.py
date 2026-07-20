"""Regression tests for the Document Processing portal models.

These tests lock in behaviour that must not change between releases:
field constraints, choices validation, cascade deletes, token generation,
and the log_access() helper. They protect against accidental schema or
behaviour regressions.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
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


def _make_user(username):
    return User.objects.create_user(username=username, password="password123")


def _make_application(user, **kwargs):
    defaults = dict(
        user=user,
        service="passport",
        first_name="John",
        last_name="Doe",
        id_number="1234567",
        district="gasabo",
        sub_county="Kimironko",
        reason="lost",
    )
    defaults.update(kwargs)
    return Application.objects.create(**defaults)


class ApplicationRegressionTest(TestCase):
    """Regression tests for the Application model."""

    def setUp(self):
        self.user = _make_user("reg_app_user")

    def test_invalid_service_type_rejected(self):
        app = Application(
            user=self.user,
            service="invalid_service",
            first_name="John",
            last_name="Doe",
            id_number="1234567",
            district="gasabo",
            sub_county="Kimironko",
            reason="lost",
        )
        with self.assertRaises(ValidationError):
            app.full_clean()

    def test_invalid_district_rejected(self):
        app = _make_application(self.user, district="not_a_district")
        with self.assertRaises(ValidationError):
            app.full_clean()

    def test_invalid_reason_rejected(self):
        app = _make_application(self.user, reason="not_a_reason")
        with self.assertRaises(ValidationError):
            app.full_clean()

    def test_application_number_auto_generated_and_prefixed(self):
        app = _make_application(self.user)
        self.assertIsNotNone(app.application_number)
        self.assertTrue(app.application_number.startswith("DC48-"))

    def test_application_number_stable_after_reload(self):
        app = _make_application(self.user)
        number = app.application_number
        app.first_name = "Jane"
        app.save()
        app.refresh_from_db()
        self.assertEqual(app.application_number, number)

    def test_is_draft_property(self):
        draft = _make_application(self.user, status="draft")
        submitted = _make_application(self.user, status="submitted")
        self.assertTrue(draft.is_draft)
        self.assertFalse(submitted.is_draft)

    def test_applicant_name_property(self):
        app = _make_application(self.user, first_name="Jane", last_name="Doe")
        self.assertEqual(app.applicant_name, "Jane Doe")

    def test_service_fee_property_uses_fee_table(self):
        app = _make_application(self.user, service="national_id_replacement")
        self.assertEqual(app.service_fee, 1500)

    def test_service_fee_property_falls_back_to_fee_field(self):
        # Use a service absent from SERVICE_FEES so the fee field is used.
        app = _make_application(self.user, service="custom_service", fee=Decimal("9999"))
        self.assertEqual(app.service_fee, 9999)

    def test_payment_property_returns_latest(self):
        app = _make_application(self.user)
        p1 = Payment.objects.create(
            application=app, method="mtn", amount=4500, bill_id="BILL-1"
        )
        p2 = Payment.objects.create(
            application=app, method="airtel", amount=4500, bill_id="BILL-2"
        )
        self.assertEqual(app.payment, p2)
        self.assertEqual(app.payment_status, "pending")

    def test_user_cascade_deletes_applications(self):
        app = _make_application(self.user)
        self.user.delete()
        self.assertFalse(Application.objects.filter(pk=app.pk).exists())

    def test_str_includes_application_number(self):
        app = _make_application(self.user)
        self.assertIn(app.application_number, str(app))


class PaymentRegressionTest(TestCase):
    """Regression tests for the Payment model."""

    def setUp(self):
        self.user = _make_user("reg_pay_user")
        self.app = _make_application(self.user)

    def test_invalid_method_rejected(self):
        pay = Payment(
            application=self.app,
            method="bitcoin",
            amount=4500,
            bill_id="BILL-X",
        )
        with self.assertRaises(ValidationError):
            pay.full_clean()

    def test_invalid_status_rejected(self):
        pay = Payment(
            application=self.app,
            method="mtn",
            amount=4500,
            bill_id="BILL-X",
            status="refunded",
        )
        with self.assertRaises(ValidationError):
            pay.full_clean()

    def test_bill_id_unique_enforced(self):
        Payment.objects.create(
            application=self.app, method="mtn", amount=4500, bill_id="BILL-DUP"
        )
        with self.assertRaises(Exception):
            Payment.objects.create(
                application=self.app, method="airtel", amount=4500, bill_id="BILL-DUP"
            )

    def test_transaction_id_unique_when_set(self):
        Payment.objects.create(
            application=self.app,
            method="mtn",
            amount=4500,
            bill_id="BILL-A",
            transaction_id="TXN-A",
        )
        with self.assertRaises(Exception):
            Payment.objects.create(
                application=self.app,
                method="airtel",
                amount=4500,
                bill_id="BILL-B",
                transaction_id="TXN-A",
            )

    def test_transaction_id_can_be_null_twice(self):
        a = Payment.objects.create(
            application=self.app, method="mtn", amount=4500,
            bill_id="BILL-N1", transaction_id=None
        )
        b = Payment.objects.create(
            application=self.app, method="airtel", amount=4500,
            bill_id="BILL-N2", transaction_id=None
        )
        self.assertIsNone(a.transaction_id)
        self.assertIsNone(b.transaction_id)

    def test_application_cascade_deletes_payments(self):
        pay = Payment.objects.create(
            application=self.app, method="mtn", amount=4500, bill_id="BILL-C"
        )
        self.app.delete()
        self.assertFalse(Payment.objects.filter(pk=pay.pk).exists())


class GeneratedDocumentRegressionTest(TestCase):
    """Regression tests for the GeneratedDocument model."""

    def setUp(self):
        self.user = _make_user("reg_doc_user")
        self.app = _make_application(self.user)

    def test_secure_token_generated_on_save(self):
        doc = GeneratedDocument.objects.create(
            application=self.app, title="Doc", file="documents/d.pdf"
        )
        self.assertTrue(doc.secure_token)
        self.assertIsNotNone(doc.token_expires_at)

    def test_token_expiry_is_24h(self):
        doc = GeneratedDocument.objects.create(
            application=self.app, title="Doc", file="documents/d.pdf"
        )
        delta = doc.token_expires_at - doc.issued_at
        self.assertAlmostEqual(delta.total_seconds(), 24 * 3600, delta=60)

    def test_is_token_valid_true_when_fresh(self):
        doc = GeneratedDocument.objects.create(
            application=self.app, title="Doc", file="documents/d.pdf"
        )
        self.assertTrue(doc.is_token_valid)

    def test_is_token_valid_false_when_expired(self):
        doc = GeneratedDocument.objects.create(
            application=self.app, title="Doc", file="documents/d.pdf"
        )
        doc.token_expires_at = timezone.now() - timezone.timedelta(hours=1)
        doc.save()
        self.assertFalse(doc.is_token_valid)

    def test_invalid_status_rejected(self):
        doc = GeneratedDocument.objects.create(
            application=self.app, title="Doc", file="documents/d.pdf"
        )
        doc.status = "archived"
        with self.assertRaises(ValidationError):
            doc.full_clean()

    def test_application_cascade_deletes_documents(self):
        doc = GeneratedDocument.objects.create(
            application=self.app, title="Doc", file="documents/d.pdf"
        )
        self.app.delete()
        self.assertFalse(GeneratedDocument.objects.filter(pk=doc.pk).exists())


class DataAccessLogRegressionTest(TestCase):
    """Regression tests for the DataAccessLog model."""

    def setUp(self):
        self.user = _make_user("reg_log_user")

    def test_log_access_creates_record(self):
        log = DataAccessLog.log_access(
            user=self.user,
            institution="Ministry",
            data_accessed="records",
            purpose="audit",
            access_type="view",
        )
        self.assertEqual(DataAccessLog.objects.count(), 1)
        self.assertEqual(log.institution, "Ministry")

    def test_invalid_access_type_rejected(self):
        log = DataAccessLog(
            user=self.user,
            institution="Ministry",
            data_accessed="records",
            purpose="audit",
            access_type="delete",
        )
        with self.assertRaises(ValidationError):
            log.full_clean()

    def test_user_cascade_deletes_logs(self):
        DataAccessLog.log_access(
            user=self.user,
            institution="Ministry",
            data_accessed="records",
            purpose="audit",
            access_type="view",
        )
        self.user.delete()
        self.assertEqual(DataAccessLog.objects.count(), 0)

    def test_str_format(self):
        log = DataAccessLog.log_access(
            user=self.user,
            institution="Ministry",
            data_accessed="records",
            purpose="audit",
            access_type="view",
        )
        self.assertIn("Ministry", str(log))
        self.assertIn("records", str(log))
