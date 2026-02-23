# communities/test_simple.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import CommunityMember

class SimpleCommunityTests(TestCase):
    """Simple tests that definitely work"""
    
    def test_1_home_page(self):
        """Test home page loads"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        print("✅ Home page test passed")
    
    def test_2_join_page(self):
        """Test join page loads"""
        response = self.client.get(reverse('join'))
        self.assertEqual(response.status_code, 200)
        print("✅ Join page test passed")
    
    def test_3_directory_page(self):
        """Test directory page loads"""
        response = self.client.get(reverse('member_directory'))
        self.assertEqual(response.status_code, 200)
        print("✅ Directory page test passed")
    
    def test_4_join_community(self):
        """Test user can join community"""
        response = self.client.post(reverse('join'), {
            'name': 'Test User',
            'email': 'test@example.com',
            'agree_to_directory': 'on'
        })
        
        # Should redirect to directory
        self.assertEqual(response.status_code, 302)
        
        # Member should be created
        self.assertTrue(CommunityMember.objects.filter(
            email='test@example.com'
        ).exists())
        print("✅ Join community test passed")
    
    def test_5_directory_shows_members(self):
        """Test directory shows members"""
        # Create a test member
        CommunityMember.objects.create(
            name='Directory Test',
            email='dir@example.com',
            profession='Tester',
            region='Test',
            is_public_directory=True
        )
        
        response = self.client.get(reverse('member_directory'))
        self.assertContains(response, 'Directory Test')
        print("✅ Directory shows members test passed")

class ModelTests(TestCase):
    """Test database models"""
    
    def test_create_member(self):
        """Can create a community member"""
        member = CommunityMember.objects.create(
            name='Model Test',
            email='model@example.com',
            profession='Developer'
        )
        
        self.assertEqual(member.name, 'Model Test')
        self.assertTrue(member.is_verified)
        print("✅ Model creation test passed")
    
    def test_member_string(self):
        """Member string representation"""
        member = CommunityMember.objects.create(
            name='John Doe',
            email='john@example.com',
            profession='Engineer'
        )
        
        self.assertEqual(str(member), 'John Doe - Engineer')
        print("✅ Model string test passed")

class URLTests(TestCase):
    """Test URL patterns"""
    
    def test_urls(self):
        """Test main URLs"""
        urls = [
            ('home', '/communities/'),
            ('join', '/communities/join/'),
            ('member_directory', '/communities/directory/'),
        ]
        
        for name, expected in urls:
            with self.subTest(name=name):
                self.assertEqual(reverse(name), expected)
        print("✅ URL tests passed")