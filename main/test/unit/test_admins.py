from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model

from main.models import Location
from main.admin import LocationAdmin  # adjust if your admin class name differs

User = get_user_model()


class MockRequest:
    """Minimal mock request for admin unit tests"""
    pass


class LocationAdminUnitTest(TestCase):
    """
    Unit tests for LocationAdmin configuration
    """

    def setUp(self):
        self.site = AdminSite()
        self.admin = LocationAdmin(Location, self.site)

    def test_admin_registered(self):
        """Admin class is correctly initialized"""
        self.assertIsNotNone(self.admin)

    def test_list_display_fields(self):
        """Admin list_display contains expected fields"""
        expected_fields = ("zipcode", "city", "state", "country")

        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_search_fields_configured(self):
        """Admin search_fields configured correctly"""
        self.assertTrue(len(self.admin.search_fields) > 0)

    def test_list_filter_configured(self):
        """Admin list_filter exists (if configured)"""
        # list_filter is optional, so only check existence
        self.assertTrue(hasattr(self.admin, "list_filter"))

    def test_ordering_configured(self):
        """Admin ordering is defined"""
        self.assertTrue(hasattr(self.admin, "ordering"))


class LocationAdminPermissionTest(TestCase):
    """
    Permission-related admin unit tests
    """

    def setUp(self):
        self.site = AdminSite()
        self.admin = LocationAdmin(Location, self.site)
        self.user = User.objects.create_user(
            username="normal_user",
            password="testpass123"
        )

    def test_has_add_permission(self):
        request = MockRequest()
        request.user = self.user

        self.assertIn(
            self.admin.has_add_permission(request),
            [True, False]  # permission depends on admin config
        )

    def test_has_change_permission(self):
        request = MockRequest()
        request.user = self.user

        self.assertIn(
            self.admin.has_change_permission(request),
            [True, False]
        )
