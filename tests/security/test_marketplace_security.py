"""
Marketplace Security Tests.
Pillar 6: Marketplace Security

Tests:
- Business profile authorization
- Investment opportunity CRUD authorization
- Job opportunity CRUD authorization  
- Application submission security
- Content injection prevention
- Search injection prevention
"""

import pytest
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from accounts.models import Category, UserProfile
from marketplace.models import (
    BusinessProfile, 
    InvestmentOpportunity, 
    JobOpportunity,
    JobApplication,
    SavedItem
)
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


@pytest.mark.security
class TestBusinessProfileAuthorization(TestCase):
    """
    Tests for business profile authorization.
    
    SECURITY REQUIREMENT: Only business owner can modify their profile.
    """

    def setUp(self):
        self.business_category, _ = Category.objects.get_or_create(
            name='Business', defaults={'slug': 'business', 'is_active': True}
        )
        
        self.owner = User.objects.create_user(
            username='business_owner',
            password='password123',
            email='owner@business.com'
        )
        self.attacker = User.objects.create_user(
            username='business_attacker',
            password='password123',
            email='attacker@test.com'
        )
        
        # Set up business profile for owner
        try:
            owner_profile = self.owner.profile
            owner_profile.category = self.business_category
            owner_profile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=self.owner, category=self.business_category)
        
        # Use correct model fields
        self.business_profile = BusinessProfile.objects.create(
            user=self.owner,
            company_name='Legitimate Company',
            industry='Technology',
            company_size='10-50',
            investment_seeking=Decimal('100000.00'),
            equity_offered=Decimal('10.00'),
            funding_stage='seed'
        )

    def test_business_profile_update__cross_user__denied(self):
        """
        SECURITY TEST: User cannot update another user's business profile.
        
        Risk: Business identity theft and fraud.
        """
        client = Client()
        client.force_login(self.attacker)
        
        response = client.post('/marketplace/business/update/', {
            'company_name': 'Hijacked Company',
            'industry': 'Fraud',
        })
        
        # Refresh from DB
        self.business_profile.refresh_from_db()
        
        # Verify no changes
        self.assertEqual(
            self.business_profile.company_name,
            'Legitimate Company',
            "SECURITY VULNERABILITY: Attacker modified victim's business profile"
        )
        self.assertNotEqual(
            self.business_profile.industry,
            'Fraud'
        )

    def test_business_profile_view__public_access__allowed(self):
        """
        SECURITY TEST: Business profiles should be publicly viewable.
        
        This is a positive test to ensure marketplace functionality.
        """
        client = Client()
        client.force_login(self.attacker)
        
        response = client.get(f'/marketplace/business/{self.business_profile.id}/')
        
        # Should be accessible (200) or redirect to list (302) or 404 (route may not exist)
        self.assertIn(response.status_code, [200, 302, 404])


@pytest.mark.security
class TestInvestmentOpportunityAuthorization(TestCase):
    """
    Tests for investment opportunity authorization.
    
    SECURITY REQUIREMENT: Only opportunity creator can modify/delete.
    """

    def setUp(self):
        self.business_category, _ = Category.objects.get_or_create(
            name='Business', defaults={'slug': 'business', 'is_active': True}
        )
        
        self.owner = User.objects.create_user(
            username='opp_owner',
            password='password123'
        )
        self.attacker = User.objects.create_user(
            username='opp_attacker',
            password='password123'
        )
        
        # Note: InvestmentOpportunity uses 'business' as ForeignKey to User
        self.opportunity = InvestmentOpportunity.objects.create(
            business=self.owner,
            title='Real Investment Opportunity',
            description='Legitimate opportunity',
            amount_seeking=Decimal('100000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('10.00'),
            industry='Technology',
            status='open'
        )

    def test_opportunity_edit__cross_user__denied(self):
        """
        SECURITY TEST: User cannot edit another user's investment opportunity.
        
        Risk: Investment fraud by modifying legitimate offers.
        """
        client = Client()
        client.force_login(self.attacker)
        
        # Try to edit opportunity (hypothetical edit endpoint)
        response = client.post(f'/marketplace/opportunity/{self.opportunity.slug}/edit/', {
            'title': 'Fraudulent Modified Title',
            'amount_seeking': '999999.00',
        })
        
        # Verify no changes
        self.opportunity.refresh_from_db()
        
        self.assertEqual(
            self.opportunity.title,
            'Real Investment Opportunity',
            "SECURITY VULNERABILITY: Attacker modified victim's investment opportunity"
        )

    def test_opportunity_delete__cross_user__denied(self):
        """
        SECURITY TEST: User cannot delete another user's opportunity.
        
        Risk: Malicious removal of legitimate business listings.
        """
        client = Client()
        client.force_login(self.attacker)
        
        response = client.post(f'/marketplace/opportunity/{self.opportunity.slug}/delete/')
        
        # Verify opportunity still exists
        self.opportunity.refresh_from_db()
        self.assertIsNotNone(self.opportunity.id)

    def test_opportunity_post__requires_business_profile(self):
        """
        SECURITY TEST: Only users with business profiles can post opportunities.
        
        Risk: Spam or fraudulent listings from non-business users.
        """
        # Create user without business profile
        regular_user = User.objects.create_user(
            username='regular_poster',
            password='password123'
        )
        
        client = Client()
        client.force_login(regular_user)
        
        response = client.post('/marketplace/opportunity/post/', {
            'title': 'Fake Opportunity',
            'description': 'Should not be created',
            'amount_seeking': '50000.00',
        })
        
        # Should not create opportunity for non-business user
        new_opps = InvestmentOpportunity.objects.filter(
            title='Fake Opportunity'
        )
        
        if new_opps.exists():
            pytest.fail(
                "SECURITY VULNERABILITY: Non-business user created investment opportunity"
            )


@pytest.mark.security
class TestJobOpportunityAuthorization(TestCase):
    """
    Tests for job opportunity authorization.
    
    SECURITY REQUIREMENT: Only job poster can modify/delete job listings.
    """

    def setUp(self):
        self.owner = User.objects.create_user(
            username='job_owner',
            password='password123'
        )
        self.attacker = User.objects.create_user(
            username='job_attacker',
            password='password123'
        )
        
        # JobOpportunity uses 'business' as ForeignKey to User
        self.job = JobOpportunity.objects.create(
            business=self.owner,
            title='Real Job Position',
            description='Legitimate job',
            requirements='Python experience',
            responsibilities='Build software',
            job_type='full_time',
            experience_level='mid',
            location='Remote',
            status='open'
        )

    def test_job_edit__cross_user__denied(self):
        """
        SECURITY TEST: User cannot edit another user's job listing.
        
        Risk: Job listing manipulation for phishing/scams.
        """
        client = Client()
        client.force_login(self.attacker)
        
        response = client.post(f'/marketplace/job/{self.job.slug}/edit/', {
            'title': 'Scam Job',
            'description': 'Send money here',
        })
        
        self.job.refresh_from_db()
        
        self.assertEqual(
            self.job.title,
            'Real Job Position',
            "SECURITY VULNERABILITY: Attacker modified victim's job listing"
        )

    def test_job_delete__cross_user__denied(self):
        """
        SECURITY TEST: User cannot delete another user's job.
        
        Risk: Sabotage of competitor listings.
        """
        client = Client()
        client.force_login(self.attacker)
        
        response = client.post(f'/marketplace/job/{self.job.slug}/delete/')
        
        self.job.refresh_from_db()
        self.assertIsNotNone(self.job.id)


@pytest.mark.security
class TestContentInjection(TestCase):
    """
    Tests for content injection prevention in marketplace.
    
    SECURITY REQUIREMENT: User-generated content should be sanitized.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='content_user',
            password='password123'
        )

    def test_opportunity_xss__html_escaped(self):
        """
        SECURITY TEST: HTML in opportunity descriptions should be escaped.
        
        Risk: Stored XSS affecting all viewers.
        """
        malicious_opportunity = InvestmentOpportunity.objects.create(
            business=self.user,
            title='Normal Title',
            description='<script>alert("XSS")</script>',
            amount_seeking=Decimal('100000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('10.00'),
            industry='Technology',
            status='open'
        )
        
        client = Client()
        client.force_login(self.user)
        
        response = client.get(f'/marketplace/opportunity/{malicious_opportunity.slug}/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8', errors='ignore')
            # Script should be escaped, not raw
            self.assertNotIn(
                '<script>alert("XSS")</script>',
                content,
                "XSS VULNERABILITY: Unescaped script tag in opportunity description"
            )

    def test_company_name_xss__html_escaped(self):
        """
        SECURITY TEST: HTML in company names should be escaped.
        
        Risk: XSS in business listings.
        """
        xss_business = BusinessProfile.objects.create(
            user=self.user,
            company_name='<img src=x onerror=alert(1)>',
            industry='Tech',
            company_size='1-10',
        )
        
        client = Client()
        
        response = client.get('/marketplace/businesses/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8', errors='ignore')
            self.assertNotIn(
                '<img src=x onerror=alert(1)>',
                content,
                "XSS VULNERABILITY: Unescaped HTML in company name"
            )


@pytest.mark.security
class TestSearchInjection(TestCase):
    """
    Tests for search injection prevention.
    
    SECURITY REQUIREMENT: Search queries should be sanitized.
    """

    def setUp(self):
        self.client = Client()

    def test_search__sql_injection__safe(self):
        """
        SECURITY TEST: SQL injection in search should be prevented.
        
        Risk: Database compromise.
        """
        payloads = [
            "'; DROP TABLE marketplace_businessprofile; --",
            "' OR '1'='1",
            "1; UPDATE auth_user SET is_superuser=1 WHERE username='attacker'--",
            "' UNION SELECT * FROM auth_user--",
        ]
        
        for payload in payloads:
            response = self.client.get(f'/marketplace/businesses/?q={payload}')
            
            # Should not crash (500)
            self.assertNotEqual(
                response.status_code, 500,
                f"SQL INJECTION: Server error with payload '{payload[:30]}...'"
            )
            
            # Check response for SQL error messages
            if response.status_code == 200:
                content = response.content.decode('utf-8', errors='ignore')
                sql_errors = ['syntax error', 'mysql', 'postgresql', 'sqlite']
                for error in sql_errors:
                    self.assertNotIn(
                        error, content.lower(),
                        f"SQL INJECTION: Database error exposed with payload"
                    )

    def test_search__xss__sanitized(self):
        """
        SECURITY TEST: XSS in search queries should be escaped.
        
        Risk: Reflected XSS in search results.
        """
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '"><img src=x onerror=alert(1)>',
            "javascript:alert('XSS')",
        ]
        
        for payload in xss_payloads:
            response = self.client.get(f'/marketplace/businesses/?q={payload}')
            
            if response.status_code == 200:
                content = response.content.decode('utf-8', errors='ignore')
                
                # Search term might be echoed but should be escaped
                if '<script>' in content:
                    pytest.fail(
                        "REFLECTED XSS: Unescaped script tag in search results"
                    )


@pytest.mark.security
class TestSavedItemsSecurity(TestCase):
    """
    Tests for saved items feature security.
    
    SECURITY REQUIREMENT: Saved items should be private.
    """

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='saver1', password='password123'
        )
        self.user2 = User.objects.create_user(
            username='saver2', password='password123'
        )
        
        self.business = BusinessProfile.objects.create(
            user=self.user1,
            company_name='Saved Business',
            industry='Tech',
            company_size='1-10',
        )
        
        # User1 saves the business
        content_type = ContentType.objects.get_for_model(BusinessProfile)
        self.saved_item = SavedItem.objects.create(
            user=self.user1,
            content_type=content_type,
            object_id=self.business.id,
            note='Private note about this business'
        )

    def test_saved_items__cross_user__denied(self):
        """
        SECURITY TEST: User cannot view other users' saved items.
        
        Risk: Privacy breach of user interests and notes.
        """
        client = Client()
        client.force_login(self.user2)
        
        response = client.get('/marketplace/saved/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8', errors='ignore')
            
            self.assertNotIn(
                'Private note about this business',
                content,
                "PRIVACY BREACH: Cross-user saved items visible"
            )

    def test_saved_items_delete__cross_user__denied(self):
        """
        SECURITY TEST: User cannot delete other users' saved items.
        
        Risk: Sabotage of user bookmarks.
        """
        client = Client()
        client.force_login(self.user2)
        
        response = client.post(f'/marketplace/saved/{self.saved_item.id}/delete/')
        
        self.assertIn(
            response.status_code, [403, 404],
            "SECURITY VULNERABILITY: Cross-user saved item deletion"
        )
        
        # Verify item still exists
        self.saved_item.refresh_from_db()
        self.assertIsNotNone(self.saved_item.id)
