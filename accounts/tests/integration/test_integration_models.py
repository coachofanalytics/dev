# accounts/tests/test_integration_model.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import LoginHistory
from accounts.models import Tracker
# accounts/tests/integration/test_integration_model.py

from django.utils import timezone



from accounts.models import CustomerUser, LoginHistory, Tracker,Transaction


from django.test import TestCase
from django.utils import timezone

from accounts.models import (
    CustomerUser,
    LoginHistory,
    Tracker,
)

User = get_user_model()
User = get_user_model()


# class PaymentHistoryIntegrationTest(TestCase):

#     def test_user_payment_history_relationship(self):
#         user = User.objects.create_user(
#             username="integrationuser",
#             email="integration@example.com",
#             password="password123"
#         )

#         Payment_History.objects.create(
#             customer=user,
#             payment_fees=4000,
#             down_payment=500,
#             plan=1,
#             payment_method="Card",
#             client_signature="Client",
#             company_rep="Company"
#         )

#         self.assertEqual(user.payment_history.count(), 1)




# User = get_user_model()


class LoginHistoryIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="integration_user",
            email="integration@test.com",
            password="strong-password"
        )

    def test_login_history_is_created_and_saved(self):
        history = LoginHistory.objects.create(
            user=self.user,
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0 Integration Test"
        )

        self.assertEqual(LoginHistory.objects.count(), 1)
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.ip_address, "192.168.1.10")
        self.assertIsNotNone(history.login_time)

    def test_related_name_login_history(self):
        LoginHistory.objects.create(user=self.user)
        LoginHistory.objects.create(user=self.user)

        self.assertEqual(self.user.login_history.count(), 2)

    def test_model_ordering_latest_first(self):
        old = LoginHistory.objects.create(
            user=self.user,
            login_time=timezone.now() - timezone.timedelta(hours=2)
        )
        latest = LoginHistory.objects.create(user=self.user)

        logs = LoginHistory.objects.all()
        self.assertEqual(logs.first(), latest)
        self.assertEqual(logs.last(), old)

    def test_string_representation(self):
        history = LoginHistory.objects.create(user=self.user)
        self.assertIn("logged in at", str(history))





class TrackerModelIntegrationTest(TestCase):
    """
    Integration tests for Tracker model.
    These tests validate interaction between
    model, database, and ORM together.
    """

    def test_tracker_full_creation_and_retrieval(self):
        """
        Ensure Tracker can be created, saved,
        and retrieved correctly from the database.
        """
        tracker = Tracker.objects.create(
            category="Training",
            sub_category="Data Analysis",
            plan="Monthly Plan",
            empname=201,
            author=2,
            employee="Alice Njeri",
            login_date=timezone.now(),
            start_time=timezone.now().time(),
            duration=90,
            time=90,
        )

        fetched_tracker = Tracker.objects.get(id=tracker.id)

        self.assertEqual(fetched_tracker.category, "Training")
        self.assertEqual(fetched_tracker.sub_category, "Data Analysis")
        self.assertEqual(fetched_tracker.plan, "Monthly Plan")
        self.assertEqual(fetched_tracker.empname, 201)
        self.assertEqual(fetched_tracker.author, 2)
        self.assertEqual(fetched_tracker.employee, "Alice Njeri")
        self.assertEqual(fetched_tracker.duration, 90)
        self.assertEqual(fetched_tracker.time, 90)

    def test_tracker_query_filtering(self):
        """
        Ensure Tracker filtering works correctly
        at database level.
        """
        Tracker.objects.bulk_create([
            Tracker(
                category="IT",
                sub_category="Maintenance",
                plan="Weekly",
                empname=i,
                author=1,
                employee=f"Employee {i}",
                login_date=timezone.now(),
                start_time=timezone.now().time(),
                duration=60,
                time=60,
            )
            for i in range(1, 6)
        ])

        it_trackers = Tracker.objects.filter(category="IT")

        self.assertEqual(it_trackers.count(), 5)
def test_tracker_relationship(self):
        tracker = Tracker.objects.create(
        customer=self.user,
        action="login",
        description="User logged in",
    )
        self.assertEqual(tracker.customer, self.user)


        second = Tracker.objects.create(
            category="Ops",
            sub_category="Reporting",
            plan="Daily",
            empname=302,
            author=3,
            employee="Second User",
            login_date=timezone.now(),
            start_time=timezone.now().time(),
            duration=45,
            time=45,
        )

        trackers = Tracker.objects.order_by("login_date")
        self.assertEqual(trackers.first().id, 'first.id')
        self.assertEqual(trackers.last().id, second.id)

class AccountIntegrationModelTests(TestCase):
    """
    Integration tests for accounts models.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomerUser.objects.create_user(
            username="integration_user",
            email="integration@test.com",
            password="StrongPass123!",
            first_name="Integration",
            last_name="User",
        )

    def test_customer_user_created(self):
        user = CustomerUser.objects.get(username="integration_user")
        self.assertEqual(user.first_name, "Integration")
        self.assertTrue(user.check_password("StrongPass123!"))

    def test_login_history_relationship(self):
        login = LoginHistory.objects.create(
            user=self.user,
            ip_address="127.0.0.1",
            user_agent="Django Test Client",
            login_time=timezone.now(),
        )
        self.assertEqual(login.user, self.user)

    def test_tracker_relationship(self):
        tracker = Tracker.objects.create(
            user=self.user,
            action="login",
            description="User logged in",
            timestamp=timezone.now(),
        )
        self.assertEqual(tracker.user, self.user)








from django.test import TestCase
from django.db import IntegrityError
from departments.models import Department


class DepartmentIntegrationTests(TestCase):
    """Integration tests for Department model with database"""

    def test_create_department_and_retrieve(self):
        dept = Department.objects.create(
            description="Finance and accounting department",
            slug="finance",
            is_featured=True,
            is_active=True
        )

        fetched = Department.objects.get(slug="finance")

        self.assertEqual(fetched.id, dept.id)
        self.assertEqual(fetched.description, dept.description)
        self.assertTrue(fetched.is_featured)
        self.assertTrue(fetched.is_active)

    def test_department_slug_uniqueness_constraint(self):
        Department.objects.create(
            description="Human Resources",
            slug="hr"
        )

        with self.assertRaises(IntegrityError):
            Department.objects.create(
                description="Duplicate HR",
                slug="hr"
            )

    def test_multiple_departments_querying(self):
        Department.objects.create(
            description="IT Department",
            slug="it",
            is_featured=False
        )

        Department.objects.create(
            description="Operations Department",
            slug="operations",
            is_featured=True
        )

        featured = Department.objects.filter(is_featured=True)

        self.assertEqual(featured.count(), 1)
        self.assertEqual(featured.first().slug, "operations")

    def test_soft_active_flag_behavior(self):
        inactive_dept = Department.objects.create(
            description="Archived Department",
            slug="archived",
            is_active=False
        )

        active_departments = Department.objects.filter(is_active=True)

        self.assertNotIn(inactive_dept, active_departments)

    def test_string_representation_integration(self):
        dept = Department.objects.create(
            description="Legal Department",
            slug="legal"
        )

        self.assertEqual(str(dept), "legal")



















