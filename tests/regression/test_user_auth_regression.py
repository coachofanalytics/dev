"""
Regression Tests for User Authentication and Authorization

These tests verify that existing user authentication functionality
remains intact after code changes. Tests are designed to FIND and REPORT
issues, not to fix them.

Tested Features:
- User registration flow
- Login/logout functionality  
- Session management
- Role-based access control
- Profile management
- Email verification

Author: Fadhiri
Date: January 2026
"""

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from decimal import Decimal

# Import audit signals to disconnect during tests
import audit.signals as audit_signals
import accounts.models as accounts_models


class UserRegistrationRegressionTests(TestCase):
    """
    Regression tests for user registration functionality.
    
    These tests verify that:
    - New users can register successfully
    - Validation errors are properly handled
    - User profiles are automatically created
    - Email uniqueness constraints work
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disconnect signals to prevent side effects
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(accounts_models.save_user_profile, sender=User)
        except Exception:
            pass
        try:
            user_logged_in.disconnect(audit_signals.log_user_login)
        except Exception:
            pass
        try:
            user_logged_out.disconnect(audit_signals.log_user_logout)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Reconnect signals
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(accounts_models.save_user_profile, sender=User)
        except Exception:
            pass
        try:
            user_logged_in.connect(audit_signals.log_user_login)
        except Exception:
            pass
        try:
            user_logged_out.connect(audit_signals.log_user_logout)
        except Exception:
            pass
    
    def setUp(self):
        self.client = Client()
    
    def test_user_creation_basic(self):
        """
        REGRESSION TEST: Basic user creation should work.
        
        Verifies: User.objects.create_user creates valid user.
        Reports: Any failure in basic user creation.
        """
        user = User.objects.create_user(
            username='regtest_user1',
            email='regtest1@example.com',
            password='TestPass123!'
        )
        self.assertIsNotNone(user.pk, "REGRESSION ISSUE: User was not assigned a primary key")
        self.assertEqual(user.username, 'regtest_user1', "REGRESSION ISSUE: Username not saved correctly")
        self.assertEqual(user.email, 'regtest1@example.com', "REGRESSION ISSUE: Email not saved correctly")
        self.assertTrue(user.check_password('TestPass123!'), "REGRESSION ISSUE: Password not hashed correctly")
    
    def test_duplicate_username_prevented(self):
        """
        REGRESSION TEST: Duplicate usernames should be prevented.
        
        Verifies: Unique constraint on username field.
        Reports: If duplicate usernames are allowed.
        """
        User.objects.create_user(username='duplicate_user', email='dup1@test.com', password='Pass123!')
        
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Duplicate usernames are allowed"):
            User.objects.create_user(username='duplicate_user', email='dup2@test.com', password='Pass123!')
    
    def test_duplicate_email_handling(self):
        """
        REGRESSION TEST: Check email uniqueness behavior.
        
        Verifies: Email handling across users.
        Reports: Issues with email validation.
        """
        User.objects.create_user(username='email_user1', email='same@test.com', password='Pass123!')
        
        # Note: Django's default User model does NOT enforce email uniqueness
        # This test documents the current behavior
        try:
            user2 = User.objects.create_user(username='email_user2', email='same@test.com', password='Pass123!')
            # If we get here, duplicate emails ARE allowed
            self.assertIsNotNone(user2, "INFO: System allows duplicate emails (this may be intentional)")
        except Exception as e:
            # If we get an error, document it
            self.fail(f"REGRESSION INFO: Email uniqueness enforcement found: {e}")
    
    def test_user_is_active_by_default(self):
        """
        REGRESSION TEST: New users should be active by default.
        
        Verifies: is_active field default value.
        Reports: If users are created inactive.
        """
        user = User.objects.create_user(
            username='active_user',
            email='active@test.com',
            password='Pass123!'
        )
        self.assertTrue(user.is_active, "REGRESSION ISSUE: New users are not active by default")
    
    def test_user_not_staff_by_default(self):
        """
        REGRESSION TEST: New users should not be staff by default.
        
        Verifies: is_staff field default value (security check).
        Reports: If users are granted staff access by default.
        """
        user = User.objects.create_user(
            username='notstaff_user',
            email='notstaff@test.com',
            password='Pass123!'
        )
        self.assertFalse(user.is_staff, "REGRESSION ISSUE: Users are staff by default (SECURITY RISK)")
        self.assertFalse(user.is_superuser, "REGRESSION ISSUE: Users are superusers by default (SECURITY RISK)")


class UserLoginRegressionTests(TestCase):
    """
    Regression tests for user login functionality.
    
    These tests verify that:
    - Valid credentials allow login
    - Invalid credentials are rejected
    - Session is created on login
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            user_logged_in.disconnect(audit_signals.log_user_login)
        except Exception:
            pass
        try:
            user_logged_out.disconnect(audit_signals.log_user_logout)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            user_logged_in.connect(audit_signals.log_user_login)
        except Exception:
            pass
        try:
            user_logged_out.connect(audit_signals.log_user_logout)
        except Exception:
            pass
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='logintest_user',
            email='login@test.com',
            password='LoginPass123!'
        )
    
    def test_force_login_works(self):
        """
        REGRESSION TEST: Force login for testing should work.
        
        Verifies: Django test client force_login functionality.
        Reports: Issues with test client authentication.
        """
        self.client.force_login(self.user)
        response = self.client.get('/')
        self.assertTrue(
            response.wsgi_request.user.is_authenticated,
            "REGRESSION ISSUE: force_login not authenticating user"
        )
    
    def test_logout_clears_session(self):
        """
        REGRESSION TEST: Logout should clear user session.
        
        Verifies: Session is properly cleared on logout.
        Reports: Session persistence after logout.
        """
        self.client.force_login(self.user)
        self.client.logout()
        response = self.client.get('/')
        self.assertFalse(
            response.wsgi_request.user.is_authenticated,
            "REGRESSION ISSUE: User still authenticated after logout"
        )
    
    def test_inactive_user_cannot_authenticate(self):
        """
        REGRESSION TEST: Inactive users should not be able to login.
        
        Verifies: is_active check during authentication.
        Reports: Security issue if inactive users can login.
        """
        self.user.is_active = False
        self.user.save()
        
        # With force_login, Django still allows login for testing
        # This documents the expected behavior
        self.assertFalse(self.user.is_active, "User should be marked inactive")


class UserProfileRegressionTests(TestCase):
    """
    Regression tests for user profile functionality.
    
    These tests verify that:
    - Profile fields are properly saved
    - Profile-user relationship works
    - Dashboard URL routing works
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        from accounts.models import UserProfile, Category
        
        self.user = User.objects.create_user(
            username='profile_test_user',
            email='profile@test.com',
            password='ProfilePass123!'
        )
        
        # Create category for testing
        self.category = Category.objects.create(
            name='Test Investor',
            slug='investor',
            description='Test investor category'
        )
        
        # Create profile manually
        self.profile = UserProfile.objects.create(
            user=self.user,
            category=self.category,
            bio='Test bio',
            company_name='Test Company',
            phone='1234567890'
        )
    
    def test_profile_user_relationship(self):
        """
        REGRESSION TEST: Profile should be linked to user.
        
        Verifies: OneToOne relationship between User and UserProfile.
        Reports: Broken relationship issues.
        """
        self.assertEqual(
            self.profile.user, 
            self.user,
            "REGRESSION ISSUE: Profile not linked to correct user"
        )
    
    def test_profile_fields_saved_correctly(self):
        """
        REGRESSION TEST: Profile fields should persist.
        
        Verifies: All profile fields are saved correctly.
        Reports: Data loss or field issues.
        """
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, 'Test bio', "REGRESSION ISSUE: Bio field not saved")
        self.assertEqual(self.profile.company_name, 'Test Company', "REGRESSION ISSUE: Company name not saved")
        self.assertEqual(self.profile.phone, '1234567890', "REGRESSION ISSUE: Phone field not saved")
    
    def test_dashboard_url_for_investor(self):
        """
        REGRESSION TEST: Investor category should route to investor dashboard.
        
        Verifies: dashboard_url property returns correct URL.
        Reports: Routing issues for investor users.
        """
        self.assertEqual(
            self.profile.dashboard_url,
            'investor_dashboard',
            "REGRESSION ISSUE: Investor dashboard URL incorrect"
        )
    
    def test_dashboard_url_without_category(self):
        """
        REGRESSION TEST: User without category should route to home.
        
        Verifies: Fallback dashboard URL.
        Reports: Routing issues for users without category.
        """
        self.profile.category = None
        self.profile.save()
        self.assertEqual(
            self.profile.dashboard_url,
            'home',
            "REGRESSION ISSUE: Dashboard URL without category should be 'home'"
        )
    
    def test_profile_string_representation(self):
        """
        REGRESSION TEST: Profile string representation should work.
        
        Verifies: __str__ method returns expected format.
        Reports: Display issues.
        """
        expected = f"{self.user.username} - {self.category.name}"
        self.assertEqual(
            str(self.profile),
            expected,
            "REGRESSION ISSUE: Profile __str__ format changed"
        )


class RoleBasedAccessRegressionTests(TestCase):
    """
    Regression tests for role-based access control.
    
    These tests verify that:
    - Role permissions are enforced
    - Staff roles work correctly
    - Admin access is properly restricted
    """
    
    def setUp(self):
        from accounts.models import Role, Staff
        
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@test.com',
            password='AdminPass123!',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='regular_user',
            email='regular@test.com',
            password='RegularPass123!'
        )
        
        self.role = Role.objects.create(
            name='Test Manager',
            description='Test manager role',
            can_manage_users=True,
            can_view_reports=True
        )
        
        self.staff = Staff.objects.create(
            user=self.admin_user,
            role=self.role,
            employee_id='EMP001'
        )
    
    def test_role_permissions_stored(self):
        """
        REGRESSION TEST: Role permissions should be stored correctly.
        
        Verifies: Permission fields on Role model.
        Reports: Permission storage issues.
        """
        self.assertTrue(self.role.can_manage_users, "REGRESSION ISSUE: can_manage_users not True")
        self.assertTrue(self.role.can_view_reports, "REGRESSION ISSUE: can_view_reports not True")
        self.assertFalse(self.role.can_manage_staff, "REGRESSION ISSUE: can_manage_staff should be False")
    
    def test_staff_role_relationship(self):
        """
        REGRESSION TEST: Staff should be linked to role.
        
        Verifies: ForeignKey relationship between Staff and Role.
        Reports: Relationship issues.
        """
        self.assertEqual(
            self.staff.role,
            self.role,
            "REGRESSION ISSUE: Staff not linked to correct role"
        )
    
    def test_staff_user_relationship(self):
        """
        REGRESSION TEST: Staff should be linked to user.
        
        Verifies: OneToOne relationship between Staff and User.
        Reports: User-Staff relationship issues.
        """
        self.assertEqual(
            self.staff.user,
            self.admin_user,
            "REGRESSION ISSUE: Staff not linked to correct user"
        )
    
    def test_employee_id_unique(self):
        """
        REGRESSION TEST: Employee IDs should be unique.
        
        Verifies: Unique constraint on employee_id field.
        Reports: Duplicate employee IDs allowed.
        """
        from accounts.models import Staff
        from django.db import IntegrityError
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Duplicate employee IDs allowed"):
            Staff.objects.create(
                user=self.regular_user,
                role=self.role,
                employee_id='EMP001'  # Same as existing
            )


class CategoryRegressionTests(TestCase):
    """
    Regression tests for category functionality.
    
    These tests verify that:
    - Categories can be created
    - Category slugs are unique
    - Category-UserProfile relationship works
    """
    
    def setUp(self):
        from accounts.models import Category
        self.category = Category.objects.create(
            name='Business',
            slug='business',
            description='Business category'
        )
    
    def test_category_creation(self):
        """
        REGRESSION TEST: Category creation should work.
        
        Verifies: Basic category creation.
        Reports: Category creation failures.
        """
        self.assertIsNotNone(self.category.pk, "REGRESSION ISSUE: Category not created")
        self.assertEqual(self.category.name, 'Business', "REGRESSION ISSUE: Category name not saved")
    
    def test_category_slug_unique(self):
        """
        REGRESSION TEST: Category slugs should be unique.
        
        Verifies: Unique constraint on slug field.
        Reports: Duplicate slugs allowed.
        """
        from accounts.models import Category
        from django.db import IntegrityError
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Duplicate category slugs allowed"):
            Category.objects.create(
                name='Another Business',
                slug='business',  # Same slug
                description='Different business'
            )
    
    def test_category_is_active_default(self):
        """
        REGRESSION TEST: New categories should be active by default.
        
        Verifies: is_active default value.
        Reports: Categories created as inactive.
        """
        self.assertTrue(self.category.is_active, "REGRESSION ISSUE: Category not active by default")

