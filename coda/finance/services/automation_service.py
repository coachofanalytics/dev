"""
Automation Service for CODA Finance System

This service handles the core automation functionality including:
- Budget request management
- Policy-based approval processing
- Automated disbursement processing
- Comprehensive audit logging
"""

import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Q

from ..models import BudgetRequest, ApprovalPolicy, DisbursementRequest, AutomationAuditLog
from .base_service import BaseFinanceService
from .mpesa_service import MPESAService
from .email_service import EmailService
from .otp_service import OTPService

logger = logging.getLogger(__name__)
User = get_user_model()


class BudgetRequestService(BaseFinanceService):
    """Service for budget request management"""
    
    def __init__(self):
        super().__init__()
        self.model = BudgetRequest
        self.audit_service = AutomationAuditService()
    
    def get_object(self, request_id):
        """Get budget request object by ID"""
        try:
            return BudgetRequest.objects.get(id=request_id)
        except BudgetRequest.DoesNotExist:
            raise ValidationError(f"Budget request with ID {request_id} not found")
    
    def create_request(self, user, data, request=None):
        """Create a new budget request"""
        try:
            with transaction.atomic():
                # Validate required fields
                required_fields = ['amount', 'purpose', 'department', 'required_date', 'budget_category']
                for field in required_fields:
                    if field not in data:
                        raise ValidationError(f"Field '{field}' is required")
                
                # Create budget request
                budget_request = BudgetRequest.objects.create(
                    requester=user,
                    amount=Decimal(str(data['amount'])),
                    purpose=data['purpose'],
                    department_id=data['department'],
                    required_date=data['required_date'],
                    budget_category_id=data['budget_category'],
                    priority=data.get('priority', 'medium'),
                    cost_center=data.get('cost_center', ''),
                    attachments=data.get('attachments', []),
                    created_by=user,
                    last_modified_by=user,
                    status='draft'
                )
                
                # Log creation
                self.audit_service.log_action(
                    action='create_budget_request',
                    action_type='create',
                    user=user,
                    object=budget_request,
                    details={
                        'amount': str(budget_request.amount),
                        'purpose': budget_request.purpose,
                        'department': budget_request.department.name if budget_request.department else None
                    },
                    request=request
                )
                
                logger.info(f"Budget request created: {budget_request.id} by {user.username}")
                return budget_request
                
        except Exception as e:
            logger.error(f"Error creating budget request: {str(e)}")
            raise
    
    def submit_for_approval(self, request_id, user, request=None):
        """Submit budget request for approval"""
        try:
            with transaction.atomic():
                budget_request = self.get_object(request_id)
                
                if budget_request.status != 'draft':
                    raise ValidationError("Only draft requests can be submitted for approval")
                
                # Get applicable approval policy
                policy_service = ApprovalEngineService()
                policy = policy_service.get_applicable_policy(budget_request)
                
                if policy:
                    budget_request.approval_policy = policy
                    budget_request.status = 'submitted'
                    
                    # Set up approval chain
                    approval_chain = policy_service.get_approval_chain(budget_request, policy)
                    budget_request.approval_chain = approval_chain
                    
                    if approval_chain:
                        budget_request.current_approver_id = approval_chain[0]['user_id']
                        budget_request.status = 'under_review'
                    
                    budget_request.last_modified_by = user
                    budget_request.save()
                    
                    # Log submission
                    self.audit_service.log_action(
                        action='submit_budget_request',
                        action_type='update',
                        user=user,
                        object=budget_request,
                        details={
                            'policy': policy.name,
                            'approval_chain': approval_chain
                        },
                        request=request
                    )
                    
                    # Send notifications
                    self._send_submission_notifications(budget_request)
                    
                    logger.info(f"Budget request submitted: {budget_request.id}")
                    return budget_request
                else:
                    raise ValidationError("No applicable approval policy found")
                    
        except Exception as e:
            logger.error(f"Error submitting budget request: {str(e)}")
            raise
    
    def update_status(self, request_id, status, user, reason=None, request=None):
        """Update budget request status"""
        try:
            with transaction.atomic():
                budget_request = self.get_object(request_id)
                old_status = budget_request.status
                
                budget_request.status = status
                budget_request.last_modified_by = user
                
                if reason:
                    budget_request.rejection_reason = reason
                
                budget_request.save()
                
                # Log status change
                self.audit_service.log_action(
                    action='update_budget_request_status',
                    action_type='update',
                    user=user,
                    object=budget_request,
                    details={
                        'old_status': old_status,
                        'new_status': status,
                        'reason': reason
                    },
                    request=request
                )
                
                logger.info(f"Budget request status updated: {budget_request.id} from {old_status} to {status}")
                return budget_request
                
        except Exception as e:
            logger.error(f"Error updating budget request status: {str(e)}")
            raise
    
    def get_approval_chain(self, request):
        """Get approval chain for request"""
        if request.approval_chain:
            return request.approval_chain
        
        policy_service = ApprovalEngineService()
        policy = policy_service.get_applicable_policy(request)
        
        if policy:
            return policy_service.get_approval_chain(request, policy)
        
        return []
    
    def _send_submission_notifications(self, budget_request):
        """Send notifications for budget request submission"""
        try:
            email_service = EmailService()
            
            # Notify requester
            email_service.send_approval_notification(
                user=budget_request.requester,
                request=budget_request,
                notification_type='submission'
            )
            
            # Notify current approver
            if budget_request.current_approver:
                email_service.send_approval_notification(
                    user=budget_request.current_approver,
                    request=budget_request,
                    notification_type='approval_required'
                )
                
        except Exception as e:
            logger.error(f"Error sending submission notifications: {str(e)}")


class ApprovalEngineService(BaseFinanceService):
    """Service for policy-based approval processing"""
    
    def __init__(self):
        super().__init__()
        self.model = ApprovalPolicy
        self.audit_service = AutomationAuditService()
    
    def get_object(self, request_id):
        """Get budget request object by ID"""
        try:
            return BudgetRequest.objects.get(id=request_id)
        except BudgetRequest.DoesNotExist:
            raise ValidationError(f"Budget request with ID {request_id} not found")
    
    def get_applicable_policy(self, request):
        """Get applicable approval policy for a request"""
        try:
            policies = ApprovalPolicy.objects.filter(
                is_active=True,
                min_amount__lte=request.amount
            ).filter(
                Q(max_amount__isnull=True) | Q(max_amount__gte=request.amount)
            ).order_by('min_amount')
            
            for policy in policies:
                if policy.is_applicable(request):
                    return policy
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting applicable policy: {str(e)}")
            return None
    
    def get_approval_chain(self, request, policy):
        """Get approval chain for a request based on policy"""
        try:
            approval_chain = []
            
            if policy.auto_approve:
                return approval_chain
            
            # Get approvers based on policy configuration
            approvers = self._get_approvers_for_policy(request, policy)
            
            for approver in approvers:
                approval_chain.append({
                    'user_id': approver.id,
                    'user_name': approver.username,
                    'role': self._get_user_role(approver),
                    'status': 'pending',
                    'assigned_at': timezone.now().isoformat()
                })
            
            return approval_chain
            
        except Exception as e:
            logger.error(f"Error getting approval chain: {str(e)}")
            return []
    
    def process_approval(self, request_id, approver, decision, comments=None, request=None):
        """Process approval decision"""
        try:
            with transaction.atomic():
                budget_request = self.get_object(request_id)
                
                if budget_request.current_approver != approver:
                    raise ValidationError("User is not the current approver")
                
                # Update approval chain
                approval_chain = budget_request.approval_chain
                current_approver_index = self._get_current_approver_index(approval_chain, approver)
                
                if current_approver_index is not None:
                    approval_chain[current_approver_index]['status'] = decision
                    approval_chain[current_approver_index]['comments'] = comments
                    approval_chain[current_approver_index]['decided_at'] = timezone.now().isoformat()
                
                budget_request.approval_chain = approval_chain
                
                if decision == 'approved':
                    # Move to next approver or complete approval
                    next_approver = self._get_next_approver(approval_chain)
                    
                    if next_approver:
                        budget_request.current_approver_id = next_approver['user_id']
                        budget_request.status = 'under_review'
                    else:
                        budget_request.current_approver = None
                        budget_request.status = 'approved'
                        
                        # Create disbursement request if auto-disburse is enabled
                        if budget_request.approval_policy and budget_request.approval_policy.auto_approve:
                            self._create_disbursement_request(budget_request)
                
                elif decision == 'rejected':
                    budget_request.current_approver = None
                    budget_request.status = 'rejected'
                
                budget_request.last_modified_by = approver
                budget_request.save()
                
                # Log approval decision
                self.audit_service.log_action(
                    action='process_approval',
                    action_type='approve' if decision == 'approved' else 'reject',
                    user=approver,
                    object=budget_request,
                    details={
                        'decision': decision,
                        'comments': comments,
                        'approval_chain': approval_chain
                    },
                    request=request
                )
                
                # Send notifications
                self._send_approval_notifications(budget_request, decision)
                
                logger.info(f"Approval processed: {budget_request.id} - {decision} by {approver.username}")
                return budget_request
                
        except Exception as e:
            logger.error(f"Error processing approval: {str(e)}")
            raise
    
    def escalate_request(self, request_id, user, request=None):
        """Escalate request if overdue"""
        try:
            with transaction.atomic():
                budget_request = self.get_object(request_id)
                
                if budget_request.status not in ['submitted', 'under_review']:
                    return budget_request
                
                # Check if escalation is needed
                if not self._is_escalation_needed(budget_request):
                    return budget_request
                
                # Escalate to next level
                escalation_result = self._escalate_to_next_level(budget_request)
                
                if escalation_result:
                    budget_request.last_modified_by = user
                    budget_request.save()
                    
                    # Log escalation
                    self.audit_service.log_action(
                        action='escalate_request',
                        action_type='escalate',
                        user=user,
                        object=budget_request,
                        details={'escalation_result': escalation_result},
                        request=request
                    )
                    
                    logger.info(f"Request escalated: {budget_request.id}")
                
                return budget_request
                
        except Exception as e:
            logger.error(f"Error escalating request: {str(e)}")
            raise
    
    def _get_approvers_for_policy(self, request, policy):
        """Get approvers for a policy"""
        # This is a simplified implementation
        # In a real system, you would have more complex logic
        # based on roles, departments, and hierarchy
        
        approvers = []
        
        # Get users with required roles
        if policy.approver_roles:
            approvers = User.objects.filter(
                groups__name__in=policy.approver_roles
            ).distinct()
        
        return approvers
    
    def _get_user_role(self, user):
        """Get user role for approval chain"""
        if user.is_staff:
            return 'Staff'
        elif hasattr(user, 'profile') and user.profile.is_karen_country_club_member:
            return 'KCC'
        else:
            return 'External'
    
    def _get_current_approver_index(self, approval_chain, approver):
        """Get index of current approver in approval chain"""
        for i, approver_info in enumerate(approval_chain):
            if approver_info['user_id'] == approver.id and approver_info['status'] == 'pending':
                return i
        return None
    
    def _get_next_approver(self, approval_chain):
        """Get next approver in the chain"""
        for approver_info in approval_chain:
            if approver_info['status'] == 'pending':
                return approver_info
        return None
    
    def _is_escalation_needed(self, budget_request):
        """Check if escalation is needed"""
        if not budget_request.approval_policy:
            return False
        
        escalation_days = budget_request.approval_policy.escalation_days
        days_since_submission = (timezone.now().date() - budget_request.request_date.date()).days
        
        return days_since_submission >= escalation_days
    
    def _escalate_to_next_level(self, budget_request):
        """Escalate request to next level"""
        # Implementation for escalation logic
        # This would depend on your organization's hierarchy
        return True
    
    def _create_disbursement_request(self, budget_request):
        """Create disbursement request for approved budget request"""
        try:
            disbursement_service = DisbursementService()
            disbursement_service.create_disbursement_request(budget_request)
        except Exception as e:
            logger.error(f"Error creating disbursement request: {str(e)}")
    
    def _send_approval_notifications(self, budget_request, decision):
        """Send notifications for approval decision"""
        try:
            email_service = EmailService()
            
            # Notify requester
            email_service.send_approval_notification(
                user=budget_request.requester,
                request=budget_request,
                notification_type='decision',
                decision=decision
            )
            
            # Notify next approver if applicable
            if budget_request.current_approver and decision == 'approved':
                email_service.send_approval_notification(
                    user=budget_request.current_approver,
                    request=budget_request,
                    notification_type='approval_required'
                )
                
        except Exception as e:
            logger.error(f"Error sending approval notifications: {str(e)}")


class DisbursementService(BaseFinanceService):
    """Service for automated disbursement processing"""
    
    def __init__(self):
        super().__init__()
        self.model = DisbursementRequest
        self.audit_service = AutomationAuditService()
        self.mpesa_service = MPESAService()
        self.email_service = EmailService()
        self.otp_service = OTPService()
    
    def create_disbursement_request(self, budget_request, disbursement_data=None):
        """Create disbursement request for approved budget request"""
        try:
            with transaction.atomic():
                # Create disbursement request
                disbursement_request = DisbursementRequest.objects.create(
                    budget_request=budget_request,
                    disbursement_method=disbursement_data.get('method', 'mpesa') if disbursement_data else 'mpesa',
                    recipient_name=disbursement_data.get('recipient_name', budget_request.requester.get_full_name()) if disbursement_data else budget_request.requester.get_full_name(),
                    recipient_phone=disbursement_data.get('recipient_phone', '') if disbursement_data else '',
                    recipient_email=disbursement_data.get('recipient_email', budget_request.requester.email) if disbursement_data else budget_request.requester.email,
                    bank_account=disbursement_data.get('bank_account', '') if disbursement_data else '',
                    amount=budget_request.amount,
                    currency=budget_request.currency
                )
                
                # Log creation
                self.audit_service.log_action(
                    action='create_disbursement_request',
                    action_type='create',
                    user=budget_request.requester,
                    object=disbursement_request,
                    details={
                        'amount': str(disbursement_request.amount),
                        'method': disbursement_request.disbursement_method,
                        'recipient': disbursement_request.recipient_name
                    }
                )
                
                logger.info(f"Disbursement request created: {disbursement_request.id}")
                return disbursement_request
                
        except Exception as e:
            logger.error(f"Error creating disbursement request: {str(e)}")
            raise
    
    def process_disbursement(self, disbursement_request_id, user, request=None):
        """Process disbursement request"""
        try:
            with transaction.atomic():
                disbursement_request = self.get_object(disbursement_request_id)
                
                if disbursement_request.status != 'pending':
                    raise ValidationError("Disbursement request is not in pending status")
                
                # Generate and send OTP
                disbursement_request.generate_otp()
                disbursement_request.status = 'otp_sent'
                disbursement_request.save()
                
                # Send OTP via email
                self.otp_service.send_otp_email(
                    user=disbursement_request.budget_request.requester,
                    otp_code=disbursement_request.otp_code,
                    disbursement_request=disbursement_request
                )
                
                # Log OTP generation
                self.audit_service.log_action(
                    action='generate_disbursement_otp',
                    action_type='otp_send',
                    user=user,
                    object=disbursement_request,
                    details={'otp_code': disbursement_request.otp_code},
                    request=request
                )
                
                logger.info(f"OTP generated for disbursement: {disbursement_request.id}")
                return disbursement_request
                
        except Exception as e:
            logger.error(f"Error processing disbursement: {str(e)}")
            raise
    
    def verify_otp(self, disbursement_request_id, otp_code, user, request=None):
        """Verify OTP and process disbursement"""
        try:
            with transaction.atomic():
                disbursement_request = self.get_object(disbursement_request_id)
                
                if disbursement_request.otp_code != otp_code:
                    raise ValidationError("Invalid OTP code")
                
                if disbursement_request.is_otp_expired():
                    raise ValidationError("OTP has expired")
                
                # Mark OTP as verified
                disbursement_request.otp_verified = True
                disbursement_request.status = 'otp_verified'
                disbursement_request.save()
                
                # Process actual disbursement
                self._process_payment(disbursement_request)
                
                # Log OTP verification
                self.audit_service.log_action(
                    action='verify_disbursement_otp',
                    action_type='otp_verify',
                    user=user,
                    object=disbursement_request,
                    details={'otp_code': otp_code},
                    request=request
                )
                
                logger.info(f"OTP verified for disbursement: {disbursement_request.id}")
                return disbursement_request
                
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            raise
    
    def _process_payment(self, disbursement_request):
        """Process actual payment based on disbursement method"""
        try:
            if disbursement_request.disbursement_method == 'mpesa':
                self._process_mpesa_payment(disbursement_request)
            elif disbursement_request.disbursement_method == 'bank_transfer':
                self._process_bank_transfer(disbursement_request)
            elif disbursement_request.disbursement_method == 'stanbic':
                self._process_stanbic_payment(disbursement_request)
            else:
                raise ValidationError(f"Unsupported disbursement method: {disbursement_request.disbursement_method}")
                
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            disbursement_request.status = 'failed'
            disbursement_request.save()
            raise
    
    def _process_mpesa_payment(self, disbursement_request):
        """Process MPESA payment"""
        try:
            # Use existing MPESA service
            result = self.mpesa_service.automated_disbursement(
                phone=disbursement_request.recipient_phone,
                amount=disbursement_request.amount,
                reference=f"CODA-{disbursement_request.id}"
            )
            
            if result.get('success'):
                disbursement_request.status = 'completed'
                disbursement_request.transaction_id = result.get('transaction_id')
                disbursement_request.payment_reference = result.get('reference')
                disbursement_request.disbursement_date = timezone.now()
                disbursement_request.completion_date = timezone.now()
            else:
                disbursement_request.status = 'failed'
            
            disbursement_request.save()
            
        except Exception as e:
            logger.error(f"Error processing MPESA payment: {str(e)}")
            disbursement_request.status = 'failed'
            disbursement_request.save()
            raise
    
    def _process_bank_transfer(self, disbursement_request):
        """Process bank transfer"""
        # Implementation for bank transfer
        disbursement_request.status = 'completed'
        disbursement_request.disbursement_date = timezone.now()
        disbursement_request.completion_date = timezone.now()
        disbursement_request.save()
    
    def _process_stanbic_payment(self, disbursement_request):
        """Process Stanbic payment"""
        # Implementation for Stanbic payment
        disbursement_request.status = 'completed'
        disbursement_request.disbursement_date = timezone.now()
        disbursement_request.completion_date = timezone.now()
        disbursement_request.save()


class AutomationAuditService(BaseFinanceService):
    """Service for comprehensive audit logging"""
    
    def __init__(self):
        super().__init__()
        self.model = AutomationAuditLog
    
    def log_action(self, action, action_type, user, object=None, details=None, old_values=None, new_values=None, success=True, error_message=None, request=None):
        """Log an action in the audit system"""
        try:
            # Get IP address and user agent
            ip_address = '127.0.0.1'
            user_agent = ''
            
            if request:
                ip_address = self._get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Get object information
            content_type = None
            object_id = None
            object_repr = ''
            
            if object:
                content_type = ContentType.objects.get_for_model(object)
                object_id = object.id
                object_repr = str(object)
            
            # Create audit log entry
            audit_log = AutomationAuditLog.objects.create(
                action=action,
                action_type=action_type,
                description=f"{action} by {user.username}",
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                content_type=content_type,
                object_id=object_id,
                object_repr=object_repr,
                details=details or {},
                old_values=old_values or {},
                new_values=new_values or {},
                success=success,
                error_message=error_message or ''
            )
            
            logger.info(f"Audit log created: {audit_log.id} - {action}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
            return None
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_audit_logs(self, object=None, user=None, action_type=None, start_date=None, end_date=None):
        """Get audit logs with filters"""
        try:
            queryset = AutomationAuditLog.objects.all()
            
            if object:
                content_type = ContentType.objects.get_for_model(object)
                queryset = queryset.filter(content_type=content_type, object_id=object.id)
            
            if user:
                queryset = queryset.filter(user=user)
            
            if action_type:
                queryset = queryset.filter(action_type=action_type)
            
            if start_date:
                queryset = queryset.filter(created_at__gte=start_date)
            
            if end_date:
                queryset = queryset.filter(created_at__lte=end_date)
            
            return queryset.order_by('-created_at')
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {str(e)}")
            return AutomationAuditLog.objects.none()
