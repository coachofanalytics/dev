from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from communities.views import directory
from communities.models import DirectoryMember


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class DirectoryViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='viewer', password='pw')

        # create some directory members
        DirectoryMember.objects.create(
            full_name='Alice Smith', profession='Engineer', region='Kigali',
            category='tech', membership_type='verified', expertise='Python'
        )
        DirectoryMember.objects.create(
            full_name='Bob Jones', profession='Doctor', region='Butare',
            category='healthcare', membership_type='verified', expertise='Pediatrics'
        )
        DirectoryMember.objects.create(
            full_name='Charlie Ray', profession='Designer', region='Kigali',
            category='creative', membership_type='premium', expertise='UI/UX'
        )

    def test_directory_view_shows_all_active_members(self):
        request = self.factory.get('/directory')
        request.user = self.user
        response = directory(request)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # ensure created member names appear in rendered content
        self.assertIn('Alice Smith', content)
        self.assertIn('Bob Jones', content)
        self.assertIn('Charlie Ray', content)

    def test_directory_search_filter(self):
        request = self.factory.get('/directory', {'search': 'Alice'})
        request.user = self.user
        response = directory(request)
        content = response.content.decode('utf-8')
        # Alice should be present; others not
        self.assertIn('Alice Smith', content)
        self.assertNotIn('Bob Jones', content)
        self.assertNotIn('Charlie Ray', content)

    def test_directory_region_filter(self):
        request = self.factory.get('/directory', {'region': 'Kigali'})
        request.user = self.user
        response = directory(request)
        content = response.content.decode('utf-8')
        # two members in Kigali should appear
        self.assertIn('Alice Smith', content)
        self.assertIn('Charlie Ray', content)
        self.assertNotIn('Bob Jones', content)
