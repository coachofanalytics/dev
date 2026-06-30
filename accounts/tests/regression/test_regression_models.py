from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from accounts.models import UserProfile, UserGroup

User = get_user_model()

class AccountsRegressionTest(TestCase):
    def setUp(self):
        """Set up initial data for our edge-case testing."""
        self.user = User.objects.create_user(
            username="regression_user", 
            password="testpassword123"
        )
        
        self.profile = UserProfile.objects.create(
            user=self.user,
            position="QA Tester"
        )
        
        self.group = UserGroup.objects.create(
            name="Alpha Team",
            description="The first team."
        )

    def test_unique_group_name_enforced(self):
        """
        Regression Test: Ensure the 'unique=True' constraint on UserGroup name remains intact.
        If someone accidentally removes 'unique=True' in models.py, this test will fail.
        """
        # We expect the database to throw an error when we try to make a duplicate
        with self.assertRaises(IntegrityError):
            UserGroup.objects.create(
                name="Alpha Team", # Duplicate name!
                description="A copycat team."
            )

    def test_cascade_delete_user_removes_profile(self):
        """
        Regression Test: Ensure on_delete=models.CASCADE is strictly enforced.
        If a user is deleted, their profile must vanish too to prevent orphaned data.
        """
        # Delete the user
        self.user.delete()
        
        # Try to find the profile - it should no longer exist
        profile_exists = UserProfile.objects.filter(position="QA Tester").exists()
        self.assertFalse(profile_exists, "Profile was not deleted when the User was deleted!")

    def test_optional_fields_allow_null(self):
        """
        Regression Test: Ensure that optional fields (like linkedin, company) 
        are still allowed to be blank. If a developer accidentally makes them 
        required, this will catch it.
        """
        try:
            # Creating a profile with ONLY the required user field
            minimal_profile = UserProfile.objects.create(
                user=User.objects.create_user(username="minimal_user", password="123")
            )
            # If it succeeds, the test passes
            self.assertIsNone(minimal_profile.company)
            self.assertEqual(minimal_profile.section, "A") # Checking default
        except Exception as e:
            self.fail(f"Profile creation failed on optional fields: {e}")