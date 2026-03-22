from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from news.models import Category, NewsArticle
from unittest.mock import patch
import time

User = get_user_model()


class PerformanceTest(TestCase):
    """Performance tests measuring response time and status codes"""

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="News")
        
        # Create articles for performance testing
        with patch('news.models.generate_article_summary', return_value='Summary'):
            for i in range(50):
                NewsArticle.objects.create(
                    category=self.category,
                    title=f"Article {i+1}",
                    author="Author",
                    featured_image="img.jpg",
                    content=f"Content for article {i+1}",
                    status="PUBLISHED" if i % 2 == 0 else "DRAFT",
                    views=i * 10
                )

    def test_landing_page_performance(self):
        """Performance test: Landing page response time < 500ms"""
        start_time = time.time()
        response = self.client.get(reverse('news:home'))
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 500, f"Landing page took {execution_time}ms (threshold: 500ms)")

    def test_article_list_page_performance(self):
        """Performance test: Article listing page response time < 800ms"""
        start_time = time.time()
        response = self.client.get(reverse('news:news_listing'))
        execution_time = (time.time() - start_time) * 1000
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 800, f"Article list took {execution_time}ms (threshold: 800ms)")

    def test_article_list_with_pagination_performance(self):
        """Performance test: Article listing page 2 response time < 800ms"""
        start_time = time.time()
        response = self.client.get(reverse('news:news_listing'), {'page': 2})
        execution_time = (time.time() - start_time) * 1000
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 800, f"Article list page 2 took {execution_time}ms (threshold: 800ms)")

    def test_article_detail_performance(self):
        """Performance test: Article detail page response time < 600ms"""
        article = NewsArticle.objects.filter(status='PUBLISHED').first()
        
        start_time = time.time()
        response = self.client.get(
            reverse('news:article_detail', kwargs={'slug': article.slug})
        )
        execution_time = (time.time() - start_time) * 1000
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 600, f"Article detail took {execution_time}ms (threshold: 600ms)")

    def test_category_list_performance(self):
        """Performance test: Category articles page response time < 700ms"""
        start_time = time.time()
        response = self.client.get(
            reverse('news:category_detail', kwargs={'slug': self.category.slug})
        )
        execution_time = (time.time() - start_time) * 1000
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 700, f"Category list took {execution_time}ms (threshold: 700ms)")

    def test_search_performance(self):
        """Performance test: Search response time < 900ms"""
        start_time = time.time()
        response = self.client.get(reverse('news:news_listing'), {'q': 'Article'})
        execution_time = (time.time() - start_time) * 1000
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 900, f"Search took {execution_time}ms (threshold: 900ms)")

    @patch('news.views.send_mail')
    def test_subscribe_endpoint_performance(self, mock_send_mail):
        """Performance test: Subscribe endpoint response time < 1000ms"""
        start_time = time.time()
        response = self.client.post(
            reverse('news:subscribe'),
            {'email': 'perftest@example.com'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        execution_time = (time.time() - start_time) * 1000
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 1000, f"Subscribe took {execution_time}ms (threshold: 1000ms)")

    def test_confirm_email_endpoint_performance(self):
        """Performance test: Email confirmation endpoint response time < 400ms"""
        from news.models import Subscriber
        subscriber = Subscriber.objects.create(email='perf@example.com')
        
        start_time = time.time()
        response = self.client.get(
            reverse('news:confirm-email', kwargs={'token': subscriber.conf_token})
        )
        execution_time = (time.time() - start_time) * 1000
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 400, f"Confirm email took {execution_time}ms (threshold: 400ms)")

    def test_database_query_efficiency(self):
        """Performance test: Article list doesn't cause N+1 queries"""
        from django.test.utils import override_settings
        from django.db import connection
        from django.test import Client as TestClient
        
        # Get baseline query count
        start_queries = len(connection.queries)
        response = self.client.get(reverse('news:home'))
        query_count = len(connection.queries) - start_queries
        
        # Should use reasonable number of queries (not N+1)
        # Landing page is paginated by 7, so we expect around 3-5 queries max
        self.assertLess(query_count, 15, f"Query count: {query_count} (too many for N+1)")
