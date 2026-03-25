"""
Regression Tests for News Models
Ensures previously working functionality continues to work after migration to main app
"""

from django.test import TestCase
from django.db import transaction, IntegrityError
from unittest.mock import patch
from main.models import Category, NewsArticle, Subscriber


class CategorySlugRegressionTests(TestCase):
    """Regression tests: Ensure Category slug behavior unchanged"""

    def test_slug_auto_generation_still_works(self):
        """Regression: Slug auto-generation hasn't broken"""
        category = Category.objects.create(name='Technology News')
        self.assertEqual(category.slug, 'technology-news')

    def test_slug_with_special_characters_unchanged(self):
        """Regression: Special character handling in slugs"""
        category = Category.objects.create(name='R&D Department')
        self.assertTrue(category.slug)
        self.assertNotIn('&', category.slug)

    def test_custom_slug_override_still_works(self):
        """Regression: Can still override slug with custom value"""
        category = Category.objects.create(name='Technology', slug='custom-slug')
        self.assertEqual(category.slug, 'custom-slug')

    def test_slug_uniqueness_still_enforced(self):
        """Regression: Slug uniqueness constraint still enforced"""
        Category.objects.create(name='Technology')

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(name='Different', slug='technology')

    def test_slug_whitespace_handling_unchanged(self):
        """Regression: Whitespace in names handled same way"""
        category = Category.objects.create(name='Multiple   Spaces')
        # Should normalize spaces
        self.assertNotIn('  ', category.slug)

    def test_slug_lowercase_unchanged(self):
        """Regression: Slug is lowercase"""
        category = Category.objects.create(name='TECHNOLOGY')
        self.assertEqual(category.slug, 'technology')

    def test_slug_persists_on_update(self):
        """Regression: Slug doesn't regenerate on update"""
        category = Category.objects.create(name='Technology', slug='tech')
        original_slug = category.slug

        category.description = 'Updated description'
        category.save()
        category.refresh_from_db()

        self.assertEqual(category.slug, original_slug)


class NewsArticleSlugRegressionTests(TestCase):
    """Regression tests: Ensure Article slug behavior unchanged"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'
        self.category = Category.objects.create(name='News')

    def tearDown(self):
        self.ai_patcher.stop()

    def test_article_slug_auto_generation_unchanged(self):
        """Regression: Article slug auto-generation hasn't broken"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Breaking News Today',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertEqual(article.slug, 'breaking-news-today')

    def test_article_slug_truncation_at_250_unchanged(self):
        """Regression: Long slugs still truncated at 250 chars"""
        long_title = 'A' * 300
        article = NewsArticle.objects.create(
            category=self.category,
            title=long_title,
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertLessEqual(len(article.slug), 250)

    def test_article_slug_uniqueness_still_enforced(self):
        """Regression: Article slug uniqueness still enforced"""
        NewsArticle.objects.create(
            category=self.category,
            title='Article Title',
            author='Author',
            content='Content 1',
            featured_image='path.jpg'
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                NewsArticle.objects.create(
                    category=self.category,
                    title='Different',
                    author='Author',
                    content='Content 2',
                    featured_image='path.jpg',
                    slug='article-title'
                )

    def test_article_slug_not_regenerated_on_update(self):
        """Regression: Slug doesn't change on update"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Original Title',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )
        original_slug = article.slug

        article.title = 'Completely Different Title'
        article.content = 'New content'
        article.save()
        article.refresh_from_db()

        self.assertEqual(article.slug, original_slug)


class AIGenerationRegressionTests(TestCase):
    """Regression tests: Ensure AI summary behavior unchanged"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Generated AI Summary'
        self.category = Category.objects.create(name='News')

    def tearDown(self):
        self.ai_patcher.stop()

    def test_ai_summary_still_generated_on_create(self):
        """Regression: AI summary is generated on create"""
        self.mock_ai.reset_mock()
        
        article = NewsArticle.objects.create(
            category=self.category,
            title='Article',
            author='Author',
            content='Real content here',
            featured_image='path.jpg'
        )

        self.mock_ai.assert_called()
        self.assertIsNotNone(article.ai_summary)

    def test_ai_summary_not_regenerated_on_update(self):
        """Regression: AI summary NOT regenerated on update"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Article',
            author='Author',
            content='Original content',
            featured_image='path.jpg'
        )
        original_summary = article.ai_summary
        call_count = self.mock_ai.call_count

        # Update article
        article.content = 'Updated content completely different'
        article.save()
        article.refresh_from_db()

        # AI should NOT have been called again
        self.assertEqual(self.mock_ai.call_count, call_count)
        self.assertEqual(article.ai_summary, original_summary)


class TimestampRegressionTests(TestCase):
    """Regression tests: Ensure timestamp behavior unchanged"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'
        self.category = Category.objects.create(name='News')

    def tearDown(self):
        self.ai_patcher.stop()

    def test_article_created_at_immutable_after_creation(self):
        """Regression: created_at doesn't change after update"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )
        original_created_at = article.created_at

        # Update multiple times
        for i in range(5):
            article.title = f'Title {i}'
            article.save()

        article.refresh_from_db()
        self.assertEqual(article.created_at, original_created_at)

    def test_article_updated_at_changes_on_save(self):
        """Regression: updated_at is updated on save"""
        import time
        
        article = NewsArticle.objects.create(
            category=self.category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )
        original_updated_at = article.updated_at

        # Small delay
        time.sleep(0.01)

        article.title = 'Updated Title'
        article.save()
        article.refresh_from_db()

        self.assertGreater(article.updated_at, original_updated_at)

    def test_category_created_at_immutable(self):
        """Regression: Category created_at doesn't change"""
        category = Category.objects.create(name='Technology')
        original_created_at = category.created_at

        # Update category
        category.name = 'Technology Updated'
        category.description = 'New description'
        category.save()

        category.refresh_from_db()
        self.assertEqual(category.created_at, original_created_at)

    def test_subscriber_subscribed_at_immutable(self):
        """Regression: Subscriber subscribed_at is immutable"""
        import time
        
        subscriber = Subscriber.objects.create(email='user@example.com')
        original_subscribed_at = subscriber.subscribed_at

        time.sleep(0.01)

        subscriber.is_active = False
        subscriber.confirmed = True
        subscriber.save()

        subscriber.refresh_from_db()
        self.assertEqual(subscriber.subscribed_at, original_subscribed_at)


class CascadeDeleteRegressionTests(TestCase):
    """Regression tests: Ensure cascade delete behavior unchanged"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'

    def tearDown(self):
        self.ai_patcher.stop()

    def test_category_delete_cascades_to_articles(self):
        """Regression: Category deletion still cascades to articles"""
        category = Category.objects.create(name='Tech')
        
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

        category.delete()

        # Articles should be deleted
        for article_id in articles:
            self.assertFalse(NewsArticle.objects.filter(id=article_id).exists())

    def test_category_delete_only_affects_own_articles(self):
        """Regression: Category deletion only affects its own articles"""
        category1 = Category.objects.create(name='Tech')
        category2 = Category.objects.create(name='Science')

        article1 = NewsArticle.objects.create(
            category=category1,
            title='Tech Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )
        article2 = NewsArticle.objects.create(
            category=category2,
            title='Science Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )

        category1.delete()

        self.assertFalse(NewsArticle.objects.filter(id=article1.id).exists())
        self.assertTrue(NewsArticle.objects.filter(id=article2.id).exists())


class EmailFieldRegressionTests(TestCase):
    """Regression tests: Ensure email handling unchanged"""

    def test_email_normalization_still_works(self):
        """Regression: Email addresses normalized to lowercase"""
        subscriber = Subscriber.objects.create(email='User@Example.COM')
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.email, 'user@example.com')

    def test_email_normalization_prevents_duplicates(self):
        """Regression: Email normalization works with uniqueness"""
        Subscriber.objects.create(email='user@example.com')

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Subscriber.objects.create(email='USER@EXAMPLE.COM')

    def test_email_whitespace_handling(self):
        """Regression: Whitespace around email handled"""
        subscriber = Subscriber.objects.create(email='  user@example.com  ')
        subscriber.refresh_from_db()
        # EmailField strips whitespace
        self.assertEqual(subscriber.email.strip(), subscriber.email)


class SubscriberTokenRegressionTests(TestCase):
    """Regression tests: Ensure subscriber token behavior unchanged"""

    def test_conf_token_immutable_after_creation(self):
        """Regression: conf_token doesn't change after creation"""
        subscriber = Subscriber.objects.create(email='user@example.com')
        original_token = subscriber.conf_token

        subscriber.is_active = False
        subscriber.confirmed = True
        subscriber.save()

        subscriber.refresh_from_db()
        self.assertEqual(subscriber.conf_token, original_token)

    def test_conf_token_unique_across_subscribers(self):
        """Regression: All tokens are unique"""
        subscribers = []
        for i in range(20):
            sub = Subscriber.objects.create(email=f'user{i}@example.com')
            subscribers.append(sub)

        tokens = [s.conf_token for s in subscribers]
        self.assertEqual(len(tokens), len(set(tokens)))

    def test_conf_token_not_blank(self):
        """Regression: Token is never blank"""
        subscriber = Subscriber.objects.create(email='user@example.com')
        self.assertTrue(subscriber.conf_token)
        self.assertGreater(len(str(subscriber.conf_token)), 0)


class StatusFieldRegressionTests(TestCase):
    """Regression tests: Ensure status field behavior unchanged"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'
        self.category = Category.objects.create(name='News')

    def tearDown(self):
        self.ai_patcher.stop()

    def test_status_defaults_to_draft(self):
        """Regression: Status still defaults to DRAFT"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertEqual(article.status, 'DRAFT')

    def test_status_can_be_published(self):
        """Regression: Status can be changed to PUBLISHED"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )
        article.status = 'PUBLISHED'
        article.save()
        article.refresh_from_db()
        self.assertEqual(article.status, 'PUBLISHED')

    def test_status_rejects_invalid_choices(self):
        """Regression: Invalid status values are rejected"""
        article = NewsArticle(
            category=self.category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg',
            status='INVALID'
        )
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            article.full_clean()


class ViewsCounterRegressionTests(TestCase):
    """Regression tests: Ensure views counter behavior unchanged"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'
        self.category = Category.objects.create(name='News')

    def tearDown(self):
        self.ai_patcher.stop()

    def test_views_defaults_to_zero(self):
        """Regression: Article views starts at 0"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertEqual(article.views, 0)

    def test_views_can_be_incremented(self):
        """Regression: Views can be incremented"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )
        article.views = 10
        article.save()
        article.refresh_from_db()
        self.assertEqual(article.views, 10)

    def test_views_bulk_update(self):
        """Regression: bulk_update for views works"""
        articles = []
        for i in range(5):
            article = NewsArticle.objects.create(
                category=self.category,
                title=f'Article {i}',
                author='Author',
                content='Content',
                featured_image='path.jpg'
            )
            article.views = i * 10
            articles.append(article)

        NewsArticle.objects.bulk_update(articles, ['views'])

        for i, article in enumerate(articles):
            article.refresh_from_db()
            self.assertEqual(article.views, i * 10)


class BreakingNewsRegressionTests(TestCase):
    """Regression tests: Ensure breaking news field behavior unchanged"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'
        self.category = Category.objects.create(name='News')

    def tearDown(self):
        self.ai_patcher.stop()

    def test_is_breaking_defaults_to_false(self):
        """Regression: is_breaking defaults to False"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertFalse(article.is_breaking)

    def test_is_breaking_can_be_true(self):
        """Regression: is_breaking can be set to True"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Breaking News',
            author='Author',
            content='Content',
            featured_image='path.jpg',
            is_breaking=True
        )
        self.assertTrue(article.is_breaking)

    def test_is_breaking_toggle(self):
        """Regression: is_breaking can be toggled"""
        article = NewsArticle.objects.create(
            category=self.category,
            title='Article',
            author='Author',
            content='Content',
            featured_image='path.jpg',
            is_breaking=False
        )

        article.is_breaking = True
        article.save()
        article.refresh_from_db()

        self.assertTrue(article.is_breaking)
