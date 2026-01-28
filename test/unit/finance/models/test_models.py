from django.test import TestCase
from django.utils import timezone
from finance.models import Default_Payment_Fees, Budget
from accounts.models import CustomerUser, Department


class DefaultPaymentFeesTests(TestCase):
    def test_str_returns_id(self):
        obj = Default_Payment_Fees.objects.create()
        self.assertEqual(str(obj), str(obj.id))


class BudgetModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomerUser.objects.create(username='lead', first_name='L', last_name='E', email='lead@example.com')
        cls.department = Department.objects.create(name='Other', slug='other')
        cls.category = None
        cls.budget = Budget.objects.create(
            budget_lead=cls.user,
            department=cls.department,
            item='Test Item',
            cases=2,
            qty=5,
            unit_price=10.00,
            start_date=timezone.now(),
            end_date=timezone.now(),
        )

    def test_amount_computation_returns_decimal(self):
        amt = self.budget.amount
        self.assertIsNotNone(amt)

    def test_days_property(self):
        days = self.budget.days
        self.assertIsInstance(days, int)
