"""
Simple regression tests for Testimonial view
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from main.models import Testimonial

# ADD THIS DECORATOR to fix static files issue
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SimpleTestimonialRegressionTests(TestCase):
    """Simple regression tests to ensure basic functionality doesn't break"""
    
    def setUp(self):
        """Create basic test data"""
        self.testimonial = Testimonial.objects.create(
            name="Test User",
            position="Developer",
            organization="Test Corp",
            testimonial="Great service!",
            image=""
        )
    
    def test_view_always_returns_200(self):
        """Regression: View should always return 200 status"""
        response = self.client.get(reverse('main:testimonial_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_view_always_uses_correct_template(self):
        """Regression: View should always use correct template"""
        response = self.client.get(reverse('main:testimonial_list'))
        self.assertTemplateUsed(response, 'main/snippets_templates/table/testimonial_list.html')
    
    def test_view_always_has_testimonial_context(self):
        """Regression: View should always pass testimonial in context"""
        response = self.client.get(reverse('main:testimonial_list'))
        self.assertIn('testimonial', response.context)
    
    def test_view_shows_testimonial_data(self):
        """Regression: View should display testimonial data"""
        response = self.client.get(reverse('main:testimonial_list'))
        self.assertContains(response, "Test User")
        self.assertContains(response, "Developer")
        self.assertContains(response, "Test Corp")
        self.assertContains(response, "Great service!")

    def test_view_handles_empty_data(self):
        """Regression: View should work when no testimonials exist"""
        # Delete the testimonial created in setUp
        Testimonial.objects.all().delete()
        
        response = self.client.get(reverse('main:testimonial_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['testimonial'].count(), 0)