from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from django.contrib.auth import get_user_model
from news.models import Category, NewsArticle, Subscriber

User = get_user_model()

@patch('news.ai_services.generate_article_summary', return_value='Mocked summary')
@patch('news.signals.send_mail')
@patch('django.core.mail.send_mail')
class RegressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='admin', password='password123')
        cls.category = Category.objects.create(name='Tech regress')
        
        cls.published_articles = []
        for i in range(8):
            art = NewsArticle.objects.create(
                category=cls.category,
                title=f'Pub {i}',
                content='Test',
                status='PUBLISHED',
                featured_image='test.jpg'
            )
            cls.published_articles.append(art)
            
        cls.draft = NewsArticle.objects.create(
            category=cls.category,
            title='Draft Article',
            content='Draft',
            status='DRAFT',
            featured_image='test.jpg'
        )

        Subscriber.objects.create(email='confirmed1@test.com', confirmed=True)
        Subscriber.objects.create(email='confirmed2@test.com', confirmed=True)
        Subscriber.objects.create(email='unconfirmed@test.com', confirmed=False)

    def test_slug_unchanged_on_update(self, mock_core, mock_signal, mock_ai):
        art = self.published_articles[0]
        old_slug = art.slug
        art.title = "NEW TITLE FOR SLUG"
        art.save()
        self.assertEqual(art.slug, old_slug)

    def test_only_published_on_public_pages(self, mock_core, mock_signal, mock_ai):
        client = Client()
        
        response = client.get(reverse('news:home'))
        self.assertNotContains(response, 'Draft Article')
        
        response = client.get(reverse('news:news_listing'))
        self.assertNotContains(response, 'Draft Article')

        response = client.get(reverse('news:category_detail', kwargs={'slug': self.category.slug}))
        self.assertNotContains(response, 'Draft Article')

    def test_pagination_7_news_6_category(self, mock_core, mock_signal, mock_ai):
        client = Client()
        response = client.get(reverse('news:news_listing'))
        self.assertEqual(len(response.context['articles']), 7)
        
        response = client.get(reverse('news:category_detail', kwargs={'slug': self.category.slug}))
        self.assertEqual(len(response.context['articles']), 6)

    def test_dashboard_keys_and_subscriber_count(self, mock_core, mock_signal, mock_ai):
        client = Client()
        client.login(username='admin', password='password123')
        response = client.get(reverse('news:dashboard'))
        
        ctx = response.context
        self.assertIn('total_count', ctx)
        self.assertIn('published_count', ctx)
        self.assertIn('draft_count', ctx)
        self.assertIn('subscriber_count', ctx)
        self.assertIn('categories', ctx)
        self.assertIn('recent_articles', ctx)
        
        self.assertEqual(ctx['subscriber_count'], 2)

