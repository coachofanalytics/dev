"""
Notification Service
Handles email and SMS notifications for managed trading
"""

import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications to clients and staff
    Supports email and SMS
    """
    
    def send_batch_notification(self, batch):
        """
        Send email notification when new batch is created
        Client has 24 hours to approve
        """
        client = batch.managed_account.client
        
        subject = f"Position Batch Approval Required - {batch.batch_number}"
        
        message = f"""
Dear {client.first_name},

Your trading manager has prepared {batch.total_positions} options positions for your review.

Batch Details:
- Batch Number: {batch.batch_number}
- Total Positions: {batch.total_positions}
- Total Capital Required: ${batch.total_capital_required:,.2f}
- Approval Deadline: {batch.approval_deadline.strftime('%B %d, %Y at %I:%M %p')}
- Time Remaining: {batch.hours_remaining} hours

IMPORTANT: You must approve or reject this batch within 24 hours.
If no action is taken, all positions will be automatically rejected.

Click here to review and approve:
{settings.SITE_URL}/investing/managed/portal/approvals/batch/{batch.id}/

Questions? Contact your account manager.

Best regards,
CODA Investment Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [client.email],
                fail_silently=False
            )
            logger.info(f"Batch notification sent to {client.email} for {batch.batch_number}")
            
            # Send SMS if enabled
            if hasattr(batch.managed_account, 'sms_notifications') and batch.managed_account.sms_notifications:
                self.send_sms_notification(
                    client.phone_number if hasattr(client, 'phone_number') else None,
                    f"CODA: {batch.total_positions} options positions await your approval. "
                    f"Expires in 24hr. Check email for details."
                )
            
        except Exception as e:
            logger.error(f"Error sending batch notification: {str(e)}")
    
    def send_batch_reminder(self, batch):
        """
        Send reminder email 12 hours before deadline
        """
        client = batch.managed_account.client
        
        subject = f"REMINDER: Position Batch Expires in 12 Hours - {batch.batch_number}"
        
        message = f"""
Dear {client.first_name},

REMINDER: Your position batch approval is pending and will expire in approximately 12 hours.

Batch Details:
- Batch Number: {batch.batch_number}
- Total Positions: {batch.total_positions}
- Total Capital: ${batch.total_capital_required:,.2f}
- Deadline: {batch.approval_deadline.strftime('%B %d at %I:%M %p')}
- Time Remaining: ~{batch.hours_remaining} hours

⚠️ ACTION REQUIRED: Please review and approve/reject before the deadline.
If no action is taken, all positions will be automatically rejected.

Review batch now:
{settings.SITE_URL}/investing/managed/portal/approvals/batch/{batch.id}/

Best regards,
CODA Investment Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [client.email],
                fail_silently=False
            )
            logger.info(f"Batch reminder sent to {client.email} for {batch.batch_number}")
        except Exception as e:
            logger.error(f"Error sending batch reminder: {str(e)}")
    
    def send_timeout_notification(self, batch):
        """
        Send notification when batch times out (24 hours expired)
        """
        client = batch.managed_account.client
        
        subject = f"Position Batch Expired - {batch.batch_number}"
        
        message = f"""
Dear {client.first_name},

Your position batch {batch.batch_number} has expired due to the 24-hour timeout.

All {batch.total_positions} positions in this batch have been automatically rejected.

Batch Summary:
- Batch Number: {batch.batch_number}
- Created: {batch.created_date.strftime('%B %d at %I:%M %p')}
- Deadline: {batch.approval_deadline.strftime('%B %d at %I:%M %p')}
- Status: EXPIRED

The ${batch.total_capital_required:,.2f} capital remains available in your account for future trades.

To avoid timeouts in the future:
- Check your email regularly for batch notifications
- Enable SMS notifications for faster alerts
- Set up email filters to prioritize batch approval emails

Your trading manager will prepare new positions for next week's batch.

Questions? Contact us at {settings.SUPPORT_EMAIL}

Best regards,
CODA Investment Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [client.email],
                fail_silently=False
            )
            logger.info(f"Timeout notification sent to {client.email} for {batch.batch_number}")
            
            batch.timeout_notification_sent = True
            batch.save()
            
        except Exception as e:
            logger.error(f"Error sending timeout notification: {str(e)}")
    
    def send_batch_approved_notification(self, batch, approved_count):
        """
        Send confirmation when client approves batch
        """
        client = batch.managed_account.client
        
        subject = f"Batch Approved - {batch.batch_number}"
        
        message = f"""
Dear {client.first_name},

Thank you for approving your position batch!

Batch Summary:
- Batch Number: {batch.batch_number}
- Positions Approved: {approved_count}
- Total Capital Deployed: ${batch.total_capital_required:,.2f}
- Approved: {batch.approved_date.strftime('%B %d at %I:%M %p')}

All approved positions are now active and will be managed according to your trading rules.

You can view your positions anytime:
{settings.SITE_URL}/investing/managed/portal/

Weekly performance updates will be sent every Monday.

Best regards,
CODA Investment Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [client.email],
                fail_silently=False
            )
            logger.info(f"Batch approved notification sent to {client.email}")
        except Exception as e:
            logger.error(f"Error sending batch approved notification: {str(e)}")
    
    def send_sms_notification(self, phone_number, message):
        """
        Send SMS notification (placeholder - integrate with SMS provider)
        
        TODO: Integrate with Twilio, AWS SNS, or other SMS provider
        """
        if not phone_number:
            return
        
        logger.info(f"SMS to {phone_number}: {message}")
        # TODO: Actual SMS integration
        # import twilio
        # client = twilio.rest.Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
        # client.messages.create(to=phone_number, from_=settings.TWILIO_FROM, body=message)

