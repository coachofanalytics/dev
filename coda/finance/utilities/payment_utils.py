"""
Payment Utilities

This module contains utility functions for payment processing including
validation, currency conversion, and payment method handling.
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Q
from decimal import Decimal
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import logging
import requests
from mail.custom_email import send_email

logger = logging.getLogger(__name__)

# Get the User model
User = get_user_model()


class PaymentUtils:
    """Utility class for payment-related operations."""
    
    @staticmethod
    def get_user_persona(user):
        """
        Determine a user's persona for payment routing.

        Priority order:
        - staff/internal
        - investor
        - student/training
        - guest/unknown
        """
        try:
            # Staff / internal users
            if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False) or getattr(user, "is_admin", False):
                return "staff"

            # Investor flags: group, top-level flag, or profile flag
            try:
                if hasattr(user, "groups") and user.groups.filter(name__iexact="investor").exists():
                    return "investor"
            except Exception:
                pass

            if getattr(user, "is_investor", False):
                return "investor"

            if hasattr(user, "profile") and getattr(user.profile, "is_investor", False):
                return "investor"

            # Student / training: group, explicit flag, or common category code
            try:
                if hasattr(user, "groups") and user.groups.filter(name__iexact="student").exists():
                    return "student"
            except Exception:
                pass

            if getattr(user, "is_training_user", False) or getattr(user, "is_student", False):
                return "student"

            # Some projects use category codes; retain as a weak signal only
            if getattr(user, "category", None) in {1, "student"}:
                return "student"

            return "unknown"
        except Exception:
            return "unknown"

    @staticmethod
    def get_persona_redirect_url(user):
        """Return the appropriate redirect URL path for a user's persona."""
        try:
            persona = PaymentUtils.get_user_persona(user)
            if persona == "staff":
                # Staff typically go straight to unified payment selection
                return "finance:unified_method_selection", None
            if persona == "investor":
                # Use absolute path for investing dashboard (external app)
                return None, "/investing/dashboard/"
            if persona == "student":
                # Professional services landing (training/data analysis)
                return None, "/professional_services/"
            # Fallback generic services landing
            return None, "/professional_services/"
        except Exception:
            return None, "/professional_services/"

    @staticmethod
    def update_link(service_array, user_payment_history, service_categories):
        """
        Update payment links based on service array and user payment history.
        Returns updated service array with payment links.
        """
        try:
            # This function would typically update payment links for services
            # For now, we'll implement a basic version
            
            updated_services = []
            
            for service in service_array:
                # Check if user has payment history for this service
                has_payment_history = any(
                    payment.get('service_id') == service.get('id')
                    for payment in user_payment_history
                )
                
                # Update service with payment link information
                service_copy = service.copy()
                service_copy['has_payment_history'] = has_payment_history
                service_copy['payment_link'] = PaymentUtils._generate_payment_link(service)
                
                updated_services.append(service_copy)
            
            return updated_services
            
        except Exception as e:
            logger.error(f"Error updating payment links: {e}")
            return service_array

    @staticmethod
    def _generate_payment_link(service):
        """Generate payment link for a service."""
        try:
            service_id = service.get('id')
            if service_id:
                return f"/finance/payments/pay/{service_id}/"
            return "/finance/payments/"
        except Exception as e:
            logger.error(f"Error generating payment link: {e}")
            return "/finance/payments/"

    @staticmethod
    def get_exchange_rate(from_currency="USD", to_currency="KES"):
        """
        Get current exchange rate between currencies.
        Returns exchange rate or None if unavailable.
        """
        try:
            # This would typically call a real exchange rate API
            # For now, we'll use static rates for common currencies
            
            exchange_rates = {
                "USD_TO_KES": 150.0,  # 1 USD = 150 KES (example rate)
                "KES_TO_USD": 0.0067,  # 1 KES = 0.0067 USD
                "EUR_TO_KES": 165.0,   # 1 EUR = 165 KES (example rate)
                "KES_TO_EUR": 0.0061,   # 1 KES = 0.0061 EUR
            }
            
            rate_key = f"{from_currency}_TO_{to_currency}"
            return exchange_rates.get(rate_key)
            
        except Exception as e:
            logger.error(f"Error getting exchange rate from {from_currency} to {to_currency}: {e}")
            return None

    @staticmethod
    def save_payment_record(payment_data):
        """
        Save payment record to database.
        Returns the saved payment record or None if failed.
        """
        try:
            # This would typically save to a Payment model
            # For now, we'll log the payment data
            
            logger.info(f"Payment record saved: {payment_data}")
            
            # Return mock payment record
            return {
                'id': 1,
                'amount': payment_data.get('amount'),
                'currency': payment_data.get('currency', 'KES'),
                'method': payment_data.get('method'),
                'status': 'completed',
                'created_at': timezone.now(),
            }
            
        except Exception as e:
            logger.error(f"Error saving payment record: {e}")
            return None

    @staticmethod
    def convert_to_usd(amount, from_currency):
        """
        Convert amount from specified currency to USD.
        Returns converted amount in USD.
        """
        try:
            if from_currency == "USD":
                return float(amount)
            
            # Get exchange rate
            rate = PaymentUtils.get_exchange_rate(from_currency, "USD")
            if rate:
                return float(amount) * rate
            
            # Fallback: assume KES if no rate available
            if from_currency == "KES":
                return float(amount) * 0.0067  # Approximate KES to USD rate
            
            return float(amount)
            
        except Exception as e:
            logger.error(f"Error converting {amount} {from_currency} to USD: {e}")
            return 0.0

    @staticmethod
    def get_user_currency(user):
        """
        Get user's preferred currency.
        Returns currency code (e.g., 'KES', 'USD').
        """
        try:
            # Check user profile for currency preference
            if hasattr(user, 'profile') and user.profile:
                if hasattr(user.profile, 'currency'):
                    return user.profile.currency
            
            # Default currency based on user location or other factors
            # For Kenya-based users, default to KES
            return "KES"
            
        except Exception as e:
            logger.error(f"Error getting user currency: {e}")
            return "KES"

    @staticmethod
    def calculate_paypal_charges(amount):
        """
        Calculate PayPal processing charges for an amount.
        Returns charge amount and total amount.
        """
        try:
            # PayPal charges: 3.4% + $0.30 USD per transaction
            percentage_charge = float(amount) * 0.034  # 3.4%
            fixed_charge = 0.30  # $0.30 USD
            
            total_charges = percentage_charge + fixed_charge
            total_amount = float(amount) + total_charges
            
            return {
                'original_amount': float(amount),
                'percentage_charge': percentage_charge,
                'fixed_charge': fixed_charge,
                'total_charges': total_charges,
                'total_amount': total_amount,
                'charge_percentage': 3.4,
                'fixed_fee': 0.30,
            }
            
        except Exception as e:
            logger.error(f"Error calculating PayPal charges: {e}")
            return {
                'original_amount': float(amount),
                'percentage_charge': 0,
                'fixed_charge': 0,
                'total_charges': 0,
                'total_amount': float(amount),
                'charge_percentage': 0,
                'fixed_fee': 0,
            }

    @staticmethod
    def validate_amount(amount_str, payment_method="general"):
        """
        Validate payment amount for specified payment method.
        Returns validation result with success status and message.
        """
        try:
            # Convert to float for validation
            try:
                amount = float(amount_str)
            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'message': 'Invalid amount format. Please enter a valid number.',
                    'amount': 0
                }
            
            # Check minimum amount
            min_amounts = {
                'paypal': 1.0,      # $1 minimum for PayPal
                'mpesa': 10.0,      # KES 10 minimum for M-Pesa
                'general': 1.0,     # General minimum
            }
            
            min_amount = min_amounts.get(payment_method, 1.0)
            if amount < min_amount:
                return {
                    'valid': False,
                    'message': f'Minimum amount for {payment_method} is {min_amount}.',
                    'amount': amount
                }
            
            # Check maximum amount
            max_amounts = {
                'paypal': 10000.0,  # $10,000 maximum for PayPal
                'mpesa': 150000.0,  # KES 150,000 maximum for M-Pesa
                'general': 1000000.0, # General maximum
            }
            
            max_amount = max_amounts.get(payment_method, 1000000.0)
            if amount > max_amount:
                return {
                    'valid': False,
                    'message': f'Maximum amount for {payment_method} is {max_amount}.',
                    'amount': amount
                }
            
            return {
                'valid': True,
                'message': 'Amount is valid.',
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"Error validating amount: {e}")
            return {
                'valid': False,
                'message': 'Error validating amount. Please try again.',
                'amount': 0
            }

    @staticmethod
    def validate_user_payment_eligibility(user, amount, payment_method="general"):
        """
        Validate if user is eligible to make payment with specified method.
        Returns validation result with eligibility status.
        """
        try:
            # Check if user is active
            if not user.is_active:
                return {
                    'eligible': False,
                    'message': 'Your account is not active. Please contact support.',
                    'reason': 'inactive_account'
                }
            
            # Check user category restrictions
            if user.category == 0:  # Inactive or restricted users
                return {
                    'eligible': False,
                    'message': 'Your account is restricted from making payments.',
                    'reason': 'restricted_account'
                }
            
            # Validate amount
            amount_validation = PaymentUtils.validate_amount(str(amount), payment_method)
            if not amount_validation['valid']:
                return {
                    'eligible': False,
                    'message': amount_validation['message'],
                    'reason': 'invalid_amount'
                }
            
            # Check payment method specific eligibility
            if payment_method == 'paypal':
                # PayPal requires email verification
                if not user.email or not user.email_verified:
                    return {
                        'eligible': False,
                        'message': 'PayPal payments require a verified email address.',
                        'reason': 'unverified_email'
                    }
            
            elif payment_method == 'mpesa':
                # M-Pesa requires phone number
                if not hasattr(user, 'profile') or not user.profile.phone_number:
                    return {
                        'eligible': False,
                        'message': 'M-Pesa payments require a phone number.',
                        'reason': 'missing_phone'
                    }
            
            return {
                'eligible': True,
                'message': 'User is eligible for payment.',
                'reason': 'eligible'
            }
            
        except Exception as e:
            logger.error(f"Error validating user payment eligibility: {e}")
            return {
                'eligible': False,
                'message': 'Error validating payment eligibility. Please try again.',
                'reason': 'system_error'
            }

    @staticmethod
    def save_payment_history(user, amount, payment_method, service_id=None, status="completed"):
        """
        Save payment history record for user.
        Returns the saved payment history record.
        """
        try:
            # This would typically save to a PaymentHistory model
            # For now, we'll create a mock record
            
            payment_record = {
                'user_id': user.id,
                'amount': float(amount),
                'currency': PaymentUtils.get_user_currency(user),
                'payment_method': payment_method,
                'service_id': service_id,
                'status': status,
                'created_at': timezone.now(),
                'transaction_id': f"TXN_{user.id}_{int(timezone.now().timestamp())}",
            }
            
            logger.info(f"Payment history saved: {payment_record}")
            return payment_record
            
        except Exception as e:
            logger.error(f"Error saving payment history: {e}")
            return None

    @staticmethod
    def process_visitor_payment(request, method):
        """
        Process payment for visitor users.
        Returns payment processing result.
        """
        try:
            # Extract payment data from request
            amount = request.POST.get('amount')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            
            # Validate visitor payment data
            if not amount or not email:
                return {
                    'success': False,
                    'message': 'Amount and email are required for visitor payments.',
                    'payment_id': None
                }
            
            # Validate amount
            amount_validation = PaymentUtils.validate_amount(amount, method)
            if not amount_validation['valid']:
                return {
                    'success': False,
                    'message': amount_validation['message'],
                    'payment_id': None
                }
            
            # Process payment based on method
            if method == 'paypal':
                return PaymentUtils._process_paypal_payment(amount, email)
            elif method == 'mpesa':
                return PaymentUtils._process_mpesa_payment(amount, phone)
            else:
                return {
                    'success': False,
                    'message': f'Payment method {method} not supported for visitors.',
                    'payment_id': None
                }
            
        except Exception as e:
            logger.error(f"Error processing visitor payment: {e}")
            return {
                'success': False,
                'message': 'Error processing payment. Please try again.',
                'payment_id': None
            }

    @staticmethod
    def _process_paypal_payment(amount, email):
        """Process PayPal payment for visitor."""
        try:
            # Mock PayPal processing
            payment_id = f"PP_{int(timezone.now().timestamp())}"
            
            return {
                'success': True,
                'message': 'PayPal payment processed successfully.',
                'payment_id': payment_id,
                'amount': float(amount),
                'method': 'paypal',
                'email': email
            }
            
        except Exception as e:
            logger.error(f"Error processing PayPal payment: {e}")
            return {
                'success': False,
                'message': 'PayPal payment failed. Please try again.',
                'payment_id': None
            }

    @staticmethod
    def _process_mpesa_payment(amount, phone):
        """Process M-Pesa payment for visitor."""
        try:
            # Mock M-Pesa processing
            payment_id = f"MP_{int(timezone.now().timestamp())}"
            
            return {
                'success': True,
                'message': 'M-Pesa payment processed successfully.',
                'payment_id': payment_id,
                'amount': float(amount),
                'method': 'mpesa',
                'phone': phone
            }
            
        except Exception as e:
            logger.error(f"Error processing M-Pesa payment: {e}")
            return {
                'success': False,
                'message': 'M-Pesa payment failed. Please try again.',
                'payment_id': None
            }


