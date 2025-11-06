"""
Unit tests for main models

Tests individual model methods, properties, validation, and business logic.

Author: CODA Development Team
Created: November 6, 2025
Category: Unit Tests
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

from main.models import Service, Assets, Department, TeamInfo, OurTeam
from accounts.choices import UserCategory

User = get_user_model()


class ServiceModelTest(TestCase):
    """Test Service model"""
    
    def setUp(self):
        """Set up test data"""
        self.service = Service.objects.create(
            title='Test Service',
            description='This is a test service',
            is_active=True,
        )
    
    def test_service_creation(self):
        """Test that service can be created"""
        self.assertEqual(self.service.title, 'Test Service')
        self.assertTrue(self.service.is_active)
    
    def test_service_str_method(self):
        """Test __str__ method returns title"""
        self.assertEqual(str(self.service), 'Test Service')
    
    def test_inactive_service_not_in_active_queryset(self):
        """Test that inactive services are excluded from active queryset"""
        # Create inactive service
        inactive_service = Service.objects.create(
            title='Inactive Service',
            description='This is inactive',
            is_active=False,
        )
        
        # Filter for active services
        active_services = Service.objects.filter(is_active=True)
        
        self.assertIn(self.service, active_services)
        self.assertNotIn(inactive_service, active_services)


class AssetsModelTest(TestCase):
    """Test Assets model"""
    
    def setUp(self):
        """Set up test data"""
        self.asset = Assets.objects.create(
            name='test_asset',
            image_url='https://example.com/image.jpg',
        )
    
    def test_asset_creation(self):
        """Test that asset can be created"""
        self.assertEqual(self.asset.name, 'test_asset')
        self.assertEqual(self.asset.image_url, 'https://example.com/image.jpg')
    
    def test_asset_str_method(self):
        """Test __str__ method returns name"""
        self.assertEqual(str(self.asset), 'test_asset')


class DepartmentModelTest(TestCase):
    """Test Department model"""
    
    def setUp(self):
        """Set up test data"""
        self.department = Department.objects.create(
            name='Test Department',
            description='This is a test department',
        )
    
    def test_department_creation(self):
        """Test that department can be created"""
        self.assertEqual(self.department.name, 'Test Department')
    
    def test_department_str_method(self):
        """Test __str__ method returns name"""
        self.assertEqual(str(self.department), 'Test Department')


class TeamInfoModelTest(TestCase):
    """Test TeamInfo model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='test_user',
            email='test@test.com',
            password='password123',
            is_staff=True,
            is_active=True,
            first_name='John',
            last_name='Doe'
        )
        
        self.team_info = TeamInfo.objects.create(
            user=self.user,
            position='Software Engineer',
            bio='Test bio',
            is_active=True,
        )
    
    def test_team_info_creation(self):
        """Test that team info can be created"""
        self.assertEqual(self.team_info.user, self.user)
        self.assertEqual(self.team_info.position, 'Software Engineer')
        self.assertTrue(self.team_info.is_active)
    
    def test_team_info_str_method(self):
        """Test __str__ method returns user's full name"""
        expected = f"{self.user.get_full_name()} - Software Engineer"
        self.assertEqual(str(self.team_info), expected)
    
    def test_inactive_team_member_not_shown(self):
        """Test that inactive team members are excluded"""
        # Create inactive team member
        inactive_user = User.objects.create_user(
            username='inactive_user',
            email='inactive@test.com',
            is_staff=True,
            is_active=True,
        )
        
        inactive_team_info = TeamInfo.objects.create(
            user=inactive_user,
            position='Manager',
            is_active=False,  # INACTIVE
        )
        
        # Filter for active team members
        active_team = TeamInfo.objects.filter(is_active=True)
        
        self.assertIn(self.team_info, active_team)
        self.assertNotIn(inactive_team_info, active_team)


class OurTeamModelTest(TestCase):
    """Test OurTeam model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='test_user',
            email='test@test.com',
            password='password123',
            is_staff=True,
            is_active=True,
            first_name='John',
            last_name='Doe'
        )
        
        self.department = Department.objects.create(
            name='Engineering',
        )
        
        self.team_member = OurTeam.objects.create(
            user=self.user,
            department=self.department,
            position='Senior Engineer',
            bio='Experienced software engineer',
            is_featured=True,
        )
    
    def test_our_team_creation(self):
        """Test that team member can be created"""
        self.assertEqual(self.team_member.user, self.user)
        self.assertEqual(self.team_member.department, self.department)
        self.assertEqual(self.team_member.position, 'Senior Engineer')
        self.assertTrue(self.team_member.is_featured)
    
    def test_our_team_str_method(self):
        """Test __str__ method"""
        self.assertIn('John', str(self.team_member))
        self.assertIn('Doe', str(self.team_member))
    
    def test_featured_team_members(self):
        """Test that featured team members can be filtered"""
        # Create non-featured member
        non_featured_user = User.objects.create_user(
            username='non_featured',
            email='nonfeatured@test.com',
            is_staff=True,
            is_active=True,
        )
        
        non_featured_member = OurTeam.objects.create(
            user=non_featured_user,
            department=self.department,
            position='Junior Engineer',
            is_featured=False,
        )
        
        # Filter for featured members
        featured_team = OurTeam.objects.filter(is_featured=True)
        
        self.assertIn(self.team_member, featured_team)
        self.assertNotIn(non_featured_member, featured_team)
