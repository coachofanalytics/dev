# investing/services/investment_reporting_service.py
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from core.services.base import BaseService
from investing.models import Investor_Information
import logging

logger = logging.getLogger(__name__)


class InvestmentReportingService(BaseService):
    """Service for investment reporting and notifications"""

    def generate_monthly_report(self, user):
        """Generate monthly investment report for user"""
        try:
            # Get user's investments
            investments = Investor_Information.objects.filter(investor=user)

            if not investments.exists():
                return {
                    "status": "no_data",
                    "message": "No investments found for report generation",
                }

            # Calculate report data
            report_data = {
                "user": user,
                "report_period": self._get_report_period(),
                "investments": investments,
                "summary": self._calculate_monthly_summary(investments),
                "performance": self._calculate_performance_data(investments),
                "milestones": self._get_recent_milestones(investments),
            }

            # Send report email
            self._send_monthly_report_email(user, report_data)

            return {
                "status": "success",
                "report_data": report_data,
                "sent_at": timezone.now(),
            }

        except Exception as e:
            logger.error(f"Error generating monthly report: {e}")
            return self.handle_error(e, "Generating monthly report")

    def send_investment_welcome_email(self, investment):
        """Send welcome email to new investor"""
        try:
            user = investment.investor
            investor_type = investment.investor_type

            # Get appropriate email template based on investor type
            template_name = self._get_welcome_template(investor_type)

            # Prepare email context
            context = {
                "user": user,
                "investment": investment,
                "investor_type": investor_type,
                "investment_plan": investment.investment_plan,
                "expected_returns": self._calculate_expected_returns(investment),
                "next_steps": self._get_next_steps(investor_type),
            }

            # Render email content
            subject = f"Welcome to CODA Investments - {investor_type.title()} Investor"
            html_message = render_to_string(template_name, context)

            # Send email
            send_mail(
                subject=subject,
                message=f"Welcome {user.full_name}! Your {investor_type} investment has been received.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            self.log_operation(
                "welcome_email_sent",
                f"Sent welcome email to {user.email} for {investor_type} investment",
            )

            return {"status": "success", "message": "Welcome email sent successfully"}

        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
            return self.handle_error(e, "Sending welcome email")

    def send_investment_upgrade_notification(
        self, user, current_amount, recommended_amount
    ):
        """Send upgrade notification to encourage larger investment"""
        try:
            investor_type = self._get_investor_type_from_user(user)

            context = {
                "user": user,
                "current_amount": current_amount,
                "recommended_amount": recommended_amount,
                "investor_type": investor_type,
                "potential_increase": recommended_amount - current_amount,
                "upgrade_benefits": self._get_upgrade_benefits(
                    investor_type, recommended_amount
                ),
            }

            subject = (
                f"Investment Upgrade Opportunity - {investor_type.title()} Investor"
            )
            html_message = render_to_string(
                "investing/emails/upgrade_opportunity.html", context
            )

            send_mail(
                subject=subject,
                message=f"Investment upgrade opportunity for {user.full_name}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            self.log_operation(
                "upgrade_notification_sent",
                f"Sent upgrade notification to {user.email}",
            )

            return {
                "status": "success",
                "message": "Upgrade notification sent successfully",
            }

        except Exception as e:
            logger.error(f"Error sending upgrade notification: {e}")
            return self.handle_error(e, "Sending upgrade notification")

    def send_quarterly_performance_report(self, user):
        """Send quarterly performance report to investor"""
        try:
            from .investment_analytics_service import InvestmentAnalyticsService

            analytics_service = InvestmentAnalyticsService()

            # Get quarterly performance data
            start_date = timezone.now().date() - timedelta(days=90)
            performance_data = analytics_service.get_investment_performance_report(
                user, start_date
            )

            if performance_data.get("status") == "no_data":
                return {
                    "status": "no_data",
                    "message": "No investment data for quarterly report",
                }

            context = {
                "user": user,
                "quarter": self._get_quarter_info(),
                "performance_data": performance_data,
                "recommendations": self._get_quarterly_recommendations(
                    performance_data
                ),
            }

            subject = (
                f"Q{context['quarter']['number']} Investment Performance Report - CODA"
            )
            html_message = render_to_string(
                "investing/emails/quarterly_report.html", context
            )

            send_mail(
                subject=subject,
                message=f"Q{context['quarter']['number']} performance report for {user.full_name}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            self.log_operation(
                "quarterly_report_sent", f"Sent quarterly report to {user.email}"
            )

            return {
                "status": "success",
                "message": "Quarterly report sent successfully",
            }

        except Exception as e:
            logger.error(f"Error sending quarterly report: {e}")
            return self.handle_error(e, "Sending quarterly report")

    def _get_report_period(self):
        """Get current month period"""
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return {
            "start": start_of_month,
            "end": now,
            "month_name": now.strftime("%B %Y"),
        }

    def _calculate_monthly_summary(self, investments):
        """Calculate monthly summary"""
        return {
            "total_invested": sum(inv.amount_invested for inv in investments),
            "current_value": sum(inv.calculate_returns() for inv in investments),
            "active_count": investments.filter(status="active").count(),
            "completed_count": investments.filter(status="completed").count(),
        }

    def _calculate_performance_data(self, investments):
        """Calculate performance data"""
        # Implementation for performance calculations
        total_invested = sum(inv.amount_invested for inv in investments)
        total_returns = sum(inv.calculate_returns() for inv in investments)

        return {
            "total_invested": total_invested,
            "total_returns": total_returns,
            "roi_percentage": (
                (total_returns / total_invested * 100) if total_invested > 0 else 0
            ),
            "average_return_rate": (
                sum(inv.revenue_share_percentage for inv in investments)
                / investments.count()
                if investments.count() > 0
                else 0
            ),
        }

    def _get_recent_milestones(self, investments):
        """Get recent milestones"""
        # Implementation for milestone tracking
        return []

    def _send_monthly_report_email(self, user, report_data):
        """Send monthly report email"""
        try:
            context = {"user": user, "report_data": report_data}

            subject = f"Monthly Investment Report - {report_data['report_period']['month_name']}"
            html_message = render_to_string(
                "investing/emails/monthly_report.html", context
            )

            send_mail(
                subject=subject,
                message=f"Monthly investment report for {user.full_name}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            self.log_operation(
                "monthly_report_sent", f"Sent monthly report to {user.email}"
            )

        except Exception as e:
            logger.error(f"Failed to send monthly report email: {e}")

    def _get_welcome_template(self, investor_type):
        """Get appropriate welcome email template"""
        template_map = {
            "individual": "investing/emails/welcome_individual.html",
            "angel": "investing/emails/welcome_angel.html",
            "vc": "investing/emails/welcome_vc.html",
            "private": "investing/emails/welcome_private.html",
        }
        return template_map.get(
            investor_type, "investing/emails/welcome_individual.html"
        )

    def _calculate_expected_returns(self, investment):
        """Calculate expected returns for investment"""
        return investment.calculate_returns()

    def _get_next_steps(self, investor_type):
        """Get next steps based on investor type"""
        steps_map = {
            "individual": [
                "Review your investment dashboard",
                "Set up monthly reporting preferences",
                "Consider upgrading to larger investment tiers",
            ],
            "angel": [
                "Access exclusive angel investor resources",
                "Join monthly investor calls",
                "Review portfolio company updates",
            ],
            "vc": [
                "Schedule quarterly portfolio review",
                "Access detailed company analytics",
                "Review co-investment opportunities",
            ],
            "private": [
                "Schedule private consultation",
                "Access premium reporting suite",
                "Review custom investment structures",
            ],
        }
        return steps_map.get(investor_type, steps_map["individual"])

    def _get_investor_type_from_user(self, user):
        """Map user subcategory to investor type"""
        from accounts.choices import InvestorSubCategoryChoices

        investor_type_map = {
            InvestorSubCategoryChoices.INDIVIDUAL: "individual",
            InvestorSubCategoryChoices.ANGEL: "angel",
            InvestorSubCategoryChoices.VC: "vc",
            InvestorSubCategoryChoices.PRIVATE: "private",
        }
        return investor_type_map.get(user.sub_category, "individual")

    def _get_upgrade_benefits(self, investor_type, amount):
        """Get upgrade benefits based on investor type and amount"""
        benefits = {
            "individual": [
                "Higher revenue share percentage",
                "Priority customer support",
                "Monthly performance reports",
            ],
            "angel": [
                "Access to exclusive deals",
                "Co-investment opportunities",
                "Direct founder access",
            ],
            "vc": ["Board observer rights", "Due diligence access", "Custom reporting"],
            "private": [
                "Custom investment structures",
                "Direct management access",
                "Premium concierge service",
            ],
        }
        return benefits.get(investor_type, benefits["individual"])

    def _get_quarter_info(self):
        """Get current quarter information"""
        now = timezone.now()
        quarter = ((now.month - 1) // 3) + 1
        year = now.year

        return {"number": quarter, "year": year, "display": f"Q{quarter} {year}"}

    def _get_quarterly_recommendations(self, performance_data):
        """Get quarterly investment recommendations"""
        # Implementation for generating recommendations based on performance
        return [
            "Consider diversifying your investment portfolio",
            "Review risk tolerance and adjust accordingly",
            "Schedule a consultation for portfolio optimization",
        ]
