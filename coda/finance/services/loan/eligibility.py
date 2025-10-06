# -*- coding: utf-8 -*-
"""
Loan Eligibility Service
Handles loan eligibility calculations and checks
"""

from django.contrib.auth import get_user_model
from django.db.models import Sum, Q
from decimal import Decimal
import logging

from finance.models import LoanApplication, LoanProduct, Budget
from finance.services.core.base import BaseFinanceService

logger = logging.getLogger(__name__)
User = get_user_model()


class LoanEligibilityService(BaseFinanceService):
    """Service for calculating loan eligibility based on budget constraints."""
    
    def calculate_eligibility(self, user, loan_amount, budget_availability):
        """
        Calculate loan eligibility based on budget constraints.
        
        Args:
            user: User requesting the loan
            loan_amount: Amount requested
            budget_availability: Available budget data
            
        Returns:
            dict: Eligibility result with recommendations
        """
        try:
            max_loan_amount = budget_availability.get('available_for_loans', 0)
            
            eligibility = {
                'eligible': loan_amount <= max_loan_amount,
                'max_loan_amount': float(max_loan_amount),
                'requested_amount': float(loan_amount),
                'budget_availability': budget_availability,
                'recommendations': []
            }
            
            if loan_amount > max_loan_amount:
                eligibility['recommendations'].append(
                    f"Reduce loan amount to ${max_loan_amount:,.2f} or less"
                )
            
            # Check existing loans
            existing_loans = LoanApplication.objects.filter(
                borrower=user,
                status__in=['active', 'approved']
            )
            
            if existing_loans.exists():
                total_existing_payments = sum(
                    loan.monthly_payment or 0 for loan in existing_loans
                )
                eligibility['existing_loan_payments'] = float(total_existing_payments)
                eligibility['recommendations'].append(
                    f"You have existing loan payments of ${total_existing_payments:,.2f}/month"
                )
            
            return eligibility
            
        except Exception as e:
            logger.error(f"Error calculating loan eligibility: {e}")
            return {
                'eligible': False,
                'error': str(e),
                'recommendations': ['Unable to calculate eligibility. Please try again.']
            }
    
    def get_budget_availability(self, company, department):
        """
        Calculate available budget for loans.
        
        Args:
            company: Company object
            department: Department object
            
        Returns:
            dict: Budget availability data
        """
        try:
            # Get total budget allocations
            total_budget = Budget.objects.filter(
                company=company,
                department=department,
                status='active'
            ).aggregate(
                total=Sum('estimated_amount')
            )['total'] or Decimal('0.00')
            
            # Get total actual spending
            total_actual = Budget.objects.filter(
                company=company,
                department=department,
                status='active'
            ).aggregate(
                total=Sum('actual_spent')
            )['total'] or Decimal('0.00')
            
            # Get existing loan allocations
            loan_allocations = Budget.objects.filter(
                company=company,
                department=department,
                item_name__icontains='loan'
            ).aggregate(
                total=Sum('estimated_amount')
            )['total'] or Decimal('0.00')
            
            # Calculate available amount
            available_budget = total_budget - total_actual
            available_for_loans = max(Decimal('0.00'), available_budget - loan_allocations)
            
            return {
                'total_budget': total_budget,
                'total_actual': total_actual,
                'available_budget': available_budget,
                'existing_loan_allocations': loan_allocations,
                'available_for_loans': available_for_loans,
                'utilization_percentage': (total_actual / total_budget * 100) if total_budget > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating budget availability: {e}")
            return {
                'total_budget': Decimal('0.00'),
                'total_actual': Decimal('0.00'),
                'available_budget': Decimal('0.00'),
                'existing_loan_allocations': Decimal('0.00'),
                'available_for_loans': Decimal('0.00'),
                'utilization_percentage': 0
            }