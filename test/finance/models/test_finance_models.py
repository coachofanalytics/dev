import pytest
from decimal import Decimal
from finance.models import Transaction, Default_Payment_Fees
from accounts.models import CustomerUser


@pytest.mark.django_db
class TestFinanceModels:
    def test_transaction_defaults_and_amount(self):
        user = CustomerUser.objects.create(username='tuser', email='t@example.com')
        tx = Transaction.objects.create(sender=user, amount=Decimal('123.45'), description='test')
        assert tx.total_payment == Decimal('123.45')

    def test_default_payment_fees_str(self):
        dp = Default_Payment_Fees.objects.create()
        assert str(dp) == str(dp.id)
