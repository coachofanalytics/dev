"""
Application Approval Service
Handles auto-approval and manual review of managed trading applications
"""

import logging
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings

from ..models import (
    ManagedTradingApplication,
    ManagedTradingAccount,
    ManagedTradingContract
)
from .managed_trading_service import ManagedTradingService

logger = logging.getLogger(__name__)


class ApplicationReviewService:
    """
    Service for reviewing and approving/rejecting applications
    Includes auto-approval logic
    """
    
    def check_auto_approval(self, application):
        """
        Check if application qualifies for automatic approval
        
        Returns: (bool, str) - (should_auto_approve, reason)
        """
        # Check 1: All contracts signed
        if not application.all_contracts_signed:
            return False, "Contracts not all signed"
        
        # Check 2: Risk/tier match
        if not application.risk_tier_match:
            return False, f"Risk profile ({application.risk_profile.risk_category}) doesn't match selected tier ({application.fee_tier})"
        
        # Check 3: Capital meets minimum
        if not application.capital_tier_match:
            tier_minimums = {
                'starter': Decimal('5000.00'),
                'professional': Decimal('15000.00'),
                'premium': Decimal('25000.00'),
                'consultative': Decimal('50000.00'),
                'co_invest': Decimal('100000.00'),
            }
            minimum = tier_minimums.get(application.fee_tier, Decimal('5000.00'))
            return False, f"Capital ${application.initial_capital:,.2f} below tier minimum ${minimum:,.2f}"
        
        # Check 4: Application status is pending
        if application.status != 'pending':
            return False, f"Application status is {application.status}, not pending"
        
        # Check 5: Risk assessment not expired
        if application.risk_profile.is_expired:
            return False, "Risk assessment has expired - reassessment required"
        
        # All checks passed - auto-approve!
        return True, "Meets all auto-approval criteria"
    
    def approve_application(self, application, approved_by=None, auto_approved=False):
        """
        Approve an application and create managed trading account
        
        Args:
            application: ManagedTradingApplication instance
            approved_by: User who approved (None for auto-approval)
            auto_approved: Boolean indicating if auto-approved
        
        Returns:
            dict with 'status', 'account', and 'message'
        """
        try:
            with transaction.atomic():
                # Create managed trading account
                trading_service = ManagedTradingService()
                account = trading_service.create_managed_account(
                    client=application.user,
                    initial_capital=application.initial_capital,
                    fee_tier=application.fee_tier,
                    account_manager=application.preferred_manager or approved_by
                )
                
                # Update application
                application.status = 'approved'
                application.reviewed_by = approved_by
                application.reviewed_date = timezone.now()
                application.managed_account = account
                
                if auto_approved:
                    application.approval_notes = "Auto-approved - met all criteria"
                
                application.save()
                
                # Link contracts to account
                application.contracts.update(managed_account=account)
                
                # Send welcome email
                self.send_welcome_email(application, account, auto_approved)
                
                logger.info(
                    f"Application approved for {application.user.get_full_name()}. "
                    f"Account: {account.account_number}. "
                    f"Auto-approved: {auto_approved}"
                )
                
                return {
                    'status': 'success',
                    'account': account,
                    'message': f"Account {account.account_number} created successfully!"
                }
                
        except Exception as e:
            logger.error(f"Error approving application {application.id}: {str(e)}")
            return {
                'status': 'error',
                'account': None,
                'message': f"Error creating account: {str(e)}"
            }
    
    def reject_application(self, application, rejected_by, reason):
        """
        Reject an application
        
        Args:
            application: ManagedTradingApplication instance
            rejected_by: User who rejected
            reason: Rejection reason (shown to client)
        
        Returns:
            dict with 'status' and 'message'
        """
        try:
            application.status = 'rejected'
            application.reviewed_by = rejected_by
            application.reviewed_date = timezone.now()
            application.rejection_reason = reason
            application.save()
            
            # Send rejection email
            self.send_rejection_email(application, reason)
            
            logger.info(
                f"Application rejected for {application.user.get_full_name()}. "
                f"Reason: {reason}"
            )
            
            return {
                'status': 'success',
                'message': "Application rejected successfully"
            }
            
        except Exception as e:
            logger.error(f"Error rejecting application {application.id}: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error rejecting application: {str(e)}"
            }
    
    def get_pending_applications(self):
        """Get all pending applications ordered by date"""
        return ManagedTradingApplication.objects.filter(
            status='pending'
        ).select_related(
            'user', 'risk_profile', 'preferred_manager'
        ).order_by('-applied_date')
    
    def get_auto_approval_candidates(self):
        """Get applications that qualify for auto-approval"""
        pending = self.get_pending_applications()
        candidates = []
        
        for app in pending:
            should_approve, reason = self.check_auto_approval(app)
            if should_approve:
                candidates.append(app)
        
        return candidates
    
    def process_auto_approvals(self):
        """
        Process all auto-approval candidates
        Should be called periodically (e.g., every hour via cron)
        
        Returns:
            dict with counts of processed, approved, and failed
        """
        candidates = self.get_auto_approval_candidates()
        
        processed = 0
        approved = 0
        failed = 0
        
        for application in candidates:
            result = self.approve_application(
                application,
                approved_by=None,  # No user for auto-approval
                auto_approved=True
            )
            
            processed += 1
            if result['status'] == 'success':
                approved += 1
            else:
                failed += 1
        
        logger.info(
            f"Auto-approval batch: {processed} processed, "
            f"{approved} approved, {failed} failed"
        )
        
        return {
            'processed': processed,
            'approved': approved,
            'failed': failed
        }
    
    def send_welcome_email(self, application, account, auto_approved=False):
        """Send welcome email to approved client"""
        subject = "Welcome to CODA Managed Options Trading!"
        
        approval_type = "automatically approved" if auto_approved else "approved"
        
        message = f"""
Dear {application.user.get_full_name()},

Congratulations! Your managed trading application has been {approval_type}.

Account Details:
- Account Number: {account.account_number}
- Fee Tier: {account.get_fee_tier_display()}
- Initial Capital: ${application.initial_capital:,.2f}
- Account Manager: {account.account_manager.get_full_name() if account.account_manager else 'To be assigned'}

Next Steps:
1. Fund your account using {application.get_funding_method_display()}
2. Review your account dashboard: {settings.SITE_URL}/investing/managed/portal/
3. Your account manager will be in touch shortly

Your account is now active and ready for trading!

Best regards,
CODA Investment Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [application.user.email],
                fail_silently=True
            )
            logger.info(f"Welcome email sent to {application.user.email}")
        except Exception as e:
            logger.error(f"Error sending welcome email: {str(e)}")
    
    def send_rejection_email(self, application, reason):
        """Send rejection email to client"""
        subject = "Managed Trading Application - Update Required"
        
        message = f"""
Dear {application.user.get_full_name()},

Thank you for your interest in CODA Managed Options Trading.

After reviewing your application, we need to inform you that we cannot approve it at this time.

Reason: {reason}

What You Can Do:
- Update your risk assessment if it has expired
- Select a different fee tier that matches your risk profile
- Increase your initial capital if it doesn't meet the tier minimum
- Contact us if you have questions: {settings.SUPPORT_EMAIL}

You're welcome to resubmit your application once you've addressed these issues.

Best regards,
CODA Investment Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [application.user.email],
                fail_silently=True
            )
            logger.info(f"Rejection email sent to {application.user.email}")
        except Exception as e:
            logger.error(f"Error sending rejection email: {str(e)}")
    
    def get_application_summary(self, application):
        """
        Get summary data for an application
        Useful for display in review queue
        """
        auto_approve, reason = self.check_auto_approval(application)
        
        return {
            'application': application,
            'risk_category': application.risk_profile.risk_category,
            'risk_score': application.risk_profile.risk_score,
            'risk_tier_match': application.risk_tier_match,
            'capital_tier_match': application.capital_tier_match,
            'contracts_signed': application.all_contracts_signed,
            'auto_approval_eligible': auto_approve,
            'auto_approval_reason': reason,
            'days_pending': (timezone.now() - application.applied_date).days,
        }

