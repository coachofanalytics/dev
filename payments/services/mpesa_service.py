import requests
import base64
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from .base import PaymentGateway


class MPesaPaymentGateway(PaymentGateway):
    """M-Pesa (Safaricom) payment gateway implementation using STK Push"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.consumer_key = self.config.get('consumer_key')
        self.consumer_secret = self.config.get('consumer_secret')
        self.business_shortcode = self.config.get('business_shortcode')
        self.passkey = self.config.get('passkey')
        self.callback_url = self.config.get('callback_url')

        if self.is_test_mode:
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'

    def get_required_config_keys(self) -> list:
        return ['consumer_key', 'consumer_secret', 'business_shortcode', 'passkey', 'callback_url']

    def get_access_token(self) -> Optional[str]:
        """Get M-Pesa API access token"""
        try:
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            response = requests.get(
                url, auth=(self.consumer_key, self.consumer_secret), timeout=30
            )
            response.raise_for_status()
            return response.json().get('access_token')
        except Exception as e:
            print(f"Failed to get M-Pesa access token: {e}")
            return None

    def generate_password(self, timestamp: str) -> str:
        """Generate M-Pesa STK Push password"""
        data_to_encode = f"{self.business_shortcode}{self.passkey}{timestamp}"
        return base64.b64encode(data_to_encode.encode()).decode('utf-8')

    def process_payment(self, amount: Decimal, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate M-Pesa STK Push payment"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'transaction_id': None, 'message': "Failed to get access token", 'data': {}}

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = self.generate_password(timestamp)

            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

            phone_number = metadata.get('phone_number', '').replace('+', '')
            if not phone_number.startswith('254'):
                phone_number = '254' + phone_number.lstrip('0')

            payload = {
                'BusinessShortCode': self.business_shortcode, 'Password': password, 'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline', 'Amount': int(amount),
                'PartyA': phone_number, 'PartyB': self.business_shortcode, 'PhoneNumber': phone_number,
                'CallBackURL': self.callback_url, 'AccountReference': metadata.get('reference', 'Payment'),
                'TransactionDesc': metadata.get('description', 'Payment'),
            }

            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()

            if result.get('ResponseCode') == '0':
                return {'success': True, 'transaction_id': result.get('CheckoutRequestID'),
                        'merchant_request_id': result.get('MerchantRequestID'),
                        'message': "STK Push sent successfully", 'data': result}
            else:
                return {'success': False, 'transaction_id': None,
                        'message': result.get('ResponseDescription', 'STK Push failed'), 'data': result}

        except Exception as e:
            return {'success': False, 'transaction_id': None, 'message': f"M-Pesa error: {str(e)}", 'data': {'error': str(e)}}

    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Query M-Pesa STK Push transaction status"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'status': 'failed', 'message': "Failed to get access token", 'data': {}}

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = self.generate_password(timestamp)

            url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

            payload = {'BusinessShortCode': self.business_shortcode, 'Password': password,
                      'Timestamp': timestamp, 'CheckoutRequestID': transaction_id}

            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()

            result_code = result.get('ResultCode', '1')
            status_mapping = {'0': 'completed', '1032': 'failed', '1': 'pending'}

            return {'success': True, 'status': status_mapping.get(str(result_code), 'pending'),
                   'amount': Decimal(result.get('Amount', 0)) if result.get('Amount') else Decimal('0'),
                   'currency': 'KES', 'message': result.get('ResultDesc', 'Query successful'), 'data': result}

        except Exception as e:
            return {'success': False, 'status': 'failed', 'message': f"Verification failed: {str(e)}", 'data': {'error': str(e)}}

    def refund_payment(self, transaction_id: str, amount: Optional[Decimal] = None) -> Dict[str, Any]:
        """M-Pesa refunds require special authorization"""
        return {'success': False, 'refund_id': None,
                'message': "M-Pesa refunds require manual processing", 'data': {}}
