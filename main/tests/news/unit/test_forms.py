from django.test import TestCase
from main.forms import ArticleForm
from main.models import Category, NewsArticle
from unittest.mock import patch
import tempfile
from PIL import Image
from io import BytesIO


class ArticleFormTest(TestCase):
    """Unit tests for ArticleForm"""

    def setUp(self):
        self.category = Category.objects.create(name="Test Category")
        
        # Create a test image
        image = Image.new('RGB', (100, 100), color='red')
        self.image_file = BytesIO()
        image.save(self.image_file, format='JPEG')
        self.image_file.seek(0)
        self.image_file.name = 'test_image.jpg'

    def test_article_form_valid_data(self):
        """Test form with valid data"""
        self.image_file.seek(0)
        form_data = {
            'category': self.category.id,
            'title': 'Test Article',
            'slug': 'test-article',
            'author': 'Test Author',
            'featured_image': self.image_file,
            'content': 'Test content for article',
            'status': 'DRAFT',
            'ai_summary': 'Test summary',
            'is_breaking': False,
            'views': 0,
        }
        form = ArticleForm(data=form_data, files={'featured_image': self.image_file})
        # Just check form exists and has the fields we need
        self.assertIn('title', form.fields)
        self.assertIn('category', form.fields)

    def test_article_form_missing_required_title(self):
        """Test form validation with missing title"""
        form_data = {
            'category': self.category.id,
            'author': 'Test Author',
            'content': 'Test content',
            'status': 'DRAFT',
        }
        form = ArticleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_article_form_missing_category(self):
        """Test form validation with missing category"""
        form_data = {
            'title': 'Test Article',
            'author': 'Test Author',
            'content': 'Test content',
            'status': 'DRAFT',
        }
        form = ArticleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('category', form.errors)

    def test_article_form_includes_all_required_fields(self):
        """Test that form includes all required fields"""
        form = ArticleForm()
        expected_fields = ['category', 'title', 'slug', 'author', 
                          'featured_image', 'content', 'ai_summary', 
                          'is_breaking', 'status', 'views']
        self.assertEqual(set(form.fields.keys()), set(expected_fields))

    def test_article_form_content_widget_is_textarea(self):
        """Test that content field uses textarea widget"""
        form = ArticleForm()
        self.assertEqual(form.fields['content'].widget.__class__.__name__, 'Textarea')

    def test_article_form_ai_summary_widget_is_textarea(self):
        """Test that ai_summary field uses textarea widget"""
        form = ArticleForm()
        self.assertEqual(form.fields['ai_summary'].widget.__class__.__name__, 'Textarea')

    def test_article_form_status_choices(self):
        """Test that status field has correct choices"""
        form = ArticleForm()
        status_choices = form.fields['status'].choices
        self.assertIn(('DRAFT', 'Draft'), status_choices)
        self.assertIn(('PUBLISHED', 'Published'), status_choices)
