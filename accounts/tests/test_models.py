from django.test import TestCase
from django.urls import reverse
import datetime 


    # import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.models import PaymentHistory


from accounts.models import Tracker
from datetime import datetime, time

# User = get_user_model()


# # class TestDepartmentModel(TestCase):
# #     def setUp(self):
# #         self.department_obj = Department.objects.create(name='HR Department', slug='test_hr_department')
        

# #     # def test_department_name(self):
# #     #     self.assertEqual(self.department.name, 'Test Department')

# #     def test_model_str(self):
        
# #         self.assertTrue(isinstance(self.department_obj, Department))
# #         self.assertEqual(str(self.department_obj.name), 'HR Department')

# #     # def test_model_get_by_id(self):
# #     #     import pdb; pdb.set_trace()
# #     #     fetch_department_by_id = Department.objects.get_by_id(self.department_obj.id)

# #     #     self.assertTrue(fetch_department_by_id, 1)
    
# #     def test_model_get_by_wrong_id(self):
        
# #         fetch_department_by_id = Department.objects.get_by_id(20)

# #         self.assertEquals(fetch_department_by_id, None)


# class TestTaskGroups(TestCase):

#     def test_model_str(self):
#         title = TaskGroups.objects.create(title='Group X')
#         description = TaskGroups.objects.create(description='Dummy Description For Group X')
#         self.assertEqual(str(title), 'Group X')

# class TestTrackerModel(TestCase):

#     def test_model_create(self):
#         self.category = "Interview"
#         self.task = "database"
#         self.duration = 10
#         tracker = Tracker.objects.create(
#             category=self.category,
#             task=self.task,
#             )

#     # def test_model_url(self):
#     #     tracker = self.test_model_create()
#     #     response = self.client.post(reverse('usertime', args=['johndoee']))
#     #     self.assertEqual(response.status_code, 200)

# class TestCredentialCategory(TestCase):

#     def test_model_str(self):
#         self.category = CredentialCategory.objects.create(category='Test Category',slug='test-category',description='Test Description')
#         self.assertEqual(str(self.category), 'Test Category')

#     # def test_model_url(self):
#     #     self.category = CredentialCategory.objects.create(category='Test Category',slug='test-category',description='Test Description')
#     #     response = self.client.post(reverse('management:credentialcategorylist', args=["test-category"])) #set unit_view to the url name in the urls.py
#     #     self.assertEqual(response.status_code, 200)

# # class TestCredential(TestCase):

#     def test_model_str(self):
#         self.user =  CustomerUser.objects.create(
#             first_name='John',
#             last_name='Doe',
#             email= 'johndoe@gmail.com',
#             gender='1',
#             is_staff=True,
#             is_active=True,
#             )
#         self.credential = Credential.objects.create(
#             added_by=self.user,
#             name='Test Credential',
#             slug='test-credential',
#             description='Test Description')
#         self.assertEqual(str(self.credential), 'Test Credential')

    # def test_model_url(self):
    #     self.category = CredentialCategory.objects.create(category='Test Category',slug='test-category',description='Test Description')
    #     self.user =  CustomerUser.objects.create(
    #         first_name='John',
    #         last_name='Doe',
    #         email= 'johndoe@gmail.com',
    #         gender='1',
    #         is_employee=True,
    #         is_active=True,
    #         )
    #     self.credential = Credential.objects.create(
    #         added_by=self.user,
    #         name='Test Credential',
    #         slug='test-credential',
    #         description='Test Description')
    #     response = self.client.post(reverse('management:credential'))
    #     self.assertEqual(response.status_code, 200)






# @pytest.mark.django_db
class TestPaymentHistoryModel:

    def setup_method(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )

        self.payment = PaymentHistory.objects.create(
            user=self.user,
            purpose="Contribution",
            reference_code="TEST-001",
            amount=100.00,
            currency="USD",
            provider="stripe",
            payment_method="Card",
            status="initiated"
        )

    # ---------------------------------------------------
    # Creation Tests
    # ---------------------------------------------------

    def test_payment_created_successfully(self):
        assert self.payment.id is not None
        assert self.payment.amount == 100.00
        assert self.payment.currency == "USD"
        assert self.payment.status == "initiated"

    def test_string_representation(self):
        expected = f"TEST-001 | 100.00 USD | stripe | initiated"
        assert str(self.payment) == expected

    # ---------------------------------------------------
    # Default Values Tests
    # ---------------------------------------------------

    def test_default_transaction_fee(self):
        assert self.payment.transaction_fee == 0

    def test_completed_at_is_none_initially(self):
        assert self.payment.completed_at is None

    # ---------------------------------------------------
    # Business Logic Tests
    # ---------------------------------------------------

    def test_mark_succeeded_updates_status(self):
        self.payment.mark_succeeded()
        self.payment.refresh_from_db()

        assert self.payment.status == "succeeded"
        assert self.payment.completed_at is not None
        assert self.payment.net_amount == 100.00

    def test_mark_succeeded_calculates_net_amount(self):
        self.payment.transaction_fee = 10
        self.payment.save()

        self.payment.mark_succeeded()
        self.payment.refresh_from_db()

        assert self.payment.net_amount == 90.00

    def test_mark_failed_updates_status(self):
        self.payment.mark_failed("Card declined")
        self.payment.refresh_from_db()

        assert self.payment.status == "failed"
        assert "Card declined" in self.payment.notes

    # ---------------------------------------------------
    # Integrity Tests
    # ---------------------------------------------------

    def test_provider_payment_id_can_be_saved(self):
        self.payment.provider_payment_id = "pi_12345"
        self.payment.save()
        self.payment.refresh_from_db()

        assert self.payment.provider_payment_id == "pi_12345"

    def test_currency_choices_validation(self):
        valid_currencies = [choice[0] for choice in PaymentHistory.Currency.choices]
        assert "USD" in valid_currencies
        assert "KES" in valid_currencies




class TrackerModelTest(TestCase):

    def setUp(self):
        self.tracker = Tracker.objects.create(
            category="Finance",
            sub_category="Payments",
            plan="Premium Plan",
            empname=101,
            author=1,
            employee="John Doe",
            login_date=datetime(2026, 3, 5, 9, 0, 0),
            start_time=time(9, 0, 0),
            duration=120
        )

    def test_tracker_creation(self):
        """Test if tracker object is created correctly"""
        self.assertEqual(self.tracker.category, "Finance")
        self.assertEqual(self.tracker.sub_category, "Payments")
        self.assertEqual(self.tracker.plan, "Premium Plan")

    def test_employee_fields(self):
        """Test employee related fields"""
        self.assertEqual(self.tracker.empname, 101)
        self.assertEqual(self.tracker.author, 1)
        self.assertEqual(self.tracker.employee, "John Doe")

    def test_time_fields(self):
        """Test time and duration fields"""
        self.assertEqual(self.tracker.duration, 120)
        self.assertEqual(self.tracker.start_time, time(9, 0, 0))

    def test_string_representation(self):
        """Test __str__ method"""
        expected = f"{self.tracker.employee} - {self.tracker.category} - {self.tracker.login_date}"
        self.assertEqual(str(self.tracker), expected)


        from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Transaction


class TransactionModelTest(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="Testpass123"
        )

        self.transaction = Transaction.objects.create(
            sender=self.user,
            department="Finance",
            receiver="Brenda",
            phone="254712345001",
            type="Income",
            activity_date=timezone.now(),
            receipt_link="https://example.com/receipt/001",
            qty=Decimal("1.00"),
            amount=Decimal("15000.00"),
            transaction_cost=Decimal("50.00"),
            description="Student training fee payment",
            payment_method="MPESA"
        )

    def test_transaction_created_successfully(self):
        self.assertEqual(Transaction.objects.count(), 1)

    def test_transaction_sender(self):
        self.assertEqual(self.transaction.sender, self.user)

    def test_transaction_department(self):
        self.assertEqual(self.transaction.department, "Finance")

    def test_transaction_receiver(self):
        self.assertEqual(self.transaction.receiver, "Brenda")

    def test_transaction_amount(self):
        self.assertEqual(self.transaction.amount, Decimal("15000.00"))

    def test_transaction_cost(self):
        self.assertEqual(self.transaction.transaction_cost, Decimal("50.00"))

    def test_transaction_payment_method(self):
        self.assertEqual(self.transaction.payment_method, "MPESA")

    def test_transaction_type(self):
        self.assertEqual(self.transaction.type, "Income")

    def test_total_amount_property(self):
        self.assertEqual(self.transaction.total_amount, Decimal("15050.00"))

    def test_transaction_string_method(self):
        expected = "Income - 15000.00 - MPESA"
        self.assertEqual(str(self.transaction), expected)