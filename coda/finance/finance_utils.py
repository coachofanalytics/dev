"""
Finance Utilities Interface

This module provides a clean interface to all finance utility classes,
maintaining backward compatibility while using the new modular structure.
"""

from .utilities.loan_utils import LoanUtils
from .utilities.payment_utils import PaymentUtils
from .utilities.financial_utils import FinancialUtils
from .utilities.analytics_utils import AnalyticsUtils

# Re-export all utility functions for backward compatibility
from .utilities.loan_utils import (
    check_user_loan_eligibility,
    get_user_loan_limits,
    check_karen_country_club_membership,
    get_eligible_staff_guarantors,
    find_or_create_guarantor_user,
    calculate_guarantor_eligibility_score,
    get_existing_guarantor_info,
)

from .utilities.payment_utils import (
    update_link,
    get_exchange_rate,
    save_payment_record,
    convert_to_usd,
    get_user_currency,
    calculate_paypal_charges,
    validate_amount,
    validate_user_payment_eligibility,
    save_payment_history,
    process_visitor_payment,
)

from .utilities.financial_utils import (
    calculate_interest,
    calculate_loan_payment,
    calculate_amortization_schedule,
    calculate_investment_return,
    calculate_debt_to_income_ratio,
    calculate_net_worth,
    format_currency,
    validate_financial_data,
)

from .utilities.analytics_utils import (
    calculate_portfolio_performance,
    calculate_loan_performance_metrics,
    generate_financial_summary,
    generate_trend_analysis,
    calculate_risk_metrics,
)

# Export utility classes
__all__ = [
    # Utility classes
    'LoanUtils',
    'PaymentUtils',
    'FinancialUtils',
    'AnalyticsUtils',
    
    # Loan utilities
    'check_user_loan_eligibility',
    'get_user_loan_limits',
    'check_karen_country_club_membership',
    'get_eligible_staff_guarantors',
    'find_or_create_guarantor_user',
    'calculate_guarantor_eligibility_score',
    'get_existing_guarantor_info',
    
    # Payment utilities
    'update_link',
    'get_exchange_rate',
    'save_payment_record',
    'convert_to_usd',
    'get_user_currency',
    'calculate_paypal_charges',
    'validate_amount',
    'validate_user_payment_eligibility',
    'save_payment_history',
    'process_visitor_payment',
    
    # Financial utilities
    'calculate_interest',
    'calculate_loan_payment',
    'calculate_amortization_schedule',
    'calculate_investment_return',
    'calculate_debt_to_income_ratio',
    'calculate_net_worth',
    'format_currency',
    'validate_financial_data',
    
    # Analytics utilities
    'calculate_portfolio_performance',
    'calculate_loan_performance_metrics',
    'generate_financial_summary',
    'generate_trend_analysis',
    'calculate_risk_metrics',
]


