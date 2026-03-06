from django.test import TestCase
from django.urls import reverse

from communities.models import CommunityMember


class JoinViewTests(TestCase):
    def test_get_join_form_does_not_show_model_defaults(self):
        """GET the join page should render empty profession/region (not the model default)."""
        url = reverse('communities:join')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(b'Not Specified', resp.content)

    def test_post_join_valid_redirects_to_member_directory(self):
        url = reverse('communities:join')
        data = {
            'name': 'Test User',
            'email': 'testuser1@example.com',
            'profession': 'Engineer',
            'region': 'Test City',
            'agree_to_directory': 'on',
            'agree_terms': 'on',
            'email_updates': 'on',
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('communities:member_directory'))
        self.assertTrue(CommunityMember.objects.filter(email='testuser1@example.com').exists())

    def test_post_join_missing_required_fields_rerenders_with_errors(self):
        url = reverse('communities:join')
        data = {
            'name': 'Incomplete',
            'email': 'incomplete@example.com',
            'agree_to_directory': 'on',
            'agree_terms': 'on',
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'This field is required', resp.content)
