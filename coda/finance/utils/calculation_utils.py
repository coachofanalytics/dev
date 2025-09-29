"""
Calculation Utilities for CODA Finance System

Centralized calculation utilities for financial operations including:
- Amount calculations
- Time-based calculations (YTD, monthly averages)
- Budget estimation methods
- Financial analytics
"""

from decimal import Decimal
from django.db.models import Sum, Q
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class CalculationUtils:
    """Centralized calculation utilities for financial operations"""
    
    @staticmethod
    def calculate_amount(unit_price: Decimal, qty: Decimal) -> Decimal:
        """
        Calculate total amount from unit price and quantity
        
        Args:
            unit_price: Unit price as Decimal
            qty: Quantity as Decimal
            
        Returns:
            Total amount as Decimal
        """
        if unit_price and qty:
            return round(Decimal(unit_price) * Decimal(qty), 2)
        return Decimal('0.00')
    
    @staticmethod
    def calculate_ytd_total(queryset, amount_field: str, qty_field: str = None) -> Decimal:
        """
        Calculate year-to-date total for a queryset
        
        Args:
            queryset: Django queryset
            amount_field: Name of amount field
            qty_field: Name of quantity field (optional)
            
        Returns:
            YTD total as Decimal
        """
        current_year = datetime.now().year
        ytd_queryset = queryset.filter(transaction_date__year=current_year)
        
        if qty_field:
            return sum(
                Decimal(getattr(item, amount_field)) * Decimal(getattr(item, qty_field))
                for item in ytd_queryset
                if hasattr(item, amount_field) and hasattr(item, qty_field)
            )
        else:
            return sum(
                Decimal(getattr(item, amount_field))
                for item in ytd_queryset
                if hasattr(item, amount_field)
            )
    
    @staticmethod
    def calculate_monthly_average(queryset, amount_field: str, qty_field: str = None, months: int = 3) -> Decimal:
        """
        Calculate average spending over last N months
        
        Args:
            queryset: Django queryset
            amount_field: Name of amount field
            qty_field: Name of quantity field (optional)
            months: Number of months to average
            
        Returns:
            Monthly average as Decimal
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=months * 30)
        
        monthly_queryset = queryset.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
        )
        
        if qty_field:
            total = sum(
                Decimal(getattr(item, amount_field)) * Decimal(getattr(item, qty_field))
                for item in monthly_queryset
                if hasattr(item, amount_field) and hasattr(item, qty_field)
            )
        else:
            total = sum(
                Decimal(getattr(item, amount_field))
                for item in monthly_queryset
                if hasattr(item, amount_field)
            )
        
        return total / months if months > 0 else Decimal('0.00')
    
    @staticmethod
    def calculate_budget_estimate(queryset, amount_field: str, qty_field: str = None, 
                                method: str = 'monthly_average', months: int = 3) -> Decimal:
        """
        Calculate budget estimate using various methods
        
        Args:
            queryset: Django queryset
            amount_field: Name of amount field
            qty_field: Name of quantity field (optional)
            method: Estimation method ('monthly_average', 'ytd_average', 'last_year')
            months: Number of months for monthly_average method
            
        Returns:
            Budget estimate as Decimal
        """
        try:
            if method == 'monthly_average':
                return CalculationUtils.calculate_monthly_average(queryset, amount_field, qty_field, months)
            elif method == 'ytd_average':
                ytd_total = CalculationUtils.calculate_ytd_total(queryset, amount_field, qty_field)
                current_month = datetime.now().month
                return ytd_total / current_month if current_month > 0 else Decimal('0.00')
            elif method == 'last_year':
                last_year = datetime.now().year - 1
                last_year_queryset = queryset.filter(transaction_date__year=last_year)
                if qty_field:
                    return sum(
                        Decimal(getattr(item, amount_field)) * Decimal(getattr(item, qty_field))
                        for item in last_year_queryset
                        if hasattr(item, amount_field) and hasattr(item, qty_field)
                    )
                else:
                    return sum(
                        Decimal(getattr(item, amount_field))
                        for item in last_year_queryset
                        if hasattr(item, amount_field)
                    )
            else:
                logger.warning(f"Unknown estimation method: {method}")
                return Decimal('0.00')
        except Exception as e:
            logger.error(f"Error calculating budget estimate: {str(e)}")
            return Decimal('0.00')
    
    @staticmethod
    def calculate_category_breakdown(queryset, amount_field: str, qty_field: str = None) -> Dict[str, Decimal]:
        """
        Calculate spending breakdown by category
        
        Args:
            queryset: Django queryset
            amount_field: Name of amount field
            qty_field: Name of quantity field (optional)
            
        Returns:
            Dictionary with category breakdown
        """
        breakdown = {}
        
        for item in queryset:
            if hasattr(item, 'category') and item.category:
                cat_name = item.category.name
                if cat_name not in breakdown:
                    breakdown[cat_name] = Decimal('0.00')
                
                if qty_field and hasattr(item, qty_field):
                    amount = Decimal(getattr(item, amount_field)) * Decimal(getattr(item, qty_field))
                else:
                    amount = Decimal(getattr(item, amount_field))
                
                breakdown[cat_name] += amount
        
        return breakdown
    
    @staticmethod
    def calculate_trend_analysis(queryset, amount_field: str, qty_field: str = None, 
                               periods: int = 6) -> Dict[str, Any]:
        """
        Calculate trend analysis over multiple periods
        
        Args:
            queryset: Django queryset
            amount_field: Name of amount field
            qty_field: Name of quantity field (optional)
            periods: Number of periods to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        end_date = timezone.now()
        period_data = []
        
        for i in range(periods):
            period_start = end_date - timedelta(days=(i + 1) * 30)
            period_end = end_date - timedelta(days=i * 30)
            
            period_queryset = queryset.filter(
                transaction_date__gte=period_start,
                transaction_date__lte=period_end
            )
            
            if qty_field:
                period_total = sum(
                    Decimal(getattr(item, amount_field)) * Decimal(getattr(item, qty_field))
                    for item in period_queryset
                    if hasattr(item, amount_field) and hasattr(item, qty_field)
                )
            else:
                period_total = sum(
                    Decimal(getattr(item, amount_field))
                    for item in period_queryset
                    if hasattr(item, amount_field)
                )
            
            period_data.append({
                'period': i + 1,
                'start_date': period_start,
                'end_date': period_end,
                'total': period_total
            })
        
        # Calculate trend
        if len(period_data) >= 2:
            recent_avg = sum(p['total'] for p in period_data[:3]) / 3
            older_avg = sum(p['total'] for p in period_data[3:]) / 3
            trend_percentage = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        else:
            trend_percentage = 0
        
        return {
            'period_data': period_data,
            'trend_percentage': trend_percentage,
            'trend_direction': 'increasing' if trend_percentage > 0 else 'decreasing' if trend_percentage < 0 else 'stable'
        }
    
    @staticmethod
    def calculate_variance_analysis(actual_queryset, budget_queryset, 
                                  actual_amount_field: str, budget_amount_field: str,
                                  actual_qty_field: str = None, budget_qty_field: str = None) -> Dict[str, Any]:
        """
        Calculate variance analysis between actual and budget
        
        Args:
            actual_queryset: Queryset with actual data
            budget_queryset: Queryset with budget data
            actual_amount_field: Name of actual amount field
            budget_amount_field: Name of budget amount field
            actual_qty_field: Name of actual quantity field (optional)
            budget_qty_field: Name of budget quantity field (optional)
            
        Returns:
            Dictionary with variance analysis
        """
        # Calculate actual total
        if actual_qty_field:
            actual_total = sum(
                Decimal(getattr(item, actual_amount_field)) * Decimal(getattr(item, actual_qty_field))
                for item in actual_queryset
                if hasattr(item, actual_amount_field) and hasattr(item, actual_qty_field)
            )
        else:
            actual_total = sum(
                Decimal(getattr(item, actual_amount_field))
                for item in actual_queryset
                if hasattr(item, actual_amount_field)
            )
        
        # Calculate budget total
        if budget_qty_field:
            budget_total = sum(
                Decimal(getattr(item, budget_amount_field)) * Decimal(getattr(item, budget_qty_field))
                for item in budget_queryset
                if hasattr(item, budget_amount_field) and hasattr(item, budget_qty_field)
            )
        else:
            budget_total = sum(
                Decimal(getattr(item, budget_amount_field))
                for item in budget_queryset
                if hasattr(item, budget_amount_field)
            )
        
        # Calculate variance
        variance = actual_total - budget_total
        variance_percentage = (variance / budget_total * 100) if budget_total > 0 else 0
        
        return {
            'actual_total': actual_total,
            'budget_total': budget_total,
            'variance': variance,
            'variance_percentage': variance_percentage,
            'status': 'over_budget' if variance > 0 else 'under_budget' if variance < 0 else 'on_budget'
        }

