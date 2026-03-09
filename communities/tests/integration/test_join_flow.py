from django.test import TestCase
from django.urls import reverse

from communities.models import CommunityMember


class JoinDirectoryFormTests(TestCase):
    def test_join_directory_form_updates_member_and_redirects(self):
        member = CommunityMember.objects.create(
            name='Session User',
            email='sessionuser@example.com',
            profession='Not Specified',
            region='Not Specified',
        )

        session = self.client.session
        session['joined_member_id'] = member.id
        session.save()

        url = reverse('communities:join_directory_form')
        data = {
            'name': 'Session User Updated',
            'profession': 'Designer',
            'region': 'Updated City',
            'category': 'design',
            'expertise': 'Design and UX',
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('communities:member_directory'))
        member.refresh_from_db()
        self.assertEqual(member.name, 'Session User Updated')
        self.assertEqual(member.profession, 'Designer')
