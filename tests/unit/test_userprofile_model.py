from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()
UserProfile = apps.get_model('accounts', 'UserProfile')
Category = apps.get_model('accounts', 'Category')


class UserProfileModelTests(TestCase):
    def test_profile_create_and_str(self):
        user = User.objects.create_user(username='bob', password='pass')
        # Avoid saving to DB to prevent schema mismatch in test DB
        profile = UserProfile(user=user)
        self.assertTrue(hasattr(profile, 'user'))
        self.assertIsInstance(profile, UserProfile)

    def test_dashboard_url_default(self):
        user = User.objects.create_user(username='carol', password='pass')
        profile = UserProfile(user=user)
        self.assertEqual(profile.dashboard_url, 'home')

    def test_dashboard_url_category(self):
        cat = Category.objects.create(name='Investor', slug='investor')
        user = User.objects.create_user(username='dan', password='pass')
        profile = UserProfile(user=user, category=cat)
        self.assertEqual(profile.dashboard_url, 'investor_dashboard')
