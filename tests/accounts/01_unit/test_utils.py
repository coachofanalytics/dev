"""
Unit tests for accounts utility functions

Tests user queryset filters and helper functions.

Author: CODA Development Team
Created: November 6, 2025
Category: Unit Tests
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.choices import UserCategory
from accounts.utilities.user_querysets import (
    get_active_staff_queryset,
    get_active_managers_queryset,
    get_active_executives_queryset,
    get_active_investors_queryset,
    get_active_students_queryset,
    get_active_consultants_queryset,
    get_active_applicants_queryset,
    get_active_explorers_queryset,
    get_active_staff_and_investors_queryset,
    get_active_students_and_staff_queryset,
    get_users_by_categories,
    get_staff_by_level,
)

User = get_user_model()


class UserQuerysetFiltersTest(TestCase):
    """
    Test user queryset filtering functions
    
    These functions were created on Nov 5, 2025 to solve the user filtering problem:
    - Forms were showing ALL users (100+) instead of filtered users
    - Dropdowns included inactive users and wrong categories
    
    Critical for security and UX across the entire platform.
    """
    
    def setUp(self):
        """Create comprehensive test user base"""
        # ===== INVESTORS (Category 4) =====
        self.investor1 = User.objects.create_user(
            username='investor1',
            email='investor1@test.com',
            category=UserCategory.INVESTOR,
            is_active=True,
            first_name='Alice',
            last_name='Investor'
        )
        
        self.investor2 = User.objects.create_user(
            username='investor2',
            email='investor2@test.com',
            category=UserCategory.INVESTOR,
            is_active=True,
            first_name='Bob',
            last_name='Investor'
        )
        
        self.inactive_investor = User.objects.create_user(
            username='inactive_investor',
            email='inactive_investor@test.com',
            category=UserCategory.INVESTOR,
            is_active=False,  # INACTIVE
            first_name='Inactive',
            last_name='Investor'
        )
        
        # ===== STUDENTS (Category 2) =====
        self.student1 = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            category=UserCategory.STUDENT,
            is_active=True,
            first_name='Charlie',
            last_name='Student'
        )
        
        self.student2 = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            category=UserCategory.STUDENT,
            is_active=True,
            first_name='Diana',
            last_name='Student'
        )
        
        # ===== CONSULTANTS (Category 3) =====
        self.consultant1 = User.objects.create_user(
            username='consultant1',
            email='consultant1@test.com',
            category=UserCategory.CONSULTANT,
            is_active=True,
            first_name='Eve',
            last_name='Consultant'
        )
        
        # ===== APPLICANTS (Category 1) =====
        self.applicant1 = User.objects.create_user(
            username='applicant1',
            email='applicant1@test.com',
            category=UserCategory.APPLICANT,
            is_active=True,
            first_name='Frank',
            last_name='Applicant'
        )
        
        # ===== EXPLORERS (Category 5) =====
        self.explorer1 = User.objects.create_user(
            username='explorer1',
            email='explorer1@test.com',
            category=UserCategory.EXPLORER,
            is_active=True,
            first_name='Grace',
            last_name='Explorer'
        )
        
        # ===== STAFF =====
        self.staff1 = User.objects.create_user(
            username='staff1',
            email='staff1@test.com',
            is_staff=True,
            is_active=True,
            first_name='Henry',
            last_name='Staff'
        )
        
        self.staff2 = User.objects.create_user(
            username='staff2',
            email='staff2@test.com',
            is_staff=True,
            is_active=True,
            first_name='Iris',
            last_name='Staff'
        )
        
        self.inactive_staff = User.objects.create_user(
            username='inactive_staff',
            email='inactive_staff@test.com',
            is_staff=True,
            is_active=False,  # INACTIVE
            first_name='Inactive',
            last_name='Staff'
        )


class StaffQuerysetTest(UserQuerysetFiltersTest):
    """Test staff-related querysets"""
    
    def test_get_active_staff_queryset_returns_only_active_staff(self):
        """Test that get_active_staff_queryset returns only active staff"""
        staff = get_active_staff_queryset()
        
        # Should have 2 active staff
        self.assertEqual(staff.count(), 2)
        
        # Should include active staff
        self.assertIn(self.staff1, staff)
        self.assertIn(self.staff2, staff)
        
        # Should NOT include inactive staff
        self.assertNotIn(self.inactive_staff, staff)
        
        # Should NOT include non-staff
        self.assertNotIn(self.investor1, staff)
        self.assertNotIn(self.student1, staff)
    
    def test_get_active_staff_queryset_ordering(self):
        """Test that staff queryset is ordered by first_name, last_name"""
        staff = list(get_active_staff_queryset())
        
        # Henry comes before Iris alphabetically
        self.assertEqual(staff[0], self.staff1)  # Henry
        self.assertEqual(staff[1], self.staff2)  # Iris


class CategoryQuerysetTest(UserQuerysetFiltersTest):
    """Test category-based querysets"""
    
    def test_get_active_investors_queryset(self):
        """Test that get_active_investors_queryset returns only active investors"""
        investors = get_active_investors_queryset()
        
        # Should have 2 active investors
        self.assertEqual(investors.count(), 2)
        
        # Should include active investors
        self.assertIn(self.investor1, investors)
        self.assertIn(self.investor2, investors)
        
        # Should NOT include inactive investor
        self.assertNotIn(self.inactive_investor, investors)
        
        # Should NOT include other categories
        self.assertNotIn(self.student1, investors)
        self.assertNotIn(self.staff1, investors)
    
    def test_get_active_students_queryset(self):
        """Test that get_active_students_queryset returns only active students"""
        students = get_active_students_queryset()
        
        # Should have 2 active students
        self.assertEqual(students.count(), 2)
        
        # Should include active students
        self.assertIn(self.student1, students)
        self.assertIn(self.student2, students)
        
        # Should NOT include other categories
        self.assertNotIn(self.investor1, students)
        self.assertNotIn(self.staff1, students)
    
    def test_get_active_consultants_queryset(self):
        """Test that get_active_consultants_queryset returns only active consultants"""
        consultants = get_active_consultants_queryset()
        
        # Should have 1 consultant
        self.assertEqual(consultants.count(), 1)
        self.assertIn(self.consultant1, consultants)
        
        # Should NOT include other categories
        self.assertNotIn(self.investor1, consultants)
        self.assertNotIn(self.student1, consultants)
    
    def test_get_active_applicants_queryset(self):
        """Test that get_active_applicants_queryset returns only active applicants"""
        applicants = get_active_applicants_queryset()
        
        # Should have 1 applicant
        self.assertEqual(applicants.count(), 1)
        self.assertIn(self.applicant1, applicants)
        
        # Should NOT include other categories
        self.assertNotIn(self.investor1, applicants)
        self.assertNotIn(self.student1, applicants)
    
    def test_get_active_explorers_queryset(self):
        """Test that get_active_explorers_queryset returns only active explorers"""
        explorers = get_active_explorers_queryset()
        
        # Should have 1 explorer
        self.assertEqual(explorers.count(), 1)
        self.assertIn(self.explorer1, explorers)
        
        # Should NOT include other categories
        self.assertNotIn(self.investor1, explorers)
        self.assertNotIn(self.student1, explorers)


class CombinedQuerysetTest(UserQuerysetFiltersTest):
    """Test combined querysets (multiple categories)"""
    
    def test_get_active_staff_and_investors_queryset(self):
        """Test that combined queryset includes staff AND investors"""
        combined = get_active_staff_and_investors_queryset()
        
        # Should have 2 staff + 2 investors = 4 users
        self.assertEqual(combined.count(), 4)
        
        # Should include staff
        self.assertIn(self.staff1, combined)
        self.assertIn(self.staff2, combined)
        
        # Should include investors
        self.assertIn(self.investor1, combined)
        self.assertIn(self.investor2, combined)
        
        # Should NOT include inactive users
        self.assertNotIn(self.inactive_staff, combined)
        self.assertNotIn(self.inactive_investor, combined)
        
        # Should NOT include other categories
        self.assertNotIn(self.student1, combined)
        self.assertNotIn(self.consultant1, combined)
    
    def test_get_active_students_and_staff_queryset(self):
        """Test that combined queryset includes students AND staff"""
        combined = get_active_students_and_staff_queryset()
        
        # Should have 2 staff + 2 students = 4 users
        self.assertEqual(combined.count(), 4)
        
        # Should include staff
        self.assertIn(self.staff1, combined)
        self.assertIn(self.staff2, combined)
        
        # Should include students
        self.assertIn(self.student1, combined)
        self.assertIn(self.student2, combined)
        
        # Should NOT include investors
        self.assertNotIn(self.investor1, combined)


class UtilityFunctionTest(UserQuerysetFiltersTest):
    """Test utility functions for advanced filtering"""
    
    def test_get_users_by_categories_single_category(self):
        """Test get_users_by_categories with single category"""
        investors = get_users_by_categories([UserCategory.INVESTOR])
        
        self.assertEqual(investors.count(), 2)
        self.assertIn(self.investor1, investors)
        self.assertIn(self.investor2, investors)
    
    def test_get_users_by_categories_multiple_categories(self):
        """Test get_users_by_categories with multiple categories"""
        users = get_users_by_categories([
            UserCategory.INVESTOR,
            UserCategory.CONSULTANT
        ])
        
        # Should have 2 investors + 1 consultant = 3 users
        self.assertEqual(users.count(), 3)
        self.assertIn(self.investor1, users)
        self.assertIn(self.investor2, users)
        self.assertIn(self.consultant1, users)
    
    def test_get_users_by_categories_includes_inactive_when_specified(self):
        """Test that get_users_by_categories can include inactive users"""
        investors = get_users_by_categories(
            [UserCategory.INVESTOR],
            active_only=False
        )
        
        # Should have 3 investors (including inactive)
        self.assertEqual(investors.count(), 3)
        self.assertIn(self.inactive_investor, investors)


class InactiveUserSecurityTest(UserQuerysetFiltersTest):
    """
    Critical security test: Inactive users should NEVER appear
    
    This is a regression test for the user filtering security issue.
    Inactive users must be completely hidden from all filtered querysets.
    """
    
    def test_inactive_users_never_in_any_active_queryset(self):
        """Test that inactive users do not appear in ANY active queryset"""
        # Get all active querysets
        staff = get_active_staff_queryset()
        investors = get_active_investors_queryset()
        students = get_active_students_queryset()
        consultants = get_active_consultants_queryset()
        applicants = get_active_applicants_queryset()
        explorers = get_active_explorers_queryset()
        
        # Inactive investor should not appear anywhere
        self.assertNotIn(self.inactive_investor, staff)
        self.assertNotIn(self.inactive_investor, investors)
        self.assertNotIn(self.inactive_investor, students)
        self.assertNotIn(self.inactive_investor, consultants)
        self.assertNotIn(self.inactive_investor, applicants)
        self.assertNotIn(self.inactive_investor, explorers)
        
        # Inactive staff should not appear anywhere
        self.assertNotIn(self.inactive_staff, staff)
        self.assertNotIn(self.inactive_staff, investors)
        self.assertNotIn(self.inactive_staff, students)
        self.assertNotIn(self.inactive_staff, consultants)
        self.assertNotIn(self.inactive_staff, applicants)
        self.assertNotIn(self.inactive_staff, explorers)
    
    def test_inactive_users_not_in_combined_querysets(self):
        """Test that inactive users don't appear in combined querysets"""
        staff_and_investors = get_active_staff_and_investors_queryset()
        students_and_staff = get_active_students_and_staff_queryset()
        
        # Inactive users should not appear
        self.assertNotIn(self.inactive_investor, staff_and_investors)
        self.assertNotIn(self.inactive_staff, staff_and_investors)
        self.assertNotIn(self.inactive_staff, students_and_staff)


class QuerysetCountTest(UserQuerysetFiltersTest):
    """
    Test that querysets return reasonable counts (not 100+)
    
    Before Nov 5 fix: Forms showed 100+ users
    After Nov 5 fix: Forms show 2-20 relevant users
    """
    
    def test_querysets_return_small_reasonable_counts(self):
        """Test that all querysets return small, reasonable user counts"""
        # All these should be small numbers (< 20 in our test data)
        self.assertLess(get_active_staff_queryset().count(), 20)
        self.assertLess(get_active_investors_queryset().count(), 20)
        self.assertLess(get_active_students_queryset().count(), 20)
        self.assertLess(get_active_consultants_queryset().count(), 20)
        self.assertLess(get_active_applicants_queryset().count(), 20)
        
        # These should be even smaller in our test data
        self.assertEqual(get_active_staff_queryset().count(), 2)
        self.assertEqual(get_active_investors_queryset().count(), 2)
        self.assertEqual(get_active_students_queryset().count(), 2)
        self.assertEqual(get_active_consultants_queryset().count(), 1)
        self.assertEqual(get_active_applicants_queryset().count(), 1)
