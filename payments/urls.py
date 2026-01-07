from django.urls import path
from . import views
from . import webhooks

app_name = 'payments'

urlpatterns = [
    # Wallet
    path('wallet/', views.wallet_dashboard, name='wallet_dashboard'),
    path('transactions/', views.transaction_history, name='transaction_history'),
    path('transactions/export/', views.export_transactions, name='export_transactions'),
    path('transactions/<str:transaction_id>/receipt/', views.download_transaction_receipt, name='download_receipt'),
    path('invoices/<int:invoice_id>/pdf/', views.download_invoice_pdf, name='download_invoice'),
    path('wallet/toggle-currency/', views.toggle_currency_view, name='toggle_currency_view'),

    # Deposits
    path('deposit/', views.deposit_initiate, name='deposit_initiate'),
    path('deposit/stripe/', views.deposit_stripe, name='deposit_stripe'),
    path('deposit/paypal/', views.deposit_paypal, name='deposit_paypal'),
    path('deposit/paypal/execute/', views.deposit_paypal_execute, name='deposit_paypal_execute'),
    path('deposit/paypal/cancel/', views.deposit_paypal_cancel, name='deposit_paypal_cancel'),
    path('deposit/mpesa/', views.deposit_mpesa, name='deposit_mpesa'),
    path('deposit/mpesa/status/<str:transaction_id>/', views.deposit_mpesa_status, name='deposit_mpesa_status'),
    path('api/mpesa/status/<str:transaction_id>/', views.check_mpesa_status, name='check_mpesa_status'),
    path('deposit/cashapp/', views.deposit_cashapp, name='deposit_cashapp'),
    path('deposit/venmo/', views.deposit_venmo, name='deposit_venmo'),

    # Subscriptions
    path('subscriptions/', views.subscription_plans, name='subscription_plans'),
    path('subscriptions/<int:plan_id>/', views.subscription_detail, name='subscription_detail'),
    path('subscriptions/<int:plan_id>/purchase/', views.subscription_purchase, name='subscription_purchase'),
    path('my-subscriptions/', views.my_subscriptions, name='my_subscriptions'),
    path('subscriptions/<int:subscription_id>/cancel/', views.subscription_cancel, name='subscription_cancel'),
    path('subscriptions/<int:subscription_id>/renew/', views.subscription_renew, name='subscription_renew'),
    path('subscriptions/payment-complete/', views.subscription_payment_complete, name='subscription_payment_complete'),
    path('subscriptions/<int:subscription_id>/cancel/', views.subscription_cancel, name='cancel_subscription'),  # Alias for compatibility

    # User Analytics & Security
    path('insights/', views.financial_insights, name='financial_insights'),
    path('activity/', views.activity_log, name='activity_log'),
    path('limits/', views.spending_limits, name='spending_limits'),
    path('disputes/', views.user_disputes, name='user_disputes'),
    path('disputes/create/<str:transaction_id>/', views.create_dispute, name='create_dispute'),

    # Staff/Admin Analytics
    path('staff/dashboard/', views.staff_analytics_dashboard, name='staff_analytics_dashboard'),
    path('staff/transactions/', views.staff_transactions, name='staff_transactions'),
    path('staff/fraud-alerts/', views.staff_fraud_alerts, name='staff_fraud_alerts'),
    path('staff/fraud-alerts/<int:alert_id>/resolve/', views.staff_resolve_fraud_alert, name='staff_resolve_fraud_alert'),
    path('staff/disputes/', views.staff_disputes, name='staff_disputes'),
    path('staff/disputes/<int:dispute_id>/resolve/', views.staff_resolve_dispute, name='staff_resolve_dispute'),

    # Webhooks
    path('webhooks/stripe/', webhooks.stripe_webhook, name='stripe_webhook'),
    path('webhooks/paypal/', webhooks.paypal_webhook, name='paypal_webhook'),
    path('webhooks/mpesa/', webhooks.mpesa_webhook, name='mpesa_webhook'),
    path('webhooks/cashapp/', webhooks.cashapp_webhook, name='cashapp_webhook'),
    path('webhooks/venmo/', webhooks.venmo_webhook, name='venmo_webhook'),

]
