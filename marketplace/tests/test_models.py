"""
Tests for marketplace models.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from marketplace.models import (
    BusinessProfile,
    InvestmentOpportunity,
    JobOpportunity,
    JobApplication,
    SavedItem,
)


@pytest.mark.django_db
class TestBusinessProfileModel:
    """Tests for BusinessProfile model."""

    def test_create_business_profile(self, create_user):
        """Test creating a business profile with valid data."""
        user = create_user()
        profile = BusinessProfile.objects.create(
            user=user,
            company_name="TechCorp Inc",
            industry="Technology",
            company_size="11-50",
            funding_stage="seed",
        )
        assert profile.company_name == "TechCorp Inc"
        assert profile.industry == "Technology"
        assert profile.company_size == "11-50"
        assert profile.funding_stage == "seed"
        assert profile.profile_views == 0

    def test_business_profile_one_to_one_with_user(self, create_user):
        """Test that BusinessProfile has one-to-one relationship with User."""
        user = create_user()
        BusinessProfile.objects.create(
            user=user, company_name="TechCorp", industry="Technology"
        )

        # Try to create another profile for same user should raise error
        with pytest.raises(IntegrityError):
            BusinessProfile.objects.create(
                user=user, company_name="Another Corp", industry="Finance"
            )

    def test_business_profile_string_representation(self, create_user):
        """Test BusinessProfile __str__ method."""
        user = create_user(username="bizuser")
        profile = BusinessProfile.objects.create(
            user=user, company_name="TechCorp", industry="Technology"
        )
        assert str(profile) == "TechCorp (bizuser)"

    def test_business_profile_increment_views(self, create_user):
        """Test increment_views method increases view count."""
        user = create_user()
        profile = BusinessProfile.objects.create(
            user=user, company_name="TechCorp", industry="Technology"
        )

        assert profile.profile_views == 0
        profile.increment_views()
        assert profile.profile_views == 1
        profile.increment_views()
        assert profile.profile_views == 2

    def test_business_profile_equity_offered_validation(self, create_user):
        """Test equity_offered must be between 0 and 100."""
        user = create_user()
        profile = BusinessProfile.objects.create(
            user=user,
            company_name="TechCorp",
            industry="Technology",
            equity_offered=Decimal("50.00"),
        )
        assert profile.equity_offered == Decimal("50.00")

        # Test validation with invalid value
        profile.equity_offered = Decimal("150.00")
        with pytest.raises(ValidationError):
            profile.full_clean()

    def test_business_profile_default_values(self, create_user):
        """Test BusinessProfile default field values."""
        user = create_user()
        profile = BusinessProfile.objects.create(
            user=user, company_name="TechCorp", industry="Technology"
        )
        assert profile.company_size == "1-10"
        assert profile.funding_stage == "idea"
        assert profile.profile_views == 0


@pytest.mark.django_db
class TestInvestmentOpportunityModel:
    """Tests for InvestmentOpportunity model."""

    def test_create_investment_opportunity(self, create_user):
        """Test creating an investment opportunity."""
        user = create_user()
        opportunity = InvestmentOpportunity.objects.create(
            business=user,
            title="Seed Investment for AI Startup",
            description="Looking for seed investment",
            amount_seeking=Decimal("100000.00"),
            minimum_investment=Decimal("10000.00"),
            equity_percentage=Decimal("15.00"),
            industry="Technology",
        )
        assert opportunity.title == "Seed Investment for AI Startup"
        assert opportunity.amount_seeking == Decimal("100000.00")
        assert opportunity.status == "open"
        assert opportunity.investment_type == "equity"
        assert opportunity.views == 0

    def test_investment_opportunity_auto_slug_generation(self, create_user):
        """Test that slug is automatically generated from title."""
        user = create_user()
        opportunity = InvestmentOpportunity.objects.create(
            business=user,
            title="Seed Investment for AI Startup",
            description="Test",
            amount_seeking=Decimal("100000.00"),
            minimum_investment=Decimal("10000.00"),
            equity_percentage=Decimal("15.00"),
            industry="Technology",
        )
        assert opportunity.slug == "seed-investment-for-ai-startup"

    def test_investment_opportunity_unique_slug_with_duplicate_titles(
        self, create_user
    ):
        """Test that duplicate titles get unique slugs with counter."""
        user = create_user()
        opp1 = InvestmentOpportunity.objects.create(
            business=user,
            title="Great Investment",
            description="Test 1",
            amount_seeking=Decimal("100000.00"),
            minimum_investment=Decimal("10000.00"),
            equity_percentage=Decimal("15.00"),
            industry="Technology",
        )

        opp2 = InvestmentOpportunity.objects.create(
            business=user,
            title="Great Investment",
            description="Test 2",
            amount_seeking=Decimal("200000.00"),
            minimum_investment=Decimal("20000.00"),
            equity_percentage=Decimal("20.00"),
            industry="Technology",
        )

        assert opp1.slug == "great-investment"
        assert opp2.slug == "great-investment-1"

    def test_investment_opportunity_increment_views(self, create_user):
        """Test increment_views method."""
        user = create_user()
        opportunity = InvestmentOpportunity.objects.create(
            business=user,
            title="Test Investment",
            description="Test",
            amount_seeking=Decimal("100000.00"),
            minimum_investment=Decimal("10000.00"),
            equity_percentage=Decimal("15.00"),
            industry="Technology",
        )

        assert opportunity.views == 0
        opportunity.increment_views()
        assert opportunity.views == 1

    def test_investment_opportunity_string_representation(self, create_user):
        """Test __str__ method returns title."""
        user = create_user()
        opportunity = InvestmentOpportunity.objects.create(
            business=user,
            title="Amazing Investment",
            description="Test",
            amount_seeking=Decimal("100000.00"),
            minimum_investment=Decimal("10000.00"),
            equity_percentage=Decimal("15.00"),
            industry="Technology",
        )
        assert str(opportunity) == "Amazing Investment"

    def test_investment_opportunity_equity_percentage_validation(self, create_user):
        """Test equity_percentage must be between 0 and 100."""
        user = create_user()
        opportunity = InvestmentOpportunity.objects.create(
            business=user,
            title="Test",
            description="Test",
            amount_seeking=Decimal("100000.00"),
            minimum_investment=Decimal("10000.00"),
            equity_percentage=Decimal("25.00"),
            industry="Technology",
        )

        # Test invalid value
        opportunity.equity_percentage = Decimal("150.00")
        with pytest.raises(ValidationError):
            opportunity.full_clean()


@pytest.mark.django_db
class TestJobOpportunityModel:
    """Tests for JobOpportunity model."""

    def test_create_job_opportunity(self, create_user):
        """Test creating a job opportunity."""
        user = create_user()
        job = JobOpportunity.objects.create(
            business=user,
            title="Senior Python Developer",
            description="We're looking for a senior Python developer",
            requirements="5+ years Python experience",
            responsibilities="Develop backend systems",
            location="Nairobi, Kenya",
            job_type="full_time",
            experience_level="senior",
        )
        assert job.title == "Senior Python Developer"
        assert job.location == "Nairobi, Kenya"
        assert job.job_type == "full_time"
        assert job.status == "open"
        assert job.views == 0
        assert job.applications_count == 0

    def test_job_opportunity_auto_slug_generation(self, create_user):
        """Test automatic slug generation."""
        user = create_user()
        job = JobOpportunity.objects.create(
            business=user,
            title="Senior Python Developer",
            description="Test",
            requirements="Test",
            responsibilities="Test",
            location="Nairobi",
        )
        assert job.slug == "senior-python-developer"

    def test_job_opportunity_unique_slug_with_duplicates(self, create_user):
        """Test unique slug generation for duplicate titles."""
        user = create_user()
        job1 = JobOpportunity.objects.create(
            business=user,
            title="Software Engineer",
            description="Test 1",
            requirements="Test",
            responsibilities="Test",
            location="Nairobi",
        )

        job2 = JobOpportunity.objects.create(
            business=user,
            title="Software Engineer",
            description="Test 2",
            requirements="Test",
            responsibilities="Test",
            location="Mombasa",
        )

        assert job1.slug == "software-engineer"
        assert job2.slug == "software-engineer-1"

    def test_job_opportunity_increment_views(self, create_user):
        """Test increment_views method."""
        user = create_user()
        job = JobOpportunity.objects.create(
            business=user,
            title="Developer",
            description="Test",
            requirements="Test",
            responsibilities="Test",
            location="Nairobi",
        )

        assert job.views == 0
        job.increment_views()
        assert job.views == 1

    def test_job_opportunity_remote_option(self, create_user):
        """Test remote_option boolean field."""
        user = create_user()
        job = JobOpportunity.objects.create(
            business=user,
            title="Remote Developer",
            description="Test",
            requirements="Test",
            responsibilities="Test",
            location="Remote",
            remote_option=True,
        )
        assert job.remote_option is True

    def test_job_opportunity_salary_range(self, create_user):
        """Test salary min and max fields."""
        user = create_user()
        job = JobOpportunity.objects.create(
            business=user,
            title="Developer",
            description="Test",
            requirements="Test",
            responsibilities="Test",
            location="Nairobi",
            salary_min=Decimal("50000.00"),
            salary_max=Decimal("80000.00"),
            salary_currency="USD",
        )
        assert job.salary_min == Decimal("50000.00")
        assert job.salary_max == Decimal("80000.00")
        assert job.salary_currency == "USD"

    def test_job_opportunity_string_representation(self, create_user):
        """Test __str__ method."""
        user = create_user()
        job = JobOpportunity.objects.create(
            business=user,
            title="Full Stack Developer",
            description="Test",
            requirements="Test",
            responsibilities="Test",
            location="Nairobi",
        )
        assert str(job) == "Full Stack Developer"


@pytest.mark.django_db
class TestJobApplicationModel:
    """Tests for JobApplication model."""

    def test_create_job_application(self, create_user):
        """Test creating a job application."""
        business_user = create_user(username="business")
        applicant = create_user(username="applicant")

        job = JobOpportunity.objects.create(
            business=business_user,
            title="Developer",
            description="Test",
            requirements="Test",
            responsibilities="Test",
            location="Nairobi",
        )

        application = JobApplication.objects.create(
            job=job,
            applicant=applicant,
            cover_letter="I am interested in this position",
            resume="resumes/test.pdf",
        )

        assert application.job == job
        assert application.applicant == applicant
        assert application.status == "pending"
        assert application.cover_letter == "I am interested in this position"

    def test_job_application_unique_together_constraint(self, create_user):
        """Test that user cannot apply to same job twice."""
        business_user = create_user(username="business")
        applicant = create_user(username="applicant")

        job = JobOpportunity.objects.create(
            business=business_user,
            title="Developer",
            description="Test",
            requirements="Test",
            responsibilities="Test",
            location="Nairobi",
        )

        JobApplication.objects.create(
            job=job,
            applicant=applicant,
            cover_letter="First application",
            resume="resumes/test1.pdf",
        )

        # Try to apply again should raise error
        with pytest.raises(IntegrityError):
            JobApplication.objects.create(
                job=job,
                applicant=applicant,
                cover_letter="Second application",
                resume="resumes/test2.pdf",
            )

    def test_job_application_string_representation(self, create_user):
        """Test __str__ method."""
        business_user = create_user(username="business")
        applicant = create_user(username="john_doe")

        job = JobOpportunity.objects.create(
            business=business_user,
            title="Python Developer",
            description="Test",
            requirements="Test",
            responsibilities="Test",
            location="Nairobi",
        )

        application = JobApplication.objects.create(
            job=job,
            applicant=applicant,
            cover_letter="Test",
            resume="resumes/test.pdf",
        )

        assert str(application) == "john_doe -> Python Developer"

    def test_job_application_status_choices(self, create_user):
        """Test different status choices."""
        business_user = create_user(username="business")
        applicant = create_user(username="applicant")

        job = JobOpportunity.objects.create(
            business=business_user,
            title="Developer",
            description="Test",
            requirements="Test",
            responsibilities="Test",
            location="Nairobi",
        )

        application = JobApplication.objects.create(
            job=job,
            applicant=applicant,
            cover_letter="Test",
            resume="resumes/test.pdf",
        )

        # Test different status transitions
        assert application.status == "pending"

        application.status = "reviewing"
        application.save()
        assert application.status == "reviewing"

        application.status = "shortlisted"
        application.save()
        assert application.status == "shortlisted"


@pytest.mark.django_db
class TestSavedItemModel:
    """Tests for SavedItem model."""

    def test_save_investment_opportunity(self, create_user):
        """Test saving an investment opportunity."""
        user = create_user()
        business_user = create_user(username="business")

        opportunity = InvestmentOpportunity.objects.create(
            business=business_user,
            title="Test Investment",
            description="Test",
            amount_seeking=Decimal("100000.00"),
            minimum_investment=Decimal("10000.00"),
            equity_percentage=Decimal("15.00"),
            industry="Technology",
        )

        content_type = ContentType.objects.get_for_model(InvestmentOpportunity)
        saved_item = SavedItem.objects.create(
            user=user,
            content_type=content_type,
            object_id=opportunity.id,
            note="Interesting opportunity",
        )

        assert saved_item.user == user
        assert saved_item.content_object == opportunity
        assert saved_item.note == "Interesting opportunity"

    def test_save_job_opportunity(self, create_user):
        """Test saving a job opportunity."""
        user = create_user()
        business_user = create_user(username="business")

        job = JobOpportunity.objects.create(
            business=business_user,
            title="Developer",
            description="Test",
            requirements="Test",
            responsibilities="Test",
            location="Nairobi",
        )

        content_type = ContentType.objects.get_for_model(JobOpportunity)
        saved_item = SavedItem.objects.create(
            user=user, content_type=content_type, object_id=job.id
        )

        assert saved_item.content_object == job

    def test_saved_item_unique_together_constraint(self, create_user):
        """Test that user cannot save same item twice."""
        user = create_user()
        business_user = create_user(username="business")

        opportunity = InvestmentOpportunity.objects.create(
            business=business_user,
            title="Test Investment",
            description="Test",
            amount_seeking=Decimal("100000.00"),
            minimum_investment=Decimal("10000.00"),
            equity_percentage=Decimal("15.00"),
            industry="Technology",
        )

        content_type = ContentType.objects.get_for_model(InvestmentOpportunity)

        SavedItem.objects.create(
            user=user, content_type=content_type, object_id=opportunity.id
        )

        # Try to save same item again should raise error
        with pytest.raises(IntegrityError):
            SavedItem.objects.create(
                user=user, content_type=content_type, object_id=opportunity.id
            )

    def test_saved_item_string_representation(self, create_user):
        """Test __str__ method."""
        user = create_user(username="john")
        business_user = create_user(username="business")

        job = JobOpportunity.objects.create(
            business=business_user,
            title="Senior Developer",
            description="Test",
            requirements="Test",
            responsibilities="Test",
            location="Nairobi",
        )

        content_type = ContentType.objects.get_for_model(JobOpportunity)
        saved_item = SavedItem.objects.create(
            user=user, content_type=content_type, object_id=job.id
        )

        assert "john saved" in str(saved_item)
        assert "Senior Developer" in str(saved_item)
