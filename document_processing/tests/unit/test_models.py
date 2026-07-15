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


class ApplicationModelTest(TestCase):
    """Unit tests for the Application model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
        )

    def _make_application(self, **kwargs):
        defaults = dict(
            user=self.user,
            service="passport",
            first_name="John",
            last_name="Doe",
            id_number="123456789",
            district="Gasabo",
            sub_county="Kimironko",
            reason="Lost passport",
        )
        defaults.update(kwargs)
        return Application.objects.create(**defaults)

    # --- Creation ---------------------------------------------------------
    def test_application_creation(self):
        app = self._make_application()
        self.assertEqual(app.first_name, "John")
        self.assertEqual(app.last_name, "Doe")
        self.assertEqual(app.id_number, "123456789")
        self.assertEqual(app.service, "passport")
        self.assertEqual(app.district, "Gasabo")
        self.assertEqual(app.sub_county, "Kimironko")
        self.assertEqual(app.reason, "Lost passport")

    def test_application_str(self):
        app = self._make_application()
        self.assertIn(str(app.pk), str(app))

    # --- Default values ---------------------------------------------------
    def test_default_status_is_draft(self):
        app = self._make_application()
        self.assertEqual(app.status, "draft")

    def test_default_fee_is_zero(self):
        app = self._make_application()
        self.assertEqual(app.fee, Decimal("0"))

    def test_default_current_step_is_one(self):
        app = self._make_application()
        self.assertEqual(app.current_step, 1)

    def test_default_completion_percentage_is_zero(self):
        app = self._make_application()
        self.assertEqual(app.completion_percentage, 0)

    def test_default_notify_flags_false(self):
        app = self._make_application()
        self.assertFalse(app.notify_by_phone)
        self.assertFalse(app.notify_by_email)

    def test_default_certified_false(self):
        app = self._make_application()
        self.assertFalse(app.certified)

    def test_optional_fields_default_blank(self):
        app = self._make_application()
        self.assertEqual(app.phone, "")
        self.assertEqual(app.email, "")
        self.assertIsNone(app.application_number)
        self.assertIsNone(app.submitted_at)

    # --- Fee handling -----------------------------------------------------
    def test_fee_is_saved_correctly(self):
        app = self._make_application(fee=Decimal("75000.00"))
        self.assertEqual(app.fee, Decimal("75000.00"))

    def test_fee_supports_decimal_precision(self):
        app = self._make_application(fee=Decimal("12345.67"))
        app.refresh_from_db()
        self.assertEqual(app.fee, Decimal("12345.67"))

    # --- Status choices ---------------------------------------------------
    def test_valid_status_choices(self):
        for status, _label in Application.STATUS_CHOICES:
            app = self._make_application(status=status)
            self.assertEqual(app.status, status)
            app.delete()

    def test_invalid_status_rejected_on_full_clean(self):
        app = self._make_application(status="not_a_real_status")
        with self.assertRaises(ValidationError):
            app.full_clean()

    # --- Uniqueness -------------------------------------------------------
    def test_application_number_unique(self):
        self._make_application(application_number="APP-001")
        with self.assertRaises(Exception):
            self._make_application(application_number="APP-001")

    def test_application_number_can_be_null_twice(self):
        a = self._make_application(application_number=None)
        b = self._make_application(application_number=None)
        self.assertIsNone(a.application_number)
        self.assertIsNone(b.application_number)

    # --- Field length constraints -----------------------------------------
    def test_id_number_max_length(self):
        app = self._make_application(id_number="x" * 50)
        app.full_clean()
        app2 = self._make_application(id_number="x" * 51)
        with self.assertRaises(ValidationError):
            app2.full_clean()

    def test_reason_max_length(self):
        app = self._make_application(reason="x" * 255)
        app.full_clean()
        app2 = self._make_application(reason="x" * 256)
        with self.assertRaises(ValidationError):
            app2.full_clean()

    # --- Timestamps -------------------------------------------------------
    def test_created_at_set_on_save(self):
        app = self._make_application()
        self.assertIsNotNone(app.created_at)

    def test_updated_at_changes_on_update(self):
        app = self._make_application()
        old_updated = app.updated_at
        app.first_name = "Jane"
        app.save()
        app.refresh_from_db()
        self.assertNotEqual(app.updated_at, old_updated)

    def test_submitted_at_can_be_set(self):
        now = timezone.now()
        app = self._make_application(submitted_at=now)
        self.assertIsNotNone(app.submitted_at)

    # --- Relationship ------------------------------------------------------
    def test_related_name_document_applications(self):
        app = self._make_application()
        self.assertIn(app, self.user.document_applications.all())

    def test_user_cascade_deletes_applications(self):
        app = self._make_application()
        self.user.delete()
        self.assertFalse(Application.objects.filter(pk=app.pk).exists())


class PaymentModelTest(TestCase):
    """Unit tests for the Payment model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="payuser", password="password123"
        )
        self.application = Application.objects.create(
            user=self.user,
            service="nid_replacement",
            first_name="Jane",
            last_name="Smith",
            id_number="987654321",
            district="Nyarugenge",
            sub_county="Nyamirambo",
            reason="Renewal",
        )

    def _make_payment(self, **kwargs):
        defaults = dict(
            application=self.application,
            method="mtn",
            amount=Decimal("5000.00"),
            bill_id="BILL-001",
        )
        defaults.update(kwargs)
        return Payment.objects.create(**defaults)

    # --- Creation ---------------------------------------------------------
    def test_payment_creation(self):
        payment = self._make_payment()
        self.assertEqual(payment.method, "mtn")
        self.assertEqual(payment.amount, Decimal("5000.00"))
        self.assertEqual(payment.bill_id, "BILL-001")

    # --- Defaults ---------------------------------------------------------
    def test_default_status_is_pending(self):
        payment = self._make_payment()
        self.assertEqual(payment.status, "pending")

    def test_default_transaction_id_null(self):
        payment = self._make_payment()
        self.assertIsNone(payment.transaction_id)

    def test_default_payer_phone_blank(self):
        payment = self._make_payment()
        self.assertEqual(payment.payer_phone, "")

    def test_default_paid_at_null(self):
        payment = self._make_payment()
        self.assertIsNone(payment.paid_at)

    # --- Method choices ---------------------------------------------------
    def test_valid_method_choices(self):
        for method, _label in Payment.METHOD_CHOICES:
            payment = self._make_payment(
                method=method, bill_id=f"BILL-{method}"
            )
            self.assertEqual(payment.method, method)
            payment.delete()

    def test_invalid_method_rejected_on_full_clean(self):
        payment = self._make_payment(method="bitcoin")
        with self.assertRaises(ValidationError):
            payment.full_clean()

    # --- Status choices ---------------------------------------------------
    def test_valid_status_choices(self):
        for status, _label in Payment.STATUS_CHOICES:
            payment = self._make_payment(
                status=status, bill_id=f"BILL-{status}"
            )
            self.assertEqual(payment.status, status)
            payment.delete()

    def test_invalid_status_rejected_on_full_clean(self):
        payment = self._make_payment(status="refunded")
        with self.assertRaises(ValidationError):
            payment.full_clean()

    # --- Uniqueness -------------------------------------------------------
    def test_bill_id_unique(self):
        self._make_payment(bill_id="BILL-DUP")
        with self.assertRaises(Exception):
            self._make_payment(bill_id="BILL-DUP")

    def test_transaction_id_unique_when_set(self):
        self._make_payment(
            bill_id="BILL-A", transaction_id="TXN-A"
        )
        with self.assertRaises(Exception):
            self._make_payment(
                bill_id="BILL-B", transaction_id="TXN-A"
            )

    def test_transaction_id_can_be_null_twice(self):
        a = self._make_payment(bill_id="BILL-N1", transaction_id=None)
        b = self._make_payment(bill_id="BILL-N2", transaction_id=None)
        self.assertIsNone(a.transaction_id)
        self.assertIsNone(b.transaction_id)

    # --- Amount -----------------------------------------------------------
    def test_amount_decimal_precision(self):
        payment = self._make_payment(amount=Decimal("1234.56"))
        payment.refresh_from_db()
        self.assertEqual(payment.amount, Decimal("1234.56"))

    # --- Relationship ------------------------------------------------------
    def test_related_name_payments(self):
        payment = self._make_payment()
        self.assertIn(payment, self.application.payments.all())

    def test_application_cascade_deletes_payments(self):
        payment = self._make_payment()
        self.application.delete()
        self.assertFalse(Payment.objects.filter(pk=payment.pk).exists())


class GeneratedDocumentModelTest(TestCase):
    """Unit tests for the GeneratedDocument model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="docuser", password="password123"
        )
        self.application = Application.objects.create(
            user=self.user,
            service="passport",
            first_name="Mary",
            last_name="Jones",
            id_number="111222333",
            district="Kicukiro",
            sub_county="Kanombe",
            reason="New passport",
        )

    def _make_document(self, **kwargs):
        defaults = dict(
            application=self.application,
            title="Passport PDF",
            file="documents/passport.pdf",
        )
        defaults.update(kwargs)
        return GeneratedDocument.objects.create(**defaults)

    # --- Creation ---------------------------------------------------------
    def test_document_creation(self):
        doc = self._make_document()
        self.assertEqual(doc.title, "Passport PDF")
        self.assertEqual(doc.file, "documents/passport.pdf")

    # --- Defaults ---------------------------------------------------------
    def test_default_status_is_valid(self):
        doc = self._make_document()
        self.assertEqual(doc.status, "valid")

    def test_default_issued_at_set(self):
        doc = self._make_document()
        self.assertIsNotNone(doc.issued_at)

    # --- Status choices ---------------------------------------------------
    def test_valid_status_choices(self):
        for status, _label in GeneratedDocument.STATUS_CHOICES:
            doc = self._make_document(
                title=f"Doc {status}", status=status
            )
            self.assertEqual(doc.status, status)
            doc.delete()

    def test_invalid_status_rejected_on_full_clean(self):
        doc = self._make_document(status="archived")
        with self.assertRaises(ValidationError):
            doc.full_clean()

    # --- Field length ------------------------------------------------------
    def test_title_max_length(self):
        doc = self._make_document(title="x" * 255)
        doc.full_clean()
        doc2 = self._make_document(title="x" * 256)
        with self.assertRaises(ValidationError):
            doc2.full_clean()

    # --- Relationship ------------------------------------------------------
    def test_related_name_documents(self):
        doc = self._make_document()
        self.assertIn(doc, self.application.documents.all())

    def test_application_cascade_deletes_documents(self):
        doc = self._make_document()
        self.application.delete()
        self.assertFalse(GeneratedDocument.objects.filter(pk=doc.pk).exists())


class DataAccessLogModelTest(TestCase):
    """Unit tests for the DataAccessLog model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="loguser", password="password123"
        )

    def _make_log(self, **kwargs):
        defaults = dict(
            user=self.user,
            institution="Ministry of Health",
            data_accessed="citizen_records",
            purpose="Research",
            access_type="view",
        )
        defaults.update(kwargs)
        return DataAccessLog.objects.create(**defaults)

    # --- Creation ---------------------------------------------------------
    def test_log_creation(self):
        log = self._make_log()
        self.assertEqual(log.institution, "Ministry of Health")
        self.assertEqual(log.data_accessed, "citizen_records")
        self.assertEqual(log.purpose, "Research")
        self.assertEqual(log.access_type, "view")

    # --- Defaults ---------------------------------------------------------
    def test_default_created_at_set(self):
        log = self._make_log()
        self.assertIsNotNone(log.created_at)

    # --- Access type choices ----------------------------------------------
    def test_valid_access_type_choices(self):
        for access_type, _label in DataAccessLog.ACCESS_TYPES:
            log = self._make_log(
                institution=f"Inst {access_type}", access_type=access_type
            )
            self.assertEqual(log.access_type, access_type)
            log.delete()

    def test_invalid_access_type_rejected_on_full_clean(self):
        log = self._make_log(access_type="delete")
        with self.assertRaises(ValidationError):
            log.full_clean()

    # --- Field length ------------------------------------------------------
    def test_institution_max_length(self):
        log = self._make_log(institution="x" * 255)
        log.full_clean()
        log2 = self._make_log(institution="x" * 256)
        with self.assertRaises(ValidationError):
            log2.full_clean()

    # --- Relationship ------------------------------------------------------
    def test_related_name_data_access_logs(self):
        log = self._make_log()
        self.assertIn(log, self.user.data_access_logs.all())

    def test_user_cascade_deletes_logs(self):
        log = self._make_log()
        self.user.delete()
        self.assertFalse(DataAccessLog.objects.filter(pk=log.pk).exists())