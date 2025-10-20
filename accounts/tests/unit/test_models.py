from django.test import TestCase
from django.utils import timezone
from accounts.models import All_transaction, Transaction, CustomerUser,PaymentInformation

class AllTransactionModelTest(TestCase):
    """✅ Tests for the All_transaction model."""

    def setUp(self):
        self.income = All_transaction.objects.create(
            type='INCOME',
            category='Donations',
            amount=5000.00,
            payment_method='Bank Transfer',
            description='Donation from community members'
        )

        self.expense = All_transaction.objects.create(
            type='EXPENSE',
            category='Utilities',
            amount=1500.00,
            payment_method='Credit Card',
            description='Electricity and internet bills'
        )

    def test_all_transaction_creation(self):
        """✅ Checks creation of All_transaction records."""
        self.assertEqual(All_transaction.objects.count(), 2)
        self.assertEqual(self.income.type, 'INCOME')
        self.assertEqual(self.expense.category, 'Utilities')

    def test_all_transaction_str(self):
        """✅ Verifies string representation."""
        self.assertEqual(str(self.income), f"{self.income.category} - {self.income.amount}")
        self.assertEqual(str(self.expense), f"{self.expense.category} - {self.expense.amount}")


class TransactionModelTest(TestCase):
    """✅ Test suite for the Transaction model."""

    def setUp(self):
        # Create a mock sender (staff user)
        self.sender = CustomerUser.objects.create(
            username="finance_staff",
            email="staff@coda.com",
            is_staff=True,
            is_active=True
        )

        # Create a sample transaction record
        self.transaction = Transaction.objects.create(
            sender=self.sender,
            receiver="John Doe",
            phone="0712345678",
            type="EXPENSE",
            activity_date=timezone.now(),
            receipt_link="receipt_001.pdf",
            qty=2,
            amount=1500.00,
            transaction_cost=50.00,
            description="Laptop purchase for new staff",
            payment_method="Bank_Transfer",
            category="Labour"
        )

    # ------------------------
    # BASIC TESTS
    # ------------------------
    def test_transaction_creation(self):
        """✅ Transaction object is created successfully."""
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(self.transaction.receiver, "John Doe")
        self.assertEqual(self.transaction.payment_method, "Bank_Transfer")
        self.assertEqual(self.transaction.category, "Labour")

    def test_string_representation(self):
        """✅ __str__ method returns human-readable info."""
        expected_str = f"{self.transaction.category} - {self.transaction.amount} ({self.transaction.payment_method})"
        self.assertEqual(str(self.transaction), expected_str)

    # ------------------------
    # COMPUTED FIELD TESTS
    # ------------------------
    def test_total_transactions_amount_computation(self):
        """✅ total_transactions_amt property returns correct value."""
        expected_total = self.transaction.amount * self.transaction.qty
        self.assertEqual(self.transaction.total_transactions_amt, expected_total)

    def test_total_transactions_amount_handles_null_qty(self):
        """✅ Handles missing qty gracefully."""
        t = Transaction.objects.create(
            sender=self.sender,
            receiver="Jane Smith",
            amount=1000.00,
            qty=None
        )
        self.assertEqual(t.total_transactions_amt, 1000.00)

    # ------------------------
    # META AND ORDER TESTS
    # ------------------------
    def test_default_ordering(self):
        """✅ Transactions are ordered by -activity_date."""
        t2 = Transaction.objects.create(
            sender=self.sender,
            receiver="Alex Mwangi",
            amount=500.00,
            qty=1,
            activity_date=timezone.now() + timezone.timedelta(days=1)
        )
        transactions = Transaction.objects.all()
        self.assertEqual(transactions.first(), t2)

    def test_verbose_name_plural(self):
        """✅ Meta verbose_name_plural is correct."""
        self.assertEqual(Transaction._meta.verbose_name_plural, "Transactions")




class PaymentInformationModelTest(TestCase):
    """✅ Unit tests for the PaymentInformation model."""

    def setUp(self):
        """Set up reusable test data."""
        # Create a mock user to act as customer/student
        self.customer = CustomerUser.objects.create(
            username="john_doe",
            email="john@example.com",
            is_active=True,
        )

        # Create sample payment record
        self.payment = PaymentInformation.objects.create(
            customer_id=self.customer,
            student=self.customer,
            payment_fees=10000.00,
            down_payment=2000.00,
            student_bonus=500.00,
            plan=1,
            subplan=None,
            payment_method="Mpesa",
            contract_submitted_date=timezone.now(),
            client_signature="John Signature",
            company_rep="Chris Maghas",
            client_date="2025-10-20",
            rep_date="2025-10-21",
        )

    # --------------------------
    # BASIC MODEL TESTS
    # --------------------------
    def test_payment_creation(self):
        """✅ Payment record should be created successfully."""
        self.assertEqual(PaymentInformation.objects.count(), 1)
        self.assertEqual(self.payment.payment_method, "Mpesa")
        self.assertEqual(self.payment.customer_id.email, "john@example.com")

    def test_string_representation(self):
        """✅ __str__ method returns a readable output."""
        expected_str = f"Payment by {self.payment.customer_id} - {self.payment.payment_method} ({self.payment.payment_fees})"
        self.assertEqual(str(self.payment), expected_str)

    def test_default_ordering(self):
        """✅ Model should order records by -contract_submitted_date."""
        newer_payment = PaymentInformation.objects.create(
            customer_id=self.customer,
            student=self.customer,
            payment_fees=5000.00,
            down_payment=500.00,
            plan=2,
            payment_method="Cash",
            client_signature="John Signature",
            company_rep="Rep",
        )
        payments = PaymentInformation.objects.all()
        self.assertEqual(payments.first(), newer_payment)

    # --------------------------
    # COMPUTED PROPERTIES TESTS
    # --------------------------
    def test_student_balance_computation(self):
        """✅ student_balance property computes correctly."""
        expected_balance = 10000.00 - (2000.00 + 500.00)
        self.assertEqual(float(self.payment.student_balance), expected_balance)

    def test_jobsupport_balance_computation(self):
        """✅ jobsupport_balance property computes correctly."""
        expected_balance = 10000.00 - 2000.00
        self.assertEqual(float(self.payment.jobsupport_balance), expected_balance)

    def test_balance_handles_missing_values(self):
        """✅ Gracefully handles missing or null values."""
        p = PaymentInformation.objects.create(
            customer_id=self.customer,
            student=self.customer,
            payment_fees=5000.00,
            down_payment=None,
            plan=3,
            payment_method="Other",
            client_signature="NA",
            company_rep="NA",
        )
        self.assertIsNotNone(p.student_balance)
        self.assertIsNotNone(p.jobsupport_balance)

