from django.test import TestCase
from django.db import IntegrityError
from news.models import Category, NewsArticle, Subscriber
from unittest.mock import patch


class RegressionTest(TestCase):
    """Regression tests for edge cases and specific bug scenarios"""

    def setUp(self):
        self.category = Category.objects.create(name="General")

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_article_slug_remains_unchanged_on_update(self, mock_summary):
        """Regression: Verify slug does not change when article is updated"""
        article = NewsArticle.objects.create(
            category=self.category,
            title="Original Title",
            author="Author",
            featured_image="img.jpg",
            content="Content",
            slug="original-title"
        )
        original_slug = article.slug
        
        # Update the article
        article.author = "Updated Author"
        article.save()
        
        # Slug should not change
        self.assertEqual(article.slug, original_slug)
        self.assertEqual(article.slug, "original-title")

    def test_duplicate_subscriber_email_raises_integrity_error(self):
        """Regression: Duplicate email should raise IntegrityError"""
        Subscriber.objects.create(email="duplicate@example.com")
        
        with self.assertRaises(IntegrityError):
            Subscriber.objects.create(email="duplicate@example.com")

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_published_filter_excludes_drafts(self, mock_summary):
        """Regression: Published filter should exclude drafts"""
        article1 = NewsArticle.objects.create(
            category=self.category,
            title="Published Article",
            author="Author",
            featured_image="img.jpg",
            content="Content",
            status="PUBLISHED"
        )
        
        article2 = NewsArticle.objects.create(
            category=self.category,
            title="Draft Article",
            author="Author",
            featured_image="img.jpg",
            content="Content",
            status="DRAFT"
        )
        
        published = NewsArticle.objects.filter(status='PUBLISHED')
        self.assertEqual(published.count(), 1)
        self.assertEqual(published.first().title, "Published Article")

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_breaking_news_filter_works(self, mock_summary):
        """Regression: Breaking news flag should filter correctly"""
        breaking = NewsArticle.objects.create(
            category=self.category,
            title="Breaking News",
            author="Author",
            featured_image="img.jpg",
            content="Important",
            is_breaking=True
        )
        
        regular = NewsArticle.objects.create(
            category=self.category,
            title="Regular News",
            author="Author",
            featured_image="img.jpg",
            content="Regular",
            is_breaking=False
        )
        
        breaking_articles = NewsArticle.objects.filter(is_breaking=True)
        self.assertEqual(breaking_articles.count(), 1)
        self.assertEqual(breaking_articles.first().title, "Breaking News")

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_pagination_returns_correct_count(self, mock_summary):
        """Regression: Pagination should return correct article counts"""
        # Create 15 articles (paginate_by = 7)
        for i in range(15):
            NewsArticle.objects.create(
                category=self.category,
                title=f"Article {i+1}",
                author="Author",
                featured_image="img.jpg",
                content="Content",
                status="PUBLISHED"
            )
        
        # First page should have 7 items
        page1 = NewsArticle.objects.filter(status='PUBLISHED').order_by('created_at')[:7]
        self.assertEqual(len(page1), 7)
        
        # Second page should have 7 items
        page2 = NewsArticle.objects.filter(status='PUBLISHED').order_by('created_at')[7:14]
        self.assertEqual(len(page2), 7)
        
        # Third page should have 1 item
        page3 = NewsArticle.objects.filter(status='PUBLISHED').order_by('created_at')[14:21]
        self.assertEqual(len(page3), 1)

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_article_update_preserves_created_at(self, mock_summary):
        """Regression: Article created_at should not change on update"""
        article = NewsArticle.objects.create(
            category=self.category,
            title="Original",
            author="Author",
            featured_image="img.jpg",
            content="Content"
        )
        original_created_at = article.created_at
        
        article.title = "Updated"
        article.save()
        
        self.assertEqual(article.created_at, original_created_at)

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_article_update_modifies_updated_at(self, mock_summary):
        """Regression: Article updated_at should change on update"""
        article = NewsArticle.objects.create(
            category=self.category,
            title="Original",
            author="Author",
            featured_image="img.jpg",
            content="Content"
        )
        original_updated_at = article.updated_at
        
        # Force a slight time difference
        import time
        time.sleep(0.1)
        
        article.title = "Updated"
        article.save()
        
        # updated_at should be different (newer)
        self.assertGreater(article.updated_at, original_updated_at)

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_multiple_articles_same_category_relationship(self, mock_summary):
        """Regression: Multiple articles can belong to same category"""
        cat = Category.objects.create(name="Tech")
        
        for i in range(5):
            NewsArticle.objects.create(
                category=cat,
                title=f"Tech Article {i+1}",
                author="Author",
                featured_image="img.jpg",
                content="Tech content"
            )
        
        # Should have 5 articles in category
        self.assertEqual(cat.articles.count(), 5)

    def test_subscriber_confirmed_status_can_be_toggled(self):
        """Regression: Subscriber confirmed status should be updatable"""
        subscriber = Subscriber.objects.create(email="test@example.com", confirmed=False)
        self.assertFalse(subscriber.confirmed)
        
        subscriber.confirmed = True
        subscriber.save()
        subscriber.refresh_from_db()
        
        self.assertTrue(subscriber.confirmed)

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_article_views_counter_increments(self, mock_summary):
        """Regression: Article views counter should increment"""
        article = NewsArticle.objects.create(
            category=self.category,
            title="Article",
            author="Author",
            featured_image="img.jpg",
            content="Content"
        )
        
        self.assertEqual(article.views, 0)
        
        article.views += 1
        article.save()
        
        article.refresh_from_db()
        self.assertEqual(article.views, 1)

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_category_slug_persists_on_article_operations(self, mock_summary):
        """Regression: Category slug should not change when articles are added"""
        cat = Category.objects.create(name="Important")
        original_slug = cat.slug
        
        for i in range(3):
            NewsArticle.objects.create(
                category=cat,
                title=f"Article {i+1}",
                author="Author",
                featured_image="img.jpg",
                content="Content"
            )
        
        cat.refresh_from_db()
        self.assertEqual(cat.slug, original_slug)

    @patch('news.models.generate_article_summary', return_value='Summary')
    def test_draft_articles_do_not_appear_in_public_list(self, mock_summary):
        """Regression: Draft articles should not be in public listing"""
        # Create mix of published and draft
        for i in range(3):
            NewsArticle.objects.create(
                category=self.category,
                title=f"Published {i+1}",
                author="Author",
                featured_image="img.jpg",
                content="Content",
                status="PUBLISHED"
            )
            
            NewsArticle.objects.create(
                category=self.category,
                title=f"Draft {i+1}",
                author="Author",
                featured_image="img.jpg",
                content="Content",
                status="DRAFT"
            )
        
        published_count = NewsArticle.objects.filter(status='PUBLISHED').count()
        self.assertEqual(published_count, 3)
