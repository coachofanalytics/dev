from django.test import TestCase
from memberjoin.models import MembershipRegistration


class MembershipRegistrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reg = MembershipRegistration.objects.create(
            first_name='Ana', last_name='Bell', email='ana@example.com', membership_type='individual'
        )

    def test_str_returns_name_and_email(self):
        self.assertIn('ana@example.com', str(self.reg))
