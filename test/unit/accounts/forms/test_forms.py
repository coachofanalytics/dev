from django.test import TestCase
from accounts.forms import UserForm
from accounts.models import CustomerUser


class AccountsFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        CustomerUser.objects.create(username='johnsmith')

    def test_clean_invalid_email_adds_error(self):
        form = UserForm(data={
            'category': 1,
            'first_name': 'Alice',
            'last_name': 'Smith',
            'email': 'not-an-email',
            'is_staff': False,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_disallowed_names_add_error(self):
        form = UserForm(data={
            'category': 1,
            'first_name': 'test',
            'last_name': 'testing',
            'email': 'a@example.com',
            'is_staff': False,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)

    def test_generate_unique_username_appends_number(self):
        form = UserForm()
        unique = form.generate_unique_username('johnsmith')
        self.assertNotEqual(unique, 'johnsmith')
        self.assertTrue(unique.startswith('johnsmith'))
