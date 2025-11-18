import time
import platform
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from finance.models import (
    OverBoughtSold,
    PaymentInformation,
    Default_Payment_Fees,
    PayslipConfig
)

# =====================================================
# OS-Aware Performance Thresholds
# =====================================================

OS_NAME = platform.system().lower()

if "windows" in OS_NAME:
    CREATE_THRESHOLD = 5.0
    QUERY_THRESHOLD = 0.20
else:
    CREATE_THRESHOLD = 2.0
    QUERY_THRESHOLD = 0.05


# =====================================================
# INTEGRATION TESTS — OVERBOUGHT SOLD
# =====================================================

class OverBoughtSoldIntegrationTest(TestCase):

    def setUp(self):
        self.stock1 = OverBoughtSold.objects.create(
            symbol="AAPL",
            description="Apple Inc.",
            last="190.50",
            volume="5000000",
            rsi="72",
            eps="5.9",
            pe="34",
            rank="1",
            profit_margin="25%"
        )

        self.stock2 = OverBoughtSold.objects.create(
            symbol="TSLA",
            description="Tesla Motors",
            last="180.10",
            volume="6000000",
            rsi="28",
            eps="2.5",
            pe="22",
            rank="2",
            profit_margin="10%"
        )

    def test_records_are_saved_with_auto_condition(self):
        self.assertEqual(self.stock1.condition_integer, 1)   # Overbought
        self.assertEqual(self.stock2.condition_integer, -1)  # Oversold

    def test_auto_timestamp_fields(self):
        self.assertIsNotNone(self.stock1.created_at)
        self.assertIsNotNone(self.stock1.updated_at)
        self.assertLessEqual(self.stock1.created_at, timezone.now())

    def test_update_model_changes_updated_at(self):
        old_timestamp = self.stock1.updated_at
        self.stock1.volume = "7000000"
        self.stock1.save()
        self.stock1.refresh_from_db()
        self.assertGreater(self.stock1.updated_at, old_timestamp)

    def test_condition_label_reflects_condition_integer(self):
        self.assertEqual(self.stock1.condition_label(), "Overbought")
        self.assertEqual(self.stock2.condition_label(), "Oversold")

    def test_bulk_create_and_condition_update(self):
        records = [
            OverBoughtSold(symbol="GOOG", rsi="55", volume="4000000"),
            OverBoughtSold(symbol="AMZN", rsi="15", volume="3000000"),
            OverBoughtSold(symbol="META", rsi="80", volume="2500000"),
        ]
        OverBoughtSold.objects.bulk_create(records)

        self.assertEqual(OverBoughtSold.objects.count(), 5)

        for stock in OverBoughtSold.objects.all():
            stock.save()

        meta = OverBoughtSold.objects.get(symbol="META")
        self.assertEqual(meta.condition_label(), "Overbought")


# =====================================================
# INTEGRATION TESTS — PAYMENT INFORMATION
# =====================================================

class PaymentInformationIntegrationTest(TestCase):

    def setUp(self):
        self.payment_data = {
            'payment_fees': 1500,
            'down_payment': 500,
            'student_bonus': 100,
            'fee_balance': 900,
            'plan': "Standard",
            'subplan': "Silver",
            'payment_method': "Mobile Money",
            'contract_submitted_date': timezone.now(),
            'client_signature': "John Doe",
            'company_rep': "Alice M.",
            'client_date': "2025-01-15",
            'description': "First installment",
            'is_active': True,
            'is_featured': False
        }

    def test_payment_information_creation(self):
        p = PaymentInformation.objects.create(**self.payment_data)
        self.assertEqual(p.plan, "Standard")
        self.assertEqual(p.payment_fees, 1500)
        self.assertEqual(str(p), "Standard - Mobile Money")

    def test_payment_information_exists_in_db(self):
        p = PaymentInformation.objects.create(**self.payment_data)
        f = PaymentInformation.objects.get(id=p.id)
        self.assertEqual(f.payment_fees, 1500)

    def test_invalid_payment_information_creation(self):
        invalid = self.payment_data.copy()
        invalid["payment_fees"] = None

        with self.assertRaises(Exception):
            PaymentInformation.objects.create(**invalid)

    def test_payment_information_str(self):
        p = PaymentInformation.objects.create(**self.payment_data)
        self.assertEqual(str(p), "Standard - Mobile Money")


# =====================================================
# INTEGRATION TESTS — DEFAULT PAYMENT FEES
# =====================================================

class DefaultPaymentFeesIntegrationTest(TestCase):

    def setUp(self):
        self.fee = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=500,
            job_plan_hours_per_month=160,
            student_down_payment_per_month=300,
            student_bonus_payment_per_month=150
        )

    def test_integration_creation(self):
        f = Default_Payment_Fees.objects.get(id=self.fee.id)
        self.assertEqual(f.job_down_payment_per_month, 500)

    def test_integration_error_handling(self):
        with self.assertRaises(IntegrityError):
            Default_Payment_Fees.objects.create(
                job_down_payment_per_month=None,
                job_plan_hours_per_month=160,
                student_down_payment_per_month=300,
                student_bonus_payment_per_month=150
            )


# =====================================================
# INTEGRATION TESTS — PAYSLIP CONFIG
# =====================================================

class PayslipConfigIntegrationTests(TestCase):

    def setUp(self):
        self.data = {
            "loan_status": True,
            "loan_amount": Decimal("100000.00"),
            "loan_repayment_percentage": Decimal("10.00"),
            "laptop_status": True,
            "lb_amount": Decimal("30000.00"),
            "ls_amount": Decimal("3500.00"),
            "ls_max_limit": Decimal("40000.00"),
            "rp_starting_period": "Month 1",
            "rp_starting_amount": Decimal("1500.00"),
            "rp_increment_percentage": Decimal("5.00"),
        }

    def test_model_full_lifecycle(self):
        c = PayslipConfig(**self.data)
        c.full_clean()
        c.save()

        c2 = PayslipConfig.objects.get(id=c.id)
        self.assertEqual(c2.loan_amount, Decimal("100000.00"))

        c2.loan_amount = Decimal("80000.00")
        c2.full_clean()
        c2.save()

        c3 = PayslipConfig.objects.get(id=c.id)
        self.assertEqual(c3.loan_amount, Decimal("80000.00"))

        c3.delete()
        self.assertFalse(PayslipConfig.objects.filter(id=c.id).exists())

    def test_negative_values_rejected(self):
        invalid = PayslipConfig(
            loan_status=True,
            loan_amount=Decimal("-10"),
            loan_repayment_percentage=Decimal("10"),
            laptop_status=False,
            lb_amount=Decimal("0"),
            ls_amount=Decimal("0"),
            ls_max_limit=Decimal("0"),
            rp_starting_period="Month 2",
            rp_starting_amount=Decimal("500"),
            rp_increment_percentage=Decimal("2"),
        )

        with self.assertRaises(ValidationError):
            invalid.full_clean()

    def test_multiple_records_consistency(self):
        for i in range(5):
            PayslipConfig.objects.create(
                loan_status=bool(i % 2),
                loan_amount=Decimal(str(10000 * i)),
                loan_repayment_percentage=Decimal("5"),
                laptop_status=False,
                lb_amount=Decimal("0"),
                ls_amount=Decimal("0"),
                ls_max_limit=Decimal("0"),
                rp_starting_period=f"Month {i}",
                rp_starting_amount=Decimal("100"),
                rp_increment_percentage=Decimal("1"),
            )

        all_configs = PayslipConfig.objects.all()
        self.assertEqual(all_configs.count(), 5)

    def test_str_representation(self):
        c = PayslipConfig.objects.create(**self.data)
        text = str(c)
        self.assertIn("Loan Status", text)
        self.assertIn("Laptop Status", text)
