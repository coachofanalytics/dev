"""
Managed Options Trading URL configuration.

Phase 5 consolidates all managed-trading endpoints under the `/managed/` prefix.
"""

from django.urls import path

from .views.managed_trading import (
    accounts,
    positions,
    monitoring,
    sessions,
    api,
    client,
    onboarding,
    batches,
    position_suggestions,
    csv_upload,
    webhooks,
    multi_file_analyzer,
    api_bulk_actions,
    analytics,
    preset_analytics,
)

urlpatterns = [
    # Account management
    path('accounts/', accounts.managed_accounts_list, name='managed_accounts_list'),
    path('accounts/create/', accounts.create_managed_account, name='create_managed_account'),
    path('accounts/<int:account_id>/', accounts.managed_account_detail, name='managed_account_detail'),
    path('accounts/<int:account_id>/positions/create/', positions.create_position, name='create_position_for_account'),
    path('accounts/<int:account_id>/analytics/', analytics.account_analytics, name='managed_account_analytics'),
    path('accounts/<int:account_id>/broker-sync/', positions.sync_broker_positions, name='broker_sync_positions'),

    # Position management
    path('positions/', positions.positions_list, name='managed_positions_list'),
    path('positions/create/', positions.create_position, name='create_managed_position'),
    path('positions/<int:position_id>/', positions.position_detail, name='managed_position_detail'),
    path('positions/<int:position_id>/close/', positions.close_position, name='close_managed_position'),
    path('positions/<int:position_id>/edit/', positions.edit_position, name='edit_managed_position'),
    path('positions/<int:position_id>/adjust-pnl/', positions.adjust_position_pnl, name='adjust_position_pnl'),
    path('positions/<int:position_id>/mark-entered/', positions.mark_position_entered, name='mark_position_entered'),

    # Monitoring & alerts
    path('monitor/', monitoring.monitor_dashboard, name='monitor_dashboard'),
    path('accounts/<int:account_id>/alerts/', monitoring.account_alerts, name='account_alerts'),

    # Session management (consultative tier)
    path('accounts/<int:account_id>/sessions/create/', sessions.create_session, name='create_session'),
    path('accounts/<int:account_id>/sessions/', sessions.sessions_list, name='sessions_list'),

    # APIs
    path('api/accounts/<int:account_id>/summary/', api.account_summary_api, name='account_summary_api'),
    path('api/positions/<int:position_id>/evaluation/', api.position_evaluation_api, name='position_evaluation_api'),

    # Client portal (with legacy aliases)
    path('client/', client.client_portal, name='client_portal_legacy'),
    path('client/<int:account_id>/', client.client_account_detail, name='client_account_detail_legacy'),
    path('portal/', client.client_portal, name='client_portal'),
    path('portal/accounts/<int:account_id>/', client.client_account_detail, name='client_account_detail'),
    path('portal/request-review/', client.request_portfolio_review, name='request_portfolio_review'),

    # Onboarding & compliance (Phase 6)
    path('onboarding/risk-assessment/', onboarding.risk_assessment_view, name='risk_assessment'),
    path('onboarding/apply/', onboarding.managed_trading_apply_view, name='managed_trading_apply'),
    path('onboarding/application/<int:application_id>/', onboarding.application_detail_view, name='application_detail'),
    path('onboarding/application/<int:application_id>/contracts/', onboarding.contract_review_view, name='contract_review'),
    path('onboarding/contracts/<int:contract_id>/sign/', onboarding.sign_contract_view, name='sign_contract'),
    path('staff/applications/pending/', onboarding.pending_applications_view, name='pending_applications'),
    path('staff/applications/<int:application_id>/review/', onboarding.review_application_view, name='review_application'),

    # Batch approval system (Phase 7)
    path('portal/approvals/batch/<int:batch_id>/', batches.batch_approval_view, name='batch_approval'),
    path('portal/batches/', batches.client_batches_list, name='client_batches_list'),
    path('accounts/<int:account_id>/batches/create/', batches.staff_create_batch_view, name='staff_create_batch'),
    path('staff/batches/', batches.staff_batches_list, name='staff_batches_list'),
    path('api/batch/<int:batch_id>/status/', batches.ajax_check_batch_status, name='ajax_batch_status'),

    # Automated position sourcing (Phase 8)
    path('staff/suggestions/', position_suggestions.suggested_positions_list, name='suggested_positions_list'),
    path('staff/suggestions/<int:suggestion_id>/review/', position_suggestions.review_position, name='review_position'),
    path('staff/suggestions/fetch-now/', position_suggestions.fetch_positions_now, name='fetch_positions_now'),
    path('staff/suggestions/fetch-quick/', position_suggestions.fetch_positions_quick, name='fetch_positions_quick'),
    path('staff/suggestions/trigger-scheduler/', position_suggestions.trigger_managed_income_scheduler, name='trigger_managed_income_scheduler'),
    path('staff/suggestions/create-batch/', position_suggestions.create_batch_from_suggestions, name='create_batch_from_suggestions'),
    path('staff/suggestions/create-batch-from-preset/', position_suggestions.create_batch_from_preset, name='create_batch_from_preset'),
    path('staff/suggestions/update-account-limit/', position_suggestions.update_account_position_limit, name='update_account_position_limit'),
    path('staff/analytics/presets/', preset_analytics.preset_analytics_dashboard, name='preset_analytics_dashboard'),
    path('staff/analytics/positions/<int:position_id>/feedback/', preset_analytics.add_position_feedback, name='add_position_feedback'),
    path('api/suggestions/<int:suggestion_id>/approve/', position_suggestions.ajax_approve_position, name='ajax_approve_position'),
    path('api/suggestions/<int:suggestion_id>/reject/', position_suggestions.ajax_reject_position, name='ajax_reject_position'),
    path('api/suggestions/accept-top-5/', position_suggestions.accept_top_5, name='accept_top_5'),
    path('api/bulk-approve-excellent/', api_bulk_actions.bulk_approve_excellent, name='bulk_approve_excellent_api'),

    # CSV upload wizard
    path('staff/upload-csv/', csv_upload.csv_upload_wizard, name='csv_upload_wizard'),
    path('staff/upload-csv/process-mapping/', csv_upload.csv_process_mapping, name='csv_process_mapping'),
    path('staff/upload-csv/import/', csv_upload.csv_import_and_score, name='csv_import_and_score'),

    # Webhooks & integrations (Phase 9)
    path('webhooks/whatsapp/', webhooks.whatsapp_webhook, name='whatsapp_webhook'),
    path('webhooks/whatsapp/status/', webhooks.whatsapp_status_callback, name='whatsapp_status_callback'),
    path('webhooks/zapier/push/', webhooks.zapier_position_push, name='zapier_position_push'),
    path('webhooks/zapier/inbound/', webhooks.zapier_inbound_handler, name='zapier_inbound_handler'),

    # Multi-file flow analyzer (Phase 9)
    path('staff/flow-analyzer/', multi_file_analyzer.multi_file_flow_analyzer, name='multi_file_analyzer'),
    path('staff/flow-analyzer/results/', multi_file_analyzer.multi_file_analyzer_results, name='multi_file_analyzer_results'),
]
