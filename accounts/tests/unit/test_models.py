from django.test import TestCase
from accounts.models import User, Department, Credential, CredentialCategory, TaskGroups, Tracker
from django.urls import reverse
import datetime 

from django.contrib.auth import get_user_model

class UserModelTest(TestCase):

    def setUp(self):
        self.User = get_user_model()

    def test_create_user(self):
        user = self.User.objects.create_user(
            username='testuser',
            password='password123',
            first_name='John',
            last_name='Doe',
            email='testuser@example.com',
            phone='555-555-5555',
            is_admin=False,
            is_client=True,
            is_applicant=False,
            is_employee_contract_signed=False,
        )
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('password123'))
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertEqual(user.phone, '555-555-5555')
        self.assertFalse(user.is_admin)
        self.assertTrue(user.is_client)
        self.assertFalse(user.is_applicant)
        self.assertFalse(user.is_employee_contract_signed)

    def test_create_superuser(self):
        superuser = self.User.objects.create_superuser(
            username='admin',
            password='adminpassword',
            first_name='Admin',
            last_name='User',
            email='admin@example.com',
        )
        self.assertEqual(superuser.username, 'admin')
        self.assertTrue(superuser.check_password('adminpassword'))
        self.assertEqual(superuser.first_name, 'Admin')
        self.assertEqual(superuser.last_name, 'User')
        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertTrue(superuser.is_admin)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_full_name(self):
        user = self.User.objects.create_user(
            username='testuser',
            password='password123',
            first_name='John',
            last_name='Doe',
            email='testuser@example.com',
            phone='555-555-5555',
            is_admin=False,
            is_client=True,
            is_applicant=False,
            is_employee_contract_signed=False,
        )
        self.assertEqual(user.full_name, 'John Doe')


class TestDepartmentModel(TestCase):
    # def setUp(self):
    #     self.department = Department.objects.create(name='Test Department')

    # def test_department_name(self):
    #     self.assertEqual(self.department.name, 'Test Department')

    def test_model_str(self):
        self.name = Department.objects.create(name='HR Department')
        self.assertEqual(str(self.name), 'HR Department')


class TestTaskGroups(TestCase):

    def test_model_str(self):
        title = TaskGroups.objects.create(title='Group X')
        description = TaskGroups.objects.create(description='Dummy Description For Group X')
        self.assertEqual(str(title), 'Group X')

class TestTrackerModel(TestCase):

    def test_model_create(self):
        self.category = "Interview"
        self.task = "database"
        self.duration = 10
        tracker = Tracker.objects.create(
            category=self.category,
            task=self.task,
            )

    # def test_model_url(self):
    #     tracker = self.test_model_create()
    #     response = self.client.post(reverse('usertime', args=['johndoee']))
    #     self.assertEqual(response.status_code, 200)

class TestCredentialCategory(TestCase):

    def test_model_str(self):
        self.category = CredentialCategory.objects.create(category='Test Category',slug='test-category',description='Test Description')
        self.assertEqual(str(self.category), 'Test Category')

    # def test_model_url(self):
    #     self.category = CredentialCategory.objects.create(category='Test Category',slug='test-category',description='Test Description')
    #     response = self.client.post(reverse('management:credentialcategorylist', args=["test-category"])) #set unit_view to the url name in the urls.py
    #     self.assertEqual(response.status_code, 200)

class TestCredential(TestCase):

    def test_model_str(self):
        self.user =  User.objects.create(
            first_name='John',
            last_name='Doe',
            email= 'johndoe@gmail.com',
            gender='1',
            is_staff=True,
            is_active=True,
            )
        self.credential = Credential.objects.create(
            added_by=self.user,
            name='Test Credential',
            slug='test-credential',
            description='Test Description')
        self.assertEqual(str(self.credential), 'Test Credential')

    # def test_model_url(self):
    #     self.category = CredentialCategory.objects.create(category='Test Category',slug='test-category',description='Test Description')
    #     self.user =  User.objects.create(
    #         first_name='John',
    #         last_name='Doe',
    #         email= 'johndoe@gmail.com',
    #         gender='1',
    #         is_staff=True,
    #         is_active=True,
    #         )
    #     self.credential = Credential.objects.create(
    #         added_by=self.user,
    #         name='Test Credential',
    #         slug='test-credential',
    #         description='Test Description')
    #     response = self.client.post(reverse('management:credential'))
    #     self.assertEqual(response.status_code, 200)