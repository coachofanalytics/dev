"""
Integration tests for finance views

Tests view functions, HTTP requests/responses, and template rendering.

Author: CODA Development Team
Created: November 6, 2025
Category: Integration Tests
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Department
from finance.models import BudgetCategory, BudgetRequest

User = get_user_model()


class BudgetRequestFormViewTest(TestCase):
    """Integration tests for the budget request creation flow."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="finance_requester",
            email="finance_requester@test.com",
            password="Password123!",
        )
        self.department = Department.objects.create(
            name=Department.IT,
            description="Information Technology",
            slug="it-department",
            is_active=True,
        )
        self.category = BudgetCategory.objects.create(
            name="Cloud Subscriptions",
            description="Recurring SaaS renewals",
            approval_tier="A",
            auto_approve_enabled=True,
            typical_monthly_amount=Decimal("1000.00"),
            variance_threshold=Decimal("25.00"),
            is_recurring=True,
        )

    def test_post_creates_auto_approved_budget_request(self):
        """Posting valid data should create an auto-approved request and redirect to detail page."""
        self.client.login(username="finance_requester", password="Password123!")

        post_data = {
            "amount": "950.00",
            "currency": "USD",
            "purpose": "Renewal of core analytics SaaS licenses",
            "department": str(self.department.id),
            "budget_category": str(self.category.id),
            "required_date": (timezone.now() + timedelta(days=7)).date().isoformat(),
            "priority": "medium",
            "cost_center": "IT-OPS-2025",
            "attachments": "invoice.pdf",
        }

        response = self.client.post(reverse("finance:budget_request_form"), post_data)
        self.assertEqual(response.status_code, 302)

        budget_request = BudgetRequest.objects.get()
        self.assertRedirects(
            response,
            reverse("finance:budget_request_detail", kwargs={"pk": budget_request.pk}),
        )
        self.assertEqual(budget_request.requester, self.user)
        self.assertEqual(budget_request.status, "approved")
        self.assertEqual(budget_request.approved_by, self.user)
        self.assertEqual(budget_request.amount, Decimal("950.00"))


class BudgetRequestListViewTest(TestCase):
    """Integration tests for the budget request listing behaviour."""

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="finance_staff",
            email="finance_staff@test.com",
            password="Password123!",
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username="finance_employee",
            email="finance_employee@test.com",
            password="Password123!",
        )
        self.other_user = User.objects.create_user(
            username="other_employee",
            email="other_employee@test.com",
            password="Password123!",
        )
        self.department = Department.objects.create(
            name=Department.MANAGEMENT,
            description="Management Department",
            slug="management-department",
            is_active=True,
        )
        self.category = BudgetCategory.objects.create(
            name="Leadership Offsites",
            description="Department strategy sessions",
            approval_tier="B",
            auto_approve_enabled=False,
            typical_monthly_amount=Decimal("5000.00"),
            variance_threshold=Decimal("30.00"),
            is_recurring=False,
        )

        self.request_for_regular = BudgetRequest.objects.create(
            requester=self.regular_user,
            amount=Decimal("1200.00"),
            currency="USD",
            purpose="Quarterly team building",
            department=self.department,
            required_date=(timezone.now() + timedelta(days=14)).date(),
            priority="medium",
            budget_category=self.category,
            cost_center="MGT-Q1",
            attachments=["agenda.pdf"],
            created_by=self.regular_user,
            last_modified_by=self.regular_user,
            status="submitted",
        )
        self.request_for_other = BudgetRequest.objects.create(
            requester=self.other_user,
            amount=Decimal("800.00"),
            currency="USD",
            purpose="Executive coaching",
            department=self.department,
            required_date=(timezone.now() + timedelta(days=21)).date(),
            priority="high",
            budget_category=self.category,
            cost_center="MGT-Q2",
            attachments=["proposal.pdf"],
            created_by=self.other_user,
            last_modified_by=self.other_user,
            status="submitted",
        )

    def test_staff_user_sees_all_requests(self):
        """Staff users should see the entire request set in the listing view."""
        self.client.login(username="finance_staff", password="Password123!")
        response = self.client.get(reverse("finance:budget_requests_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 2)

    def test_regular_user_sees_only_own_requests(self):
        """Non-staff users should only see their own submissions."""
        self.client.login(username="finance_employee", password="Password123!")
        response = self.client.get(reverse("finance:budget_requests_list"))
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.paginator.count, 1)
        self.assertEqual(page_obj.object_list[0].requester, self.regular_user)

    def test_regular_user_cannot_view_other_detail(self):
        """Regular users should be redirected when attempting to view another user's request."""
        self.client.login(username="finance_employee", password="Password123!")
        response = self.client.get(
            reverse("finance:budget_request_detail", kwargs={"pk": self.request_for_other.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("finance:budget_requests_list"))
