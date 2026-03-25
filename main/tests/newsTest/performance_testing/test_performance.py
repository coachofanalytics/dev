"""
Performance Tests for News Models
Tests for bulk operations, query optimization, and performance characteristics
"""

from django.test import TestCase, TransactionTestCase, override_settings
from django.db import connection, reset_queries
from unittest.mock import patch
import time

from main.models import Category, NewsArticle, Subscriber


@override_settings(DEBUG=True)  # Enable query counting
class BulkArticleCreationPerformanceTests(TransactionTestCase):
    """Tests for bulk article creation performance"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'AI Summary'
        self.category = Category.objects.create(name='News')

    def tearDown(self):
        self.ai_patcher.stop()

    def test_bulk_create_100_articles(self):
        """Performance Test: Create 100 articles efficiently"""
        reset_queries()

        articles = [
            NewsArticle(
                category=self.category,
                title=f'Article {i}',
                author='Author',
                content=f'Content {i}',
                featured_image='path.jpg'
            )
            for i in range(100)
        ]

        start_time = time.time()
        NewsArticle.objects.bulk_create(articles, batch_size=50)
        elapsed = time.time() - start_time

        self.assertLess(elapsed, 5.0, "Bulk create of 100 articles took too long")
        self.assertEqual(NewsArticle.objects.count(), 100)

    def test_bulk_create_1000_articles(self):
        """Performance Test: Create 1000 articles"""
        reset_queries()

        articles = [
            NewsArticle(
                category=self.category,
                title=f'Article {i}',
                author='Author',
                content=f'Content {i}',
                featured_image='path.jpg'
            )
            for i in range(1000)
        ]

        start_time = time.time()
        NewsArticle.objects.bulk_create(articles, batch_size=100)
        elapsed = time.time() - start_time

        self.assertLess(elapsed, 15.0, "Bulk create of 1000 took too long")
        self.assertEqual(NewsArticle.objects.count(), 1000)

    def test_bulk_create_vs_individual_create(self):
        """Performance Test: Bulk create faster than individual saves"""
        # Individual creates
        start_time = time.time()
        for i in range(50):
            NewsArticle.objects.create(
                category=self.category,
                title=f'Individual {i}',
                author='Author',
                content='Content',
                featured_image='path.jpg'
            )
        individual_time = time.time() - start_time

        # Bulk create
        articles = [
            NewsArticle(
                category=self.category,
                title=f'Bulk {i}',
                author='Author',
                content='Content',
                featured_image='path.jpg'
            )
            for i in range(50)
        ]
        start_time = time.time()
        NewsArticle.objects.bulk_create(articles)
        bulk_time = time.time() - start_time

        # Bulk should be faster
        self.assertLess(bulk_time, individual_time,
                       f"Bulk ({bulk_time}s) not faster than individual ({individual_time}s)")


class BulkSubscriberCreationPerformanceTests(TransactionTestCase):
    """Tests for bulk subscriber operations"""

    def test_bulk_create_500_subscribers(self):
        """Performance Test: Create 500 subscribers efficiently"""
        reset_queries()

        subscribers = [
            Subscriber(email=f'user{i}@example.com')
            for i in range(500)
        ]

        start_time = time.time()
        Subscriber.objects.bulk_create(subscribers, batch_size=100)
        elapsed = time.time() - start_time

        self.assertLess(elapsed, 5.0, "Bulk create subscribers took too long")
        self.assertEqual(Subscriber.objects.count(), 500)

    def test_bulk_update_subscriber_status(self):
        """Performance Test: Bulk update subscriber status efficiently"""
        # Create subscribers
        subscribers = [
            Subscriber(email=f'user{i}@example.com', confirmed=False)
            for i in range(100)
        ]
        Subscriber.objects.bulk_create(subscribers)

        # Bulk update
        to_update = list(Subscriber.objects.filter(confirmed=False))
        for sub in to_update:
            sub.confirmed = True

        start_time = time.time()
        Subscriber.objects.bulk_update(to_update, ['confirmed'], batch_size=50)
        elapsed = time.time() - start_time

        self.assertLess(elapsed, 2.0, "Bulk update took too long")

        confirmed_count = Subscriber.objects.filter(confirmed=True).count()
        self.assertEqual(confirmed_count, 100)


@override_settings(DEBUG=True)
class QueryOptimizationTests(TestCase):
    """Tests for query optimization and N+1 detection"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'

        self.category = Category.objects.create(name='News')
        for i in range(10):
            NewsArticle.objects.create(
                category=self.category,
                title=f'Article {i}',
                author='Author',
                content='Content',
                featured_image='path.jpg'
            )

    def tearDown(self):
        self.ai_patcher.stop()

    def test_n_plus_one_article_category_access(self):
        """Performance Test: Detect N+1 when accessing article.category"""
        reset_queries()

        articles = NewsArticle.objects.all()[:5]
        for article in articles:
            _category = article.category.name  # Causes N+1

        query_count_without_optimization = len(connection.queries)

        # Should have N+1 queries (1 for articles + 5 for categories)
        self.assertGreaterEqual(query_count_without_optimization, 6)

    def test_select_related_optimization(self):
        """Performance Test: select_related reduces queries"""
        reset_queries()

        articles = NewsArticle.objects.select_related('category')[:5]
        for article in articles:
            _category = article.category.name  # No additional queries

        query_count_with_optimization = len(connection.queries)

        # Should be 1 query
        self.assertEqual(query_count_with_optimization, 1)

    def test_filter_by_category_efficiency(self):
        """Performance Test: Filter by category is efficient"""
        reset_queries()

        articles = NewsArticle.objects.filter(category__name='News')
        list(articles)

        query_count = len(connection.queries)
        self.assertEqual(query_count, 1)

    def test_count_efficiency(self):
        """Performance Test: count() is efficient"""
        reset_queries()

        count = NewsArticle.objects.count()

        query_count = len(connection.queries)
        self.assertEqual(query_count, 1)
        self.assertEqual(count, 10)

    def test_exists_efficiency(self):
        """Performance Test: exists() is efficient"""
        reset_queries()

        exists = NewsArticle.objects.filter(title__contains='Article').exists()

        query_count = len(connection.queries)
        # exists() should be 1 query
        self.assertEqual(query_count, 1)
        self.assertTrue(exists)


@override_settings(DEBUG=True)
class FilteringPerformanceTests(TestCase):
    """Tests for filtering performance"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'

        self.category = Category.objects.create(name='News')

        # Create half published, half draft
        for i in range(100):
            status = 'PUBLISHED' if i % 2 == 0 else 'DRAFT'
            NewsArticle.objects.create(
                category=self.category,
                title=f'Article {i}',
                author='Author',
                content='Content',
                featured_image='path.jpg',
                status=status,
                views=i % 10
            )

    def tearDown(self):
        self.ai_patcher.stop()

    def test_status_filter_performance(self):
        """Performance Test: Status filter is efficient"""
        reset_queries()

        published = NewsArticle.objects.filter(status='PUBLISHED')
        count = published.count()

        query_count = len(connection.queries)
        self.assertEqual(query_count, 1)
        self.assertEqual(count, 50)

    def test_complex_filter_performance(self):
        """Performance Test: Complex filters execute efficiently"""
        reset_queries()

        from django.db.models import Q
        articles = NewsArticle.objects.filter(
            Q(status='PUBLISHED') & Q(views__gte=5)
        )
        list(articles)

        query_count = len(connection.queries)
        self.assertEqual(query_count, 1)

    def test_exclude_filter_performance(self):
        """Performance Test: Exclude filters are efficient"""
        reset_queries()

        drafts = NewsArticle.objects.exclude(status='PUBLISHED')
        count = drafts.count()

        query_count = len(connection.queries)
        self.assertEqual(query_count, 1)
        self.assertEqual(count, 50)

    def test_ordering_performance(self):
        """Performance Test: Ordering is efficient"""
        reset_queries()

        articles = NewsArticle.objects.order_by('-views')[:10]
        list(articles)

        query_count = len(connection.queries)
        self.assertEqual(query_count, 1)


class SlugGenerationPerformanceTests(TestCase):
    """Tests for slug generation performance"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'
        self.category = Category.objects.create(name='News')

    def tearDown(self):
        self.ai_patcher.stop()

    def test_long_title_slug_generation(self):
        """Performance Test: Long title slug generation is fast"""
        long_title = 'A Very Long Article Title That Contains Many Words ' * 20

        start_time = time.time()
        article = NewsArticle.objects.create(
            category=self.category,
            title=long_title,
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )
        elapsed = time.time() - start_time

        self.assertLess(elapsed, 1.0)
        self.assertLessEqual(len(article.slug), 250)

    def test_special_character_slug_generation(self):
        """Performance Test: Special character slug generation is fast"""
        title = "Article with @#$%^&*() special chars & symbols!"

        start_time = time.time()
        article = NewsArticle.objects.create(
            category=self.category,
            title=title,
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )
        elapsed = time.time() - start_time

        self.assertLess(elapsed, 1.0)
        self.assertIsNotNone(article.slug)


class LargeContentPerformanceTests(TestCase):
    """Tests for handling large content"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'
        self.category = Category.objects.create(name='News')

    def tearDown(self):
        self.ai_patcher.stop()

    def test_very_large_content_field(self):
        """Performance Test: Large content fields handled efficiently"""
        large_content = "Article content. " * 10000  # Very large text

        start_time = time.time()
        article = NewsArticle.objects.create(
            category=self.category,
            title='Article',
            author='Author',
            content=large_content,
            featured_image='path.jpg'
        )
        elapsed = time.time() - start_time

        self.assertLess(elapsed, 2.0)

        retrieved = NewsArticle.objects.get(id=article.id)
        self.assertEqual(len(retrieved.content), len(large_content))

    def test_retrieve_large_result_set(self):
        """Performance Test: Retrieving large result sets"""
        # Create 200 articles
        articles = [
            NewsArticle(
                category=self.category,
                title=f'Article {i}',
                author='Author',
                content='Content',
                featured_image='path.jpg'
            )
            for i in range(200)
        ]
        NewsArticle.objects.bulk_create(articles)

        reset_queries()

        start_time = time.time()
        all_articles = list(NewsArticle.objects.all())
        elapsed = time.time() - start_time

        self.assertLess(elapsed, 1.0)
        self.assertEqual(len(all_articles), 200)


class PaginationPerformanceTests(TestCase):
    """Tests for pagination performance"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'

        self.category = Category.objects.create(name='News')

        articles = [
            NewsArticle(
                category=self.category,
                title=f'Article {i}',
                author='Author',
                content='Content',
                featured_image='path.jpg'
            )
            for i in range(100)
        ]
        NewsArticle.objects.bulk_create(articles)

    def tearDown(self):
        self.ai_patcher.stop()

    def test_pagination_with_ordering(self):
        """Performance Test: Pagination with ordering"""
        reset_queries()

        # Get page 3 (items 20-30)
        articles = NewsArticle.objects.order_by('-id')[20:30]
        list(articles)

        query_count = len(connection.queries)
        self.assertEqual(query_count, 1)

    def test_limit_clause_efficiency(self):
        """Performance Test: LIMIT clause efficiency"""
        reset_queries()

        articles = NewsArticle.objects.all()[:10]
        list(articles)

        query_count = len(connection.queries)
        self.assertEqual(query_count, 1)


class SortingPerformanceTests(TestCase):
    """Tests for sorting and ordering performance"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'

        self.category = Category.objects.create(name='News')

        for i in range(50):
            NewsArticle.objects.create(
                category=self.category,
                title=f'Article {i}',
                author='Author',
                content='Content',
                featured_image='path.jpg',
                views=i % 10,
                is_breaking=i % 5 == 0
            )

    def tearDown(self):
        self.ai_patcher.stop()

    def test_order_by_single_field(self):
        """Performance Test: Order by single field"""
        reset_queries()

        articles = NewsArticle.objects.order_by('-views')[:20]
        list(articles)

        query_count = len(connection.queries)
        self.assertEqual(query_count, 1)

    def test_order_by_multiple_fields(self):
        """Performance Test: Order by multiple fields"""
        reset_queries()

        articles = NewsArticle.objects.order_by('-is_breaking', '-views')[:20]
        list(articles)

        query_count = len(connection.queries)
        self.assertEqual(query_count, 1)


class TransactionPerformanceTests(TransactionTestCase):
    """Tests for transaction performance"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'
        self.category = Category.objects.create(name='News')

    def tearDown(self):
        self.ai_patcher.stop()

    def test_bulk_atomic_operation(self):
        """Performance Test: Bulk atomic operation"""
        from django.db import transaction

        articles = [
            NewsArticle(
                category=self.category,
                title=f'Article {i}',
                author='Author',
                content='Content',
                featured_image='path.jpg'
            )
            for i in range(100)
        ]

        start_time = time.time()
        with transaction.atomic():
            NewsArticle.objects.bulk_create(articles)
        elapsed = time.time() - start_time

        self.assertLess(elapsed, 3.0)
        self.assertEqual(NewsArticle.objects.count(), 100)
