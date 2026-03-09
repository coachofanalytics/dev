import pytest
from memberjoin.models import MembershipRegistration, ContactMessage


@pytest.mark.django_db
class TestMemberJoinModels:
    def test_membership_registration_and_str(self):
        m = MembershipRegistration.objects.create(first_name='A', last_name='B', email='ab@example.com', membership_type='individual')
        assert 'A' in str(m)

    def test_contact_message(self):
        c = ContactMessage.objects.create(name='X', email='x@example.com', message='Hi')
        assert 'Hi' in c.message
