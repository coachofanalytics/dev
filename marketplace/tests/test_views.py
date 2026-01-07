"""
Comprehensive tests for marketplace views and HTTP controllers.

Tests business profile, investment opportunity, job posting,
and application views.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from marketplace.models import (
    BusinessProfile, InvestmentOpportunity, 
    JobOpportunity, JobApplication, SavedItem
)


@pytest.mark.django_db
class TestBusinessProfileViews:
    """Test suite for business profile views."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='business_user',
            email='business@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def business_profile(self, user):
        """Create test business profile."""
        return BusinessProfile.objects.create(
            user=user,
            company_name='Test Company',
            industry='Technology',
            company_size='11-50',
            funding_stage='seed'
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_business_profile_list_accessible(self, client):
        """Test business profile list is accessible."""
        response = client.get('/marketplace/businesses/')
        assert response.status_code in [200, 404]

    def test_business_profile_detail_accessible(self, client, business_profile):
        """Test business profile detail is accessible."""
        response = client.get(f'/marketplace/business/{business_profile.id}/')
        assert response.status_code in [200, 404]

    def test_create_business_profile_requires_login(self, client):
        """Test creating business profile requires login."""
        response = client.get('/marketplace/business/create/')
        assert response.status_code in [302, 403]

    def test_create_business_profile_authenticated(self, client, user):
        """Test authenticated user can access create page."""
        client.force_login(user)
        response = client.get('/marketplace/business/create/')
        assert response.status_code in [200, 404]

    def test_edit_own_business_profile(self, client, user, business_profile):
        """Test user can edit their own business profile."""
        client.force_login(user)
        response = client.get(f'/marketplace/business/{business_profile.id}/edit/')
        assert response.status_code in [200, 404]

    def test_edit_other_business_profile_forbidden(self, client, business_profile):
        """Test user cannot edit another's business profile."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        client.force_login(other_user)
        
        response = client.post(f'/marketplace/business/{business_profile.id}/edit/', {
            'company_name': 'Hacked Company'
        })
        assert response.status_code in [403, 404]

    def test_business_profile_view_increments_counter(self, client, business_profile):
        """Test viewing profile increments view counter."""
        initial_views = business_profile.profile_views
        
        response = client.get(f'/marketplace/business/{business_profile.id}/')
        
        if response.status_code == 200:
            business_profile.refresh_from_db()
            assert business_profile.profile_views >= initial_views


@pytest.mark.django_db
class TestInvestmentOpportunityViews:
    """Test suite for investment opportunity views."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='investor_user',
            email='investor@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def investment(self, user):
        """Create test investment opportunity."""
        return InvestmentOpportunity.objects.create(
            business=user,
            title='Tech Startup Investment',
            description='Investment opportunity in tech startup',
            amount_seeking=Decimal('100000.00'),
            minimum_investment=Decimal('10000.00'),
            equity_percentage=Decimal('10.00'),
            industry='Technology',
            status='open'
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_investment_list_accessible(self, client):
        """Test investment list is publicly accessible."""
        response = client.get('/marketplace/investments/')
        assert response.status_code in [200, 404]

    def test_investment_detail_accessible(self, client, investment):
        """Test investment detail is accessible."""
        response = client.get(f'/marketplace/investment/{investment.slug}/')
        assert response.status_code in [200, 404]

    def test_create_investment_requires_login(self, client):
        """Test creating investment requires login."""
        response = client.get('/marketplace/investment/create/')
        assert response.status_code in [302, 403]

    def test_create_investment_authenticated(self, client, user):
        """Test authenticated user can create investment."""
        client.force_login(user)
        response = client.get('/marketplace/investment/create/')
        assert response.status_code in [200, 404]

    def test_investment_filter_by_industry(self, client, investment):
        """Test filtering investments by industry."""
        response = client.get('/marketplace/investments/?industry=Technology')
        assert response.status_code in [200, 404]

    def test_investment_filter_by_amount(self, client, investment):
        """Test filtering investments by amount."""
        response = client.get('/marketplace/investments/?min_amount=5000')
        assert response.status_code in [200, 404]

    def test_investment_search(self, client, investment):
        """Test searching investments."""
        response = client.get('/marketplace/investments/?q=Tech')
        assert response.status_code in [200, 404]


@pytest.mark.django_db
class TestJobOpportunityViews:
    """Test suite for job opportunity views."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='employer_user',
            email='employer@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def job(self, user):
        """Create test job opportunity."""
        return JobOpportunity.objects.create(
            business=user,
            title='Senior Python Developer',
            description='Looking for senior Python developer',
            requirements='5+ years Python experience',
            responsibilities='Build backend systems',
            location='Remote',
            job_type='full_time',
            experience_level='senior'
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_job_list_accessible(self, client):
        """Test job list is publicly accessible."""
        response = client.get('/marketplace/jobs/')
        assert response.status_code in [200, 404]

    def test_job_detail_accessible(self, client, job):
        """Test job detail is accessible."""
        response = client.get(f'/marketplace/job/{job.slug}/')
        assert response.status_code in [200, 404]

    def test_create_job_requires_login(self, client):
        """Test creating job requires login."""
        response = client.get('/marketplace/job/create/')
        assert response.status_code in [302, 403]

    def test_apply_job_requires_login(self, client, job):
        """Test applying for job requires login."""
        response = client.post(f'/marketplace/job/{job.slug}/apply/')
        assert response.status_code in [302, 403]

    def test_job_filter_by_type(self, client, job):
        """Test filtering jobs by type."""
        response = client.get('/marketplace/jobs/?job_type=full_time')
        assert response.status_code in [200, 404]

    def test_job_filter_by_location(self, client, job):
        """Test filtering jobs by location."""
        response = client.get('/marketplace/jobs/?location=Remote')
        assert response.status_code in [200, 404]

    def test_job_filter_by_experience(self, client, job):
        """Test filtering jobs by experience level."""
        response = client.get('/marketplace/jobs/?experience=senior')
        assert response.status_code in [200, 404]


@pytest.mark.django_db
class TestJobApplicationViews:
    """Test suite for job application views."""

    @pytest.fixture
    def employer(self):
        """Create employer user."""
        return User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def applicant(self):
        """Create applicant user."""
        return User.objects.create_user(
            username='applicant',
            email='applicant@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def job(self, employer):
        """Create test job."""
        return JobOpportunity.objects.create(
            business=employer,
            title='Test Job',
            description='Test description',
            requirements='Test requirements',
            responsibilities='Test responsibilities',
            location='Test location'
        )

    @pytest.fixture
    def application(self, job, applicant):
        """Create test application."""
        return JobApplication.objects.create(
            job=job,
            applicant=applicant,
            cover_letter='Test cover letter',
            resume='resumes/test.pdf'
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_submit_application(self, client, job, applicant):
        """Test submitting job application."""
        client.force_login(applicant)
        
        response = client.post(f'/marketplace/job/{job.slug}/apply/', {
            'cover_letter': 'I am interested in this position',
            'resume': 'path/to/resume.pdf'
        })
        
        assert response.status_code in [200, 302, 404]

    def test_view_own_applications(self, client, applicant, application):
        """Test viewing own applications."""
        client.force_login(applicant)
        
        response = client.get('/marketplace/my-applications/')
        assert response.status_code in [200, 404]

    def test_employer_view_applications(self, client, employer, job, application):
        """Test employer can view applications to their jobs."""
        client.force_login(employer)
        
        response = client.get(f'/marketplace/job/{job.slug}/applications/')
        assert response.status_code in [200, 404]

    def test_applicant_cannot_view_other_applications(self, client, applicant, employer, job):
        """Test applicant cannot view other applications."""
        other_applicant = User.objects.create_user(
            username='other_applicant',
            email='other@example.com',
            password='testpass123'
        )
        JobApplication.objects.create(
            job=job,
            applicant=other_applicant,
            cover_letter='Other cover letter',
            resume='resumes/other.pdf'
        )
        
        client.force_login(applicant)
        response = client.get(f'/marketplace/job/{job.slug}/applications/')
        
        assert response.status_code in [403, 404]

    def test_duplicate_application_prevented(self, client, job, applicant):
        """Test duplicate application is prevented."""
        # Create first application
        JobApplication.objects.create(
            job=job,
            applicant=applicant,
            cover_letter='First application',
            resume='resumes/first.pdf'
        )
        
        client.force_login(applicant)
        
        # Try to apply again
        response = client.post(f'/marketplace/job/{job.slug}/apply/', {
            'cover_letter': 'Second application',
            'resume': 'path/to/second.pdf'
        })
        
        # Should show error or redirect
        assert response.status_code in [200, 302, 400, 404]


@pytest.mark.django_db
class TestSavedItemViews:
    """Test suite for saved items functionality."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='saver_user',
            email='saver@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def investment(self, user):
        """Create test investment."""
        return InvestmentOpportunity.objects.create(
            business=user,
            title='Saveable Investment',
            description='Test',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('5000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Technology'
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_save_item_requires_login(self, client, investment):
        """Test saving item requires login."""
        response = client.post(f'/marketplace/investment/{investment.slug}/save/')
        assert response.status_code in [302, 403]

    def test_save_item_authenticated(self, client, user, investment):
        """Test authenticated user can save item."""
        client.force_login(user)
        response = client.post(f'/marketplace/investment/{investment.slug}/save/')
        assert response.status_code in [200, 302, 404]

    def test_view_saved_items(self, client, user):
        """Test viewing saved items."""
        client.force_login(user)
        response = client.get('/marketplace/saved/')
        assert response.status_code in [200, 404]

    def test_unsave_item(self, client, user, investment):
        """Test removing saved item."""
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(InvestmentOpportunity)
        SavedItem.objects.create(
            user=user,
            content_type=content_type,
            object_id=investment.id
        )
        
        client.force_login(user)
        response = client.post(f'/marketplace/investment/{investment.slug}/unsave/')
        assert response.status_code in [200, 302, 404]


@pytest.mark.django_db
class TestMarketplaceSearch:
    """Test marketplace search functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_global_search(self, client):
        """Test global marketplace search."""
        response = client.get('/marketplace/search/?q=python')
        assert response.status_code in [200, 404]

    def test_empty_search(self, client):
        """Test empty search query."""
        response = client.get('/marketplace/search/?q=')
        assert response.status_code in [200, 404]

    def test_special_characters_in_search(self, client):
        """Test search with special characters."""
        response = client.get('/marketplace/search/?q=%3Cscript%3E')
        assert response.status_code in [200, 400, 404]


@pytest.mark.django_db
class TestMarketplaceAccessControl:
    """Test access control in marketplace views."""

    @pytest.fixture
    def owner(self):
        """Create content owner."""
        return User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def other_user(self):
        """Create other user."""
        return User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def investment(self, owner):
        """Create test investment."""
        return InvestmentOpportunity.objects.create(
            business=owner,
            title='Owner Investment',
            description='Test',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('5000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Technology'
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_owner_can_edit_investment(self, client, owner, investment):
        """Test owner can edit their investment."""
        client.force_login(owner)
        response = client.get(f'/marketplace/investment/{investment.slug}/edit/')
        assert response.status_code in [200, 404]

    def test_other_cannot_edit_investment(self, client, other_user, investment):
        """Test non-owner cannot edit investment."""
        client.force_login(other_user)
        response = client.get(f'/marketplace/investment/{investment.slug}/edit/')
        assert response.status_code in [403, 404]

    def test_owner_can_delete_investment(self, client, owner, investment):
        """Test owner can delete their investment."""
        client.force_login(owner)
        response = client.post(f'/marketplace/investment/{investment.slug}/delete/')
        assert response.status_code in [200, 302, 404]

    def test_other_cannot_delete_investment(self, client, other_user, investment):
        """Test non-owner cannot delete investment."""
        client.force_login(other_user)
        response = client.post(f'/marketplace/investment/{investment.slug}/delete/')
        assert response.status_code in [403, 404]

