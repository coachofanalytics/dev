"""
Payment processing service - handles payment processing and validation.
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta

from ..core.base import BaseFinanceService
from ...models import Transaction, Budget, BudgetCategory

logger = logging.getLogger(__name__)


class PaymentProcessingService(BaseFinanceService):
    """
    Service for processing payments and handling payment validation.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment transaction."""
        try:
            # Validate payment data
            validation_result = self._validate_payment_data(payment_data)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'validation_errors': validation_result['errors']
                }
            
            # Check budget availability
            budget_check = self._check_budget_availability(payment_data)
            if not budget_check['available']:
                return {
                    'success': False,
                    'error': 'Insufficient budget available',
                    'budget_details': budget_check
                }
            
            # Process the payment
            payment_result = self._execute_payment(payment_data)
            
            if payment_result['success']:
                # Update budget
                self._update_budget(payment_data, payment_result)
                
                # Log payment
                self._log_payment(payment_data, payment_result)
                
                return {
                    'success': True,
                    'payment_id': payment_result['payment_id'],
                    'transaction_id': payment_result['transaction_id'],
                    'amount': payment_data['amount'],
                    'status': 'completed'
                }
            else:
                return {
                    'success': False,
                    'error': payment_result['error']
                }
        
        except Exception as e:
            self.log_error("Error processing payment", e)
            return {
                'success': False,
                'error': 'Payment processing failed due to system error'
            }
    
    def _validate_payment_data(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate payment data."""
        try:
            errors = []
            
            # Check required fields
            required_fields = ['amount', 'receiver', 'category_id', 'department_id']
            for field in required_fields:
                if field not in payment_data or not payment_data[field]:
                    errors.append(f"Missing required field: {field}")
            
            # Validate amount
            if 'amount' in payment_data:
                try:
                    amount = Decimal(str(payment_data['amount']))
                    if amount <= 0:
                        errors.append("Amount must be greater than zero")
                except (ValueError, TypeError):
                    errors.append("Invalid amount format")
            
            # Validate category
            if 'category_id' in payment_data:
                try:
                    category = BudgetCategory.objects.get(id=payment_data['category_id'])
                except BudgetCategory.DoesNotExist:
                    errors.append("Invalid category ID")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'error': 'Validation failed' if errors else None
            }
        
        except Exception as e:
            self.log_error("Error validating payment data", e)
            return {
                'valid': False,
                'errors': ['Validation error'],
                'error': str(e)
            }
    
    def _check_budget_availability(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if budget is available for the payment."""
        try:
            category_id = payment_data.get('category_id')
            department_id = payment_data.get('department_id')
            amount = Decimal(str(payment_data['amount']))
            
            # Get budget for the category and department
            budget = Budget.objects.filter(
                category_id=category_id,
                department_id=department_id,
                is_active=True
            ).first()
            
            if not budget:
                return {
                    'available': False,
                    'reason': 'No budget found for this category and department'
                }
            
            # Check available amount
            available_amount = budget.estimated_amount - budget.actual_spent
            
            if amount > available_amount:
                return {
                    'available': False,
                    'reason': 'Insufficient budget available',
                    'requested_amount': amount,
                    'available_amount': available_amount,
                    'budget_id': budget.id
                }
            
            return {
                'available': True,
                'available_amount': available_amount,
                'budget_id': budget.id
            }
        
        except Exception as e:
            self.log_error("Error checking budget availability", e)
            return {
                'available': False,
                'reason': 'Error checking budget availability'
            }
    
    def _execute_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the payment transaction."""
        try:
            # Create transaction record
            transaction = Transaction.objects.create(
                sender=payment_data.get('sender'),
                receiver=payment_data['receiver'],
                amount=Decimal(str(payment_data['amount'])),
                category_id=payment_data['category_id'],
                department_id=payment_data['department_id'],
                transaction_date=timezone.now(),
                payment_method=payment_data.get('payment_method', 'unknown'),
                description=payment_data.get('description', ''),
                status='completed'
            )
            
            return {
                'success': True,
                'payment_id': f"PAY_{transaction.id}_{int(timezone.now().timestamp())}",
                'transaction_id': transaction.id,
                'transaction': transaction
            }
        
        except Exception as e:
            self.log_error("Error executing payment", e)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_budget(self, payment_data: Dict[str, Any], payment_result: Dict[str, Any]):
        """Update budget with payment information."""
        try:
            category_id = payment_data.get('category_id')
            department_id = payment_data.get('department_id')
            amount = Decimal(str(payment_data['amount']))
            
            # Update budget actual spent
            budget = Budget.objects.filter(
                category_id=category_id,
                department_id=department_id,
                is_active=True
            ).first()
            
            if budget:
                budget.actual_spent += amount
                budget.save(update_fields=['actual_spent'])
        
        except Exception as e:
            self.log_error("Error updating budget", e)
    
    def _log_payment(self, payment_data: Dict[str, Any], payment_result: Dict[str, Any]):
        """Log payment for audit purposes."""
        try:
            # Log payment details
            self.log_info("Payment processed successfully", {
                'payment_id': payment_result['payment_id'],
                'transaction_id': payment_result['transaction_id'],
                'amount': payment_data['amount'],
                'receiver': payment_data['receiver'],
                'category_id': payment_data['category_id'],
                'department_id': payment_data['department_id']
            })
        
        except Exception as e:
            self.log_error("Error logging payment", e)
    
    def get_payment_history(self, user, start_date=None, end_date=None) -> Dict[str, Any]:
        """Get payment history for a user."""
        try:
            # Set default date range if not provided
            if not start_date:
                start_date = timezone.now().date() - timedelta(days=30)
            if not end_date:
                end_date = timezone.now().date()
            
            # Get transactions
            transactions = Transaction.objects.filter(
                sender=user,
                transaction_date__date__gte=start_date,
                transaction_date__date__lte=end_date
            ).select_related('category', 'department').order_by('-transaction_date')
            
            # Calculate statistics
            total_amount = transactions.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            transaction_count = transactions.count()
            avg_amount = total_amount / transaction_count if transaction_count > 0 else Decimal('0.00')
            
            # Group by category
            category_breakdown = transactions.values('category__name').annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            )
            
            return {
                'transactions': list(transactions.values(
                    'id', 'receiver', 'amount', 'category__name', 
                    'transaction_date', 'description', 'status'
                )),
                'statistics': {
                    'total_amount': total_amount,
                    'transaction_count': transaction_count,
                    'avg_amount': avg_amount
                },
                'category_breakdown': list(category_breakdown),
                'date_range': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        
        except Exception as e:
            self.log_error("Error getting payment history", e)
            return {
                'transactions': [],
                'statistics': {
                    'total_amount': Decimal('0.00'),
                    'transaction_count': 0,
                    'avg_amount': Decimal('0.00')
                },
                'category_breakdown': [],
                'date_range': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
    
    def validate_payment_method(self, payment_method: str, amount: Decimal) -> Dict[str, Any]:
        """Validate payment method for given amount."""
        try:
            # Payment method limits (simplified)
            limits = {
                'cash': Decimal('10000.00'),
                'mpesa': Decimal('5000.00'),
                'bank_transfer': Decimal('50000.00'),
                'credit_card': Decimal('20000.00')
            }
            
            method_limit = limits.get(payment_method.lower(), Decimal('0.00'))
            
            if amount > method_limit:
                return {
                    'valid': False,
                    'error': f'Amount exceeds {payment_method} limit of ${method_limit}',
                    'limit': method_limit
                }
            
            return {
                'valid': True,
                'limit': method_limit
            }
        
        except Exception as e:
            self.log_error("Error validating payment method", e)
            return {
                'valid': False,
                'error': 'Error validating payment method'
            }
    
    def calculate_payment_fees(self, amount: Decimal, payment_method: str) -> Dict[str, Any]:
        """Calculate payment fees for given amount and method."""
        try:
            # Fee structure (simplified)
            fee_rates = {
                'cash': Decimal('0.00'),
                'mpesa': Decimal('0.02'),  # 2%
                'bank_transfer': Decimal('0.01'),  # 1%
                'credit_card': Decimal('0.03')  # 3%
            }
            
            fee_rate = fee_rates.get(payment_method.lower(), Decimal('0.02'))
            fee_amount = amount * fee_rate
            
            return {
                'fee_rate': fee_rate,
                'fee_amount': fee_amount,
                'total_amount': amount + fee_amount,
                'payment_method': payment_method
            }
        
        except Exception as e:
            self.log_error("Error calculating payment fees", e)
            return {
                'fee_rate': Decimal('0.00'),
                'fee_amount': Decimal('0.00'),
                'total_amount': amount,
                'payment_method': payment_method
            }



