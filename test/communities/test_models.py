from django.test import TestCase
from django.contrib.auth import get_user_model
from communities.models import DirectoryMember


class DirectoryMemberModelTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='tester', password='pass')

    def test_initials_generated_for_two_names_and_premium_flag(self):
        member = DirectoryMember(
            user=self.user,
            full_name='John Doe',
            profession='Developer',
            region='Kigali',
            category='tech',
            membership_type='premium',
            expertise='Django',
        )
        member.save()

        # initials should be JD
        self.assertEqual(member.initials, 'JD')
        # premium membership should set is_premium True
        self.assertTrue(member.is_premium)
        # avatar_color should be one of the expected palette
        palette = ['#dc2626', '#059669', '#2563eb', '#7c3aed', '#ea580c', '#0891b2']
        self.assertIn(member.avatar_color, palette)

    def test_initials_for_single_name(self):
        member = DirectoryMember(
            user=self.user,
            full_name='Prince',
            profession='Artist',
            region='Butare',
            category='creative',
            membership_type='verified',
            expertise='Painting',
        )
        member.save()

        # initials should be first two letters of single name
        self.assertEqual(member.initials, 'PR')
        # not premium
        self.assertFalse(member.is_premium)
