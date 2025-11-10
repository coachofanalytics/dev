"""
Performance tests for finance page load times

Tests response times and performance benchmarks.

Author: CODA Development Team
Created: November 5, 2025
Category: Performance Tests
"""

import time
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Department
from finance.models import BudgetCategory, BudgetRequest

User = get_user_model()


class BudgetRequestListLoadTimeTest(TestCase):
    """Verify budget request list meets sub-500ms target in test environment."""

    @classmethod
    def setUpTestData(cls):
        cls.staff_user = User.objects.create_user(
            username="finance_staff_load",
            email="finance_staff_load@test.com",
            password="password123",
            is_staff=True,
            is_active=True,
        )
        cls.requester = User.objects.create_user(
            username="finance_requester_load",
            email="finance_requester_load@test.com",
            password="password123",
            is_active=True,
        )
        cls.department = Department.objects.create(
            name=Department.FIN,
            description="Finance",
            slug="finance-dept",
            is_active=True,
        )
        cls.category = BudgetCategory.objects.create(
            name="Annual Renewals",
            approval_tier="A",
            auto_approve_enabled=True,
            typical_monthly_amount=Decimal("1500.00"),
            variance_threshold=Decimal("10.00"),
        )

        for index in range(12):
            BudgetRequest.objects.create(
                requester=cls.requester,
                amount=Decimal("750.00") + Decimal(index),
                currency="USD",
                purpose=f"Annual renewal item {index}",
                department=cls.department,
                required_date=timezone.now().date() + timedelta(days=21),
                priority="medium",
                budget_category=cls.category,
                cost_center=f"FIN-{index:03d}",
                approval_chain=[{"role": "Finance Manager", "user": "finance.manager@test.com"}],
                current_approver=cls.staff_user,
                status="submitted",
                attachments=[],
                created_by=cls.requester,
                last_modified_by=cls.requester,
            )

    def test_budget_requests_list_renders_under_half_second(self):
        """Budget request list response should complete within 500ms."""
        self.client.login(username="finance_staff_load", password="password123")

        url = reverse("finance:budget_requests_list")
        start = time.perf_counter()
        response = self.client.get(url)
        duration = time.perf_counter() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            duration,
            0.50,
            msg="Budget request list exceeded 500ms render time in test environment.",
        )
