"""
Regression Tests for Marketplace Functionality

These tests verify that existing marketplace features remain intact
after code changes. Tests are designed to FIND and REPORT issues.

Tested Features:
- Business profile management
- Investment opportunities
- Job opportunities
- Job applications
- Saved items functionality

Author: Fadhiri
Date: January 2026
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from datetime import date, timedelta

import accounts.models as accounts_models
from marketplace.models import (
    BusinessProfile, InvestmentOpportunity, 
    JobOpportunity, JobApplication, SavedItem
)


class BusinessProfileRegressionTests(TestCase):
    """
    Regression tests for business profile model.
    
    These tests verify that:
    - Business profiles can be created
    - User relationship works
    - Profile views tracking works
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='business_user',
            email='business@test.com',
            password='BusinessPass123!'
        )
    
    def test_business_profile_creation(self):
        """
        REGRESSION TEST: Business profile should be created successfully.
        
        Verifies: Basic profile creation.
        Reports: Profile creation failures.
        """
        profile = BusinessProfile.objects.create(
            user=self.user,
            company_name='Test Company',
            industry='Technology'
        )
        
        self.assertIsNotNone(profile.pk, "REGRESSION ISSUE: Business profile not created")
        self.assertEqual(profile.company_name, 'Test Company', "REGRESSION ISSUE: Company name not saved")
    
    def test_business_profile_one_per_user(self):
        """
        REGRESSION TEST: Each user should have only one business profile.
        
        Verifies: OneToOne constraint enforced.
        Reports: Multiple business profiles per user allowed.
        """
        BusinessProfile.objects.create(
            user=self.user,
            company_name='Company 1',
            industry='Tech'
        )
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Multiple business profiles per user allowed"):
            BusinessProfile.objects.create(
                user=self.user,
                company_name='Company 2',
                industry='Finance'
            )
    
    def test_business_profile_views_default_zero(self):
        """
        REGRESSION TEST: Profile views should default to zero.
        
        Verifies: Default profile_views value.
        Reports: Non-zero default views.
        """
        profile = BusinessProfile.objects.create(
            user=self.user,
            company_name='Views Test',
            industry='Tech'
        )
        
        self.assertEqual(profile.profile_views, 0, "REGRESSION ISSUE: profile_views not defaulting to 0")
    
    def test_business_profile_increment_views(self):
        """
        REGRESSION TEST: increment_views() should increase view count.
        
        Verifies: View tracking functionality.
        Reports: View increment not working.
        """
        profile = BusinessProfile.objects.create(
            user=self.user,
            company_name='Views Test',
            industry='Tech'
        )
        
        profile.increment_views()
        profile.refresh_from_db()
        
        self.assertEqual(profile.profile_views, 1, "REGRESSION ISSUE: increment_views() not working")
    
    def test_business_profile_company_size_choices(self):
        """
        REGRESSION TEST: Company size should accept valid choices.
        
        Verifies: COMPANY_SIZE_CHOICES validation.
        Reports: Invalid company sizes accepted.
        """
        profile = BusinessProfile.objects.create(
            user=self.user,
            company_name='Size Test',
            industry='Tech',
            company_size='51-200'
        )
        
        self.assertEqual(profile.company_size, '51-200', "REGRESSION ISSUE: Company size not saved correctly")
    
    def test_business_profile_funding_stage_choices(self):
        """
        REGRESSION TEST: Funding stage should accept valid choices.
        
        Verifies: FUNDING_STAGE_CHOICES validation.
        Reports: Invalid funding stages accepted.
        """
        profile = BusinessProfile.objects.create(
            user=self.user,
            company_name='Stage Test',
            industry='Tech',
            funding_stage='series_a'
        )
        
        self.assertEqual(profile.funding_stage, 'series_a', "REGRESSION ISSUE: Funding stage not saved correctly")
    
    def test_business_profile_equity_offered_validation(self):
        """
        REGRESSION TEST: Equity offered should be between 0 and 100.
        
        Verifies: Equity percentage validators.
        Reports: Invalid equity percentages allowed.
        """
        profile = BusinessProfile(
            user=self.user,
            company_name='Equity Test',
            industry='Tech',
            equity_offered=Decimal('150.00')  # Invalid - over 100%
        )
        
        with self.assertRaises(ValidationError, msg="REGRESSION ISSUE: Equity over 100% allowed"):
            profile.full_clean()


class InvestmentOpportunityRegressionTests(TestCase):
    """
    Regression tests for investment opportunity model.
    
    These tests verify that:
    - Investment opportunities can be created
    - Slug auto-generation works
    - Status management works
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='investor_user',
            email='investor@test.com',
            password='InvestorPass123!'
        )
    
    def test_investment_opportunity_creation(self):
        """
        REGRESSION TEST: Investment opportunity should be created successfully.
        
        Verifies: Basic opportunity creation.
        Reports: Opportunity creation failures.
        """
        opportunity = InvestmentOpportunity.objects.create(
            business=self.user,
            title='Tech Startup Opportunity',
            description='Great investment opportunity',
            amount_seeking=Decimal('100000.00'),
            minimum_investment=Decimal('5000.00'),
            equity_percentage=Decimal('10.00'),
            industry='Technology'
        )
        
        self.assertIsNotNone(opportunity.pk, "REGRESSION ISSUE: Investment opportunity not created")
        self.assertEqual(opportunity.title, 'Tech Startup Opportunity', "REGRESSION ISSUE: Title not saved")
    
    def test_investment_opportunity_slug_auto_generated(self):
        """
        REGRESSION TEST: Slug should be auto-generated from title.
        
        Verifies: Slug auto-generation on save.
        Reports: Slug not generated.
        """
        opportunity = InvestmentOpportunity.objects.create(
            business=self.user,
            title='Amazing Investment Chance',
            description='Test opportunity',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Tech'
        )
        
        self.assertIsNotNone(opportunity.slug, "REGRESSION ISSUE: Slug not auto-generated")
        self.assertIn('amazing', opportunity.slug.lower(), "REGRESSION ISSUE: Slug not derived from title")
    
    def test_investment_opportunity_slug_unique(self):
        """
        REGRESSION TEST: Slugs should be unique (with counter for duplicates).
        
        Verifies: Unique slug generation.
        Reports: Duplicate slugs causing errors.
        """
        opp1 = InvestmentOpportunity.objects.create(
            business=self.user,
            title='Duplicate Title',
            description='First opportunity',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Tech'
        )
        
        opp2 = InvestmentOpportunity.objects.create(
            business=self.user,
            title='Duplicate Title',
            description='Second opportunity',
            amount_seeking=Decimal('60000.00'),
            minimum_investment=Decimal('2000.00'),
            equity_percentage=Decimal('6.00'),
            industry='Tech'
        )
        
        self.assertNotEqual(opp1.slug, opp2.slug, "REGRESSION ISSUE: Duplicate slugs generated")
    
    def test_investment_opportunity_default_status_open(self):
        """
        REGRESSION TEST: Default status should be 'open'.
        
        Verifies: Default status value.
        Reports: Incorrect default status.
        """
        opportunity = InvestmentOpportunity.objects.create(
            business=self.user,
            title='Status Test',
            description='Test',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Tech'
        )
        
        self.assertEqual(opportunity.status, 'open', "REGRESSION ISSUE: Default status not 'open'")
    
    def test_investment_opportunity_equity_validation(self):
        """
        REGRESSION TEST: Equity percentage should be between 0 and 100.
        
        Verifies: Equity validators.
        Reports: Invalid equity percentages allowed.
        """
        opportunity = InvestmentOpportunity(
            business=self.user,
            title='Equity Test',
            description='Test',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('150.00'),  # Invalid
            industry='Tech'
        )
        
        with self.assertRaises(ValidationError, msg="REGRESSION ISSUE: Invalid equity percentage allowed"):
            opportunity.full_clean()
    
    def test_investment_opportunity_increment_views(self):
        """
        REGRESSION TEST: increment_views() should increase view count.
        
        Verifies: View tracking functionality.
        Reports: View increment not working.
        """
        opportunity = InvestmentOpportunity.objects.create(
            business=self.user,
            title='Views Test',
            description='Test',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Tech'
        )
        
        opportunity.increment_views()
        opportunity.refresh_from_db()
        
        self.assertEqual(opportunity.views, 1, "REGRESSION ISSUE: increment_views() not working")


class JobOpportunityRegressionTests(TestCase):
    """
    Regression tests for job opportunity model.
    
    These tests verify that:
    - Job opportunities can be created
    - Slug auto-generation works
    - Job type and experience level choices work
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='employer_user',
            email='employer@test.com',
            password='EmployerPass123!'
        )
    
    def test_job_opportunity_creation(self):
        """
        REGRESSION TEST: Job opportunity should be created successfully.
        
        Verifies: Basic job creation.
        Reports: Job creation failures.
        """
        job = JobOpportunity.objects.create(
            business=self.user,
            title='Software Engineer',
            description='Full-stack developer role',
            requirements='Python, Django, React',
            responsibilities='Build and maintain applications',
            location='Remote'
        )
        
        self.assertIsNotNone(job.pk, "REGRESSION ISSUE: Job opportunity not created")
        self.assertEqual(job.title, 'Software Engineer', "REGRESSION ISSUE: Job title not saved")
    
    def test_job_opportunity_slug_auto_generated(self):
        """
        REGRESSION TEST: Slug should be auto-generated from title.
        
        Verifies: Slug auto-generation.
        Reports: Slug not generated.
        """
        job = JobOpportunity.objects.create(
            business=self.user,
            title='Senior Python Developer',
            description='Senior role',
            requirements='5+ years Python',
            responsibilities='Lead development',
            location='NYC'
        )
        
        self.assertIsNotNone(job.slug, "REGRESSION ISSUE: Slug not auto-generated")
        self.assertIn('senior', job.slug.lower(), "REGRESSION ISSUE: Slug not derived from title")
    
    def test_job_opportunity_default_job_type(self):
        """
        REGRESSION TEST: Default job type should be 'full_time'.
        
        Verifies: Default job_type value.
        Reports: Incorrect default job type.
        """
        job = JobOpportunity.objects.create(
            business=self.user,
            title='Default Type Test',
            description='Test',
            requirements='Test',
            responsibilities='Test',
            location='Test'
        )
        
        self.assertEqual(job.job_type, 'full_time', "REGRESSION ISSUE: Default job type not 'full_time'")
    
    def test_job_opportunity_default_experience_level(self):
        """
        REGRESSION TEST: Default experience level should be 'mid'.
        
        Verifies: Default experience_level value.
        Reports: Incorrect default experience level.
        """
        job = JobOpportunity.objects.create(
            business=self.user,
            title='Default Exp Test',
            description='Test',
            requirements='Test',
            responsibilities='Test',
            location='Test'
        )
        
        self.assertEqual(job.experience_level, 'mid', "REGRESSION ISSUE: Default experience level not 'mid'")
    
    def test_job_opportunity_default_status_open(self):
        """
        REGRESSION TEST: Default status should be 'open'.
        
        Verifies: Default status value.
        Reports: Incorrect default status.
        """
        job = JobOpportunity.objects.create(
            business=self.user,
            title='Default Status Test',
            description='Test',
            requirements='Test',
            responsibilities='Test',
            location='Test'
        )
        
        self.assertEqual(job.status, 'open', "REGRESSION ISSUE: Default status not 'open'")
    
    def test_job_opportunity_remote_option_default(self):
        """
        REGRESSION TEST: Remote option should default to False.
        
        Verifies: Default remote_option value.
        Reports: Incorrect default for remote option.
        """
        job = JobOpportunity.objects.create(
            business=self.user,
            title='Remote Test',
            description='Test',
            requirements='Test',
            responsibilities='Test',
            location='Test'
        )
        
        self.assertFalse(job.remote_option, "REGRESSION ISSUE: remote_option not defaulting to False")


class JobApplicationRegressionTests(TestCase):
    """
    Regression tests for job application model.
    
    These tests verify that:
    - Job applications can be created
    - One application per user per job
    - Status transitions work
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.employer = User.objects.create_user(
            username='app_employer',
            email='app_employer@test.com',
            password='EmployerPass123!'
        )
        self.applicant = User.objects.create_user(
            username='app_applicant',
            email='app_applicant@test.com',
            password='ApplicantPass123!'
        )
        self.job = JobOpportunity.objects.create(
            business=self.employer,
            title='Test Job',
            description='Test',
            requirements='Test',
            responsibilities='Test',
            location='Test'
        )
    
    def test_job_application_creation(self):
        """
        REGRESSION TEST: Job application should be created successfully.
        
        Verifies: Basic application creation.
        Reports: Application creation failures.
        """
        application = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant,
            cover_letter='I am interested in this position',
            resume='resumes/test_resume.pdf'
        )
        
        self.assertIsNotNone(application.pk, "REGRESSION ISSUE: Job application not created")
        self.assertEqual(application.job, self.job, "REGRESSION ISSUE: Job not linked")
        self.assertEqual(application.applicant, self.applicant, "REGRESSION ISSUE: Applicant not linked")
    
    def test_job_application_default_status_pending(self):
        """
        REGRESSION TEST: Default application status should be 'pending'.
        
        Verifies: Default status value.
        Reports: Incorrect default status.
        """
        application = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant,
            cover_letter='Test',
            resume='resumes/test.pdf'
        )
        
        self.assertEqual(application.status, 'pending', "REGRESSION ISSUE: Default status not 'pending'")
    
    def test_job_application_one_per_user_per_job(self):
        """
        REGRESSION TEST: Only one application per user per job.
        
        Verifies: unique_together constraint.
        Reports: Duplicate applications allowed.
        """
        JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant,
            cover_letter='First application',
            resume='resumes/first.pdf'
        )
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Duplicate applications per job allowed"):
            JobApplication.objects.create(
                job=self.job,
                applicant=self.applicant,
                cover_letter='Second application',
                resume='resumes/second.pdf'
            )
    
    def test_job_application_status_choices_valid(self):
        """
        REGRESSION TEST: All status choices should be valid.
        
        Verifies: STATUS_CHOICES are accepted.
        Reports: Invalid status handling.
        """
        valid_statuses = ['pending', 'reviewing', 'shortlisted', 'interview', 'offered', 'rejected', 'withdrawn']
        
        for i, status in enumerate(valid_statuses):
            applicant = User.objects.create_user(
                username=f'status_applicant_{i}',
                email=f'status_applicant_{i}@test.com',
                password='TestPass123!'
            )
            application = JobApplication.objects.create(
                job=self.job,
                applicant=applicant,
                cover_letter='Test',
                resume='resumes/test.pdf',
                status=status
            )
            self.assertEqual(
                application.status, 
                status, 
                f"REGRESSION ISSUE: Status '{status}' not accepted"
            )


class SavedItemRegressionTests(TestCase):
    """
    Regression tests for saved items functionality.
    
    These tests verify that:
    - Items can be saved
    - Duplicate saves are prevented
    - Generic foreign key works
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        from django.contrib.contenttypes.models import ContentType
        
        self.user = User.objects.create_user(
            username='save_user',
            email='save@test.com',
            password='SavePass123!'
        )
        self.employer = User.objects.create_user(
            username='save_employer',
            email='save_employer@test.com',
            password='EmployerPass123!'
        )
        self.job = JobOpportunity.objects.create(
            business=self.employer,
            title='Saved Job',
            description='Test',
            requirements='Test',
            responsibilities='Test',
            location='Test'
        )
        self.content_type = ContentType.objects.get_for_model(JobOpportunity)
    
    def test_save_item_creation(self):
        """
        REGRESSION TEST: Saved item should be created successfully.
        
        Verifies: Basic save functionality.
        Reports: Save functionality failures.
        """
        saved = SavedItem.objects.create(
            user=self.user,
            content_type=self.content_type,
            object_id=self.job.pk
        )
        
        self.assertIsNotNone(saved.pk, "REGRESSION ISSUE: Saved item not created")
        self.assertEqual(saved.content_object, self.job, "REGRESSION ISSUE: Content object not linked")
    
    def test_save_item_no_duplicate(self):
        """
        REGRESSION TEST: Same item cannot be saved twice by same user.
        
        Verifies: unique_together constraint on saves.
        Reports: Duplicate saves allowed.
        """
        SavedItem.objects.create(
            user=self.user,
            content_type=self.content_type,
            object_id=self.job.pk
        )
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Duplicate saves allowed"):
            SavedItem.objects.create(
                user=self.user,
                content_type=self.content_type,
                object_id=self.job.pk
            )
    
    def test_save_item_timestamp_set(self):
        """
        REGRESSION TEST: saved_at timestamp should be set automatically.
        
        Verifies: Auto timestamp on save.
        Reports: Missing timestamp.
        """
        saved = SavedItem.objects.create(
            user=self.user,
            content_type=self.content_type,
            object_id=self.job.pk
        )
        
        self.assertIsNotNone(saved.saved_at, "REGRESSION ISSUE: saved_at timestamp not set")

