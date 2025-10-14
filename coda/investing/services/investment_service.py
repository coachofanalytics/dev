"""
Investment Service

Handles all investment-related business logic including:
- Investment plan management
- Investment creation and tracking
- Investment rate management
- Investment calculations

This service encapsulates the business logic previously scattered across investing/views.py
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import Investment_rates, Investor_Information
from .base_service import BaseInvestingService

logger = logging.getLogger(__name__)
User = get_user_model()


class InvestmentService(BaseInvestingService):
    """
    Service for managing investment operations.
    
    Handles investment plans, creation, tracking, and rate management.
    """

    def __init__(self):
        super().__init__()
        self.logger = logger
    
    def create_investment(
        self, 
        user: User, 
        investment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new investment.
        
        Args:
            user: The user making the investment
            investment_data: Dictionary containing investment details
            
        Returns:
            Dict with success status and investment data
        """
        try:
            self._validate_user(user)
            
            # Validate required fields
            required_fields = ['amount_invested', 'investment_plan']
            for field in required_fields:
                if field not in investment_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Validate investment amount
            amount = self._validate_investment_amount(investment_data['amount_invested'])
            
            # Get investment plan
            try:
                investment_plan = Investment_rates.objects.get(id=investment_data['investment_plan'])
            except Investment_rates.DoesNotExist:
                raise ValidationError("Invalid investment plan")
            
            with transaction.atomic():
                # Create investment using Investor_Information model
                investment = Investor_Information.objects.create(
                    investor=user,
                    amount_invested=Decimal(str(amount)),
                    investment_type=investment_data.get('investment_type', 'equity'),
                    investment_purpose=investment_data.get('investment_purpose', 'Investment in CODA'),
                    duration=investment_data.get('duration', 12),
                    revenue_share_percentage=investment_data.get('revenue_share_percentage', Decimal('8.00')),
                    expected_return_rate=investment_data.get('expected_return_rate', Decimal('8.00')),
                    risk_tolerance=investment_data.get('risk_tolerance', 'moderate'),
                    kyc_status='pending',
                    status='pending',
                    model_type=investment_data.get('model_type', 'Installment')
                )
                
                # Log the operation
                self._log_operation(
                    'create_investment',
                    user,
                    {'investment_id': investment.id, 'amount': amount}
                )
                
                return {
                    'status': 'success',
                    'message': 'Investment application submitted successfully',
                    'data': {'investment_id': investment.id, 'amount': amount}
                }
                
        except Exception as e:
            self.logger.error(f"Error creating investment for user {user.id}: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to create investment: {str(e)}',
                'data': {}
            }
    
    def get_user_investments(
        self, 
        user: User,
        status_filter: Optional[str] = None,
        investment_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get investments for a user.
        
        Args:
            user: The user whose investments to retrieve
            status_filter: Optional status filter ('active', 'closed', 'pending')
            investment_type: Optional investment type filter
            
        Returns:
            Dict with success status and list of investments
        """
        try:
            self._validate_user(user)
            
            queryset = Investor_Information.objects.filter(investor=user)
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            if investment_type:
                queryset = queryset.filter(investment_type=investment_type)
            
            investments = []
            for investment in queryset.order_by('-created_at'):
                investments.append({
                    'id': investment.id,
                    'amount_invested': float(investment.amount_invested),
                    'current_value': float(investment.current_value),
                    'investment_type': investment.investment_type,
                    'status': investment.status,
                    'created_at': investment.created_at,
                    'investment_date': investment.investment_date,
                    'expected_return_rate': float(investment.expected_return_rate),
                    'total_returns_paid': float(investment.total_returns_paid),
                    'notes': investment.notes
                })
            
            return self.create_success_response(
                {'investments': investments},
                f"Retrieved {len(investments)} investments"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_user_investments', user)
    
    def create_investment_rate(
        self, 
        user: User, 
        rate_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new investment rate.
        
        Args:
            user: The user creating the rate
            rate_data: Dictionary containing rate details
            
        Returns:
            Dict with success status and rate data
        """
        try:
            self._validate_user(user)
            
            # Validate required fields
            required_fields = ['rate_name', 'rate_value', 'rate_type']
            for field in required_fields:
                if field not in rate_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Validate rate value
            rate_value = self._validate_amount(rate_data['rate_value'])
            
            # Validate rate type
            valid_types = ['annual', 'monthly', 'daily', 'compound']
            if rate_data['rate_type'] not in valid_types:
                raise ValidationError(f"Invalid rate type: {rate_data['rate_type']}")
            
            with transaction.atomic():
                # Create investment rate
                investment_rate = Investment_rates.objects.create(
                    name=rate_data['rate_name'],
                    rate=Decimal(str(rate_value)),
                    type=rate_data['rate_type'],
                    description=rate_data.get('description', '')
                )
                
                # Log the operation
                self._log_operation(
                    'create_investment_rate',
                    user,
                    {'rate_id': investment_rate.id, 'rate_value': rate_value}
                )
                
                return self.create_success_response(
                    {'rate_id': investment_rate.id, 'rate_value': rate_value},
                    "Investment rate created successfully"
                )

        except Exception as e:
            self._handle_error(e, 'create_investment_rate', user)
    
    def get_investment_rates(
        self, 
        rate_type: Optional[str] = None,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """
        Get investment rates.
        
        Args:
            rate_type: Optional rate type filter
            active_only: Whether to return only active rates
            
        Returns:
            Dict with success status and list of rates
        """
        try:
            queryset = Investment_rates.objects.all()
            
            # Note: is_active field doesn't exist in Investment_rates model
            
            if rate_type:
                queryset = queryset.filter(type=rate_type)
            
            rates = []
            for rate in queryset.order_by('-created_date'):
                rates.append({
                    'id': rate.id,
                    'rate_name': rate.name,
                    'rate_value': float(rate.rate),
                    'rate_type': rate.type,
                    'description': rate.description,
                    'created_at': rate.created_date,
                    'is_active': True  # This field doesn't exist in the model
                })
            
            return self.create_success_response(
                {'rates': rates},
                f"Retrieved {len(rates)} investment rates"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_investment_rates')
    
    def calculate_investment_returns(
        self, 
        investment_id: int,
        user: User
    ) -> Dict[str, Any]:
        """
        Calculate returns for an investment.
        
        Args:
            investment_id: ID of the investment
            user: The user requesting the calculation
            
        Returns:
            Dict with success status and return calculations
        """
        try:
            self._validate_user(user)
            
            # Get investment
            try:
                investment = Investor_Information.objects.get(id=investment_id, user=user)
            except ObjectDoesNotExist:
                raise ValidationError("Investment not found")
            
            # Get applicable rate
            rate = Investment_rates.objects.filter(
                rate_type='annual',
                is_active=True
            ).first()
            
            if not rate:
                raise ValidationError("No active investment rate found")
            
            # Calculate returns
            principal = float(investment.amount)
            rate_value = float(rate.rate_value)
            
            # Simple annual return calculation
            annual_return = principal * (rate_value / 100)
            
            # Calculate for different time periods
            monthly_return = annual_return / 12
            daily_return = annual_return / 365
            
            # Calculate compound returns for different periods
            compound_1_year = principal * ((1 + rate_value/100) ** 1)
            compound_5_years = principal * ((1 + rate_value/100) ** 5)
            compound_10_years = principal * ((1 + rate_value/100) ** 10)
            
            calculations = {
                'principal': principal,
                'rate_value': rate_value,
                'annual_return': round(annual_return, 2),
                'monthly_return': round(monthly_return, 2),
                'daily_return': round(daily_return, 2),
                'compound_1_year': round(compound_1_year, 2),
                'compound_5_years': round(compound_5_years, 2),
                'compound_10_years': round(compound_10_years, 2),
                'total_gain_1_year': round(compound_1_year - principal, 2),
                'total_gain_5_years': round(compound_5_years - principal, 2),
                'total_gain_10_years': round(compound_10_years - principal, 2)
            }
            
            return self.create_success_response(
                {'calculations': calculations},
                "Investment returns calculated successfully"
            )
            
        except Exception as e:
            self._handle_error(e, 'calculate_investment_returns', user)
    
    def update_investment_status(
        self, 
        investment_id: int, 
        user: User,
        new_status: str
    ) -> Dict[str, Any]:
        """
        Update investment status.
        
        Args:
            investment_id: ID of the investment
            user: The user updating the investment
            new_status: New status for the investment
            
        Returns:
            Dict with success status
        """
        try:
            self._validate_user(user)
            
            # Validate status
            valid_statuses = ['active', 'closed', 'pending', 'suspended']
            if new_status not in valid_statuses:
                raise ValidationError(f"Invalid status: {new_status}")
            
            # Get investment
            try:
                investment = Investor_Information.objects.get(id=investment_id, user=user)
            except ObjectDoesNotExist:
                raise ValidationError("Investment not found")
            
            with transaction.atomic():
                # Update status
                old_status = investment.status
                investment.status = new_status
                investment.updated_at = timezone.now()
                investment.save()

                # Log the operation
                self._log_operation(
                    'update_investment_status',
                    user,
                    {'investment_id': investment_id, 'old_status': old_status, 'new_status': new_status}
                )
                
                return self.create_success_response(
                    {'investment_id': investment_id, 'status': new_status},
                    f"Investment status updated from {old_status} to {new_status}"
                )
                
        except Exception as e:
            self._handle_error(e, 'update_investment_status', user)
    
    def get_investment_summary(
        self, 
        user: User
    ) -> Dict[str, Any]:
        """
        Get investment summary for a user.
        
        Args:
            user: The user whose summary to retrieve
            
        Returns:
            Dict with success status and summary data
        """
        try:
            self._validate_user(user)
            
            # Get all user investments
            investments = Investor_Information.objects.filter(user=user)
            
            # Calculate summary statistics
            total_investments = investments.count()
            total_amount = sum(float(inv.amount) for inv in investments)
            
            # Status breakdown
            status_breakdown = {}
            for investment in investments:
                status = investment.status
                if status not in status_breakdown:
                    status_breakdown[status] = {'count': 0, 'amount': 0}
                status_breakdown[status]['count'] += 1
                status_breakdown[status]['amount'] += float(investment.amount)
            
            # Type breakdown
            type_breakdown = {}
            for investment in investments:
                inv_type = investment.investment_type
                if inv_type not in type_breakdown:
                    type_breakdown[inv_type] = {'count': 0, 'amount': 0}
                type_breakdown[inv_type]['count'] += 1
                type_breakdown[inv_type]['amount'] += float(investment.amount)
            
            summary = {
                'total_investments': total_investments,
                'total_amount': total_amount,
                'status_breakdown': status_breakdown,
                'type_breakdown': type_breakdown
            }
            
            return self.create_success_response(
                {'summary': summary},
                "Investment summary retrieved successfully"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_investment_summary', user)
    
    def get_investment_plans_for_user(self, user: User) -> Dict[str, Any]:
        """
        Get investment plans available for a user based on their investor type.
        
        Args:
            user: The user requesting investment plans
            
        Returns:
            Dict with success status and list of investment plans
        """
        try:
            self._validate_user(user)
            
            # Determine investor type based on user category/subcategory
            investor_type = "individual"  # Default
            
            if hasattr(user, 'category'):
                if user.category == 4:  # Investor category
                    if hasattr(user, 'sub_category'):
                        if user.sub_category == 1:  # Angel
                            investor_type = "angel"
                        elif user.sub_category == 2:  # VC
                            investor_type = "vc"
                        elif user.sub_category == 3:  # Private
                            investor_type = "private"
                        elif user.sub_category == 4:  # Individual
                            investor_type = "individual"
            
            # Get investment plans based on investor type
            if investor_type == "angel":
                # Angel investors get higher tier plans
                plans = Investment_rates.objects.filter(
                    type="investment",
                    tier__in=["Tier 2", "Tier 3"],
                    is_active=True
                ).order_by('-base_amount')
            elif investor_type == "vc":
                # VC investors get all plans
                plans = Investment_rates.objects.filter(
                    type="investment",
                    is_active=True
                ).order_by('-base_amount')
            elif investor_type == "private":
                # Private equity investors get highest tier plans
                plans = Investment_rates.objects.filter(
                    type="investment",
                    tier="Tier 3",
                    is_active=True
                ).order_by('-base_amount')
            else:
                # Individual investors get all plans
                plans = Investment_rates.objects.filter(
                    type="investment",
                    is_active=True
                ).order_by('base_amount')
            
            # Convert to list of dictionaries
            plans_list = []
            for plan in plans:
                plans_list.append({
                    'id': plan.id,
                    'name': plan.name or f"Investment Plan {plan.id}",
                    'description': plan.description or "Professional investment opportunity",
                    'tier': plan.tier or "Tier 1",
                    'base_amount': float(plan.base_amount or 1000),
                    'rate': float(plan.rate * 100),  # Convert to percentage
                    'duration': plan.duration or 12,
                    'type': plan.type,
                    'is_featured': plan.is_featured,
                    'advantages': plan.advantages or "Professional management, Regular reporting"
                })
            
            return {
                'status': 'success',
                'plans': plans_list,
                'investor_type': investor_type
            }
            
        except Exception as e:
            self.logger.error(f"Error getting investment plans for user {user.id}: {str(e)}")
            return {
                'status': 'error',
                'message': 'Failed to retrieve investment plans',
                'plans': [],
                'investor_type': 'individual'
            }