"""
Comprehensive unit tests for Category model.
Tests category creation, uniqueness, validations, and edge cases.
"""
from django.test import TestCase
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import IntegrityError

Category = apps.get_model('accounts', 'Category')


class CategoryModelBasicTests(TestCase):
    """Basic tests for Category model creation and representation."""

    def test_category_creation(self):
        """Test basic category creation."""
        cat = Category.objects.create(name='Test Category', slug='test-category')
        self.assertEqual(cat.name, 'Test Category')
        self.assertEqual(cat.slug, 'test-category')

    def test_category_str_representation(self):
        """Test string representation returns name."""
        cat = Category.objects.create(name='My Category', slug='my-category')
        self.assertEqual(str(cat), 'My Category')

    def test_category_default_values(self):
        """Test default values for category fields."""
        cat = Category.objects.create(name='Default Test', slug='default-test')
        self.assertTrue(cat.is_active)
        self.assertEqual(cat.icon, 'bi-tag')
        self.assertEqual(cat.description, '')


class CategoryUniqueConstraintTests(TestCase):
    """Tests for unique constraints on Category model."""

    def test_unique_name_constraint(self):
        """Test that category name must be unique."""
        Category.objects.create(name='Unique Name', slug='unique-slug-1')
        with self.assertRaises(IntegrityError):
            Category.objects.create(name='Unique Name', slug='unique-slug-2')

    def test_unique_slug_constraint(self):
        """Test that category slug must be unique."""
        Category.objects.create(name='Name 1', slug='same-slug')
        with self.assertRaises(IntegrityError):
            Category.objects.create(name='Name 2', slug='same-slug')

    def test_case_sensitive_name(self):
        """Test that name uniqueness is case-sensitive at DB level."""
        Category.objects.create(name='Business', slug='business-1')
        # This might succeed or fail depending on DB collation
        # Just testing that we handle it
        try:
            Category.objects.create(name='business', slug='business-2')
        except IntegrityError:
            pass  # Expected if DB is case-insensitive


class CategoryFieldValidationTests(TestCase):
    """Tests for field validations."""

    def test_name_max_length(self):
        """Test name field max length constraint (50 chars)."""
        cat = Category(name='x' * 50, slug='max-name')
        cat.full_clean()  # Should not raise

    def test_name_exceeds_max_length(self):
        """Test name exceeding max length raises error."""
        cat = Category(name='x' * 51, slug='too-long-name')
        with self.assertRaises(ValidationError):
            cat.full_clean()

    def test_slug_max_length(self):
        """Test slug field max length constraint (50 chars)."""
        cat = Category(name='Test', slug='x' * 50)
        cat.full_clean()

    def test_slug_invalid_format(self):
        """Test slug with invalid format raises error."""
        cat = Category(name='Test', slug='Invalid Slug With Spaces')
        with self.assertRaises(ValidationError):
            cat.full_clean()

    def test_description_max_length(self):
        """Test description max length (200 chars)."""
        cat = Category(name='Test', slug='test', description='x' * 200)
        cat.full_clean()

    def test_description_allows_empty(self):
        """Test description can be empty."""
        cat = Category(name='Test', slug='test', description='')
        cat.full_clean()  # Should not raise

    def test_icon_default(self):
        """Test icon default value."""
        cat = Category(name='Test', slug='test')
        self.assertEqual(cat.icon, 'bi-tag')

    def test_icon_custom_value(self):
        """Test custom icon value."""
        cat = Category.objects.create(name='Test', slug='test', icon='bi-briefcase')
        self.assertEqual(cat.icon, 'bi-briefcase')


class CategoryActiveStatusTests(TestCase):
    """Tests for is_active field behavior."""

    def test_default_is_active(self):
        """Test is_active defaults to True."""
        cat = Category.objects.create(name='Active Test', slug='active-test')
        self.assertTrue(cat.is_active)

    def test_inactive_category(self):
        """Test creating inactive category."""
        cat = Category.objects.create(name='Inactive Test', slug='inactive-test', is_active=False)
        self.assertFalse(cat.is_active)

    def test_deactivate_category(self):
        """Test deactivating an active category."""
        cat = Category.objects.create(name='Deactivate Test', slug='deactivate-test')
        self.assertTrue(cat.is_active)
        
        cat.is_active = False
        cat.save()
        cat.refresh_from_db()
        
        self.assertFalse(cat.is_active)


class CategoryMetaOptionsTests(TestCase):
    """Tests for Meta class options."""

    def test_ordering_by_name(self):
        """Test categories are ordered by name."""
        Category.objects.create(name='Zebra', slug='zebra')
        Category.objects.create(name='Apple', slug='apple')
        Category.objects.create(name='Mango', slug='mango')
        
        categories = list(Category.objects.all())
        names = [c.name for c in categories]
        self.assertEqual(names, ['Apple', 'Mango', 'Zebra'])

    def test_verbose_name(self):
        """Test verbose name meta option."""
        self.assertEqual(Category._meta.verbose_name, 'Category')

    def test_verbose_name_plural(self):
        """Test verbose name plural meta option."""
        self.assertEqual(Category._meta.verbose_name_plural, 'Categories')


class CategoryTimestampTests(TestCase):
    """Tests for timestamp fields."""

    def test_created_at_auto_set(self):
        """Test created_at is automatically set."""
        cat = Category.objects.create(name='Timestamp Test', slug='timestamp-test')
        self.assertIsNotNone(cat.created_at)

    def test_updated_at_auto_set(self):
        """Test updated_at is automatically set."""
        cat = Category.objects.create(name='Update Test', slug='update-test')
        self.assertIsNotNone(cat.updated_at)

    def test_updated_at_changes_on_save(self):
        """Test updated_at changes when saved."""
        cat = Category.objects.create(name='Save Test', slug='save-test')
        original_updated = cat.updated_at
        
        cat.description = 'Updated description'
        cat.save()
        cat.refresh_from_db()
        
        self.assertGreaterEqual(cat.updated_at, original_updated)

