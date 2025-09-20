"""
Loan URLs

URL patterns for loan-related operations.
Extracted from the main finance URLs for better organization.
"""

from django.urls import path
from . import loan_views

app_name = 'finance'

loan_urlpatterns = [
    # Loan Application URLs
    path('loan-home/', loan_views.loan_application_home, name='loan-home'),
    path('apply-for-loan/', loan_views.apply_for_loan, name='apply-for-loan'),
    path('apply-for-loan/<int:plan_id>/', loan_views.apply_for_loan, name='apply-for-loan-with-plan'),
    path('loan-confirmation/', loan_views.loan_application_confirmation, name='loan-confirmation'),
    path('loan-application-confirmation/', loan_views.loan_application_confirmation, name='loan-application-confirmation'),
    
    # Admin Loan Management URLs
    path('admin/loan-applications/', loan_views.admin_loan_applications, name='admin-loan-applications'),
    path('admin/loan-applications/<int:pk>/approve/', loan_views.approve_loan_application, name='approve-loan-application'),
    path('admin/loan-applications/<int:pk>/reject/', loan_views.reject_loan_application, name='reject-loan-application'),
    path('admin/loan-analytics/', loan_views.loan_analytics, name='loan-analytics'),
]

