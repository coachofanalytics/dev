"""
Financial Analytics Service

Handles all financial analytics and reporting business logic including:
- Loan performance analytics
- Payment analytics
- Budget analytics
- Financial reporting
- KCC optimization analytics

This service encapsulates the business logic previously scattered across finance/views.py
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction, models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import LoanApplication, Payment_Information, Budget, Transaction, Inflow
from .base_service import BaseFinanceService

logger = logging.getLogger(__name__)
User = get_user_model()


class FinancialAnalyticsService(BaseFinanceService):
    """
    Service for managing financial analytics and reporting.
    
    Handles loan performance, payment analytics, budget analytics, and financial reporting.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logger
    
    def get_loan_performance_analytics(
        self, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        company: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get loan performance analytics.
        
        Args:
            date_from: Optional start date filter
            date_to: Optional end date filter
            company: Optional company filter
            
        Returns:
            Dict with success status and loan analytics
        """
        try:
            queryset = LoanApplication.objects.all()
            
            if date_from:
                queryset = queryset.filter(submitted_at__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(submitted_at__lte=date_to)
            
            # Calculate loan statistics
            total_applications = queryset.count()
            total_amount_requested = sum(float(app.amount_requested) for app in queryset)
            
            # Status breakdown
            status_breakdown = {}
            for app in queryset:
                status = app.status
                if status not in status_breakdown:
                    status_breakdown[status] = {'count': 0, 'amount': 0}
                status_breakdown[status]['count'] += 1
                status_breakdown[status]['amount'] += float(app.amount_requested)
            
            # Approval rate calculation
            processed_applications = status_breakdown.get('approved', {'count': 0})['count'] + \
                                  status_breakdown.get('rejected', {'count': 0})['count']
            approval_rate = (status_breakdown.get('approved', {'count': 0})['count'] / processed_applications * 100) \
                          if processed_applications > 0 else 0
            
            # Average loan amount
            avg_loan_amount = total_amount_requested / total_applications if total_applications > 0 else 0
            
            # Monthly trends (if date range provided)
            monthly_trends = {}
            if date_from and date_to:
                current_date = date_from.replace(day=1)
                while current_date <= date_to:
                    month_key = current_date.strftime('%Y-%m')
                    month_apps = queryset.filter(
                        submitted_at__year=current_date.year,
                        submitted_at__month=current_date.month
                    )
                    monthly_trends[month_key] = {
                        'applications': month_apps.count(),
                        'amount': sum(float(app.amount_requested) for app in month_apps)
                    }
                    # Move to next month
                    if current_date.month == 12:
                        current_date = current_date.replace(year=current_date.year + 1, month=1)
                    else:
                        current_date = current_date.replace(month=current_date.month + 1)
            
            analytics = {
                'total_applications': total_applications,
                'total_amount_requested': total_amount_requested,
                'avg_loan_amount': round(avg_loan_amount, 2),
                'approval_rate': round(approval_rate, 2),
                'status_breakdown': status_breakdown,
                'monthly_trends': monthly_trends
            }
            
            return self.create_success_response(
                {'analytics': analytics},
                "Loan performance analytics retrieved successfully"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_loan_performance_analytics')
    
    def get_payment_analytics(
        self, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        payment_method: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get payment analytics.
        
        Args:
            date_from: Optional start date filter
            date_to: Optional end date filter
            payment_method: Optional payment method filter
            
        Returns:
            Dict with success status and payment analytics
        """
        try:
            queryset = Payment_Information.objects.all()
            
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)
            
            if payment_method:
                queryset = queryset.filter(payment_method=payment_method)
            
            # Calculate payment statistics
            total_payments = queryset.count()
            total_amount = sum(float(p.amount) for p in queryset)
            
            # Status breakdown
            status_breakdown = {}
            for payment in queryset:
                status = payment.status
                if status not in status_breakdown:
                    status_breakdown[status] = {'count': 0, 'amount': 0}
                status_breakdown[status]['count'] += 1
                status_breakdown[status]['amount'] += float(payment.amount)
            
            # Payment method breakdown
            method_breakdown = {}
            for payment in queryset:
                method = payment.payment_method
                if method not in method_breakdown:
                    method_breakdown[method] = {'count': 0, 'amount': 0}
                method_breakdown[method]['count'] += 1
                method_breakdown[method]['amount'] += float(payment.amount)
            
            # Average payment amount
            avg_payment_amount = total_amount / total_payments if total_payments > 0 else 0
            
            # Success rate
            successful_payments = status_breakdown.get('approved', {'count': 0})['count']
            success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
            
            analytics = {
                'total_payments': total_payments,
                'total_amount': total_amount,
                'avg_payment_amount': round(avg_payment_amount, 2),
                'success_rate': round(success_rate, 2),
                'status_breakdown': status_breakdown,
                'method_breakdown': method_breakdown
            }
            
            return self.create_success_response(
                {'analytics': analytics},
                "Payment analytics retrieved successfully"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_payment_analytics')
    
    def get_budget_analytics(
        self, 
        company: Optional[str] = None,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get budget analytics.
        
        Args:
            company: Optional company filter
            department: Optional department filter
            
        Returns:
            Dict with success status and budget analytics
        """
        try:
            queryset = Budget.objects.filter(is_active=True)
            
            if company:
                queryset = queryset.filter(company=company)
            
            if department:
                queryset = queryset.filter(department=department)
            
            # Calculate budget statistics
            total_items = queryset.count()
            total_budget = sum(float(item.qty * item.unit_price) for item in queryset)
            
            # Category breakdown
            category_breakdown = {}
            for item in queryset:
                category = item.category
                if category not in category_breakdown:
                    category_breakdown[category] = {'count': 0, 'amount': 0}
                category_breakdown[category]['count'] += 1
                category_breakdown[category]['amount'] += float(item.qty * item.unit_price)
            
            # Department breakdown
            department_breakdown = {}
            for item in queryset:
                dept = item.department
                if dept not in department_breakdown:
                    department_breakdown[dept] = {'count': 0, 'amount': 0}
                department_breakdown[dept]['count'] += 1
                department_breakdown[dept]['amount'] += float(item.qty * item.unit_price)
            
            # Average item cost
            avg_item_cost = total_budget / total_items if total_items > 0 else 0
            
            analytics = {
                'total_items': total_items,
                'total_budget': total_budget,
                'avg_item_cost': round(avg_item_cost, 2),
                'category_breakdown': category_breakdown,
                'department_breakdown': department_breakdown
            }
            
            return self.create_success_response(
                {'analytics': analytics},
                "Budget analytics retrieved successfully"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_budget_analytics')
    
    def get_cashflow_analytics(
        self, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get cashflow analytics combining inflows and outflows.
        
        Args:
            date_from: Optional start date filter
            date_to: Optional end date filter
            
        Returns:
            Dict with success status and cashflow analytics
        """
        try:
            # Get inflows
            inflow_queryset = Inflow.objects.all()
            if date_from:
                inflow_queryset = inflow_queryset.filter(created_at__gte=date_from)
            if date_to:
                inflow_queryset = inflow_queryset.filter(created_at__lte=date_to)
            
            # Get outflows (transactions)
            outflow_queryset = Transaction.objects.all()
            if date_from:
                outflow_queryset = outflow_queryset.filter(created_at__gte=date_from)
            if date_to:
                outflow_queryset = outflow_queryset.filter(created_at__lte=date_to)
            
            # Calculate totals
            total_inflows = sum(float(inflow.amount) for inflow in inflow_queryset)
            total_outflows = sum(float(transaction.amount) for transaction in outflow_queryset)
            net_cashflow = total_inflows - total_outflows
            
            # Inflow breakdown by category
            inflow_categories = {}
            for inflow in inflow_queryset:
                category = inflow.category
                if category not in inflow_categories:
                    inflow_categories[category] = 0
                inflow_categories[category] += float(inflow.amount)
            
            # Outflow breakdown by category
            outflow_categories = {}
            for transaction in outflow_queryset:
                category = transaction.category
                if category not in outflow_categories:
                    outflow_categories[category] = 0
                outflow_categories[category] += float(transaction.amount)
            
            # Cashflow ratio
            cashflow_ratio = (total_inflows / total_outflows) if total_outflows > 0 else 0
            
            analytics = {
                'total_inflows': total_inflows,
                'total_outflows': total_outflows,
                'net_cashflow': net_cashflow,
                'cashflow_ratio': round(cashflow_ratio, 2),
                'inflow_categories': inflow_categories,
                'outflow_categories': outflow_categories
            }
            
            return self.create_success_response(
                {'analytics': analytics},
                "Cashflow analytics retrieved successfully"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_cashflow_analytics')
    
    def get_kcc_optimization_analytics(
        self, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get KCC (Key Credit Criteria) optimization analytics.
        
        Args:
            date_from: Optional start date filter
            date_to: Optional end date filter
            
        Returns:
            Dict with success status and KCC analytics
        """
        try:
            queryset = LoanApplication.objects.all()
            
            if date_from:
                queryset = queryset.filter(submitted_at__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(submitted_at__lte=date_to)
            
            # Analyze credit criteria
            total_applications = queryset.count()
            
            # Employment status analysis
            employment_breakdown = {}
            for app in queryset:
                status = app.employment_status
                if status not in employment_breakdown:
                    employment_breakdown[status] = {'count': 0, 'approved': 0}
                employment_breakdown[status]['count'] += 1
                if app.status == 'approved':
                    employment_breakdown[status]['approved'] += 1
            
            # Calculate approval rates by employment status
            for status, data in employment_breakdown.items():
                data['approval_rate'] = (data['approved'] / data['count'] * 100) if data['count'] > 0 else 0
            
            # Income analysis
            income_ranges = {
                '0-1000': {'count': 0, 'approved': 0},
                '1000-5000': {'count': 0, 'approved': 0},
                '5000-10000': {'count': 0, 'approved': 0},
                '10000+': {'count': 0, 'approved': 0}
            }
            
            for app in queryset:
                income = float(app.monthly_income) if app.monthly_income else 0
                if income < 1000:
                    range_key = '0-1000'
                elif income < 5000:
                    range_key = '1000-5000'
                elif income < 10000:
                    range_key = '5000-10000'
                else:
                    range_key = '10000+'
                
                income_ranges[range_key]['count'] += 1
                if app.status == 'approved':
                    income_ranges[range_key]['approved'] += 1
            
            # Calculate approval rates by income range
            for range_key, data in income_ranges.items():
                data['approval_rate'] = (data['approved'] / data['count'] * 100) if data['count'] > 0 else 0
            
            # Loan amount analysis
            amount_ranges = {
                '0-5000': {'count': 0, 'approved': 0},
                '5000-20000': {'count': 0, 'approved': 0},
                '20000-50000': {'count': 0, 'approved': 0},
                '50000+': {'count': 0, 'approved': 0}
            }
            
            for app in queryset:
                amount = float(app.amount_requested)
                if amount < 5000:
                    range_key = '0-5000'
                elif amount < 20000:
                    range_key = '5000-20000'
                elif amount < 50000:
                    range_key = '20000-50000'
                else:
                    range_key = '50000+'
                
                amount_ranges[range_key]['count'] += 1
                if app.status == 'approved':
                    amount_ranges[range_key]['approved'] += 1
            
            # Calculate approval rates by loan amount range
            for range_key, data in amount_ranges.items():
                data['approval_rate'] = (data['approved'] / data['count'] * 100) if data['count'] > 0 else 0
            
            analytics = {
                'total_applications': total_applications,
                'employment_breakdown': employment_breakdown,
                'income_ranges': income_ranges,
                'amount_ranges': amount_ranges
            }
            
            return self.create_success_response(
                {'analytics': analytics},
                "KCC optimization analytics retrieved successfully"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_kcc_optimization_analytics')
    
    def generate_financial_report(
        self, 
        report_type: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        company: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive financial report.
        
        Args:
            report_type: Type of report ('summary', 'detailed', 'executive')
            date_from: Optional start date filter
            date_to: Optional end date filter
            company: Optional company filter
            
        Returns:
            Dict with success status and report data
        """
        try:
            # Get all analytics
            loan_analytics = self.get_loan_performance_analytics(date_from, date_to, company)
            payment_analytics = self.get_payment_analytics(date_from, date_to)
            budget_analytics = self.get_budget_analytics(company)
            cashflow_analytics = self.get_cashflow_analytics(date_from, date_to)
            
            # Compile comprehensive report
            report = {
                'report_type': report_type,
                'date_range': {
                    'from': date_from.isoformat() if date_from else None,
                    'to': date_to.isoformat() if date_to else None
                },
                'company': company,
                'generated_at': timezone.now().isoformat(),
                'loan_performance': loan_analytics.get('data', {}).get('analytics', {}),
                'payment_analytics': payment_analytics.get('data', {}).get('analytics', {}),
                'budget_analytics': budget_analytics.get('data', {}).get('analytics', {}),
                'cashflow_analytics': cashflow_analytics.get('data', {}).get('analytics', {})
            }
            
            # Add executive summary for executive reports
            if report_type == 'executive':
                report['executive_summary'] = {
                    'total_loan_applications': loan_analytics.get('data', {}).get('analytics', {}).get('total_applications', 0),
                    'total_loan_amount': loan_analytics.get('data', {}).get('analytics', {}).get('total_amount_requested', 0),
                    'approval_rate': loan_analytics.get('data', {}).get('analytics', {}).get('approval_rate', 0),
                    'total_payments': payment_analytics.get('data', {}).get('analytics', {}).get('total_payments', 0),
                    'net_cashflow': cashflow_analytics.get('data', {}).get('analytics', {}).get('net_cashflow', 0)
                }
            
            return self.create_success_response(
                {'report': report},
                f"{report_type.title()} financial report generated successfully"
            )
            
        except Exception as e:
            self._handle_error(e, 'generate_financial_report')

