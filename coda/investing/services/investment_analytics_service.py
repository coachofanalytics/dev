# investing/services/investment_analytics_service.py
from decimal import Decimal
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from core.services.base import BaseService
from investing.models import Investor_Information
import logging

logger = logging.getLogger(__name__)


class InvestmentAnalyticsService(BaseService):
    """Service for investment analytics and reporting"""

    def get_investor_type_analytics(self):
        """Get analytics broken down by investor type"""
        try:
            analytics = {}

            for investor_type in ["individual", "angel", "vc", "private"]:
                # Map investor_type to subcategory for filtering
                from accounts.choices import InvestorSubCategoryChoices

                type_mapping = {
                    "individual": InvestorSubCategoryChoices.INDIVIDUAL,
                    "angel": InvestorSubCategoryChoices.ANGEL,
                    "vc": InvestorSubCategoryChoices.VC,
                    "private": InvestorSubCategoryChoices.PRIVATE,
                }
                sub_category = type_mapping.get(
                    investor_type, InvestorSubCategoryChoices.INDIVIDUAL
                )
                investments = Investor_Information.objects.filter(
                    investor__sub_category=sub_category
                )

                analytics[investor_type] = {
                    "total_investments": investments.count(),
                    "total_amount": investments.aggregate(Sum("amount_invested"))[
                        "amount_invested__sum"
                    ]
                    or 0,
                    "average_investment": investments.aggregate(Avg("amount_invested"))[
                        "amount_invested__avg"
                    ]
                    or 0,
                    "active_investments": investments.filter(status="active").count(),
                    "completed_investments": investments.filter(
                        status="completed"
                    ).count(),
                }

            return {
                "status": "success",
                "analytics": analytics,
                "generated_at": timezone.now(),
            }

        except Exception as e:
            logger.error(f"Error getting investor analytics: {e}")
            return self.handle_error(e, "Getting investor analytics")

    def get_performance_metrics(self, user=None):
        """Get performance metrics for user or all users"""
        try:
            if user:
                investments = Investor_Information.objects.filter(investor=user)
            else:
                investments = Investor_Information.objects.all()

            metrics = {
                "total_investments": investments.count(),
                "total_invested": investments.aggregate(Sum("amount_invested"))[
                    "amount_invested__sum"
                ]
                or 0,
                "total_returns": sum(
                    inv.amount_invested
                    * (inv.revenue_share_percentage or Decimal("8.00"))
                    / Decimal("100")
                    for inv in investments
                ),
                "average_return_rate": investments.aggregate(
                    Avg("revenue_share_percentage")
                )["revenue_share_percentage__avg"]
                or 0,
                "success_rate": self._calculate_success_rate(investments),
                "monthly_trend": self._get_monthly_trend(investments),
            }

            return {
                "status": "success",
                "metrics": metrics,
                "generated_at": timezone.now(),
            }

        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return self.handle_error(e, "Getting performance metrics")

    def get_investment_dashboard_data(self, user):
        """Get comprehensive dashboard data for user"""
        try:
            from .investment_service import InvestmentService

            investment_service = InvestmentService()

            # Get user investments
            investments_result = investment_service.get_user_investments(user)

            # Get performance metrics
            metrics_result = self.get_performance_metrics(user)

            # Get investor type analytics
            type_analytics = self.get_investor_type_analytics()

            return {
                "status": "success",
                "investments": investments_result.get("investments", []),
                "summary": investments_result.get("summary", {}),
                "metrics": metrics_result.get("metrics", {}),
                "type_analytics": type_analytics.get("analytics", {}),
                "user_type": investment_service._get_investor_type_from_user(user),
            }

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return self.handle_error(e, "Getting dashboard data")

    def _calculate_success_rate(self, investments):
        """Calculate investment success rate"""
        if not investments.exists():
            return 0

        successful = investments.filter(status="completed").count()
        total = investments.count()

        return (successful / total * 100) if total > 0 else 0

    def _get_monthly_trend(self, investments):
        """Get monthly investment trend"""
        from django.db.models.functions import TruncMonth

        monthly_data = (
            investments.annotate(month=TruncMonth("investment_date"))
            .values("month")
            .annotate(count=Count("id"), total=Sum("amount_invested"))
            .order_by("month")
        )

        return list(monthly_data)

    def get_investment_performance_report(self, user, start_date=None, end_date=None):
        """Generate detailed performance report for user"""
        try:
            from decimal import Decimal

            # Set default date range if not provided
            if not start_date:
                start_date = timezone.now().date() - timedelta(days=365)
            if not end_date:
                end_date = timezone.now().date()

            investments = Investor_Information.objects.filter(
                investor=user, investment_date__range=[start_date, end_date]
            )

            if not investments.exists():
                return {
                    "status": "no_data",
                    "message": "No investments found for the specified period",
                }

            # Calculate detailed metrics
            total_invested = sum(inv.amount_invested for inv in investments)
            total_returns = sum(
                inv.amount_invested
                * (inv.revenue_share_percentage or Decimal("8.00"))
                / Decimal("100")
                for inv in investments
            )
            roi_percentage = (
                (total_returns / total_invested * 100)
                if total_invested > 0
                else Decimal("0.00")
            )

            # Performance by status
            status_breakdown = {}
            for status in ["pending", "active", "completed", "cancelled"]:
                status_investments = investments.filter(status=status)
                status_breakdown[status] = {
                    "count": status_investments.count(),
                    "total_amount": sum(
                        inv.amount_invested for inv in status_investments
                    ),
                    "percentage": (
                        (status_investments.count() / investments.count() * 100)
                        if investments.count() > 0
                        else 0
                    ),
                }

            return {
                "status": "success",
                "period": {"start": start_date, "end": end_date},
                "summary": {
                    "total_investments": investments.count(),
                    "total_invested": total_invested,
                    "total_returns": total_returns,
                    "roi_percentage": roi_percentage,
                    "average_investment": (
                        total_invested / investments.count()
                        if investments.count() > 0
                        else Decimal("0.00")
                    ),
                },
                "status_breakdown": status_breakdown,
                "investments": list(
                    investments.values(
                        "id",
                        "amount_invested",
                        "contract_date",
                        "status",
                        "revenue_share_percentage",
                        "investment_plan__tier",
                    )
                ),
            }

        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return self.handle_error(e, "Generating performance report")
