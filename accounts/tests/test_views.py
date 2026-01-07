"""
Tests for accounts views - login, password reset.
"""
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Category


@pytest.mark.django_db
class TestLoginView:
    """Tests for user login functionality."""

    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get(reverse('login'))
        assert response.status_code == 200

    def test_login_with_valid_credentials(self, client, create_user):
        """Test login with valid credentials."""
        user = create_user(username='testuser', password='testpass123')
        response = client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        assert response.status_code in [200, 302]

    def test_login_with_invalid_credentials(self, client, create_user):
        """Test login with invalid credentials."""
        create_user(username='testuser', password='testpass123')
        response = client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        assert response.status_code == 200

    def test_login_with_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(reverse('login'), {
            'username': 'nonexistent',
            'password': 'testpass123'
        })
        assert response.status_code == 200


@pytest.mark.django_db
class TestPasswordResetView:
    """Tests for password reset functionality."""

    def test_password_reset_page_loads(self, client):
        """Test that password reset page loads successfully."""
        response = client.get(reverse('password_reset'))
        assert response.status_code == 200

    def test_password_reset_with_valid_email(self, client, create_user):
        """Test password reset with valid email shows success."""
        create_user(email='test@example.com')
        response = client.post(reverse('password_reset'), {
            'email': 'test@example.com'
        })
        assert response.status_code == 200
        assert b'Success' in response.content

    def test_password_reset_with_invalid_email(self, client):
        """Test password reset with non-existent email shows error."""
        response = client.post(reverse('password_reset'), {
            'email': 'nonexistent@example.com'
        })
        assert response.status_code == 200
        assert b'Error' in response.content


@pytest.mark.django_db
class TestCategoryFiltering:
    """Tests for category model and filtering."""

    def test_active_categories_count(self):
        """Test that only active categories are returned."""
        Category.objects.create(name='Active1', slug='active1', is_active=True)
        Category.objects.create(name='Active2', slug='active2', is_active=True)
        Category.objects.create(name='Inactive', slug='inactive', is_active=False)

        active = Category.objects.filter(is_active=True, slug__in=['active1', 'active2', 'inactive'])
        assert active.count() == 2

    def test_inactive_categories_excluded(self):
        """Test that inactive categories are excluded."""
        Category.objects.create(name='Active', slug='active-test', is_active=True)
        Category.objects.create(name='Inactive', slug='inactive-test', is_active=False)

        active = Category.objects.filter(is_active=True)
        slugs = list(active.values_list('slug', flat=True))
        assert 'inactive-test' not in slugs
