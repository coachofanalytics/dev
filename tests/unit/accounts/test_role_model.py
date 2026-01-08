"""
Comprehensive unit tests for Role model.
Tests role creation, permissions, validations, and edge cases.
"""
from django.test import TestCase
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import IntegrityError

Role = apps.get_model('accounts', 'Role')


class RoleModelBasicTests(TestCase):
    """Basic tests for Role model creation and representation."""

    def test_role_creation(self):
        """Test basic role creation."""
        role = Role.objects.create(name='Admin')
        self.assertEqual(role.name, 'Admin')

    def test_role_str_representation(self):
        """Test string representation returns name."""
        role = Role.objects.create(name='Manager')
        self.assertEqual(str(role), 'Manager')

    def test_role_with_description(self):
        """Test role creation with description."""
        role = Role.objects.create(
            name='Editor',
            description='Can edit content on the platform'
        )
        self.assertEqual(role.description, 'Can edit content on the platform')


class RoleUniqueConstraintTests(TestCase):
    """Tests for unique constraints on Role model."""

    def test_unique_name_constraint(self):
        """Test that role name must be unique."""
        Role.objects.create(name='Unique Role')
        with self.assertRaises(IntegrityError):
            Role.objects.create(name='Unique Role')


class RolePermissionTests(TestCase):
    """Tests for role permission fields."""

    def test_default_permissions_false(self):
        """Test all permissions default to False."""
        role = Role.objects.create(name='Default Role')
        self.assertFalse(role.can_manage_users)
        self.assertFalse(role.can_manage_categories)
        self.assertFalse(role.can_manage_staff)
        self.assertFalse(role.can_view_reports)
        self.assertFalse(role.can_moderate_content)

    def test_admin_role_full_permissions(self):
        """Test admin role with all permissions."""
        role = Role.objects.create(
            name='Admin',
            can_manage_users=True,
            can_manage_categories=True,
            can_manage_staff=True,
            can_view_reports=True,
            can_moderate_content=True
        )
        self.assertTrue(role.can_manage_users)
        self.assertTrue(role.can_manage_categories)
        self.assertTrue(role.can_manage_staff)
        self.assertTrue(role.can_view_reports)
        self.assertTrue(role.can_moderate_content)

    def test_moderator_role_limited_permissions(self):
        """Test moderator role with limited permissions."""
        role = Role.objects.create(
            name='Moderator',
            can_moderate_content=True,
            can_view_reports=True
        )
        self.assertFalse(role.can_manage_users)
        self.assertFalse(role.can_manage_categories)
        self.assertFalse(role.can_manage_staff)
        self.assertTrue(role.can_view_reports)
        self.assertTrue(role.can_moderate_content)

    def test_viewer_role_minimal_permissions(self):
        """Test viewer role with only view reports permission."""
        role = Role.objects.create(
            name='Viewer',
            can_view_reports=True
        )
        self.assertFalse(role.can_manage_users)
        self.assertFalse(role.can_manage_categories)
        self.assertFalse(role.can_manage_staff)
        self.assertTrue(role.can_view_reports)
        self.assertFalse(role.can_moderate_content)


class RoleFieldValidationTests(TestCase):
    """Tests for field validations."""

    def test_name_max_length(self):
        """Test name field max length (100 chars)."""
        role = Role(name='x' * 100)
        role.full_clean()

    def test_name_exceeds_max_length(self):
        """Test name exceeding max length raises error."""
        role = Role(name='x' * 101)
        with self.assertRaises(ValidationError):
            role.full_clean()

    def test_description_max_length(self):
        """Test description max length (300 chars)."""
        role = Role(name='Test', description='x' * 300)
        role.full_clean()

    def test_description_allows_empty(self):
        """Test description can be empty."""
        role = Role(name='Test', description='')
        role.full_clean()  # Should not raise


class RoleMetaOptionsTests(TestCase):
    """Tests for Meta class options."""

    def test_ordering_by_name(self):
        """Test roles are ordered by name."""
        Role.objects.create(name='Zebra')
        Role.objects.create(name='Admin')
        Role.objects.create(name='Manager')
        
        roles = list(Role.objects.all())
        names = [r.name for r in roles]
        self.assertEqual(names, ['Admin', 'Manager', 'Zebra'])

    def test_verbose_name(self):
        """Test verbose name meta option."""
        self.assertEqual(Role._meta.verbose_name, 'Role')

    def test_verbose_name_plural(self):
        """Test verbose name plural meta option."""
        self.assertEqual(Role._meta.verbose_name_plural, 'Roles')


class RoleTimestampTests(TestCase):
    """Tests for timestamp fields."""

    def test_created_at_auto_set(self):
        """Test created_at is automatically set."""
        role = Role.objects.create(name='Timestamp Test')
        self.assertIsNotNone(role.created_at)

    def test_updated_at_changes_on_save(self):
        """Test updated_at changes when saved."""
        role = Role.objects.create(name='Update Test')
        original_updated = role.updated_at
        
        role.description = 'Updated'
        role.save()
        role.refresh_from_db()
        
        self.assertGreaterEqual(role.updated_at, original_updated)

