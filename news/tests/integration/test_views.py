from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from django.contrib.auth import get_user_model
from news.models import Category, NewsArticle, Subscriber

User = get_user_model()

@patch('news.ai_services.generate_article_summary', return_value='Mocked summary')
@patch('news.signals.send_mail')
@patch('django.core.mail.send_mail')
class ViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password123')
        cls.category = Category.objects.create(name='Tech')
        from django.core.files.uploadedfile import SimpleUploadedFile
        cls.article = NewsArticle.objects.create(
            category=cls.category, 
            title='Test Title', 
            content='Test content',
            status='PUBLISHED',
            featured_image='news_images/mock_image.jpg'
        )
        cls.public_urls = [
            reverse('news:home'),
            reverse('news:news_listing'),
            reverse('news:article_detail', kwargs={'slug': cls.article.slug}),
            reverse('news:category_detail', kwargs={'slug': cls.category.slug}),
        ]
        cls.protected_urls = [
            reverse('news:dashboard'),
            reverse('news:article_add'),
            reverse('news:article_edit', kwargs={'pk': cls.article.pk}),
            reverse('news:article_delete', kwargs={'pk': cls.article.pk}),
            reverse('news:category_add'),
            reverse('news:category_edit', kwargs={'pk': cls.category.pk}),
            reverse('news:category_delete', kwargs={'pk': cls.category.pk}),
        ]

    def setUp(self):
        self.client = Client()

    def test_public_views_200(self, mock_core_mail, mock_signal_mail, mock_ai_summary):
        for url in self.public_urls:
            response = self.client.get(url, follow=False)
            self.assertEqual(response.status_code, 200, f"URL {url} failed")

    def test_public_views_templates(self, mock_core_mail, mock_signal_mail, mock_ai_summary):
        templates_mapping = {
            reverse('news:home'): 'home.html',
            reverse('news:news_listing'): 'news_listing.html',
            reverse('news:article_detail', kwargs={'slug': self.article.slug}): 'article_detail.html',
            reverse('news:category_detail', kwargs={'slug': self.category.slug}): 'category_articles.html',
        }
        for url, template in templates_mapping.items():
            response = self.client.get(url, follow=False)
            self.assertTemplateUsed(response, template)

    def test_subscribe_post_valid_email(self, mock_core_mail, mock_signal_mail, mock_ai_summary):
        url = reverse('news:subscribe')
        response = self.client.post(url, {'email': 'new@example.com'}, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "msg": "Check your email to confirm!"})

    def test_subscribe_post_duplicate_email(self, mock_core_mail, mock_signal_mail, mock_ai_summary):
        Subscriber.objects.create(email='dup@example.com')
        url = reverse('news:subscribe')
        response = self.client.post(url, {'email': 'dup@example.com'}, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "exists", "msg": "you're already on the list."})

    def test_subscribe_post_invalid_email(self, mock_core_mail, mock_signal_mail, mock_ai_summary):
        url = reverse('news:subscribe')
        response = self.client.post(url, {}, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "error", "msg": "Invalid Request"})

    def test_protected_views_redirect_logged_out(self, mock_core_mail, mock_signal_mail, mock_ai_summary):
        for url in self.protected_urls:
            response = self.client.get(url, follow=False)
            self.assertEqual(response.status_code, 302, f"URL {url} should redirect")
            self.assertIn('/login/', response.url)

    def test_protected_views_200_logged_in(self, mock_core_mail, mock_signal_mail, mock_ai_summary):
        self.client.login(username='testuser', password='password123')
        for url in self.protected_urls:
            response = self.client.get(url, follow=False)
            self.assertEqual(response.status_code, 200, f"URL {url} failed to return 200")
