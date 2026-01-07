"""
URL configuration for onboarding app.
"""
from django.urls import path
from . import views

app_name = 'onboarding'

urlpatterns = [
    # Registration
    path('register/', views.simplified_register, name='register'),
    path('check-email/', views.check_email, name='check_email'),

    # Email Verification
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),

    # Profile Completion
    path('complete-profile/', views.complete_profile, name='complete_profile'),

    # Social Auth Category Selection
    path('select-category/', views.select_category_social, name='select_category_social'),

    # Status
    path('status/', views.onboarding_status, name='status'),
]
