"""
Comprehensive unit tests for Marketplace models.
Tests business profiles, investment opportunities, job opportunities, and applications.
"""
from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from datetime import date

User = get_user_model()
BusinessProfile = apps.get_model('marketplace', 'BusinessProfile')
InvestmentOpportunity = apps.get_model('marketplace', 'InvestmentOpportunity')
JobOpportunity = apps.get_model('marketplace', 'JobOpportunity')
JobApplication = apps.get_model('marketplace', 'JobApplication')


class BusinessProfileBasicTests(TestCase):
    """Basic tests for BusinessProfile model."""

    def setUp(self):
        self.user = User.objects.create_user(username='bizuser', password='pass')

    def test_business_profile_creation(self):
        """Test creating a business profile."""
        profile = BusinessProfile.objects.create(
            user=self.user,
            company_name='Test Company',
            industry='Technology'
        )
        self.assertEqual(profile.company_name, 'Test Company')
        self.assertEqual(profile.industry, 'Technology')

    def test_business_profile_str_representation(self):
        """Test business profile string representation."""
        profile = BusinessProfile.objects.create(
            user=self.user,
            company_name='Test Company',
            industry='Technology'
        )
        expected = f'Test Company ({self.user.username})'
        self.assertEqual(str(profile), expected)

    def test_default_values(self):
        """Test business profile default values."""
        profile = BusinessProfile.objects.create(
            user=self.user,
            company_name='Test Company',
            industry='Technology'
        )
        self.assertEqual(profile.company_size, '1-10')
        self.assertEqual(profile.funding_stage, 'idea')
        self.assertEqual(profile.profile_views, 0)


class BusinessProfileIncrementViewsTests(TestCase):
    """Tests for profile views increment."""

    def setUp(self):
        self.user = User.objects.create_user(username='viewsuser', password='pass')
        self.profile = BusinessProfile.objects.create(
            user=self.user,
            company_name='Test Company',
            industry='Technology'
        )

    def test_increment_views(self):
        """Test incrementing profile views."""
        self.assertEqual(self.profile.profile_views, 0)
        self.profile.increment_views()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.profile_views, 1)

    def test_multiple_increments(self):
        """Test multiple view increments."""
        for _ in range(5):
            self.profile.increment_views()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.profile_views, 5)


class BusinessProfileFieldValidationTests(TestCase):
    """Tests for business profile field validations."""

    def setUp(self):
        self.user = User.objects.create_user(username='validateuser', password='pass')

    def test_equity_offered_max_value(self):
        """Test equity offered max value (100%)."""
        profile = BusinessProfile(
            user=self.user,
            company_name='Test',
            industry='Tech',
            equity_offered=Decimal('100.00')
        )
        profile.full_clean()

    def test_equity_offered_exceeds_max(self):
        """Test equity offered exceeding max raises error."""
        profile = BusinessProfile(
            user=self.user,
            company_name='Test',
            industry='Tech',
            equity_offered=Decimal('101.00')
        )
        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_equity_offered_negative(self):
        """Test negative equity offered raises error."""
        profile = BusinessProfile(
            user=self.user,
            company_name='Test',
            industry='Tech',
            equity_offered=Decimal('-5.00')
        )
        with self.assertRaises(ValidationError):
            profile.full_clean()


class InvestmentOpportunityBasicTests(TestCase):
    """Basic tests for InvestmentOpportunity model."""

    def setUp(self):
        self.user = User.objects.create_user(username='investuser', password='pass')

    def test_investment_opportunity_creation(self):
        """Test creating an investment opportunity."""
        opp = InvestmentOpportunity.objects.create(
            business=self.user,
            title='Tech Startup Investment',
            description='Invest in our tech startup',
            amount_seeking=Decimal('100000.00'),
            minimum_investment=Decimal('5000.00'),
            equity_percentage=Decimal('10.00'),
            industry='Technology'
        )
        self.assertEqual(opp.title, 'Tech Startup Investment')
        self.assertEqual(opp.amount_seeking, Decimal('100000.00'))

    def test_investment_opportunity_str_representation(self):
        """Test investment opportunity string representation."""
        opp = InvestmentOpportunity.objects.create(
            business=self.user,
            title='My Investment',
            description='Description',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Tech'
        )
        self.assertEqual(str(opp), 'My Investment')


class InvestmentOpportunitySlugTests(TestCase):
    """Tests for investment opportunity slug generation."""

    def setUp(self):
        self.user = User.objects.create_user(username='sluguser', password='pass')

    def test_slug_auto_generated(self):
        """Test slug is automatically generated."""
        opp = InvestmentOpportunity.objects.create(
            business=self.user,
            title='My Great Opportunity',
            description='Description',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Tech'
        )
        self.assertEqual(opp.slug, 'my-great-opportunity')

    def test_slug_unique_on_duplicate_title(self):
        """Test unique slug is generated for duplicate titles."""
        opp1 = InvestmentOpportunity.objects.create(
            business=self.user,
            title='Same Title',
            description='First',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Tech'
        )
        opp2 = InvestmentOpportunity.objects.create(
            business=self.user,
            title='Same Title',
            description='Second',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Tech'
        )
        self.assertNotEqual(opp1.slug, opp2.slug)
        self.assertTrue(opp2.slug.startswith('same-title'))


class InvestmentOpportunityIncrementViewsTests(TestCase):
    """Tests for opportunity views increment."""

    def setUp(self):
        self.user = User.objects.create_user(username='viewsuser', password='pass')
        self.opp = InvestmentOpportunity.objects.create(
            business=self.user,
            title='Test Opportunity',
            description='Description',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Tech'
        )

    def test_increment_views(self):
        """Test incrementing opportunity views."""
        self.assertEqual(self.opp.views, 0)
        self.opp.increment_views()
        self.opp.refresh_from_db()
        self.assertEqual(self.opp.views, 1)


class InvestmentOpportunityStatusTests(TestCase):
    """Tests for investment opportunity status."""

    def setUp(self):
        self.user = User.objects.create_user(username='statususer', password='pass')

    def test_default_status_open(self):
        """Test default status is open."""
        opp = InvestmentOpportunity.objects.create(
            business=self.user,
            title='Test Opportunity',
            description='Description',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Tech'
        )
        self.assertEqual(opp.status, 'open')

    def test_status_closed(self):
        """Test setting status to closed."""
        opp = InvestmentOpportunity.objects.create(
            business=self.user,
            title='Test Opportunity',
            description='Description',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Tech',
            status='closed'
        )
        self.assertEqual(opp.status, 'closed')

    def test_status_funded(self):
        """Test setting status to funded."""
        opp = InvestmentOpportunity.objects.create(
            business=self.user,
            title='Test Opportunity',
            description='Description',
            amount_seeking=Decimal('50000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('5.00'),
            industry='Tech',
            status='funded'
        )
        self.assertEqual(opp.status, 'funded')


class JobOpportunityBasicTests(TestCase):
    """Basic tests for JobOpportunity model."""

    def setUp(self):
        self.user = User.objects.create_user(username='jobuser', password='pass')

    def test_job_opportunity_creation(self):
        """Test creating a job opportunity."""
        job = JobOpportunity.objects.create(
            business=self.user,
            title='Software Developer',
            description='Join our team',
            requirements='Python, Django',
            responsibilities='Build web apps',
            location='Remote'
        )
        self.assertEqual(job.title, 'Software Developer')
        self.assertEqual(job.location, 'Remote')

    def test_job_opportunity_str_representation(self):
        """Test job opportunity string representation."""
        job = JobOpportunity.objects.create(
            business=self.user,
            title='Product Manager',
            description='Description',
            requirements='Requirements',
            responsibilities='Responsibilities',
            location='NYC'
        )
        self.assertEqual(str(job), 'Product Manager')


class JobOpportunitySlugTests(TestCase):
    """Tests for job opportunity slug generation."""

    def setUp(self):
        self.user = User.objects.create_user(username='sluguser', password='pass')

    def test_slug_auto_generated(self):
        """Test slug is automatically generated."""
        job = JobOpportunity.objects.create(
            business=self.user,
            title='Senior Developer',
            description='Description',
            requirements='Requirements',
            responsibilities='Responsibilities',
            location='Remote'
        )
        self.assertEqual(job.slug, 'senior-developer')

    def test_slug_unique_on_duplicate_title(self):
        """Test unique slug is generated for duplicate titles."""
        job1 = JobOpportunity.objects.create(
            business=self.user,
            title='Developer',
            description='First',
            requirements='Requirements',
            responsibilities='Responsibilities',
            location='Remote'
        )
        job2 = JobOpportunity.objects.create(
            business=self.user,
            title='Developer',
            description='Second',
            requirements='Requirements',
            responsibilities='Responsibilities',
            location='NYC'
        )
        self.assertNotEqual(job1.slug, job2.slug)


class JobOpportunityIncrementViewsTests(TestCase):
    """Tests for job views increment."""

    def setUp(self):
        self.user = User.objects.create_user(username='viewsuser', password='pass')
        self.job = JobOpportunity.objects.create(
            business=self.user,
            title='Test Job',
            description='Description',
            requirements='Requirements',
            responsibilities='Responsibilities',
            location='Remote'
        )

    def test_increment_views(self):
        """Test incrementing job views."""
        self.assertEqual(self.job.views, 0)
        self.job.increment_views()
        self.job.refresh_from_db()
        self.assertEqual(self.job.views, 1)


class JobOpportunityStatusTests(TestCase):
    """Tests for job opportunity status."""

    def setUp(self):
        self.user = User.objects.create_user(username='statususer', password='pass')

    def test_default_status_open(self):
        """Test default status is open."""
        job = JobOpportunity.objects.create(
            business=self.user,
            title='Test Job',
            description='Description',
            requirements='Requirements',
            responsibilities='Responsibilities',
            location='Remote'
        )
        self.assertEqual(job.status, 'open')

    def test_status_filled(self):
        """Test setting status to filled."""
        job = JobOpportunity.objects.create(
            business=self.user,
            title='Test Job',
            description='Description',
            requirements='Requirements',
            responsibilities='Responsibilities',
            location='Remote',
            status='filled'
        )
        self.assertEqual(job.status, 'filled')


class JobApplicationBasicTests(TestCase):
    """Basic tests for JobApplication model."""

    def setUp(self):
        self.business_user = User.objects.create_user(username='bizuser', password='pass')
        self.applicant_user = User.objects.create_user(username='applicant', password='pass')
        self.job = JobOpportunity.objects.create(
            business=self.business_user,
            title='Test Job',
            description='Description',
            requirements='Requirements',
            responsibilities='Responsibilities',
            location='Remote'
        )

    def test_job_application_creation(self):
        """Test creating a job application."""
        app = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant_user,
            cover_letter='I am interested in this position',
            resume='resume.pdf'
        )
        self.assertEqual(app.job, self.job)
        self.assertEqual(app.applicant, self.applicant_user)

    def test_job_application_str_representation(self):
        """Test job application string representation."""
        app = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant_user,
            cover_letter='Cover letter',
            resume='resume.pdf'
        )
        expected = f'{self.applicant_user.username} -> {self.job.title}'
        self.assertEqual(str(app), expected)


class JobApplicationUniqueConstraintTests(TestCase):
    """Tests for job application unique constraints."""

    def setUp(self):
        self.business_user = User.objects.create_user(username='bizuser', password='pass')
        self.applicant_user = User.objects.create_user(username='applicant', password='pass')
        self.job = JobOpportunity.objects.create(
            business=self.business_user,
            title='Test Job',
            description='Description',
            requirements='Requirements',
            responsibilities='Responsibilities',
            location='Remote'
        )

    def test_unique_application_per_job(self):
        """Test unique application per user per job."""
        JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant_user,
            cover_letter='First application',
            resume='resume.pdf'
        )
        with self.assertRaises(IntegrityError):
            JobApplication.objects.create(
                job=self.job,
                applicant=self.applicant_user,
                cover_letter='Duplicate application',
                resume='resume2.pdf'
            )


class JobApplicationStatusTests(TestCase):
    """Tests for job application status."""

    def setUp(self):
        self.business_user = User.objects.create_user(username='bizuser', password='pass')
        self.applicant_user = User.objects.create_user(username='applicant', password='pass')
        self.job = JobOpportunity.objects.create(
            business=self.business_user,
            title='Test Job',
            description='Description',
            requirements='Requirements',
            responsibilities='Responsibilities',
            location='Remote'
        )

    def test_default_status_pending(self):
        """Test default application status is pending."""
        app = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant_user,
            cover_letter='Cover letter',
            resume='resume.pdf'
        )
        self.assertEqual(app.status, 'pending')

    def test_status_shortlisted(self):
        """Test setting status to shortlisted."""
        app = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant_user,
            cover_letter='Cover letter',
            resume='resume.pdf'
        )
        app.status = 'shortlisted'
        app.save()
        self.assertEqual(app.status, 'shortlisted')

    def test_status_interview(self):
        """Test setting status to interview."""
        app = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant_user,
            cover_letter='Cover letter',
            resume='resume.pdf'
        )
        app.status = 'interview'
        app.save()
        self.assertEqual(app.status, 'interview')

    def test_status_offered(self):
        """Test setting status to offered."""
        app = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant_user,
            cover_letter='Cover letter',
            resume='resume.pdf'
        )
        app.status = 'offered'
        app.save()
        self.assertEqual(app.status, 'offered')

    def test_status_rejected(self):
        """Test setting status to rejected."""
        app = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant_user,
            cover_letter='Cover letter',
            resume='resume.pdf'
        )
        app.status = 'rejected'
        app.save()
        self.assertEqual(app.status, 'rejected')
