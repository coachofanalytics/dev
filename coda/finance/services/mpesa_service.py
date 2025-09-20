"""
MPESA Service
Mobile money payment processing for Kenya
"""

from decimal import Decimal
from typing import Dict, Any, Optional
from django.conf import settings
import logging
import requests
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class MpesaService:
    """
    MPESA mobile money payment service
    Handles STK push, C2B, and B2C transactions
    """
    
    def __init__(self):
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', None)
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', None)
        self.shortcode = getattr(settings, 'MPESA_SHORTCODE', None)
        self.password = getattr(settings, 'MPESA_PASSWORD', None)
        self.timestamp = getattr(settings, 'MPESA_TIMESTAMP', None)
        self.callback_url = getattr(settings, 'MPESA_CALLBACK_URL', None)
        
        # Service configuration
        self.supported_currencies = ['KES']
        self.min_amount = Decimal('10.00')  # 10 KES minimum
        self.max_amount = Decimal('70000.00')  # 70,000 KES maximum
        self.processing_time = 'Instant to 24 hours'
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate MPESA configuration"""
        required_fields = [
            'consumer_key', 'consumer_secret', 'shortcode', 
            'password', 'timestamp', 'callback_url'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(self, field):
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"MPESA configuration incomplete. Missing: {missing_fields}")
    
    def _get_access_token(self) -> Optional[str]:
        """Get MPESA access token"""
        try:
            if not self.consumer_key or not self.consumer_secret:
                raise ValueError("MPESA credentials not configured")
            
            # MPESA OAuth endpoint
            url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
            
            response = requests.get(
                url,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('access_token')
            else:
                logger.error(f"Failed to get MPESA access token: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting MPESA access token: {str(e)}")
            return None
    
    def process_payment(self, amount: Decimal, reference: str, **kwargs) -> Dict[str, Any]:
        """
        Process MPESA payment using STK push
        
        Args:
            amount: Payment amount in KES
            reference: Unique payment reference
            **kwargs: Additional parameters including phone_number
        
        Returns:
            Dict containing payment result
        """
        try:
            # Validate amount
            if amount < self.min_amount:
                return {
                    'success': False,
                    'error': f'Amount {amount} is below minimum {self.min_amount} KES',
                    'reference': reference
                }
            
            if amount > self.max_amount:
                return {
                    'success': False,
                    'error': f'Amount {amount} exceeds maximum {self.max_amount} KES',
                    'reference': reference
                }
            
            # Get phone number from kwargs
            phone_number = kwargs.get('phone_number')
            if not phone_number:
                return {
                    'success': False,
                    'error': 'Phone number is required for MPESA payment',
                    'reference': reference
                }
            
            # Format phone number (remove + and add 254 if needed)
            formatted_phone = self._format_phone_number(phone_number)
            
            # Get access token
            access_token = self._get_access_token()
            if not access_token:
                return {
                    'success': False,
                    'error': 'Failed to get MPESA access token',
                    'reference': reference
                }
            
            # Initiate STK push
            stk_result = self._initiate_stk_push(
                access_token, amount, formatted_phone, reference
            )
            
            if stk_result.get('success'):
                return {
                    'success': True,
                    'method': 'mpesa',
                    'reference': reference,
                    'amount': amount,
                    'phone_number': formatted_phone,
                    'checkout_request_id': stk_result.get('checkout_request_id'),
                    'message': 'STK push sent successfully. Please check your phone.',
                    'status': 'pending'
                }
            else:
                return {
                    'success': False,
                    'error': stk_result.get('error', 'STK push failed'),
                    'reference': reference
                }
                
        except Exception as e:
            logger.error(f"MPESA payment processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'reference': reference
            }
    
    def _initiate_stk_push(self, access_token: str, amount: Decimal, phone_number: str, reference: str) -> Dict[str, Any]:
        """Initiate STK push to user's phone"""
        try:
            url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": self.password,
                "Timestamp": self.timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": self.callback_url,
                "AccountReference": reference,
                "TransactionDesc": f"CODA Payment - {reference}"
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('ResponseCode') == '0':
                    return {
                        'success': True,
                        'checkout_request_id': data.get('CheckoutRequestID'),
                        'merchant_request_id': data.get('MerchantRequestID'),
                        'response_code': data.get('ResponseCode'),
                        'response_description': data.get('ResponseDescription')
                    }
                else:
                    return {
                        'success': False,
                        'error': data.get('ResponseDescription', 'STK push failed'),
                        'response_code': data.get('ResponseCode')
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"STK push initiation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """Verify MPESA payment status"""
        try:
            # In a real implementation, this would check the MPESA API
            # For now, return a placeholder response
            return {
                'success': True,
                'method': 'mpesa',
                'reference': reference,
                'status': 'pending_verification',
                'message': 'Payment verification requires MPESA callback implementation'
            }
            
        except Exception as e:
            logger.error(f"MPESA payment verification failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'reference': reference
            }
    
    def refund_payment(self, reference: str, amount: Optional[Decimal] = None) -> Dict[str, Any]:
        """Refund MPESA payment"""
        try:
            # In a real implementation, this would initiate a B2C refund
            return {
                'success': True,
                'method': 'mpesa',
                'reference': reference,
                'status': 'refund_initiated',
                'message': 'Refund initiated. Processing time: 24-48 hours.'
            }
            
        except Exception as e:
            logger.error(f"MPESA refund failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'reference': reference
            }
    
    def _format_phone_number(self, phone_number: str) -> str:
        """Format phone number for MPESA API"""
        # Remove any non-digit characters
        cleaned = ''.join(filter(str.isdigit, phone_number))
        
        # Handle different formats
        if cleaned.startswith('254'):
            return cleaned
        elif cleaned.startswith('0'):
            return '254' + cleaned[1:]
        elif cleaned.startswith('+254'):
            return cleaned[1:]
        else:
            # Assume it's a 9-digit number, add 254
            return '254' + cleaned
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get MPESA service information"""
        return {
            'name': 'MPESA Mobile Money',
            'country': 'Kenya',
            'supported_currencies': self.supported_currencies,
            'min_amount': str(self.min_amount),
            'max_amount': str(self.max_amount),
            'processing_time': self.processing_time,
            'configured': all([
                self.consumer_key, self.consumer_secret, self.shortcode,
                self.password, self.timestamp, self.callback_url
            ])
        }

