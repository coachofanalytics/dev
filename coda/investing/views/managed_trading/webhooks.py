"""
Real-time webhook endpoints for Managed Trading.

Includes:
- WhatsApp/Twilio callbacks for client approvals
- Zapier integrations for operations automations (Phase 1 enhancement)
"""

import json
import logging

import requests
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from ...models import PositionBatch, OptionsPosition, SuggestedPosition

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


@csrf_exempt
@staff_member_required
@require_POST
def zapier_position_push(request):
    """
    Push a position (suggested or active) summary to Zapier for downstream automation.
    
    Expected POST params:
    - suggestion_id (optional): ID of SuggestedPosition
    - position_id (optional): ID of OptionsPosition
    
    Requires staff authentication and an environment variable `ZAPIER_POSITION_WEBHOOK`.
    """
    webhook_url = getattr(settings, 'ZAPIER_POSITION_WEBHOOK', None)
    if not webhook_url:
        logger.warning("Zapier webhook push attempted without configuration")
        return JsonResponse(
            {'success': False, 'message': 'Zapier webhook not configured'},
            status=503,
        )

    suggestion_id = request.POST.get('suggestion_id')
    position_id = request.POST.get('position_id')

    if not suggestion_id and not position_id:
        return JsonResponse(
            {'success': False, 'message': 'Provide suggestion_id or position_id'},
            status=400,
        )

    payload = {
        'triggered_at': timezone.now().isoformat(),
        'triggered_by': request.user.get_username(),
    }

    if suggestion_id:
        suggestion = get_object_or_404(SuggestedPosition, id=suggestion_id)
        payload.update({
            'record_type': 'suggested_position',
            'id': suggestion.id,
            'symbol': suggestion.symbol,
            'strategy': suggestion.get_strategy_display(),
            'probability_of_profit': float(suggestion.probability_of_profit or 0),
            'ai_score': float(suggestion.ai_score or 0),
            'ai_rating': suggestion.ai_rating,
            'source': suggestion.get_source_display(),
            'premium_collected': float(suggestion.premium_collected or 0),
            'capital_required': float(suggestion.capital_required or 0),
            'dte': suggestion.dte,
            'expiration_date': suggestion.expiration_date.isoformat(),
            'flow_notes_present': bool(suggestion.notes and 'Unusual Whales' in suggestion.notes),
            'api_response': suggestion.api_response_data or {},
            'legs': suggestion.positions or [],
        })
        if suggestion.notes:
            payload['notes'] = suggestion.notes
    else:
        position = get_object_or_404(OptionsPosition, id=position_id)
        account_number = getattr(position.managed_account, 'account_number', None)
        account_manager = getattr(position.managed_account, 'account_manager', None)
        account_manager_name = account_manager.get_full_name() if account_manager else None

        payload.update({
            'record_type': 'options_position',
            'id': position.id,
            'symbol': position.symbol,
            'strategy': position.get_strategy_display(),
            'status': position.status,
            'entry_date': position.entry_date.isoformat() if position.entry_date else None,
            'expiration_date': position.expiration_date.isoformat() if position.expiration_date else None,
            'max_profit': float(position.max_profit or 0),
            'max_loss': float(position.max_loss or 0),
            'premium_collected': float(position.premium_collected or 0),
            'capital_required': float(position.capital_required or 0),
            'managed_account': account_number,
            'account_manager': account_manager_name,
            'notes': position.notes or '',
        })

    try:
        logger.info("🔗 Sending Zapier payload: %s", payload['record_type'])
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=8,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("❌ Zapier push failed: %s", exc, exc_info=True)
        return JsonResponse(
            {'success': False, 'message': str(exc)},
            status=502,
        )

    return JsonResponse(
        {
            'success': True,
            'message': 'Zapier notified',
            'status_code': response.status_code,
        }
    )


@csrf_exempt
@require_POST
def zapier_inbound_handler(request):
    """
    Receive inbound notifications from Zapier (e.g., audits, approvals).
    
    Security:
    - Optional shared token via header `X-Zapier-Token` or `token` query param
    """
    expected_token = getattr(settings, 'ZAPIER_WEBHOOK_TOKEN', None)
    provided_token = (
        request.headers.get('X-Zapier-Token')
        or request.GET.get('token')
        or request.POST.get('token')
    )

    if expected_token and expected_token != provided_token:
        logger.warning("⚠️ Zapier inbound rejected - invalid token")
        return JsonResponse(
            {'success': False, 'message': 'Invalid token'},
            status=403,
        )

    try:
        body = request.body.decode('utf-8') or '{}'
        payload = json.loads(body)
    except json.JSONDecodeError:
        logger.error("❌ Zapier inbound payload not JSON")
        return JsonResponse(
            {'success': False, 'message': 'Invalid JSON payload'},
            status=400,
        )

    event = payload.get('event', 'unknown')
    logger.info("📬 Zapier inbound event: %s", event)

    if event == 'position_ack':
        logger.debug("Zapier acknowledged position: %s", payload.get('position_id'))
    elif event == 'alert_feedback':
        logger.debug("Zapier provided alert feedback: %s", payload.get('details'))
    else:
        logger.debug("Zapier payload: %s", payload)

    return JsonResponse({'success': True})

