from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.admin.sites import site

from accounts.models import LoginHistory

User = get_user_model()


from django.contrib import admin
class LoginHistoryAdminIntegrationTest(TestCase):
    """
    Integration tests for LoginHistory admin configuration.
    """

    def setUp(self):
        self.client = Client()

        # Create superuser
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="adminpass123"
        )

        # Normal user
        self.user = User.objects.create_user(
            username="user1",
            email="user1@test.com",
            password="userpass123"
        )

        self.client.login(username="admin", password="adminpass123")

        self.history = LoginHistory.objects.create(
            user=self.user,
            ip_address="127.0.0.1",
            user_agent="Admin Test Browser"
        )

    def test_login_history_is_registered_in_admin(self):
        """
        Admin: model must be registered
        """
        self.assertIn(LoginHistory, site._registry)

    def test_login_history_admin_list_page_loads(self):
        """
        Admin: changelist page loads successfully
        """
        url = reverse("admin:accounts_loginhistory_changelist")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_login_history_admin_detail_page_loads(self):
        """
        Admin: detail page loads successfully
        """
        url = reverse(
            "admin:accounts_loginhistory_change",
            args=[self.history.id],
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login History")

    def test_non_admin_user_cannot_access_admin(self):
        """
        Security regression: non-admin must not access admin
        """
        self.client.logout()
        self.client.login(username="user1", password="userpass123")

        url = reverse("admin:accounts_loginhistory_changelist")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)  # Redirect to login


from django.contrib import admin



class TrackerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "employee",
        "category",
        "sub_category",
        "plan",
        "login_date",
        "start_time",
        "duration",
        "time",
    )

    list_filter = (
        "category",
        "sub_category",
        "plan",
        "login_date",
    )

    search_fields = (
        "employee",
        "category",
        "sub_category",
        "plan",
    )

    ordering = ("-login_date",)

    readonly_fields = ("login_date",)

    fieldsets = (
        ("Task Information", {
            "fields": (
                "category",
                "sub_category",
                "plan",
            )
        }),
        ("Employee Information", {
            "fields": (
                "employee",
                "empname",
                "author",
            )
        }),
        ("Time Tracking", {
            "fields": (
                "login_date",
                "start_time",
                "duration",
                "time",
            )
        }),
    )
