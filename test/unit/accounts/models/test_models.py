from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from accounts.models import CustomerUser, Membership, Department


class CustomerUserModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomerUser.objects.create(
            username='jdoe',
            first_name='John',
            last_name='Doe',
            email='jdoe@example.com',
        )

    def test_full_name_property(self):
        self.assertEqual(self.user.full_name, 'John,Doe')

    def test_user_details_contains_username(self):
        self.assertIn('Username: jdoe', self.user.user_details)

    def test_is_recent_true_for_recent_user(self):
        self.user.date_joined = timezone.now()
        self.user.save()
        self.assertTrue(self.user.is_recent)

    def test_tenure_months_is_numeric(self):
        months = self.user.tenure
        self.assertIsInstance(months, float)


class MembershipModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomerUser.objects.create(username='muser', first_name='M', last_name='U', email='m@example.com')
        cls.membership = Membership.objects.create(member=cls.user, fee=100.00, status='PAID', paid_date=timezone.now())

    def test_str_contains_member_and_status(self):
        self.assertIn('PAID', str(self.membership))

    def test_is_paid_property(self):
        self.assertTrue(self.membership.is_paid)


class DepartmentModelTests(TestCase):
    def test_get_default_pk_creates_default(self):
        pk = Department.get_default_pk()
        self.assertIsInstance(pk, int)
        # Ensure the department exists
        dept = Department.objects.get(pk=pk)
        self.assertEqual(dept.name, 'Other')
