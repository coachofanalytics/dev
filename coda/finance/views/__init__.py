# -*- coding: utf-8 -*-
"""
Finance Views Package
Clean organized structure without circular imports
"""

# Import organized views directly (avoiding circular imports)
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

# Import legacy views directly from the legacy views file
import importlib.util
import os

# Load legacy views module directly
legacy_views_path = os.path.join(os.path.dirname(__file__), '..', 'views.py')
spec = importlib.util.spec_from_file_location("legacy_views", legacy_views_path)
legacy_views = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy_views)

# Make legacy views available
finance_index = legacy_views.finance_index
openai_balancesheet = legacy_views.openai_balancesheet
StatementsUpdateView = legacy_views.StatementsUpdateView
send_invoice = legacy_views.send_invoice
send_notification = legacy_views.send_notification
finance_report = legacy_views.finance_report
site_budget = legacy_views.site_budget
WebBudgetUpdateView = legacy_views.WebBudgetUpdateView
investment_report = legacy_views.investment_report
transact = legacy_views.transact
inflow = legacy_views.inflow
cashflows = legacy_views.cashflows

# Import other view modules
from .. import (
    payment_views, views_automation, views_enhanced_budget,
    views_finance_dashboard, views_legacy_dashboard, views_unified_department,
    views_projections, views_estimates, views_approvals, views_detailed_budget,
    views_enhanced_approvals, views_salary_dashboard, views_realtime_compliance,
    views_admin_controls, views_unified_budget, views_forms
)

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
    'finance_index', 'openai_balancesheet', 'StatementsUpdateView',
    'send_invoice', 'send_notification', 'finance_report', 'site_budget',
    'WebBudgetUpdateView', 'investment_report', 'transact', 'inflow', 'cashflows',
    
    # View modules
    'payment_views', 'views_automation', 'views_enhanced_budget',
    'views_finance_dashboard', 'views_legacy_dashboard', 'views_unified_department',
    'views_projections', 'views_estimates', 'views_approvals', 'views_detailed_budget',
    'views_enhanced_approvals', 'views_salary_dashboard', 'views_realtime_compliance',
    'views_admin_controls', 'views_unified_budget', 'views_forms',
]