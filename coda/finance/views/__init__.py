# -*- coding: utf-8 -*-
"""
Finance Views Package
Imports all views from organized structure and legacy files
"""

# Import from organized structure
from .budget.dashboard import unified_budget_dashboard
from .budget.editing import (
    budget_category_edit, save_budget_estimates, budget_requests_list,
    budget_request_detail, approve_budget_request, reject_budget_request,
    budget_approval_dashboard
)
from .budget.drilldown import (
    budget_category_detail, budget_comparison_view, budget_item_edit
)
from .loan.budget_integration import (
    loan_eligibility_check, loan_application_with_budget,
    loan_budget_dashboard, budget_loan_impact_analysis
)
from .transaction.smart_entry import (
    smart_transaction_entry, api_suggest_category, api_validate_amount,
    api_receiver_suggestions
)

# Import from legacy views file (to be migrated gradually)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from views import (
    finance_index, openai_balancesheet, StatementsUpdateView, send_invoice,
    send_notification, finance_report, site_budget, WebBudgetUpdateView,
    investment_report, transact, inflow, cashflows
)

# Import other view modules
from .. import (
    payment_views, views_automation, views_enhanced_budget,
    views_finance_dashboard, views_legacy_dashboard, views_unified_department,
    views_projections, views_estimates, views_approvals, views_detailed_budget,
    views_enhanced_approvals, views_salary_dashboard, views_realtime_compliance,
    views_admin_controls, views_unified_budget, views_forms
)

# Import organized views as modules
from . import budget, loan, transaction

__all__ = [
    # Organized views
    'unified_budget_dashboard',
    'budget_category_edit', 'save_budget_estimates', 'budget_requests_list',
    'budget_request_detail', 'approve_budget_request', 'reject_budget_request',
    'budget_approval_dashboard',
    'budget_category_detail', 'budget_comparison_view', 'budget_item_edit',
    'loan_eligibility_check', 'loan_application_with_budget',
    'loan_budget_dashboard', 'budget_loan_impact_analysis',
    'smart_transaction_entry', 'api_suggest_category', 'api_validate_amount',
    'api_receiver_suggestions',
    
    # Legacy views
    'legacy_views',
    
    # View modules
    'payment_views', 'views_automation', 'views_enhanced_budget',
    'views_finance_dashboard', 'views_legacy_dashboard', 'views_unified_department',
    'views_projections', 'views_estimates', 'views_approvals', 'views_detailed_budget',
    'views_enhanced_approvals', 'views_salary_dashboard', 'views_realtime_compliance',
    'views_admin_controls', 'views_unified_budget', 'views_forms',
    'budget', 'loan', 'transaction',
]
