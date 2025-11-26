"""
Payment Receipt Generator Service
Generates professional PDF receipts for payments with QR codes
"""
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from io import BytesIO
import logging
import base64
from datetime import datetime
from shared_core.utils import get_company_receipt_data

# Optional qrcode import - gracefully handle if not installed
try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False
    logging.warning("qrcode library not installed - QR code generation disabled")

logger = logging.getLogger(__name__)


class PaymentReceiptService:
    """Service for generating payment receipts"""
    
    @staticmethod
    def generate_qr_code(data):
        """
        Generate QR code for payment verification
        Returns base64 encoded image or None if qrcode not available
        """
        if not HAS_QRCODE:
            logger.warning("QR code generation skipped - qrcode library not installed")
            return None
            
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None
    
    @staticmethod
    def format_payment_method(method):
        """Format payment method name for display"""
        method_names = {
            'PayPal': 'PayPal',
            'paypal': 'PayPal',
            'Stripe': 'Credit/Debit Card (Stripe)',
            'stripe': 'Credit/Debit Card (Stripe)',
            'mpesa': 'M-Pesa',
            'MPESA': 'M-Pesa',
            'cashapp': 'CashApp',
            'CashApp': 'CashApp',
            'zelle': 'Zelle',
            'Zelle': 'Zelle',
            'venmo': 'Venmo',
            'Venmo': 'Venmo',
        }
        return method_names.get(method, method.title())
    
    @classmethod
    def generate_receipt_data(cls, payment_history):
        """
        Generate receipt data dictionary from Payment_History object
        """
        try:
            # Generate verification URL (for QR code)
            verification_url = f"https://codamakutano.herokuapp.com/finance/verify-payment/{payment_history.id}/"
            
            # Generate QR code
            qr_code_data = verification_url
            qr_code_image = cls.generate_qr_code(qr_code_data)
            
            # Format payment method
            payment_method_display = cls.format_payment_method(
                payment_history.payment_method
            )
            
            # Calculate fees (if applicable)
            processing_fee = 0
            if hasattr(payment_history, 'payment_fees') and hasattr(payment_history, 'down_payment'):
                # Processing fee might be included in the payment
                processing_fee = 0  # TODO: Calculate actual processing fees
            
            receipt_data = {
                # Receipt Info
                'receipt_number': f"RCPT-{payment_history.id}-{datetime.now().strftime('%Y%m')}",
                'issue_date': timezone.now(),
                
                # Payment Info
                'payment_id': payment_history.id,
                'payment_reference': f"PAY-{payment_history.id}",
                'payment_date': payment_history.payment_date if hasattr(payment_history, 'payment_date') else payment_history.contract_submitted_date,
                'payment_method': payment_method_display,
                'transaction_id': getattr(payment_history, 'transaction_id', 'N/A'),
                
                # Amount Details
                'amount_paid': payment_history.payment_fees,
                'processing_fee': processing_fee,
                'total_amount': payment_history.payment_fees + processing_fee,
                'currency': getattr(payment_history, 'currency', 'USD'),
                
                # Customer Info
                'customer_name': payment_history.customer.get_full_name() or payment_history.customer.username,
                'customer_email': payment_history.customer.email,
                'customer_id': payment_history.customer.id,
                
                # Payment Status
                'status': getattr(payment_history, 'status', 'completed').upper(),
                'notes': getattr(payment_history, 'notes', ''),
                
                # Verification
                'verification_url': verification_url,
                'qr_code': qr_code_image,
            }
            
            # Get company branding data (from payment_history.company or defaults)
            company = getattr(payment_history, 'company', None)
            company_data = get_company_receipt_data(company)
            receipt_data.update(company_data)
            
            return receipt_data
            
        except Exception as e:
            logger.error(f"Error generating receipt data: {e}")
            raise
    
    @classmethod
    def generate_receipt_html(cls, payment_history):
        """
        Generate HTML receipt (can be converted to PDF or sent as email)
        """
        try:
            receipt_data = cls.generate_receipt_data(payment_history)
            
            html_content = render_to_string(
                'finance/receipts/payment_receipt.html',
                receipt_data
            )
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error generating receipt HTML: {e}")
            raise
    
    @classmethod
    def send_receipt_email(cls, payment_history):
        """
        Send receipt via email to customer
        """
        try:
            from mail.custom_email import send_email
            
            receipt_data = cls.generate_receipt_data(payment_history)
            
            subject = f"Payment Receipt - {receipt_data['receipt_number']}"
            
            send_email(
                category=payment_history.customer.category if hasattr(payment_history.customer, 'category') else 'client',
                to_email=[payment_history.customer.email],
                subject=subject,
                html_template='finance/receipts/payment_receipt_email.html',
                context=receipt_data
            )
            
            logger.info(f"Receipt emailed to {payment_history.customer.email} for payment {payment_history.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending receipt email: {e}")
            return False
    
    @classmethod
    def generate_receipt_pdf(cls, payment_history):
        """
        Generate PDF receipt (requires reportlab or weasyprint)
        For now, returns HTML that can be printed to PDF
        """
        # TODO: Implement PDF generation with reportlab when needed
        # For now, return HTML that browsers can print to PDF
        return cls.generate_receipt_html(payment_history)

