# communities/tests/integration/test_user_flows.py
from django.test import TestCase
from django.urls import reverse
from communities.models import CommunityMember

class TestUserFlowIntegration(TestCase):
    """Integration tests for complete user flows"""
    
    def test_complete_registration_flow(self):
        """
        Complete user registration flow:
        1. Join community
        2. Member created with correct defaults
        3. Can access directory form
        """
        print("\n🚀 Testing Complete Registration Flow...")
        
        # 1. Join community
        response = self.client.post(reverse('join'), {
            'name': 'Flow User',
            'email': 'flow@example.com',
            'agree_to_directory': 'on'
        }, follow=True)
        
        self.assertContains(response, 'Welcome')
        print("✅ Step 1: Joined community")
        
        # 2. Verify member created with correct defaults
        member = CommunityMember.objects.get(email='flow@example.com')
        self.assertEqual(member.name, 'Flow User')
        self.assertTrue(member.is_verified)  # Default True
        self.assertTrue(member.is_public_directory)  # Default True
        print("✅ Step 2: Member created with correct defaults")
        
        # 3. Simulate session for directory form
        session = self.client.session
        session['joined_member_id'] = member.id
        session.save()
        
        response = self.client.get(reverse('join_directory_form'))
        self.assertEqual(response.status_code, 200)
        print("✅ Step 3: Can access directory form")
        
        print("🎉 Complete flow test PASSED!")
    
    def test_directory_search_flow(self):
        """
        Directory search flow:
        1. Create members
        2. Search works
        3. Filters work
        """
        # Create test members
        members = [
            CommunityMember(name='Alice', email='alice@example.com', 
                           profession='Doctor', region='New York', is_public_directory=True),
            CommunityMember(name='Bob', email='bob@example.com', 
                           profession='Engineer', region='Boston', is_public_directory=True),
            CommunityMember(name='Charlie', email='charlie@example.com', 
                           profession='Teacher', region='New York', is_public_directory=True),
        ]
        
        for member in members:
            member.save()
        
        # Test search
        response = self.client.get(reverse('member_directory'), {'search': 'Doctor'})
        self.assertContains(response, 'Alice')
        self.assertNotContains(response, 'Bob')
        
        # Test filter
        response = self.client.get(reverse('member_directory'), {'region': 'New York'})
        self.assertContains(response, 'Alice')
        self.assertContains(response, 'Charlie')
        self.assertNotContains(response, 'Bob')