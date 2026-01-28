from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from communities.views import directory
from communities.models import DirectoryMember


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
        # context should contain members (page object)
        members = response.context_data['members'] if hasattr(response, 'context_data') else response.context['members']
        # ensure at least 3 members are present in queryset
        self.assertGreaterEqual(members.paginator.count, 3)

    def test_directory_search_filter(self):
        request = self.factory.get('/directory', {'search': 'Alice'})
        request.user = self.user
        response = directory(request)
        members = response.context_data['members'] if hasattr(response, 'context_data') else response.context['members']
        # only Alice should match
        self.assertEqual(members.paginator.count, 1)

    def test_directory_region_filter(self):
        request = self.factory.get('/directory', {'region': 'Kigali'})
        request.user = self.user
        response = directory(request)
        members = response.context_data['members'] if hasattr(response, 'context_data') else response.context['members']
        # two members in Kigali
        self.assertEqual(members.paginator.count, 2)
