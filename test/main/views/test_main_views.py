import pytest
from django.test import Client
from django.urls import reverse
from main.models import Page


@pytest.mark.django_db
class TestMainViews:
    def test_home_layout_get(self):
        client = Client()
        # ensure a Page exists
        Page.objects.create(page_name='Home')
        resp = client.get(reverse('main:layout'))
        assert resp.status_code == 200

    def test_add_message_post(self):
        client = Client()
        url = reverse('main:add_message')
        resp = client.post(url, {'name': 'T', 'email': 't@example.com', 'message': 'hi'})
        # view redirects on success
        assert resp.status_code in (200,302)
