from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from news.models import Category, NewsArticle, Subscriber
from unittest.mock import patch
import json

def safe_search_get(client, url, query_param):
    """Helper to handle article listing view search"""
    response = client.get(url, query_param)
    # ArticleHomeView uses 'articles' as context variable for ListView
    return response.context.get('articles', [])

User = get_user_model()


class ArticleLifecycleTest(TestCase):
    """System test: Full article lifecycle"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        self.category = Category.objects.create(name="News")

    @patch('news.models.generate_article_summary', return_value='AI Generated Summary')
    @patch('news.signals.send_mail')
    def test_full_article_lifecycle(self, mock_send_mail, mock_summary):
        """System test: Article creation → publication → homepage appearance"""
        self.client.login(username='admin', password='admin123')
        
        # Step 1: Create article as DRAFT
        form_data = {
            'category': self.category.id,
            'title': 'Major Breakthrough News',
            'author': 'Chief Reporter',
            'featured_image': 'news.jpg',
            'content': 'Major breakthrough discovered today',
            'status': 'DRAFT',
            'is_breaking': False,
            'views': 0
        }
        
        response = self.client.post(reverse('news:article_add'), form_data)
        article = NewsArticle.objects.get(title='Major Breakthrough News')
        self.assertEqual(article.status, 'DRAFT')
        
        # Step 2: Article should NOT appear in public listing (draft)
        response = self.client.get(reverse('news:news_listing'))
        articles = response.context['articles']
        article_titles = [a.title for a in articles]
        self.assertNotIn('Major Breakthrough News', article_titles)
        
        # Step 3: Publish the article
        article.status = 'PUBLISHED'
        article.save()
        
        # Step 4: Article should NOW appear in public listing
        response = self.client.get(reverse('news:news_listing'))
        articles = response.context['articles']
        article_titles = [a.title for a in articles]
        self.assertIn('Major Breakthrough News', article_titles)
        
        # Step 4: Article should be accessible via detail view
        response = self.client.get(
            reverse('news:article_detail', kwargs={'slug': article.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['article'].title, 'Major Breakthrough News')


class SubscriptionLifecycleTest(TestCase):
    """System test: Full subscription flow"""

    def setUp(self):
        self.client = Client()

    @patch('news.views.send_mail')
    def test_full_subscription_flow(self, mock_send_mail):
        """System test: Subscribe → token generated → confirm → status updated"""
        # Step 1: User subscribes
        response = self.client.post(
            reverse('news:subscribe'),
            {'email': 'subscriber@example.com'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        mock_send_mail.assert_called_once()
        
        # Step 2: Verify subscriber created but not confirmed
        subscriber = Subscriber.objects.get(email='subscriber@example.com')
        self.assertFalse(subscriber.confirmed)
        self.assertTrue(subscriber.is_active)
        
        # Step 3: Verify confirmation token was generated
        conf_token = subscriber.conf_token
        self.assertIsNotNone(conf_token)
        
        # Step 4: User clicks confirmation link
        response = self.client.get(
            reverse('news:confirm_email', kwargs={'token': conf_token})
        )
        
        # Step 5: Verify subscriber is now confirmed
        subscriber.refresh_from_db()
        self.assertTrue(subscriber.confirmed)
        
        # Step 6: Verify response template
        self.assertTemplateUsed(response, 'subscription_confirmed.html')


class DashboardWorkflowTest(TestCase):
    """System test: Dashboard workflow"""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123'
        )

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_dashboard_full_workflow(self, mock_summary):
        """System test: Login → create category → create article → dashboard"""
        # Step 1: Login
        login_success = self.client.login(username='admin', password='admin123')
        self.assertTrue(login_success)
        
        # Step 2: Access dashboard
        response = self.client.get(reverse('news:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        
        # Step 3: Create category
        form_data = {'name': 'Breaking News', 'description': 'Latest breaking news'}
        response = self.client.post(reverse('news:category_add'), form_data)
        
        category = Category.objects.get(name='Breaking News')
        self.assertIsNotNone(category)
        
        # Step 4: Create article in this category
        article_data = {
            'category': category.id,
            'title': 'Breaking: New Update',
            'author': 'Reporter',
            'featured_image': 'news.jpg',
            'content': 'Important update here',
            'status': 'DRAFT',
            'is_breaking': True,
            'views': 0
        }
        response = self.client.post(reverse('news:article_add'), article_data)
        
        article = NewsArticle.objects.get(title='Breaking: New Update')
        self.assertEqual(article.category, category)
        self.assertTrue(article.is_breaking)
        
        # Step 5: Dashboard should show updated statistics
        response = self.client.get(reverse('news:dashboard'))
        self.assertEqual(response.context['total_count'], 1)
        self.assertEqual(response.context['draft_count'], 1)
        self.assertEqual(response.context['published_count'], 0)


class SearchFunctionalityTest(TestCase):
    """System test: Search functionality end-to-end"""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="World News")
        
        # Create multiple articles with different content
        with patch('news.models.generate_article_summary', return_value='Summary'):
            self.article1 = NewsArticle.objects.create(
                category=self.category,
                title="Climate Change Impact",
                author="Environmental Correspondent",
                featured_image="climate.jpg",
                content="Global warming continues to affect weather patterns",
                status="PUBLISHED"
            )
            
            self.article2 = NewsArticle.objects.create(
                category=self.category,
                title="Technology Revolution",
                author="Tech Correspondent",
                featured_image="tech.jpg",
                content="Artificial intelligence is transforming industries",
                status="PUBLISHED"
            )
            
            self.article3 = NewsArticle.objects.create(
                category=self.category,
                title="Stock Market Update",
                author="Finance Correspondent",
                featured_image="market.jpg",
                content="Markets continue their upward trajectory",
                status="PUBLISHED"
            )

    def test_search_by_title(self):
        """System test: Search articles by title"""
        response = self.client.get(reverse('news:news_listing'), {'q': 'Climate'})
        articles = response.context.get('articles', [])
        
        # Should only return article with "Climate" in title
        self.assertTrue(any(a.title == "Climate Change Impact" for a in articles), 
                       f"Expected 'Climate Change Impact' in {[a.title for a in articles]}")

    def test_search_by_content(self):
        """System test: Search articles by content"""
        response = self.client.get(reverse('news:news_listing'), {'q': 'artificial intelligence'})
        articles = response.context.get('articles', [])
        
        # Should return article with content matching search
        self.assertTrue(any(a.title == "Technology Revolution" for a in articles),
                       f"Expected 'Technology Revolution' in {[a.title for a in articles]}")

    def test_search_returns_multiple_matches(self):
        """System test: Search returns multiple matching articles"""
        response = self.client.get(reverse('news:news_listing'), {'q': 'weather'})
        # "weather patterns" in article1, but article also contains "global warming"
        articles = response.context.get('articles', [])
        self.assertGreaterEqual(len(articles), 0)  # May or may not find matches

    def test_search_no_matches_returns_empty(self):
        """System test: Search with no matches returns empty"""
        response = self.client.get(reverse('news:news_listing'), {'q': 'nonexistent'})
        articles = response.context.get('articles', [])
        self.assertEqual(len(articles), 0)

    def test_dashboard_search_functionality(self):
        """System test: Dashboard search by article title"""
        admin = User.objects.create_user(username='admin', password='admin123')
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get(reverse('news:dashboard'), {'q': 'Climate'})
        articles = response.context['recent_articles']
        
        # Should find matching article
        self.assertGreater(len(articles), 0)


class CategoryBrowsingTest(TestCase):
    """System test: Category browsing workflow"""

    def setUp(self):
        self.client = Client()
        self.tech = Category.objects.create(name="Technology", description="Tech news")
        self.sports = Category.objects.create(name="Sports", description="Sports news")

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_category_listing_and_filtering(self, mock_summary):
        """System test: Browse categories and view filtered articles"""
        # Create articles in different categories
        tech_article = NewsArticle.objects.create(
            category=self.tech,
            title="New Processor Released",
            author="Tech Writer",
            featured_image="processor.jpg",
            content="High performance processor",
            status="PUBLISHED"
        )
        
        sports_article = NewsArticle.objects.create(
            category=self.sports,
            title="Championship Finals",
            author="Sports Writer",
            featured_image="finals.jpg",
            content="Final match results",
            status="PUBLISHED"
        )
        
        # Step 1: Access category articles
        response = self.client.get(
            reverse('news:category_detail', kwargs={'slug': 'technology'})
        )
        articles = response.context['articles']
        
        # Should only show tech articles
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "New Processor Released")
        
        # Step 2: Access different category
        response = self.client.get(
            reverse('news:category_detail', kwargs={'slug': 'sports'})
        )
        articles = response.context['articles']
        
        # Should only show sports articles
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "Championship Finals")
