from django.test import TestCase, override_settings
from django.urls import reverse
from main.models import Testimonial

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestimonialTemplateTest(TestCase):
    """Basic template tests for Testimonial view"""
    
    @classmethod
    def setUpTestData(cls):
        Testimonial.objects.create(
            name="Test User",
            position="Test Position",
            organization="Test Org",
            testimonial="Test testimonial text.",
            image=""
        )
    
    def test_correct_template_used(self):
        """Test that correct template is used"""
        response = self.client.get(reverse('main:testimonial_list'))
        self.assertTemplateUsed(response, 'main/snippets_templates/table/testimonial_list.html')
    
    def test_template_displays_data(self):
        """Test that data appears in template"""
        response = self.client.get(reverse('main:testimonial_list'))
        
        # Test basic content
        self.assertContains(response, "Test User")
        self.assertContains(response, "Test Position")
        self.assertContains(response, "Test Org")
        self.assertContains(response, "Test testimonial text.")
        
        # Test template renders HTML
        self.assertContains(response, '<html', html=False)
    
    def test_template_empty_state(self):
        """Test template with no testimonials"""
        Testimonial.objects.all().delete()
        response = self.client.get(reverse('main:testimonial_list'))
        self.assertEqual(response.status_code, 200)