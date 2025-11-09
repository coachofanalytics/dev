from django.urls import path, include

from . import views

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
