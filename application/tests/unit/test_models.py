from django.test import TestCase
from django.contrib.auth import get_user_model

from application.models import UserProfile


class UserProfileModelTest(TestCase):
    def setUp(self):
        User = get_user_model()

        username_field = User.USERNAME_FIELD

        user_data = {
            username_field: "testuser@example.com"
            if username_field == "email"
            else "testuser"
        }

        if username_field != "email" and hasattr(User, "email"):
            user_data["email"] = "testuser@example.com"

        self.user = User.objects.create(**user_data)
        self.user.set_password("TestPass123")
        self.user.save()

        self.profile = UserProfile.objects.create(
            user=self.user,
            position="Python Developer",
            description="Test user profile description.",
            company="CODA Analytics",
            linkedin="https://linkedin.com/in/testuser",
            section="A",
            is_active=True,
            laptop_status=True,
            national_id_no="12345678",
            emergency_name="John Mwangi",
            emergency_address="Nairobi, Kenya",
            emergency_citizenship="Kenyan",
            emergency_national_id_no="87654321",
            emergency_phone="07289905233",
            emergency_email="emergency@example.com",
        )

    def test_user_profile_is_created_successfully(self):
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.company, "CODA Analytics")
        self.assertEqual(self.profile.position, "Python Developer")

    def test_user_profile_string_returns_user(self):
        self.assertEqual(str(self.profile), f"{self.user} Applicant Profile")

    def test_user_profile_active_status(self):
        self.assertTrue(self.profile.is_active)

    def test_user_profile_laptop_status(self):
        self.assertTrue(self.profile.laptop_status)

    def test_user_profile_emergency_details(self):
        self.assertEqual(self.profile.emergency_name, "John Mwangi")
        self.assertEqual(self.profile.emergency_phone, "07289905233")
        self.assertEqual(self.profile.emergency_email, "emergency@example.com")

    def test_user_profile_can_be_updated(self):
        self.profile.company = "CODA Technology"
        self.profile.position = "Django Developer"
        self.profile.save()

        updated_profile = UserProfile.objects.get(id=self.profile.id)

        self.assertEqual(updated_profile.company, "CODA Technology")
        self.assertEqual(updated_profile.position, "Django Developer")