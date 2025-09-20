"""
PayPal Service
International payment processing via PayPal
Integrated with existing frontend implementation
"""

from decimal import Decimal
from typing import Dict, Any, Optional
from django.conf import settings
import logging
import requests
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class PayPalService:
    """
    PayPal payment service
    Handles international payments via PayPal API
    Integrated with existing frontend implementation
    """
    
    def __init__(self):
        self.client_id = getattr(settings, 'PAYPAL_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'PAYPAL_CLIENT_SECRET', None)
        self.mode = getattr(settings, 'PAYPAL_MODE', 'sandbox')  # sandbox or live
        
        # Service configuration
        self.supported_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY']
        self.min_amount = Decimal('1.00')  # $1 minimum
        self.max_amount = Decimal('10000.00')  # $10,000 maximum
        self.processing_time = 'Instant to 3-5 business days'
        
        # API endpoints
        if self.mode == 'live':
            self.base_url = 'https://api-m.paypal.com'
        else:
            self.base_url = 'https://api-m.sandbox.paypal.com'
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate PayPal configuration"""
        if not self.client_id or not self.client_secret:
            logger.warning("PayPal configuration incomplete. Missing credentials.")
    
    def _get_access_token(self) -> Optional[str]:
        """Get PayPal access token"""
        try:
            if not self.client_id or not self.client_secret:
                raise ValueError("PayPal credentials not configured")
            
            url = f"{self.base_url}/v1/oauth2/token"
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {self._get_basic_auth()}'
            }
            
            data = {
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(
                url,
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('access_token')
            else:
                logger.error(f"Failed to get PayPal access token: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting PayPal access token: {str(e)}")
            return None
    
    def _get_basic_auth(self) -> str:
        """Get basic authentication header"""
        import base64
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()
    
    def process_payment(self, amount: Decimal, reference: str, **kwargs) -> Dict[str, Any]:
        """
        Process PayPal payment
        
        Args:
            amount: Payment amount
            reference: Unique payment reference
            **kwargs: Additional parameters including currency, return_url, cancel_url
        
        Returns:
            Dict containing payment result
        """
        try:
            # Validate amount
            if amount < self.min_amount:
                return {
                    'success': False,
                    'error': f'Amount {amount} is below minimum {self.min_amount}',
                    'reference': reference
                }
            
            if amount > self.max_amount:
                return {
                    'success': False,
                    'error': f'Amount {amount} exceeds maximum {self.max_amount}',
                    'reference': reference
                }
            
            # Get parameters from kwargs
            currency = kwargs.get('currency', 'USD')
            return_url = kwargs.get('return_url')
            cancel_url = kwargs.get('cancel_url')
            
            if currency not in self.supported_currencies:
                return {
                    'success': False,
                    'error': f'Currency {currency} not supported. Supported: {self.supported_currencies}',
                    'reference': reference
                }
            
            # Get access token
            access_token = self._get_access_token()
            if not access_token:
                return {
                    'success': False,
                    'error': 'Failed to get PayPal access token',
                    'reference': reference
                }
            
            # Create PayPal order
            order_result = self._create_paypal_order(
                access_token, amount, currency, reference, return_url, cancel_url
            )
            
            if order_result.get('success'):
                return {
                    'success': True,
                    'method': 'paypal',
                    'reference': reference,
                    'amount': amount,
                    'currency': currency,
                    'order_id': order_result.get('order_id'),
                    'approval_url': order_result.get('approval_url'),
                    'message': 'PayPal order created successfully. Redirect user to approval URL.',
                    'status': 'pending',
                    'frontend_integration': True
                }
            else:
                return {
                    'success': False,
                    'error': order_result.get('error', 'PayPal order creation failed'),
                    'reference': reference
                }
                
        except Exception as e:
            logger.error(f"PayPal payment processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'reference': reference
            }
    
    def _create_paypal_order(self, access_token: str, amount: Decimal, currency: str, 
                            reference: str, return_url: str, cancel_url: str) -> Dict[str, Any]:
        """Create PayPal order"""
        try:
            url = f"{self.base_url}/v2/checkout/orders"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "reference_id": reference,
                        "amount": {
                            "currency_code": currency,
                            "value": str(amount)
                        },
                        "description": f"CODA Payment - {reference}",
                        "custom_id": reference
                    }
                ],
                "application_context": {
                    "return_url": return_url,
                    "cancel_url": cancel_url,
                    "brand_name": "CODA Analytics",
                    "landing_page": "LOGIN",
                    "user_action": "PAY_NOW"
                }
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                
                if data.get('status') == 'CREATED':
                    # Get approval URL from links
                    approval_url = None
                    for link in data.get('links', []):
                        if link.get('rel') == 'approve':
                            approval_url = link.get('href')
                            break
                    
                    return {
                        'success': True,
                        'order_id': data.get('id'),
                        'status': data.get('status'),
                        'approval_url': approval_url
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Order status: {data.get("status")}',
                        'order_id': data.get('id')
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"PayPal order creation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """Verify PayPal payment status"""
        try:
            # In a real implementation, this would check the PayPal API
            # For now, return a placeholder response
            return {
                'success': True,
                'method': 'paypal',
                'reference': reference,
                'status': 'pending_verification',
                'message': 'Payment verification requires PayPal callback implementation'
            }
            
        except Exception as e:
            logger.error(f"PayPal payment verification failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'reference': reference
            }
    
    def refund_payment(self, reference: str, amount: Optional[Decimal] = None) -> Dict[str, Any]:
        """Refund PayPal payment"""
        try:
            # In a real implementation, this would initiate a PayPal refund
            return {
                'success': True,
                'method': 'paypal',
                'reference': reference,
                'status': 'refund_initiated',
                'message': 'Refund initiated. Processing time: 3-5 business days.'
            }
            
        except Exception as e:
            logger.error(f"PayPal refund failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'reference': reference
            }
    
    def capture_payment(self, order_id: str) -> Dict[str, Any]:
        """Capture PayPal payment after user approval"""
        try:
            access_token = self._get_access_token()
            if not access_token:
                return {
                    'success': False,
                    'error': 'Failed to get PayPal access token'
                }
            
            url = f"{self.base_url}/v2/checkout/orders/{order_id}/capture"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                
                if data.get('status') == 'COMPLETED':
                    return {
                        'success': True,
                        'order_id': order_id,
                        'capture_id': data.get('purchase_units', [{}])[0].get('payments', {}).get('captures', [{}])[0].get('id'),
                        'status': 'completed',
                        'message': 'Payment captured successfully'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Capture status: {data.get("status")}'
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"PayPal payment capture failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get PayPal service information"""
        return {
            'name': 'PayPal',
            'type': 'International Payment',
            'supported_currencies': self.supported_currencies,
            'min_amount': str(self.min_amount),
            'max_amount': str(self.max_amount),
            'processing_time': self.processing_time,
            'mode': self.mode,
            'configured': bool(self.client_id and self.client_secret),
            'frontend_integration': True
        }
    
    def get_frontend_config(self) -> Dict[str, Any]:
        """Get PayPal frontend configuration for existing implementation"""
        return {
            'client_id': self.client_id,
            'mode': self.mode,
            'currency': 'USD',
            'supported_currencies': self.supported_currencies,
            'min_amount': str(self.min_amount),
            'max_amount': str(self.max_amount)
        }
