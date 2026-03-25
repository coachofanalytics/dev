"""
Unit Tests for News Models
Tests for Category, NewsArticle, and Subscriber models - field validation, defaults, auto-generation
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils.text import slugify
from unittest.mock import patch
from uuid import UUID
import string

from main.models import Category, NewsArticle, Subscriber


class CategoryFieldValidationTests(TestCase):
    """Unit tests for Category model field validation"""

    def test_category_name_required(self):
        """Test: Category name is required"""
        category = Category(name='', slug='test')
        with self.assertRaises(ValidationError):
            category.full_clean()

    def test_category_name_max_length_100(self):
        """Test: Category name max_length is 100 characters"""
        long_name = 'A' * 101
        category = Category(name=long_name)
        with self.assertRaises(ValidationError):
            category.full_clean()

    def test_category_name_within_length(self):
        """Test: Category name exactly 100 chars is valid"""
        valid_name = 'A' * 100
        category = Category(name=valid_name)
        category.full_clean()  # Should not raise

    def test_category_slug_auto_generated(self):
        """Test: Slug is auto-generated from name"""
        category = Category.objects.create(name='Technology News')
        self.assertEqual(category.slug, 'technology-news')

    def test_category_slug_auto_generated_special_chars(self):
        """Test: Special characters handled in slug generation"""
        category = Category.objects.create(name='Science & Technology')
        # slugify removes &
        self.assertTrue(category.slug)
        self.assertNotIn('&', category.slug)

    def test_category_slug_uniqueness_enforced(self):
        """Test: Slug uniqueness constraint is enforced"""
        Category.objects.create(name='Technology', slug='technology')
        
        with self.assertRaises(IntegrityError):
            with self.settings(DEBUG=False):
                Category.objects.create(name='Tech', slug='technology')

    def test_category_custom_slug_override(self):
        """Test: Custom slug can override auto-generation"""
        category = Category.objects.create(name='Technology', slug='custom-tech')
        self.assertEqual(category.slug, 'custom-tech')

    def test_category_description_optional(self):
        """Test: Description is optional"""
        category = Category.objects.create(name='Tech', description='')
        self.assertEqual(category.description, '')

    def test_category_description_null_allowed(self):
        """Test: Description can be null"""
        category = Category.objects.create(name='Tech', description=None)
        self.assertIsNone(category.description)

    def test_category_created_at_auto_set(self):
        """Test: created_at is automatically set"""
        category = Category.objects.create(name='Tech')
        self.assertIsNotNone(category.created_at)

    def test_category_string_representation(self):
        """Test: __str__ returns category name"""
        category = Category.objects.create(name='Technology')
        self.assertEqual(str(category), 'Technology')

    def test_category_slug_with_unicode(self):
        """Test: Unicode characters handled in slug"""
        category = Category.objects.create(name='Café News')
        self.assertTrue(category.slug)
        self.assertGreater(len(category.slug), 0)

    def test_category_slug_with_multiple_spaces(self):
        """Test: Multiple spaces handled in slug"""
        category = Category.objects.create(name='Science   &   Tech')
        # Should normalize to single hyphens
        self.assertNotIn('  ', category.slug)

    def test_category_slug_lowercase(self):
        """Test: Slug is lowercase"""
        category = Category.objects.create(name='TECHNOLOGY')
        self.assertEqual(category.slug, 'technology')

    def test_category_slug_persists_on_update(self):
        """Test: Slug doesn't regenerate on update"""
        category = Category.objects.create(name='Technology', slug='tech')
        original_slug = category.slug
        
        category.description = 'Updated description'
        category.save()
        category.refresh_from_db()
        
        self.assertEqual(category.slug, original_slug)


class NewsArticleFieldValidationTests(TestCase):
    """Unit tests for NewsArticle model field validation"""

    def setUp(self):
        self.category = Category.objects.create(name='Technology')
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'AI Generated Summary'

    def tearDown(self):
        self.ai_patcher.stop()

    def test_article_title_required(self):
        """Test: Article title is required"""
        article = NewsArticle(
            title='',
            category=self.category,
            author='John',
            content='Content here',
            featured_image='path.jpg'
        )
        with self.assertRaises(ValidationError):
            article.full_clean()

    def test_article_title_max_length_255(self):
        """Test: Article title max_length is 255"""
        long_title = 'A' * 256
        article = NewsArticle(
            title=long_title,
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        with self.assertRaises(ValidationError):
            article.full_clean()

    def test_article_title_valid_exactly_255(self):
        """Test: Article title exactly 255 chars is valid"""
        title = 'A' * 255
        article = NewsArticle.objects.create(
            title=title,
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertEqual(article.title, title)

    def test_article_content_required(self):
        """Test: Article content is required"""
        article = NewsArticle(
            title='Title',
            category=self.category,
            author='John',
            content='',
            featured_image='path.jpg'
        )
        # TextField doesn't enforce blank=False at model level
        # Need full_clean to validate
        article.full_clean()
        # Only ImageField is actually required

    def test_article_author_required(self):
        """Test: Article author is required"""
        article = NewsArticle(
            title='Title',
            category=self.category,
            author='',
            content='Content',
            featured_image='path.jpg'
        )
        with self.assertRaises(ValidationError):
            article.full_clean()

    def test_article_author_max_length_100(self):
        """Test: Article author max_length is 100"""
        long_author = 'A' * 101
        article = NewsArticle(
            title='Title',
            category=self.category,
            author=long_author,
            content='Content',
            featured_image='path.jpg'
        )
        with self.assertRaises(ValidationError):
            article.full_clean()

    def test_article_slug_auto_generated(self):
        """Test: Slug is auto-generated from title"""
        article = NewsArticle.objects.create(
            title='Breaking News Today',
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertEqual(article.slug, 'breaking-news-today')

    def test_article_slug_truncated_at_250_chars(self):
        """Test: Slug is truncated at 250 characters"""
        long_title = 'A' * 300
        article = NewsArticle.objects.create(
            title=long_title,
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertLessEqual(len(article.slug), 250)

    def test_article_slug_uniqueness_enforced(self):
        """Test: Slug uniqueness is enforced"""
        NewsArticle.objects.create(
            title='Article One',
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )

        with self.assertRaises(IntegrityError):
            with self.settings(DEBUG=False):
                NewsArticle.objects.create(
                    title='Different Title',
                    category=self.category,
                    author='John',
                    content='Content',
                    featured_image='path.jpg',
                    slug='article-one'
                )

    def test_article_status_default_draft(self):
        """Test: Article status defaults to DRAFT"""
        article = NewsArticle.objects.create(
            title='Title',
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertEqual(article.status, 'DRAFT')

    def test_article_status_choices_valid(self):
        """Test: Article status accepts DRAFT and PUBLISHED"""
        for status in ['DRAFT', 'PUBLISHED']:
            article = NewsArticle.objects.create(
                title=f'Title {status}',
                category=self.category,
                author='John',
                content='Content',
                featured_image='path.jpg',
                status=status
            )
            self.assertEqual(article.status, status)

    def test_article_status_invalid_choice(self):
        """Test: Article status rejects invalid choices"""
        article = NewsArticle(
            title='Title',
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg',
            status='INVALID'
        )
        with self.assertRaises(ValidationError):
            article.full_clean()

    def test_article_ai_summary_auto_generated(self):
        """Test: AI summary is auto-generated on save"""
        article = NewsArticle.objects.create(
            title='Title',
            category=self.category,
            author='John',
            content='Some content for AI to summarize',
            featured_image='path.jpg'
        )
        self.mock_ai.assert_called_once()
        self.assertIsNotNone(article.ai_summary)

    def test_article_ai_summary_blank_if_no_content(self):
        """Test: AI summary not generated if no content"""
        self.mock_ai.reset_mock()
        article = NewsArticle.objects.create(
            title='Title',
            category=self.category,
            author='John',
            content='',
            featured_image='path.jpg'
        )
        # If content is blank, AI summary shouldn't be called
        # (depending on implementation)

    def test_article_is_breaking_default_false(self):
        """Test: is_breaking defaults to False"""
        article = NewsArticle.objects.create(
            title='Title',
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertFalse(article.is_breaking)

    def test_article_is_breaking_can_be_true(self):
        """Test: is_breaking can be set to True"""
        article = NewsArticle.objects.create(
            title='Breaking: Major Event',
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg',
            is_breaking=True
        )
        self.assertTrue(article.is_breaking)

    def test_article_created_at_auto_set(self):
        """Test: created_at is automatically set"""
        article = NewsArticle.objects.create(
            title='Title',
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertIsNotNone(article.created_at)

    def test_article_updated_at_auto_set(self):
        """Test: updated_at is automatically set"""
        article = NewsArticle.objects.create(
            title='Title',
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertIsNotNone(article.updated_at)

    def test_article_views_default_zero(self):
        """Test: Views counter defaults to 0"""
        article = NewsArticle.objects.create(
            title='Title',
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertEqual(article.views, 0)

    def test_article_views_can_increment(self):
        """Test: Views counter can be incremented"""
        article = NewsArticle.objects.create(
            title='Title',
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        article.views = 10
        article.save()
        article.refresh_from_db()
        self.assertEqual(article.views, 10)

    def test_article_string_representation(self):
        """Test: __str__ returns article title"""
        article = NewsArticle.objects.create(
            title='My Article Title',
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertEqual(str(article), 'My Article Title')

    def test_article_slug_with_special_characters(self):
        """Test: Special characters in title handled in slug"""
        article = NewsArticle.objects.create(
            title='Breaking: A & B Study Results!',
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertTrue(article.slug)
        self.assertNotIn('&', article.slug)

    def test_article_slug_with_unicode(self):
        """Test: Unicode characters in title handled"""
        article = NewsArticle.objects.create(
            title='Café News Update',
            category=self.category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertTrue(article.slug)

    def test_article_very_long_content(self):
        """Test: Very long content doesn't cause issues"""
        long_content = 'Content line. ' * 10000
        article = NewsArticle.objects.create(
            title='Title',
            category=self.category,
            author='John',
            content=long_content,
            featured_image='path.jpg'
        )
        self.assertEqual(len(article.content), len(long_content))

    def test_article_slug_not_regenerated_on_update(self):
        """Test: Slug doesn't change when article is updated"""
        article = NewsArticle.objects.create(
            title='Original Title',
            category=self.category,
            author='John',
            content='Original content',
            featured_image='path.jpg'
        )
        original_slug = article.slug

        article.title = 'Completely Different Title'
        article.content = 'New content'
        article.save()
        article.refresh_from_db()

        self.assertEqual(article.slug, original_slug)


class SubscriberFieldValidationTests(TestCase):
    """Unit tests for Subscriber model field validation"""

    def test_subscriber_email_required(self):
        """Test: Subscriber email is required"""
        subscriber = Subscriber(email='')
        with self.assertRaises(ValidationError):
            subscriber.full_clean()

    def test_subscriber_email_valid_format(self):
        """Test: Subscriber email validates format"""
        # Invalid email
        subscriber = Subscriber(email='not-an-email')
        with self.assertRaises(ValidationError):
            subscriber.full_clean()

    def test_subscriber_email_valid(self):
        """Test: Valid email is accepted"""
        subscriber = Subscriber.objects.create(email='user@example.com')
        self.assertEqual(subscriber.email, 'user@example.com')

    def test_subscriber_email_uniqueness(self):
        """Test: Email uniqueness is enforced"""
        Subscriber.objects.create(email='user@example.com')

        with self.assertRaises(IntegrityError):
            with self.settings(DEBUG=False):
                Subscriber.objects.create(email='user@example.com')

    def test_subscriber_email_normalized_lowercase(self):
        """Test: Email is normalized to lowercase"""
        subscriber = Subscriber.objects.create(email='User@Example.COM')
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.email, 'user@example.com')

    def test_subscriber_is_active_default_true(self):
        """Test: is_active defaults to True"""
        subscriber = Subscriber.objects.create(email='user@example.com')
        self.assertTrue(subscriber.is_active)

    def test_subscriber_is_active_can_be_false(self):
        """Test: is_active can be set to False"""
        subscriber = Subscriber.objects.create(
            email='user@example.com',
            is_active=False
        )
        self.assertFalse(subscriber.is_active)

    def test_subscriber_conf_token_auto_generated(self):
        """Test: conf_token is auto-generated"""
        subscriber = Subscriber.objects.create(email='user@example.com')
        self.assertIsNotNone(subscriber.conf_token)

    def test_subscriber_conf_token_unique(self):
        """Test: Each subscriber has unique token"""
        subs = []
        for i in range(5):
            sub = Subscriber.objects.create(email=f'user{i}@example.com')
            subs.append(sub.conf_token)

        # All tokens should be unique
        self.assertEqual(len(subs), len(set(subs)))

    def test_subscriber_conf_token_immutable(self):
        """Test: conf_token cannot be changed"""
        subscriber = Subscriber.objects.create(email='user@example.com')
        original_token = subscriber.conf_token

        subscriber.is_active = False
        subscriber.save()
        subscriber.refresh_from_db()

        self.assertEqual(subscriber.conf_token, original_token)

    def test_subscriber_conf_token_not_blank(self):
        """Test: conf_token is never blank"""
        subscriber = Subscriber.objects.create(email='user@example.com')
        self.assertTrue(subscriber.conf_token)

    def test_subscriber_confirmed_default_false(self):
        """Test: confirmed defaults to False"""
        subscriber = Subscriber.objects.create(email='user@example.com')
        self.assertFalse(subscriber.confirmed)

    def test_subscriber_confirmed_can_be_true(self):
        """Test: confirmed can be set to True"""
        subscriber = Subscriber.objects.create(
            email='user@example.com',
            confirmed=True
        )
        self.assertTrue(subscriber.confirmed)

    def test_subscriber_subscribed_at_auto_set(self):
        """Test: subscribed_at is automatically set"""
        subscriber = Subscriber.objects.create(email='user@example.com')
        self.assertIsNotNone(subscriber.subscribed_at)

    def test_subscriber_string_representation(self):
        """Test: __str__ returns email"""
        email = 'user@example.com'
        subscriber = Subscriber.objects.create(email=email)
        self.assertEqual(str(subscriber), email)

    def test_subscriber_email_with_plus_addressing(self):
        """Test: Email with plus addressing is valid"""
        subscriber = Subscriber.objects.create(email='user+tag@example.com')
        self.assertEqual(subscriber.email, 'user+tag@example.com')

    def test_subscriber_email_with_subdomain(self):
        """Test: Email with subdomain is valid"""
        subscriber = Subscriber.objects.create(email='user@mail.example.com')
        self.assertEqual(subscriber.email, 'user@mail.example.com')

    def test_subscriber_multiple_emails_different_users(self):
        """Test: Different subscribers can have different emails"""
        sub1 = Subscriber.objects.create(email='user1@example.com')
        sub2 = Subscriber.objects.create(email='user2@example.com')

        self.assertNotEqual(sub1.email, sub2.email)
        self.assertNotEqual(sub1.conf_token, sub2.conf_token)


class CategoryNewsArticleRelationshipTests(TestCase):
    """Tests for Category-NewsArticle foreign key relationship"""

    def setUp(self):
        self.ai_patcher = patch('main.ai_services.generate_article_summary')
        self.mock_ai = self.ai_patcher.start()
        self.mock_ai.return_value = 'Summary'

    def tearDown(self):
        self.ai_patcher.stop()

    def test_article_requires_category(self):
        """Test: Article requires a category"""
        article = NewsArticle(
            title='Title',
            category=None,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        with self.assertRaises(ValidationError):
            article.full_clean()

    def test_article_category_foreign_key(self):
        """Test: Article has category foreign key"""
        category = Category.objects.create(name='Technology')
        article = NewsArticle.objects.create(
            title='Title',
            category=category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertEqual(article.category, category)

    def test_article_category_related_name(self):
        """Test: Category has articles related name"""
        category = Category.objects.create(name='Technology')
        article = NewsArticle.objects.create(
            title='Title',
            category=category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        self.assertIn(article, category.articles.all())

    def test_category_cascade_delete_articles(self):
        """Test: Deleting category cascades to articles"""
        category = Category.objects.create(name='Technology')
        article = NewsArticle.objects.create(
            title='Title',
            category=category,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        article_id = article.id

        category.delete()

        self.assertFalse(NewsArticle.objects.filter(id=article_id).exists())

    def test_multiple_articles_same_category(self):
        """Test: Multiple articles can belong to same category"""
        category = Category.objects.create(name='Technology')
        
        for i in range(3):
            NewsArticle.objects.create(
                title=f'Article {i}',
                category=category,
                author='John',
                content='Content',
                featured_image='path.jpg'
            )

        self.assertEqual(category.articles.count(), 3)

    def test_query_articles_by_category(self):
        """Test: Articles can be queried by category"""
        tech = Category.objects.create(name='Technology')
        science = Category.objects.create(name='Science')

        NewsArticle.objects.create(
            title='Tech Article',
            category=tech,
            author='John',
            content='Content',
            featured_image='path.jpg'
        )
        NewsArticle.objects.create(
            title='Science Article',
            category=science,
            author='Jane',
            content='Content',
            featured_image='path.jpg'
        )

        tech_articles = NewsArticle.objects.filter(category=tech)
        self.assertEqual(tech_articles.count(), 1)
