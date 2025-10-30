from django.test import TestCase
#from accounts.models import CustomerUser, Department, Credential, CredentialCategory, TaskGroups, Tracker,Transaction
from django.urls import reverse
import datetime 
from django.utils import timezone
from decimal import Decimal
from main.models import Transaction, CustomerUser, Department

# class TestDepartmentModel(TestCase):
#     def setUp(self):
#         self.department_obj = Department.objects.create(name='HR Department', slug='test_hr_department')
        

#     # def test_department_name(self):
#     #     self.assertEqual(self.department.name, 'Test Department')

#     def test_model_str(self):
        
#         self.assertTrue(isinstance(self.department_obj, Department))
#         self.assertEqual(str(self.department_obj.name), 'HR Department')

#     # def test_model_get_by_id(self):
#     #     import pdb; pdb.set_trace()
#     #     fetch_department_by_id = Department.objects.get_by_id(self.department_obj.id)

#     #     self.assertTrue(fetch_department_by_id, 1)
    
#     def test_model_get_by_wrong_id(self):
        
#         fetch_department_by_id = Department.objects.get_by_id(20)

#         self.assertEquals(fetch_department_by_id, None)


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

# class TestCredential(TestCase):

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





class TransactionModelTest(TestCase):
    def setUp(self):
        # Create sample sender and department for FK relationships
        self.sender = CustomerUser.objects.create(
            first_name="John",
            last_name="Doe",
            gender="Male",
            user_category="Staff"
        )
        self.department = Department.objects.create(
            name="Finance",
            description="Handles company financial transactions."
        )

    def test_create_transaction(self):
        """Test that a Transaction record can be created successfully."""
        transaction = Transaction.objects.create(
            sender=self.sender,
            department=self.department,
            receiver="Jane Doe",
            phone="0712345678",
            type="Payment",
            qty=Decimal("3.00"),
            amount=Decimal("15000.00"),
            transaction_cost=Decimal("100.00"),
            description="Payment for office supplies."
        )

        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(transaction.sender.first_name, "John")
        self.assertEqual(transaction.receiver, "Jane Doe")
        self.assertEqual(transaction.amount, Decimal("15000.00"))
        self.assertEqual(transaction.transaction_cost, Decimal("100.00"))
        self.assertIsNotNone(transaction.created_at)
        self.assertTrue(isinstance(transaction.activity_date, timezone.datetime))

    def test_default_transaction_cost(self):
        """Test that transaction_cost defaults to 0.00."""
        transaction = Transaction.objects.create(
            sender=self.sender,
            department=self.department,
            receiver="Grace Atieno",
            phone="0700000000",
            type="Refund",
            qty=Decimal("1.00"),
            amount=Decimal("5000.00"),
            description="Refund for overpayment."
        )
        self.assertEqual(transaction.transaction_cost, Decimal("0.00"))

    def test_update_transaction(self):
        """Test updating an existing transaction."""
        transaction = Transaction.objects.create(
            sender=self.sender,
            department=self.department,
            receiver="David Otieno",
            phone="0722334455",
            type="Purchase",
            amount=Decimal("20000.00")
        )
        transaction.amount = Decimal("25000.00")
        transaction.save()

        updated = Transaction.objects.get(id=transaction.id)
        self.assertEqual(updated.amount, Decimal("25000.00"))

    def test_null_fields_allowed(self):
        """Test that nullable fields can be left empty."""
        transaction = Transaction.objects.create(
            sender=None,
            department=None,
            receiver=None,
            phone=None,
            type=None,
            amount=None,
        )
        self.assertIsNone(transaction.sender)
        self.assertIsNone(transaction.department)
        self.assertIsNone(transaction.receiver)
        self.assertIsNone(transaction.amount)
