from django.test import TestCase

from communities.forms import JoinForm
from communities.models import CommunityMember


class JoinFormTests(TestCase):
    def test_clean_email_rejects_duplicate(self):
        CommunityMember.objects.create(name='Existing', email='dup@example.com')
        form = JoinForm(data={
            'name': 'New',
            'email': 'dup@example.com',
            'profession': 'Dev',
            'region': 'City',
            'agree_to_directory': True,
            'agree_terms': True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_clean_phone_invalid_short_number(self):
        form = JoinForm(data={
            'name': 'Phone Test',
            'email': 'phone@example.com',
            'profession': 'Dev',
            'region': 'City',
            'phone': '12345',
            'agree_to_directory': True,
            'agree_terms': True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)
