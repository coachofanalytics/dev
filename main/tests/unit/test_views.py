from django.test import TestCase, override_settings
from django.urls import reverse
from main.models import Testimonial

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestimonialListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create 2 testimonials for testing
        Testimonial.objects.create(
            name="Test Subject 1",
            position="Developer",
            organization="Test Corp",
            testimonial="Great service!",
            image=""
        )
        Testimonial.objects.create(
            name="Test Subject 2",
            position="Designer", 
            organization="Design Inc",
            testimonial="Excellent work!",
            image=""
        )
    
    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/Testimonial/')
        self.assertEqual(response.status_code, 200)
    
    def test_view_passes_correct_context(self):
        response = self.client.get(reverse('main:testimonial_list'))
        self.assertIn('testimonial', response.context)
        testimonials = response.context['testimonial']
        self.assertEqual(testimonials.count(), 2)
    
    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('main:testimonial_list'))
        self.assertTemplateUsed(response, 'main/snippets_templates/table/testimonial_list.html')