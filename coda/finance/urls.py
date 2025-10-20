from django.urls import path, reverse
from django.shortcuts import redirect
from . import views
from .views import legacy_views

# Import organized payment views
from .views.payment import (
    payment_method_selection as unified_payment_selection,
    payment_processing as unified_payment_processing,
    payment_success as unified_payment_success,
    payment_failed as unified_payment_failed,
    mpesa_otp_confirmation as unified_mpesa_otp,
    verify_mpesa_otp as unified_verify_otp,
)
from .views.payment.payment_details import (
    show_payment_details,
    upload_payment_proof,
)
from .views.payment.receipt_views import (
    view_receipt,
    download_receipt,
    email_receipt,
    verify_payment_receipt,
)
from .views.payment.dashboard_views import (
    payment_dashboard,
    retry_payment,
)
from .views.payment.admin_verification import (
    admin_payment_verification_dashboard,
    approve_payment,
    reject_payment,
    bulk_approve_payments,
)
from .views.payment.stripe_views import (
    create_payment_intent,
    stripe_webhook,
)

# Import organized budget views
from .views.budget import drilldown as views_budget_drilldown
from .views.budget import editing as views_budget_editing
from .views.api import smart_form_api as views_api_smart_form
from .views.budget import dashboard as views_budget_dashboard
from .views.budget import approvals  # CONSOLIDATED: approval.py + views_approvals.py + views_enhanced_approvals.py
from .views.budget import views_unified_budget, views_enhanced_budget, views_projections
from .views.budget import views_estimates, views_detailed_budget
from .views.budget import views_forms, views_salary_dashboard
from .views.budget import views_automation, views_admin_controls, views_realtime_compliance
from .views.budget import views_tier_management  # Phase 2: Finance Manager tier controls
# views_budget_presentation migrated to portfolio app

# Import organized core views  
from .views.core import views_finance_dashboard

# Import organized legacy views (for backward compatibility)
from .views.legacy import views_legacy_dashboard, views_unified_department

# Import organized loan views
from .views.loan import budget_integration as views_loan_budget_integration

# Import organized transaction views
from .views.transaction import smart_entry as views_smart_transaction

# Import smart transaction views (Phase 1 Data Cleanup) - now using organized views
# from . import views_smart_transaction  # Legacy import removed

# Import cascading form API
from .views.api import api_cascading

# Import auto-prediction API
from .views.api import api_auto_predict

# Import budget editing views (Phase 2)
# views_budget_editing now imported above

# Import loan-budget integration views (Phase 3)
# from . import views_loan_budget_integration  # Legacy import removed - using organized views

app_name = 'finance'
urlpatterns = [
    #=============================FINANCE INDEX=====================================
    path('', views.finance_index, name='finance-index'),
    
    #=============================FINANCES=====================================
    path('statements/', views.openai_balancesheet, name='open_statements'),
    path('update_statements/<int:pk>', views.StatementsUpdateView.as_view(template_name="main/snippets_templates/generalform.html"), name='update_statements'),
    path('send_invoice/<str:type>/', views.send_invoice, name='send_invoice'),
    path('send_notification/<int:payment_id>/', views.send_notification, name='send_notification'),
    path('finance_report/', views.finance_report, name='finance_report'),
    # path('save-and-upload/', views.save_and_upload_to_drive, name='save_and_upload_to_drive'),  # COMMENTED: Function doesn't exist
    path('category_budget/<str:category>/', views.site_budget, name='site_budget'),
    path('category_budget/<str:company_slug>/<str:category>/<str:subcategory>/', views.site_budget, name='site_budget_with_subcategory'),
    path('web_budget/<int:pk>/update/', views.WebBudgetUpdateView.as_view(), name='web-update'),
    path('investment_report/', views.investment_report, name='investment_report'),
    path('transact/', views.transact, name='finance-transact'),
    
    # Smart Transaction Entry (Phase 1 Data Cleanup - Improved UX)
    path('transaction/smart-entry/', views_smart_transaction.smart_transaction_entry, name='smart-transaction-entry'),
    path('api/suggest-category/', views_smart_transaction.api_suggest_category, name='api-suggest-category'),
    path('api/validate-amount/', views_smart_transaction.api_validate_amount, name='api-validate-amount'),
    path('api/receiver-suggestions/', views_smart_transaction.api_receiver_suggestions, name='api-receiver-suggestions'),
    
    # Cascading Form API (Phase 2 - Smart Data Entry)
    path('api/subcategories/', api_cascading.api_get_subcategories, name='api-get-subcategories'),
    path('api/items/', api_cascading.api_get_items, name='api-get-items'),
    path('api/suggest-defaults/', api_cascading.api_suggest_defaults, name='api-suggest-defaults'),
    
    # Auto-Prediction API (Phase 2 - Intelligent Auto-Fill)
    path('api/predict-all/', api_auto_predict.api_predict_all_fields, name='api-predict-all'),
    
    # path('transaction/<str:transaction_type>', views.outflows, name='transaction-list'),
    # path('transaction/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction-detail'),  # COMMENTED: View doesn't exist
    # path('transaction/<int:pk>/update/', views.TransactionUpdateView.as_view(template_name="finance/payments/transaction_form.html"), name='transaction-update'),  # COMMENTED: View doesn't exist
    # path('transaction/<int:pk>/delete/', views.TransactionUpdateView.as_view(template_name="finance/payments/transaction_confirm_delete.html"), name='transaction-delete'),  # COMMENTED: View doesn't exist
     #-----------CASHINFLOW---------------------------------------
    path('inflow_entry/', views.inflow, name='entry_inflow'),
    path('cashflows/<str:type>/', views.cashflows, name='cashflows-list'),
    path('user_inflow/', views.UserInflowListView.as_view(), name='user-list'),
    path('inflow/<int:pk>/', views.InflowDetailView.as_view(), name='inflow-detail'),
    path('inflow/<int:pk>/delete/', views.InflowDetailView.as_view(), name='inflow-delete'),
    path('inflow/<int:pk>/update/', views.InflowUpdateView.as_view(template_name="finance/cashflows/inflow_form.html"), name='inflow-update'),
    #=============================CLIENT CASHFLOW=====================================
    path('clientinflows/<str:username>/', views.clientinflows, name='userclientinflows'),
    #=============================CLIENT CONTRACT FORM SUBMISSIONS=====================================
    path('contract_data/', views.contract_data_submission, name='contract_data_submission'),
    path('investment_submission/', views.contract_investment_submission, name='investment_submission'),
    path('mycontract/<str:username>/', views.mycontract, name='mycontract'),
    path('newcontract/<str:username>/', views.new_contract, name='newcontract'),
    path('newinvestmentcontract/<int:plan_id>/', views.new_investment_contract, name='newinvestmentcontract'),
    path('pay/', unified_payment_selection, name='pay'),
    path('payment/<int:service>/', views.pay, name='service_pay'),
    path('payment_method/<str:method>/', legacy_views.payment, name='payment_method'),
    path("payment_complete/", views.paymentComplete, name="payment_complete"),
    path('payments/<str:title>/<str:status>/', views.payments, name='payments'),
    path('payment_plan/<str:payment_id>', views.payment_plan, name='payment_plan'),
    path('mpesa-payment/', views.MpesaPaymentView, name='mpesa_payment'),
    path('otp-confirmation/', views.verify_otp, name='otp_confirmation'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('pay/<int:pk>/', views.UserPayUpdateView.as_view(), name='updatepay'),
    
    #=============================UNIFIED PAYMENT SYSTEM=====================================
    # New unified payment URLs - Conditionally loaded if payment_views is available
    # If not available, unified_method_selection redirects to legacy pay page
    
    # Legacy payment URLs (maintained for backward compatibility)
    path('defaultpayments/', legacy_views.DefaultPaymentListView.as_view(template_name='finance/payments/defaultpayments.html'), name='defaultpayments'),
    path('newpayment/', legacy_views.PaymentCreateView.as_view(template_name='finance/payments/payment_form.html'), name='newpayment'),
    path('payment/<int:pk>/update/', legacy_views.DefaultPaymentUpdateView.as_view(template_name='finance/payments/payment_form.html'), name='payment-update'),
    path('updatepaymentinfo/<int:pk>/update/', views.PaymentInformationUpdateView.as_view(template_name='finance/payments/payment_form.html'), name='paymentinfo-update'),
    path('updatepaymenthistory/<int:pk>/update/', views.PaymentHistoryUpdateView.as_view(template_name='finance/payments/payment_form.html'), name='paymentHist-update'),
    #Pay configs URLS
    path('newpaymentconfigs/',views.PaymentConfigCreateView.as_view(template_name='finance/payments/payment_form.html'), name='newpaymentconfigs'),
    path('paymentconfigs/', views.PaymentConfigListView.as_view(), name='paymentconfigs'),
    path('paymentconfigs/<int:pk>/update/', views.PaymentConfigUpdateView.as_view(template_name='finance/payments/payment_form.html'), name='paymentconfigs-update'),
    #Loans URLS
    path('loan-home/', views.loan_application_home, name='loan-home'),
    # path('apply-for-loan/', views.apply_for_loan, name='apply-for-loan'),
    path('loan-rejection/', views.loan_rejection, name='loan-rejection'),
    path('loans/', views.LoanListView.as_view(template_name='finance/payments/loans.html'), name='trainingloans'),
    path('loan-confirmation/', views.loan_application_confirmation, name='loan-confirmation'),
    # Aliases to support template/test reverse names
    path('loan-application-confirmation/', views.loan_application_confirmation, name='loan-application-confirmation'),
    path('user-loans/', views.userLoanListView.as_view(), name='user-loans'),
    path('loan/<int:pk>/', views.loan_detail, name='loan-detail'),
    path('collateral-form/<int:loan_id>/', views.collateral_form, name='collateral-form'),
    path('submit-collateral/<int:loan_id>/', views.submit_collateral, name='submit-collateral'),
    path('edit-loan/<int:loan_id>/', views.edit_loan, name='edit-loan'),
    path('update-loan/<int:loan_id>/', views.update_loan, name='update-loan'),
    path('apply-for-loan/<int:plan_id>/', views.apply_for_loan, name='apply-for-loan'),
    path('guarantor/request/<int:loan_id>/', views.guarantor_approval_request, name='guarantor-approval-request'),
    path('guarantor/approve/<int:loan_id>/', views.guarantor_approve_loan, name='guarantor-approve-loan'),
    path('guarantor/reject/<int:loan_id>/', views.guarantor_reject_loan, name='guarantor-reject-loan'),
    # guarantor-dashboard URL removed - functionality moved to unified dashboard
    path('guarantor/process-approval/<int:loan_id>/', views.guarantor_process_approval, name='guarantor-process-approval'),
    path('get-guarantor-eligibility-scores/', views.get_guarantor_eligibility_scores, name='get-guarantor-eligibility-scores'),
    # path('newpay/', LoanCreateView.as_view(template_name='finance/payments/payment_form.html'), name='newpay'),
    # path('loanuser/', views.userLoanListView.as_view(), name='loanuser'),
    path('loan/<int:pk>/update/', views.LoanUpdateView.as_view(template_name='finance/payments/payment_form.html'), name='loan-update'),
    #Admin Loan Management
    path('admin/loan-applications/', views.admin_loan_applications, name='admin-loan-applications'),
    path('admin/loan-applications/<int:pk>/approve/', views.approve_loan_application, name='approve-loan-application'),
    path('admin/loan-applications/<int:pk>/reject/', views.reject_loan_application, name='reject-loan-application'),
    path('admin/loan-applications/<int:pk>/recompute/', views.recompute_loan_application, name='recompute-loan-application'),
    path('admin/loan-analytics/', views.loan_analytics, name='loan-analytics'),
    path('admin/smart-collateral-dashboard/', views.smart_collateral_dashboard, name='smart-collateral-dashboard'),
    path('presentation/', views.loan_system_presentation, name='loan-system-presentation'),
    path('my-collateral-status/<int:loan_id>/', views.user_collateral_status, name='user-collateral-status'),
    path('admin/loan-applications/<int:pk>/notify-guarantor-available/', views.notify_guarantor_available, name='notify-guarantor-available'),
     #FOOD & SUPPLIERS
    path(
        "newsupplies/",
        views.FoodCreateView.as_view(
            template_name='main/snippets_templates/generalform.html'
        ),
        name="newsupplies",
    ),
    path(
        "newsupplier/",
        views.SupplierCreateView.as_view(
            template_name='main/snippets_templates/generalform.html'
        ),
        name="newsupplier",
    ),
    path("supplier/update/<int:pk>/",views.SupplierUpdateView.as_view(template_name='main/snippets_templates/generalform.html'),name="update-supplier"),
    path("food/<int:pk>/update",views.FoodUpdateView.as_view(template_name='main/snippets_templates/generalform.html'),name="update-food"),
    path("suppliers/",views.SupplierListView.as_view(),name="suppliers"),    
    path("food/", views.FoodListView.as_view(), name="supplies"),
    path("foodhistory/",views.food_history_view,name="foodhistory"),
    path("foodhistoryupdate/<int:pk>/",views.food_history_update,name="foodhistoryupdate"),
    path('add_budget_item/', views.add_budget_item, name='add_budget_item'),
    path('budget/<str:company_slug>/', views.budget, name='company_budget'),
    path('budget/<int:pk>/update/', views.BudgetUpdateView.as_view(), name='budget-update'),
    path('budget_projection/<int:pk>/update/', views.CodaBudgetUpdateView.as_view(), name='budget_projection-update'),
    path('budget_projection_summary/<int:pk>/update/', views.BudgetSummaryUpdateView.as_view(), name='budget_projection_summary-update'),
    # path("coda_budget_estimation/<str:app>/",views.coda_budget_estimation, name="coda_budget_estimation"),  # View not found - commented out
    # path("budget/<str:subtitle>/<str:duration>/", views.budget_projection, name="budget_projection"),
    path("budget_projection/<str:subtitle>/", views.budget_projection, name="budget_projection"),
    # path('delete_payment_history/', views.delete_bad_entry_in_payment_history, name="delete_bad_entry_in_payment_history"),  # View not found
    
    #=============================ANALYTICS DASHBOARD=====================================
    path('analytics/', lambda request: redirect(reverse('finance:unified-budget-dashboard', kwargs={'company_slug': 'coda'}) + '?tab=analytics'), name='analytics-dashboard'),
    # path('analytics/loan-performance/', views.loan_performance_analytics, name='loan-performance-analytics'),  # View not found
    # path('analytics/kcc-optimization/', views.kcc_optimization_analytics, name='kcc-optimization-analytics'),  # View not found
    # path('analytics/export/', views.analytics_export, name='analytics-export'),  # View not found
    # path('analytics/api/', views.analytics_api, name='analytics-api'),  # View not found
    
    #=============================AUTOMATION DASHBOARD=====================================
    path('automation/', views_automation.automation_dashboard, name='automation-dashboard'),
    path('automation/budget-requests/', views_automation.budget_requests_dashboard, name='budget-requests-dashboard'),
    path('automation/disbursements/', views_automation.disbursements_dashboard, name='disbursements-dashboard'),
    path('automation/policies/', views_automation.approval_policies_dashboard, name='approval-policies-dashboard'),
    path('automation/audit-logs/', views_automation.audit_logs_dashboard, name='audit-logs-dashboard'),
    path('automation/api/', views_automation.automation_dashboard_api, name='automation-dashboard-api'),
    
    #=============================AUTOMATED BUDGET ESTIMATION (DEPRECATED - PHASE 3)=====================================
    # OLD URLs - Redirect to unified dashboard
    path('automated-budget-estimation/', 
         lambda request: redirect(reverse('finance:unified-budget-dashboard', kwargs={'company_slug': 'coda'}) + '?tab=estimation'),
         name='automated-budget-estimation'),
    path('budget-consolidation/', 
         lambda request: redirect(reverse('finance:unified-budget-dashboard', kwargs={'company_slug': 'coda'}) + '?tab=overview'),
         name='budget-consolidation-dashboard'),
    path('consolidation-dashboard/<str:company_slug>/', 
         lambda request, company_slug: redirect(reverse('finance:unified-budget-dashboard', kwargs={'company_slug': company_slug}) + '?tab=overview'),
         name='consolidation-dashboard'),
    path('budget-projection/<str:company_slug>/', 
         lambda request, company_slug: redirect(reverse('finance:unified-budget-dashboard', kwargs={'company_slug': company_slug}) + '?tab=analytics'),
         name='budget-projection-redirect'),
    
    #=============================FINANCE DASHBOARD=====================================
    # Finance dashboard
    path('finance-dashboard/<str:company_slug>/', views_finance_dashboard.finance_dashboard, name='finance-dashboard'),
    path('api/finance-dashboard/<str:company_slug>/', views_finance_dashboard.finance_dashboard_api, name='finance-dashboard-api'),
    
    # Enhanced Legacy Dashboard
    path('legacy-dashboard/<str:company_slug>/', views_legacy_dashboard.enhanced_legacy_dashboard, name='enhanced-legacy-dashboard'),
    path('legacy-dashboard/', views_legacy_dashboard.legacy_dashboard_redirect, name='legacy-dashboard-redirect'),
    
    #=============================SMART FORM API=====================================
    path('api/smart-form/suggestions/', views_api_smart_form.get_form_suggestions, name='smart-form-suggestions'),
    path('api/smart-form/defaults/', views_api_smart_form.get_department_defaults, name='smart-form-defaults'),
    
    #=============================UNIFIED BUDGET SYSTEM (PHASE 3)=====================================
    # New unified dashboard - consolidates all budget views
    path('budget-dashboard/<str:company_slug>/', views_budget_dashboard.unified_budget_dashboard, name='unified-budget-dashboard'),
    path('budget-planning/<str:company_slug>/', views_unified_budget.unified_budget_planning, name='unified-budget-planning'),
    
    # Budget drill-down views (User perspective - Phase 2)
    path('budget/<str:company_slug>/category/<int:category_id>/', views_budget_drilldown.budget_category_detail, name='budget-category-detail'),
    path('budget/<str:company_slug>/category/<int:category_id>/compare/', views_budget_drilldown.budget_comparison_view, name='budget-category-compare'),
    path('budget/<str:company_slug>/item/<int:item_id>/edit/', views_budget_drilldown.budget_item_edit, name='budget-item-edit'),
    
    #=============================ENHANCED BUDGET SYSTEM (DEPRECATED - PHASE 3)=====================================
    # OLD URLs - Redirect to new unified dashboard
    # Enhanced budget dashboard → unified dashboard (planning tab)
    path('enhanced-budget-dashboard/<str:company_slug>/', 
         lambda request, company_slug: redirect(reverse('finance:unified-budget-dashboard', kwargs={'company_slug': company_slug}) + '?tab=planning'),
         name='enhanced-budget-dashboard'),
    
    # Multi-timeframe planning → unified planning with timeframe parameter
    path('weekly-planning/<str:company_slug>/', 
         lambda request, company_slug: redirect(reverse('finance:unified-budget-planning', kwargs={'company_slug': company_slug}) + '?timeframe=weekly'),
         name='weekly-budget-planning'),
    path('monthly-planning/<str:company_slug>/', 
         lambda request, company_slug: redirect(reverse('finance:unified-budget-planning', kwargs={'company_slug': company_slug}) + '?timeframe=monthly'),
         name='monthly-budget-planning'),
    path('yearly-planning/<str:company_slug>/', 
         lambda request, company_slug: redirect(reverse('finance:unified-budget-planning', kwargs={'company_slug': company_slug}) + '?timeframe=yearly'),
         name='yearly-budget-planning'),
    path('multi-year-planning/<str:company_slug>/', 
         lambda request, company_slug: redirect(reverse('finance:unified-budget-planning', kwargs={'company_slug': company_slug}) + '?timeframe=multi_year&periods=2'),
         name='multi-year-planning'),
    
    # CODA development estimation
    path('coda-development-estimation/<str:company_slug>/', views_enhanced_budget.coda_development_estimation, name='coda-development-estimation'),
    
    # Investment planning
    path('investment-planning/<str:company_slug>/', views_enhanced_budget.investment_planning, name='investment-planning'),
    
    # Budget consolidation report
    path('consolidation-report/<str:company_slug>/', views_enhanced_budget.budget_consolidation_report, name='consolidation-report'),
    
    # API endpoints
    path('api/create-budget-from-estimation/<str:company_slug>/', views_enhanced_budget.create_budget_from_estimation, name='create-budget-from-estimation'),

    # Projections review UI
    path('projections/', views_projections.projections_list, name='projections-list'),

    # User-facing Estimate Wizard
    path('estimates/', views_estimates.estimate_wizard, name='estimates-wizard'),
    
        # Budget Projection Approvals
        path('approvals/projections/', approvals.budget_projection_approvals, name='budget-projection-approvals'),
        path('approvals/projections/<int:projection_id>/', approvals.approve_budget_projection, name='approve-projection'),
        path('approvals/projections/<int:projection_id>/detail/', approvals.budget_projection_detail, name='projection-detail'),
        path('my-projections/', approvals.my_budget_projections, name='my-projections'),
        
        # Enhanced Budget Approvals with 33% Compliance
        path('approvals/enhanced/', approvals.enhanced_budget_projection_approvals, name='enhanced-budget-approvals'),
        path('approvals/compliance/', approvals.compliance_report_dashboard, name='compliance-dashboard'),
        path('approvals/compliance/export/', approvals.compliance_export, name='compliance-export'),
        path('approvals/compliance/employee/<int:employee_id>/', approvals.individual_compliance_detail, name='individual-compliance'),
        path('approvals/compliance/department/<int:department_id>/', approvals.department_compliance_detail, name='department-compliance'),
        path('approvals/budget/<int:budget_id>/compliance/', approvals.budget_compliance_integration, name='budget-compliance'),
        path('api/send-compliance-notifications/', approvals.send_compliance_notifications, name='send-compliance-notifications'),
        
        # Detailed Budget Breakdown
        path('detailed-breakdown/<int:projection_id>/', views_detailed_budget.detailed_budget_breakdown, name='detailed-budget-breakdown'),
        path('detailed-breakdown/<int:projection_id>/save-item/', views_detailed_budget.save_item_estimate, name='save-item-estimate'),
        path('detailed-breakdown/<int:projection_id>/submit/', views_detailed_budget.submit_detailed_estimate, name='submit-detailed-estimate'),
        path('create-detailed/', views_detailed_budget.create_detailed_projection, name='create-detailed-projection'),
    
    #=============================UNIFIED DEPARTMENT DASHBOARD=====================================
    # Unified department dashboard (serves all departments)
    path('department/<str:department_name>/', views_unified_department.unified_department_dashboard, name='unified-department-dashboard'),
    path('api/department/<str:department_name>/', views_unified_department.department_dashboard_api, name='department-dashboard-api'),
    path('api/search-links/', views_unified_department.search_department_links, name='search-department-links'),
    
    #=============================USER-FRIENDLY BUDGET REQUEST FORMS=====================================
    # Budget request forms for regular users
    path('budget-requests/create/', views_forms.budget_request_form, name='budget_request_form'),
    path('budget-requests/', views_forms.budget_requests_list, name='budget_requests_list'),
    path('budget-requests/<int:pk>/', views_forms.budget_request_detail, name='budget_request_detail'),
    path('budget-requests/<int:pk>/edit/', views_forms.budget_request_edit, name='budget_request_edit'),
    path('budget-requests/<int:pk>/submit/', views_forms.submit_for_approval, name='submit_for_approval'),
    path('budget-requests/<int:pk>/approve/', views_forms.approve_request, name='approve_request'),
    path('budget-requests/<int:pk>/reject/', views_forms.reject_request, name='reject_request'),

    #=============================BUDGET EDITING & APPROVAL SYSTEM (PHASE 2)=====================================
    # Budget editing with approval workflow
    path('budget/<str:company_slug>/category/<int:category_id>/edit/', views_budget_editing.budget_category_edit, name='budget-category-edit'),
    path('budget/<str:company_slug>/category/<int:category_id>/save/', views_budget_editing.save_budget_estimates, name='save-budget-estimates'),
    path('budget/<str:company_slug>/requests/', views_budget_editing.budget_requests_list, name='budget-requests-list'),
    path('budget/<str:company_slug>/requests/<int:request_id>/', views_budget_editing.budget_request_detail, name='budget-request-detail'),
    path('budget/<str:company_slug>/requests/<int:request_id>/approve/', views_budget_editing.approve_budget_request, name='approve-budget-request'),
    path('budget/<str:company_slug>/requests/<int:request_id>/reject/', views_budget_editing.reject_budget_request, name='reject-budget-request'),
    path('budget/<str:company_slug>/approvals/', views_budget_editing.budget_approval_dashboard, name='budget-approval-dashboard'),

    #=============================PHASE 2: FINANCE MANAGER TIER CONTROLS=====================================
    # Finance Manager interface for managing budget category tiers and auto-approval
    path('tier-management/<str:company_slug>/', views_tier_management.tier_management_dashboard, name='tier-management-dashboard'),
    path('tier/auto-approval-log/<str:company_slug>/', views_tier_management.auto_approval_log, name='auto-approval-log'),
    
    # API endpoints for tier management
    path('api/tier/toggle-auto-approval/<int:category_id>/', views_tier_management.toggle_auto_approval, name='api-toggle-auto-approval'),
    path('api/tier/update-variance-threshold/<int:category_id>/', views_tier_management.update_variance_threshold, name='api-update-variance-threshold'),
    path('api/tier/run-reclassification/<str:company_slug>/', views_tier_management.run_tier_reclassification, name='api-run-reclassification'),

    #=============================LOAN-BUDGET INTEGRATION (PHASE 3)=====================================
    # Loan system integrated with budget constraints
    path('loan/<str:company_slug>/eligibility/', views_loan_budget_integration.loan_eligibility_check, name='loan-eligibility-check'),
    path('loan/<str:company_slug>/apply/', views_loan_budget_integration.loan_application_with_budget, name='loan-application-with-budget'),
    path('loan/<str:company_slug>/dashboard/', views_loan_budget_integration.loan_budget_dashboard, name='loan-budget-dashboard'),
    path('loan/<str:company_slug>/impact-analysis/', views_loan_budget_integration.budget_loan_impact_analysis, name='budget-loan-impact-analysis'),

    #=============================SALARY DASHBOARD & INTEGRATION (PHASE 3)=====================================
    # Salary dashboard and budget integration
    path('salary/dashboard/', views_salary_dashboard.salary_dashboard, name='salary-dashboard'),
    path('salary/employee/<int:employee_id>/', views_salary_dashboard.employee_salary_detail, name='employee-salary-detail'),
    path('api/salary/compliance-report/', views_salary_dashboard.salary_compliance_report, name='salary-compliance-report'),
    path('api/salary/update-compliance/', views_salary_dashboard.update_compliance_status, name='update-compliance-status'),
    path('api/salary/export/', views_salary_dashboard.salary_export, name='salary-export'),

    #=============================REAL-TIME COMPLIANCE MONITORING (PHASE 3)=====================================
    # Real-time compliance monitoring and notifications
    path('realtime/compliance-dashboard/', views_realtime_compliance.realtime_compliance_dashboard, name='realtime-compliance-dashboard'),
    path('api/realtime/trigger-monitoring/', views_realtime_compliance.trigger_compliance_monitoring, name='trigger-compliance-monitoring'),
    path('api/realtime/send-reminders/', views_realtime_compliance.send_compliance_reminders, name='send-compliance-reminders'),
    path('api/realtime/dashboard-data/', views_realtime_compliance.get_realtime_dashboard_data, name='realtime-dashboard-data'),
    path('api/realtime/check-employee/<int:employee_id>/', views_realtime_compliance.check_employee_compliance_status, name='check-employee-compliance'),
    path('api/realtime/compliance-statistics/', views_realtime_compliance.get_compliance_statistics, name='compliance-statistics'),

    #=============================ADMIN CONTROLS & REGULATIONS (PHASE 3)=====================================
    # Admin controls for employee regulations and overrides
    path('admin/controls-dashboard/', views_admin_controls.admin_controls_dashboard, name='admin-controls-dashboard'),
    path('api/admin/employee-regulations/', views_admin_controls.get_employee_regulations, name='employee-regulations'),
    path('api/admin/update-threshold/', views_admin_controls.update_compliance_threshold, name='update-compliance-threshold'),
    path('api/admin/create-override/', views_admin_controls.create_employee_override, name='create-employee-override'),
    path('api/admin/employee-compliance/<int:employee_id>/', views_admin_controls.get_employee_compliance_with_overrides, name='employee-compliance-with-overrides'),
    path('api/admin/statistics/', views_admin_controls.get_admin_statistics, name='admin-statistics'),
    path('api/admin/audit-log/', views_admin_controls.get_audit_log, name='audit-log'),
    path('api/admin/export-report/', views_admin_controls.export_admin_report, name='export-admin-report'),

    #=============================BUDGET TIER SYSTEM PRESENTATIONS=====================================
    # MIGRATED to portfolio app - Redirects for backward compatibility
    path('budget-tier-presentation/', lambda request: redirect('/portfolio/budget-tier/investor/', permanent=True), name='budget-tier-presentation'),
    path('budget-tier-presentation-guide/', lambda request: redirect('/portfolio/guide/', permanent=True), name='budget-tier-presentation-guide'),
]

# Unified Payment System URLs
urlpatterns += [
    # Payment Method Selection
    path('unified/methods/', unified_payment_selection, name='unified_method_selection'),
    
    # Payment Processing
    path('unified/process/<str:method>/', unified_payment_processing, name='unified_processing'),
    
    # Payment Results
    path('unified/success/', unified_payment_success, name='unified_success'),
    path('unified/failed/', unified_payment_failed, name='unified_failed'),
    
    # Payment Details (Universal Fallback)
    path('payment-details/<str:method>/', show_payment_details, name='payment_details'),
    path('payment-proof/upload/<str:reference>/', upload_payment_proof, name='upload_payment_proof'),
    
    # Payment Dashboard (User)
    path('my-payments/', payment_dashboard, name='payment_dashboard'),
    path('payment/retry/<int:payment_id>/', retry_payment, name='retry_payment'),
    
    # Payment Receipts
    path('receipt/<int:payment_id>/', view_receipt, name='view_receipt'),
    path('receipt/<int:payment_id>/download/', download_receipt, name='download_receipt'),
    path('receipt/<int:payment_id>/email/', email_receipt, name='email_receipt'),
    path('verify-payment/<int:payment_id>/', verify_payment_receipt, name='verify_payment_receipt'),
    
    # Admin Payment Verification
    path('admin/verify-payments/', admin_payment_verification_dashboard, name='admin_payment_verification'),
    path('admin/payment/<int:payment_id>/approve/', approve_payment, name='approve_payment'),
    path('admin/payment/<int:payment_id>/reject/', reject_payment, name='reject_payment'),
    path('admin/payments/bulk-approve/', bulk_approve_payments, name='bulk_approve_payments'),
    
    # M-Pesa OTP Verification Flow
    path('unified/mpesa-otp/', unified_mpesa_otp, name='mpesa_otp_confirmation'),
    path('unified/verify-otp/', unified_verify_otp, name='verify_mpesa_otp'),
    
    # Stripe Payment Integration
    path('stripe/payment-intent/', create_payment_intent, name='stripe_payment_intent'),
    path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),
]