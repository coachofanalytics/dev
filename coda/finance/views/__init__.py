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
UserInflowListView = legacy_views.UserInflowListView
InflowDetailView = legacy_views.InflowDetailView
InflowUpdateView = legacy_views.InflowUpdateView
InflowDeleteView = legacy_views.InflowDeleteView
clientinflows = legacy_views.clientinflows
contract_data_submission = legacy_views.contract_data_submission
contract_investment_submission = legacy_views.contract_investment_submission
mycontract = legacy_views.mycontract
new_contract = legacy_views.new_contract
new_investment_contract = legacy_views.new_investment_contract
pay = legacy_views.pay
payment = legacy_views.payment
paymentComplete = legacy_views.paymentComplete
payments = legacy_views.payments
payment_plan = legacy_views.payment_plan
MpesaPaymentView = legacy_views.MpesaPaymentView
verify_otp = legacy_views.verify_otp
payment_success = legacy_views.payment_success
payment_failed = legacy_views.payment_failed
UserPayUpdateView = legacy_views.UserPayUpdateView
DefaultPaymentListView = legacy_views.DefaultPaymentListView
PaymentCreateView = legacy_views.PaymentCreateView
DefaultPaymentUpdateView = legacy_views.DefaultPaymentUpdateView
PaymentInformationUpdateView = legacy_views.PaymentInformationUpdateView
PaymentHistoryUpdateView = legacy_views.PaymentHistoryUpdateView
PaymentConfigCreateView = legacy_views.PaymentConfigCreateView
PaymentConfigListView = legacy_views.PaymentConfigListView
PaymentConfigUpdateView = legacy_views.PaymentConfigUpdateView
loan_application_home = legacy_views.loan_application_home
loan_rejection = legacy_views.loan_rejection
LoanListView = legacy_views.LoanListView
loan_application_confirmation = legacy_views.loan_application_confirmation
userLoanListView = legacy_views.userLoanListView
loan_detail = legacy_views.loan_detail
collateral_form = legacy_views.collateral_form
submit_collateral = legacy_views.submit_collateral
edit_loan = legacy_views.edit_loan
update_loan = legacy_views.update_loan
apply_for_loan = legacy_views.apply_for_loan
guarantor_approval_request = legacy_views.guarantor_approval_request
guarantor_approve_loan = legacy_views.guarantor_approve_loan
guarantor_reject_loan = legacy_views.guarantor_reject_loan
guarantor_process_approval = legacy_views.guarantor_process_approval
get_guarantor_eligibility_scores = legacy_views.get_guarantor_eligibility_scores
admin_loan_applications = legacy_views.admin_loan_applications
approve_loan_application = legacy_views.approve_loan_application
reject_loan_application = legacy_views.reject_loan_application
recompute_loan_application = legacy_views.recompute_loan_application
loan_analytics = legacy_views.loan_analytics
smart_collateral_dashboard = legacy_views.smart_collateral_dashboard
loan_system_presentation = legacy_views.loan_system_presentation
user_collateral_status = legacy_views.user_collateral_status
notify_guarantor_available = legacy_views.notify_guarantor_available
FoodCreateView = legacy_views.FoodCreateView
SupplierCreateView = legacy_views.SupplierCreateView
SupplierUpdateView = legacy_views.SupplierUpdateView
FoodUpdateView = legacy_views.FoodUpdateView
SupplierListView = legacy_views.SupplierListView
food_history_view = legacy_views.food_history_view
food_history_update = legacy_views.food_history_update
add_budget_item = legacy_views.add_budget_item
budget = legacy_views.budget
BudgetUpdateView = legacy_views.BudgetUpdateView
LoanUpdateView = legacy_views.LoanUpdateView
FoodListView = legacy_views.FoodListView
foodlist = legacy_views.foodlist
determine_rejection_reason = legacy_views.determine_rejection_reason
CodaBudgetUpdateView = legacy_views.CodaBudgetUpdateView
BudgetSummaryUpdateView = legacy_views.BudgetSummaryUpdateView
budget_projection = legacy_views.budget_projection
automated_budget_estimation = legacy_views.automated_budget_estimation
budget_consolidation_dashboard = legacy_views.budget_consolidation_dashboard

# Import other view modules from organized structure
# payment_views is imported in urls.py from _deprecated.legacy_views
from .budget import (
    views_automation, views_enhanced_budget, views_projections, views_estimates,
    views_approvals, views_detailed_budget, views_enhanced_approvals,
    views_salary_dashboard, views_realtime_compliance, views_admin_controls,
    views_unified_budget, views_forms
)
from .core import views_finance_dashboard
from .legacy import views_legacy_dashboard, views_unified_department

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
    'views_automation', 'views_enhanced_budget',
    'views_finance_dashboard', 'views_legacy_dashboard', 'views_unified_department',
    'views_projections', 'views_estimates', 'views_approvals', 'views_detailed_budget',
    'views_enhanced_approvals', 'views_salary_dashboard', 'views_realtime_compliance',
    'views_admin_controls', 'views_unified_budget', 'views_forms',
]