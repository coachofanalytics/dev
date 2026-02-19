from django.test import TestCase
from django.db import IntegrityError

from communities.models import CommunityMember, DirectoryProfile


class CommunityMemberModelTests(TestCase):
    def test_str_representation(self):
        m = CommunityMember.objects.create(name='Jane', email='jane@example.com', profession='Artist')
        self.assertIn('Jane', str(m))

    def test_unique_email_constraint(self):
        CommunityMember.objects.create(name='A', email='unique@example.com')
        with self.assertRaises(IntegrityError):
            CommunityMember.objects.create(name='B', email='unique@example.com')


class DirectoryProfileModelTests(TestCase):
    def test_save_updates_member_fields(self):
        member = CommunityMember.objects.create(name='Old', email='dp@example.com', profession='Old', region='Old')
        dp = DirectoryProfile(community_member=member, full_name='New Name', profession='New Profession', region_city='New Region', category='other', expertise_summary='x')
        dp.save()
        member.refresh_from_db()
        self.assertEqual(member.name, 'New Name')
        self.assertEqual(member.profession, 'New Profession')
