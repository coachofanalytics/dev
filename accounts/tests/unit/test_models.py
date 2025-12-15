from django.test import TestCase
from accounts.models import CustomerUser, Payment_Historyy
from django.urls import reverse
# import datetime 

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

    # def test_model_url(self):
    #     tracker = self.test_model_create()
    #     response = self.client.post(reverse('usertime', args=['johndoee']))
    #     self.assertEqual(response.status_code, 200)

# class TestCredentialCategory(TestCase):

#     def test_model_str(self):
#         self.category = CredentialCategory.objects.create(category='Test Category',slug='test-category',description='Test Description')
#         self.assertEqual(str(self.category), 'Test Category')

#     # def test_model_url(self):
    #     self.category = CredentialCategory.objects.create(category='Test Category',slug='test-category',description='Test Description')
    #     response = self.client.post(reverse('management:credentialcategorylist', args=["test-category"])) #set unit_view to the url name in the urls.py
    #     self.assertEqual(response.status_code, 200)

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
# accounts/tests/test_models.py

from django.test import TestCase
from django.utils import timezone
from accounts.models import CustomerUser, Payment_Historyy


class PaymentHistoryModelTest(TestCase):

    def setUp(self):
        self.customer = CustomerUser.objects.create(
            username="testuser",
            email="testuser@example.com",
            password="password123"
        )

    def test_payment_history_creation(self):
        payment = Payment_Historyy.objects.create(
            customer=self.customer,
            payment_fees=2500,
            down_payment=500,
            student_bonus=100,
            fee_balance=2000,
            plan=1,
            subplan=1,
            payment_method="Cash",
            client_signature="John Doe",
            company_rep="Brenda K",
            client_date="2025-01-05",
            rep_date="2025-01-05"
        )

        # Validate saved data
        self.assertEqual(payment.payment_fees, 2500)
        self.assertEqual(payment.down_payment, 500)
        self.assertEqual(payment.student_bonus, 100)
        self.assertEqual(payment.fee_balance, 2000)
        self.assertEqual(payment.plan, 1)
        self.assertEqual(payment.subplan, 1)
        self.assertEqual(payment.payment_method, "Cash")
        self.assertEqual(payment.client_signature, "John Doe")
        self.assertEqual(payment.company_rep, "Brenda K")
        self.assertEqual(payment.customer, self.customer)

        # Default datetime should not be empty
        self.assertIsNotNone(payment.contract_submitted_date)
