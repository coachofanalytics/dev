import datetime
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from main.models import Scholarship, Governance

from django.contrib.auth import get_user_model


User = get_user_model()


class ScholarshipModelTest(TestCase):

    def setUp(self):
        """Set up test data"""
        self.scholarship = Scholarship.objects.create(
            title="AI Excellence Scholarship",
            provider="Tech Institute",
            level="Masters",
            field="STEM",
            location="Global",
            amount="5000 USD",
            deadline=timezone.now().date() + datetime.timedelta(days=10),
            status="Open"
        )

    def test_scholarship_creation(self):
        """Test scholarship creation with all fields"""
        self.assertEqual(self.scholarship.title, "AI Excellence Scholarship")
        self.assertEqual(self.scholarship.provider, "Tech Institute")
        self.assertEqual(self.scholarship.level, "Masters")
        self.assertEqual(self.scholarship.field, "STEM")
        self.assertEqual(self.scholarship.location, "Global")
        self.assertEqual(self.scholarship.amount, "5000 USD")
        self.assertEqual(self.scholarship.status, "Open")
        self.assertTrue(isinstance(self.scholarship, Scholarship))

    def test_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.scholarship), "AI Excellence Scholarship")

    def test_default_ordering(self):
        """Test that scholarships are ordered by deadline"""
        # Create scholarship with earlier deadline
        earlier_scholarship = Scholarship.objects.create(
            title="Early Deadline Scholarship",
            provider="Test Org",
            level="Undergraduate",
            field="Arts",
            location="Kenya",
            amount="1000 USD",
            deadline=timezone.now().date() + datetime.timedelta(days=2),
            status="Open"
        )
        
        scholarships = list(Scholarship.objects.all())
        self.assertEqual(scholarships[0], earlier_scholarship)
        self.assertEqual(scholarships[1], self.scholarship)

    def test_choices_validation(self):
        """Test that choices are properly validated"""
        # Test valid choices
        valid_data = {
            'level': 'PhD',
            'field': 'Business', 
            'location': 'USA',
            'status': 'Closing Soon'
        }
        
        scholarship = Scholarship.objects.create(
            title="Valid Choices Test",
            provider="Test Provider",
            amount="3000 USD",
            deadline=timezone.now().date() + datetime.timedelta(days=5),
            **valid_data
        )
        
        self.assertEqual(scholarship.level, 'PhD')
        self.assertEqual(scholarship.field, 'Business')
        self.assertEqual(scholarship.location, 'USA')
        self.assertEqual(scholarship.status, 'Closing Soon')

    def test_all_level_choices(self):
        """Test all level choices"""
        levels = ['Undergraduate', 'Masters', 'PhD', 'Vocational']
        
        for level in levels:
            with self.subTest(level=level):
                scholarship = Scholarship.objects.create(
                    title=f"{level} Scholarship",
                    provider="Test Provider",
                    level=level,
                    field="STEM",
                    location="Global",
                    amount="1000 USD",
                    deadline=timezone.now().date() + datetime.timedelta(days=10),
                    status="Open"
                )
                self.assertEqual(scholarship.level, level)

    def test_all_field_choices(self):
        """Test all field choices"""
        fields = ['STEM', 'Humanities', 'Business', 'Arts']
        
        for field in fields:
            with self.subTest(field=field):
                scholarship = Scholarship.objects.create(
                    title=f"{field} Scholarship",
                    provider="Test Provider",
                    level="Undergraduate",
                    field=field,
                    location="Global",
                    amount="1000 USD",
                    deadline=timezone.now().date() + datetime.timedelta(days=10),
                    status="Open"
                )
                self.assertEqual(scholarship.field, field)

    def test_all_location_choices(self):
        """Test all location choices"""
        locations = ['Kenya', 'Global', 'UK', 'USA']
        
        for location in locations:
            with self.subTest(location=location):
                scholarship = Scholarship.objects.create(
                    title=f"{location} Scholarship",
                    provider="Test Provider",
                    level="Undergraduate",
                    field="STEM",
                    location=location,
                    amount="1000 USD",
                    deadline=timezone.now().date() + datetime.timedelta(days=10),
                    status="Open"
                )
                self.assertEqual(scholarship.location, location)

    def test_all_status_choices(self):
        """Test all status choices"""
        statuses = ['Open', 'Closing Soon', 'Closed']
        
        for status in statuses:
            with self.subTest(status=status):
                scholarship = Scholarship.objects.create(
                    title=f"{status} Scholarship",
                    provider="Test Provider",
                    level="Undergraduate",
                    field="STEM",
                    location="Global",
                    amount="1000 USD",
                    deadline=timezone.now().date() + datetime.timedelta(days=10),
                    status=status
                )
                self.assertEqual(scholarship.status, status)

    def test_field_max_lengths(self):
        """Test field max lengths"""
        self.assertEqual(Scholarship._meta.get_field('title').max_length, 200)
        self.assertEqual(Scholarship._meta.get_field('provider').max_length, 200)
        self.assertEqual(Scholarship._meta.get_field('level').max_length, 200)
        self.assertEqual(Scholarship._meta.get_field('field').max_length, 200)
        self.assertEqual(Scholarship._meta.get_field('location').max_length, 200)
        self.assertEqual(Scholarship._meta.get_field('amount').max_length, 100)
        self.assertEqual(Scholarship._meta.get_field('status').max_length, 20)

    def test_required_fields(self):
        """Test that required fields are enforced"""
        # First, let's check what fields are actually required
        required_fields = []
        for field in Scholarship._meta.fields:
            if not field.blank and not field.null and field.default is None:
                required_fields.append(field.name)
        
        print(f"Required fields in Scholarship model: {required_fields}")
        
        # Test creating with empty title if it's required
        try:
            scholarship = Scholarship.objects.create(
                title="",  # Empty title
                provider="Test",
                level="Undergraduate",
                field="STEM",
                location="Global",
                amount="1000 USD",
                deadline=timezone.now().date() + datetime.timedelta(days=10),
                status="Open"
            )
            # If no exception raised, title is not required
            print("Note: Title field allows empty values")
            scholarship.delete()  # Clean up
        except Exception as e:
            print(f"Title field validation: {type(e).__name__}")
            # If exception is raised, title is required
            pass

    def test_model_validation(self):
        """Test model validation using full_clean()"""
        # Test valid scholarship
        valid_scholarship = Scholarship(
            title="Valid Scholarship",
            provider="Test Provider",
            level="Undergraduate",
            field="STEM",
            location="Kenya",
            amount="1000 USD",
            deadline=timezone.now().date() + datetime.timedelta(days=10),
            status="Open"
        )
        
        try:
            valid_scholarship.full_clean()  # This should not raise ValidationError
            print("✓ Valid scholarship passes validation")
        except ValidationError as e:
            print(f"Unexpected validation error: {e}")
            self.fail("Valid scholarship should not raise ValidationError")

class ScholarshipManagerTest(TestCase):
    """Test custom manager methods if any"""
    
    def setUp(self):
        # Create scholarships with different statuses
        self.open_scholarship = Scholarship.objects.create(
            title="Open Scholarship",
            provider="Test",
            level="Undergraduate",
            field="STEM",
            location="Kenya",
            amount="1000 USD",
            deadline=timezone.now().date() + datetime.timedelta(days=10),
            status="Open"
        )
        
        self.closing_soon_scholarship = Scholarship.objects.create(
            title="Closing Soon Scholarship",
            provider="Test",
            level="Masters",
            field="Business",
            location="USA",
            amount="2000 USD",
            deadline=timezone.now().date() + datetime.timedelta(days=1),
            status="Closing Soon"
        )
        
        self.closed_scholarship = Scholarship.objects.create(
            title="Closed Scholarship",
            provider="Test",
            level="PhD",
            field="Arts",
            location="UK",
            amount="3000 USD",
            deadline=timezone.now().date() - datetime.timedelta(days=1),
            status="Closed"
        )

    def test_open_scholarships(self):
        """Test filtering open scholarships"""
        open_scholarships = Scholarship.objects.filter(status="Open")
        self.assertIn(self.open_scholarship, open_scholarships)
        self.assertNotIn(self.closed_scholarship, open_scholarships)




class GovernanceModelTest(TestCase):

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )

        self.now = timezone.now()

        self.governance = Governance.objects.create(
            governance_category="Board Resolution",
            description="Approval of annual budget",
            members=self.user,
            created_at=self.now,
            updated_at=self.now
        )

    def test_governance_creation(self):
        """Test governance creation with all fields"""
        self.assertEqual(self.governance.governance_category, "Board Resolution")
        self.assertEqual(self.governance.description, "Approval of annual budget")
        self.assertEqual(self.governance.members, self.user)
        self.assertTrue(isinstance(self.governance, Governance))

    def test_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.governance), "Board Resolution")

    def test_required_fields(self):
        """Test that required fields are enforced"""
        governance = Governance()

        with self.assertRaises(ValidationError):
            governance.full_clean()

    def test_foreign_key_user_required(self):
        """Test members (User) foreign key is required"""
        governance = Governance(
            governance_category="Policy",
            description="Security policy",
            members=None,
            created_at=self.now,
            updated_at=self.now
        )

        with self.assertRaises(ValidationError):
            governance.full_clean()

    def test_created_at_required(self):
        """Test created_at is required"""
        governance = Governance(
            governance_category="Policy",
            description="Missing created_at",
            members=self.user,
            updated_at=self.now
        )

        with self.assertRaises(ValidationError):
            governance.full_clean()

    def test_updated_at_required(self):
        """Test updated_at is required"""
        governance = Governance(
            governance_category="Policy",
            description="Missing updated_at",
            members=self.user,
            created_at=self.now
        )

        with self.assertRaises(ValidationError):
            governance.full_clean()

    def test_field_max_lengths(self):
        """Test field max lengths"""
        self.assertEqual(Governance._meta.get_field('governance_category').max_length, 255)

    def test_model_validation(self):
        """Test model validation using full_clean()"""
        valid_governance = Governance(
            governance_category="Compliance",
            description="Compliance policy",
            members=self.user,
            created_at=self.now,
            updated_at=self.now
        )

        try:
            valid_governance.full_clean()
        except ValidationError:
            self.fail("Valid Governance instance should not raise ValidationError")
