from django.urls import path, include

from . import views
from .views.shareholders import views as sh_views, views_snapshots as sh_snapshots

# =============================================================================
# SHAREHOLDERS MANAGEMENT URLS
# =============================================================================
# CONSOLIDATED from investing/urls_shareholders.py — March 2026
# These patterns are imported by coda_project/urls.py for top-level namespace
# =============================================================================
shareholders_urlpatterns = [
    # Dashboard & Ledgers
    path('dashboard/', sh_views.shareholders_dashboard, name='shareholders_dashboard'),
    path('ledgers/', sh_views.ledgers_view, name='ledgers_view'),

    # Deal Configuration (Phase 2: Full Backend)
    path('deal-config/', sh_views.deal_config_view, name='deal_config'),
    path('deal-config/save/', sh_views.deal_config_save, name='deal_config_save'),

    # Audit Log (Phase 1: Frontend-Only UI)
    path('audit-log/', sh_views.audit_log_view, name='audit_log'),

    # Snapshots (Phase 2: Full Backend)
    path('snapshots/', sh_views.snapshots_view, name='snapshots_view'),
    path('snapshots/create/', sh_views.snapshot_create, name='snapshot_create'),
    path('snapshots/export/', sh_snapshots.snapshots_export_csv, name='snapshots_export_csv'),
    path('snapshots/<int:snapshot_id>/', sh_snapshots.snapshot_detail, name='snapshot_detail'),
    path('snapshots/<int:snapshot_id>/lock/', sh_snapshots.snapshot_lock, name='snapshot_lock'),
    path('snapshots/<int:snapshot_id>/export/', sh_snapshots.snapshot_export_detail_csv, name='snapshot_export_detail_csv'),

    # Phase 2: Ledger Actions
    path('ledgers/export/', sh_views.ledgers_export_csv, name='ledgers_export_csv'),
    path('ledgers/<str:tx_id>/', sh_views.ledger_detail, name='ledger_detail'),
    path('ledgers/<str:tx_id>/receipt/', sh_views.ledger_receipt, name='ledger_receipt'),
    path('ledgers/<str:tx_id>/proof/', sh_views.ledger_proof, name='ledger_proof'),
    path('ledgers/<str:tx_id>/approve/', sh_views.ledger_approve, name='ledger_approve'),
    path('ledgers/<str:tx_id>/dispute/', sh_views.ledger_dispute, name='ledger_dispute'),

    # Members & Equity
    path('members/', sh_views.members_overview, name='members_overview'),
    path('members/register/', sh_views.member_register, name='member_register'),
    path('members/<int:member_id>/', sh_views.member_detail, name='member_detail'),
    path('members/<int:member_id>/edit/', sh_views.member_edit, name='member_edit'),

    # Contributions
    path('contributions/new/', sh_views.contribution_log, name='contribution_log'),

    # Direct Deposit Flow (Phase 6: Full deposit → contribution pipeline)
    path('deposit/', sh_views.shareholder_deposit, name='shareholder_deposit'),
    path('deposit/process/<str:method>/', sh_views.shareholder_deposit_process, name='shareholder_deposit_process'),
    path('deposit/success/', sh_views.shareholder_deposit_success, name='shareholder_deposit_success'),

    # Real Payment Gateway AJAX Endpoints
    path('deposit/paypal/capture/', sh_views.shareholder_paypal_capture, name='shareholder_paypal_capture'),
    path('deposit/cashapp/capture/', sh_views.shareholder_cashapp_capture, name='shareholder_cashapp_capture'),
    path('deposit/mpesa/stk-push/', sh_views.shareholder_mpesa_stk_push, name='shareholder_mpesa_stk_push'),
    path('deposit/mpesa/check-status/', sh_views.shareholder_mpesa_check_status, name='shareholder_mpesa_check_status'),
]


app_name = "investing"
urlpatterns = [
    path("", views.InvestmentPlatformOverview, name="home"),
    path("training/", views.training, name="training"),
    path("newinvestment/", views.newinvestment, name="newinvestment"),
    path(
        "InvestmentPlatformOverview/",
        views.InvestmentPlatformOverview,
        name="InvestmentPlatformOverview",
    ),
    
    path("newinvestmentrate/", views.newinvestmentrate, name="newinvestmentrate"),
    path("investments/", views.investments, name="investments"),
    path("companyreturns/<str:title>/", views.options_returns, name="companyreturns"),
    path("costbasis/", views.cost_basis, name="costbasis"),
    path(
        "user_investments/<str:username>/",
        views.user_investments,
        name="user_investments",
    ),
    path("options/<str:title>/", views.OptionListView.as_view(), name="option_list"),
    path(
        "creditspreadupdate/<int:pk>",
        views.credit_spread_update,
        name="creditspreadupdate",
    ),
    path("myportfolio/", views.PortfolioListView.as_view(), name="my_portfolio"),
    path("myportfoliocreate/", views.portfolioCreate, name="portfoliocreate"),
    path("myportfolioupdate/<str:symbol>", views.portfolio, name="portfolioupdate"),
    path("coveredupdate/<int:pk>", views.covered_update, name="coveredupdate"),
    path("shortputupdate/<int:pk>", views.shortput_update, name="shortputupdate"),
    path("overboughtsold/<str:symbol>", views.oversoldpositions, name="overboughtsold"),
    path("measures/", views.ticker_measures, name="ticker_measures"),
    path(
        "oversoldupdate/<int:pk>",
        views.oversold_update.as_view(),
        name="oversoldupdate",
    ),
    path("investstrategy/", views.list_investment_strategies, name="investstrategy"),
    path(
        "investstrategycreate/",
        views.create_investment_strategies,
        name="investstrategycreate",
    ),
    path(
        "investstrategyupdate/<int:pk>",
        views.update_investment_strategies,
        name="investstrategyupdate",
    ),
    path(
        "investmentupdate/<int:pk>",
        views.Investment_Update_View.as_view(),
        name="investmentupdate",
    ),
    path(
        "investmentplans/",
        views.InvestmentPlanListView.as_view(),
        name="investment_plan_list",
    ),
    path(
        "investment-plans/<int:pk>/",
        views.investment_plan_detail,
        name="investment_plan_detail",
    ),
    # Individual Investment Management
    path(
        "individual-investments/",
        views.IndividualInvestmentListView.as_view(),
        name="individual_investments",
    ),
    path(
        "individual-investment/<int:pk>/",
        views.IndividualInvestmentDetailView.as_view(),
        name="individual_investment_detail",
    ),
    path(
        "create-individual-investment/",
        views.create_individual_investment,
        name="create_individual_investment",
    ),
    # Investment Dashboard
    path("dashboard/", views.investment_dashboard, name="investment_dashboard"),
    # Unified Investment Application
    path("apply/", views.apply_for_investment, name="apply_for_investment"),
    # Performance Management (Admin functions)
    path(
        "update-performance/<int:investment_id>/",
        views.update_investment_performance,
        name="update_investment_performance",
    ),
    # Upgrade Offers
    path(
        "accept-upgrade/<int:offer_id>/",
        views.accept_upgrade_offer,
        name="accept_upgrade_offer",
    ),
    # API Endpoints
    path(
        "api/analytics/",
        views.investment_analytics_api,
        name="investment_analytics_api",
    ),
    
    # Risk Management URLs
    path("risk/", include("investing.urls_risk_management")),
    
    # Managed Options Trading URLs
    path("managed/", include("investing.urls_managed_trading")),
]
