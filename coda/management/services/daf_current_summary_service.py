"""
DAF Current Summary Service

Computes current DAF summary from active tasks (is_active=True).
Used by DAF v2 view to display summary cards.
"""

import logging
from decimal import Decimal
from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
from management.models import Task

logger = logging.getLogger(__name__)
User = get_user_model()


def get_current_daf_summary(employee_user) -> Dict[str, Any]:
    """
    Get current DAF summary for an employee.

    Computes summary from active tasks (is_active=True) only.
    Target amount is sum of mxearning from current active Task records.

    Args:
        employee_user: User instance (from get_user_model())

    Returns:
        Dict with:
        - employee: dict with id, username, full_name
        - money: dict with target_amount, released_total, locked_total, net_income
        - metrics: dict with points_earned, target_points
        - activities: list of task summaries (optional)
    """
    try:
        # Get active tasks for employee
        active_tasks = Task.objects.filter(employee=employee_user, is_active=True)

        # Calculate target amount (sum of mxearning)
        target_amount = active_tasks.aggregate(total=Sum("mxearning"))[
            "total"
        ] or Decimal("0")

        # Calculate points
        points_earned_result = active_tasks.aggregate(total=Sum("point"))
        points_earned = float(points_earned_result["total"] or Decimal("0"))

        target_points_result = active_tasks.aggregate(total=Sum("mxpoint"))
        target_points = float(target_points_result["total"] or Decimal("0"))

        # Calculate released total (earned from approved tasks)
        # Released = sum of get_pay() for tasks where point >= mxpoint * 0.8 (80% threshold)
        released_total = Decimal("0")
        for task in active_tasks:
            try:
                # Only count tasks that meet minimum completion threshold
                if (
                    task.point
                    and task.mxpoint
                    and task.point >= task.mxpoint * Decimal("0.8")
                ):
                    task_pay = (
                        task.get_pay() if hasattr(task, "get_pay") else Decimal("0")
                    )
                    released_total += task_pay
            except Exception as e:
                logger.warning(f"Error calculating pay for task {task.id}: {e}")
                continue

        # Calculate locked total (pending = target - released)
        locked_total = max(Decimal("0"), target_amount - released_total)

        # Net income (same as released for now)
        net_income = released_total

        # Build summary
        summary = {
            "employee": {
                "id": employee_user.id if hasattr(employee_user, "id") else 0,
                "username": getattr(employee_user, "username", "unknown"),
                "full_name": str(employee_user),
            },
            "money": {
                "target_amount": target_amount,
                "released_total": released_total,
                "locked_total": locked_total,
                "net_income": net_income,
            },
            "metrics": {
                "points_earned": points_earned,
                "target_points": target_points,
            },
            "activities": [],  # Optional: can be populated with task summaries if needed
        }

        return summary

    except Exception as e:
        logger.error(
            f"Error generating current DAF summary for {employee_user}: {e}",
            exc_info=True,
        )
        # Return safe defaults
        return {
            "employee": {
                "id": employee_user.id if hasattr(employee_user, "id") else 0,
                "username": getattr(employee_user, "username", "unknown"),
                "full_name": str(employee_user),
            },
            "money": {
                "target_amount": Decimal("0"),
                "released_total": Decimal("0"),
                "locked_total": Decimal("0"),
                "net_income": Decimal("0"),
            },
            "metrics": {
                "points_earned": 0.0,
                "target_points": 0.0,
            },
            "activities": [],
        }
