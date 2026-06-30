from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import UserProfile, UserGroup  # Adjust imports if UserGroup is in a different app

# Fetch the active User model (CustomerUser in your case)
User = get_user_model()

class UserProfileModelTest(TestCase):
    def setUp(self):
        """Set up a temporary user and profile for testing."""
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword123"
        )
        
        self.profile = UserProfile.objects.create(
            user=self.user,
            position="Software Engineer",
            company="TechCorp",
            national_id_no="12345678"
        )

    def test_profile_creation(self):
        """Test that the profile is created and linked to the user."""
        self.assertEqual(self.profile.user.username, "testuser")
        self.assertEqual(self.profile.position, "Software Engineer")
        self.assertEqual(self.profile.company, "TechCorp")

    def test_profile_defaults(self):
        """Test that the default fields are correctly applied."""
        self.assertEqual(self.profile.section, "A")
        self.assertTrue(self.profile.is_active)
        self.assertTrue(self.profile.laptop_status)
        self.assertEqual(self.profile.image.name, "default.jpg")

    def test_profile_str_method(self):
        """Test the string representation of the model."""
        expected_str = f"{self.user.username} Applicant Profile"
        self.assertEqual(str(self.profile), expected_str)

    def test_profile_related_name(self):
        """Test the reverse lookup we fixed earlier (applicant_profile)."""
        # We can access the profile directly from the user instance
        fetched_profile = self.user.applicant_profile
        self.assertEqual(fetched_profile.position, "Software Engineer")


class UserGroupModelTest(TestCase):
    def setUp(self):
        """Set up temporary users and a group for testing."""
        self.user1 = User.objects.create_user(username="user1", password="pw1", is_active=True)
        self.user2 = User.objects.create_user(username="user2", password="pw2", is_active=False)
        
        self.group = UserGroup.objects.create(
            name="Developers",
            description="Backend and Frontend Devs"
        )
        
        # Add both users to the group
        self.group.members.add(self.user1, self.user2)

    def test_group_creation(self):
        """Test that the group is created correctly."""
        self.assertEqual(self.group.name, "Developers")
        self.assertTrue(self.group.is_active)

    def test_group_str_method(self):
        """Test the string representation of the group."""
        self.assertEqual(str(self.group), "Developers")

    def test_get_member_count(self):
        """
        Test the custom get_member_count method.
        It should only count 'active' users. Since user2 is inactive, 
        the count should be 1.
        """
        self.assertEqual(self.group.members.count(), 2) # Total members
        self.assertEqual(self.group.get_member_count(), 1) # Active members only