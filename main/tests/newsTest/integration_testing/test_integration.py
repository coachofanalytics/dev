"""
Integration Tests for News Models
Tests for interactions between models, signals, and data consistency
"""

from django.test import TestCase, TransactionTestCase
from django.db import transaction
from unittest.mock import patch
from main.models import Category, NewsArticle, Subscriber


class CategoryArticleIntegrationTests(TestCase):
    """Tests for interactions between Category and NewsArticle"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'AI Summary'

    def tearDown(self):
        self.ai_patcher.stop()

    def test_create_category_and_add_articles(self):
        """Test: Create category and add multiple articles to it"""
        # Create category
        category = Category.objects.create(
            name='Technology',
            description='Latest tech news'
        )
        
        # Create articles
        article1 = NewsArticle.objects.create(
            category=category,
            title='Article 1',
            author='Author 1',
            content='Content 1',
            featured_image='path.jpg'
        )
        article2 = NewsArticle.objects.create(
            category=category,
            title='Article 2',
            author='Author 2',
            content='Content 2',
            featured_image='path.jpg'
        )

        # Verify relationship
        self.assertEqual(category.articles.count(), 2)
        self.assertIn(article1, category.articles.all())
        self.assertIn(article2, category.articles.all())

    def test_category_update_doesnt_affect_articles(self):
        """Test: Updating category doesn't affect articles"""
        category = Category.objects.create(name='Tech')
        article = NewsArticle.objects.create(
            category=category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )

        # Update category
        category.name = 'Technology Updated'
        category.description = 'Updated description'
        category.save()

        # Article should still be attached
        article.refresh_from_db()
        self.assertEqual(article.category, category)

    def test_query_articles_by_category(self):
        """Test: Query articles filtered by category"""
        tech = Category.objects.create(name='Technology')
        science = Category.objects.create(name='Science')

        # Create articles
        for i in range(2):
            NewsArticle.objects.create(
                category=tech,
                title=f'Tech Article {i}',
                author='Author',
                content='Content',
                featured_image='path.jpg'
            )
            NewsArticle.objects.create(
                category=science,
                title=f'Science Article {i}',
                author='Author',
                content='Content',
                featured_image='path.jpg'
            )

        # Query by category
        tech_articles = NewsArticle.objects.filter(category=tech)
        science_articles = NewsArticle.objects.filter(category=science)

        self.assertEqual(tech_articles.count(), 2)
        self.assertEqual(science_articles.count(), 2)

    def test_change_article_category(self):
        """Test: Article can be moved to different category"""
        tech = Category.objects.create(name='Technology')
        science = Category.objects.create(name='Science')

        article = NewsArticle.objects.create(
            category=tech,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )

        # Move to science
        article.category = science
        article.save()

        # Verify move
        tech.refresh_from_db()
        science.refresh_from_db()
        self.assertEqual(tech.articles.count(), 0)
        self.assertEqual(science.articles.count(), 1)

    def test_cascade_delete_removes_articles(self):
        """Test: Deleting category cascades delete to articles"""
        category = Category.objects.create(name='To Delete')
        
        articles = []
        for i in range(3):
            article = NewsArticle.objects.create(
                category=category,
                title=f'Article {i}',
                author='Author',
                content='Content',
                featured_image='path.jpg'
            )
            articles.append(article.id)

        # Delete category
        category.delete()

        # Articles should be deleted
        for article_id in articles:
            self.assertFalse(NewsArticle.objects.filter(id=article_id).exists())

    def test_cascade_delete_only_affects_own_articles(self):
        """Test: Cascade delete only affects articles of that category"""
        tech = Category.objects.create(name='Technology')
        science = Category.objects.create(name='Science')

        tech_article = NewsArticle.objects.create(
            category=tech,
            title='Tech Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )
        science_article = NewsArticle.objects.create(
            category=science,
            title='Science Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )

        # Delete tech category
        tech.delete()

        # Only tech article should be deleted
        self.assertFalse(NewsArticle.objects.filter(id=tech_article.id).exists())
        self.assertTrue(NewsArticle.objects.filter(id=science_article.id).exists())


class SubscriberIntegrationTests(TestCase):
    """Tests for Subscriber model functionality"""

    def test_subscriber_creation_and_confirmation(self):
        """Test: Create subscriber and confirm"""
        # Create subscriber
        subscriber = Subscriber.objects.create(email='user@example.com')
        
        self.assertFalse(subscriber.confirmed)
        self.assertTrue(subscriber.is_active)
        self.assertIsNotNone(subscriber.conf_token)

        # Confirm subscription
        subscriber.confirmed = True
        subscriber.save()
        subscriber.refresh_from_db()

        self.assertTrue(subscriber.confirmed)

    def test_multiple_subscribers_unique_tokens(self):
        """Test: Multiple subscribers have unique tokens"""
        subscribers = []
        for i in range(10):
            sub = Subscriber.objects.create(email=f'user{i}@example.com')
            subscribers.append(sub)

        # All tokens must be unique
        tokens = [s.conf_token for s in subscribers]
        self.assertEqual(len(tokens), len(set(tokens)))

    def test_subscriber_by_token_lookup(self):
        """Test: Can find subscriber by confirmation token"""
        subscriber = Subscriber.objects.create(email='user@example.com')
        token = subscriber.conf_token

        found = Subscriber.objects.get(conf_token=token)
        self.assertEqual(found.email, subscriber.email)

    def test_subscriber_deactivation(self):
        """Test: Subscriber can be deactivated"""
        subscriber = Subscriber.objects.create(
            email='user@example.com',
            confirmed=True
        )

        subscriber.is_active = False
        subscriber.save()
        subscriber.refresh_from_db()

        self.assertFalse(subscriber.is_active)
        self.assertTrue(subscriber.confirmed)  # Unchanged

    def test_query_confirmed_subscribers(self):
        """Test: Query confirmed subscribers"""
        Subscriber.objects.create(email='confirmed1@example.com', confirmed=True)
        Subscriber.objects.create(email='unconfirmed@example.com', confirmed=False)
        Subscriber.objects.create(email='confirmed2@example.com', confirmed=True)

        confirmed = Subscriber.objects.filter(confirmed=True)
        self.assertEqual(confirmed.count(), 2)

    def test_query_active_subscribers(self):
        """Test: Query active subscribers"""
        Subscriber.objects.create(email='active1@example.com', is_active=True)
        Subscriber.objects.create(email='inactive@example.com', is_active=False)
        Subscriber.objects.create(email='active2@example.com', is_active=True)

        active = Subscriber.objects.filter(is_active=True)
        self.assertEqual(active.count(), 2)

    def test_query_confirmed_and_active_subscribers(self):
        """Test: Query subscribers that are both confirmed and active"""
        Subscriber.objects.create(
            email='ok@example.com',
            confirmed=True,
            is_active=True
        )
        Subscriber.objects.create(
            email='confirmed-inactive@example.com',
            confirmed=True,
            is_active=False
        )
        Subscriber.objects.create(
            email='unconfirmed-active@example.com',
            confirmed=False,
            is_active=True
        )

        eligible = Subscriber.objects.filter(confirmed=True, is_active=True)
        self.assertEqual(eligible.count(), 1)


class ArticleStatusTransitionTests(TestCase):
    """Tests for article status transitions"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'
        self.category = Category.objects.create(name='News')

    def tearDown(self):
        self.ai_patcher.stop()

    def test_article_draft_to_published_transition(self):
        """Test: Article can transition from DRAFT to PUBLISHED"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg',
            status='DRAFT'
        )

        self.assertEqual(article.status, 'DRAFT')

        article.status = 'PUBLISHED'
        article.save()
        article.refresh_from_db()

        self.assertEqual(article.status, 'PUBLISHED')

    def test_article_published_to_draft_transition(self):
        """Test: Article can transition from PUBLISHED back to DRAFT"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg',
            status='PUBLISHED'
        )

        article.status = 'DRAFT'
        article.save()
        article.refresh_from_db()

        self.assertEqual(article.status, 'DRAFT')

    def test_query_published_articles(self):
        """Test: Query only published articles"""
        NewsArticle.objects.create(
            category=self.category,
            title='Draft Article',
            author='Author',
            content='Content',
            featured_image='path.jpg',
            status='DRAFT'
        )
        NewsArticle.objects.create(
            category=self.category,
            title='Published Article 1',
            author='Author',
            content='Content',
            featured_image='path.jpg',
            status='PUBLISHED'
        )
        NewsArticle.objects.create(
            category=self.category,
            title='Published Article 2',
            author='Author',
            content='Content',
            featured_image='path.jpg',
            status='PUBLISHED'
        )

        published = NewsArticle.objects.filter(status='PUBLISHED')
        self.assertEqual(published.count(), 2)

    def test_breaking_news_visibility(self):
        """Test: Breaking news articles can be filtered"""
        regular = NewsArticle.objects.create(
            category=self.category,
            title='Regular Article',
            author='Author',
            content='Content',
            featured_image='path.jpg',
            is_breaking=False
        )
        breaking = NewsArticle.objects.create(
            category=self.category,
            title='Breaking News',
            author='Author',
            content='Content',
            featured_image='path.jpg',
            is_breaking=True
        )

        breaking_articles = NewsArticle.objects.filter(is_breaking=True)
        self.assertEqual(breaking_articles.count(), 1)
        self.assertIn(breaking, breaking_articles)
        self.assertNotIn(regular, breaking_articles)


class DataConsistencyTests(TestCase):
    """Tests for data integrity across models"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'

    def tearDown(self):
        self.ai_patcher.stop()

    def test_email_uniqueness_across_subscribers(self):
        """Test: Email uniqueness is enforced at database level"""
        Subscriber.objects.create(email='user@example.com')

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Subscriber.objects.create(email='user@example.com')

    def test_slug_uniqueness_across_articles(self):
        """Test: Slug uniqueness is enforced for articles"""
        category = Category.objects.create(name='News')
        
        NewsArticle.objects.create(
            category=category,
            title='Article One',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                NewsArticle.objects.create(
                    category=category,
                    title='Different',
                    author='Author',
                    content='Content',
                    featured_image='path.jpg',
                    slug='article-one'
                )

    def test_slug_uniqueness_across_categories(self):
        """Test: Category slug uniqueness is enforced"""
        Category.objects.create(name='Technology')

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(name='Different', slug='technology')

    def test_timestamp_ordering(self):
        """Test: Articles created in order have ordered timestamps"""
        category = Category.objects.create(name='News')
        
        articles = []
        for i in range(5):
            article = NewsArticle.objects.create(
                category=category,
                title=f'Article {i}',
                author='Author',
                content='Content',
                featured_image='path.jpg'
            )
            articles.append(article)

        # Query in order
        db_articles = list(NewsArticle.objects.order_by('created_at'))

        for i, db_article in enumerate(db_articles):
            self.assertEqual(db_article.id, articles[i].id)

    def test_no_orphaned_articles(self):
        """Test: No articles exist without a category"""
        category = Category.objects.create(name='Tech')
        NewsArticle.objects.create(
            category=category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )

        orphaned = NewsArticle.objects.filter(category__isnull=True)
        self.assertEqual(orphaned.count(), 0)

    def test_bulk_subscriber_creation_uniqueness(self):
        """Test: Bulk creation respects email uniqueness"""
        Subscriber.objects.create(email='existing@example.com')

        new_subscribers = [
            Subscriber(email=f'user{i}@example.com')
            for i in range(50)
        ]

        Subscriber.objects.bulk_create(new_subscribers)

        total = Subscriber.objects.count()
        self.assertEqual(total, 51)  # 1 existing + 50 new

    def test_article_updated_at_changes_on_save(self):
        """Test: updated_at changes when article is saved"""
        import time
        
        category = Category.objects.create(name='News')
        article = NewsArticle.objects.create(
            category=category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )

        original_updated = article.updated_at

        # Small delay
        time.sleep(0.01)

        article.title = 'Updated Title'
        article.save()
        article.refresh_from_db()

        self.assertGreater(article.updated_at, original_updated)
