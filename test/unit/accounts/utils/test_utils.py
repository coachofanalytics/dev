from django.test import TestCase
from types import SimpleNamespace
from accounts.utils import agreement_data


class AccountsUtilsTests(TestCase):
    def test_agreement_data_extracts_post(self):
        fake_request = SimpleNamespace()
        fake_request.POST = {
            'first_name': 'Alice',
            'last_name': 'Smith',
            'address': '123 Lane',
            'category': '1',
            'sub_category': '2',
            'username': 'alice',
            'password1': 'p',
            'password2': 'p',
            'email': 'a@example.com',
            'phone': '1234',
            'gender': 'F',
        }
        data, contract_date = agreement_data(fake_request)
        self.assertEqual(data['first_name'], 'Alice')
        self.assertIn(' ', contract_date or '')
