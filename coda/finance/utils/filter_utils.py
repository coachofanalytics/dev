"""
Filter Utilities for CODA Finance System

Standardized filtering utilities for financial operations including:
- User-based filtering
- Company and department filtering
- Time-based filtering
- Status and category filtering
- Combined filtering
"""

from django.db.models import Q
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class FilterUtils:
    """Standardized filtering utilities for financial operations"""
    
    @staticmethod
    def get_user_filter(user, is_staff_override: bool = False) -> Q:
        """
        Get user-based filter with staff override option
        
        Args:
            user: User object
            is_staff_override: Whether to allow staff to see all data
            
        Returns:
            Django Q object for user filtering
        """
        if is_staff_override and (user.is_staff or user.is_superuser):
            return Q()  # No filtering for staff
        return Q(customer=user) | Q(requester=user) | Q(borrower=user)
    
    @staticmethod
    def get_company_filter(company) -> Q:
        """
        Get company-based filter
        
        Args:
            company: Company object
            
        Returns:
            Django Q object for company filtering
        """
        # For models with direct company field
        return Q(company=company)
    
    @staticmethod
    def get_company_filter_via_department(company) -> Q:
        """
        Get company-based filter via department relationship
        
        Args:
            company: Company object
            
        Returns:
            Django Q object for company filtering via department
        """
        # For models where department doesn't have company field,
        # we need to filter by department directly if company is provided
        # This is a fallback - the calling code should handle company filtering differently
        return Q()  # Return empty filter as fallback
    
    @staticmethod
    def get_department_filter(department) -> Q:
        """
        Get department-based filter
        
        Args:
            department: Department object
            
        Returns:
            Django Q object for department filtering
        """
        return Q(department=department)
    
    @staticmethod
    def get_status_filter(status: str) -> Q:
        """
        Get status-based filter
        
        Args:
            status: Status string
            
        Returns:
            Django Q object for status filtering
        """
        return Q(status=status)
    
    @staticmethod
    def get_time_filter(start_date=None, end_date=None, months: int = None) -> Q:
        """
        Get time-based filter
        
        Args:
            start_date: Start date (optional)
            end_date: End date (optional)
            months: Number of months back from now (optional)
            
        Returns:
            Django Q object for time filtering
        """
        if months:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=months * 30)
        
        if start_date and end_date:
            return Q(transaction_date__gte=start_date, transaction_date__lte=end_date)
        elif start_date:
            return Q(transaction_date__gte=start_date)
        elif end_date:
            return Q(transaction_date__lte=end_date)
        return Q()
    
    @staticmethod
    def get_category_filter(category) -> Q:
        """
        Get category-based filter
        
        Args:
            category: Category object
            
        Returns:
            Django Q object for category filtering
        """
        return Q(category=category)
    
    @staticmethod
    def get_subcategory_filter(subcategory) -> Q:
        """
        Get subcategory-based filter
        
        Args:
            subcategory: Subcategory object
            
        Returns:
            Django Q object for subcategory filtering
        """
        return Q(subcategory=subcategory)
    
    @staticmethod
    def get_amount_range_filter(min_amount: float = None, max_amount: float = None) -> Q:
        """
        Get amount range filter
        
        Args:
            min_amount: Minimum amount (optional)
            max_amount: Maximum amount (optional)
            
        Returns:
            Django Q object for amount range filtering
        """
        if min_amount and max_amount:
            return Q(amount__gte=min_amount, amount__lte=max_amount)
        elif min_amount:
            return Q(amount__gte=min_amount)
        elif max_amount:
            return Q(amount__lte=max_amount)
        return Q()
    
    @staticmethod
    def get_priority_filter(priority: str) -> Q:
        """
        Get priority-based filter
        
        Args:
            priority: Priority string
            
        Returns:
            Django Q object for priority filtering
        """
        return Q(priority=priority)
    
    @staticmethod
    def get_active_filter(is_active: bool = True) -> Q:
        """
        Get active/inactive filter
        
        Args:
            is_active: Whether to filter for active items
            
        Returns:
            Django Q object for active filtering
        """
        return Q(is_active=is_active)
    
    @staticmethod
    def get_combined_filter(user=None, company=None, department=None, 
                          status=None, start_date=None, end_date=None, 
                          category=None, subcategory=None, min_amount=None,
                          max_amount=None, priority=None, is_active=None,
                          is_staff_override=False, model_class=None) -> Q:
        """
        Get combined filter with multiple criteria
        
        Args:
            user: User object (optional)
            company: Company object (optional)
            department: Department object (optional)
            status: Status string (optional)
            start_date: Start date (optional)
            end_date: End date (optional)
            category: Category object (optional)
            subcategory: Subcategory object (optional)
            min_amount: Minimum amount (optional)
            max_amount: Maximum amount (optional)
            priority: Priority string (optional)
            is_active: Active status (optional)
            is_staff_override: Whether to allow staff to see all data
            model_class: Model class to determine appropriate company filter
            
        Returns:
            Django Q object with combined filters
        """
        filters = Q()
        
        if user:
            filters &= FilterUtils.get_user_filter(user, is_staff_override)
        if company:
            # Use appropriate company filter based on model
            if model_class and hasattr(model_class, '_meta'):
                model_name = model_class._meta.model_name
                if model_name == 'transaction':
                    # Transaction doesn't have company field, skip company filtering
                    # Company filtering for transactions should be handled by filtering departments
                    pass
                else:
                    # Other models have direct company field
                    filters &= FilterUtils.get_company_filter(company)
            else:
                # Default to direct company filter
                filters &= FilterUtils.get_company_filter(company)
        if department:
            filters &= FilterUtils.get_department_filter(department)
        if status:
            filters &= FilterUtils.get_status_filter(status)
        if start_date or end_date:
            filters &= FilterUtils.get_time_filter(start_date, end_date)
        if category:
            filters &= FilterUtils.get_category_filter(category)
        if subcategory:
            filters &= FilterUtils.get_subcategory_filter(subcategory)
        if min_amount or max_amount:
            filters &= FilterUtils.get_amount_range_filter(min_amount, max_amount)
        if priority:
            filters &= FilterUtils.get_priority_filter(priority)
        if is_active is not None:
            filters &= FilterUtils.get_active_filter(is_active)
        
        return filters
    
    @staticmethod
    def get_financial_year_filter(year: int = None) -> Q:
        """
        Get financial year filter
        
        Args:
            year: Financial year (optional, defaults to current year)
            
        Returns:
            Django Q object for financial year filtering
        """
        if year is None:
            year = datetime.now().year
        
        from django.utils import timezone
        start_date = timezone.make_aware(datetime(year, 1, 1))
        end_date = timezone.make_aware(datetime(year, 12, 31, 23, 59, 59))
        
        return Q(transaction_date__gte=start_date, transaction_date__lte=end_date)
    
    @staticmethod
    def get_quarter_filter(quarter: int, year: int = None) -> Q:
        """
        Get quarter filter
        
        Args:
            quarter: Quarter number (1-4)
            year: Year (optional, defaults to current year)
            
        Returns:
            Django Q object for quarter filtering
        """
        if year is None:
            year = datetime.now().year
        
        quarter_months = {
            1: (1, 3),   # Q1: Jan-Mar
            2: (4, 6),   # Q2: Apr-Jun
            3: (7, 9),   # Q3: Jul-Sep
            4: (10, 12)  # Q4: Oct-Dec
        }
        
        if quarter not in quarter_months:
            return Q()
        
        start_month, end_month = quarter_months[quarter]
        start_date = datetime(year, start_month, 1)
        end_date = datetime(year, end_month, 31)
        
        return Q(transaction_date__gte=start_date, transaction_date__lte=end_date)
    
    @staticmethod
    def get_payment_method_filter(payment_method: str) -> Q:
        """
        Get payment method filter
        
        Args:
            payment_method: Payment method string
            
        Returns:
            Django Q object for payment method filtering
        """
        return Q(payment_method=payment_method)
    
    @staticmethod
    def get_currency_filter(currency: str) -> Q:
        """
        Get currency filter
        
        Args:
            currency: Currency code string
            
        Returns:
            Django Q object for currency filtering
        """
        return Q(currency=currency)
    
    @staticmethod
    def get_approval_status_filter(approval_status: str) -> Q:
        """
        Get approval status filter
        
        Args:
            approval_status: Approval status string
            
        Returns:
            Django Q object for approval status filtering
        """
        return Q(approval_status=approval_status)
    
    @staticmethod
    def get_advanced_filter(filters_dict: Dict[str, Any]) -> Q:
        """
        Get advanced filter from dictionary
        
        Args:
            filters_dict: Dictionary of filter criteria
            
        Returns:
            Django Q object with advanced filters
        """
        combined_filter = Q()
        
        for key, value in filters_dict.items():
            if value is not None:
                if key == 'user':
                    combined_filter &= FilterUtils.get_user_filter(value, filters_dict.get('is_staff_override', False))
                elif key == 'company':
                    combined_filter &= FilterUtils.get_company_filter(value)
                elif key == 'department':
                    combined_filter &= FilterUtils.get_department_filter(value)
                elif key == 'status':
                    combined_filter &= FilterUtils.get_status_filter(value)
                elif key == 'category':
                    combined_filter &= FilterUtils.get_category_filter(value)
                elif key == 'subcategory':
                    combined_filter &= FilterUtils.get_subcategory_filter(value)
                elif key == 'priority':
                    combined_filter &= FilterUtils.get_priority_filter(value)
                elif key == 'payment_method':
                    combined_filter &= FilterUtils.get_payment_method_filter(value)
                elif key == 'currency':
                    combined_filter &= FilterUtils.get_currency_filter(value)
                elif key == 'approval_status':
                    combined_filter &= FilterUtils.get_approval_status_filter(value)
                elif key == 'is_active':
                    combined_filter &= FilterUtils.get_active_filter(value)
                elif key == 'start_date' or key == 'end_date':
                    combined_filter &= FilterUtils.get_time_filter(
                        filters_dict.get('start_date'),
                        filters_dict.get('end_date')
                    )
                elif key == 'min_amount' or key == 'max_amount':
                    combined_filter &= FilterUtils.get_amount_range_filter(
                        filters_dict.get('min_amount'),
                        filters_dict.get('max_amount')
                    )
                elif key == 'quarter':
                    combined_filter &= FilterUtils.get_quarter_filter(
                        value,
                        filters_dict.get('year')
                    )
                elif key == 'financial_year':
                    combined_filter &= FilterUtils.get_financial_year_filter(value)
        
        return combined_filter

