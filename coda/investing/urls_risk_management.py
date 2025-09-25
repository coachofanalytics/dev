"""
Enhanced Risk Management URL Patterns for Investing App
Uses optimized models and provides comprehensive risk management routes
"""

from django.urls import path, include
from . import views_risk_management

app_name = 'investing_risk'

urlpatterns = [
    # Risk Management Dashboard
    path('risk-dashboard/', views_risk_management.RiskManagementDashboardView.as_view(), name='risk-dashboard'),
    
    # Risk Assessment URLs
    path('risk-assessment/create/', views_risk_management.RiskAssessmentCreateView.as_view(), name='risk-assessment-create'),
    path('risk-assessment/create/<int:investment_id>/', views_risk_management.RiskAssessmentCreateView.as_view(), name='risk-assessment-create-for-investment'),
    
    # Compliance Tracking URLs
    path('compliance-tracking/', views_risk_management.ComplianceTrackingView.as_view(), name='compliance-tracking'),
    
    # Risk Alert URLs
    path('risk-alerts/', views_risk_management.RiskAlertManagementView.as_view(), name='risk-alerts'),
    
    # Analytics and API URLs
    path('api/risk-analytics/', views_risk_management.risk_analytics_api, name='risk-analytics-api'),
    path('auto-risk-assessment/<int:investment_id>/', views_risk_management.auto_risk_assessment, name='auto-risk-assessment'),
    
    # TODO: Add remaining URLs as views are implemented
    # path('risk-assessment/<int:pk>/', views_risk_management.RiskAssessmentDetailView.as_view(), name='risk-assessment-detail'),
    # path('risk-assessment/<int:pk>/edit/', views_risk_management.RiskAssessmentUpdateView.as_view(), name='risk-assessment-edit'),
    # path('compliance-record/create/', views_risk_management.ComplianceRecordCreateView.as_view(), name='compliance-record-create'),
    # path('compliance-record/<int:pk>/', views_risk_management.ComplianceRecordDetailView.as_view(), name='compliance-record-detail'),
    # path('compliance-record/<int:pk>/edit/', views_risk_management.ComplianceRecordUpdateView.as_view(), name='compliance-record-edit'),
    # path('risk-alert/create/', views_risk_management.RiskAlertCreateView.as_view(), name='risk-alert-create'),
    # path('risk-alert/<int:pk>/resolve/', views_risk_management.RiskAlertResolveView.as_view(), name='risk-alert-resolve'),
    # path('bulk-risk-assessment/', views_risk_management.BulkRiskAssessmentView.as_view(), name='bulk-risk-assessment'),
    # path('bulk-compliance-update/', views_risk_management.BulkComplianceUpdateView.as_view(), name='bulk-compliance-update'),
    # path('risk-report/', views_risk_management.RiskReportView.as_view(), name='risk-report'),
    # path('compliance-report/', views_risk_management.ComplianceReportView.as_view(), name='compliance-report'),
    # path('investor-communication/', views_risk_management.InvestorCommunicationView.as_view(), name='investor-communication'),
    # path('communication/create/', views_risk_management.InvestorCommunicationCreateView.as_view(), name='communication-create'),
    # path('notification-preferences/', views_risk_management.NotificationPreferencesView.as_view(), name='notification-preferences'),
    # path('notification-preference/create/', views_risk_management.NotificationPreferenceCreateView.as_view(), name='notification-preference-create'),
    # path('advanced-analytics/', views_risk_management.AdvancedAnalyticsView.as_view(), name='advanced-analytics'),
    # path('analytics/create/', views_risk_management.InvestmentAnalyticsCreateView.as_view(), name='analytics-create'),
    # path('risk-mitigation/', views_risk_management.RiskMitigationView.as_view(), name='risk-mitigation'),
    # path('mitigation-strategy/create/', views_risk_management.RiskMitigationStrategyCreateView.as_view(), name='mitigation-strategy-create'),
    # path('audit-trail/', views_risk_management.AuditTrailView.as_view(), name='audit-trail'),
    # path('audit-trail/<int:investment_id>/', views_risk_management.InvestmentAuditTrailView.as_view(), name='investment-audit-trail'),
]
