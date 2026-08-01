from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Transaction, Tracker, PaymentHistory

User = get_user_model()

from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Transaction, Tracker, PaymentHistory

User = get_user_model()


# class TransactionIntegrationModelTest(TestCase):
#     """Integration tests for the Transaction model."""

#     def setUp(self):
#         self.transaction = Transaction.objects.create(
#             sender=None,
#             department="Finance",
#             receiver="CODA Analytics",
#             phone="+254712345678",
#             type="Income",
#             activity_date=timezone.now(),
#             receipt_link="https://example.com/receipts/TRX-001",
#             qty=Decimal("2.00"),
#             amount=Decimal("5000.00"),
#             transaction_cost=Decimal("50.00"),
#             description="Payment for consulting services.",
#             payment_method="MPESA",
#         )

#     def test_transaction_is_created(self):
#         """A transaction should be saved successfully."""
#         self.assertEqual(Transaction.objects.count(), 1)
#         self.assertEqual(self.transaction.department, "Finance")
#         self.assertEqual(self.transaction.receiver, "CODA Analytics")
#         self.assertEqual(self.transaction.type, "Income")
#         self.assertEqual(self.transaction.payment_method, "MPESA")

#     def test_default_transaction_type(self):
#         """The default transaction type should be Other."""
#         transaction = Transaction.objects.create(
#             receiver="Test Receiver",
#             amount=Decimal("1000.00"),
#         )
#         self.assertEqual(transaction.type, "Other")

#     def test_default_payment_method(self):
#         """The default payment method should be Cash."""
#         transaction = Transaction.objects.create(
#             receiver="Test Receiver",
#             amount=Decimal("1000.00"),
#         )
#         self.assertEqual(transaction.payment_method, "Cash")

#     def test_default_transaction_cost(self):
#         """The default transaction cost should be zero."""
#         transaction = Transaction.objects.create(
#             receiver="Test Receiver",
#             amount=Decimal("1000.00"),
#         )
#         self.assertEqual(
#             transaction.transaction_cost,
#             Decimal("0.00"),
#         )

#     def test_total_amount_property(self):
#         """Total amount should include the transaction cost."""
#         self.assertEqual(
#             self.transaction.total_amount,
#             Decimal("5050.00"),
#         )

#     def test_total_amount_when_amount_is_null(self):
#         """A missing amount should be treated as zero."""
#         transaction = Transaction.objects.create(
#             receiver="Test Receiver",
#             amount=None,
#             transaction_cost=Decimal("25.00"),
#         )
#         self.assertEqual(
#             transaction.total_amount,
#             Decimal("25.00"),
#         )

#     def test_total_amount_when_cost_is_zero(self):
#         """The total should equal the amount when cost is zero."""
#         transaction = Transaction.objects.create(
#             receiver="Test Receiver",
#             amount=Decimal("2500.00"),
#             transaction_cost=Decimal("0.00"),
#         )
#         self.assertEqual(
#             transaction.total_amount,
#             Decimal("2500.00"),
#         )

#     def test_string_representation(self):
#         """The model should return a readable string."""
#         self.assertEqual(
#             str(self.transaction),
#             "Income - 5000.00 - MPESA",
#         )

#     def test_activity_date_has_default_value(self):
#         """Activity date should be generated automatically."""
#         transaction = Transaction.objects.create(
#             receiver="Test Receiver",
#             amount=Decimal("500.00"),
#         )
#         self.assertIsNotNone(transaction.activity_date)

#     def test_created_and_updated_dates_are_generated(self):
#         """Created and updated timestamps should be populated."""
#         self.assertIsNotNone(self.transaction.created_at)
#         self.assertIsNotNone(self.transaction.updated_at)

#     def test_optional_fields_can_be_null(self):
#         """Optional fields should accept null values."""
#         transaction = Transaction.objects.create(
#             sender=None,
#             department=None,
#             receiver=None,
#             phone=None,
#             receipt_link=None,
#             qty=None,
#             amount=None,
#             description=None,
#         )
#         self.assertIsNone(transaction.sender)
#         self.assertIsNone(transaction.department)
#         self.assertIsNone(transaction.receiver)
#         self.assertIsNone(transaction.phone)
#         self.assertIsNone(transaction.receipt_link)
#         self.assertIsNone(transaction.qty)
#         self.assertIsNone(transaction.amount)
#         self.assertIsNone(transaction.description)

#     def test_invalid_payment_method_fails_validation(self):
#         """An unsupported payment method should fail validation."""
#         transaction = Transaction(
#             receiver="Test Receiver",
#             amount=Decimal("100.00"),
#             payment_method="Bitcoin",
#         )
#         with self.assertRaises(ValidationError):
#             transaction.full_clean()

#     def test_invalid_transaction_type_fails_validation(self):
#         """An unsupported transaction type should fail validation."""
#         transaction = Transaction(
#             receiver="Test Receiver",
#             amount=Decimal("100.00"),
#             type="Unknown Type",
#         )
#         with self.assertRaises(ValidationError):
#             transaction.full_clean()

#     def test_transactions_are_ordered_by_activity_date(self):
#         """The latest transaction should appear first."""
#         old_transaction = Transaction.objects.create(
#             receiver="Old Receiver",
#             amount=Decimal("100.00"),
#             activity_date=timezone.now() - timedelta(days=2),
#         )
#         new_transaction = Transaction.objects.create(
#             receiver="New Receiver",
#             amount=Decimal("200.00"),
#             activity_date=timezone.now() + timedelta(days=1),
#         )
#         transactions = list(Transaction.objects.all())
#         self.assertEqual(transactions[0], new_transaction)
#         self.assertIn(old_transaction, transactions)