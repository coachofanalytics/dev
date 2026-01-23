import pytest
from django.test import Client
from django.urls import reverse
from accounts.models import CustomerUser, Membership


@pytest.mark.django_db
class TestFinanceViews:
    def test_pay_view_requires_login(self):
        client = Client()
        resp = client.get(reverse('finance:pay'))
        # should redirect to login
        assert resp.status_code in (302,)

    def test_process_payment_post(self):
        user = CustomerUser.objects.create(username='payu', email='p@example.com')
        Membership.objects.create(member=user, fee=10, currency='USD', status='NOT_PAID')
        client = Client()
        client.force_login(user)
        resp = client.post(reverse('finance:process_payment'), {'amount': '20'})
        assert resp.status_code in (302,)
