"""
WhatsApp/Telegram Notification Signals (Phase 3)

Automatically sends WhatsApp/Telegram notifications when:
- Position opens
- Position closes (with P&L)
- Position batch created
- Position batch reminder needed
"""

import logging
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from ..models import OptionsPosition, PositionBatch
from ..services.notification_service import NotificationService

logger = logging.getLogger(__name__)


# ========================================================================
# POSITION NOTIFICATIONS
# ========================================================================

@receiver(post_save, sender=OptionsPosition)
def notify_position_status_change(sender, instance, created, **kwargs):
    """
    Send WhatsApp/Telegram notification when position status changes
    
    Triggers:
    - Position opened → "New position opened" alert
    - Position closed → Win/Loss alert with P&L
    """
    # Skip if account doesn't have WhatsApp/Telegram enabled
    if not instance.managed_account:
        return
    
    account = instance.managed_account
    
    # Skip if no notification preferences enabled
    if not (account.whatsapp_enabled or account.telegram_enabled):
        return
    
    notification_service = NotificationService()
    
    # ========================================================================
    # POSITION OPENED
    # ========================================================================
    if created and instance.status == 'open':
        logger.info(f"📱 Sending position opened notification for {instance.symbol}")
        
        # Prepare template parameters
        params = {
            'symbol': instance.symbol,
            'strategy': instance.get_strategy_display(),
            'contracts': instance.contracts,
            'premium': f"{instance.premium_collected:.2f}" if instance.premium_collected else "TBD",
            'max_profit': f"{instance.max_profit:.2f}" if instance.max_profit else "TBD",
            'dte': instance.dte if instance.dte else "N/A",
        }
        
        # Send WhatsApp
        if account.whatsapp_enabled and account.whatsapp_phone:
            try:
                notification_service.send_whatsapp_message(
                    phone_number=account.whatsapp_phone,
                    template_name='position_opened',
                    template_params=params
                )
                logger.info(f"✅ WhatsApp sent for {instance.symbol} opened")
            except Exception as e:
                logger.error(f"❌ WhatsApp failed for {instance.symbol}: {e}")
        
        # Send Telegram
        if account.telegram_enabled and account.telegram_chat_id:
            try:
                message = f"""
🟢 **NEW POSITION OPENED**

Symbol: {params['symbol']}
Strategy: {params['strategy']}
Contracts: {params['contracts']}
Premium: ${params['premium']}
Max Profit: ${params['max_profit']}
DTE: {params['dte']} days

Your position is now active!
                """.strip()
                
                notification_service.send_telegram_message(
                    chat_id=account.telegram_chat_id,
                    message=message
                )
                logger.info(f"✅ Telegram sent for {instance.symbol} opened")
            except Exception as e:
                logger.error(f"❌ Telegram failed for {instance.symbol}: {e}")
    
    # ========================================================================
    # POSITION CLOSED
    # ========================================================================
    elif not created and instance.status == 'closed' and instance.realized_pnl is not None:
        logger.info(f"📱 Sending position closed notification for {instance.symbol}")
        
        # Determine if win or loss
        is_win = instance.realized_pnl > 0
        pnl_display = f"+${instance.realized_pnl:.2f}" if is_win else f"-${abs(instance.realized_pnl):.2f}"
        
        # Calculate ROI
        roi = Decimal('0')
        if instance.premium_collected and instance.premium_collected > 0:
            roi = (instance.realized_pnl / instance.premium_collected) * 100
        
        # Calculate days held
        days_held = 0
        if instance.entry_date and instance.exit_date:
            days_held = (instance.exit_date - instance.entry_date).days
        
        # Calculate annualized return
        annualized_return = Decimal('0')
        if days_held > 0 and roi != 0:
            annualized_return = roi * (365 / Decimal(str(days_held)))
        
        # Prepare template parameters
        if is_win:
            # WIN notification
            params = {
                'symbol': instance.symbol,
                'profit': f"{instance.realized_pnl:.2f}",
                'roi': f"{roi:.1f}",
                'premium': f"{instance.premium_collected:.2f}" if instance.premium_collected else "N/A",
                'days_held': days_held,
                'annualized_return': f"{annualized_return:.0f}",
            }
            template_name = 'position_profit'
            emoji = "✅"
            result = "WINNER!"
        else:
            # LOSS notification
            params = {
                'symbol': instance.symbol,
                'loss': f"{abs(instance.realized_pnl):.2f}",
                'roi': f"{roi:.1f}",
            }
            template_name = 'position_loss'
            emoji = "⚠️"
            result = "Position Closed"
        
        # Add generic params for position_closed template
        generic_params = {
            'status_emoji': emoji,
            'symbol': instance.symbol,
            'strategy': instance.get_strategy_display(),
            'pnl_display': pnl_display,
            'roi': f"{roi:.1f}",
            'days_held': days_held,
            'result_message': result,
        }
        
        # Send WhatsApp
        if account.whatsapp_enabled and account.whatsapp_phone:
            try:
                notification_service.send_whatsapp_message(
                    phone_number=account.whatsapp_phone,
                    template_name=template_name,
                    template_params=params
                )
                logger.info(f"✅ WhatsApp sent for {instance.symbol} closed ({result})")
            except Exception as e:
                logger.error(f"❌ WhatsApp failed for {instance.symbol}: {e}")
        
        # Send Telegram
        if account.telegram_enabled and account.telegram_chat_id:
            try:
                if is_win:
                    message = f"""
✅ **WINNER!**

{instance.symbol} closed at +${params['profit']} ({params['roi']}% return)

Premium collected: ${params['premium']}
Held for: {params['days_held']} days
Annualized: {params['annualized_return']}%

Great trade! 🎉
                    """.strip()
                else:
                    message = f"""
⚠️ **Position Closed**

{instance.symbol}: ${params['loss']} loss ({params['roi']}%)

This position didn't work out, but it's part of the strategy.
Overall portfolio performance remains strong.

Next positions coming soon!
                    """.strip()
                
                notification_service.send_telegram_message(
                    chat_id=account.telegram_chat_id,
                    message=message
                )
                logger.info(f"✅ Telegram sent for {instance.symbol} closed ({result})")
            except Exception as e:
                logger.error(f"❌ Telegram failed for {instance.symbol}: {e}")


# ========================================================================
# BATCH NOTIFICATIONS
# ========================================================================

@receiver(post_save, sender=PositionBatch)
def notify_batch_created(sender, instance, created, **kwargs):
    """
    Send WhatsApp/Telegram notification when new batch is created
    """
    if not created:
        return
    
    # Skip if account doesn't have WhatsApp/Telegram enabled
    if not instance.managed_account:
        return
    
    account = instance.managed_account
    
    # Skip if no notification preferences enabled
    if not (account.whatsapp_enabled or account.telegram_enabled):
        return
    
    logger.info(f"📱 Sending batch created notification for {instance.batch_number}")
    
    notification_service = NotificationService()
    
    # Prepare template parameters
    params = {
        'count': instance.total_positions,
        'capital': f"{instance.total_capital_required:,.2f}",
        'deadline': instance.approval_deadline.strftime('%B %d at %I:%M %p'),
        'link': f"{getattr(settings, 'SITE_URL', 'https://codamakutano.herokuapp.com')}/investing/managed/portal/approvals/batch/{instance.id}/",
    }
    
    # Send WhatsApp
    if account.whatsapp_enabled and account.whatsapp_phone:
        try:
            notification_service.send_whatsapp_message(
                phone_number=account.whatsapp_phone,
                template_name='batch_approval',
                template_params=params
            )
            logger.info(f"✅ WhatsApp sent for batch {instance.batch_number}")
        except Exception as e:
            logger.error(f"❌ WhatsApp failed for batch {instance.batch_number}: {e}")
    
    # Send Telegram
    if account.telegram_enabled and account.telegram_chat_id:
        try:
            message = f"""
📦 **NEW POSITIONS READY**

{params['count']} positions need your approval!

Total Capital: ${params['capital']}
Approval Deadline: {params['deadline']}

Click to review:
{params['link']}

Approve within 24 hours!
            """.strip()
            
            notification_service.send_telegram_message(
                chat_id=account.telegram_chat_id,
                message=message
            )
            logger.info(f"✅ Telegram sent for batch {instance.batch_number}")
        except Exception as e:
            logger.error(f"❌ Telegram failed for batch {instance.batch_number}: {e}")

