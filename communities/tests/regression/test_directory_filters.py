from django.test import TestCase
from django.urls import reverse

from communities.models import CommunityMember


class MemberDirectoryFilterTests(TestCase):
    def setUp(self):
        CommunityMember.objects.create(name='Alice Smith', email='alice@example.com', profession='Engineer', region='Seattle', bio='Experienced engineer')
        CommunityMember.objects.create(name='Bob Jones', email='bob@example.com', profession='Doctor', region='Portland', bio='Medical professional')
        CommunityMember.objects.create(name='Carol Lee', email='carol@example.com', profession='Engineer', region='Seattle', bio='Civil engineer')

    def test_member_directory_renders_members(self):
        url = reverse('communities:member_directory')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Alice Smith', resp.content)
        self.assertIn(b'Bob Jones', resp.content)
        self.assertIn(b'Carol Lee', resp.content)

    def test_search_query_filters_results(self):
        url = reverse('communities:member_directory') + '?search=Alice'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Alice Smith', resp.content)
        self.assertNotIn(b'Bob Jones', resp.content)

    def test_region_and_profession_filters(self):
        url = reverse('communities:member_directory') + '?region=Seattle'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Alice Smith', resp.content)
        self.assertIn(b'Carol Lee', resp.content)
        self.assertNotIn(b'Bob Jones', resp.content)

        url = reverse('communities:member_directory') + '?profession=Doctor'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Bob Jones', resp.content)
        self.assertNotIn(b'Alice Smith', resp.content)
