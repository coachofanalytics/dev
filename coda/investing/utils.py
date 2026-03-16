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


# ---------------------------------------------------------------------
# Staff preview helpers (shared by dashboard + tests)
# ---------------------------------------------------------------------


def _safe_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _normalize_legs(legs_payload):
    if not legs_payload:
        return []
    normalized = []
    for leg in legs_payload:
        normalized.append({
            'type': leg.get('type') or leg.get('leg_type'),
            'direction': leg.get('direction'),
            'contracts': leg.get('contracts'),
            'strike': _safe_number(leg.get('strike')),
            'expiration': leg.get('expiration') or leg.get('expiry'),
            'premium': _safe_number(leg.get('premium')),
            'delta': _safe_number(leg.get('delta')),
            'theta': _safe_number(leg.get('theta')),
        })
    return normalized


def build_preview_payloads(pending_queryset, approved_queryset):
    preview_payloads = {}
    for position in list(pending_queryset) + list(approved_queryset):
        metadata = getattr(position, 'api_response_data', {}) or {}
        whales_meta = metadata.get('unusual_whales') or {}
        legs = _normalize_legs(getattr(position, 'positions', []))

        short_leg = next(
            (leg for leg in legs if str(leg.get('direction', '')).lower().startswith('short')),
            legs[0] if legs else None,
        )
        long_leg = next(
            (leg for leg in legs if str(leg.get('direction', '')).lower().startswith('long')),
            legs[1] if len(legs) > 1 else None,
        )

        def _coerce_number(value):
            number = _safe_number(value)
            return float(number) if isinstance(number, (int, float)) else None

        short_strike = _coerce_number(short_leg.get('strike')) if short_leg else None
        long_strike = _coerce_number(long_leg.get('strike')) if long_leg else None

        underlying_price = metadata.get('underlying_price') or metadata.get('stock_price') or metadata.get('underlying')
        underlying_price = _coerce_number(underlying_price)

        preview_payloads[position.id] = {
            'id': position.id,
            'symbol': position.symbol,
            'strategy': position.get_strategy_display() if hasattr(position, 'get_strategy_display') else getattr(position, 'strategy', ''),
            'raw_strategy': getattr(position, 'strategy', None),
            'probability': float(getattr(position, 'probability_of_profit', 0) or 0),
            'ai_score': float(getattr(position, 'ai_score', 0) or 0),
            'premium_collected': float(getattr(position, 'premium_collected', 0) or 0),
            'capital_required': float(getattr(position, 'capital_required', 0) or 0),
            'max_profit': float(getattr(position, 'max_profit', 0) or 0),
            'max_loss': float(getattr(position, 'max_loss', 0) or 0),
            'dte': getattr(position, 'dte', None),
            'timing_signal': whales_meta.get('timing_signal'),
            'flow_score': whales_meta.get('flow_score'),
            'sentiment': whales_meta.get('sentiment'),
            'entry_window': whales_meta.get('entry_window'),
            'notes': getattr(position, 'notes', '') or '',
            'legs': legs,
            'short_strike': short_strike,
            'long_strike': long_strike,
            'underlying_price': underlying_price,
        }
    return preview_payloads


__all__ = [
    'send_investor_welcome_email',
    'get_investor_type_from_user',
    'risk_ratios',
    'get_user_investment',
    'financial_categories',
    'investment_rules',
    'calculate_investor_returns',
    'build_preview_payloads',
]
