"""
Comprehensive unit tests for Staff model.
Tests staff creation, role assignment, validations, and edge cases.
"""
from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date

User = get_user_model()
Staff = apps.get_model('accounts', 'Staff')
Role = apps.get_model('accounts', 'Role')


class StaffModelBasicTests(TestCase):
    """Basic tests for Staff model creation and representation."""

    def setUp(self):
        self.user = User.objects.create_user(username='staffuser', password='pass')
        self.role = Role.objects.create(name='Admin')

    def test_staff_creation(self):
        """Test basic staff creation."""
        staff = Staff.objects.create(
            user=self.user,
            role=self.role,
            employee_id='EMP001'
        )
        self.assertEqual(staff.employee_id, 'EMP001')

    def test_staff_str_representation_with_name(self):
        """Test string representation with user's full name."""
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.save()
        
        staff = Staff.objects.create(
            user=self.user,
            role=self.role,
            employee_id='EMP001'
        )
        self.assertEqual(str(staff), 'John Doe - Admin')

    def test_staff_str_representation_without_name(self):
        """Test string representation with username."""
        staff = Staff.objects.create(
            user=self.user,
            role=self.role,
            employee_id='EMP001'
        )
        self.assertEqual(str(staff), 'staffuser - Admin')


class StaffUniqueConstraintTests(TestCase):
    """Tests for unique constraints on Staff model."""

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass')
        self.user2 = User.objects.create_user(username='user2', password='pass')
        self.role = Role.objects.create(name='Admin')

    def test_unique_employee_id_constraint(self):
        """Test that employee_id must be unique."""
        Staff.objects.create(user=self.user1, role=self.role, employee_id='EMP001')
        with self.assertRaises(IntegrityError):
            Staff.objects.create(user=self.user2, role=self.role, employee_id='EMP001')

    def test_one_to_one_user_constraint(self):
        """Test that each user can only have one staff record."""
        Staff.objects.create(user=self.user1, role=self.role, employee_id='EMP001')
        with self.assertRaises(IntegrityError):
            Staff.objects.create(user=self.user1, role=self.role, employee_id='EMP002')


class StaffRoleTests(TestCase):
    """Tests for staff role relationship."""

    def setUp(self):
        self.user = User.objects.create_user(username='roletest', password='pass')
        self.admin_role = Role.objects.create(name='Admin', can_manage_users=True)
        self.viewer_role = Role.objects.create(name='Viewer', can_view_reports=True)

    def test_staff_with_role(self):
        """Test staff creation with role."""
        staff = Staff.objects.create(
            user=self.user,
            role=self.admin_role,
            employee_id='EMP001'
        )
        self.assertEqual(staff.role.name, 'Admin')
        self.assertTrue(staff.role.can_manage_users)

    def test_staff_role_set_null_on_delete(self):
        """Test that role is set to null when role is deleted."""
        staff = Staff.objects.create(
            user=self.user,
            role=self.admin_role,
            employee_id='EMP001'
        )
        self.admin_role.delete()
        staff.refresh_from_db()
        self.assertIsNone(staff.role)

    def test_change_staff_role(self):
        """Test changing staff role."""
        staff = Staff.objects.create(
            user=self.user,
            role=self.admin_role,
            employee_id='EMP001'
        )
        staff.role = self.viewer_role
        staff.save()
        staff.refresh_from_db()
        self.assertEqual(staff.role.name, 'Viewer')


class StaffFieldValidationTests(TestCase):
    """Tests for field validations."""

    def setUp(self):
        self.user = User.objects.create_user(username='fieldtest', password='pass')
        self.role = Role.objects.create(name='Admin')

    def test_employee_id_max_length(self):
        """Test employee_id max length (20 chars)."""
        staff = Staff(user=self.user, role=self.role, employee_id='x' * 20)
        staff.full_clean()

    def test_employee_id_exceeds_max_length(self):
        """Test employee_id exceeding max length raises error."""
        staff = Staff(user=self.user, role=self.role, employee_id='x' * 21)
        with self.assertRaises(ValidationError):
            staff.full_clean()

    def test_department_max_length(self):
        """Test department max length (100 chars)."""
        staff = Staff(
            user=self.user,
            role=self.role,
            employee_id='EMP001',
            department='x' * 100
        )
        staff.full_clean()


class StaffActiveStatusTests(TestCase):
    """Tests for is_active field behavior."""

    def setUp(self):
        self.user = User.objects.create_user(username='activetest', password='pass')
        self.role = Role.objects.create(name='Admin')

    def test_default_is_active(self):
        """Test is_active defaults to True."""
        staff = Staff.objects.create(
            user=self.user,
            role=self.role,
            employee_id='EMP001'
        )
        self.assertTrue(staff.is_active)

    def test_inactive_staff(self):
        """Test creating inactive staff."""
        staff = Staff.objects.create(
            user=self.user,
            role=self.role,
            employee_id='EMP001',
            is_active=False
        )
        self.assertFalse(staff.is_active)

    def test_deactivate_staff(self):
        """Test deactivating active staff."""
        staff = Staff.objects.create(
            user=self.user,
            role=self.role,
            employee_id='EMP001'
        )
        staff.is_active = False
        staff.save()
        staff.refresh_from_db()
        self.assertFalse(staff.is_active)


class StaffHiredDateTests(TestCase):
    """Tests for hired_date field."""

    def setUp(self):
        self.user = User.objects.create_user(username='hiredtest', password='pass')
        self.role = Role.objects.create(name='Admin')

    def test_hired_date_null(self):
        """Test hired_date can be null."""
        staff = Staff.objects.create(
            user=self.user,
            role=self.role,
            employee_id='EMP001'
        )
        self.assertIsNone(staff.hired_date)

    def test_hired_date_set(self):
        """Test setting hired_date."""
        hired = date(2024, 1, 15)
        staff = Staff.objects.create(
            user=self.user,
            role=self.role,
            employee_id='EMP001',
            hired_date=hired
        )
        self.assertEqual(staff.hired_date, hired)


class StaffNotesTests(TestCase):
    """Tests for notes field."""

    def setUp(self):
        self.user = User.objects.create_user(username='notestest', password='pass')
        self.role = Role.objects.create(name='Admin')

    def test_notes_blank(self):
        """Test notes can be blank."""
        staff = Staff.objects.create(
            user=self.user,
            role=self.role,
            employee_id='EMP001'
        )
        self.assertEqual(staff.notes, '')

    def test_notes_with_content(self):
        """Test notes with content."""
        staff = Staff.objects.create(
            user=self.user,
            role=self.role,
            employee_id='EMP001',
            notes='Internal note about this staff member'
        )
        self.assertEqual(staff.notes, 'Internal note about this staff member')


class StaffMetaOptionsTests(TestCase):
    """Tests for Meta class options."""

    def test_ordering_by_created_at_desc(self):
        """Test staff are ordered by created_at descending."""
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')
        role = Role.objects.create(name='Admin')
        
        Staff.objects.create(user=user1, role=role, employee_id='EMP001')
        Staff.objects.create(user=user2, role=role, employee_id='EMP002')
        
        staff_list = list(Staff.objects.all())
        self.assertEqual(staff_list[0].employee_id, 'EMP002')  # Most recent first

    def test_verbose_name(self):
        """Test verbose name meta option."""
        self.assertEqual(Staff._meta.verbose_name, 'Staff')

    def test_verbose_name_plural(self):
        """Test verbose name plural meta option."""
        self.assertEqual(Staff._meta.verbose_name_plural, 'Staff')


class StaffTimestampTests(TestCase):
    """Tests for timestamp fields."""

    def setUp(self):
        self.user = User.objects.create_user(username='timestamp', password='pass')
        self.role = Role.objects.create(name='Admin')

    def test_created_at_auto_set(self):
        """Test created_at is automatically set."""
        staff = Staff.objects.create(
            user=self.user,
            role=self.role,
            employee_id='EMP001'
        )
        self.assertIsNotNone(staff.created_at)

    def test_updated_at_changes_on_save(self):
        """Test updated_at changes when saved."""
        staff = Staff.objects.create(
            user=self.user,
            role=self.role,
            employee_id='EMP001'
        )
        original_updated = staff.updated_at
        
        staff.department = 'Engineering'
        staff.save()
        staff.refresh_from_db()
        
        self.assertGreaterEqual(staff.updated_at, original_updated)


class StaffUserDeleteTests(TestCase):
    """Tests for cascade delete behavior."""

    def test_staff_deleted_when_user_deleted(self):
        """Test that staff record is deleted when user is deleted."""
        user = User.objects.create_user(username='cascade_test', password='pass')
        role = Role.objects.create(name='Admin')
        Staff.objects.create(user=user, role=role, employee_id='EMP001')
        
        user_id = user.id
        user.delete()
        
        self.assertFalse(Staff.objects.filter(user_id=user_id).exists())

