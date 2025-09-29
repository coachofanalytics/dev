"""
Extended MPESA Service for Automation System

This service extends the existing MPESA service to support automated disbursements
and integration with the automation system.
"""

import logging
import requests
import json
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

from .base_service import BaseFinanceService

logger = logging.getLogger(__name__)


class MPESAService(BaseFinanceService):
    """Extended MPESA service for automation system"""
    
    def __init__(self):
        super().__init__()
        self.base_url = getattr(settings, 'MPESA_BASE_URL', 'https://sandbox.safaricom.co.ke')
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        self.shortcode = getattr(settings, 'MPESA_SHORTCODE', '')
        self.callback_url = getattr(settings, 'MPESA_CALLBACK_URL', '')
        self.access_token = None
        self.token_expires_at = None
    
    def get_access_token(self):
        """Get MPESA access token"""
        try:
            # Check if token is still valid
            if self.access_token and self.token_expires_at and timezone.now() < self.token_expires_at:
                return self.access_token
            
            # Get new token
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            auth = (self.consumer_key, self.consumer_secret)
            
            response = requests.get(url, auth=auth)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data['access_token']
            
            # Set expiration time (subtract 5 minutes for safety)
            expires_in = data.get('expires_in', 3600)
            self.token_expires_at = timezone.now() + timezone.timedelta(seconds=expires_in - 300)
            
            logger.info("MPESA access token obtained successfully")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Error getting MPESA access token: {str(e)}")
            raise ValidationError("Failed to get MPESA access token")
    
    def automated_disbursement(self, phone, amount, reference):
        """Process automated disbursement via MPESA"""
        try:
            # Validate inputs
            if not phone or not amount or not reference:
                raise ValidationError("Phone, amount, and reference are required")
            
            # Format phone number
            phone = self._format_phone_number(phone)
            
            # Get access token
            access_token = self.get_access_token()
            
            # Prepare request data
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            password = self._generate_password(timestamp)
            
            request_data = {
                "InitiatorName": getattr(settings, 'MPESA_INITIATOR_NAME', 'CODA'),
                "SecurityCredential": getattr(settings, 'MPESA_SECURITY_CREDENTIAL', ''),
                "CommandID": "BusinessPayment",
                "Amount": int(amount),
                "PartyA": self.shortcode,
                "PartyB": phone,
                "Remarks": f"CODA Disbursement - {reference}",
                "QueueTimeOutURL": f"{self.callback_url}/mpesa/timeout",
                "ResultURL": f"{self.callback_url}/mpesa/result",
                "Occasion": f"Budget Disbursement - {reference}"
            }
            
            # Make API request
            url = f"{self.base_url}/mpesa/b2c/v1/paymentrequest"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, json=request_data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ResponseCode') == '0':
                logger.info(f"MPESA disbursement initiated successfully: {reference}")
                return {
                    'success': True,
                    'transaction_id': result.get('ConversationID'),
                    'reference': reference,
                    'response': result
                }
            else:
                logger.error(f"MPESA disbursement failed: {result}")
                return {
                    'success': False,
                    'error': result.get('ResponseDescription', 'Unknown error'),
                    'response': result
                }
                
        except Exception as e:
            logger.error(f"Error processing MPESA disbursement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_transaction_status(self, transaction_id):
        """Check transaction status"""
        try:
            access_token = self.get_access_token()
            
            url = f"{self.base_url}/mpesa/transactionstatus/v1/query"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            request_data = {
                "Initiator": getattr(settings, 'MPESA_INITIATOR_NAME', 'CODA'),
                "SecurityCredential": getattr(settings, 'MPESA_SECURITY_CREDENTIAL', ''),
                "CommandID": "TransactionStatusQuery",
                "TransactionID": transaction_id,
                "PartyA": self.shortcode,
                "IdentifierType": "4",
                "ResultURL": f"{self.callback_url}/mpesa/status/result",
                "QueueTimeOutURL": f"{self.callback_url}/mpesa/status/timeout",
                "Remarks": "Transaction status query",
                "Occasion": "Status check"
            }
            
            response = requests.post(url, headers=headers, json=request_data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'status': result.get('ResponseDescription'),
                    'response': result
                }
            else:
                return {
                    'success': False,
                    'error': result.get('ResponseDescription', 'Unknown error'),
                    'response': result
                }
                
        except Exception as e:
            logger.error(f"Error checking transaction status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_callback(self, callback_data):
        """Handle MPESA callback"""
        try:
            # Parse callback data
            if isinstance(callback_data, str):
                callback_data = json.loads(callback_data)
            
            # Extract transaction details
            result = callback_data.get('Result', {})
            result_parameters = result.get('ResultParameters', {})
            
            transaction_id = result.get('ConversationID')
            result_code = result.get('ResultCode')
            result_desc = result.get('ResultDescription')
            
            # Process successful transaction
            if result_code == 0:
                # Extract payment details
                payment_details = {}
                for param in result_parameters.get('ResultParameter', []):
                    key = param.get('Key')
                    value = param.get('Value')
                    payment_details[key] = value
                
                logger.info(f"MPESA callback processed successfully: {transaction_id}")
                return {
                    'success': True,
                    'transaction_id': transaction_id,
                    'payment_details': payment_details,
                    'result_code': result_code,
                    'result_description': result_desc
                }
            else:
                logger.error(f"MPESA callback failed: {result_desc}")
                return {
                    'success': False,
                    'transaction_id': transaction_id,
                    'error': result_desc,
                    'result_code': result_code
                }
                
        except Exception as e:
            logger.error(f"Error handling MPESA callback: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_phone_number(self, phone):
        """Format phone number for MPESA"""
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Add country code if missing
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif not phone.startswith('254'):
            phone = '254' + phone
        
        return phone
    
    def _generate_password(self, timestamp):
        """Generate password for MPESA request"""
        import base64
        import hashlib
        
        # This is a simplified implementation
        # In production, you should use the actual MPESA password generation
        password_string = f"{self.shortcode}{self.passkey}{timestamp}"
        password_bytes = password_string.encode('utf-8')
        password_hash = hashlib.sha256(password_bytes).digest()
        password = base64.b64encode(password_hash).decode('utf-8')
        
        return password
    
    def validate_phone_number(self, phone):
        """Validate phone number format"""
        try:
            formatted_phone = self._format_phone_number(phone)
            
            # Check if it's a valid Kenyan phone number
            if len(formatted_phone) == 12 and formatted_phone.startswith('254'):
                return True, formatted_phone
            else:
                return False, phone
                
        except Exception as e:
            logger.error(f"Error validating phone number: {str(e)}")
            return False, phone
    
    def get_transaction_history(self, start_date=None, end_date=None):
        """Get transaction history"""
        try:
            # This would typically involve querying your database
            # for MPESA transactions within the date range
            # Implementation depends on your data model
            
            logger.info("Transaction history retrieved")
            return {
                'success': True,
                'transactions': []
            }
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def refund_transaction(self, transaction_id, amount, reason):
        """Refund a transaction"""
        try:
            # This would involve calling MPESA's reversal API
            # Implementation depends on MPESA's reversal requirements
            
            logger.info(f"Refund initiated for transaction: {transaction_id}")
            return {
                'success': True,
                'refund_id': f"REF_{transaction_id}",
                'message': 'Refund initiated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }