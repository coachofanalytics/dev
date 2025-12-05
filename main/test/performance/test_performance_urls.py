import time
from django.test import TestCase, Client
from django.test.utils import override_settings
from django.urls import reverse, resolve

@override_settings(
    DEBUG=True,
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    STATICFILES_DIRS=[],
)
class URLPerformanceTest(TestCase):
    """Performance tests for URL resolution and routing"""
    
    def setUp(self):
        self.client = Client()
    
    def test_url_resolution_performance(self):
        """Test URL reverse resolution performance"""
        print("Testing URL resolution performance...")
        
        # Common URL patterns to test
        url_names = [
            'scholarship_list',
            'scholarship_create',
            'scholarship_detail',
            'scholarship_update',
            'scholarship_delete',
            # Add your actual URL names
        ]
        
        iterations = 1000
        
        start_time = time.time()
        for i in range(iterations):
            for url_name in url_names:
                try:
                    reverse(url_name)
                except:
                    pass  # Skip if URL doesn't exist
        end_time = time.time()
        
        resolution_time = end_time - start_time
        print(f"✓ URL reverse resolution: {iterations * len(url_names)} operations in {resolution_time:.3f}s")
        self.assertLess(resolution_time, 2.0)
    
    def test_url_pattern_matching_performance(self):
        """Test URL pattern matching performance"""
        print("Testing URL pattern matching performance...")
        
        # Test URLs to match
        test_urls = [
            '/scholarship/',
        
        ]
        
        iterations = 500
        
        start_time = time.time()
        for i in range(iterations):
            for url in test_urls:
                try:
                    resolve(url)
                except:
                    pass  # Skip if URL doesn't resolve
        end_time = time.time()
        
        matching_time = end_time - start_time
        print(f"✓ URL pattern matching: {iterations * len(test_urls)} operations in {matching_time:.3f}s")
        self.assertLess(matching_time, 3.0)
    
    def test_urlconf_loading_performance(self):
        """Test URL configuration loading performance"""
        print("Testing URL configuration loading performance...")
        
        iterations = 100
        
        start_time = time.time()
        for i in range(iterations):
            # Reload URL configuration
            from django.urls import clear_url_caches
            import importlib
            from django.conf import settings
            
            clear_url_caches()
            if hasattr(settings, 'ROOT_URLCONF'):
                importlib.reload(__import__(settings.ROOT_URLCONF, {}, {}, ['']))
        end_time = time.time()
        
        loading_time = end_time - start_time
        print(f"✓ URL configuration loading: {iterations} reloads in {loading_time:.3f}s")
        self.assertLess(loading_time, 5.0)
    
    def test_url_parameter_extraction_performance(self):
        """Test URL parameter extraction performance"""
        print("Testing URL parameter extraction performance...")
        
        # URLs with parameters
        parameterized_urls = [
            '/scholarship/123/',
        ]
        
        iterations = 1000
        
        start_time = time.time()
        for i in range(iterations):
            for url in parameterized_urls:
                try:
                    match = resolve(url)
                    kwargs = match.kwargs
                    args = match.args
                except:
                    pass
        end_time = time.time()
        
        param_time = end_time - start_time
        print(f"✓ URL parameter extraction: {iterations * len(parameterized_urls)} operations in {param_time:.3f}s")
        self.assertLess(param_time, 2.0)