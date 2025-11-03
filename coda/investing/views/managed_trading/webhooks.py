"""
WhatsApp Webhooks for Real-Time Client Approval

Handles incoming WhatsApp messages for quick position batch approvals.
Client replies "YES" to approve or "NO" to view details.
"""

import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings

from ...models import PositionBatch

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def whatsapp_webhook(request):
    """
    Handle incoming WhatsApp messages from Twilio
    
    Expected format from Twilio:
    - Body: Message text ("YES", "NO", etc.)
    - From: Sender phone (whatsapp:+1234567890)
    - MessageSid: Unique message ID
    
    Workflow:
    1. Client receives batch notification
    2. Client replies "YES" or "NO"
    3. Webhook processes reply
    4. Batch approved/rejected instantly
    """
    try:
        # Get message details from Twilio
        message_body = request.POST.get('Body', '').strip().upper()
        from_number = request.POST.get('From', '').replace('whatsapp:', '')
        message_sid = request.POST.get('MessageSid', '')
        
        logger.info(f"📱 WhatsApp webhook received: {message_body} from {from_number}")
        logger.debug(f"   Message SID: {message_sid}")
        
        # Find pending batch for this client
        # NOTE: We match by phone number on ManagedTradingAccount
        batch = PositionBatch.objects.filter(
            status='pending',
            managed_account__client_phone=from_number
        ).order_by('-created_date').first()
        
        if not batch:
            logger.warning(f"⚠️  No pending batch found for {from_number}")
            return HttpResponse(
                "<?xml version='1.0' encoding='UTF-8'?>"
                "<Response>"
                "<Message>No pending batch found. Please check your email or portal.</Message>"
                "</Response>",
                content_type='text/xml'
            )
        
        # Handle "YES" - Approve batch
        if message_body in ['YES', 'APPROVE', 'CONFIRMED', 'Y']:
            logger.info(f"✅ Approving batch {batch.batch_number} via WhatsApp")
            
            # Approve batch
            batch.status = 'approved'
            batch.approved_date = timezone.now()
            batch.approval_method = 'whatsapp'
            batch.approval_ip = get_client_ip(request)
            batch.save()
            
            # Send confirmation
            response_message = f"✅ APPROVED!\n\n{batch.total_positions} positions activated.\nCapital deployed: ${batch.total_capital_required:,.2f}\n\nYou'll receive updates as positions are entered."
            
            # TODO: Trigger position entry workflow
            # from ...services.batch_processor import BatchProcessor
            # processor = BatchProcessor()
            # processor.process_approved_batch(batch)
            
            logger.info(f"✅ Batch {batch.batch_number} approved via WhatsApp by {from_number}")
        
        # Handle "NO" - Send portal link
        elif message_body in ['NO', 'REJECT', 'REVIEW', 'N']:
            logger.info(f"❌ Client {from_number} wants to review batch {batch.batch_number}")
            
            portal_link = f"{getattr(settings, 'SITE_URL', 'https://codamakutano.herokuapp.com')}/investing/managed/portal/approvals/batch/{batch.id}/"
            response_message = f"📊 Review your {batch.total_positions} positions:\n{portal_link}\n\nYou have {batch.time_remaining.total_seconds() / 3600:.0f} hours to approve."
        
        # Handle "HELP" or unknown
        else:
            logger.info(f"❓ Unknown command from {from_number}: {message_body}")
            response_message = f"Reply 'YES' to approve {batch.total_positions} positions or 'NO' to review details.\n\nBatch: {batch.batch_number}"
        
        # Send response via Twilio
        return HttpResponse(
            f"<?xml version='1.0' encoding='UTF-8'?>"
            f"<Response>"
            f"<Message>{response_message}</Message>"
            f"</Response>",
            content_type='text/xml'
        )
    
    except Exception as e:
        logger.error(f"❌ WhatsApp webhook error: {str(e)}", exc_info=True)
        return HttpResponse(
            "<?xml version='1.0' encoding='UTF-8'?>"
            "<Response>"
            "<Message>Error processing request. Please contact support.</Message>"
            "</Response>",
            content_type='text/xml'
        )


def get_client_ip(request):
    """Get client IP from request headers"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@csrf_exempt
@require_POST
def whatsapp_status_callback(request):
    """
    Handle delivery status updates from Twilio
    
    Statuses: queued, sending, sent, delivered, read, failed
    """
    try:
        message_sid = request.POST.get('MessageSid', '')
        message_status = request.POST.get('MessageStatus', '')
        
        logger.info(f"📱 WhatsApp status: {message_sid} - {message_status}")
        
        # TODO: Update batch notification status in database
        # if message_status in ['delivered', 'read']:
        #     batch = PositionBatch.objects.filter(...).first()
        #     batch.whatsapp_delivered = True
        #     batch.save()
        
        return JsonResponse({'status': 'ok'})
    
    except Exception as e:
        logger.error(f"❌ Status callback error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

