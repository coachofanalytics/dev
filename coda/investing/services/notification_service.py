"""
Notification Service
Handles email and SMS notifications for managed trading
"""

import logging
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


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
{getattr(settings, 'SITE_URL', 'https://codamakutano.herokuapp.com')}/investing/managed/portal/approvals/batch/{batch.id}/

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

    # ------------------------------------------------------------------
    # Managed Income Automation
    # ------------------------------------------------------------------

    def send_internal_allocation_digest(self, allocation_summary: dict, *, subject: str | None = None) -> bool:
        """Email staff with the latest allocation recommendations."""

        staff_emails = self._get_staff_emails()
        if not staff_emails:
            logger.warning("No staff emails configured; skipping allocation digest")
            return False

        allocations = allocation_summary.get('allocations') or []
        totals = allocation_summary.get('totals') or {}
        account_capital = allocation_summary.get('account_capital', 0)
        income_target = allocation_summary.get('income_target', 0)
        coverage_pct = totals.get('coverage_pct', 0)
        meets_target = allocation_summary.get('meets_target', False)
        cache_stats = allocation_summary.get('cache_stats') or {}

        subject = subject or "💼 Managed Income Allocation Preview"

        account_capital_value = Decimal(str(account_capital or 0))
        income_target_value = Decimal(str(income_target or 0))
        expected_income_value = Decimal(str(totals.get('expected_income', 0) or 0))
        coverage_decimal = Decimal(str(coverage_pct or 0))

        if allocations:
            allocation_lines = []
            for idx, item in enumerate(allocations, start=1):
                capital_used = Decimal(str(item.get('capital_used', 0) or 0))
                expected_income_item = Decimal(str(item.get('expected_income', 0) or 0))
                flow_score_value = Decimal(str(item.get('flow_score', 0) or 0))
                ai_score_value = Decimal(str(item.get('ai_score', 0) or 0))
                allocation_lines.append(
                    f"{idx}. {item['symbol']} {item['strategy']} — ${capital_used:,.2f} capital, "
                    f"${expected_income_item:,.2f} income, AI {ai_score_value:.0f} / Flow {flow_score_value:.0f} "
                    f"({item['timing_signal']})"
                )
        else:
            allocation_lines = ["No qualifying positions this cycle — review pending suggestions or adjust filters."]

        cache_line = (
            f"UW cache: {cache_stats.get('cache_hits', 0)} hit(s), {cache_stats.get('api_calls', 0)} live call(s), TTL {cache_stats.get('ttl', 0)}s"
            if cache_stats
            else "UW cache: n/a"
        )

        notes_joined = ', '.join(allocation_summary.get('notes') or ['None'])

        body = f"""
Managed Income Allocation Preview ({timezone.now().strftime('%Y-%m-%d %H:%M %Z')})

Account Capital: ${account_capital_value:,.0f}
Income Target: ${income_target_value:,.0f}
Expected Income: ${expected_income_value:,.0f} ({coverage_decimal:.1f}% of target)
Positions Selected: {totals.get('positions', 0)}
Target Met: {'✅ Yes' if meets_target else '⚠️ Not yet'}

Recommendations:
{"\n".join(allocation_lines)}

Notes: {notes_joined}
{cache_line}
        """.strip()

        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                staff_emails,
                fail_silently=False
            )
            logger.info("Sent allocation digest to %s staff recipients", len(staff_emails))
            return True
        except Exception as exc:
            logger.error("Failed to send allocation digest: %s", exc)
            return False
    
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
{getattr(settings, 'SITE_URL', 'https://codamakutano.herokuapp.com')}/investing/managed/portal/approvals/batch/{batch.id}/

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

Questions? Contact us at {getattr(settings, 'SUPPORT_EMAIL', 'support@codanalytics.net')}

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
{getattr(settings, 'SITE_URL', 'https://codamakutano.herokuapp.com')}/investing/managed/portal/

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
    
    def send_auto_approved_notification(self, batch, position_count):
        """
        Notify trading staff that a batch auto-approved after the client timeout window.
        """
        staff_emails = self._get_staff_emails()
        
        if not staff_emails:
            logger.info(
                "Auto-approved batch %s with %s positions (no staff recipients configured)",
                batch.batch_number,
                position_count,
            )
            return
        
        subject = f"[Managed Trading] Batch {batch.batch_number} auto-approved ({position_count} positions)"
        site_url = getattr(settings, 'SITE_URL', 'https://codamakutano.herokuapp.com')
        message = (
            f"Client timeout reached for batch {batch.batch_number} (account {batch.managed_account.account_number}).\n\n"
            f"{position_count} positions are now cleared by the client window and await trader execution.\n\n"
            f"Review the batch here:\n{site_url}/investing/managed/staff/batches/\n"
            f"Filter for batch number {batch.batch_number} to process the trades."
        )
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                staff_emails,
                fail_silently=False,
            )
            logger.info(
                "Sent auto-approval notice for batch %s to %d staff recipients",
                batch.batch_number,
                len(staff_emails),
            )
        except Exception as exc:
            logger.error(
                "Error sending auto-approval notification for batch %s: %s",
                batch.batch_number,
                exc,
            )
    
    def send_auto_suggestion_summary(self, auto_positions: list, remaining: list):
        """
        Email staff a summary of system-approved suggestions and remaining opportunities.
        """
        if not auto_positions:
            return
        
        staff_emails = self._get_staff_emails()
        if not staff_emails:
            logger.info("Auto suggestion summary suppressed (no staff recipients).")
            return
        
        subject = "[Managed Trading] System auto-approved top ranked positions"
        summary_lines = [
            "The ranking engine auto-approved the following positions:",
            "",
        ]
        for item in auto_positions:
            summary_lines.append(
                f"• #{item['rank']} {item['symbol']} {item['strategy']} "
                f"(Score {item['total_score']:.1f}/100, {item['recommendation']})"
            )
        summary_lines.append("")
        
        if remaining:
            summary_lines.append("Additional high-ranking suggestions awaiting review:")
            for item in remaining[:5]:
                summary_lines.append(
                    f"• #{item['rank']} {item['position'].symbol} "
                    f"(Score {item['total_score']:.1f}/100, {item['recommendation']})"
                )
            summary_lines.append("")
        
        summary_lines.append("Log in to the suggestion dashboard to review or adjust exposures.")
        site_url = getattr(settings, 'SITE_URL', 'https://codamakutano.herokuapp.com')
        summary_lines.append(f"Dashboard: {site_url}/investing/managed/staff/suggestions/")
        
        message = "\n".join(summary_lines)
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                staff_emails,
                fail_silently=False,
            )
            logger.info(
                "Sent auto suggestion summary to %d staff recipients",
                len(staff_emails),
            )
        except Exception as exc:
            logger.error("Error sending auto suggestion summary: %s", exc)
    
    @staticmethod
    def _get_staff_emails() -> list[str]:
        base_qs = User.objects.filter(
            is_active=True,
            email__isnull=False,
        ).exclude(email='').filter(
            Q(is_superuser=True) | Q(is_staff=True)
        )

        emails = set(
            base_qs.filter(is_superuser=True).values_list('email', flat=True)
        )

        group_name = getattr(settings, 'MANAGED_INCOME_DIGEST_GROUP', None)
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
            except Group.DoesNotExist:
                group = None

            if group:
                emails.update(
                    base_qs.filter(groups=group).values_list('email', flat=True)
                )

        return sorted(emails)

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
    
    # ========================================================================
    # WHATSAPP INTEGRATION (Phase 3)
    # ========================================================================
    
    def send_whatsapp_message(self, phone_number, template_name, template_params):
        """
        Send WhatsApp message using WhatsApp Business API
        
        Args:
            phone_number: Client phone in international format (+1234567890)
            template_name: Approved WhatsApp template name
            template_params: Dict of template variables
        
        Templates Available:
        - position_opened: New position notification
        - position_closed: Position close alert with P&L
        - batch_approval: New batch requires approval
        - position_profit: Win notification
        - position_loss: Loss notification
        
        Example:
            service.send_whatsapp_message(
                "+1234567890",
                "position_closed",
                {"symbol": "AAPL", "pnl": "+$150", "roi": "15%"}
            )
        """
        if not phone_number:
            logger.warning("WhatsApp: No phone number provided")
            return False
        
        # Check if WhatsApp enabled
        whatsapp_enabled = getattr(settings, 'WHATSAPP_ENABLED', False)
        if not whatsapp_enabled:
            logger.info(f"WhatsApp disabled - would send to {phone_number}: {template_name}")
            return False
        
        try:
            # Import WhatsApp client (lazy load)
            from twilio.rest import Client as TwilioClient
            
            # Twilio credentials
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            whatsapp_from = getattr(settings, 'TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
            
            if not account_sid or not auth_token:
                logger.error("WhatsApp: Twilio credentials not configured")
                return False
            
            # Initialize Twilio client
            client = TwilioClient(account_sid, auth_token)
            
            # Format message from template
            message_body = self._format_whatsapp_template(template_name, template_params)
            
            # Send WhatsApp message
            # Note: Twilio client has built-in timeout (default ~60s)
            # Can't set custom timeout easily without modifying Twilio client
            message = client.messages.create(
                from_=whatsapp_from,
                body=message_body,
                to=f'whatsapp:{phone_number}'
            )
            
            logger.info(f"✅ WhatsApp sent to {phone_number}: {message.sid}")
            return True
            
        except ImportError:
            logger.warning("Twilio not installed - install with: pip install twilio")
            return False
        except Exception as e:
            logger.error(f"❌ WhatsApp send failed to {phone_number}: {e}")
            return False
    
    def send_telegram_message(self, chat_id, message, parse_mode='Markdown'):
        """
        Send Telegram message using Telegram Bot API
        
        Args:
            chat_id: Telegram chat ID (user or group)
            message: Message text (supports Markdown)
            parse_mode: 'Markdown' or 'HTML'
        
        Example:
            service.send_telegram_message(
                chat_id=123456789,
                message="*AAPL Closed*\nP&L: +$150 (15%)\n✅ WIN!"
            )
        """
        if not chat_id:
            logger.warning("Telegram: No chat_id provided")
            return False
        
        telegram_enabled = getattr(settings, 'TELEGRAM_ENABLED', False)
        if not telegram_enabled:
            logger.info(f"Telegram disabled - would send to {chat_id}")
            return False
        
        try:
            import requests
            
            bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
            if not bot_token:
                logger.error("Telegram: Bot token not configured")
                return False
            
            # Telegram API endpoint
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)  # FIX: Add 10 second timeout
            
            if response.status_code == 200:
                logger.info(f"✅ Telegram sent to {chat_id}")
                return True
            else:
                logger.error(f"❌ Telegram failed: {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Telegram send error: {e}")
            return False
    
    def _format_whatsapp_template(self, template_name, params):
        """
        Format WhatsApp message from template
        
        Templates use simple string formatting for now
        Later: Use WhatsApp approved message templates
        """
        templates = {
            'position_opened': """
🟢 *NEW POSITION OPENED*

Symbol: {symbol}
Strategy: {strategy}
Contracts: {contracts}
Premium: ${premium}
Max Profit: ${max_profit}
DTE: {dte} days

Your position is now active!
            """,
            
            'position_closed': """
{status_emoji} *POSITION CLOSED*

Symbol: {symbol}
Strategy: {strategy}
P&L: {pnl_display}
ROI: {roi}%
Days Held: {days_held}

{result_message}
            """,
            
            'position_profit': """
✅ *WINNER!*

{symbol} closed at +${profit} ({roi}% return)

Premium collected: ${premium}
Held for: {days_held} days
Annualized: {annualized_return}%

Great trade! 🎉
            """,
            
            'position_loss': """
⚠️ *Position Closed*

{symbol}: ${loss} loss ({roi}%)

This position didn't work out, but it's part of the strategy.
Overall portfolio performance remains strong.

Next positions coming soon!
            """,
            
            'batch_approval': """
📦 *NEW POSITIONS READY*

{count} positions need your approval!

Total Capital: ${capital}
Approval Deadline: {deadline}

Click to review:
{link}

Approve within 24 hours!
            """,
            
            'batch_reminder': """
⏰ *REMINDER: Batch Expires Soon!*

{count} positions expire in {hours_left} hours

Capital: ${capital}
Deadline: {deadline}

Please review ASAP:
{link}
            """,
            
            'batch_quick_approval': """
💎 *NEW POSITIONS READY FOR APPROVAL*

{count} high-conviction positions selected!

Total Capital: ${capital:,.2f}
AI Average Score: {avg_score}/100
Cross-Validated: {cv_count} positions
Technical Confirmed: {tech_count} positions

🚀 QUICK APPROVE: Reply "YES" to approve all
❌ REVIEW FIRST: Reply "NO" to see details
📊 DETAILS: {link}

⏰ Expires in 24 hours
🔐 Token: {token}
            """,
        }
        
        template = templates.get(template_name, "Message: {message}")
        
        try:
            return template.format(**params)
        except KeyError as e:
            logger.error(f"Template formatting error: Missing parameter {e}")
            return f"Error formatting message for {template_name}"
    
    def send_realtime_batch_notification(self, batch):
        """
        Send real-time WhatsApp notification with quick approval option
        
        Client can reply "YES" to approve or "NO" to review in portal
        """
        from django.contrib.auth.models import User
        import secrets
        
        # Generate approval token if not exists
        if not batch.approval_token:
            batch.approval_token = secrets.token_urlsafe(32)
            batch.save()
        
        client = batch.managed_account.client
        account = batch.managed_account
        
        # Get client phone (assumes client has phone_number field)
        phone_number = getattr(account, 'client_phone', None) or getattr(client, 'phone_number', None)
        
        if not phone_number:
            logger.warning(f"No phone number for {client.email} - skipping WhatsApp notification")
            return False
        
        # Get batch stats
        from django.db.models import Avg
        positions = batch.suggested_positions.all()
        avg_score = positions.aggregate(avg=Avg('ai_score'))['avg'] or 0
        cv_count = positions.filter(notes__icontains='Cross-Validated').count()
        tech_count = positions.filter(notes__icontains='Technical:').count()
        
        # Format WhatsApp message
        params = {
            'count': batch.total_positions,
            'capital': batch.total_capital_required,
            'avg_score': round(avg_score, 1),
            'cv_count': cv_count,
            'tech_count': tech_count,
            'link': f"{getattr(settings, 'SITE_URL', 'https://codamakutano.herokuapp.com')}/investing/managed/portal/approvals/batch/{batch.id}/",
            'token': batch.approval_token[:8]  # Show first 8 chars for reference
        }
        
        # Send WhatsApp
        success = self.send_whatsapp_message(
            phone_number,
            'batch_quick_approval',
            params
        )
        
        if success:
            batch.whatsapp_notification_sent = True
            batch.whatsapp_notification_date = timezone.now()
            batch.save()
            logger.info(f"✅ Real-time WhatsApp sent to {phone_number} for {batch.batch_number}")
        
        return success

