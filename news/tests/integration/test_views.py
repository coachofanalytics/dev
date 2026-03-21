from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from news.models import Category, NewsArticle, Subscriber
from unittest.mock import patch
import json

User = get_user_model()


class PublicViewsTest(TestCase):
    """Integration tests for public views"""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Tech", description="Technology news")
        
        # Create a published article
        with patch('news.models.generate_article_summary', return_value='Mocked summary'):
            self.article = NewsArticle.objects.create(
                category=self.category,
                title="Breaking Tech News",
                author="Reporter",
                featured_image="news.jpg",
                content="Latest in technology",
                status="PUBLISHED",
                ai_summary="Breaking tech update"
            )

    def test_landing_page_view_returns_200(self):
        """Test landing page view returns status 200"""
        response = self.client.get(reverse('news:home'))
        self.assertEqual(response.status_code, 200)

    def test_landing_page_view_uses_correct_template(self):
        """Test landing page uses correct template"""
        response = self.client.get(reverse('news:home'))
        self.assertTemplateUsed(response, 'home.html')

    def test_landing_page_context_contains_latest_news(self):
        """Test landing page context has latest_news"""
        response = self.client.get(reverse('news:home'))
        self.assertIn('latest_news', response.context)
        self.assertEqual(len(response.context['latest_news']), 1)

    def test_landing_page_context_contains_categories(self):
        """Test landing page context has categories"""
        response = self.client.get(reverse('news:home'))
        self.assertIn('categories', response.context)

    def test_article_home_view_returns_200(self):
        """Test article listing view returns status 200"""
        response = self.client.get(reverse('news:news_listing'))
        self.assertEqual(response.status_code, 200)

    def test_article_home_view_uses_correct_template(self):
        """Test article listing uses correct template"""
        response = self.client.get(reverse('news:news_listing'))
        self.assertTemplateUsed(response, 'news_listing.html')

    def test_article_home_view_shows_published_articles(self):
        """Test article listing shows only published articles"""
        with patch('news.models.generate_article_summary', return_value='Summary'):
            draft_article = NewsArticle.objects.create(
                category=self.category,
                title="Draft Article",
                author="Author",
                featured_image="draft.jpg",
                content="Draft content",
                status="DRAFT"
            )
        
        response = self.client.get(reverse('news:news_listing'))
        articles = response.context['articles']
        
        # Should only contain published article
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "Breaking Tech News")

    def test_article_home_pagination(self):
        """Test article listing pagination works"""
        response = self.client.get(reverse('news:news_listing'))
        self.assertIn('is_paginated', response.context)

    def test_article_detail_view_returns_200(self):
        """Test article detail view returns status 200"""
        response = self.client.get(
            reverse('news:article-detail', kwargs={'slug': self.article.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_article_detail_view_uses_correct_template(self):
        """Test article detail uses correct template"""
        response = self.client.get(
            reverse('news:article-detail', kwargs={'slug': self.article.slug})
        )
        self.assertTemplateUsed(response, 'article_detail.html')

    def test_article_detail_view_has_correct_article(self):
        """Test article detail view shows correct article"""
        response = self.client.get(
            reverse('news:article-detail', kwargs={'slug': self.article.slug})
        )
        self.assertEqual(response.context['article'], self.article)

    def test_article_detail_shows_related_articles(self):
        """Test article detail shows related articles from same category"""
        response = self.client.get(
            reverse('news:article-detail', kwargs={'slug': self.article.slug})
        )
        self.assertIn('related_articles', response.context)

    def test_category_article_list_returns_200(self):
        """Test category article list view returns status 200"""
        response = self.client.get(
            reverse('news:category_detail', kwargs={'slug': self.category.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_category_article_list_template(self):
        """Test category article list uses correct template"""
        response = self.client.get(
            reverse('news:category_detail', kwargs={'slug': self.category.slug})
        )
        self.assertTemplateUsed(response, 'category_articles.html')


class AuthenticationRequiredViewsTest(TestCase):
    """Test views that require authentication"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name="Business")

    def test_admin_dashboard_redirects_unauthenticated(self):
        """Test dashboard redirects unauthenticated users to login"""
        response = self.client.get(reverse('news:dashboard'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_admin_dashboard_accessible_to_authenticated(self):
        """Test dashboard is accessible to authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('news:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_dashboard_context_has_statistics(self):
        """Test dashboard context has all required statistics"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('news:dashboard'))
        
        self.assertIn('total_count', response.context)
        self.assertIn('published_count', response.context)
        self.assertIn('draft_count', response.context)
        self.assertIn('subscriber_count', response.context)

    def test_category_create_redirects_unauthenticated(self):
        """Test category create view redirects unauthenticated users"""
        response = self.client.get(reverse('news:category_add'), follow=False)
        self.assertEqual(response.status_code, 302)

    def test_category_create_accessible_to_authenticated(self):
        """Test category create is accessible to authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('news:category_add'))
        self.assertEqual(response.status_code, 200)

    def test_article_create_redirects_unauthenticated(self):
        """Test article create view redirects unauthenticated users"""
        response = self.client.get(reverse('news:article_add'), follow=False)
        self.assertEqual(response.status_code, 302)

    def test_article_create_accessible_to_authenticated(self):
        """Test article create is accessible to authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('news:article_add'))
        self.assertEqual(response.status_code, 200)

    def test_article_edit_redirects_unauthenticated(self):
        """Test article edit redirects unauthenticated users"""
        with patch('news.models.generate_article_summary', return_value='Summary'):
            article = NewsArticle.objects.create(
                category=self.category,
                title="Test Article",
                author="Author",
                featured_image="img.jpg",
                content="Content"
            )
        
        response = self.client.get(
            reverse('news:article_edit', kwargs={'pk': article.id}),
            follow=False
        )
        self.assertEqual(response.status_code, 302)

    def test_article_delete_redirects_unauthenticated(self):
        """Test article delete redirects unauthenticated users"""
        with patch('news.models.generate_article_summary', return_value='Summary'):
            article = NewsArticle.objects.create(
                category=self.category,
                title="Test Article",
                author="Author",
                featured_image="img.jpg",
                content="Content"
            )
        
        response = self.client.get(
            reverse('news:article_delete', kwargs={'pk': article.id}),
            follow=False
        )
        self.assertEqual(response.status_code, 302)


class SubscriptionEndpointTest(TestCase):
    """Integration tests for subscribe endpoint"""

    def setUp(self):
        self.client = Client()

    @patch('news.views.send_mail')
    def test_subscribe_with_valid_email_success(self, mock_send_mail):
        """Test POST to subscribe with valid email returns success"""
        response = self.client.post(
            reverse('news:subscribe'),
            {'email': 'newuser@example.com'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        mock_send_mail.assert_called_once()

    @patch('news.views.send_mail')
    def test_subscribe_duplicate_email_response(self, mock_send_mail):
        """Test POST to subscribe with existing email returns exists"""
        Subscriber.objects.create(email='existing@example.com')
        
        response = self.client.post(
            reverse('news:subscribe'),
            {'email': 'existing@example.com'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'exists')

    def test_subscribe_missing_email(self):
        """Test POST to subscribe without email returns error"""
        response = self.client.post(
            reverse('news:subscribe'),
            {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')

    def test_subscribe_get_request_returns_405(self):
        """Test GET request to subscribe returns 405"""
        response = self.client.get(reverse('news:subscribe'))
        self.assertEqual(response.status_code, 405)

    @patch('news.views.send_mail')
    def test_subscribe_creates_subscriber(self, mock_send_mail):
        """Test subscribe creates new Subscriber"""
        response = self.client.post(
            reverse('news:subscribe'),
            {'email': 'newuser@example.com'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertTrue(Subscriber.objects.filter(email='newuser@example.com').exists())

    @patch('news.views.send_mail')
    def test_subscribe_creates_conf_token(self, mock_send_mail):
        """Test subscribe creates confirmation token"""
        response = self.client.post(
            reverse('news:subscribe'),
            {'email': 'newuser@example.com'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        subscriber = Subscriber.objects.get(email='newuser@example.com')
        self.assertIsNotNone(subscriber.conf_token)

    def test_confirm_email_endpoint_sets_confirmed_true(self):
        """Test email confirmation sets confirmed to True"""
        subscriber = Subscriber.objects.create(email='test@example.com', confirmed=False)
        
        response = self.client.get(
            reverse('news:confirm_email', kwargs={'token': subscriber.conf_token})
        )
        
        subscriber.refresh_from_db()
        self.assertTrue(subscriber.confirmed)


class ArticleCRUDTest(TestCase):
    """Integration tests for article CRUD operations"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name="News")
        self.client.login(username='testuser', password='testpass123')

    @patch('news.models.generate_article_summary', return_value='AI Summary')
    def test_article_create_form_submission(self, mock_summary):
        """Test article can be created via form submission"""
        form_data = {
            'category': self.category.id,
            'title': 'New Article',
            'author': 'Test Author',
            'featured_image': 'test.jpg',
            'content': 'Test content here',
            'status': 'DRAFT',
            'ai_summary': 'Generated summary',  
            'is_breaking': False,
            'views': 0
        }
        
        response = self.client.post(
            reverse('news:article_add'),
            form_data,
            follow=True
        )
        
        # Verify the article exists
        self.assertTrue(NewsArticle.objects.filter(title='New Article').exists())

    @patch('news.models.generate_article_summary', return_value='AI Summary')
    def test_article_create_form_submission(self, mock_summary):
        """Test article can be created via form submission"""
        form_data = {
            'category': self.category.id,
            'title': 'New Article',
            'author': 'Test Author',
            'featured_image': 'test.jpg',
            'content': 'Test content here',
            'status': 'DRAFT',
            'is_breaking': False,
            'views': 0
        }
        
        response = self.client.post(
            reverse('news:article_add'),
            form_data,
            follow=True
        )
        
        self.assertTrue(NewsArticle.objects.filter(title='New Article').exists())

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_article_create_redirects_to_dashboard(self, mock_summary):
        """Test article create redirects to dashboard after success"""
        form_data = {
            'category': self.category.id,
            'title': 'New Article',
            'author': 'Test Author',
            'featured_image': 'test.jpg',
            'content': 'Test content here',
            'status': 'DRAFT'
        }
        
        response = self.client.post(
            reverse('news:article_add'),
            form_data,
            follow=True
        )
        
        self.assertTemplateUsed(response, 'dashboard.html')

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_article_edit_updates_content(self, mock_summary):
        """Test article can be edited"""
        article = NewsArticle.objects.create(
            category=self.category,
            title="Original Title",
            author="Original Author",
            featured_image="test.jpg",
            content="Original content"
        )
        
        form_data = {
            'category': self.category.id,
            'title': 'Updated Title',
            'author': 'Updated Author',
            'featured_image': 'test.jpg',
            'content': 'Updated content',
            'status': 'DRAFT'
        }
        
        response = self.client.post(
            reverse('news:article_edit', kwargs={'pk': article.id}),
            form_data,
            follow=True
        )
        
        article.refresh_from_db()
        self.assertEqual(article.title, 'Updated Title')
        self.assertEqual(article.author, 'Updated Author')

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_article_delete_removes_article(self, mock_summary):
        """Test article can be deleted"""
        article = NewsArticle.objects.create(
            category=self.category,
            title="To Delete",
            author="Author",
            featured_image="test.jpg",
            content="Content"
        )
        article_id = article.id
        
        response = self.client.post(
            reverse('news:article_delete', kwargs={'pk': article.id}),
            follow=True
        )
        
        self.assertFalse(NewsArticle.objects.filter(id=article_id).exists())
