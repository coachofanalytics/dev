"""
Tests for accounts models.
"""

import pytest
from django.contrib.auth.models import User
from django.db.utils import IntegrityError

from accounts.models import Category, UserProfile, Role, Staff


@pytest.mark.django_db
class TestCategoryModel:
    """Tests for Category model."""

    def test_create_category(self):
        """Test creating a category."""
        # Use unique name to avoid conflicts with existing data
        category = Category.objects.create(
            name="Test Investor Category",
            slug="test-investor",
            description="Investor category",
            is_active=True
        )
        assert category.name == "Test Investor Category"
        assert category.slug == "test-investor"
        assert category.is_active is True
        assert str(category) == "Test Investor Category"

    def test_category_unique_slug(self):
        """Test that category slug must be unique."""
        Category.objects.create(name="Test Slug 1", slug="test-unique-slug")
        with pytest.raises(IntegrityError):
            Category.objects.create(name="Test Slug 2", slug="test-unique-slug")


@pytest.mark.django_db
class TestUserProfileModel:
    """Tests for UserProfile model."""

    def test_user_profile_auto_created(self, create_user):
        """Test that UserProfile is automatically created when User is created."""
        user = create_user()
        assert hasattr(user, 'profile')
        assert isinstance(user.profile, UserProfile)
        assert user.profile.user == user

    def test_user_profile_with_category(self, create_user, sample_categories):
        """Test UserProfile with a category."""
        user = create_user()
        investor_category = Category.objects.get(name="Investor")
        user.profile.category = investor_category
        user.profile.save()

        assert user.profile.category == investor_category
        assert user.profile.category.name == "Investor"

    def test_user_profile_string_representation(self, create_user):
        """Test UserProfile string representation."""
        user = create_user(username="testuser")
        assert str(user.profile) == "testuser's profile"


@pytest.mark.django_db
class TestRoleModel:
    """Tests for Role model."""

    def test_create_role(self):
        """Test creating a role."""
        role = Role.objects.create(
            name="Admin",
            can_manage_users=True,
            can_manage_categories=True,
            can_manage_staff=True,
            can_view_reports=True,
            can_moderate_content=True
        )
        assert role.name == "Admin"
        assert role.can_manage_users is True
        assert str(role) == "Admin"

    def test_role_default_permissions(self):
        """Test that role has default permissions set to False."""
        role = Role.objects.create(name="Viewer")
        assert role.can_manage_users is False
        assert role.can_manage_categories is False
        assert role.can_manage_staff is False
        assert role.can_view_reports is False
        assert role.can_moderate_content is False


@pytest.mark.django_db
class TestStaffModel:
    """Tests for Staff model."""

    def test_create_staff(self, create_user):
        """Test creating a staff member."""
        user = create_user()
        role = Role.objects.create(name="Admin")
        staff = Staff.objects.create(
            user=user,
            role=role,
            department="IT"
        )
        assert staff.user == user
        assert staff.role == role
        assert staff.department == "IT"
        assert str(staff) == f"{user.username} - Admin"

    def test_staff_one_to_one_with_user(self, create_user):
        """Test that Staff has one-to-one relationship with User."""
        user = create_user()
        role = Role.objects.create(name="Admin")
        Staff.objects.create(user=user, role=role)

        # Try to create another staff with same user should raise error
        with pytest.raises(IntegrityError):
            Staff.objects.create(user=user, role=role)
