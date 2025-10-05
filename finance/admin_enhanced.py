"""
Enhanced Admin Interface for Finance App
Payment analytics, management tools, and improved user experience
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.http import JsonResponse
from django.template.response import TemplateResponse
from datetime import datetime, timedelta
import json

# Import models
from .models import (
    Payment_Information, Payment_History, LoanApplication,
    LoanProduct, Inflow, Transaction, Budget, Supplier
)

class PaymentInformationAdminEnhanced:
    """Enhanced admin functionality for payment information"""
    
    @staticmethod
    def get_payment_analytics():
        """Get payment analytics data"""
        try:
            total_payments = Payment_Information.objects.count()
            active_payments = Payment_Information.objects.filter(is_active=True).count()
            total_amount = Payment_Information.objects.aggregate(Sum('payment_fees'))['payment_fees__sum'] or 0
            total_collected = Payment_Information.objects.aggregate(Sum('down_payment'))['down_payment__sum'] or 0
            outstanding_balance = total_amount - total_collected
            
            return {
                'total_payments': total_payments,
                'active_payments': active_payments,
                'total_amount': total_amount,
                'total_collected': total_collected,
                'outstanding_balance': outstanding_balance,
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_payment_method_distribution():
        """Get payment method distribution"""
        try:
            return Payment_Information.objects.values('payment_method').annotate(
                count=Count('id'),
                total_amount=Sum('payment_fees')
            ).order_by('-count')
        except Exception as e:
            return []
    
    @staticmethod
    def get_monthly_trends(months=6):
        """Get monthly payment trends"""
        try:
            trends = []
            for i in range(months):
                date = timezone.now() - timedelta(days=30*i)
                month_start = date.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                month_payments = Payment_Information.objects.filter(
                    contract_submitted_date__range=[month_start, month_end]
                ).count()
                
                trends.append({
                    'month': month_start.strftime('%B %Y'),
                    'count': month_payments
                })
            
            return trends
        except Exception as e:
            return []

class PaymentHistoryAdminEnhanced:
    """Enhanced admin functionality for payment history"""
    
    @staticmethod
    def get_payment_status_summary():
        """Get payment status summary"""
        try:
            total_history = Payment_History.objects.count()
            recent_payments = Payment_History.objects.filter(
                contract_submitted_date__gte=timezone.now() - timedelta(days=30)
            ).count()
            
            return {
                'total_history': total_history,
                'recent_payments': recent_payments,
            }
        except Exception as e:
            return {'error': str(e)}

# Utility functions for admin enhancement
def get_payment_dashboard_data():
    """Get comprehensive payment dashboard data"""
    return {
        'payment_info': PaymentInformationAdminEnhanced.get_payment_analytics(),
        'payment_methods': PaymentInformationAdminEnhanced.get_payment_method_distribution(),
        'monthly_trends': PaymentInformationAdminEnhanced.get_monthly_trends(),
        'payment_history': PaymentHistoryAdminEnhanced.get_payment_status_summary(),
    }

def format_payment_amount(amount):
    """Format payment amount with color coding"""
    if amount > 0:
        color = 'red'
        icon = '⚠️'
    else:
        color = 'green'
        icon = '✅'
    
    return format_html(
        '<span style="color: {};">{} ${}</span>',
        color, icon, abs(amount)
    )

def get_payment_status_display(payment):
    """Get payment status display with color coding"""
    try:
        if hasattr(payment, 'fee_balance'):
            balance = payment.fee_balance
            if balance > 0:
                return format_html(
                    '<span style="color: orange; font-weight: bold;">Outstanding</span>'
                )
            else:
                return format_html(
                    '<span style="color: green; font-weight: bold;">Paid</span>'
                )
        else:
            return 'Unknown'
    except:
        return 'Unknown'
