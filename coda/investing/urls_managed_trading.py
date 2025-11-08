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
    onboarding,  # Phase 6
    batches,  # Phase 7
    position_suggestions,  # Phase 8: Automated position sourcing
    csv_upload,  # CSV Upload Wizard (Enhanced with Cross-Validation)
    webhooks,  # Phase 9: Real-time WhatsApp approval
    multi_file_analyzer,  # Phase 9: Multi-file flow analyzer (manual Unusual Whales)
    api_bulk_actions,  # Phase 9: Bulk approval and distribution
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
    
    path('managed/positions/<int:position_id>/edit/', 
         positions.edit_position, 
         name='edit_managed_position'),
    
    path('managed/positions/<int:position_id>/adjust-pnl/', 
         positions.adjust_position_pnl, 
         name='adjust_position_pnl'),
    
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
    # Legacy aliases (client/)
    path('managed/client/', 
         client.client_portal,
         name='client_portal_legacy'),
    path('managed/client/<int:account_id>/', 
         client.client_account_detail,
         name='client_account_detail_legacy'),
    
    path('managed/portal/', 
         client.client_portal, 
         name='client_portal'),
    
    path('managed/portal/accounts/<int:account_id>/', 
         client.client_account_detail, 
         name='client_account_detail'),
    
    # ========================================================================
    # PHASE 6: CLIENT ONBOARDING & COMPLIANCE
    # ========================================================================
    
    # Risk Assessment (Step 1)
    path('managed/onboarding/risk-assessment/', 
         onboarding.risk_assessment_view, 
         name='risk_assessment'),
    
    # Application (Step 2)
    path('managed/onboarding/apply/', 
         onboarding.managed_trading_apply_view, 
         name='managed_trading_apply'),
    
    path('managed/onboarding/application/<int:application_id>/', 
         onboarding.application_detail_view, 
         name='application_detail'),
    
    # Contract Review & Signing (Step 3)
    path('managed/onboarding/application/<int:application_id>/contracts/', 
         onboarding.contract_review_view, 
         name='contract_review'),
    
    path('managed/onboarding/contracts/<int:contract_id>/sign/', 
         onboarding.sign_contract_view, 
         name='sign_contract'),
    
    # ========================================================================
    # STAFF: APPLICATION REVIEW
    # ========================================================================
    
    path('managed/staff/applications/pending/', 
         onboarding.pending_applications_view, 
         name='pending_applications'),
    
    path('managed/staff/applications/<int:application_id>/review/', 
         onboarding.review_application_view, 
         name='review_application'),
    
    # ========================================================================
    # PHASE 7: BATCH APPROVAL SYSTEM
    # ========================================================================
    
    # Client: Batch Approval
    path('managed/portal/approvals/batch/<int:batch_id>/', 
         batches.batch_approval_view, 
         name='batch_approval'),
    
    path('managed/portal/batches/', 
         batches.client_batches_list, 
         name='client_batches_list'),
    
    # ========================================================================
    # PHASE 8: AUTOMATED POSITION SOURCING (Staff Only)
    # ========================================================================
    
    # Staff: Review suggested positions
    path('managed/staff/suggestions/', 
         position_suggestions.suggested_positions_list, 
         name='suggested_positions_list'),
    
    path('managed/staff/suggestions/<int:suggestion_id>/review/', 
         position_suggestions.review_position, 
         name='review_position'),
    
    # Staff: Fetch positions manually
    path('managed/staff/suggestions/fetch-now/', 
         position_suggestions.fetch_positions_now, 
         name='fetch_positions_now'),

    # Staff: Quick fetch via GET (fallback)
    path('managed/staff/suggestions/fetch-quick/', 
         position_suggestions.fetch_positions_quick, 
         name='fetch_positions_quick'),

    # Staff: Trigger managed income scheduler (superusers)
    path('managed/staff/suggestions/trigger-scheduler/',
         position_suggestions.trigger_managed_income_scheduler,
         name='trigger_managed_income_scheduler'),
    
    # Staff: Create batch from approved suggestions
    path('managed/staff/suggestions/create-batch/', 
         position_suggestions.create_batch_from_suggestions, 
         name='create_batch_from_suggestions'),
    path('managed/staff/suggestions/update-account-limit/',
         position_suggestions.update_account_position_limit,
         name='update_account_position_limit'),
    
    # AJAX endpoints for quick actions
    path('managed/api/suggestions/<int:suggestion_id>/approve/', 
         position_suggestions.ajax_approve_position, 
         name='ajax_approve_position'),
    
    path('managed/api/suggestions/<int:suggestion_id>/reject/', 
         position_suggestions.ajax_reject_position, 
         name='ajax_reject_position'),
    
    # Phase 10A: Accept Top 5 Recommended
    path('managed/api/suggestions/accept-top-5/', 
         position_suggestions.accept_top_5, 
         name='accept_top_5'),
    
    # Bulk actions API
    path('managed/api/bulk-approve-excellent/', 
         api_bulk_actions.bulk_approve_excellent, 
         name='bulk_approve_excellent_api'),
    
    # Staff: Batch Management
    path('managed/accounts/<int:account_id>/batches/create/', 
         batches.staff_create_batch_view, 
         name='staff_create_batch'),
    
    path('managed/staff/batches/', 
         batches.staff_batches_list, 
         name='staff_batches_list'),
    
    # AJAX: Batch Status Check
    path('managed/api/batch/<int:batch_id>/status/', 
         batches.ajax_check_batch_status, 
         name='ajax_batch_status'),
    
    # ========================================================================
    # CSV UPLOAD WIZARD (Staff Only)
    # ========================================================================
    
    path('managed/staff/upload-csv/', 
         csv_upload.csv_upload_wizard, 
         name='csv_upload_wizard'),
    
    path('managed/staff/upload-csv/process-mapping/', 
         csv_upload.csv_process_mapping, 
         name='csv_process_mapping'),
    
    path('managed/staff/upload-csv/import/', 
         csv_upload.csv_import_and_score, 
         name='csv_import_and_score'),
    
    # ========================================================================
    # WEBHOOKS: Real-Time Approval (Phase 9)
    # ========================================================================
    
    path('webhooks/whatsapp/', 
         webhooks.whatsapp_webhook, 
         name='whatsapp_webhook'),
    
    path('webhooks/whatsapp/status/', 
         webhooks.whatsapp_status_callback, 
         name='whatsapp_status_callback'),
    
    # Zapier integrations (Phase 1 - Quick Wins)
    path('managed/webhooks/zapier/push/', 
         webhooks.zapier_position_push, 
         name='zapier_position_push'),
    
    path('webhooks/zapier/inbound/', 
         webhooks.zapier_inbound_handler, 
         name='zapier_inbound_handler'),
    
    # ========================================================================
    # MULTI-FILE FLOW ANALYZER: Manual Unusual Whales Workflow (Phase 9)
    # ========================================================================
    
    path('managed/staff/flow-analyzer/', 
         multi_file_analyzer.multi_file_flow_analyzer, 
         name='multi_file_analyzer'),
    
    path('managed/staff/flow-analyzer/results/', 
         multi_file_analyzer.multi_file_analyzer_results, 
         name='multi_file_analyzer_results'),
]

