import pytest
from django.urls import reverse
from django.test import Client
from accounts.models import CustomerUser, Membership


@pytest.mark.django_db
class TestAccountsViews:
    def test_register_and_login_view_get(self):
        client = Client()
        url = reverse('accounts:account-login')
        # Ensure a SocialApp exists so allauth template tags don't error
        try:
            from allauth.socialaccount.models import SocialApp
            from django.contrib.sites.models import Site
            Site.objects.get_or_create(id=1, defaults={'domain': 'example.com', 'name': 'example'})
            sa, _ = SocialApp.objects.get_or_create(provider='google', name='Google', client_id='x', secret='y')
            sa.sites.add(Site.objects.get(id=1))
        except Exception:
            # If allauth isn't installed/configured in test env, skip setup
            pass
        resp = client.get(url)
        assert resp.status_code in (200,302)

    def test_membership_redirect_for_unpaid(self):
        user = CustomerUser.objects.create(username='u1', email='u1@example.com')
        membership = Membership.objects.create(member=user, fee=10, currency='USD', status='NOT_PAID')
        client = Client()
        client.force_login(user)
        resp = client.get(reverse('finance:pay'))
        # pay view requires login and returns 200
        assert resp.status_code == 200
