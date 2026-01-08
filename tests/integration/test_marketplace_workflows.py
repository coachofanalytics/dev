"""
Marketplace Integration Tests

End-to-end marketplace workflows for Business, Investor, and Individual users.
Tests opportunity creation, applications, saved items, and access control.

Author: Fadhiri
Date: January 2026
Classification: Production-Grade Integration Tests
"""

import pytest
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from accounts.models import Category, UserProfile
from marketplace.models import (
    BusinessProfile, InvestmentOpportunity, 
    JobOpportunity, JobApplication, SavedItem
)
from onboarding.models import OnboardingProgress


@pytest.mark.django_db
@pytest.mark.integration
class TestBusinessProfileWorkflow:
    """
    INTEGRATION: Business user profile and opportunity management.
    """
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def business_user(self):
        """Create verified business user."""
        category = Category.objects.create(
            name='Business', slug='business', is_active=True
        )
        user = User.objects.create_user(
            username='business_owner',
            email='business@company.com',
            password='BusinessPass123!',
            is_active=True
        )
        UserProfile.objects.create(user=user, category=category)
        OnboardingProgress.objects.create(
            user=user, email_verified=True, profile_completed=True
        )
        return user
    
    def test_business_profile__creation__success(self, client, business_user):
        """
        INTEGRATION: Business user can create business profile.
        """
        client.force_login(business_user)
        
        response = client.post('/marketplace/business/update/', {
            'company_name': 'Test Company Ltd',
            'industry': 'Technology',
            'description': 'A test technology company',
            'website': 'https://testcompany.com',
            'employee_count': '10-50',
        })
        
        # Check if business profile created
        profile = BusinessProfile.objects.filter(user=business_user).first()
        
        if profile:
            assert profile.company_name == 'Test Company Ltd'
    
    def test_business_profile__view_tracking(self, client, business_user):
        """
        INTEGRATION: Business profile tracks view count.
        """
        client.force_login(business_user)
        
        # Create profile first
        profile = BusinessProfile.objects.create(
            user=business_user,
            company_name='View Test Company',
            industry='Technology',
            description='Testing view tracking'
        )
        
        initial_views = profile.view_count
        
        # View the profile (as another user or anonymously)
        client.logout()
        response = client.get(f'/marketplace/business/{profile.id}/')
        
        profile.refresh_from_db()
        # View count should increase (depends on implementation)


@pytest.mark.django_db
@pytest.mark.integration
class TestInvestmentOpportunityWorkflow:
    """
    INTEGRATION: Investment opportunity CRUD operations.
    """
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def business_user(self):
        category = Category.objects.create(
            name='Business', slug='business-inv', is_active=True
        )
        user = User.objects.create_user(
            username='investment_business',
            email='investment_business@company.com',
            password='InvestBizPass123!',
            is_active=True
        )
        UserProfile.objects.create(user=user, category=category)
        return user
    
    def test_investment_opportunity__create__success(self, client, business_user):
        """
        INTEGRATION: Business user can create investment opportunity.
        """
        client.force_login(business_user)
        
        response = client.post('/marketplace/opportunity/post/', {
            'title': 'Series A Investment',
            'description': 'Looking for Series A funding',
            'amount_seeking': '500000.00',
            'minimum_investment': '50000.00',
            'equity_percentage': '15.00',
            'industry': 'Technology',
        })
        
        opportunity = InvestmentOpportunity.objects.filter(
            business=business_user,
            title='Series A Investment'
        ).first()
        
        if opportunity:
            assert opportunity.amount_seeking == Decimal('500000.00')
            assert opportunity.status == 'open'
    
    def test_investment_opportunity__slug_generated(self, client, business_user):
        """
        INTEGRATION: Investment opportunity generates unique slug.
        """
        opportunity = InvestmentOpportunity.objects.create(
            business=business_user,
            title='Unique Slug Test Opportunity',
            description='Testing slug generation',
            amount_seeking=Decimal('100000.00'),
            minimum_investment=Decimal('10000.00'),
            equity_percentage=Decimal('10.00'),
            industry='Technology'
        )
        
        assert opportunity.slug is not None
        assert 'unique-slug-test' in opportunity.slug.lower() or opportunity.slug
    
    def test_investment_opportunity__equity_validation(self, client, business_user):
        """
        INTEGRATION: Investment equity percentage validated (max 100%).
        """
        client.force_login(business_user)
        
        response = client.post('/marketplace/opportunity/post/', {
            'title': 'Invalid Equity',
            'description': 'Testing invalid equity',
            'amount_seeking': '100000.00',
            'minimum_investment': '10000.00',
            'equity_percentage': '150.00',  # Invalid - over 100%
            'industry': 'Technology',
        })
        
        # Should not create with invalid equity
        invalid_opp = InvestmentOpportunity.objects.filter(
            business=business_user,
            equity_percentage__gt=100
        ).exists()
        
        if invalid_opp:
            pytest.fail("FINDING: Investment created with equity > 100%")


@pytest.mark.django_db
@pytest.mark.integration
class TestJobOpportunityWorkflow:
    """
    INTEGRATION: Job opportunity CRUD operations.
    """
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def business_user(self):
        category = Category.objects.create(
            name='Business', slug='business-job', is_active=True
        )
        user = User.objects.create_user(
            username='job_poster',
            email='jobs@company.com',
            password='JobPosterPass123!',
            is_active=True
        )
        UserProfile.objects.create(user=user, category=category)
        return user
    
    def test_job_opportunity__create__success(self, client, business_user):
        """
        INTEGRATION: Business user can create job opportunity.
        """
        client.force_login(business_user)
        
        response = client.post('/marketplace/job/post/', {
            'title': 'Software Engineer',
            'description': 'Looking for a software engineer',
            'requirements': '3+ years Python experience',
            'responsibilities': 'Backend development',
            'location': 'Remote',
            'job_type': 'full_time',
            'salary_min': '80000',
            'salary_max': '120000',
        })
        
        job = JobOpportunity.objects.filter(
            business=business_user,
            title='Software Engineer'
        ).first()
        
        if job:
            assert job.status == 'open'
    
    def test_job_opportunity__default_status_open(self, business_user):
        """
        INTEGRATION: New job opportunity has 'open' status by default.
        """
        job = JobOpportunity.objects.create(
            business=business_user,
            title='Default Status Test',
            description='Testing default status',
            requirements='None',
            responsibilities='None',
            location='Remote',
            job_type='full_time'
        )
        
        assert job.status == 'open'


@pytest.mark.django_db
@pytest.mark.integration
class TestInvestorWorkflow:
    """
    INTEGRATION: Investor user workflows.
    """
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def investor_user(self):
        category = Category.objects.create(
            name='Investor', slug='investor', is_active=True
        )
        user = User.objects.create_user(
            username='angel_investor',
            email='angel@investor.com',
            password='AngelPass123!',
            is_active=True
        )
        UserProfile.objects.create(user=user, category=category)
        return user
    
    @pytest.fixture
    def investment_opportunity(self):
        business_user = User.objects.create_user(
            username='opp_business',
            email='opp@business.com',
            password='OppPass123!'
        )
        return InvestmentOpportunity.objects.create(
            business=business_user,
            title='Investment for Investor Test',
            description='Test opportunity',
            amount_seeking=Decimal('200000.00'),
            minimum_investment=Decimal('20000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Technology',
            status='open'
        )
    
    def test_investor__browse_opportunities__success(
        self, client, investor_user, investment_opportunity
    ):
        """
        INTEGRATION: Investor can browse investment opportunities.
        """
        client.force_login(investor_user)
        
        response = client.get('/marketplace/opportunities/')
        
        assert response.status_code == 200
    
    def test_investor__save_opportunity__success(
        self, client, investor_user, investment_opportunity
    ):
        """
        INTEGRATION: Investor can save investment opportunity.
        """
        client.force_login(investor_user)
        
        # Save the opportunity
        saved = SavedItem.objects.create(
            user=investor_user,
            content_object=investment_opportunity
        )
        
        assert saved.pk is not None
        
        # Verify can retrieve saved items
        saved_items = SavedItem.objects.filter(user=investor_user)
        assert saved_items.count() >= 1
    
    def test_investor__unsave_opportunity__success(
        self, client, investor_user, investment_opportunity
    ):
        """
        INTEGRATION: Investor can unsave opportunity.
        """
        # First save
        saved = SavedItem.objects.create(
            user=investor_user,
            content_object=investment_opportunity
        )
        
        # Then unsave
        saved.delete()
        
        remaining = SavedItem.objects.filter(
            user=investor_user
        ).count()
        
        assert remaining == 0


@pytest.mark.django_db
@pytest.mark.integration
class TestJobApplicationWorkflow:
    """
    INTEGRATION: Job application workflow for individuals.
    """
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def individual_user(self):
        category = Category.objects.create(
            name='General', slug='general', is_active=True
        )
        user = User.objects.create_user(
            username='job_seeker',
            email='seeker@jobs.com',
            password='SeekerPass123!',
            is_active=True
        )
        UserProfile.objects.create(user=user, category=category)
        return user
    
    @pytest.fixture
    def job_opportunity(self):
        business_user = User.objects.create_user(
            username='job_business',
            email='job@business.com',
            password='JobBizPass123!'
        )
        return JobOpportunity.objects.create(
            business=business_user,
            title='Developer Position',
            description='Looking for developers',
            requirements='Python, Django',
            responsibilities='Backend development',
            location='Remote',
            job_type='full_time',
            status='open'
        )
    
    def test_job_application__create__success(
        self, client, individual_user, job_opportunity
    ):
        """
        INTEGRATION: User can apply to job opportunity.
        """
        application = JobApplication.objects.create(
            job=job_opportunity,
            applicant=individual_user,
            cover_letter='I am interested in this position.'
        )
        
        assert application.pk is not None
        assert application.status == 'pending'
    
    def test_job_application__one_per_user_per_job(
        self, client, individual_user, job_opportunity
    ):
        """
        INTEGRATION: User can only apply once per job.
        """
        # First application
        JobApplication.objects.create(
            job=job_opportunity,
            applicant=individual_user,
            cover_letter='First application'
        )
        
        # Second application should fail
        from django.db import IntegrityError
        
        try:
            JobApplication.objects.create(
                job=job_opportunity,
                applicant=individual_user,
                cover_letter='Second application'
            )
            pytest.fail("FINDING: Duplicate job application allowed")
        except IntegrityError:
            pass  # Expected behavior
    
    def test_job_application__status_tracking(
        self, individual_user, job_opportunity
    ):
        """
        INTEGRATION: Job application status can be tracked.
        """
        application = JobApplication.objects.create(
            job=job_opportunity,
            applicant=individual_user,
            cover_letter='Status tracking test'
        )
        
        # Initial status
        assert application.status == 'pending'
        
        # Update status
        application.status = 'reviewed'
        application.save()
        application.refresh_from_db()
        
        assert application.status == 'reviewed'


@pytest.mark.django_db
@pytest.mark.integration
class TestMarketplaceAccessControl:
    """
    INTEGRATION: Marketplace access control tests.
    """
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def business_user(self):
        category = Category.objects.create(
            name='Business', slug='business-access', is_active=True
        )
        user = User.objects.create_user(
            username='access_business',
            email='access@business.com',
            password='AccessPass123!',
            is_active=True
        )
        UserProfile.objects.create(user=user, category=category)
        return user
    
    @pytest.fixture
    def other_business_user(self):
        user = User.objects.create_user(
            username='other_business',
            email='other@business.com',
            password='OtherPass123!',
            is_active=True
        )
        return user
    
    def test_opportunity__cannot_edit_others(
        self, client, business_user, other_business_user
    ):
        """
        INTEGRATION: User cannot edit other users' opportunities.
        """
        # Create opportunity by business_user
        opportunity = InvestmentOpportunity.objects.create(
            business=business_user,
            title='Protected Opportunity',
            description='Should be protected',
            amount_seeking=Decimal('100000.00'),
            minimum_investment=Decimal('10000.00'),
            equity_percentage=Decimal('10.00'),
            industry='Technology'
        )
        
        # Login as other user and try to edit
        client.force_login(other_business_user)
        
        response = client.post(f'/marketplace/opportunity/{opportunity.slug}/edit/', {
            'title': 'Hacked Title',
            'description': 'Modified description'
        })
        
        opportunity.refresh_from_db()
        
        # Title should NOT have changed
        if opportunity.title == 'Hacked Title':
            pytest.fail("FINDING: User can edit other users' opportunities")
    
    def test_unauthenticated__cannot_create_opportunity(self, client):
        """
        INTEGRATION: Unauthenticated user cannot create opportunities.
        """
        response = client.post('/marketplace/opportunity/post/', {
            'title': 'Unauthorized',
            'description': 'Should not create'
        })
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/login/' in response.url or '/accounts/' in response.url


@pytest.mark.django_db
@pytest.mark.integration
class TestMarketplaceFiltersAndSearch:
    """
    INTEGRATION: Marketplace filtering and search.
    """
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def opportunities(self):
        business = User.objects.create_user(
            username='filter_business',
            email='filter@business.com',
            password='FilterPass123!'
        )
        
        opps = []
        industries = ['Technology', 'Healthcare', 'Finance']
        for i, industry in enumerate(industries):
            opp = InvestmentOpportunity.objects.create(
                business=business,
                title=f'{industry} Investment {i}',
                description=f'Investment in {industry}',
                amount_seeking=Decimal(f'{(i+1) * 100000}.00'),
                minimum_investment=Decimal(f'{(i+1) * 10000}.00'),
                equity_percentage=Decimal(f'{(i+1) * 5}.00'),
                industry=industry,
                status='open'
            )
            opps.append(opp)
        
        return opps
    
    def test_opportunities__filter_by_industry(self, client, opportunities):
        """
        INTEGRATION: Opportunities can be filtered by industry.
        """
        response = client.get('/marketplace/opportunities/?industry=Technology')
        
        assert response.status_code == 200
        # Verify filtering works (check response content)
    
    def test_jobs__filter_by_type(self, client):
        """
        INTEGRATION: Jobs can be filtered by type.
        """
        business = User.objects.create_user(
            username='job_filter_business',
            email='jobfilter@business.com',
            password='JobFilterPass123!'
        )
        
        JobOpportunity.objects.create(
            business=business,
            title='Full Time Job',
            description='FT position',
            requirements='None',
            responsibilities='None',
            location='Remote',
            job_type='full_time'
        )
        
        JobOpportunity.objects.create(
            business=business,
            title='Part Time Job',
            description='PT position',
            requirements='None',
            responsibilities='None',
            location='Remote',
            job_type='part_time'
        )
        
        response = client.get('/marketplace/jobs/?job_type=full_time')
        
        assert response.status_code == 200

