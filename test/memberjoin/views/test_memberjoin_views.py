import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestMemberJoinViews:
    def test_member_home_get(self):
        client = Client()
        resp = client.get(reverse('member_home'))
        assert resp.status_code in (200,)
