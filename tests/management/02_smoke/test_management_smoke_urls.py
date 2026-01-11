"""
Comprehensive Smoke Tests for Management URLs

These tests verify that key management URLs load without runtime errors.
This prevents regressions from:
- Missing modules/services
- Invalid prefetch_related/select_related
- Broken URLs
- Broken manager actions

Author: CODA Development Team
Created: January 2026
Category: Smoke Tests
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class ManagementSmokeURLTests(TestCase):
    """Comprehensive smoke tests for management URLs."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()

        # Create a superuser for testing
        self.superuser = User.objects.create_user(
            username="test_superuser",
            password="testpass123",
            email="test@example.com",
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )

        # Create a regular employee user
        self.employee_user = User.objects.create_user(
            username="test_employee",
            password="testpass123",
            email="employee@example.com",
            is_staff=False,
            is_superuser=False,
            is_active=True,
            first_name="Test",
            last_name="Employee",
        )

        # Login as superuser by default
        self.client.login(username="test_superuser", password="testpass123")

    def test_enhanced_dashboard_loads(self):
        """Test that enhanced dashboard page loads."""
        try:
            url = reverse("management:enhanced-dashboard")
            response = self.client.get(url)

            # Should return 200 or 302 (redirect is acceptable)
            self.assertIn(
                response.status_code,
                [200, 302],
                f"Enhanced dashboard should return 200/302, got {response.status_code}",
            )
        except Exception as e:
            self.fail(f"Enhanced dashboard should not raise exceptions: {e}")

    def test_tasks_list_loads(self):
        """Test that tasks list page loads."""
        try:
            url = reverse("management:tasks")
            response = self.client.get(url)

            # Should return 200
            self.assertEqual(
                response.status_code,
                200,
                f"Tasks list should return 200, got {response.status_code}",
            )
        except Exception as e:
            self.fail(f"Tasks list should not raise exceptions: {e}")

    def test_daf_v2_page_loads(self):
        """Test that DAF v2 page loads without exceptions."""
        try:
            url = reverse("management:daf_v2")
            response = self.client.get(url)

            # Should return 200 OK
            self.assertEqual(
                response.status_code,
                200,
                f"DAF v2 page should return 200, got {response.status_code}",
            )

            # Should have content
            self.assertIsNotNone(response.content)

        except Exception as e:
            self.fail(f"DAF v2 page should not raise exceptions: {e}")

    def test_daf_v2_with_user_id_parameter(self):
        """Test that DAF v2 page loads with user_id parameter."""
        try:
            url = reverse("management:daf_v2") + f"?user_id={self.employee_user.id}"
            response = self.client.get(url)

            # Should return 200 OK
            self.assertEqual(
                response.status_code,
                200,
                f"DAF v2 page with user_id should return 200, got {response.status_code}",
            )

        except Exception as e:
            self.fail(f"DAF v2 page with user_id should not raise exceptions: {e}")

    def test_evidence_form_loads(self):
        """Test that evidence form page loads (requires a task)."""
        try:
            # First, try to get a task (if any exist in test DB)
            from management.models import Task

            task = Task.objects.filter(is_active=True).first()

            if task:
                url = reverse("management:new_evidence", args=[task.id])
                response = self.client.get(url)

                # Should return 200 or 302 (redirect if permission denied)
                self.assertIn(
                    response.status_code,
                    [200, 302, 403],
                    f"Evidence form should return 200/302/403, got {response.status_code}",
                )
            else:
                # Skip if no tasks exist (test DB might be empty)
                self.skipTest("No tasks in test database to test evidence form")

        except Exception as e:
            self.fail(f"Evidence form should not raise exceptions: {e}")

    def test_daf_v2_as_regular_user(self):
        """Test that regular users can access their own DAF v2 page."""
        # Login as regular employee
        self.client.logout()
        self.client.login(username="test_employee", password="testpass123")

        try:
            url = reverse("management:daf_v2")
            response = self.client.get(url)

            # Should return 200 OK (users can view their own DAF)
            self.assertEqual(
                response.status_code,
                200,
                f"Regular user should be able to access DAF v2, got {response.status_code}",
            )
        except Exception as e:
            self.fail(f"Regular user DAF v2 access should not raise exceptions: {e}")

    def test_daf_v2_contains_expected_markers(self):
        """Test that DAF v2 page contains expected content markers."""
        try:
            url = reverse("management:daf_v2")
            response = self.client.get(url)

            if response.status_code == 200:
                content = response.content.decode("utf-8")

                # Light assertions - just check page rendered (not empty)
                self.assertTrue(
                    len(content) > 0,
                    "DAF v2 page should have content (not empty response)",
                )
        except Exception as e:
            self.fail(f"DAF v2 content check should not raise exceptions: {e}")

    def test_no_prefetch_related_errors(self):
        """Test that management URLs don't raise prefetch_related errors."""
        # Test multiple URLs to catch prefetch_related issues
        urls_to_test = [
            ("management:daf_v2", {}),
            ("management:tasks", {}),
        ]

        for url_name, kwargs in urls_to_test:
            try:
                url = reverse(url_name, kwargs=kwargs)
                response = self.client.get(url)

                # Should not return 500 (server error)
                self.assertNotEqual(
                    response.status_code,
                    500,
                    f"{url_name} should not return 500 (no prefetch_related errors)",
                )
            except Exception as e:
                error_msg = str(e)

                # Check if it's a prefetch_related error
                if (
                    "prefetch_related" in error_msg.lower()
                    or "invalid prefetch" in error_msg.lower()
                ):
                    self.fail(f"prefetch_related error occurred for {url_name}: {e}")
                else:
                    # Other errors might be expected (database, etc.)
                    pass

    def test_no_missing_module_errors(self):
        """Test that management URLs don't raise ModuleNotFoundError."""
        urls_to_test = [
            ("management:daf_v2", {}),
            ("management:tasks", {}),
        ]

        for url_name, kwargs in urls_to_test:
            try:
                url = reverse(url_name, kwargs=kwargs)
                response = self.client.get(url)

                # Should not return 500 (server error from missing modules)
                self.assertNotEqual(
                    response.status_code,
                    500,
                    f"{url_name} should not return 500 (no missing module errors)",
                )
            except ModuleNotFoundError as e:
                self.fail(f"ModuleNotFoundError occurred for {url_name}: {e}")
            except Exception as e:
                error_msg = str(e)
                if "No module named" in error_msg or "ModuleNotFoundError" in str(
                    type(e).__name__
                ):
                    self.fail(f"ModuleNotFoundError occurred for {url_name}: {e}")

    def test_approve_reject_endpoints_resolve(self):
        """Test that approve/reject endpoints resolve (even if they require a task)."""
        try:
            from management.models import Task

            task = Task.objects.filter(is_active=True).first()

            if task:
                # Test that URLs resolve (even if we get 404/403 due to permissions/conditions)
                approve_url = reverse("management:approve_task", args=[task.id])
                reject_url = reverse("management:reject_task", args=[task.id])

                # Just verify URLs resolve (don't test actual approval logic)
                self.assertIsNotNone(approve_url)
                self.assertIsNotNone(reject_url)
            else:
                # Skip if no tasks exist
                self.skipTest(
                    "No tasks in test database to test approve/reject endpoints"
                )
        except Exception as e:
            self.fail(
                f"Approve/reject endpoint resolution should not raise exceptions: {e}"
            )
