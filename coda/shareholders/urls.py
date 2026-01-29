from django.urls import path
from . import views

app_name = 'shareholders'

urlpatterns = [
    # Dashboard & Ledgers
    path('dashboard/', views.shareholders_dashboard, name='shareholders_dashboard'),
    path('ledgers/', views.ledgers_view, name='ledgers_view'),
    
    # Members & Equity
    path('members/', views.members_overview, name='members_overview'),
    path('members/register/', views.member_register, name='member_register'),
    path('members/<int:member_id>/', views.member_detail, name='member_detail'),
    path('members/<int:member_id>/edit/', views.member_edit, name='member_edit'),
    
    # Contributions
    path('contributions/new/', views.contribution_log, name='contribution_log'),
]
