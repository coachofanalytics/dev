"""
API URL Configuration

This module contains URL patterns for all API endpoints in the CODA application.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from .viewsets import (
    UserViewSet, DepartmentViewSet, GroupViewSet,
    LoanProductViewSet, LoanApplicationViewSet, PaymentInformationViewSet,
    BudgetViewSet, InvestmentRatesViewSet, InvestorInformationViewSet,
    EmployeeViewSet, TaskViewSet, MeetingViewSet,
    AIAnalysisViewSet, StockAnalysisViewSet,
    TrainingProgramViewSet, AssessmentViewSet,
    DashboardViewSet, BudgetRequestViewSet, ApprovalPolicyViewSet,
    DisbursementRequestViewSet, AutomationAuditLogViewSet
)
from finance.api.budget_estimation_api import BudgetEstimationAPIView

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'loan-products', LoanProductViewSet)
router.register(r'loan-applications', LoanApplicationViewSet)
router.register(r'payments', PaymentInformationViewSet)
router.register(r'budgets', BudgetViewSet)
router.register(r'investment-rates', InvestmentRatesViewSet)
router.register(r'investments', InvestorInformationViewSet)
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'tasks', TaskViewSet)
router.register(r'meetings', MeetingViewSet)
router.register(r'ai-analysis', AIAnalysisViewSet)
router.register(r'stock-analysis', StockAnalysisViewSet)
router.register(r'training-programs', TrainingProgramViewSet)
router.register(r'assessments', AssessmentViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'budget-requests', BudgetRequestViewSet)
router.register(r'approval-policies', ApprovalPolicyViewSet)
router.register(r'disbursement-requests', DisbursementRequestViewSet)
router.register(r'audit-logs', AutomationAuditLogViewSet)
router.register(r'budget-estimation', BudgetEstimationAPIView, basename='budget-estimation')

# API URL patterns
urlpatterns = [
    # API v1 routes
    path('v1/', include(router.urls)),
    
    # Authentication
    path('v1/auth/token/', obtain_auth_token, name='api_token_auth'),
    
    # API Documentation
    path('v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('v1/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('v1/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API root
    path('', include(router.urls)),
]


