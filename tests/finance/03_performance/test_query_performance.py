"""
Performance tests for finance database queries

Tests for N+1 queries, query counts, and database performance.

Author: CODA Development Team
Created: November 5, 2025
Category: Performance Tests
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from accounts.choices import UserCategory
from accounts.models import Department
from finance.models import BudgetCategory, BudgetRequest

User = get_user_model()


class BudgetRequestListQueryPerformanceTest(TestCase):
    """
    Ensure the budget request list maintains a predictable query budget.

    Scenario:
        - Staff reviewer viewing 15 budget requests across departments
        - Expectation: render within <= 11 database queries
    """

    @classmethod
    def setUpTestData(cls):
        cls.staff_user = User.objects.create_user(
            username="finance_staff_perf",
            email="finance_staff_perf@test.com",
            password="password123",
            is_staff=True,
            is_active=True,
            category=UserCategory.CONSULTANT,
            first_name="Finance",
            last_name="Reviewer",
        )
        cls.requester = User.objects.create_user(
            username="finance_requester",
            email="finance_requester@test.com",
            password="password123",
            is_active=True,
            first_name="Request",
            last_name="Owner",
        )

        cls.department = Department.objects.create(
            name=Department.IT,
            description="Engineering department",
            slug="engineering-dept",
            is_active=True,
        )
        cls.other_department = Department.objects.create(
            name=Department.MANAGEMENT,
            description="Operations department",
            slug="operations-dept",
            is_active=True,
        )

        cls.category = BudgetCategory.objects.create(
            name="Software Licenses",
            approval_tier="A",
            auto_approve_enabled=True,
            typical_monthly_amount=Decimal("2000.00"),
            variance_threshold=Decimal("15.00"),
        )

        # Seed 15 requests to exercise pagination + select_related
        for index in range(15):
            department = cls.department if index % 2 == 0 else cls.other_department
            BudgetRequest.objects.create(
                requester=cls.requester,
                amount=Decimal("950.00") + Decimal(index),
                currency="USD",
                purpose=f"Purchase software license #{index}",
                department=department,
                required_date=timezone.now().date() + timedelta(days=14),
                priority="medium",
                budget_category=cls.category,
                cost_center=f"ENG-{index:03d}",
                approval_chain=[
                    {"role": "Department Lead", "user": "lead@example.com"},
                    {"role": "Finance", "user": "finance@example.com"},
                ],
                current_approver=cls.staff_user,
                status="submitted",
                attachments=[],
                created_by=cls.requester,
                last_modified_by=cls.requester,
            )

    def test_budget_requests_list_query_count_is_stable(self):
        """Finance budget request list should keep query count within target."""
        self.client.login(username="finance_staff_perf", password="password123")

        url = reverse("finance:budget_requests_list")
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(
            len(context.captured_queries),
            11,
            msg=(
                "Budget requests list triggered too many database queries. "
                "Review select_related/prefetch usage or pagination helpers."
            ),
        )
