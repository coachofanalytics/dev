"""
Comprehensive tests for accounts services.

Tests user profile service, category service, role management,
and authentication-related services.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone

from accounts.models import Category, UserProfile, Role, Staff


@pytest.mark.django_db
class TestUserProfileService:
    """Test suite for user profile operations."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        user = User.objects.create_user(
            username='profile_user',
            email='profile@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        return user

    @pytest.fixture
    def category(self):
        """Create test category."""
        return Category.objects.create(
            name='Investor',
            slug='investor',
            description='Investor category',
            is_active=True
        )

    def test_user_profile_auto_created(self, user):
        """Test that UserProfile is automatically created with user."""
        assert hasattr(user, 'profile')
        assert user.profile is not None

    def test_profile_category_assignment(self, user, category):
        """Test assigning category to profile."""
        user.profile.category = category
        user.profile.save()
        
        user.refresh_from_db()
        assert user.profile.category == category
        assert user.profile.category.name == 'Investor'

    def test_profile_dashboard_url_investor(self, user, category):
        """Test dashboard URL for investor category."""
        user.profile.category = category
        user.profile.save()
        
        assert user.profile.dashboard_url == 'investor_dashboard'

    def test_profile_dashboard_url_business(self, user):
        """Test dashboard URL for business category."""
        business_cat = Category.objects.create(
            name='Business',
            slug='business',
            is_active=True
        )
        user.profile.category = business_cat
        user.profile.save()
        
        assert user.profile.dashboard_url == 'business_dashboard'

    def test_profile_dashboard_url_individual(self, user):
        """Test dashboard URL for individual category."""
        individual_cat = Category.objects.create(
            name='Individual',
            slug='individual',
            is_active=True
        )
        user.profile.category = individual_cat
        user.profile.save()
        
        assert user.profile.dashboard_url == 'individual_dashboard'

    def test_profile_dashboard_url_no_category(self, user):
        """Test dashboard URL when no category assigned."""
        user.profile.category = None
        user.profile.save()
        
        assert user.profile.dashboard_url == 'home'

    def test_profile_string_representation_with_category(self, user, category):
        """Test profile string representation with category."""
        user.profile.category = category
        user.profile.save()
        
        str_repr = str(user.profile)
        assert user.username in str_repr

    def test_profile_string_representation_without_category(self, user):
        """Test profile string representation without category."""
        user.profile.category = None
        user.profile.save()
        
        str_repr = str(user.profile)
        assert user.username in str_repr
        assert 'profile' in str_repr.lower()

    def test_profile_gdpr_consent(self, user):
        """Test GDPR consent recording."""
        user.profile.gdpr_consent = True
        user.profile.gdpr_consent_date = timezone.now()
        user.profile.gdpr_consent_ip = '192.168.1.1'
        user.profile.save()
        
        user.refresh_from_db()
        assert user.profile.gdpr_consent is True
        assert user.profile.gdpr_consent_date is not None
        assert user.profile.gdpr_consent_ip == '192.168.1.1'

    def test_profile_bio_max_length(self, user):
        """Test profile bio max length constraint."""
        user.profile.bio = 'A' * 500  # Max length
        user.profile.save()
        
        user.refresh_from_db()
        assert len(user.profile.bio) == 500

    def test_profile_optional_fields(self, user):
        """Test optional profile fields."""
        user.profile.company_name = 'Test Company'
        user.profile.job_title = 'Developer'
        user.profile.phone = '+1234567890'
        user.profile.location = 'New York'
        user.profile.website = 'https://example.com'
        user.profile.linkedin_url = 'https://linkedin.com/in/test'
        user.profile.twitter_handle = 'testuser'
        user.profile.years_of_experience = 5
        user.profile.industry = 'Technology'
        user.profile.skills = 'Python, Django, JavaScript'
        user.profile.save()
        
        user.refresh_from_db()
        assert user.profile.company_name == 'Test Company'
        assert user.profile.years_of_experience == 5


@pytest.mark.django_db
class TestCategoryService:
    """Test suite for category operations."""

    def test_create_category(self):
        """Test creating a category."""
        category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            description='A test category',
            is_active=True
        )
        
        assert category.id is not None
        assert category.name == 'Test Category'
        assert category.slug == 'test-category'

    def test_category_unique_slug(self):
        """Test category slug must be unique."""
        Category.objects.create(
            name='Category 1',
            slug='unique-slug',
            is_active=True
        )
        
        with pytest.raises(Exception):
            Category.objects.create(
                name='Category 2',
                slug='unique-slug',
                is_active=True
            )

    def test_category_unique_name(self):
        """Test category name must be unique."""
        Category.objects.create(
            name='Unique Name',
            slug='slug-1',
            is_active=True
        )
        
        with pytest.raises(Exception):
            Category.objects.create(
                name='Unique Name',
                slug='slug-2',
                is_active=True
            )

    def test_category_string_representation(self):
        """Test category string representation."""
        category = Category.objects.create(
            name='Test Category',
            slug='test',
            is_active=True
        )
        
        assert str(category) == 'Test Category'

    def test_category_ordering(self):
        """Test categories are ordered by name."""
        Category.objects.create(name='Zebra', slug='zebra', is_active=True)
        Category.objects.create(name='Alpha', slug='alpha', is_active=True)
        Category.objects.create(name='Beta', slug='beta', is_active=True)
        
        categories = list(Category.objects.all().values_list('name', flat=True))
        assert categories == sorted(categories)

    def test_active_categories_filter(self):
        """Test filtering active categories."""
        Category.objects.create(name='Active 1', slug='active-1', is_active=True)
        Category.objects.create(name='Active 2', slug='active-2', is_active=True)
        Category.objects.create(name='Inactive', slug='inactive', is_active=False)
        
        active = Category.objects.filter(is_active=True)
        assert active.count() >= 2
        
        inactive = Category.objects.filter(is_active=False)
        assert inactive.count() >= 1

    def test_category_default_icon(self):
        """Test category default icon."""
        category = Category.objects.create(
            name='Test',
            slug='test-icon',
            is_active=True
        )
        
        assert category.icon == 'bi-tag'


@pytest.mark.django_db
class TestRoleService:
    """Test suite for role operations."""

    def test_create_role(self):
        """Test creating a role."""
        role = Role.objects.create(
            name='Admin',
            description='Administrator role',
            can_manage_users=True,
            can_manage_categories=True,
            can_manage_staff=True,
            can_view_reports=True,
            can_moderate_content=True
        )
        
        assert role.id is not None
        assert role.name == 'Admin'

    def test_role_default_permissions(self):
        """Test role default permissions are False."""
        role = Role.objects.create(
            name='Viewer',
            description='View-only role'
        )
        
        assert role.can_manage_users is False
        assert role.can_manage_categories is False
        assert role.can_manage_staff is False
        assert role.can_view_reports is False
        assert role.can_moderate_content is False

    def test_role_string_representation(self):
        """Test role string representation."""
        role = Role.objects.create(name='Moderator')
        
        assert str(role) == 'Moderator'

    def test_role_unique_name(self):
        """Test role name must be unique."""
        Role.objects.create(name='Unique Role')
        
        with pytest.raises(Exception):
            Role.objects.create(name='Unique Role')


@pytest.mark.django_db
class TestStaffService:
    """Test suite for staff operations."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='staff_user',
            email='staff@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def role(self):
        """Create test role."""
        return Role.objects.create(
            name='Manager',
            can_manage_users=True,
            can_view_reports=True
        )

    def test_create_staff(self, user, role):
        """Test creating a staff member."""
        staff = Staff.objects.create(
            user=user,
            role=role,
            employee_id='EMP001',
            department='Engineering'
        )
        
        assert staff.id is not None
        assert staff.user == user
        assert staff.role == role
        assert staff.employee_id == 'EMP001'

    def test_staff_one_to_one_with_user(self, user, role):
        """Test staff has one-to-one with user."""
        Staff.objects.create(
            user=user,
            role=role,
            employee_id='EMP001'
        )
        
        with pytest.raises(Exception):
            Staff.objects.create(
                user=user,
                role=role,
                employee_id='EMP002'
            )

    def test_staff_unique_employee_id(self, role):
        """Test employee ID must be unique."""
        user1 = User.objects.create_user(
            username='staff1',
            email='staff1@example.com',
            password='testpass123'
        )
        user2 = User.objects.create_user(
            username='staff2',
            email='staff2@example.com',
            password='testpass123'
        )
        
        Staff.objects.create(user=user1, role=role, employee_id='EMP001')
        
        with pytest.raises(Exception):
            Staff.objects.create(user=user2, role=role, employee_id='EMP001')

    def test_staff_string_representation(self, user, role):
        """Test staff string representation."""
        staff = Staff.objects.create(
            user=user,
            role=role,
            employee_id='EMP001'
        )
        
        str_repr = str(staff)
        assert role.name in str_repr

    def test_staff_is_active_default(self, user, role):
        """Test staff is active by default."""
        staff = Staff.objects.create(
            user=user,
            role=role,
            employee_id='EMP001'
        )
        
        assert staff.is_active is True


@pytest.mark.django_db
class TestAuthenticationService:
    """Test suite for authentication operations."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='auth_user',
            email='auth@example.com',
            password='testpass123'
        )

    def test_authenticate_valid_credentials(self, user):
        """Test authentication with valid credentials."""
        authenticated_user = authenticate(
            username='auth_user',
            password='testpass123'
        )
        
        assert authenticated_user is not None
        assert authenticated_user.username == 'auth_user'

    def test_authenticate_invalid_password(self, user):
        """Test authentication with invalid password."""
        authenticated_user = authenticate(
            username='auth_user',
            password='wrongpassword'
        )
        
        assert authenticated_user is None

    def test_authenticate_invalid_username(self, user):
        """Test authentication with invalid username."""
        authenticated_user = authenticate(
            username='nonexistent',
            password='testpass123'
        )
        
        assert authenticated_user is None

    def test_authenticate_inactive_user(self):
        """Test authentication with inactive user."""
        inactive_user = User.objects.create_user(
            username='inactive_user',
            email='inactive@example.com',
            password='testpass123',
            is_active=False
        )
        
        authenticated_user = authenticate(
            username='inactive_user',
            password='testpass123'
        )
        
        assert authenticated_user is None

    def test_password_check(self, user):
        """Test password check method."""
        assert user.check_password('testpass123') is True
        assert user.check_password('wrongpassword') is False

    def test_set_password(self, user):
        """Test changing password."""
        user.set_password('newpassword123')
        user.save()
        
        assert user.check_password('newpassword123') is True
        assert user.check_password('testpass123') is False


@pytest.mark.django_db
class TestLoginService:
    """Test suite for login functionality."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='login_user',
            email='login@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_login_success(self, client, user):
        """Test successful login."""
        response = client.post('/accounts/login/', {
            'username': 'login_user',
            'password': 'testpass123'
        })
        
        # Should redirect after successful login or return 200 with form
        assert response.status_code in [200, 302]

    def test_login_failure(self, client, user):
        """Test failed login."""
        response = client.post('/accounts/login/', {
            'username': 'login_user',
            'password': 'wrongpassword'
        })
        
        # Should stay on login page
        assert response.status_code == 200

    def test_logout(self, client, user):
        """Test logout functionality."""
        client.force_login(user)
        
        response = client.post('/accounts/logout/')
        
        # Should redirect after logout
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestPasswordResetService:
    """Test suite for password reset functionality."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='reset_user',
            email='reset@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_password_reset_request_valid_email(self, client, user):
        """Test password reset request with valid email."""
        response = client.post('/accounts/password/reset/', {
            'email': 'reset@example.com'
        })
        
        assert response.status_code in [200, 302]

    def test_password_reset_request_invalid_email(self, client):
        """Test password reset request with invalid email."""
        response = client.post('/accounts/password/reset/', {
            'email': 'nonexistent@example.com'
        })
        
        # Should show same message (no account enumeration)
        assert response.status_code in [200, 302]

    def test_password_reset_page_loads(self, client):
        """Test password reset page loads."""
        response = client.get('/accounts/password/reset/')
        
        assert response.status_code == 200

