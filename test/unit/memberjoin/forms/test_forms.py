from django.test import TestCase
from memberjoin.forms import MembershipRegistrationForm


class MemberjoinFormsTests(TestCase):
    def test_membership_registration_form_valid(self):
        form = MembershipRegistrationForm(data={'first_name': 'A', 'last_name': 'B', 'email': 'ab@example.com', 'membership_type': 'individual'})
        self.assertTrue(form.is_valid())
