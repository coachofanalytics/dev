from django.test import TestCase
from accounts.models import All_transaction

from django.urls import reverse
import datetime 
 


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
   


class AllTransactionModelTest(TestCase):
    """Tests for the All_transaction model."""

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