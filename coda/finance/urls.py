from django.urls import path
from . import views
from .views import (
                    PaymentCreateView,TransanctionDetailView,TransactionUpdateView,TransactionDeleteView,
                    UserInflowListView,InflowDetailView,InflowUpdateView,InflowDeleteView,
                    DefaultPaymentUpdateView,DefaultPaymentListView,LoanListView,LoanUpdateView,
                    save_and_upload_to_drive,FoodListView
)
# Import new unified payment views
from . import payment_views

# Import automation dashboard views
from . import views_automation

# Import enhanced budget views
from . import views_enhanced_budget, views_finance_dashboard, views_legacy_dashboard, views_unified_department
from . import views_projections, views_estimates, views_approvals, views_detailed_budget

# Import unified budget views (Phase 3)
from . import views_unified_budget

# Import budget drill-down views (Phase 2 - User perspective)
from . import views_budget_drilldown

# Import user-friendly form views
from . import views_forms

# Import smart transaction views (Phase 1 Data Cleanup)
from . import views_smart_transaction

# Import cascading form API
from . import api_cascading

# Import auto-prediction API
from . import api_auto_predict

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
    path('save-and-upload/', save_and_upload_to_drive, name='save_and_upload_to_drive'),
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
    path('transaction/<int:pk>/', TransanctionDetailView.as_view(), name='transaction-detail'),
    path('transaction/<int:pk>/update/', TransactionUpdateView.as_view(template_name="finance/payments/transaction_form.html"), name='transaction-update'),
    path('transaction/<int:pk>/delete/', TransactionUpdateView.as_view(template_name="finance/payments/transaction_confirm_delete.html"), name='transaction-delete'),
     #-----------CASHINFLOW---------------------------------------
    path('inflow_entry/', views.inflow, name='entry_inflow'),
    path('cashflows/<str:type>/', views.cashflows, name='cashflows-list'),
    path('user_inflow/', UserInflowListView.as_view(), name='user-list'),
    path('inflow/<int:pk>/', InflowDetailView.as_view(), name='inflow-detail'),
    path('inflow/<int:pk>/delete/', InflowDetailView.as_view(), name='inflow-delete'),
    path('inflow/<int:pk>/update/', InflowUpdateView.as_view(template_name="finance/cashflows/inflow_form.html"), name='inflow-update'),
    #=============================CLIENT CASHFLOW=====================================
    path('clientinflows/<str:username>/', views.clientinflows, name='userclientinflows'),
    #=============================CLIENT CONTRACT FORM SUBMISSIONS=====================================
    path('contract_data/', views.contract_data_submission, name='contract_data_submission'),
    path('investment_submission/', views.contract_investment_submission, name='investment_submission'),
    path('mycontract/<str:username>/', views.mycontract, name='mycontract'),
    path('newcontract/<str:username>/', views.new_contract, name='newcontract'),
    path('newinvestmentcontract/<int:plan_id>/', views.new_investment_contract, name='newinvestmentcontract'),
    path('pay/', views.pay, name='pay'),
    path('payment/<int:service>/', views.pay, name='service_pay'),
    path('payment_method/<str:method>/', views.payment, name='payment_method'),
    path("payment_complete/", views.paymentComplete, name="payment_complete"),
    path('payments/<str:title>/<str:status>/', views.payments, name='payments'),
    path('payment_plan/<str:payment_id>', views.payment_plan, name='payment_plan'),
    path('mpesa-payment/', views.MpesaPaymentView, name='mpesa_payment'),
    path('otp-confirmation/', views.verify_otp, name='otp_confirmation'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('pay/<int:pk>/', views.UserPayUpdateView.as_view(), name='updatepay'),
    
    #=============================UNIFIED PAYMENT SYSTEM=====================================
    # New unified payment URLs
    path('unified/methods/', payment_views.payment_method_selection, name='unified_method_selection'),
    path('unified/process/<str:method>/', payment_views.payment_processing, name='unified_processing'),
    path('unified/success/', payment_views.payment_success, name='unified_success'),
    path('unified/failed/', payment_views.payment_failed, name='unified_failed'),
    # path('visitor/<str:method>/', payment_views.process_visitor_payment, name='visitor_payment'),
    
    # MPESA OTP verification
    path('mpesa-otp-confirmation/', payment_views.mpesa_otp_confirmation, name='mpesa_otp_confirmation'),
    path('verify-mpesa-otp/', payment_views.verify_mpesa_otp, name='verify_mpesa_otp'),
    
    # Legacy payment URLs (maintained for backward compatibility)
    path('defaultpayments/', DefaultPaymentListView.as_view(template_name='finance/payments/defaultpayments.html'), name='defaultpayments'),
    path('newpayment/', PaymentCreateView.as_view(template_name='finance/payments/payment_form.html'), name='newpayment'),
    path('payment/<int:pk>/update/', DefaultPaymentUpdateView.as_view(template_name='finance/payments/payment_form.html'), name='payment-update'),
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
    path('loans/', LoanListView.as_view(template_name='finance/payments/loans.html'), name='trainingloans'),
    path('loan-confirmation/', views.loan_application_confirmation, name='loan-confirmation'),
    # Aliases to support template/test reverse names
    path('loan-application-confirmation/', views.loan_application_confirmation, name='loan-application-confirmation'),
    path('user-loans/', views.userLoanListView.as_view(), name='user-loans'),
    path('apply-for-loan/<int:plan_id>/', views.apply_for_loan, name='apply-for-loan'),
    path('guarantor/request/<int:loan_id>/', views.guarantor_approval_request, name='guarantor-approval-request'),
    path('guarantor/approve/<int:loan_id>/', views.guarantor_approve_loan, name='guarantor-approve-loan'),
    path('guarantor/reject/<int:loan_id>/', views.guarantor_reject_loan, name='guarantor-reject-loan'),
    # guarantor-dashboard URL removed - functionality moved to unified dashboard
    path('guarantor/process-approval/<int:loan_id>/', views.guarantor_process_approval, name='guarantor-process-approval'),
    path('get-guarantor-eligibility-scores/', views.get_guarantor_eligibility_scores, name='get-guarantor-eligibility-scores'),
    # path('newpay/', LoanCreateView.as_view(template_name='finance/payments/payment_form.html'), name='newpay'),
    # path('loanuser/', views.userLoanListView.as_view(), name='loanuser'),
    path('loan/<int:pk>/update/', LoanUpdateView.as_view(template_name='finance/payments/payment_form.html'), name='loan-update'),
    #Admin Loan Management
    path('admin/loan-applications/', views.admin_loan_applications, name='admin-loan-applications'),
    path('admin/loan-applications/<int:pk>/approve/', views.approve_loan_application, name='approve-loan-application'),
    path('admin/loan-applications/<int:pk>/reject/', views.reject_loan_application, name='reject-loan-application'),
    path('admin/loan-applications/<int:pk>/recompute/', views.recompute_loan_application, name='recompute-loan-application'),
    path('admin/loan-analytics/', views.loan_analytics, name='loan-analytics'),
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
    path("food/", FoodListView.as_view(), name="supplies"),
    path("foodhistory/",views.food_history_view,name="foodhistory"),
    path("foodhistoryupdate/<int:pk>/",views.food_history_update,name="foodhistoryupdate"),
    path('add_budget_item/', views.add_budget_item, name='add_budget_item'),
    path('budget/<str:company_slug>/', views.budget, name='company_budget'),
    path('budget/<int:pk>/update/', views.BudgetUpdateView.as_view(), name='budget-update'),
    path('budget_projection/<int:pk>/update/', views.CodaBudgetUpdateView.as_view(), name='budget_projection-update'),
    path('budget_projection_summary/<int:pk>/update/', views.BudgetSummaryUpdateView.as_view(), name='budget_projection_summary-update'),
    path("coda_budget_estimation/<str:app>/",views.coda_budget_estimation, name="coda_budget_estimation"),
    # path("budget/<str:subtitle>/<str:duration>/", views.budget_projection, name="budget_projection"),
    path("budget_projection/<str:subtitle>/", views.budget_projection, name="budget_projection"),
    path('delete_payment_history/', views.delete_bad_entry_in_payment_history, name="delete_bad_entry_in_payment_history"),
    
    #=============================ANALYTICS DASHBOARD=====================================
    path('analytics/', views.analytics_dashboard, name='analytics-dashboard'),
    path('analytics/loan-performance/', views.loan_performance_analytics, name='loan-performance-analytics'),
    path('analytics/kcc-optimization/', views.kcc_optimization_analytics, name='kcc-optimization-analytics'),
    path('analytics/export/', views.analytics_export, name='analytics-export'),
    path('analytics/api/', views.analytics_api, name='analytics-api'),
    
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
         lambda request: redirect('finance:unified-budget-dashboard', company_slug='coda', permanent=False) + '?tab=estimation',
         name='automated-budget-estimation'),
    path('budget-consolidation/', 
         lambda request: redirect('finance:unified-budget-dashboard', company_slug='coda', permanent=False) + '?tab=overview',
         name='budget-consolidation-dashboard'),
    path('consolidation-dashboard/<str:company_slug>/', 
         lambda request, company_slug: redirect('finance:unified-budget-dashboard', company_slug=company_slug, permanent=False) + '?tab=overview',
         name='consolidation-dashboard'),
    path('budget-projection/<str:company_slug>/', 
         lambda request, company_slug: redirect('finance:unified-budget-dashboard', company_slug=company_slug, permanent=False) + '?tab=analytics',
         name='budget-projection-redirect'),
    
    #=============================FINANCE DASHBOARD=====================================
    # Finance dashboard
    path('finance-dashboard/<str:company_slug>/', views_finance_dashboard.finance_dashboard, name='finance-dashboard'),
    path('api/finance-dashboard/<str:company_slug>/', views_finance_dashboard.finance_dashboard_api, name='finance-dashboard-api'),
    
    # Enhanced Legacy Dashboard
    path('legacy-dashboard/<str:company_slug>/', views_legacy_dashboard.enhanced_legacy_dashboard, name='enhanced-legacy-dashboard'),
    path('legacy-dashboard/', views_legacy_dashboard.legacy_dashboard_redirect, name='legacy-dashboard-redirect'),
    
    #=============================UNIFIED BUDGET SYSTEM (PHASE 3)=====================================
    # New unified dashboard - consolidates all budget views
    path('budget-dashboard/<str:company_slug>/', views_unified_budget.unified_budget_dashboard, name='unified-budget-dashboard'),
    path('budget-planning/<str:company_slug>/', views_unified_budget.unified_budget_planning, name='unified-budget-planning'),
    
    # Budget drill-down views (User perspective - Phase 2)
    path('budget/<str:company_slug>/category/<int:category_id>/', views_budget_drilldown.budget_category_detail, name='budget-category-detail'),
    path('budget/<str:company_slug>/category/<int:category_id>/compare/', views_budget_drilldown.budget_comparison_view, name='budget-category-compare'),
    path('budget/item/<int:item_id>/edit/', views_budget_drilldown.budget_item_edit, name='budget-item-edit'),
    
    #=============================ENHANCED BUDGET SYSTEM (DEPRECATED - PHASE 3)=====================================
    # OLD URLs - Redirect to new unified dashboard
    # Enhanced budget dashboard → unified dashboard (planning tab)
    path('enhanced-budget-dashboard/<str:company_slug>/', 
         lambda request, company_slug: redirect('finance:unified-budget-dashboard', company_slug=company_slug, permanent=False) + '?tab=planning',
         name='enhanced-budget-dashboard'),
    
    # Multi-timeframe planning → unified planning with timeframe parameter
    path('weekly-planning/<str:company_slug>/', 
         lambda request, company_slug: redirect('finance:unified-budget-planning', company_slug=company_slug, permanent=False) + '?timeframe=weekly',
         name='weekly-budget-planning'),
    path('monthly-planning/<str:company_slug>/', 
         lambda request, company_slug: redirect('finance:unified-budget-planning', company_slug=company_slug, permanent=False) + '?timeframe=monthly',
         name='monthly-budget-planning'),
    path('yearly-planning/<str:company_slug>/', 
         lambda request, company_slug: redirect('finance:unified-budget-planning', company_slug=company_slug, permanent=False) + '?timeframe=yearly',
         name='yearly-budget-planning'),
    path('multi-year-planning/<str:company_slug>/', 
         lambda request, company_slug: redirect('finance:unified-budget-planning', company_slug=company_slug, permanent=False) + '?timeframe=multi_year&periods=2',
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
        path('approvals/projections/', views_approvals.budget_projection_approvals, name='budget-projection-approvals'),
        path('approvals/projections/<int:projection_id>/', views_approvals.approve_budget_projection, name='approve-projection'),
        path('approvals/projections/<int:projection_id>/detail/', views_approvals.budget_projection_detail, name='projection-detail'),
        path('my-projections/', views_approvals.my_budget_projections, name='my-projections'),
        
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
]