"""
Budget Service

Handles all budget-related business logic including:
- Budget creation and management
- Budget projections
- Budget analytics
- Budget reporting

This service encapsulates the business logic previously scattered across finance/views.py
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import Budget, CodaBudget, BalanceSheetCategory
from .base_service import BaseFinanceService

logger = logging.getLogger(__name__)
User = get_user_model()


class BudgetService(BaseFinanceService):
    """
    Service for managing budget operations.
    
    Handles budget creation, management, projections, and analytics.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logger
    
    def create_budget_item(
        self, 
        user: User, 
        budget_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new budget item.
        
        Args:
            user: The user creating the budget item
            budget_data: Dictionary containing budget details
            
        Returns:
            Dict with success status and budget data
        """
        try:
            self._validate_user(user)
            
            # Validate required fields
            required_fields = ['company', 'department', 'category', 'item', 'qty', 'unit_price']
            for field in required_fields:
                if field not in budget_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Validate quantities and prices
            qty = self._validate_amount(budget_data['qty'])
            unit_price = self._validate_amount(budget_data['unit_price'])
            
            if qty <= 0:
                raise ValidationError("Quantity must be greater than 0")
            
            if unit_price < 0:
                raise ValidationError("Unit price cannot be negative")
            
            with transaction.atomic():
                # Create budget item
                budget_item = Budget.objects.create(
                    company=budget_data['company'],
                    budget_lead=user,
                    department=budget_data['department'],
                    category=budget_data['category'],
                    subcategory=budget_data.get('subcategory', ''),
                    item=budget_data['item'],
                    qty=qty,
                    unit_price=Decimal(str(unit_price)),
                    description=budget_data.get('description', ''),
                    is_active=budget_data.get('is_active', True),
                    receipt_link=budget_data.get('receipt_link', '')
                )
                
                # Log the operation
                self._log_operation(
                    'create_budget_item',
                    user,
                    {'budget_id': budget_item.id, 'total_cost': float(qty * unit_price)}
                )
                
                return self.create_success_response(
                    {'budget_id': budget_item.id, 'total_cost': float(qty * unit_price)},
                    "Budget item created successfully"
                )
                
        except Exception as e:
            self._handle_error(e, 'create_budget_item', user)
    
    def update_budget_item(
        self, 
        budget_id: int, 
        user: User,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing budget item.
        
        Args:
            budget_id: ID of the budget item
            user: The user updating the budget item
            update_data: Dictionary containing updated details
            
        Returns:
            Dict with success status and updated budget data
        """
        try:
            self._validate_user(user)
            
            # Get budget item
            try:
                budget_item = Budget.objects.get(id=budget_id)
            except ObjectDoesNotExist:
                raise ValidationError("Budget item not found")
            
            with transaction.atomic():
                # Update fields
                if 'qty' in update_data:
                    budget_item.qty = self._validate_amount(update_data['qty'])
                
                if 'unit_price' in update_data:
                    budget_item.unit_price = Decimal(str(self._validate_amount(update_data['unit_price'])))
                
                if 'description' in update_data:
                    budget_item.description = update_data['description']
                
                if 'is_active' in update_data:
                    budget_item.is_active = update_data['is_active']
                
                budget_item.save()
                
                # Log the operation
                self._log_operation(
                    'update_budget_item',
                    user,
                    {'budget_id': budget_id, 'total_cost': float(budget_item.qty * budget_item.unit_price)}
                )
                
                return self.create_success_response(
                    {'budget_id': budget_id, 'total_cost': float(budget_item.qty * budget_item.unit_price)},
                    "Budget item updated successfully"
                )
                
        except Exception as e:
            self._handle_error(e, 'update_budget_item', user)
    
    def get_budget_summary(
        self, 
        company: Optional[str] = None,
        department: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get budget summary with totals and breakdowns.
        
        Args:
            company: Optional company filter
            department: Optional department filter
            category: Optional category filter
            
        Returns:
            Dict with success status and budget summary
        """
        try:
            queryset = Budget.objects.filter(is_active=True)
            
            if company:
                queryset = queryset.filter(company=company)
            
            if department:
                queryset = queryset.filter(department=department)
            
            if category:
                queryset = queryset.filter(category=category)
            
            # Calculate totals
            total_items = queryset.count()
            total_cost = sum(float(item.qty * item.unit_price) for item in queryset)
            
            # Category breakdown
            category_breakdown = {}
            for item in queryset:
                cat = item.category
                if cat not in category_breakdown:
                    category_breakdown[cat] = {'count': 0, 'total': 0}
                category_breakdown[cat]['count'] += 1
                category_breakdown[cat]['total'] += float(item.qty * item.unit_price)
            
            # Department breakdown
            department_breakdown = {}
            for item in queryset:
                dept = item.department
                if dept not in department_breakdown:
                    department_breakdown[dept] = {'count': 0, 'total': 0}
                department_breakdown[dept]['count'] += 1
                department_breakdown[dept]['total'] += float(item.qty * item.unit_price)
            
            summary = {
                'total_items': total_items,
                'total_cost': total_cost,
                'category_breakdown': category_breakdown,
                'department_breakdown': department_breakdown
            }
            
            return self.create_success_response(
                {'summary': summary},
                "Budget summary retrieved successfully"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_budget_summary')
    
    def create_budget_projection(
        self, 
        user: User, 
        projection_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a budget projection.
        
        Args:
            user: The user creating the projection
            projection_data: Dictionary containing projection details
            
        Returns:
            Dict with success status and projection data
        """
        try:
            self._validate_user(user)
            
            # Validate required fields
            required_fields = ['company', 'projection_type', 'projected_amount']
            for field in required_fields:
                if field not in projection_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Validate projected amount
            projected_amount = self._validate_amount(projection_data['projected_amount'])
            
            with transaction.atomic():
                # Create budget projection
                projection = CodaBudget.objects.create(
                    company=projection_data['company'],
                    projection_type=projection_data['projection_type'],
                    projected_amount=Decimal(str(projected_amount)),
                    created_by=user,
                    created_at=timezone.now(),
                    is_active=True
                )
                
                # Log the operation
                self._log_operation(
                    'create_budget_projection',
                    user,
                    {'projection_id': projection.id, 'amount': projected_amount}
                )
                
                return self.create_success_response(
                    {'projection_id': projection.id, 'amount': projected_amount},
                    "Budget projection created successfully"
                )
                
        except Exception as e:
            self._handle_error(e, 'create_budget_projection', user)
    
    def get_budget_analytics(
        self, 
        company: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get budget analytics and insights.
        
        Args:
            company: Optional company filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            
        Returns:
            Dict with success status and analytics data
        """
        try:
            # Get budget items
            budget_queryset = Budget.objects.filter(is_active=True)
            if company:
                budget_queryset = budget_queryset.filter(company=company)
            
            # Get projections
            projection_queryset = CodaBudget.objects.filter(is_active=True)
            if company:
                projection_queryset = projection_queryset.filter(company=company)
            
            if date_from:
                budget_queryset = budget_queryset.filter(created_at__gte=date_from)
                projection_queryset = projection_queryset.filter(created_at__gte=date_from)
            
            if date_to:
                budget_queryset = budget_queryset.filter(created_at__lte=date_to)
                projection_queryset = projection_queryset.filter(created_at__lte=date_to)
            
            # Calculate analytics
            total_budget_items = budget_queryset.count()
            total_budget_cost = sum(float(item.qty * item.unit_price) for item in budget_queryset)
            
            total_projections = projection_queryset.count()
            total_projected_amount = sum(float(p.projected_amount) for p in projection_queryset)
            
            # Budget vs Projection analysis
            variance = total_projected_amount - total_budget_cost
            variance_percentage = (variance / total_projected_amount * 100) if total_projected_amount > 0 else 0
            
            # Top categories by cost
            category_costs = {}
            for item in budget_queryset:
                cat = item.category
                if cat not in category_costs:
                    category_costs[cat] = 0
                category_costs[cat] += float(item.qty * item.unit_price)
            
            top_categories = sorted(category_costs.items(), key=lambda x: x[1], reverse=True)[:5]
            
            analytics = {
                'total_budget_items': total_budget_items,
                'total_budget_cost': total_budget_cost,
                'total_projections': total_projections,
                'total_projected_amount': total_projected_amount,
                'variance': variance,
                'variance_percentage': round(variance_percentage, 2),
                'top_categories': top_categories
            }
            
            return self.create_success_response(
                {'analytics': analytics},
                "Budget analytics retrieved successfully"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_budget_analytics')
    
    def delete_budget_item(
        self, 
        budget_id: int, 
        user: User
    ) -> Dict[str, Any]:
        """
        Delete a budget item.
        
        Args:
            budget_id: ID of the budget item
            user: The user deleting the budget item
            
        Returns:
            Dict with success status
        """
        try:
            self._validate_user(user)
            
            # Get budget item
            try:
                budget_item = Budget.objects.get(id=budget_id)
            except ObjectDoesNotExist:
                raise ValidationError("Budget item not found")
            
            with transaction.atomic():
                # Soft delete by setting is_active to False
                budget_item.is_active = False
                budget_item.save()
                
                # Log the operation
                self._log_operation(
                    'delete_budget_item',
                    user,
                    {'budget_id': budget_id}
                )
                
                return self.create_success_response(
                    {'budget_id': budget_id},
                    "Budget item deleted successfully"
                )
                
        except Exception as e:
            self._handle_error(e, 'delete_budget_item', user)

