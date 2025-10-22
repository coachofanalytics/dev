"""
Portfolio URL Configuration
"""

from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    # ========== PORTFOLIO HUB (Branded) ==========
    path('', views.portfolio_hub, name='hub'),
    
    # ========== INTERVIEW HUB (White-label) ==========
    path('interview/', views.interview_hub, name='interview-hub'),
    
    # ========== PROJECT PRESENTATIONS ==========
    # Project landing page
    path('<slug:project_slug>/', views.project_landing, name='project-landing'),
    
    # Specific audience presentations
    path('<slug:project_slug>/<str:audience_type>/', views.project_presentation, name='project-presentation'),
    
    # Interview mode presentations (white-label)
    path('interview/<slug:project_slug>/', views.project_landing, name='interview-project-landing'),
    path('interview/<slug:project_slug>/<str:audience_type>/', views.project_presentation, name='interview-project-presentation'),
    
    # ========== GUIDE & RESOURCES ==========
    path('guide/', views.presentation_guide, name='guide'),
    
    # ========== LEGACY PRESENTATIONS (Exact copies from original apps) ==========
    # AI Diaspora legacy presentation
    path('legacy/ai-diaspora/', views.legacy_ai_diaspora_presentation, {'presentation_mode': 'investor'}, name='legacy-ai-diaspora'),
    path('legacy/ai-diaspora/<str:presentation_mode>/', views.legacy_ai_diaspora_presentation, name='legacy-ai-diaspora-mode'),
    
    # Finance legacy presentation
    path('legacy/finance/', views.legacy_finance_presentation, name='legacy-finance'),
]

