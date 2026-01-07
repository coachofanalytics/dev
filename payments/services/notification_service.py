"""
Payment Notification Service

Handles all payment-related notifications including:
- Failed payment notifications
- Successful payment confirmations
- Subscription expiry warnings
- Refund notifications
- Suspicious activity alerts
"""

from typing import Dict, Any, Optional, List
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


# Import PDF service for receipt attachments
try:
    from .pdf_service import PDFReceiptService
    PDF_SERVICE_AVAILABLE = True
except ImportError:
    PDF_SERVICE_AVAILABLE = False
    logger.warning("PDFReceiptService not available - receipts will not be attached to emails")


class PaymentNotificationService:
    """
    Service for sending payment-related notifications via multiple channels.
    """

    @classmethod
    def send_failed_payment_notification(
        cls,
        user: User,
        transaction_id: str,
        amount: Decimal,
        currency: str,
        failure_reason: str,
        retry_scheduled: bool = False,
        next_retry_time: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Send notification when a payment fails.

        Args:
            user: User whose payment failed
            transaction_id: Transaction reference ID
            amount: Payment amount
            currency: Payment currency
            failure_reason: Reason for failure
            retry_scheduled: Whether automatic retry is scheduled
            next_retry_time: When the next retry will occur

        Returns:
            Dictionary with notification status
        """
        results = {'email': False, 'log': False}

        # Log the failure
        logger.warning(
            f"Payment failed for user {user.username}: "
            f"Transaction {transaction_id}, Amount: {currency} {amount}, "
            f"Reason: {failure_reason}"
        )
        results['log'] = True

        # Send email notification
        try:
            subject = f"Payment Failed - Action Required"

            context = {
                'user': user,
                'transaction_id': transaction_id,
                'amount': amount,
                'currency': currency,
                'failure_reason': failure_reason,
                'retry_scheduled': retry_scheduled,
                'next_retry_time': next_retry_time,
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@biasharabridges.com'),
                'site_url': getattr(settings, 'SITE_URL', 'https://biasharabridges.com'),
            }

            # Plain text version
            text_content = f"""
Hello {user.first_name or user.username},

We were unable to process your payment.

Transaction Details:
- Transaction ID: {transaction_id}
- Amount: {currency} {amount}
- Reason: {failure_reason}

{"We will automatically retry this payment." if retry_scheduled else "Please update your payment method or try again."}

If you need assistance, please contact our support team at {context['support_email']}.

Best regards,
Biashara Bridges Team
"""

            # HTML version
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .btn {{ display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Payment Failed</h1>
        </div>
        <div class="content">
            <p>Hello {user.first_name or user.username},</p>
            <p>We were unable to process your payment. Please review the details below:</p>

            <div class="details">
                <p><strong>Transaction ID:</strong> {transaction_id}</p>
                <p><strong>Amount:</strong> {currency} {amount}</p>
                <p><strong>Reason:</strong> {failure_reason}</p>
            </div>

            {"<p><em>We will automatically retry this payment.</em></p>" if retry_scheduled else "<p>Please update your payment method or try again.</p>"}

            <p><a href="{context['site_url']}/payments/wallet/" class="btn">Go to Wallet</a></p>
        </div>
        <div class="footer">
            <p>Need help? Contact us at {context['support_email']}</p>
            <p>&copy; {timezone.now().year} Biashara Bridges. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            results['email'] = True
            logger.info(f"Failed payment notification sent to {user.email}")

        except Exception as e:
            logger.error(f"Failed to send payment failure notification: {e}")

        return results

    @classmethod
    def send_payment_success_notification(
        cls,
        user: User,
        transaction_id: str,
        amount: Decimal,
        currency: str,
        payment_type: str,
        description: str = "",
        attach_receipt: bool = True
    ) -> Dict[str, bool]:
        """
        Send notification when a payment succeeds.

        Args:
            user: User who made the payment
            transaction_id: Transaction reference ID
            amount: Payment amount
            currency: Payment currency
            payment_type: Type of payment (deposit, subscription, etc.)
            description: Optional description
            attach_receipt: Whether to attach PDF receipt (default: True)
        """
        results = {'email': False, 'log': False, 'receipt_attached': False}

        logger.info(
            f"Payment successful for user {user.username}: "
            f"Transaction {transaction_id}, Amount: {currency} {amount}"
        )
        results['log'] = True

        try:
            subject = f"Payment Successful - {currency} {amount}"

            text_content = f"""
Hello {user.first_name or user.username},

Your payment has been processed successfully.

Transaction Details:
- Transaction ID: {transaction_id}
- Amount: {currency} {amount}
- Type: {payment_type}
{f"- Description: {description}" if description else ""}

{"A PDF receipt is attached to this email for your records." if attach_receipt and PDF_SERVICE_AVAILABLE else ""}

Thank you for using Biashara Bridges!

Best regards,
Biashara Bridges Team
"""

            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .attachment-note {{ background-color: #e7f3ff; border-left: 4px solid #007bff; padding: 10px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Payment Successful</h1>
        </div>
        <div class="content">
            <p>Hello {user.first_name or user.username},</p>
            <p>Your payment has been processed successfully.</p>

            <div class="details">
                <p><strong>Transaction ID:</strong> {transaction_id}</p>
                <p><strong>Amount:</strong> {currency} {amount}</p>
                <p><strong>Type:</strong> {payment_type}</p>
                {f"<p><strong>Description:</strong> {description}</p>" if description else ""}
            </div>

            {"<div class='attachment-note'><strong>PDF Receipt:</strong> A PDF receipt is attached to this email for your records.</div>" if attach_receipt and PDF_SERVICE_AVAILABLE else ""}

            <p>Thank you for using Biashara Bridges!</p>
        </div>
        <div class="footer">
            <p>&copy; {timezone.now().year} Biashara Bridges. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            msg.attach_alternative(html_content, "text/html")

            # Attach PDF receipt if requested and available
            if attach_receipt and PDF_SERVICE_AVAILABLE:
                try:
                    pdf_buffer = PDFReceiptService.generate_transaction_receipt(transaction_id)
                    msg.attach(
                        f'receipt_{transaction_id}.pdf',
                        pdf_buffer.getvalue(),
                        'application/pdf'
                    )
                    results['receipt_attached'] = True
                    logger.info(f"PDF receipt attached to email for transaction {transaction_id}")
                except Exception as pdf_error:
                    logger.error(f"Failed to attach PDF receipt: {pdf_error}")
                    # Continue sending email even if PDF fails

            msg.send()

            results['email'] = True

        except Exception as e:
            logger.error(f"Failed to send payment success notification: {e}")

        return results

    @classmethod
    def send_subscription_expiry_warning(
        cls,
        user: User,
        subscription_name: str,
        days_remaining: int,
        end_date: str,
        auto_renew: bool
    ) -> Dict[str, bool]:
        """
        Send warning notification when subscription is about to expire.
        """
        results = {'email': False, 'log': False}

        logger.info(
            f"Subscription expiry warning for {user.username}: "
            f"{subscription_name} expires in {days_remaining} days"
        )
        results['log'] = True

        try:
            subject = f"Your {subscription_name} subscription expires in {days_remaining} days"

            site_url = getattr(settings, 'SITE_URL', 'https://biasharabridges.com')

            text_content = f"""
Hello {user.first_name or user.username},

Your {subscription_name} subscription will expire on {end_date}.

{"Auto-renewal is enabled. Your subscription will automatically renew." if auto_renew else "Please renew your subscription to continue enjoying our services."}

Visit your subscription page: {site_url}/payments/subscriptions/

Best regards,
Biashara Bridges Team
"""

            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            results['email'] = True

        except Exception as e:
            logger.error(f"Failed to send subscription expiry warning: {e}")

        return results

    @classmethod
    def send_refund_notification(
        cls,
        user: User,
        transaction_id: str,
        amount: Decimal,
        currency: str,
        reason: str
    ) -> Dict[str, bool]:
        """
        Send notification when a refund is processed.
        """
        results = {'email': False, 'log': False}

        logger.info(
            f"Refund processed for user {user.username}: "
            f"Transaction {transaction_id}, Amount: {currency} {amount}"
        )
        results['log'] = True

        try:
            subject = f"Refund Processed - {currency} {amount}"

            text_content = f"""
Hello {user.first_name or user.username},

A refund has been processed for your account.

Refund Details:
- Transaction ID: {transaction_id}
- Amount: {currency} {amount}
- Reason: {reason}

The refund will be credited to your original payment method within 5-10 business days.

Best regards,
Biashara Bridges Team
"""

            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            results['email'] = True

        except Exception as e:
            logger.error(f"Failed to send refund notification: {e}")

        return results

    @classmethod
    def send_suspicious_activity_alert(
        cls,
        user: User,
        activity_type: str,
        details: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Send alert for suspicious wallet/payment activity.
        """
        results = {'email': False, 'admin_email': False, 'log': False}

        logger.warning(
            f"Suspicious activity detected for user {user.username}: "
            f"Type: {activity_type}, Details: {details}"
        )
        results['log'] = True

        # Notify user
        try:
            subject = f"Security Alert - Unusual Activity Detected"

            text_content = f"""
Hello {user.first_name or user.username},

We detected unusual activity on your account:

Activity Type: {activity_type}

If this was you, you can ignore this message. If not, please:
1. Change your password immediately
2. Review your recent transactions
3. Contact our support team

Best regards,
Biashara Bridges Security Team
"""

            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            results['email'] = True

        except Exception as e:
            logger.error(f"Failed to send suspicious activity alert to user: {e}")

        # Notify admin
        try:
            admin_email = getattr(settings, 'SECURITY_ADMIN_EMAIL', None)
            if admin_email:
                subject = f"[ALERT] Suspicious Activity - User: {user.username}"

                text_content = f"""
Suspicious Activity Alert
========================

User: {user.username} ({user.email})
Activity Type: {activity_type}
Timestamp: {timezone.now()}

Details:
{chr(10).join(f'- {k}: {v}' for k, v in details.items())}

Please investigate this activity.
"""

                send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin_email],
                    fail_silently=False,
                )

                results['admin_email'] = True

        except Exception as e:
            logger.error(f"Failed to send suspicious activity alert to admin: {e}")

        return results

    @classmethod
    def send_deposit_confirmation(
        cls,
        user: User,
        amount: Decimal,
        currency: str,
        new_balance: Decimal,
        payment_method: str
    ) -> Dict[str, bool]:
        """
        Send confirmation when funds are deposited to wallet.
        """
        results = {'email': False, 'log': False}

        logger.info(
            f"Deposit confirmed for user {user.username}: "
            f"{currency} {amount}, New balance: {currency} {new_balance}"
        )
        results['log'] = True

        try:
            subject = f"Deposit Confirmed - {currency} {amount}"

            text_content = f"""
Hello {user.first_name or user.username},

Your deposit has been confirmed and added to your wallet.

Deposit Details:
- Amount: {currency} {amount}
- Payment Method: {payment_method}
- New Balance: {currency} {new_balance}

Thank you for using Biashara Bridges!

Best regards,
Biashara Bridges Team
"""

            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            results['email'] = True

        except Exception as e:
            logger.error(f"Failed to send deposit confirmation: {e}")

        return results

    @classmethod
    def send_dispute_created_notification_to_user(
        cls,
        user: User,
        dispute_id: str,
        transaction_id: str,
        amount: Decimal,
        priority: str,
        sla_deadline
    ) -> Dict[str, bool]:
        """
        Send confirmation to user when they create a dispute.
        """
        results = {'email': False, 'log': False}

        logger.info(f"Dispute created by user {user.username}: {dispute_id}")
        results['log'] = True

        try:
            priority_label = dict([('normal', 'Normal'), ('high', 'High'), ('critical', 'Critical')]).get(priority, 'Normal')
            sla_date = sla_deadline.strftime('%B %d, %Y at %I:%M %p') if sla_deadline else 'N/A'

            subject = f"Dispute Created - {dispute_id}"

            text_content = f"""
Hello {user.first_name or user.username},

Your payment dispute has been successfully created and is being reviewed by our team.

Dispute Details:
- Dispute ID: {dispute_id}
- Transaction ID: {transaction_id}
- Amount Disputed: ${amount}
- Priority: {priority_label}
- Expected Resolution By: {sla_date}

We will review your dispute and provide a resolution as soon as possible. You will receive an email notification when the status changes.

You can track your dispute status at: https://biasharadev-68034baaf749.herokuapp.com/payments/disputes/

Thank you for your patience.

Best regards,
Biashara Bridges Support Team
"""

            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #ff9800; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .priority-badge {{ display: inline-block; padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
        .priority-critical {{ background-color: #f44336; color: white; }}
        .priority-high {{ background-color: #ff9800; color: white; }}
        .priority-normal {{ background-color: #4caf50; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Dispute Created</h1>
        </div>
        <div class="content">
            <p>Hello {user.first_name or user.username},</p>
            <p>Your payment dispute has been successfully created and is being reviewed by our team.</p>

            <div class="details">
                <p><strong>Dispute ID:</strong> {dispute_id}</p>
                <p><strong>Transaction ID:</strong> {transaction_id}</p>
                <p><strong>Amount Disputed:</strong> ${amount}</p>
                <p><strong>Priority:</strong> <span class="priority-badge priority-{priority}">{priority_label}</span></p>
                <p><strong>Expected Resolution By:</strong> {sla_date}</p>
            </div>

            <p>We will review your dispute and provide a resolution as soon as possible. You will receive an email notification when the status changes.</p>

            <p><a href="https://biasharadev-68034baaf749.herokuapp.com/payments/disputes/" style="color: #007bff;">Track your dispute status</a></p>
        </div>
        <div class="footer">
            <p>&copy; {timezone.now().year} Biashara Bridges. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            results['email'] = True

        except Exception as e:
            logger.error(f"Failed to send dispute created notification: {e}")

        return results

    @classmethod
    def send_dispute_created_notification_to_staff(
        cls,
        dispute_id: str,
        user_email: str,
        transaction_id: str,
        amount: Decimal,
        reason: str,
        priority: str,
        sla_deadline
    ) -> Dict[str, bool]:
        """
        Notify staff when a new dispute is created.
        """
        results = {'email': False, 'log': False}

        logger.info(f"Notifying staff of new dispute: {dispute_id}")
        results['log'] = True

        try:
            from accounts.models import Staff

            # Get all active staff members
            staff_emails = Staff.objects.filter(is_active=True).values_list('user__email', flat=True)

            if not staff_emails:
                logger.warning("No active staff members to notify")
                return results

            priority_label = dict([('normal', 'Normal'), ('high', 'High'), ('critical', 'Critical')]).get(priority, 'Normal')
            sla_date = sla_deadline.strftime('%B %d, %Y at %I:%M %p') if sla_deadline else 'N/A'

            subject = f"[{priority_label} Priority] New Dispute - {dispute_id}"

            text_content = f"""
New Payment Dispute Alert

A new payment dispute has been filed and requires attention.

Dispute Details:
- Dispute ID: {dispute_id}
- User: {user_email}
- Transaction ID: {transaction_id}
- Amount: ${amount}
- Reason: {reason}
- Priority: {priority_label}
- SLA Deadline: {sla_date}

Please review and resolve this dispute at:
https://biasharadev-68034baaf749.herokuapp.com/payments/staff/disputes/

Biashara Bridges Payment System
"""

            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(staff_emails),
                fail_silently=False,
            )

            results['email'] = True

        except Exception as e:
            logger.error(f"Failed to send staff notification: {e}")

        return results

    @classmethod
    def send_dispute_status_change_notification(
        cls,
        user: User,
        dispute_id: str,
        old_status: str,
        new_status: str,
        resolution_notes: str = None
    ) -> Dict[str, bool]:
        """
        Notify user when dispute status changes.
        """
        results = {'email': False, 'log': False}

        logger.info(f"Dispute {dispute_id} status changed from {old_status} to {new_status}")
        results['log'] = True

        try:
            status_display = dict([
                ('open', 'Open'),
                ('under_review', 'Under Review'),
                ('resolved_favor_user', 'Resolved - In Your Favor'),
                ('resolved_favor_merchant', 'Resolved - In Merchant Favor'),
                ('closed', 'Closed'),
            ]).get(new_status, new_status)

            subject = f"Dispute Status Update - {dispute_id}"

            text_content = f"""
Hello {user.first_name or user.username},

The status of your payment dispute has been updated.

Dispute ID: {dispute_id}
Previous Status: {old_status.replace('_', ' ').title()}
Current Status: {status_display}

{f"Resolution Notes: {resolution_notes}" if resolution_notes else ""}

You can view full details at:
https://biasharadev-68034baaf749.herokuapp.com/payments/disputes/

Thank you for your patience.

Best regards,
Biashara Bridges Support Team
"""

            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2196f3; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .status-badge {{ display: inline-block; padding: 5px 10px; border-radius: 3px; font-weight: bold; background-color: #2196f3; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Dispute Status Update</h1>
        </div>
        <div class="content">
            <p>Hello {user.first_name or user.username},</p>
            <p>The status of your payment dispute has been updated.</p>

            <div class="details">
                <p><strong>Dispute ID:</strong> {dispute_id}</p>
                <p><strong>Previous Status:</strong> {old_status.replace('_', ' ').title()}</p>
                <p><strong>Current Status:</strong> <span class="status-badge">{status_display}</span></p>
                {f"<p><strong>Resolution Notes:</strong><br>{resolution_notes}</p>" if resolution_notes else ""}
            </div>

            <p><a href="https://biasharadev-68034baaf749.herokuapp.com/payments/disputes/" style="color: #007bff;">View full details</a></p>
        </div>
        <div class="footer">
            <p>&copy; {timezone.now().year} Biashara Bridges. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            results['email'] = True

        except Exception as e:
            logger.error(f"Failed to send status change notification: {e}")

        return results
