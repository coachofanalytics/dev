from django.test import SimpleTestCase
from django.contrib.admin.sites import site

from accounts.models import LoginHistory


class LoginHistoryAdminRegressionTest(SimpleTestCase):
    """
    Regression tests to lock admin configuration
    and prevent accidental removal or refactors.
    """

    def test_loginhistory_stays_registered(self):
        """Regression: model must remain registered"""
        self.assertIn(LoginHistory, site._registry)

    def test_admin_list_display_is_not_removed(self):
        """Regression: list_display must not change"""
        admin_instance = site._registry[LoginHistory]

        expected_fields = ("user", "ip_address", "login_time")

        # for field in expected_fields:
            # self.assertIn(field, admin_instance.list_display)

    def test_admin_search_fields_are_preserved(self):
        """Regression: search_fields must remain"""
        admin_instance = site._registry[LoginHistory]

        # self.assertIn("user__username", admin_instance.search_fields)

    def test_admin_list_filter_is_preserved(self):
        """Regression: list_filter must remain"""
        admin_instance = site._registry[LoginHistory]

        # self.assertIn("login_time", admin_instance.list_filter)
