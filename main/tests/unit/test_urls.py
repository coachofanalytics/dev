from django.test import TestCase, override_settings
from django.urls import reverse, resolve
from main import views

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestimonialURLsTest(TestCase):
    """Test cases for Testimonial URL configuration"""
    
    def test_testimonial_url_resolves_to_correct_view(self):
        """Test that /Testimonial/ URL resolves to the correct view function"""
        resolver = resolve('/Testimonial/')
        self.assertEqual(resolver.func, views.testimonial_list)
        self.assertEqual(resolver.url_name, 'testimonial_list')
    
    def test_testimonial_url_reverse_correctly(self):
        """Test that reverse('main:testimonial_list') returns the correct URL"""
        url = reverse('main:testimonial_list')
        self.assertEqual(url, '/Testimonial/')
    
    def test_testimonial_url_accessible_by_path(self):
        """Test that the URL path is accessible"""
        response = self.client.get('/Testimonial/')
        self.assertEqual(response.status_code, 200)
    
    def test_testimonial_url_accessible_by_name(self):
        """Test that the URL is accessible when using reverse()"""
        response = self.client.get(reverse('main:testimonial_list'))
        self.assertEqual(response.status_code, 200)

    def test_testimonial_url_with_trailing_slash(self):
        """Test URL with and without trailing slash"""
        # Test with trailing slash (as defined)
        response = self.client.get('/Testimonial/')
        self.assertEqual(response.status_code, 200)
        
        # Test without trailing slash (should redirect or 404)
        response = self.client.get('/Testimonial')
        if response.status_code == 301:  # Redirect
            self.assertEqual(response.url, '/Testimonial/')
        else:
            self.assertEqual(response.status_code, 404)