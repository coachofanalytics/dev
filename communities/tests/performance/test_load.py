# communities/tests/performance/test_load.py
import time
from django.test import TestCase
from django.urls import reverse
from communities.models import CommunityMember

class TestDirectoryPerformance(TestCase):
    """Performance tests for directory"""
    
    def test_directory_load_with_many_users(self):
        """Test directory load time with 100 users"""
        print("\n⚡ Performance Test: Directory with 100 users")
        
        # Create 100 members
        for i in range(100):
            CommunityMember.objects.create(
                name=f'User {i}',
                email=f'user{i}@example.com',
                profession='Performance Test',
                region='Test City',
                is_public_directory=True
            )
        
        # Measure load time
        start_time = time.time()
        response = self.client.get(reverse('member_directory'))
        end_time = time.time()
        
        load_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        
        # Performance requirement: load in under 2 seconds
        self.assertLess(load_time, 2.0, 
                       f"Directory loaded in {load_time:.3f}s, expected <2s")
        
        print(f"✅ Load time: {load_time:.3f} seconds")
    
    def test_search_performance(self):
        """Test search performance"""
        print("\n⚡ Performance Test: Search")
        
        # Create test data
        for i in range(50):
            CommunityMember.objects.create(
                name=f'Search User {i}',
                email=f'search{i}@example.com',
                profession='Developer',
                is_public_directory=True
            )
        
        start_time = time.time()
        response = self.client.get(reverse('member_directory'), {
            'search': 'Developer'
        })
        end_time = time.time()
        
        search_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(search_time, 1.0, 
                       f"Search completed in {search_time:.3f}s, expected <1s")
        
        print(f"✅ Search time: {search_time:.3f} seconds")