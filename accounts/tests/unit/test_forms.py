from django.test import TestCase
from accounts.forms import UserForm,CredentialForm
from accounts.models import User, Credential, CredentialCategory

class TestForms(TestCase):

    def test_user_form_valid_data(self):
        form = UserForm(data={
            'category': '1',
            'sub_category': '1',
            'first_name': 'john',
            'last_name': 'doe',
            'username': 'johndoeeeee',
            'password1': 'Passw@rd123',
            'password2': 'Passw@rd123',
            'phone': '1234567890',
            'gender': '1',
            'email': 'johndoe@gmail.com',
            'address': '1234 Main Street',
            'city': 'New York',
            'state': 'NY',
            'country': 'US',
        })

        self.assertTrue(form.is_valid())

    def test_user_form_no_data(self):
        form = UserForm(data={})

        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 10)

class TestCredentialForm(TestCase):

    def test_user_form_valid_data(self):
        self.category = CredentialCategory.objects.create(category='Test Category',slug='test-category',description='Test Description')
        self.user =  User.objects.create(
            first_name='John',
            last_name='Doe',
            email= 'johndoe@gmail.com',
            gender='1',
            is_staff=True,
            is_active=True,
            )
        self.credential = Credential.objects.create(
            # category=self.category,
            added_by=self.user,
            name='Test Credential',
            slug='test-credential',
            description='Test Description')
        self.assertEqual(str(self.credential), 'Test Credential')
