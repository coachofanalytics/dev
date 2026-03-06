import time
from django.test import TestCase
from django.urls import reverse

from communities.models import CommunityMember


class DirectoryLoadPerformance(TestCase):
    def test_directory_load_time_with_many_members(self):
        members = [CommunityMember(name=f'Member {i}', email=f'm{i}@example.com') for i in range(200)]
        CommunityMember.objects.bulk_create(members)

        url = reverse('communities:member_directory')
        start = time.perf_counter()
        resp = self.client.get(url)
        elapsed = time.perf_counter() - start

        self.assertEqual(resp.status_code, 200)
        self.assertLess(elapsed, 2.5, f"Directory load took too long: {elapsed:.2f}s")
