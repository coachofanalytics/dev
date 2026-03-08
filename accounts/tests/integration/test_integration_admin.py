from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.admin.sites import site

from accounts.models import LoginHistory,Department

User = get_user_model()


class LoginHistoryAdminIntegrationTest(TestCase):
    """
    Integration tests for LoginHistory admin.
    Uses DB + HTTP client.
    """

    def setUp(self):
        self.client = Client()

        self.admin_user = User.objects.create_superuser(
            username="admin_user",
            email="admin@test.com",
            password="adminpass123"
        )

        self.normal_user = User.objects.create_user(
            username="normal_user",
            email="user@test.com",
            password="userpass123"
        )

        self.login_history = LoginHistory.objects.create(
            user=self.normal_user,
            ip_address="127.0.0.1",
            user_agent="Integration Admin Test"
        )

    def test_model_is_registered_in_admin(self):
        """Integration: model is registered in admin site"""
        self.assertIn(LoginHistory, site._registry)

    def test_admin_changelist_page_loads(self):
        """Integration: admin changelist loads for superuser"""
        self.client.login(username="admin_user", password="adminpass123")

        url = reverse("admin:accounts_loginhistory_changelist")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.normal_user.username)

    def test_admin_change_page_loads(self):
        """Integration: admin change page loads"""
        self.client.login(username="admin_user", password="adminpass123")

        url = reverse(
            "admin:accounts_loginhistory_change",
            args=[self.login_history.id]
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_non_admin_user_cannot_access_admin(self):
        """Security: non-admin users must be blocked"""
        self.client.login(username="normal_user", password="userpass123")

        url = reverse("admin:accounts_loginhistory_changelist")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)  # redirect to login





from django.contrib import admin



@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("slug", "is_featured", "is_active")
    list_filter = ("is_featured", "is_active")
    search_fields = ("slug", "description")
    ordering = ("slug",)



































