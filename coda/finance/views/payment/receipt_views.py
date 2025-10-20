"""
Payment Receipt Views
Handle receipt generation, display, download, and email
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
import logging

from finance.models import Payment_History
from finance.services.payment_receipt_service import PaymentReceiptService

logger = logging.getLogger(__name__)


@login_required
def view_receipt(request, payment_id):
    """
    View payment receipt in browser
    User can print to PDF from browser
    """
    try:
        # Get payment history
        payment = get_object_or_404(
            Payment_History,
            id=payment_id,
            customer=request.user
        )
        
        # Generate receipt HTML
        receipt_html = PaymentReceiptService.generate_receipt_html(payment)
        
        return HttpResponse(receipt_html)
        
    except Payment_History.DoesNotExist:
        messages.error(request, 'Payment not found or you do not have permission to view this receipt.')
        return redirect('finance:payment_dashboard')
    except Exception as e:
        logger.error(f"Error viewing receipt for payment {payment_id}: {e}")
        messages.error(request, 'Error generating receipt. Please try again or contact support.')
        return redirect('finance:payment_dashboard')


@login_required
def download_receipt(request, payment_id):
    """
    Download payment receipt as PDF
    Currently returns HTML for browser print-to-PDF
    """
    try:
        # Get payment history
        payment = get_object_or_404(
            Payment_History,
            id=payment_id,
            customer=request.user
        )
        
        # Generate receipt HTML
        receipt_html = PaymentReceiptService.generate_receipt_html(payment)
        
        # Return as downloadable HTML
        response = HttpResponse(receipt_html, content_type='text/html')
        response['Content-Disposition'] = f'inline; filename="receipt_{payment_id}.html"'
        
        return response
        
    except Payment_History.DoesNotExist:
        messages.error(request, 'Payment not found.')
        return redirect('finance:payment_dashboard')
    except Exception as e:
        logger.error(f"Error downloading receipt for payment {payment_id}: {e}")
        messages.error(request, 'Error downloading receipt.')
        return redirect('finance:payment_dashboard')


@login_required
def email_receipt(request, payment_id):
    """
    Email payment receipt to customer
    """
    try:
        # Get payment history
        payment = get_object_or_404(
            Payment_History,
            id=payment_id,
            customer=request.user
        )
        
        # Send receipt email
        success = PaymentReceiptService.send_receipt_email(payment)
        
        if success:
            messages.success(
                request,
                f'Receipt emailed to {request.user.email}'
            )
        else:
            messages.warning(
                request,
                'Error sending email. Please try downloading the receipt instead.'
            )
        
        return redirect('finance:payment_dashboard')
        
    except Payment_History.DoesNotExist:
        messages.error(request, 'Payment not found.')
        return redirect('finance:payment_dashboard')
    except Exception as e:
        logger.error(f"Error emailing receipt for payment {payment_id}: {e}")
        messages.error(request, 'Error sending receipt email.')
        return redirect('finance:payment_dashboard')


def verify_payment_receipt(request, payment_id):
    """
    Public endpoint to verify payment receipt authenticity
    Accessed via QR code scan
    """
    try:
        payment = get_object_or_404(Payment_History, id=payment_id)
        
        context = {
            'payment': payment,
            'receipt_number': f"RCPT-{payment.id}-{payment.payment_date.strftime('%Y%m') if hasattr(payment, 'payment_date') else timezone.now().strftime('%Y%m')}",
            'verified': True,
            'verification_date': timezone.now(),
        }
        
        return render(request, 'finance/receipts/receipt_verification.html', context)
        
    except Payment_History.DoesNotExist:
        context = {
            'verified': False,
            'error': 'Receipt not found or invalid'
        }
        return render(request, 'finance/receipts/receipt_verification.html', context)

