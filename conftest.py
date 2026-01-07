"""
Pytest configuration and fixtures for Biashara Bridges testing.

This module provides shared fixtures and configuration for all tests.
"""

import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings
from faker import Faker
from types import SimpleNamespace
from django.db.models.signals import post_save

import accounts.models as accounts_models
from accounts.models import Category
from marketplace.models import BusinessProfile
from payments.models import Wallet
import audit.signals as audit_signals
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed

# Leave automatic profile creation enabled so tests that expect a
# `User.profile` created by signals will work. Audit logging signals
# are still disconnected below to avoid writing to audit tables during tests.
try:
    post_save.disconnect(audit_signals.log_user_changes, sender=User)
except Exception:
    pass
try:
    user_logged_in.disconnect(audit_signals.log_user_login)
except Exception:
    pass
try:
    user_logged_out.disconnect(audit_signals.log_user_logout)
except Exception:
    pass
try:
    user_login_failed.disconnect(audit_signals.log_failed_login)
except Exception:
    pass

# Disconnect other audit post_save receivers that log model changes
from django.apps import apps
try:
    Transaction = apps.get_model('payments', 'Transaction')
    post_save.disconnect(audit_signals.log_transaction_created, sender=Transaction)
except Exception:
    pass
try:
    UserSubscription = apps.get_model('payments', 'UserSubscription')
    post_save.disconnect(audit_signals.log_subscription_created, sender=UserSubscription)
except Exception:
    pass
try:
    BusinessProfile = apps.get_model('marketplace', 'BusinessProfile')
    post_save.disconnect(audit_signals.log_business_profile_changes, sender=BusinessProfile)
except Exception:
    pass
try:
    InvestmentOpportunity = apps.get_model('marketplace', 'InvestmentOpportunity')
    post_save.disconnect(audit_signals.log_investment_opportunity, sender=InvestmentOpportunity)
except Exception:
    pass
try:
    JobApplication = apps.get_model('marketplace', 'JobApplication')
    post_save.disconnect(audit_signals.log_job_application, sender=JobApplication)
except Exception:
    pass

# Initialize Faker
fake = Faker()


# Override static files storage for tests to avoid manifest issues
@pytest.fixture(autouse=True)
def override_staticfiles_storage(settings):
    """Use simple static files storage in tests to avoid manifest issues."""
    settings.STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'


# Do not override pytest-django's `django_db_setup` fixture here — leave
# migrations and test DB setup to pytest-django so test tables are created.


@pytest.fixture
def api_client():
    """Provide a Django test client."""
    return Client()


@pytest.fixture
def create_user(db):
    """Factory fixture for creating test users."""
    def make_user(
        username: str = None,
        email: str = None,
        password: str = "testpass123",
        **kwargs
    ) -> User:
        """
        Create and return a test user.

        Args:
            username: Username (auto-generated if not provided)
            email: Email (auto-generated if not provided)
            password: Password (default: testpass123)
            **kwargs: Additional fields for User model

        Returns:
            User: Created user instance
        """
        if not username:
            username = fake.user_name()
        if not email:
            email = fake.email()

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **kwargs
        )

        # Attach a lightweight in-memory `profile` to avoid creating a DB-backed
        # UserProfile during tests when migrations/schema may be incomplete.
        class FakeProfile(SimpleNamespace):
            def save(self, *a, **k):
                return None

        # Assign into the instance dict to bypass the OneToOne descriptor's
        # type-checking (which expects a real `UserProfile` instance).
        user.__dict__["profile"] = FakeProfile(user=user)
        return user

    return make_user


@pytest.fixture
def authenticated_user(db, api_client, create_user):
    """
    Provide an authenticated user and client.

    Returns:
        tuple: (user, client) where client is logged in as user
    """
    user = create_user()
    api_client.force_login(user)
    return user, api_client


@pytest.fixture
def investor_user(db, create_user):
    """Create a user with Investor category."""
    category, _ = Category.objects.get_or_create(
        name="Investor",
        defaults={"slug": "investor", "is_active": True}
    )
    user = create_user()
    # Populate the in-memory profile with the category without hitting the DB
    user.__dict__["profile"] = SimpleNamespace(user=user, category=category)
    return user


@pytest.fixture
def business_user(db, create_user):
    """Create a user with Business category."""
    category, _ = Category.objects.get_or_create(
        name="Business",
        defaults={"slug": "business", "is_active": True}
    )
    user = create_user()
    user.__dict__["profile"] = SimpleNamespace(user=user, category=category)
    return user


@pytest.fixture
def individual_user(db, create_user):
    """Create a user with Individual category."""
    category, _ = Category.objects.get_or_create(
        name="Individual",
        defaults={"slug": "individual", "is_active": True}
    )
    user = create_user()
    user.__dict__["profile"] = SimpleNamespace(user=user, category=category)
    return user


@pytest.fixture
def user_with_wallet(db, create_user):
    """Create a user with a wallet."""
    user = create_user()
    # Wallet should be auto-created by signal, but avoid failing tests when
    # the payments table is missing by guarding DB access.
    try:
        if not hasattr(user, 'wallet'):
            Wallet.objects.create(user=user)
    except Exception:
        pass
    return user


@pytest.fixture
def business_profile(db, business_user):
    """Create a business profile for testing."""
    profile, _ = BusinessProfile.objects.get_or_create(
        user=business_user,
        defaults={
            'company_name': fake.company(),
            'industry': 'Technology',
            'company_size': '10-50',
            'description': fake.text(),
            'funding_amount_seeking': 100000.00,
            'equity_offered': 10.0,
            'funding_stage': 'seed',
        }
    )
    return profile


@pytest.fixture
def sample_categories(db):
    """Create sample user categories."""
    categories = []
    for name in ['Investor', 'Business', 'Individual']:
        category, _ = Category.objects.get_or_create(
            name=name,
            defaults={'slug': name.lower(), 'is_active': True}
        )
        categories.append(category)
    return categories


# Marker for database access
pytestmark = pytest.mark.django_db
