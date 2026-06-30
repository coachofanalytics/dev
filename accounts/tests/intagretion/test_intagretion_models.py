from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import UserProfile, UserGroup

User = get_user_model()

class AccountsDatabaseIntegrationTest(TestCase):
    def setUp(self):
        """Set up the foundational data needed for the integration scenario."""
        # Create a group that will exist before users join
        self.group = UserGroup.objects.create(
            name="Engineering Department", 
            description="All software and QA engineers."
        )

    def test_full_user_onboarding_flow(self):
        """
        Integration Test: 
        Verify that a User, a UserProfile, and a UserGroup can be linked 
        together and queried from any direction.
        """
        
        # Step 1: A new user registers
        user = User.objects.create_user(
            username="jane_integration", 
            password="securepassword123",
            email="jane@example.com"
        )
        
        # Step 2: The system creates a profile for them
        profile = UserProfile.objects.create(
            user=user,
            position="Backend Developer",
            company="DC48K"
        )
        
        # Step 3: The admin adds the user to a specific group
        self.group.members.add(user)

        # --- The Assertions (Checking the "Glue") ---

        # 1. Check Reverse Lookup: Can the User find their Profile?
        # (This uses the 'applicant_profile' related_name we fixed earlier)
        self.assertEqual(user.applicant_profile.position, "Backend Developer")
        
        # 2. Check Reverse Lookup: Can the User see what Groups they are in?
        # (This uses the 'custom_user_groups' related_name from the UserGroup model)
        self.assertIn(self.group, user.custom_user_groups.all())
        
        # 3. Check Forward Lookup: Can the Group see the new User?
        self.assertIn(user, self.group.members.all())
        
        # 4. Check Custom Method: Does the group count correctly update?
        self.assertEqual(self.group.get_member_count(), 1)