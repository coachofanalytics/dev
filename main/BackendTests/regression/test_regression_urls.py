"""
URL-only regression tests (no template rendering)
"""
from django.test import TestCase
from django.urls import reverse, resolve
from main import views

class URLOnlyTests(TestCase):
    """Tests that only check URL resolution, not template rendering"""
    
    def test_url_resolution(self):
        """Test URL resolves to correct view (no template rendering)"""
        resolver = resolve('/Testimonial/')
        self.assertEqual(resolver.func, views.testimonial_list)
        self.assertEqual(resolver.url_name, 'testimonial_list')
    
    def test_url_reverse(self):
        """Test reverse URL lookup (no template rendering)"""
        url = reverse('main:testimonial_list')
        self.assertEqual(url, '/Testimonial/')
    
    def test_url_consistency(self):
        """Test URL behavior is consistent (no template rendering)"""
        # These tests don't render templates
        self.assertEqual(reverse('main:testimonial_list'), '/Testimonial/')
        
        resolver = resolve('/Testimonial/')
        self.assertEqual(resolver.func, views.testimonial_list)