from django.urls import path
from . import views
from . import webhooks

app_name = 'payments'

urlpatterns = [
    # Wallet
    path('wallet/', views.wallet_dashboard, name='wallet_dashboard'),
    path('transactions/', views.transaction_history, name='transaction_history'),
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
    
    # Subscriptions
    path('subscriptions/', views.subscription_plans, name='subscription_plans'),
    path('subscriptions/<int:plan_id>/', views.subscription_detail, name='subscription_detail'),
    path('subscriptions/<int:plan_id>/purchase/', views.subscription_purchase, name='subscription_purchase'),
    path('my-subscriptions/', views.my_subscriptions, name='my_subscriptions'),
    path('subscriptions/<int:subscription_id>/cancel/', views.subscription_cancel, name='subscription_cancel'),
    path('subscriptions/<int:subscription_id>/renew/', views.subscription_renew, name='subscription_renew'),
    path('subscriptions/payment-complete/', views.subscription_payment_complete, name='subscription_payment_complete'),
    path('subscriptions/<int:subscription_id>/cancel/', views.subscription_cancel, name='cancel_subscription'),  # Alias for compatibility
    
    # Webhooks
    path('webhooks/stripe/', webhooks.stripe_webhook, name='stripe_webhook'),
    path('webhooks/paypal/', webhooks.paypal_webhook, name='paypal_webhook'),
    path('webhooks/mpesa/', webhooks.mpesa_webhook, name='mpesa_webhook'),
    
]
