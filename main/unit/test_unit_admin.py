from django.test import TestCase
from django.contrib.admin.sites import AdminSite

from main.models import ServiceCategory
from main.admin import ServiceCategoryAdmin


class ServiceCategoryAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.category = ServiceCategory.objects.create(
            service=101,
            name="Data Analytics Training",
            description="Testing admin registration"
        )
        self.admin = ServiceCategoryAdmin(ServiceCategory, self.site)

    def test_admin_list_display(self):
        """Admin should include key fields in list_display"""
        self.assertIn("name", self.admin.list_display)
        self.assertIn("slug", self.admin.list_display)
        self.assertIn("is_active", self.admin.list_display)
        self.assertIn("is_featured", self.admin.list_display)

    def test_admin_search_fields(self):
        """Admin should have search_fields configured"""
        self.assertIn("name", self.admin.search_fields)
        self.assertIn("slug", self.admin.search_fields)

    def test_admin_list_filter(self):
        """Admin should include list filters"""
        self.assertIn("is_active", self.admin.list_filter)
        self.assertIn("is_featured", self.admin.list_filter)
