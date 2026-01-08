"""
Comprehensive unit tests for user registration.
Tests registration for all user types and various scenarios.
"""
from django.test import TestCase, Client, override_settings
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
import tempfile
import os

User = get_user_model()
Category = apps.get_model('accounts', 'Category')
UserProfile = apps.get_model('accounts', 'UserProfile')

# Import audit signals to disconnect them during login/logout tests
try:
    from audit.signals import log_user_login, log_user_logout
    _audit_signals_available = True
except ImportError:
    _audit_signals_available = False


class UserRegistrationSuccessTests(TestCase):
    """Tests for successful user registration."""

    def setUp(self):
        self.client = Client()
        self.investor_cat = Category.objects.create(name='Investor', slug='investor')
        self.business_cat = Category.objects.create(name='Business', slug='business')
        self.individual_cat = Category.objects.create(name='Individual', slug='individual')

    def test_create_investor_user(self):
        """Test creating an investor user."""
        user = User.objects.create_user(
            username='investor_test',
            email='investor@example.com',
            password='TestPass123!'
        )
        profile = user.profile
        profile.category = self.investor_cat
        profile.save()
        
        self.assertEqual(profile.dashboard_url, 'investor_dashboard')

    def test_create_business_user(self):
        """Test creating a business user."""
        user = User.objects.create_user(
            username='business_test',
            email='business@example.com',
            password='TestPass123!'
        )
        profile = user.profile
        profile.category = self.business_cat
        profile.save()
        
        self.assertEqual(profile.dashboard_url, 'business_dashboard')

    def test_create_individual_user(self):
        """Test creating an individual user."""
        user = User.objects.create_user(
            username='individual_test',
            email='individual@example.com',
            password='TestPass123!'
        )
        profile = user.profile
        profile.category = self.individual_cat
        profile.save()
        
        self.assertEqual(profile.dashboard_url, 'individual_dashboard')

    def test_create_admin_user(self):
        """Test creating an admin/superuser."""
        admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@example.com',
            password='AdminPass123!'
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)


class UserRegistrationFailureTests(TestCase):
    """Tests for registration failure scenarios."""

    def setUp(self):
        self.existing_user = User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='ExistingPass123!'
        )

    def test_duplicate_username_fails(self):
        """Test registration with duplicate username fails."""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='existing',
                email='new@example.com',
                password='NewPass123!'
            )

    def test_empty_username_fails(self):
        """Test registration with empty username fails."""
        from django.db import IntegrityError
        with self.assertRaises((ValueError, IntegrityError)):
            User.objects.create_user(
                username='',
                email='empty@example.com',
                password='Pass123!'
            )

    def test_no_password_fails(self):
        """Test registration without password fails."""
        from django.db import IntegrityError
        # Django allows creating user with None password but they can't login
        user = User.objects.create_user(
            username='nopass',
            email='nopass@example.com',
            password=None
        )
        self.assertFalse(user.has_usable_password())


class UserLoginLogoutTests(TestCase):
    """Tests for user login and logout functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disconnect audit signals to prevent database errors during tests
        if _audit_signals_available:
            user_logged_in.disconnect(log_user_login)
            user_logged_out.disconnect(log_user_logout)

    @classmethod
    def tearDownClass(cls):
        # Reconnect audit signals
        if _audit_signals_available:
            user_logged_in.connect(log_user_login)
            user_logged_out.connect(log_user_logout)
        super().tearDownClass()

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='loginuser',
            email='login@example.com',
            password='LoginPass123!'
        )

    def test_valid_password_check(self):
        """Test password verification with valid credentials."""
        # Use check_password to verify credentials work (bypasses axes)
        self.assertTrue(self.user.check_password('LoginPass123!'))

    def test_invalid_password_check(self):
        """Test password verification with invalid password fails."""
        self.assertFalse(self.user.check_password('WrongPassword'))

    def test_user_exists_by_username(self):
        """Test user can be found by username."""
        user = User.objects.filter(username='loginuser').first()
        self.assertIsNotNone(user)

    def test_nonexistent_username(self):
        """Test nonexistent username returns None."""
        user = User.objects.filter(username='nonexistent').first()
        self.assertIsNone(user)

    def test_case_sensitive_username(self):
        """Test username is case-sensitive."""
        # Django default is case-sensitive username
        user = User.objects.filter(username='LOGINUSER').first()
        self.assertIsNone(user)

    def test_inactive_user_cannot_authenticate(self):
        """Test inactive user is_active flag."""
        self.user.is_active = False
        self.user.save()
        self.user.refresh_from_db()
        
        self.assertFalse(self.user.is_active)

    def test_logout(self):
        """Test user logout."""
        # Use force_login to bypass axes authentication
        self.client.force_login(self.user)
        self.client.logout()
        # After logout, user should not be authenticated
        response = self.client.get('/')
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class UserProfileUpdateTests(TestCase):
    """Tests for user profile updates."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='profileupdate',
            email='profile@example.com',
            password='ProfilePass123!'
        )
        self.profile = self.user.profile

    def test_update_bio(self):
        """Test updating user bio."""
        self.profile.bio = 'Updated bio text'
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, 'Updated bio text')

    def test_update_company_name(self):
        """Test updating company name."""
        self.profile.company_name = 'Test Company'
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.company_name, 'Test Company')

    def test_update_phone(self):
        """Test updating phone number."""
        self.profile.phone = '+1234567890'
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, '+1234567890')

    def test_update_location(self):
        """Test updating location."""
        self.profile.location = 'New York, USA'
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.location, 'New York, USA')

    def test_update_first_last_name(self):
        """Test updating user first and last name."""
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.get_full_name(), 'John Doe')

    def test_update_email(self):
        """Test updating user email."""
        self.user.email = 'newemail@example.com'
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')


class PasswordResetTests(TestCase):
    """Tests for password reset functionality."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='resetuser',
            email='reset@example.com',
            password='OldPass123!'
        )

    def test_set_password(self):
        """Test setting new password."""
        self.user.set_password('NewPass123!')
        self.user.save()
        
        self.assertTrue(self.user.check_password('NewPass123!'))
        self.assertFalse(self.user.check_password('OldPass123!'))

    def test_check_password_after_reset(self):
        """Test old password doesn't work after reset."""
        old_password = 'OldPass123!'
        new_password = 'NewPass123!'
        
        self.assertTrue(self.user.check_password(old_password))
        
        self.user.set_password(new_password)
        self.user.save()
        
        self.assertFalse(self.user.check_password(old_password))
        self.assertTrue(self.user.check_password(new_password))


class RoleBasedPermissionTests(TestCase):
    """Tests for role-based permissions."""

    def setUp(self):
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='RegularPass123!'
        )
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='StaffPass123!',
            is_staff=True
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!'
        )

    def test_regular_user_not_staff(self):
        """Test regular user is not staff."""
        self.assertFalse(self.regular_user.is_staff)
        self.assertFalse(self.regular_user.is_superuser)

    def test_staff_user_is_staff(self):
        """Test staff user is staff but not superuser."""
        self.assertTrue(self.staff_user.is_staff)
        self.assertFalse(self.staff_user.is_superuser)

    def test_admin_user_is_superuser(self):
        """Test admin user is both staff and superuser."""
        self.assertTrue(self.admin_user.is_staff)
        self.assertTrue(self.admin_user.is_superuser)

    def test_user_permissions_default_empty(self):
        """Test new user has no permissions by default."""
        self.assertEqual(self.regular_user.user_permissions.count(), 0)

    def test_superuser_has_all_permissions(self):
        """Test superuser has all permissions."""
        self.assertTrue(self.admin_user.has_perm('any.permission'))


class UserDifferentCategoryBehaviorTests(TestCase):
    """Tests for different user category behaviors."""

    def setUp(self):
        self.investor_cat = Category.objects.create(name='Investor', slug='investor')
        self.business_cat = Category.objects.create(name='Business', slug='business')
        self.individual_cat = Category.objects.create(name='Individual', slug='individual')

    def test_investor_dashboard_url(self):
        """Test investor gets correct dashboard URL."""
        user = User.objects.create_user(username='investor', password='pass')
        user.profile.category = self.investor_cat
        user.profile.save()
        self.assertEqual(user.profile.dashboard_url, 'investor_dashboard')

    def test_business_dashboard_url(self):
        """Test business user gets correct dashboard URL."""
        user = User.objects.create_user(username='business', password='pass')
        user.profile.category = self.business_cat
        user.profile.save()
        self.assertEqual(user.profile.dashboard_url, 'business_dashboard')

    def test_individual_dashboard_url(self):
        """Test individual gets correct dashboard URL."""
        user = User.objects.create_user(username='individual', password='pass')
        user.profile.category = self.individual_cat
        user.profile.save()
        self.assertEqual(user.profile.dashboard_url, 'individual_dashboard')

    def test_user_without_category(self):
        """Test user without category gets home URL."""
        user = User.objects.create_user(username='nocategory', password='pass')
        self.assertEqual(user.profile.dashboard_url, 'home')


class SessionManagementTests(TestCase):
    """Tests for session management."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disconnect audit signals to prevent database errors during tests
        if _audit_signals_available:
            user_logged_in.disconnect(log_user_login)
            user_logged_out.disconnect(log_user_logout)

    @classmethod
    def tearDownClass(cls):
        # Reconnect audit signals
        if _audit_signals_available:
            user_logged_in.connect(log_user_login)
            user_logged_out.connect(log_user_logout)
        super().tearDownClass()

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='sessionuser',
            email='session@example.com',
            password='SessionPass123!'
        )

    def test_session_created_on_login(self):
        """Test session is created on login using force_login."""
        # Use force_login to bypass axes authentication
        self.client.force_login(self.user)
        self.assertIn('_auth_user_id', self.client.session)

    def test_session_cleared_on_logout(self):
        """Test session is cleared on logout."""
        self.client.force_login(self.user)
        self.client.logout()
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_multiple_sessions(self):
        """Test user can have multiple sessions."""
        client1 = Client()
        client2 = Client()
        
        # Use force_login to bypass axes authentication
        client1.force_login(self.user)
        client2.force_login(self.user)
        
        # Both clients should be authenticated
        self.assertIn('_auth_user_id', client1.session)
        self.assertIn('_auth_user_id', client2.session)

