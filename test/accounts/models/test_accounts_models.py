import pytest
from accounts.models import CustomerUser, Membership


@pytest.mark.django_db
class TestAccountsModels:
    def test_customeruser_str_and_defaults(self):
        user = CustomerUser.objects.create(username='jdoe', email='jdoe@example.com', first_name='John', last_name='Doe')
        assert user.username == 'jdoe'
        assert user.email == 'jdoe@example.com'
        assert hasattr(user, 'date_joined')

    def test_membership_creation_and_is_paid(self):
        user = CustomerUser.objects.create(username='member1', email='m1@example.com')
        membership = Membership.objects.create(member=user, fee=10.00, currency='USD', status='NOT_PAID')
        assert not membership.is_paid
        membership.status = 'PAID'
        membership.paid_date = None
        assert not membership.is_paid
        membership.paid_date = '2020-01-01T00:00:00'
        membership.status = 'PAID'
        assert membership.is_paid
