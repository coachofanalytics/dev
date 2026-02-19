import time
from django.test import TransactionTestCase

from communities.models import CommunityMember


class BulkMemberCreationPerformance(TransactionTestCase):
    reset_sequences = True

    def test_bulk_create_500_members(self):
        count = 500
        members = [CommunityMember(name=f'Member {i}', email=f'bulk{i}@example.com') for i in range(count)]
        start = time.perf_counter()
        CommunityMember.objects.bulk_create(members)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 5.0, f"Bulk create took too long: {elapsed:.2f}s")
        self.assertEqual(CommunityMember.objects.count(), count)
