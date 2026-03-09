from django.test import TestCase
from django.urls import reverse

from communities.models import CommunityMember
from communities.forms import JoinForm


class DirectoryEdgeCaseTests(TestCase):
    def test_empty_state_when_no_members(self):
        CommunityMember.objects.all().delete()
        url = reverse('communities:member_directory')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'No members found', resp.content)

    def test_empty_state_shows_filter_help_when_filters_active(self):
        url = reverse('communities:member_directory') + '?search=Nonexistent&region=Nowhere'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Try adjusting your search filters', resp.content)

    def test_edge_case_input_validation_long_name(self):
        data = {
            'name': 'A' * 500,
            'email': 'longname@example.com',
            'profession': 'Dev',
            'region': 'City',
            'agree_to_directory': True,
            'agree_terms': True,
        }
        form = JoinForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
