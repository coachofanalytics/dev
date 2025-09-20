"""
URL Configuration for Unified Payment Views
"""

from django.urls import path
from . import payment_views

app_name = 'payments'

urlpatterns = [
    # Payment Method Selection
    path('methods/', payment_views.payment_method_selection, name='method_selection'),
    
    # Payment Processing
    path('process/<str:method>/', payment_views.payment_processing, name='processing'),
    
    # Payment Results
    path('success/', payment_views.payment_success, name='success'),
    path('failed/', payment_views.payment_failed, name='failed'),
    
    # Legacy Payment Views (for backward compatibility)
    path('mpesa/', payment_views.process_mpesa_payment, name='mpesa'),
    path('paypal/', payment_views.process_paypal_payment, name='paypal'),
    path('cashapp/', payment_views.process_cashapp_payment, name='cashapp'),
    path('zelle/', payment_views.process_zelle_payment, name='zelle'),
    path('venmo/', payment_views.process_venmo_payment, name='venmo'),
]
