"""
Payroll Summary Service - Single source of truth for payroll/DAF calculations.

This service provides unified API for payroll calculations used by DAF v2 and payslip.
Ensures consistency between DAF v2 and payslip views.

Backward compatible: Returns safe defaults if models/fields are missing.
"""

import logging
from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
from django.utils import timezone as django_timezone

logger = logging.getLogger(__name__)

try:
    from management.models import Task
    from management.services.daf_current_summary_service import \
        get_current_daf_summary
except ImportError:
    logger.warning(
        "Payroll summary service: Could not import Task/daf_current_summary_service"
    )
    Task = None
    get_current_daf_summary = None

User = get_user_model()


def get_15th_of_next_month(today: Optional[date] = None) -> date:
    """
    Get the 15th of next month (Pay Day date).

    Args:
        today: Optional date (defaults to today)

    Returns:
        Date object for 15th of next month
    """
    if today is None:
        today = django_timezone.now().date()

    # Get next month
    if today.month == 12:
        next_month = 1
        next_year = today.year + 1
    else:
        next_month = today.month + 1
        next_year = today.year

    # Return 15th of next month
    return date(next_year, next_month, 15)


def get_time_remaining_until_pay_day(
    today: Optional[datetime] = None,
) -> Dict[str, int]:
    """
    Get time remaining until Pay Day (15th of next month).

    Args:
        today: Optional datetime (defaults to now)

    Returns:
        dict with:
        - days: int
        - hours: int
        - minutes: int
        - seconds: int
    """
    if today is None:
        today = django_timezone.now()

    try:
        pay_day_date = get_15th_of_next_month(today.date())
        pay_day_datetime = django_timezone.make_aware(
            datetime.combine(pay_day_date, datetime.min.time())
        )

        # Calculate time delta
        delta = pay_day_datetime - today

        if delta.total_seconds() < 0:
            # Pay day has passed, return zeros
            return {"days": 0, "hours": 0, "minutes": 0, "seconds": 0}

        total_seconds = int(delta.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return {
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
        }
    except Exception as e:
        logger.error(
            f"Error calculating time remaining until pay day: {e}", exc_info=True
        )
        return {"days": 0, "hours": 0, "minutes": 0, "seconds": 0}


def get_time_remaining_until_month_end(
    today: Optional[datetime] = None,
) -> Dict[str, int]:
    """
    Get time remaining until end of current month.

    Args:
        today: Optional datetime (defaults to now)

    Returns:
        dict with:
        - days: int
        - hours: int
        - minutes: int
        - seconds: int
    """
    if today is None:
        today = django_timezone.now()

    try:
        today_date = today.date()
        last_day = monthrange(today_date.year, today_date.month)[1]
        month_end_date = datetime(today_date.year, today_date.month, last_day).date()
        month_end_datetime = django_timezone.make_aware(
            datetime.combine(month_end_date, datetime.max.time())
        )

        # Calculate time delta
        delta = month_end_datetime - today

        if delta.total_seconds() < 0:
            # Month end has passed, return zeros
            return {"days": 0, "hours": 0, "minutes": 0, "seconds": 0}

        total_seconds = int(delta.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return {
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
        }
    except Exception as e:
        logger.error(
            f"Error calculating time remaining until month end: {e}", exc_info=True
        )
        return {"days": 0, "hours": 0, "minutes": 0, "seconds": 0}


class PayrollSummaryService:
    """
    Service for calculating payroll summaries for employees.

    Single source of truth for payroll calculations used by DAF v2 and payslip.
    """

    def get_user_pay_summary(self, user: User) -> Dict[str, Any]:
        """
        Get payroll summary for a user.

        Args:
            user: User instance

        Returns:
            dict with:
            - target_amount: Decimal (total target earnings)
            - earned_amount_provisional: Decimal (total earned, including pending)
            - approved_earned_amount: Decimal (approved earnings only)
            - pending_approval_amount: Decimal (pending approval)
            - remaining_amount: Decimal (remaining to earn)
            - points_earned_provisional: Decimal (total points earned)
            - approved_earned_points: Decimal (approved points only)
            - target_points: Decimal (target points)
            - approval_percentage: float (0.0 to 100.0)
            - approval_status: str ('COMPLETE', 'NEEDS WORK', etc.)
            - pay_day_date: date (15th of next month)
            - pay_day_formatted: str (formatted date string)
            - time_remaining: dict (time until pay day)
            - time_remaining_until_month_end: dict (time until month end)
            - net_income: Decimal (net income)
        """
        if Task is None or get_current_daf_summary is None:
            # Backward compatible: return safe defaults if models not available
            return self._get_empty_summary()

        try:
            # Use daf_current_summary_service as base
            daf_summary = get_current_daf_summary(user)

            money = daf_summary.get("money", {})
            metrics = daf_summary.get("metrics", {})

            # Extract base values
            target_amount = Decimal(str(money.get("target_amount", 0)))
            released_total = Decimal(str(money.get("released_total", 0)))
            locked_total = Decimal(str(money.get("locked_total", 0)))
            net_income = Decimal(str(money.get("net_income", 0)))

            points_earned = Decimal(str(metrics.get("points_earned", 0)))
            target_points = Decimal(str(metrics.get("target_points", 0)))

            # Get active tasks for more detailed calculations
            active_tasks = Task.objects.filter(employee=user, is_active=True)

            # Calculate approved vs provisional
            # Approved = tasks with point >= mxpoint * 0.8 (80% threshold)
            approved_amount = Decimal("0")
            approved_points = Decimal("0")
            provisional_amount = Decimal("0")
            provisional_points = Decimal("0")

            for task in active_tasks:
                try:
                    task_pay = (
                        task.get_pay() if hasattr(task, "get_pay") else Decimal("0")
                    )
                    task_point = Decimal(str(task.point or 0))
                    task_mxpoint = Decimal(str(task.mxpoint or 1))

                    # Calculate if approved (80% threshold)
                    if task_mxpoint > 0 and task_point >= task_mxpoint * Decimal("0.8"):
                        approved_amount += task_pay
                        approved_points += task_point
                    else:
                        provisional_amount += task_pay
                        provisional_points += task_point
                except Exception as e:
                    logger.warning(
                        f"Error calculating task {task.id if hasattr(task, 'id') else 'unknown'}: {e}"
                    )
                    continue

            # Total earned (provisional = approved + pending)
            earned_amount_provisional = approved_amount + provisional_amount
            points_earned_provisional = approved_points + provisional_points

            # Pending approval = provisional amount
            pending_approval_amount = provisional_amount

            # Remaining = target - earned (provisional)
            remaining_amount = max(
                Decimal("0"), target_amount - earned_amount_provisional
            )

            # Calculate approval percentage (approved points / target points * 100)
            approval_percentage = 0.0
            if target_points > 0:
                approval_percentage = float(
                    (approved_points / target_points) * Decimal("100")
                )

            # Determine approval status
            if approval_percentage >= 33.0:
                approval_status = "COMPLETE"
            elif approval_percentage >= 0.0:
                approval_status = "NEEDS WORK"
            else:
                approval_status = "NOT STARTED"

            # Get pay day date (15th of next month)
            pay_day_date = get_15th_of_next_month()
            pay_day_formatted = pay_day_date.strftime("%B %d, %Y")

            # Get time remaining
            time_remaining = get_time_remaining_until_pay_day()
            time_remaining_month_end = get_time_remaining_until_month_end()

            return {
                "target_amount": target_amount,
                "earned_amount_provisional": earned_amount_provisional,
                "approved_earned_amount": approved_amount,
                "pending_approval_amount": pending_approval_amount,
                "remaining_amount": remaining_amount,
                "points_earned_provisional": points_earned_provisional,
                "approved_earned_points": approved_points,
                "target_points": target_points,
                "approval_percentage": approval_percentage,
                "approval_status": approval_status,
                "pay_day_date": pay_day_date,
                "pay_day_formatted": pay_day_formatted,
                "time_remaining": time_remaining,
                "time_remaining_until_month_end": time_remaining_month_end,
                "net_income": net_income,
            }

        except Exception as e:
            logger.error(
                f"Error generating payroll summary for user {user.username if hasattr(user, 'username') else 'unknown'}: {e}",
                exc_info=True,
            )
            return self._get_empty_summary()

    def _get_empty_summary(self) -> Dict[str, Any]:
        """Return empty summary with safe defaults."""
        today = django_timezone.now().date()
        pay_day_date = get_15th_of_next_month(today)

        return {
            "target_amount": Decimal("0"),
            "earned_amount_provisional": Decimal("0"),
            "approved_earned_amount": Decimal("0"),
            "pending_approval_amount": Decimal("0"),
            "remaining_amount": Decimal("0"),
            "points_earned_provisional": Decimal("0"),
            "approved_earned_points": Decimal("0"),
            "target_points": Decimal("0"),
            "approval_percentage": 0.0,
            "approval_status": "NOT STARTED",
            "pay_day_date": pay_day_date,
            "pay_day_formatted": pay_day_date.strftime("%B %d, %Y"),
            "time_remaining": {"days": 0, "hours": 0, "minutes": 0, "seconds": 0},
            "time_remaining_until_month_end": {
                "days": 0,
                "hours": 0,
                "minutes": 0,
                "seconds": 0,
            },
            "net_income": Decimal("0"),
        }
