from django.test import TestCase
from unittest.mock import patch
from django.db.utils import IntegrityError
from main.models import Category, NewsArticle, Subscriber

@patch('main.ai_services.generate_article_summary', return_value='Mocked summary')
@patch('main.signals.send_mail')
@patch('django.core.mail.send_mail')
class ModelTests(TestCase):
    def test_str_representations(self, mock_core_mail, mock_signal_mail, mock_ai_summary):
        cat = Category.objects.create(name='Tech')
        self.assertEqual(str(cat), 'Tech')
        article = NewsArticle.objects.create(category=cat, title='Apple Apple', content='Content')
        self.assertEqual(str(article), 'Apple Apple')
        sub = Subscriber.objects.create(email='test@example.com')
        self.assertEqual(str(sub), 'test@example.com')

    def test_slug_auto_generation(self, mock_core_mail, mock_signal_mail, mock_ai_summary):
        cat = Category.objects.create(name='Tech News')
        self.assertEqual(cat.slug, 'tech-news')
        article = NewsArticle.objects.create(category=cat, title='Apple Releases Phone', content='Content')
        self.assertEqual(article.slug, 'apple-releases-phone')

    def test_slug_not_regenerated_on_resave(self, mock_core_mail, mock_signal_mail, mock_ai_summary):
        cat = Category.objects.create(name='Tech')
        cat.name = 'New Tech'
        cat.save()
        self.assertEqual(cat.slug, 'tech')
        article = NewsArticle.objects.create(category=cat, title='Old Title', content='Content')
        article.title = 'New Title'
        article.save()
        self.assertEqual(article.slug, 'old-title')
    
    def test_default_status_draft(self, mock_core_mail, mock_signal_mail, mock_ai_summary):
        cat = Category.objects.create(name='Tech')
        article = NewsArticle.objects.create(category=cat, title='Test Default Status', content='Content')
        self.assertEqual(article.status, 'DRAFT')

    def test_confirmed_defaults_false(self, mock_core_mail, mock_signal_mail, mock_ai_summary):
        sub = Subscriber.objects.create(email='sub@example.com')
        self.assertFalse(sub.confirmed)

    def test_email_unique_constraint(self, mock_core_mail, mock_signal_mail, mock_ai_summary):
        Subscriber.objects.create(email='duplicate@example.com')
        with self.assertRaises(IntegrityError):
            Subscriber.objects.create(email='duplicate@example.com')

    def test_cascade_delete(self, mock_core_mail, mock_signal_mail, mock_ai_summary):
        cat = Category.objects.create(name='Tech')
        article = NewsArticle.objects.create(category=cat, title='Del Title', content='Content')
        self.assertEqual(NewsArticle.objects.count(), 1)
        cat.delete()
        self.assertEqual(NewsArticle.objects.count(), 0)
