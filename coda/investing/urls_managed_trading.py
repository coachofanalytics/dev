"""
URLs for Managed Options Trading

URL patterns for CODA managed options trading feature.
Includes account management, position tracking, monitoring, and client portal.
"""

from django.urls import path
from .views.managed_trading import (
    accounts,
    positions,
    monitoring,
    sessions,
    api,
    client,
)

urlpatterns = [
    # ========================================================================
    # ACCOUNT MANAGEMENT (Staff Only)
    # ========================================================================
    path('managed/accounts/', 
         accounts.managed_accounts_list, 
         name='managed_accounts_list'),
    
    path('managed/accounts/create/', 
         accounts.create_managed_account, 
         name='create_managed_account'),
    
    path('managed/accounts/<int:account_id>/', 
         accounts.managed_account_detail, 
         name='managed_account_detail'),
    
    # ========================================================================
    # POSITION MANAGEMENT (Staff Only)
    # ========================================================================
    path('managed/positions/', 
         positions.positions_list, 
         name='managed_positions_list'),
    
    path('managed/positions/create/', 
         positions.create_position, 
         name='create_managed_position'),
    
    path('managed/accounts/<int:account_id>/positions/create/', 
         positions.create_position, 
         name='create_position_for_account'),
    
    path('managed/positions/<int:position_id>/', 
         positions.position_detail, 
         name='managed_position_detail'),
    
    path('managed/positions/<int:position_id>/close/', 
         positions.close_position, 
         name='close_managed_position'),
    
    # ========================================================================
    # MONITORING & ALERTS (Staff Only)
    # ========================================================================
    path('managed/monitor/', 
         monitoring.monitor_dashboard, 
         name='monitor_dashboard'),
    
    path('managed/accounts/<int:account_id>/alerts/', 
         monitoring.account_alerts, 
         name='account_alerts'),
    
    # ========================================================================
    # SESSION MANAGEMENT (Staff Only - Consultative Tier)
    # ========================================================================
    path('managed/accounts/<int:account_id>/sessions/create/', 
         sessions.create_session, 
         name='create_session'),
    
    path('managed/accounts/<int:account_id>/sessions/', 
         sessions.sessions_list, 
         name='sessions_list'),
    
    # ========================================================================
    # API ENDPOINTS (Staff Only)
    # ========================================================================
    path('managed/api/accounts/<int:account_id>/summary/', 
         api.account_summary_api, 
         name='account_summary_api'),
    
    path('managed/api/positions/<int:position_id>/evaluation/', 
         api.position_evaluation_api, 
         name='position_evaluation_api'),
    
    # ========================================================================
    # CLIENT PORTAL (Client Access)
    # ========================================================================
    path('managed/portal/', 
         client.client_portal, 
         name='client_portal'),
    
    path('managed/portal/accounts/<int:account_id>/', 
         client.client_account_detail, 
         name='client_account_detail'),
]

