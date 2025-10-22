"""
Loan Service

Handles all loan-related business logic including:
- Loan applications
- Loan approvals/rejections
- Guarantor management
- Loan analytics

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

from ..models import LoanApplication, LoanProduct, Payment_History
from .base_service import BaseFinanceService
from mail.custom_email import send_email

logger = logging.getLogger(__name__)
User = get_user_model()


class LoanService(BaseFinanceService):
    """
    Service for managing loan operations.
    
    Handles loan applications, approvals, rejections, and guarantor management.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logger
    
    def create_loan_application(
        self, 
        user: User, 
        loan_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new loan application.
        
        Args:
            user: The user applying for the loan
            loan_data: Dictionary containing loan application details
            
        Returns:
            Dict with success status and loan application data
        """
        try:
            self._validate_user(user)
            
            # Validate required fields
            required_fields = ['loan_amount', 'loan_product_id', 'purpose']
            for field in required_fields:
                if field not in loan_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Validate loan amount
            loan_amount = self._validate_amount(loan_data['loan_amount'])
            
            # Get loan product
            try:
                loan_product = LoanProduct.objects.get(id=loan_data['loan_product_id'])
            except ObjectDoesNotExist:
                raise ValidationError("Invalid loan product")
            
            # Check if user already has pending application
            existing_app = LoanApplication.objects.filter(
                borrower=user,
                status__in=['pending', 'under_review']
            ).first()
            
            if existing_app:
                raise ValidationError("You already have a pending loan application")
            
            with transaction.atomic():
                # Create loan application
                loan_application = LoanApplication.objects.create(
                    borrower=user,
                    loan_product=loan_product,
                    loan_plan_id=loan_product.id,  # Set loan_plan_id to match loan_product
                    amount_requested=Decimal(str(loan_amount)),
                    purpose=loan_data['purpose'],
                    employment_status=loan_data.get('employment_status', ''),
                    monthly_income=Decimal(str(loan_data.get('monthly_income', 0))),
                    duration=loan_data.get('duration', loan_product.term_months),
                    interest_rate=loan_product.interest_rate,
                    status='pending',
                    submitted_at=timezone.now()
                )
                
                # Log the operation
                self._log_operation(
                    'create_loan_application',
                    user,
                    {'loan_id': loan_application.id, 'amount': loan_amount}
                )
                
                # Send notification email
                self._send_application_notification(loan_application)
                
                return self.create_success_response(
                    {'loan_application_id': loan_application.id},
                    "Loan application submitted successfully"
                )
                
        except Exception as e:
            self._handle_error(e, 'create_loan_application', user)
    
    def approve_loan_application(
        self, 
        loan_id: int, 
        approver: User,
        approval_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Approve a loan application.
        
        Args:
            loan_id: ID of the loan application
            approver: User approving the loan
            approval_data: Additional approval details
            
        Returns:
            Dict with success status and approval details
        """
        try:
            self._validate_user(approver)
            
            # Get loan application
            try:
                loan_app = LoanApplication.objects.get(id=loan_id)
            except ObjectDoesNotExist:
                raise ValidationError("Loan application not found")
            
            # Check if already processed
            if loan_app.status != 'pending':
                raise ValidationError("Loan application has already been processed")
            
            with transaction.atomic():
                # Update loan application status
                loan_app.status = 'approved'
                loan_app.approved_by = approver
                loan_app.approved_at = timezone.now()
                loan_app.save()
                
                # Log the operation
                self._log_operation(
                    'approve_loan_application',
                    approver,
                    {'loan_id': loan_id, 'applicant_id': loan_app.user.id}
                )
                
                # Send approval notification
                self._send_approval_notification(loan_app)
                
                return self.create_success_response(
                    {'loan_id': loan_id, 'status': 'approved'},
                    "Loan application approved successfully"
                )
                
        except Exception as e:
            self._handle_error(e, 'approve_loan_application', approver)
    
    def reject_loan_application(
        self, 
        loan_id: int, 
        rejector: User,
        rejection_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reject a loan application.
        
        Args:
            loan_id: ID of the loan application
            rejector: User rejecting the loan
            rejection_data: Rejection details including reason
            
        Returns:
            Dict with success status and rejection details
        """
        try:
            self._validate_user(rejector)
            
            if 'reason' not in rejection_data:
                raise ValidationError("Rejection reason is required")
            
            # Get loan application
            try:
                loan_app = LoanApplication.objects.get(id=loan_id)
            except ObjectDoesNotExist:
                raise ValidationError("Loan application not found")
            
            # Check if already processed
            if loan_app.status != 'pending':
                raise ValidationError("Loan application has already been processed")
            
            with transaction.atomic():
                # Update loan application status
                loan_app.status = 'rejected'
                loan_app.save()
                
                # Log the operation
                self._log_operation(
                    'reject_loan_application',
                    rejector,
                    {'loan_id': loan_id, 'reason': rejection_data['reason']}
                )
                
                # Send rejection notification
                self._send_rejection_notification(loan_app)
                
                return self.create_success_response(
                    {'loan_id': loan_id, 'status': 'rejected'},
                    "Loan application rejected"
                )
                
        except Exception as e:
            self._handle_error(e, 'reject_loan_application', rejector)
    
    def get_user_loan_applications(
        self, 
        user: User,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get loan applications for a user.
        
        Args:
            user: The user whose applications to retrieve
            status_filter: Optional status filter ('pending', 'approved', 'rejected')
            
        Returns:
            Dict with success status and list of applications
        """
        try:
            self._validate_user(user)
            
            queryset = LoanApplication.objects.filter(borrower=user)
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            applications = []
            for app in queryset.order_by('-submitted_at'):
                applications.append({
                    'id': app.id,
                    'loan_amount': float(app.amount_requested),
                    'purpose': app.purpose,
                    'status': app.status,
                    'application_date': app.submitted_at,
                    'loan_product': app.loan_product.name if app.loan_product else None
                })
            
            return self.create_success_response(
                {'applications': applications},
                f"Retrieved {len(applications)} loan applications"
            )
            
        except Exception as e:
            self.logger.error(f"Error in get_user_loan_applications: {str(e)}")
            return self.create_error_response(
                f"Failed to retrieve loan applications: {str(e)}",
                {'user_id': user.id if user else None}
            )
    
    def get_user_loans(
        self, 
        user: User,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get loans for a user (alias for get_user_loan_applications for compatibility).
        
        Args:
            user: The user whose loans to retrieve
            status: Optional status filter ('pending', 'approved', 'rejected', etc.)
            
        Returns:
            Dict with success status and QuerySet of loans
        """
        try:
            from finance.models import LoanApplication
            
            # Get actual queryset instead of dict
            queryset = LoanApplication.objects.filter(borrower=user)
            
            if status:
                queryset = queryset.filter(status=status)
            
            return {
                'status': 'success',
                'message': f'Retrieved {queryset.count()} loans',
                'loans': queryset.order_by('-submitted_at')
            }
            
        except Exception as e:
            self.logger.error(f"Error in get_user_loans: {str(e)}")
            from finance.models import LoanApplication
            return {
                'status': 'error',
                'message': f'Failed to retrieve loans: {str(e)}',
                'loans': LoanApplication.objects.none()
            }
    
    def _send_application_notification(self, loan_application: LoanApplication):
        """Send notification email for loan application submission."""
        try:
            subject = "Loan Application Submitted"
            message = f"""
            Your loan application for ${loan_application.amount_requested} has been submitted successfully.
            
            Application ID: {loan_application.id}
            Purpose: {loan_application.purpose}
            Status: {loan_application.status}
            
            We will review your application and notify you of the decision.
            """
            
            send_email(
                subject=subject,
                message=message,
                recipient_list=[loan_application.borrower.email]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send application notification: {str(e)}")
    
    def _send_approval_notification(self, loan_application: LoanApplication):
        """Send notification email for loan approval."""
        try:
            subject = "Loan Application Approved"
            message = f"""
            Congratulations! Your loan application has been approved.
            
            Application ID: {loan_application.id}
            Loan Amount: ${loan_application.amount_requested}
            Purpose: {loan_application.purpose}
            
            Please contact us to proceed with the loan disbursement.
            """
            
            send_email(
                subject=subject,
                message=message,
                recipient_list=[loan_application.borrower.email]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send approval notification: {str(e)}")
    
    def get_loan_statistics(self):
        """
        Get loan statistics for admin dashboard.
        Returns statistics about all loans in the system.
        """
        from django.db.models import Count, Sum, Avg, Q
        from finance.models import LoanApplication
        
        try:
            total_loans = LoanApplication.objects.count()
            
            statistics = {
                'total_applications': total_loans,
                'pending_applications': LoanApplication.objects.filter(
                    status__in=['draft', 'submitted', 'pending_guarantor', 'under_review']
                ).count(),
                'approved_loans': LoanApplication.objects.filter(status='approved').count(),
                'active_loans': LoanApplication.objects.filter(status='active').count(),
                'rejected_loans': LoanApplication.objects.filter(status='rejected').count(),
                'repaid_loans': LoanApplication.objects.filter(status='repaid').count(),
                'overdue_loans': LoanApplication.objects.filter(status='overdue').count(),
                'total_amount_requested': LoanApplication.objects.aggregate(
                    total=Sum('amount_requested')
                )['total'] or 0,
                'total_amount_approved': LoanApplication.objects.filter(
                    status__in=['approved', 'active', 'repaid']
                ).aggregate(total=Sum('amount_requested'))['total'] or 0,
                'average_loan_amount': LoanApplication.objects.aggregate(
                    avg=Avg('amount_requested')
                )['avg'] or 0,
            }
            
            return {
                'success': True,
                'statistics': statistics
            }
            
        except Exception as e:
            self.logger.error(f"Error getting loan statistics: {str(e)}")
            return {
                'success': False,
                'statistics': {},
                'error': str(e)
            }
    
    def _send_rejection_notification(self, loan_application: LoanApplication):
        """Send notification email for loan rejection."""
        try:
            subject = "Loan Application Decision"
            message = f"""
            Thank you for your loan application. After careful review, we regret to inform you that your application has not been approved at this time.
            
            Application ID: {loan_application.id}
            Loan Amount: ${loan_application.amount_requested}
            Status: {loan_application.status}
            
            You may reapply in the future when your circumstances change.
            """
            
            send_email(
                subject=subject,
                message=message,
                recipient_list=[loan_application.borrower.email]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send rejection notification: {str(e)}")