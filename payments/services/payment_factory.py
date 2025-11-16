from typing import Optional
from ..models import PaymentGatewayConfig
from .stripe_service import StripePaymentGateway
from .paypal_service import PayPalPaymentGateway
from .mpesa_service import MPesaPaymentGateway
from .base import PaymentGateway


class PaymentGatewayFactory:
    """Factory class to create payment gateway instances"""

    GATEWAY_CLASSES = {
        'stripe': StripePaymentGateway,
        'paypal': PayPalPaymentGateway,
        'mpesa': MPesaPaymentGateway,
    }

    @classmethod
    def create_gateway(cls, gateway_name: str) -> Optional[PaymentGateway]:
        """
        Create a payment gateway instance from database configuration.

        Args:
            gateway_name: Name of the gateway ('stripe', 'paypal', 'mpesa')

        Returns:
            PaymentGateway instance or None if not configured
        """
        try:
            config_obj = PaymentGatewayConfig.objects.get(gateway_name=gateway_name, is_active=True)

            config_data = config_obj.config_data.copy()
            config_data['is_test_mode'] = config_obj.is_test_mode

            gateway_class = cls.GATEWAY_CLASSES.get(gateway_name)
            if gateway_class:
                return gateway_class(config_data)

            return None

        except PaymentGatewayConfig.DoesNotExist:
            return None

    @classmethod
    def get_active_gateways(cls) -> list:
        """
        Get list of all active payment gateways.

        Returns:
            List of gateway names that are active
        """
        return list(PaymentGatewayConfig.objects.filter(is_active=True).values_list('gateway_name', flat=True))

    @classmethod
    def is_gateway_available(cls, gateway_name: str) -> bool:
        """
        Check if a specific gateway is available and active.

        Args:
            gateway_name: Name of the gateway

        Returns:
            bool: True if gateway is configured and active
        """
        return PaymentGatewayConfig.objects.filter(gateway_name=gateway_name, is_active=True).exists()
