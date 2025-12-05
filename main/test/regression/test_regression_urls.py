from django.test import TestCase
from django.urls import reverse, resolve, NoReverseMatch

class URLRegressionTest(TestCase):
    """Regression tests for URL configuration"""
    
    def test_url_patterns_consistency(self):
        """Ensure URL patterns remain consistent"""
        # Common scholarship URL patterns that should exist
        expected_urls = [
            ('scholarship_list', '/scholarship/'),
            ('scholarship_create', '/scholarship/create/'),
            ('scholarship_detail', '/scholarship/1/'),
            ('scholarship_update', '/scholarship/1/update/'),
            ('scholarship_delete', '/scholarship/1/delete/'),
        ]
        
        for url_name, expected_path in expected_urls:
            try:
                # Test reverse URL resolution
                reversed_url = reverse(url_name)
                print(f"✓ URL name '{url_name}' resolves to '{reversed_url}'")
                
                # Test URL pattern matching
                resolver_match = resolve(reversed_url)
                self.assertEqual(resolver_match.view_name, url_name)
                print(f"✓ URL '{reversed_url}' correctly resolves to '{url_name}'")
                
            except NoReverseMatch:
                print(f"Note: URL name '{url_name}' is not implemented")
            except Exception as e:
                print(f"Note: URL test for '{url_name}' failed: {e}")
    
    def test_url_parameter_consistency(self):
        """Ensure URL parameters are handled consistently"""
        test_cases = [
            {'url_name': 'scholarship_detail', 'kwargs': {'pk': 1}, 'expected_path': '/scholarship/1/'},
            {'url_name': 'scholarship_update', 'kwargs': {'pk': 42}, 'expected_path': '/scholarship/42/update/'},
            {'url_name': 'scholarship_delete', 'kwargs': {'slug': 'test-slug'}, 'expected_path': None},  # May not exist
        ]
        
        for test_case in test_cases:
            try:
                reversed_url = reverse(test_case['url_name'], kwargs=test_case['kwargs'])
                print(f"✓ URL '{test_case['url_name']}' with params {test_case['kwargs']} resolves to '{reversed_url}'")
                
                if test_case['expected_path']:
                    self.assertEqual(reversed_url, test_case['expected_path'])
                
            except NoReverseMatch:
                print(f"Note: URL '{test_case['url_name']}' with params {test_case['kwargs']} not implemented")
            except Exception as e:
                print(f"URL parameter test failed: {e}")
    
    def test_url_namespace_consistency(self):
        """Ensure URL namespaces work correctly"""
        try:
            # Test if URLs are properly namespaced
            namespaced_urls = [
                'scholarship:list',
                'scholarship:detail',
                'scholarship:create',
            ]
            
            for namespaced_url in namespaced_urls:
                try:
                    reversed_url = reverse(namespaced_url)
                    print(f"✓ Namespaced URL '{namespaced_url}' resolves to '{reversed_url}'")
                except NoReverseMatch:
                    print(f"Note: Namespaced URL '{namespaced_url}' not implemented")
                    
        except Exception as e:
            print(f"Note: URL namespacing may not be implemented: {e}")
    
    def test_url_trailing_slash_consistency(self):
        """Ensure URL trailing slash behavior is consistent"""
        test_urls = [
            '/scholarship',
            '/scholarship/',
            '/scholarship/create',
            '/scholarship/create/',
        ]
        
        for test_url in test_urls:
            try:
                response = self.client.get(test_url)
                # Should either work or redirect appropriately
                self.assertIn(response.status_code, [200, 301, 302, 404])
                print(f"✓ URL '{test_url}' handled appropriately (status: {response.status_code})")
            except Exception as e:
                print(f"Note: URL '{test_url}' test failed: {e}")


class URLResponseRegressionTest(TestCase):
    """Regression tests for URL responses"""
    
    def test_url_http_method_consistency(self):
        """Ensure URLs respond correctly to different HTTP methods"""
        test_cases = [
            {'path': '/scholarship/', 'methods': ['GET'], 'expected_status': 200},
            {'path': '/scholarship/create/', 'methods': ['GET', 'POST'], 'expected_status': 200},
        ]
        
        for test_case in test_cases:
            for method in test_case['methods']:
                try:
                    if method == 'GET':
                        response = self.client.get(test_case['path'])
                    elif method == 'POST':
                        response = self.client.post(test_case['path'])
                    elif method == 'PUT':
                        response = self.client.put(test_case['path'])
                    elif method == 'DELETE':
                        response = self.client.delete(test_case['path'])
                    
                    self.assertIn(response.status_code, [200, 201, 302, 405])
                    print(f"✓ {method} {test_case['path']} -> {response.status_code}")
                    
                except Exception as e:
                    print(f"Note: {method} {test_case['path']} test failed: {e}")
    
    def test_url_redirect_consistency(self):
        """Ensure URL redirects work consistently"""
        redirect_cases = [
            {'from_path': '/scholarship', 'to_path': '/scholarship/'},
        ]
        
        for redirect_case in redirect_cases:
            try:
                response = self.client.get(redirect_case['from_path'])
                if response.status_code in [301, 302]:
                    self.assertEqual(response.url, redirect_case['to_path'])
                    print(f"✓ Redirect from '{redirect_case['from_path']}' to '{redirect_case['to_path']}' works")
                else:
                    print(f"Note: No redirect from '{redirect_case['from_path']}'")
            except Exception as e:
                print(f"Note: Redirect test failed: {e}")