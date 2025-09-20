# investing/utils.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_investor_welcome_email(investment):
    """Send welcome email to new investor"""
    try:
        user = investment.investor
        investor_type = getattr(investment, "investor_type", "individual")

        template_name = "investing/emails/welcome_individual.html"

        context = {
            "user": user,
            "investment": investment,
            "investor_type": investor_type,
        }

        subject = f"Welcome to CODA Investments - {investor_type.title()} Investor"
        html_message = render_to_string(template_name, context)

        send_mail(
            subject=subject,
            message=f"Welcome {user.full_name}! Your investment has been received.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Welcome email sent to {user.email}")

    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")


def get_investor_type_from_user(user):
    """Map user subcategory to investor type"""
    from accounts.choices import InvestorSubCategoryChoices

    investor_type_map = {
        InvestorSubCategoryChoices.INDIVIDUAL: "individual",
        InvestorSubCategoryChoices.ANGEL: "angel",
        InvestorSubCategoryChoices.VC: "vc",
        InvestorSubCategoryChoices.PRIVATE: "private",
    }
    return investor_type_map.get(user.sub_category, "individual")


# Legacy functions for compatibility with existing views
def risk_ratios():
    """Legacy function for risk ratios calculation"""
    return {}


def get_user_investment(user):
    """Legacy function to get user investments"""
    try:
        from .models import Investor_Information

        return Investor_Information.objects.filter(investor=user)
    except:
        return []


def financial_categories():
    """Legacy function for financial categories"""
    return {}


def investment_rules():
    """Legacy function for investment rules"""
    return {}


def calculate_investor_returns(investment):
    """Legacy function to calculate investor returns"""
    try:
        return investment.calculate_returns()
    except:
        return 0
