import pytest
from django.test import Client
from django.urls import reverse
from communities.models import ForumCategory


@pytest.mark.django_db
class TestCommunitiesViews:
    def test_forum_home_and_category(self):
        client = Client()
        cat = ForumCategory.objects.create(name='A', slug='a', description='d')
        # reverse without namespace because urls are included without an app_name
        resp = client.get(reverse('forum_home'))
        assert resp.status_code in (200,)
        resp2 = client.get(reverse('category_detail', kwargs={'slug': 'a'}))
        assert resp2.status_code == 200
