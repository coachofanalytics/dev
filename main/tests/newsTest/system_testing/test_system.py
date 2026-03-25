"""
System Tests for News Models
Tests for complete workflows and user scenarios after migration
"""

from django.test import TestCase
from unittest.mock import patch
from main.models import Category, NewsArticle, Subscriber


class NewsPublishingWorkflowTests(TestCase):
    """Tests for complete news publishing workflows"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'AI Summary'

    def tearDown(self):
        self.ai_patcher.stop()

    def test_complete_news_publishing_workflow(self):
        """System Test: Admin creates category and publishes article"""
        # Step 1: Admin creates category
        category = Category.objects.create(
            name='Technology',
            description='Latest tech news'
        )
        self.assertIsNotNone(category.id)

        # Step 2: Admin creates article in draft
        article = NewsArticle.objects.create(
            category=category,
            title='New JavaScript Framework Released',
            author='Tech Correspondent',
            content='A groundbreaking new framework has been released...',
            featured_image='tech_framework.jpg',
            status='DRAFT'
        )

        # Step 3: Verify article is draft
        self.assertEqual(article.status, 'DRAFT')
        self.assertIsNotNone(article.ai_summary)

        # Step 4: Admin publishes article
        article.status = 'PUBLISHED'
        article.save()

        # Step 5: Verify article published
        article.refresh_from_db()
        self.assertEqual(article.status, 'PUBLISHED')

        # Step 6: Article appears in published list
        published = NewsArticle.objects.filter(status='PUBLISHED')
        self.assertIn(article, published)

    def test_create_multiple_articles_in_category(self):
        """System Test: Create multiple articles in same category"""
        category = Category.objects.create(name='Science')

        # Create articles
        articles = []
        for i in range(5):
            article = NewsArticle.objects.create(
                category=category,
                title=f'Science Article {i}',
                author='Scientist',
                content=f'Article about science topic {i}',
                featured_image='science.jpg',
                status='PUBLISHED' if i % 2 == 0 else 'DRAFT'
            )
            articles.append(article)

        # Verify all articles in category
        self.assertEqual(category.articles.count(), 5)

        # Verify filtering
        published = category.articles.filter(status='PUBLISHED')
        self.assertEqual(published.count(), 3)

        draft = category.articles.filter(status='DRAFT')
        self.assertEqual(draft.count(), 2)

    def test_article_update_workflow(self):
        """System Test: Update published article"""
        category = Category.objects.create(name='News')
        article = NewsArticle.objects.create(
            category=category,
            title='Breaking News',
            author='Reporter',
            content='Initial content',
            featured_image='news.jpg',
            status='PUBLISHED'
        )

        original_created = article.created_at

        # Update article
        article.title = 'Updated Breaking News'
        article.content = 'Updated content with more details'
        article.save()

        # Verify update
        article.refresh_from_db()
        self.assertEqual(article.title, 'Updated Breaking News')
        self.assertEqual(article.created_at, original_created)
        self.assertGreater(article.updated_at, original_created)

    def test_categorize_and_search_workflow(self):
        """System Test: Create categories and articles for searching"""
        # Create categories
        tech = Category.objects.create(name='Technology')
        science = Category.objects.create(name='Science')

        # Create articles
        tech_article = NewsArticle.objects.create(
            category=tech,
            title='Python 3.12 Released',
            author='Author',
            content='Python programming language update',
            featured_image='python.jpg',
            status='PUBLISHED'
        )

        science_article = NewsArticle.objects.create(
            category=science,
            title='New Quantum Computing Breakthrough',
            author='Author',
            content='Scientists discover quantum breakthrough',
            featured_image='quantum.jpg',
            status='PUBLISHED'
        )

        # Search by category
        tech_articles = NewsArticle.objects.filter(category=tech, status='PUBLISHED')
        science_articles = NewsArticle.objects.filter(category=science, status='PUBLISHED')

        self.assertEqual(tech_articles.count(), 1)
        self.assertEqual(science_articles.count(), 1)

        # Search by title
        python_articles = NewsArticle.objects.filter(title__icontains='Python')
        self.assertEqual(python_articles.count(), 1)


class SubscriberWorkflowTests(TestCase):
    """Tests for subscriber registration and confirmation workflows"""

    def test_subscriber_registration_workflow(self):
        """System Test: User subscribes and confirms"""
        # Step 1: User provides email
        subscriber = Subscriber.objects.create(email='john@example.com')

        # Step 2: Confirm not yet confirmed
        self.assertFalse(subscriber.confirmed)
        self.assertTrue(subscriber.is_active)

        # Step 3: User confirms subscription (via email link)
        found = Subscriber.objects.get(conf_token=subscriber.conf_token)
        found.confirmed = True
        found.save()

        # Step 4: Verify confirmation
        found.refresh_from_db()
        self.assertTrue(found.confirmed)

    def test_subscriber_unsubscribe_workflow(self):
        """System Test: Subscriber unsubscribes"""
        subscriber = Subscriber.objects.create(
            email='user@example.com',
            confirmed=True,
            is_active=True
        )

        # User unsubscribes
        subscriber.is_active = False
        subscriber.save()

        subscriber.refresh_from_db()
        self.assertFalse(subscriber.is_active)
        self.assertTrue(subscriber.confirmed)  # Confirmation status unchanged

    def test_multiple_subscribers_workflow(self):
        """System Test: Multiple users subscribe"""
        emails = [f'user{i}@example.com' for i in range(100)]
        
        # Bulk create subscribers
        subscribers = [Subscriber(email=email) for email in emails]
        Subscriber.objects.bulk_create(subscribers)

        # Verify all created
        self.assertEqual(Subscriber.objects.count(), 100)

        # Verify all unique
        distinct_emails = Subscriber.objects.values('email').distinct().count()
        self.assertEqual(distinct_emails, 100)

    def test_subscriber_confirmation_workflow(self):
        """System Test: Partial confirmation of subscribers"""
        # Create subscribers
        for i in range(3):
            Subscriber.objects.create(email=f'user{i}@example.com', confirmed=False)

        # Some confirm
        unconfirmed = Subscriber.objects.filter(confirmed=False).first()
        unconfirmed.confirmed = True
        unconfirmed.save()

        # Verify counts
        confirmed = Subscriber.objects.filter(confirmed=True)
        unconfirmed = Subscriber.objects.filter(confirmed=False)

        self.assertEqual(confirmed.count(), 1)
        self.assertEqual(unconfirmed.count(), 2)


class BreakingNewsWorkflowTests(TestCase):
    """Tests for breaking news feature workflows"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'
        self.category = Category.objects.create(name='News')

    def tearDown(self):
        self.ai_patcher.stop()

    def test_breaking_news_publication(self):
        """System Test: Breaking news article is marked and published"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='BREAKING: Major Event Occurred',
            author='Reporter',
            content='Details of major event...',
            featured_image='breaking.jpg',
            is_breaking=True,
            status='PUBLISHED'
        )

        # Verify breaking flag
        self.assertTrue(article.is_breaking)
        self.assertEqual(article.status, 'PUBLISHED')

        # Can filter breaking news
        breaking = NewsArticle.objects.filter(is_breaking=True)
        self.assertEqual(breaking.count(), 1)

    def test_breaking_news_mixed_with_regular(self):
        """System Test: Breaking news displayed separately from regular"""
        # Create regular articles
        regular = NewsArticle.objects.create(
            category=self.category,
            title='Regular News',
            author='Author',
            content='Regular content',
            featured_image='news.jpg',
            is_breaking=False,
            status='PUBLISHED'
        )

        # Create breaking news
        breaking = NewsArticle.objects.create(
            category=self.category,
            title='BREAKING: Major Event',
            author='Author',
            content='Important content',
            featured_image='breaking.jpg',
            is_breaking=True,
            status='PUBLISHED'
        )

        # Filter each type
        breaking_articles = NewsArticle.objects.filter(is_breaking=True)
        regular_articles = NewsArticle.objects.filter(is_breaking=False)

        self.assertEqual(breaking_articles.count(), 1)
        self.assertEqual(regular_articles.count(), 1)


class ArticleMetricsWorkflowTests(TestCase):
    """Tests for article metrics and viewing workflows"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'
        self.category = Category.objects.create(name='News')

    def tearDown(self):
        self.ai_patcher.stop()

    def test_article_views_tracking(self):
        """System Test: Track article view count"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Popular Article',
            author='Author',
            content='Content',
            featured_image='image.jpg',
            status='PUBLISHED'
        )

        # Initial views
        self.assertEqual(article.views, 0)

        # Simulate views
        for i in range(1, 11):
            article.views = i
            article.save()

        article.refresh_from_db()
        self.assertEqual(article.views, 10)

    def test_popular_articles_ranking(self):
        """System Test: Rank articles by views"""
        # Create articles with different view counts
        articles = []
        for i in range(5):
            article = NewsArticle.objects.create(
                category=self.category,
                title=f'Article {i}',
                author='Author',
                content='Content',
                featured_image='image.jpg',
                status='PUBLISHED',
                views=i * 100
            )
            articles.append(article)

        # Get most popular
        popular = NewsArticle.objects.order_by('-views')[:3]

        # Verify order
        views_list = [a.views for a in popular]
        self.assertEqual(views_list, [400, 300, 200])

    def test_article_engagement_workflow(self):
        """System Test: High engagement article"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Viral Article',
            author='Author',
            content='Highly engaging content',
            featured_image='viral.jpg',
            status='PUBLISHED',
            is_breaking=True
        )

        # Simulate viral behavior
        for _ in range(1000):
            article.views += 1

        article.save()

        article.refresh_from_db()
        self.assertEqual(article.views, 1000)


class ContentManagementWorkflowTests(TestCase):
    """Tests for content management workflows"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'

    def tearDown(self):
        self.ai_patcher.stop()

    def test_category_management_workflow(self):
        """System Test: Manage categories"""
        # Create categories
        categories = []
        for i, name in enumerate(['Technology', 'Science', 'Business']):
            cat = Category.objects.create(name=name)
            categories.append(cat)

        # Verify all created
        self.assertEqual(Category.objects.count(), 3)

        # Update category
        categories[0].description = 'Technology and Innovation'
        categories[0].save()

        # Verify update
        categories[0].refresh_from_db()
        self.assertEqual(categories[0].description, 'Technology and Innovation')

    def test_bulk_article_import_workflow(self):
        """System Test: Import multiple articles at once"""
        category = Category.objects.create(name='Imported')

        # Prepare bulk articles
        articles = [
            NewsArticle(
                category=category,
                title=f'Imported Article {i}',
                author='Bulk Import',
                content=f'Content for article {i}',
                featured_image='import.jpg'
            )
            for i in range(50)
        ]

        # Bulk create
        NewsArticle.objects.bulk_create(articles)

        # Verify import
        self.assertEqual(category.articles.count(), 50)

    def test_archive_old_articles_workflow(self):
        """System Test: Archive (mark as draft) old articles"""
        category = Category.objects.create(name='News')

        # Create articles
        for i in range(5):
            NewsArticle.objects.create(
                category=category,
                title=f'Article {i}',
                author='Author',
                content='Content',
                featured_image='news.jpg',
                status='PUBLISHED'
            )

        # Verify all published
        published = NewsArticle.objects.filter(status='PUBLISHED')
        self.assertEqual(published.count(), 5)

        # Archive first two
        to_archive = NewsArticle.objects.order_by('created_at')[:2]
        for article in to_archive:
            article.status = 'DRAFT'
            article.save()

        # Verify archive
        published = NewsArticle.objects.filter(status='PUBLISHED')
        archived = NewsArticle.objects.filter(status='DRAFT')

        self.assertEqual(published.count(), 3)
        self.assertEqual(archived.count(), 2)


class DataMigrationConsistencyTests(TestCase):
    """Tests to verify data consistency after migration to main app"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'

    def tearDown(self):
        self.ai_patcher.stop()

    def test_all_models_functional_after_migration(self):
        """System Test: All models work after migration to main app"""
        # Create all model types
        category = Category.objects.create(name='Test Category')
        article = NewsArticle.objects.create(
            category=category,
            title='Test Article',
            author='Test Author',
            content='Test content',
            featured_image='test.jpg'
        )
        subscriber = Subscriber.objects.create(email='test@example.com')

        # Verify all created
        self.assertIsNotNone(category.id)
        self.assertIsNotNone(article.id)
        self.assertIsNotNone(subscriber.id)

    def test_relationships_intact_after_migration(self):
        """System Test: Foreign key relationships work after migration"""
        category = Category.objects.create(name='Category')
        article = NewsArticle.objects.create(
            category=category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='image.jpg'
        )

        # Verify relationship
        self.assertEqual(article.category, category)
        self.assertIn(article, category.articles.all())

    def test_queries_work_after_migration(self):
        """System Test: Complex queries work after migration"""
        # Create test data
        tech = Category.objects.create(name='Technology')
        for i in range(10):
            NewsArticle.objects.create(
                category=tech,
                title=f'Tech Article {i}',
                author='Author',
                content='Content',
                featured_image='tech.jpg',
                status='PUBLISHED' if i % 2 == 0 else 'DRAFT'
            )

        # Complex query
        published_tech = NewsArticle.objects.filter(
            category=tech,
            status='PUBLISHED'
        ).order_by('-created_at')

        self.assertEqual(published_tech.count(), 5)
