"""
Payment Service

Handles all payment-related business logic including:
- Payment processing
- Payment validation
- Payment history management
- Payment notifications

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

from ..models import Payment_Information, Payment_History, Transaction
from .base_service import BaseFinanceService
from mail.custom_email import send_email

logger = logging.getLogger(__name__)
User = get_user_model()


class PaymentService(BaseFinanceService):
    """
    Service for managing payment operations.
    
    Handles payment processing, validation, history management, and notifications.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logger
    
    def process_payment(
        self, 
        user: User, 
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a new payment.
        
        Args:
            user: The user making the payment
            payment_data: Dictionary containing payment details
            
        Returns:
            Dict with success status and payment data
        """
        try:
            self._validate_user(user)
            
            # Validate required fields
            required_fields = ['amount', 'payment_method', 'description']
            for field in required_fields:
                if field not in payment_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Validate payment amount
            amount = self._validate_amount(payment_data['amount'])
            
            # Validate payment method
            valid_methods = ['cash', 'bank_transfer', 'mobile_money', 'credit_card', 'check']
            if payment_data['payment_method'] not in valid_methods:
                raise ValidationError(f"Invalid payment method: {payment_data['payment_method']}")
            
            with transaction.atomic():
                # Create payment information
                payment_info = Payment_Information.objects.create(
                    customer_id=user,
                    payment_fees=int(amount),
                    payment_method=payment_data['payment_method'],
                    description=payment_data['description'],
                    plan=payment_data.get('plan', 1),
                    is_active=True
                )
                
                # Create payment history entry
                payment_history = Payment_History.objects.create(
                    customer=user,
                    payment_fees=int(amount),
                    plan=payment_data.get('plan', 1),
                    down_payment=payment_data.get('down_payment', 500)
                )
                
                # Log the operation
                self._log_operation(
                    'process_payment',
                    user,
                    {'payment_id': payment_info.id, 'amount': amount}
                )
                
                # Send payment notification
                self._send_payment_notification(payment_info)
                
                return self.create_success_response(
                    {'payment_id': payment_info.id, 'status': 'pending'},
                    "Payment processed successfully"
                )
                
        except Exception as e:
            self._handle_error(e, 'process_payment', user)
    
    def approve_payment(
        self, 
        payment_id: int, 
        approver: User,
        approval_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Approve a payment.
        
        Args:
            payment_id: ID of the payment
            approver: User approving the payment
            approval_data: Additional approval details
            
        Returns:
            Dict with success status and approval details
        """
        try:
            self._validate_user(approver)
            
            # Get payment information
            try:
                payment_info = Payment_Information.objects.get(id=payment_id)
            except ObjectDoesNotExist:
                raise ValidationError("Payment not found")
            
            # Check if already processed
            if payment_info.status != 'pending':
                raise ValidationError("Payment has already been processed")
            
            with transaction.atomic():
                # Update payment status
                payment_info.status = 'approved'
                payment_info.approved_by = approver
                payment_info.approved_at = timezone.now()
                payment_info.save()
                
                # Update payment history
                payment_history = Payment_History.objects.filter(payment_info=payment_info).first()
                if payment_history:
                    payment_history.status = 'approved'
                    payment_history.approved_at = timezone.now()
                    payment_history.save()
                
                # Log the operation
                self._log_operation(
                    'approve_payment',
                    approver,
                    {'payment_id': payment_id, 'amount': float(payment_info.payment_fees)}
                )
                
                # Send approval notification
                self._send_approval_notification(payment_info)
                
                return self.create_success_response(
                    {'payment_id': payment_id, 'status': 'approved'},
                    "Payment approved successfully"
                )
                
        except Exception as e:
            self._handle_error(e, 'approve_payment', approver)
    
    def reject_payment(
        self, 
        payment_id: int, 
        rejector: User,
        rejection_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reject a payment.
        
        Args:
            payment_id: ID of the payment
            rejector: User rejecting the payment
            rejection_data: Rejection details including reason
            
        Returns:
            Dict with success status and rejection details
        """
        try:
            self._validate_user(rejector)
            
            if 'reason' not in rejection_data:
                raise ValidationError("Rejection reason is required")
            
            # Get payment information
            try:
                payment_info = Payment_Information.objects.get(id=payment_id)
            except ObjectDoesNotExist:
                raise ValidationError("Payment not found")
            
            # Check if already processed
            if payment_info.status != 'pending':
                raise ValidationError("Payment has already been processed")
            
            with transaction.atomic():
                # Update payment status
                payment_info.status = 'rejected'
                payment_info.rejected_by = rejector
                payment_info.rejected_at = timezone.now()
                payment_info.save()
                
                # Update payment history
                payment_history = Payment_History.objects.filter(payment_info=payment_info).first()
                if payment_history:
                    payment_history.status = 'rejected'
                    payment_history.rejected_at = timezone.now()
                    payment_history.save()
                
                # Log the operation
                self._log_operation(
                    'reject_payment',
                    rejector,
                    {'payment_id': payment_id, 'reason': rejection_data['reason']}
                )
                
                # Send rejection notification
                self._send_rejection_notification(payment_info, rejection_data['reason'])
                
                return self.create_success_response(
                    {'payment_id': payment_id, 'status': 'rejected'},
                    "Payment rejected"
                )
                
        except Exception as e:
            self._handle_error(e, 'reject_payment', rejector)
    
    def get_user_payments(
        self, 
        user: User,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get payments for a user.
        
        Args:
            user: The user whose payments to retrieve
            status_filter: Optional status filter ('pending', 'approved', 'rejected')
            limit: Optional limit on number of results
            
        Returns:
            Dict with success status and list of payments
        """
        try:
            self._validate_user(user)
            
            queryset = Payment_Information.objects.filter(customer_id=user)
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            if limit:
                queryset = queryset[:limit]
            
            payments = []
            for payment in queryset.order_by('-contract_submitted_date'):
                payments.append({
                    'id': payment.id,
                    'amount': float(payment.payment_fees),
                    'payment_method': payment.payment_method,
                    'description': payment.description,
                    'status': 'active' if payment.is_active else 'inactive',
                    'created_at': payment.contract_submitted_date,
                    'approved_at': None  # This field doesn't exist in the model
                })
            
            return self.create_success_response(
                {'payments': payments},
                f"Retrieved {len(payments)} payments"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_user_payments', user)
    
    def get_payment_statistics(
        self, 
        user: Optional[User] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get payment statistics.
        
        Args:
            user: Optional user filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            
        Returns:
            Dict with success status and statistics
        """
        try:
            queryset = Payment_Information.objects.all()
            
            if user:
                queryset = queryset.filter(user=user)
            
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)
            
            # Calculate statistics
            total_payments = queryset.count()
            total_amount = sum(float(p.payment_fees) for p in queryset)
            active_payments = queryset.filter(is_active=True).count()
            inactive_payments = queryset.filter(is_active=False).count()
            
            # Calculate activity rate
            activity_rate = (active_payments / total_payments * 100) if total_payments > 0 else 0
            
            statistics = {
                'total_payments': total_payments,
                'total_amount': total_amount,
                'active_payments': active_payments,
                'inactive_payments': inactive_payments,
                'activity_rate': round(activity_rate, 2)
            }
            
            return self.create_success_response(
                {'statistics': statistics},
                "Payment statistics retrieved successfully"
            )
            
        except Exception as e:
            self._handle_error(e, 'get_payment_statistics')
    
    def _send_payment_notification(self, payment_info: Payment_Information):
        """Send notification email for payment submission."""
        try:
            subject = "Payment Submitted"
            message = f"""
            Your payment of ${payment_info.payment_fees} has been submitted successfully.
            
            Payment ID: {payment_info.id}
            Method: {payment_info.payment_method}
            Description: {payment_info.description}
            Status: {'Active' if payment_info.is_active else 'Inactive'}
            
            We will process your payment and notify you of the status.
            """
            
            send_email(
                subject=subject,
                message=message,
                recipient_list=[payment_info.customer_id.email]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send payment notification: {str(e)}")
    
    def _send_approval_notification(self, payment_info: Payment_Information):
        """Send notification email for payment approval."""
        try:
            subject = "Payment Approved"
            message = f"""
            Your payment has been approved.
            
            Payment ID: {payment_info.id}
            Amount: ${payment_info.payment_fees}
            Method: {payment_info.payment_method}
            Description: {payment_info.description}
            
            Your payment has been processed successfully.
            """
            
            send_email(
                subject=subject,
                message=message,
                recipient_list=[payment_info.customer_id.email]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send approval notification: {str(e)}")
    
    def _send_rejection_notification(self, payment_info: Payment_Information, reason: str):
        """Send notification email for payment rejection."""
        try:
            subject = "Payment Decision"
            message = f"""
            Your payment has been processed.
            
            Payment ID: {payment_info.id}
            Amount: ${payment_info.payment_fees}
            Method: {payment_info.payment_method}
            Status: {'Active' if payment_info.is_active else 'Inactive'}
            Reason: {reason}
            
            Please contact us if you have any questions.
            """
            
            send_email(
                subject=subject,
                message=message,
                recipient_list=[payment_info.customer_id.email]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send rejection notification: {str(e)}")