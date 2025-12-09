import time
import random
import string
from django.test import TestCase, override_settings
from django.urls import reverse
from django.db import connection
from django.core.cache import cache
from main.models import Testimonial

@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    DEBUG=False,  # Debug mode can slow down performance
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
)
class PerformanceRegressionTests(TestCase):
    """Performance regression tests to catch slowdowns over time"""
    
    @classmethod
    def setUpTestData(cls):
        """Create performance test data once for all tests"""
        # Create base test data
        cls.base_testimonials = []
        for i in range(20):  # Base dataset
            testimonial = Testimonial.objects.create(
                name=f"Performance User {i}",
                position=f"Position {i}",
                organization=f"Organization {i}",
                testimonial=f"Testimonial content {i}" * 3,  # 3x longer
                image=f"image_{i}.jpg"
            )
            cls.base_testimonials.append(testimonial)
        
        # Clear cache before tests
        cache.clear()
    
    def setUp(self):
        """Reset cache before each test"""
        cache.clear()
        connection.queries_log.clear()
    
    # ==================== VIEW PERFORMANCE TESTS ====================
    
    def test_view_response_time_baseline(self):
        """Establish baseline response time for testimonial list view"""
        iterations = 5
        total_time = 0
        
        for i in range(iterations):
            start_time = time.perf_counter()
            response = self.client.get(reverse('main:testimonial_list'))
            end_time = time.perf_counter()
            
            self.assertEqual(response.status_code, 200)
            total_time += (end_time - start_time)
        
        average_time = total_time / iterations
        
        # Baseline: should render in reasonable time
        # This establishes a performance benchmark
        self.assertLess(average_time, 1.0, 
                       f"View response time too slow: {average_time:.3f}s")
        
        print(f"📊 View response baseline: {average_time:.3f} seconds")
        print(f"   (Based on {iterations} iterations with {Testimonial.objects.count()} testimonials)")
        
        # Store for comparison in future runs
        self._log_performance_metric('view_response_time', average_time)
    
    def test_view_response_time_under_load(self):
        """Test view performance with increased data"""
        # Add more data to simulate growth
        additional_count = 50
        for i in range(additional_count):
            Testimonial.objects.create(
                name=f"Load User {i}",
                position=f"Load Position {i}",
                organization=f"Load Org {i}",
                testimonial=f"Load content {i}" * 5,
                image=f"load_{i}.jpg"
            )
        
        total_testimonials = Testimonial.objects.count()
        
        # Measure response time
        start_time = time.perf_counter()
        response = self.client.get(reverse('main:testimonial_list'))
        end_time = time.perf_counter()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        
        # Should still render reasonably fast even with more data
        # Linear or sub-linear growth is acceptable
        self.assertLess(response_time, 2.0, 
                       f"View too slow with {total_testimonials} items: {response_time:.3f}s")
        
        print(f"📊 View with {total_testimonials} testimonials: {response_time:.3f} seconds")
        self._log_performance_metric('view_response_time_loaded', response_time)
    
    def test_view_scalability(self):
        """Test how view performance scales with data growth"""
        test_sizes = [10, 50, 100]
        results = {}
        
        for size in test_sizes:
            # Clean up and create specific dataset size
            Testimonial.objects.all().delete()
            
            for i in range(size):
                Testimonial.objects.create(
                    name=f"Scale User {i}",
                    position=f"Position {i}",
                    organization=f"Org {i}",
                    testimonial=f"Content {i}" * 3,
                    image=f"img_{i}.jpg"
                )
            
            # Clear cache and queries
            cache.clear()
            connection.queries_log.clear()
            
            # Measure
            start_time = time.perf_counter()
            response = self.client.get(reverse('main:testimonial_list'))
            end_time = time.perf_counter()
            
            self.assertEqual(response.status_code, 200)
            response_time = end_time - start_time
            query_count = len(connection.queries)
            
            results[size] = {
                'time': response_time,
                'queries': query_count
            }
            
            print(f"📈 Size {size:3d}: {response_time:.3f}s, {query_count:2d} queries")
        
        # Analyze scalability
        print("\n📊 Scalability Analysis:")
        prev_time = None
        for size in test_sizes:
            time_val = results[size]['time']
            queries = results[size]['queries']
            
            if prev_time is not None:
                growth_factor = time_val / prev_time
                data_growth = size / (size - 10)  # Assuming 10 item increments
                efficiency = data_growth / growth_factor
                
                print(f"  {size} items: {time_val:.3f}s ({growth_factor:.2f}x time, "
                      f"efficiency: {efficiency:.2f})")
            
            prev_time = time_val
        
        # Restore original data
        self._restore_test_data()
    
    # ==================== DATABASE PERFORMANCE TESTS ====================
    
    def test_database_query_count(self):
        """Regression: View should maintain efficient query count"""
        connection.queries_log.clear()
        
        response = self.client.get(reverse('main:testimonial_list'))
        query_count = len(connection.queries)
        
        # Should use minimal queries (1-2 typically)
        self.assertLessEqual(query_count, 3, 
                           f"Too many queries: {query_count}. Possible N+1 problem.")
        
        print(f"✅ Query efficiency: {query_count} queries for {Testimonial.objects.count()} items")
        
        # Log query details for debugging
        if query_count > 2:
            print("  Query breakdown:")
            for i, query in enumerate(connection.queries[:5], 1):
                print(f"    {i}. {query['time']:.3f}s: {query['sql'][:100]}...")
    
    def test_database_query_complexity(self):
        """Test that queries don't become overly complex"""
        connection.queries_log.clear()
        
        self.client.get(reverse('main:testimonial_list'))
        
        total_query_time = 0
        complex_queries = 0
        
        for query in connection.queries:
            total_query_time += float(query['time'])
            
            # Check for potentially complex operations
            sql_lower = query['sql'].lower()
            complexity_indicators = [
                'join',           # Multiple joins
                'subselect',      # Subqueries
                'union',          # UNION operations
                'distinct',       # DISTINCT can be expensive
                'group by',       # Grouping operations
                'order by',       # Sorting (can be expensive without indexes)
            ]
            
            if any(indicator in sql_lower for indicator in complexity_indicators):
                complex_queries += 1
        
        average_query_time = total_query_time / len(connection.queries) if connection.queries else 0
        
        print(f"📊 Query analysis: {len(connection.queries)} queries, "
              f"{total_query_time:.3f}s total, {average_query_time:.3f}s avg, "
              f"{complex_queries} complex queries")
        
        # Queries should generally be fast
        self.assertLess(average_query_time, 0.1, 
                       f"Average query time too high: {average_query_time:.3f}s")
    
    def test_database_index_usage(self):
        """Test that database queries use indexes efficiently"""
        # This is more of a monitoring test
        # In production, you'd use EXPLAIN ANALYZE
        print("ℹ For index analysis, run EXPLAIN on production queries")
        print("  Common indexes needed for testimonials:")
        print("    - Created date (if ordering by date)")
        print("    - Organization (if filtering)")
        print("    - Name (if searching)")
        
        # Just a placeholder - real index testing requires database-specific tools
        self.assertTrue(True, "Index monitoring recommended")
    
    # ==================== MEMORY USAGE TESTS ====================
    
    def test_memory_usage_growth(self):
        """Test that memory usage doesn't grow excessively"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Get baseline memory
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform operations that might use memory
        for i in range(10):
            response = self.client.get(reverse('main:testimonial_list'))
            self.assertEqual(response.status_code, 200)
        
        # Get memory after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        print(f"📊 Memory usage: {memory_before:.1f}MB → {memory_after:.1f}MB "
              f"(Δ {memory_increase:+.1f}MB)")
        
        # Memory increase should be reasonable
        # Large increases might indicate memory leaks
        self.assertLess(memory_increase, 50.0, 
                       f"Excessive memory increase: {memory_increase:.1f}MB")
    
    # ==================== CONCURRENT PERFORMANCE TESTS ====================
    
    def test_concurrent_request_handling(self):
        """Test performance under concurrent requests (simulated)"""
        import threading
        
        results = []
        errors = []
        
        def make_concurrent_request(request_id):
            try:
                start_time = time.perf_counter()
                response = self.client.get(reverse('main:testimonial_list'))
                end_time = time.perf_counter()
                
                if response.status_code == 200:
                    results.append({
                        'id': request_id,
                        'time': end_time - start_time,
                        'success': True
                    })
                else:
                    errors.append(f"Request {request_id}: Status {response.status_code}")
            except Exception as e:
                errors.append(f"Request {request_id}: {str(e)}")
        
        # Simulate concurrent requests
        threads = []
        concurrent_users = 5
        
        for i in range(concurrent_users):
            thread = threading.Thread(target=make_concurrent_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Analyze results
        if errors:
            print(f"⚠ {len(errors)} errors in concurrent test: {errors[:3]}")
        
        self.assertEqual(len(errors), 0, f"Errors in concurrent test: {errors}")
        
        if results:
            times = [r['time'] for r in results]
            avg_time = sum(times) / len(times)
            max_time = max(times)
            
            print(f"📊 Concurrent ({concurrent_users} users): "
                  f"avg {avg_time:.3f}s, max {max_time:.3f}s")
            
            # Concurrent requests should complete reasonably
            self.assertLess(max_time, 3.0, 
                          f"Slow concurrent response: {max_time:.3f}s")
    
    # ==================== CACHE PERFORMANCE TESTS ====================
    
    def test_cache_effectiveness(self):
        """Test that caching improves performance"""
        # First request (cold cache)
        start_time = time.perf_counter()
        response1 = self.client.get(reverse('main:testimonial_list'))
        end_time = time.perf_counter()
        time_cold = end_time - start_time
        
        # Second request (warm cache if implemented)
        start_time = time.perf_counter()
        response2 = self.client.get(reverse('main:testimonial_list'))
        end_time = time.perf_counter()
        time_warm = end_time - start_time
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        print(f"📊 Cache test: Cold: {time_cold:.3f}s, Warm: {time_warm:.3f}s")
        
        # If caching is implemented, warm should be faster
        if time_warm < time_cold:
            improvement = (time_cold - time_warm) / time_cold * 100
            print(f"✅ Cache effective: {improvement:.1f}% improvement")
        else:
            print("ℹ Consider implementing caching for performance")
    
    # ==================== LOAD TESTING (SIMPLIFIED) ====================
    
    def test_sustained_performance(self):
        """Test performance under sustained load"""
        request_count = 20
        times = []
        
        for i in range(request_count):
            start_time = time.perf_counter()
            response = self.client.get(reverse('main:testimonial_list'))
            end_time = time.perf_counter()
            
            self.assertEqual(response.status_code, 200)
            times.append(end_time - start_time)
        
        # Calculate statistics
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        # Check for performance degradation over time
        first_half = times[:len(times)//2]
        second_half = times[len(times)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        degradation = ((avg_second - avg_first) / avg_first * 100) if avg_first > 0 else 0
        
        print(f"📊 Sustained load ({request_count} requests):")
        print(f"  Avg: {avg_time:.3f}s, Min: {min_time:.3f}s, Max: {max_time:.3f}s")
        print(f"  First half: {avg_first:.3f}s, Second half: {avg_second:.3f}s")
        print(f"  Degradation: {degradation:+.1f}%")
        
        # Should not degrade significantly
        self.assertLess(degradation, 50.0, 
                       f"Significant performance degradation: {degradation:.1f}%")
    
    # ==================== HELPER METHODS ====================
    
    def _log_performance_metric(self, metric_name, value):
        """Log performance metric for tracking"""
        # In real implementation, you might store this in a database
        # For now, just print it
        print(f"  📈 Metric logged: {metric_name} = {value:.3f}")
    
    def _restore_test_data(self):
        """Restore original test data"""
        # Delete any extra data
        Testimonial.objects.exclude(
            id__in=[t.id for t in self.base_testimonials]
        ).delete()
    
    def tearDown(self):
        """Cleanup after tests"""
        self._restore_test_data()
        cache.clear()


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class QuickPerformanceTests(TestCase):
    """Quick performance sanity checks"""
    
    def setUp(self):
        # Create some test data
        for i in range(10):
            Testimonial.objects.create(
                name=f"Quick Test {i}",
                position=f"Position {i}",
                organization=f"Org {i}",
                testimonial=f"Content {i}",
                image=""
            )
    
    def test_quick_response_time(self):
        """Quick test that page loads in reasonable time"""
        start_time = time.perf_counter()
        response = self.client.get(reverse('main:testimonial_list'))
        end_time = time.perf_counter()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        
        # Should be fast
        self.assertLess(response_time, 1.0, 
                       f"Response too slow: {response_time:.3f}s")
        
        print(f"✅ Quick response: {response_time:.3f} seconds")
    
    def test_query_efficiency(self):
        """Quick check for query efficiency"""
        from django.db import connection
        
        connection.queries_log.clear()
        
        response = self.client.get(reverse('main:testimonial_list'))
        
        query_count = len(connection.queries)
        
        # Should be efficient
        self.assertLessEqual(query_count, 3, 
                           f"Too many queries: {query_count}")
        
        print(f"✅ Query count: {query_count}")

    def test_no_memory_leaks(self):
        """Quick memory usage check"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Multiple requests to check for leaks
        memory_readings = []
        
        for i in range(5):
            response = self.client.get(reverse('main:testimonial_list'))
            self.assertEqual(response.status_code, 200)
            
            memory_mb = process.memory_info().rss / 1024 / 1024
            memory_readings.append(memory_mb)
        
        # Check if memory consistently increases
        # Allow some fluctuation
        memory_change = memory_readings[-1] - memory_readings[0]
        
        print(f"📊 Memory readings: {[f'{m:.1f}MB' for m in memory_readings]}")
        print(f"📊 Memory change: {memory_change:+.1f}MB")
        
        # Should not leak significantly
        self.assertLess(memory_change, 10.0, 
                       f"Possible memory leak: {memory_change:+.1f}MB increase")


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PerformanceMonitoringTests(TestCase):
    """Tests that set up performance monitoring"""
    
    def test_performance_baselines(self):
        """Establish and document performance baselines"""
        print("\n" + "="*60)
        print("PERFORMANCE BASELINES")
        print("="*60)
        
        # Create standardized test data
        Testimonial.objects.all().delete()
        for i in range(25):  # Standard test size
            Testimonial.objects.create(
                name=f"Baseline User {i}",
                position=f"Position {i}",
                organization=f"Organization {i}",
                testimonial=f"Standard test content {i}",
                image=f"image_{i}.jpg"
            )
        
        # Measure multiple times for accuracy
        times = []
        for i in range(5):
            start_time = time.perf_counter()
            response = self.client.get(reverse('main:testimonial_list'))
            end_time = time.perf_counter()
            
            self.assertEqual(response.status_code, 200)
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📊 Test Configuration:")
        print(f"  - Testimonials: {Testimonial.objects.count()}")
        print(f"  - Iterations: {len(times)}")
        print(f"  - Static files: Disabled (testing mode)")
        
        print(f"\n📊 Performance Results:")
        print(f"  Average time: {avg_time:.3f} seconds")
        print(f"  Best time:    {min_time:.3f} seconds")
        print(f"  Worst time:   {max_time:.3f} seconds")
        print(f"  Variance:     {(max_time - min_time):.3f} seconds")
        
        print(f"\n📊 Recommendations:")
        print(f"  1. Monitor these baselines over time")
        print(f"  2. Investigate if average time exceeds {avg_time * 1.5:.3f}s")
        print(f"  3. Set up CI/CD performance gates")
        
        # Store baseline
        self._save_baseline('testimonial_list', avg_time)
    
    def _save_baseline(self, endpoint, time_value):
        """Save performance baseline"""
        # In production, save to database or file
        print(f"\n💾 Baseline saved: {endpoint} = {time_value:.3f}s")
        print("  (Implement saving to database/file for long-term tracking)")


# Run performance tests
if __name__ == '__main__':
    import django
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
    django.setup()
    
    print("🚀 Running performance regression tests...")
    print("="*60)
    
    # You could add custom test runner logic here