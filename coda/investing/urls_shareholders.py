"""
Shareholders Management System - URL Configuration for Investing App

Routes for the Shareholders Management System, migrated from shareholders app.
All URLs are prefixed with 'shareholders/' and use namespace 'shareholders'.
"""

from django.urls import path
from investing.views.shareholders import views, views_snapshots

app_name = 'shareholders'

urlpatterns = [
    # Dashboard & Ledgers
    path('dashboard/', views.shareholders_dashboard, name='shareholders_dashboard'),
    path('ledgers/', views.ledgers_view, name='ledgers_view'),
    
    # Deal Configuration (Phase 2: Full Backend)
    path('deal-config/', views.deal_config_view, name='deal_config'),
    path('deal-config/save/', views.deal_config_save, name='deal_config_save'),
    
    # Audit Log (Phase 1: Frontend-Only UI)
    path('audit-log/', views.audit_log_view, name='audit_log'),
    
    # Snapshots (Phase 2: Full Backend)
    path('snapshots/', views.snapshots_view, name='snapshots_view'),
    path('snapshots/create/', views.snapshot_create, name='snapshot_create'),
    path('snapshots/export/', views_snapshots.snapshots_export_csv, name='snapshots_export_csv'),
    path('snapshots/<int:snapshot_id>/', views_snapshots.snapshot_detail, name='snapshot_detail'),
    path('snapshots/<int:snapshot_id>/lock/', views_snapshots.snapshot_lock, name='snapshot_lock'),
    path('snapshots/<int:snapshot_id>/export/', views_snapshots.snapshot_export_detail_csv, name='snapshot_export_detail_csv'),
    
    # Phase 2: Ledger Actions
    path('ledgers/export/', views.ledgers_export_csv, name='ledgers_export_csv'),
    path('ledgers/<str:tx_id>/', views.ledger_detail, name='ledger_detail'),
    path('ledgers/<str:tx_id>/receipt/', views.ledger_receipt, name='ledger_receipt'),
    path('ledgers/<str:tx_id>/proof/', views.ledger_proof, name='ledger_proof'),  # Phase 3: Proof preview
    path('ledgers/<str:tx_id>/approve/', views.ledger_approve, name='ledger_approve'),
    path('ledgers/<str:tx_id>/dispute/', views.ledger_dispute, name='ledger_dispute'),
    
    # Members & Equity
    path('members/', views.members_overview, name='members_overview'),
    path('members/register/', views.member_register, name='member_register'),
    path('members/<int:member_id>/', views.member_detail, name='member_detail'),
    path('members/<int:member_id>/edit/', views.member_edit, name='member_edit'),
    
    # Contributions
    path('contributions/new/', views.contribution_log, name='contribution_log'),
    
    # Direct Deposit Flow (Phase 6: Full deposit → contribution pipeline)
    path('deposit/', views.shareholder_deposit, name='shareholder_deposit'),
    path('deposit/process/<str:method>/', views.shareholder_deposit_process, name='shareholder_deposit_process'),
    path('deposit/success/', views.shareholder_deposit_success, name='shareholder_deposit_success'),

    # Real Payment Gateway AJAX Endpoints
    path('deposit/paypal/capture/', views.shareholder_paypal_capture, name='shareholder_paypal_capture'),
    path('deposit/cashapp/capture/', views.shareholder_cashapp_capture, name='shareholder_cashapp_capture'),
    path('deposit/mpesa/stk-push/', views.shareholder_mpesa_stk_push, name='shareholder_mpesa_stk_push'),
    path('deposit/mpesa/check-status/', views.shareholder_mpesa_check_status, name='shareholder_mpesa_check_status'),
]
