"""
Integration tests for performance to ensure components work efficiently together.
"""
from django.test import TestCase, Client, TransactionTestCase, override_settings
from django.urls import reverse, resolve
from django.test.utils import CaptureQueriesContext
from django.db import connection, reset_queries
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from main.models import Testimonial
import time


# Use a simpler static files storage for tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PerformanceIntegrationTests(TransactionTestCase):
    """
    Performance integration tests that measure efficiency of component interactions.
    """
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        
        # Create test user
        self.user = get_user_model().objects.create_user(
            username='perfuser',
            email='perf@example.com',
            password='perfpass123'
        )
        
        # Clear cache before tests
        cache.clear()
        
        # Reset query count
        reset_queries()
    
    def tearDown(self):
        """Clean up after tests"""
        Testimonial.objects.all().delete()
        get_user_model().objects.all().delete()
        cache.clear()
    
    # ==================== DATABASE PERFORMANCE TESTS ====================
    
    def test_database_query_count(self):
        """Integration: View should use efficient database queries"""
        print("\n📊 Testing database query efficiency:")
        
        # Create test data
        num_testimonials = 5
        for i in range(num_testimonials):
            Testimonial.objects.create(
                name=f"Performance Test {i}",
                position=f"Position {i}",
                organization=f"Org {i}",
                testimonial=f"Performance test content {i}",
                image=""
            )
        
        # Capture queries
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get('/Testimonial/')
        
        query_count = len(queries)
        
        print(f"Total queries: {query_count}")
        if query_count > 0 and query_count <= 5:
            for i, query in enumerate(queries[:3], 1):
                print(f"  {i}. {query['sql'][:80]}...")
        
        # Reasonable query count
        self.assertLess(query_count, 20, 
                       f"Too many queries ({query_count}) for testimonial list")
        
        # Response should be successful
        self.assertEqual(response.status_code, 200)
        
        print(f"✅ Database query efficiency: {query_count} queries for {num_testimonials} items")
    
    # ==================== VIEW PERFORMANCE TESTS ====================
    
    def test_view_response_time(self):
        """Integration: View response time should be acceptable"""
        print("\n⚡ Testing view response time:")
        
        # Create some test data
        for i in range(3):
            Testimonial.objects.create(
                name=f"Response Test {i}",
                position="Tester",
                organization="Response Corp",
                testimonial="Testing response time",
                image=""
            )
        
        # Measure response time
        iterations = 3
        total_time = 0
        
        for i in range(iterations):
            start_time = time.perf_counter()
            response = self.client.get('/Testimonial/')
            end_time = time.perf_counter()
            
            total_time += (end_time - start_time)
            
            # Verify response
            self.assertEqual(response.status_code, 200)
        
        avg_time = total_time / iterations
        
        print(f"Average response time: {avg_time:.3f}s")
        
        # Should respond within reasonable time
        self.assertLess(avg_time, 2.0, 
                       f"View response too slow: {avg_time:.3f}s")
        
        print(f"✅ View response time: {avg_time:.3f}s average")
    
    # ==================== TEMPLATE PERFORMANCE TESTS ====================
    
    def test_template_rendering_speed(self):
        """Integration: Template rendering should be efficient"""
        print("\n🎨 Testing template rendering speed:")
        
        # Create data for template
        for i in range(5):
            Testimonial.objects.create(
                name=f"Template Perf {i}",
                position="Template Tester",
                organization="Template Corp",
                testimonial="Testing template rendering performance",
                image=""
            )
        
        # Measure template rendering in view context
        start_time = time.perf_counter()
        
        response = self.client.get('/Testimonial/')
        
        end_time = time.perf_counter()
        render_time = end_time - start_time
        
        print(f"Template rendering time: {render_time:.3f}s")
        
        # Should render reasonably quickly
        self.assertLess(render_time, 1.0, 
                       f"Template rendering too slow: {render_time:.3f}s")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        print("✅ Template rendering performance is acceptable")
    
    # ==================== URL RESOLUTION PERFORMANCE ====================
    
    def test_url_resolution_speed(self):
        """Integration: URL resolution should be fast"""
        print("\n🔗 Testing URL resolution speed:")
        
        iterations = 50
        total_time = 0
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            # Test URL operations
            url = reverse('main:testimonial_list')
            
            end_time = time.perf_counter()
            total_time += (end_time - start_time)
        
        avg_time = total_time / iterations
        
        print(f"URL resolution average time: {avg_time:.6f}s")
        print(f"Total for {iterations} iterations: {total_time:.3f}s")
        
        # Should be very fast
        self.assertLess(avg_time, 0.001, 
                       f"URL resolution too slow: {avg_time:.6f}s")
        
        print(f"✅ URL resolution performance: {avg_time:.6f}s average")
    
    # ==================== STRESS TEST ====================
    
    def test_stress_performance(self):
        """Integration: Performance under stress conditions"""
        print("\n💥 Testing stress performance:")
        
        # Create some data
        for i in range(10):
            Testimonial.objects.create(
                name=f"Stress Test {i}",
                position=f"Position {i}",
                organization=f"Stress Org {i % 3}",
                testimonial=f"Stress test content {i}",
                image=""
            )
        
        # Multiple rapid requests
        request_count = 10
        times = []
        
        for i in range(request_count):
            start_time = time.perf_counter()
            response = self.client.get('/Testimonial/')
            end_time = time.perf_counter()
            
            times.append(end_time - start_time)
            self.assertEqual(response.status_code, 200)
        
        avg_time = sum(times) / len(times)
        
        print(f"Requests: {request_count}")
        print(f"Average time: {avg_time:.3f}s")
        print(f"Minimum time: {min(times):.3f}s")
        print(f"Maximum time: {max(times):.3f}s")
        
        # Should be reasonable
        self.assertLess(avg_time, 2.0, 
                       f"Stress performance too slow: {avg_time:.3f}s")
        
        print("✅ Stress performance is acceptable")
    
    # ==================== COMPREHENSIVE PERFORMANCE TEST ====================
    
    def test_comprehensive_performance_workflow(self):
        """Integration: Complete workflow performance"""
        print("\n🚀 Testing complete workflow performance:")
        
        # Setup phase
        print("1. Setup phase")
        setup_start = time.perf_counter()
        
        # Create test data
        testimonials = []
        for i in range(10):
            testimonial = Testimonial(
                name=f"Workflow Test {i}",
                position=f"Role {i % 3}",
                organization=f"Org {i % 4}",
                testimonial=f"Performance workflow test {i}",
                image=""
            )
            testimonials.append(testimonial)
        
        Testimonial.objects.bulk_create(testimonials)
        
        setup_end = time.perf_counter()
        setup_time = setup_end - setup_start
        print(f"   Setup time: {setup_time:.3f}s")
        
        # URL resolution phase
        print("2. URL resolution phase")
        url_start = time.perf_counter()
        
        url = reverse('main:testimonial_list')
        self.assertEqual(url, '/Testimonial/')
        
        url_end = time.perf_counter()
        url_time = url_end - url_start
        print(f"   URL resolution time: {url_time:.6f}s")
        
        # View processing phase
        print("3. View processing phase")
        view_start = time.perf_counter()
        
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
        
        view_end = time.perf_counter()
        view_time = view_end - view_start
        query_count = len(queries)
        print(f"   View processing time: {view_time:.3f}s")
        print(f"   Database queries: {query_count}")
        
        # Verification phase
        print("4. Verification phase")
        self.assertEqual(response.status_code, 200)
        
        # Total time
        total_time = view_time
        
        print(f"\n📊 Performance Summary:")
        print(f"   Total time: {total_time:.3f}s")
        print(f"   Queries: {query_count}")
        
        # Performance thresholds
        self.assertLess(total_time, 2.0, f"Total workflow too slow: {total_time:.3f}s")
        self.assertLess(query_count, 20, f"Too many queries: {query_count}")
        
        print("✅ Complete workflow performance meets expectations")


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SimplePerformanceTests(TestCase):
    """Simple performance integration tests"""
    
    def setUp(self):
        """Set up test data"""
        self.testimonial = Testimonial.objects.create(
            name="Simple Performance Test",
            position="Performance Tester",
            organization="Performance Corp",
            testimonial="Simple performance test content",
            image=""
        )
    
    def test_basic_performance(self):
        """Basic performance integration test"""
        print("\n⚡ Basic performance test:")
        
        # Test response time
        start_time = time.perf_counter()
        
        response = self.client.get('/Testimonial/')
        
        end_time = time.perf_counter()
        response_time = end_time - start_time
        
        # Basic checks
        self.assertEqual(response.status_code, 200)
        
        print(f"Response time: {response_time:.3f}s")
        
        # Should be reasonably fast
        self.assertLess(response_time, 1.0, 
                       f"Response too slow: {response_time:.3f}s")
        
        print("✅ Basic performance meets expectations")
    
    def test_query_efficiency(self):
        """Test query efficiency"""
        print("\n📊 Query efficiency test:")
        
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get('/Testimonial/')
        
        query_count = len(queries)
        
        print(f"Query count: {query_count}")
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(query_count, 10, f"Too many queries: {query_count}")
        
        print("✅ Query efficiency is acceptable")
    
    def tearDown(self):
        """Clean up test data"""
        Testimonial.objects.all().delete()


# Run tests
if __name__ == '__main__':
    import django
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
    django.setup()
    
    print("⚡ Running performance integration tests...")
    print("="*60)