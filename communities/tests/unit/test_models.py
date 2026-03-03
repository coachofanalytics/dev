from django.test import TestCase
from django.contrib.auth import get_user_model  # Changed this
from django.utils import timezone
from communities.models import (
    CommunityMember, DirectoryProfile, ForumCategory,
    Post, EventCalendar, ContactMessage, UserProfile,
    UserSettings, UserPreferences
)

# Get the custom user model
User = get_user_model()  # This will get your CustomerUser model

class TestCommunityMemberModel(TestCase):
    """Unit tests for CommunityMember model"""
    
    def test_create_community_member(self):
        """Test creating a CommunityMember with correct defaults"""
        member = CommunityMember.objects.create(
            name="John Doe",
            email="john@example.com",
            profession="Software Engineer"
        )
        
        # Test basic fields
        self.assertEqual(member.name, "John Doe")
        self.assertEqual(member.email, "john@example.com")
        self.assertEqual(member.profession, "Software Engineer")
        
        # Test DEFAULT VALUES from your model
        self.assertEqual(member.region, "Not Specified")  # Default from model
        self.assertTrue(member.is_verified)  # default=True
        self.assertTrue(member.is_public_directory)  # default=True
        self.assertIsNone(member.phone)  # blank=True, null=True
        self.assertIsNone(member.specialization)  # blank=True, null=True
    
    def test_email_uniqueness(self):
        """Test email must be unique"""
        CommunityMember.objects.create(
            name="User 1",
            email="unique@example.com",
            profession="Test"
        )
        
        # Second with same email should fail
        with self.assertRaises(Exception):
            CommunityMember.objects.create(
                name="User 2",
                email="unique@example.com",
                profession="Test"
            )
    
    def test_string_representation(self):
        """Test string representation"""
        member = CommunityMember.objects.create(
            name="Jane Smith",
            email="jane@example.com",
            profession="Doctor"
        )
        
        self.assertEqual(str(member), "Jane Smith - Doctor")
    
    def test_ordering(self):
        """Test model ordering by date_joined descending"""
        # Create members with different dates
        member1 = CommunityMember.objects.create(
            name="First",
            email="first@example.com",
            profession="First"
        )
        
        # Force a time difference by updating the date_joined
        import time
        time.sleep(0.1)
        
        member2 = CommunityMember.objects.create(
            name="Second",
            email="second@example.com",
            profession="Second"
        )
        
        members = list(CommunityMember.objects.all())
        
        # Most recent first (member2 should be first)
        # Debug output
        print(f"Member1 date: {member1.date_joined}")
        print(f"Member2 date: {member2.date_joined}")
        
        self.assertEqual(members[0].id, member2.id)  # Most recent first
        self.assertEqual(members[1].id, member1.id)

class TestDirectoryProfileModel(TestCase):
    """Unit tests for DirectoryProfile model"""
    
    def setUp(self):
        self.member = CommunityMember.objects.create(
            name="Test Member",
            email="test@example.com",
            profession="Test"
        )
    
    def test_create_directory_profile(self):
        """Test creating a DirectoryProfile"""
        profile = DirectoryProfile.objects.create(
            community_member=self.member,
            full_name="Profile Full Name",
            profession="Profile Profession",
            region_city="New York",
            category="tech",
            membership_type="verified",
            expertise_summary="Expert in testing"
        )
        
        # Test fields
        self.assertEqual(profile.full_name, "Profile Full Name")
        self.assertEqual(profile.category, "tech")
        self.assertEqual(profile.membership_type, "verified")
        
        # Test DEFAULT VALUES from your model
        self.assertFalse(profile.is_approved)  # default=False
        self.assertTrue(profile.is_published)  # default=True
    
    def test_save_updates_community_member(self):
        """Test that save() updates the linked CommunityMember"""
        profile = DirectoryProfile.objects.create(
            community_member=self.member,
            full_name="Updated Name",
            profession="Updated Profession",
            region_city="Updated City",
            category="tech",
            expertise_summary="Test"
        )
        
        # Refresh member from database
        self.member.refresh_from_db()
        
        # Should be updated
        self.assertEqual(self.member.name, "Updated Name")
        self.assertEqual(self.member.profession, "Updated Profession")
        self.assertEqual(self.member.region, "Updated City")
    
    def test_category_choices(self):
        """Test category field choices"""
        profile = DirectoryProfile(
            community_member=self.member,
            full_name="Test",
            profession="Test",
            region_city="Test",
            category="tech",  # Valid choice
            expertise_summary="Test"
        )
        
        # Should save without error
        profile.save()
        self.assertEqual(profile.category, "tech")
    
    def test_membership_type_choices(self):
        """Test membership_type field choices"""
        profile = DirectoryProfile.objects.create(
            community_member=self.member,
            full_name="Test",
            profession="Test",
            region_city="Test",
            category="tech",
            membership_type="premium",  # Valid choice
            expertise_summary="Test"
        )
        
        self.assertEqual(profile.membership_type, "premium")

class TestForumModels(TestCase):
    """Unit tests for forum models"""
    
    def test_forum_category(self):
        """Test ForumCategory model"""
        category = ForumCategory.objects.create(
            name="General Discussion",
            slug="general-discussion",
            description="General topics"
        )
        
        self.assertEqual(str(category), "General Discussion")
        self.assertEqual(category.slug, "general-discussion")
    
    def test_post_model(self):
        """Test Post model"""
        category = ForumCategory.objects.create(
            name="Test Category",
            slug="test-category",
            description="Test"
        )
        
        post = Post.objects.create(
            title="Test Post",
            content="Test content",
            category=category
        )
        
        self.assertEqual(str(post), "Test Post")
        self.assertEqual(post.category, category)

class TestEventCalendarModel(TestCase):
    """Unit tests for EventCalendar model"""
    
    def test_event_creation(self):
        """Test creating an event"""
        start = timezone.now()
        end = start + timezone.timedelta(hours=2)
        
        event = EventCalendar.objects.create(
            name="Test Event",
            start_date=start,
            end_date=end,
            location="Test Location",
            description="Test description"
        )
        
        self.assertEqual(str(event), "Test Event")
        self.assertEqual(event.location, "Test Location")
        self.assertLess(event.start_date, event.end_date)

class TestContactMessageModel(TestCase):
    """Unit tests for ContactMessage model"""
    
    def test_contact_message(self):
        """Test ContactMessage model"""
        contact = ContactMessage.objects.create(
            name="Contact Name",
            email="contact@example.com",
            message="Test message"
        )
        
        self.assertIn("Contact Name", str(contact))
        self.assertIn("contact@example.com", str(contact))

class TestUserProfileModels(TestCase):
    """Unit tests for user profile models"""
    
    def setUp(self):
        # Create user based on your CustomerUser model requirements
        # Check what fields your CustomerUser model requires
        try:
            # Try common approaches for custom user models
            self.user = User.objects.create_user(
                email='test@example.com',
                password='testpass123',
                username='testuser'  # Include if your model has username
            )
        except Exception as e:
            # If that fails, try with just email and password
            print(f"Error creating user: {e}")
            self.user = User.objects.create_user(
                email='test@example.com',
                password='testpass123'
            )
    
    def test_user_profile(self):
        """Test UserProfile model"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name="Test User Full Name",
            contact_email="profile@example.com",
            county_city="Test City"
        )
        
        self.assertEqual(str(profile), f"{self.user.username} Profile")
        self.assertEqual(profile.full_name, "Test User Full Name")
    
    def test_user_settings(self):
        """Test UserSettings model"""
        settings = UserSettings.objects.create(
            user=self.user,
            enable_notifications=False,
            enable_2fa=True,
            allow_marketing_emails=False
        )
        
        self.assertEqual(str(settings), f"{self.user.username} Settings")
        self.assertFalse(settings.enable_notifications)
        self.assertTrue(settings.enable_2fa)
    
    def test_user_preferences(self):
        """Test UserPreferences model"""
        preferences = UserPreferences.objects.create(
            user=self.user,
            interest_area="Technology",
            communication_channel="WhatsApp",
            profile_visibility=False
        )
        
        self.assertEqual(str(preferences), f"{self.user.username} Preferences")
        self.assertEqual(preferences.communication_channel, "WhatsApp")
        self.assertEqual(preferences.interest_area, "Technology")
