from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal


class PaymentGateway(ABC):
    """
    Abstract base class for all payment gateway implementations.
    All payment gateways must inherit from this class.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the payment gateway with configuration.

        Args:
            config: Dictionary containing API keys and other configuration
        """
        self.config = config
        self.is_test_mode = config.get('is_test_mode', True)

    @abstractmethod
    def process_payment(self, amount: Decimal, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a payment transaction.

        Args:
            amount: The amount to charge
            currency: Currency code (e.g., 'USD')
            metadata: Additional payment information (user_id, email, etc.)

        Returns:
            Dict containing:
                - success: bool
                - transaction_id: str (gateway's transaction ID)
                - message: str
                - data: Dict (raw response from gateway)
        """
        pass

    @abstractmethod
    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify a payment transaction status.

        Args:
            transaction_id: The gateway's transaction ID

        Returns:
            Dict containing:
                - success: bool
                - status: str ('completed', 'pending', 'failed')
                - amount: Decimal
                - message: str
        """
        pass

    @abstractmethod
    def refund_payment(self, transaction_id: str, amount: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Refund a payment transaction.

        Args:
            transaction_id: The gateway's transaction ID
            amount: Amount to refund (None for full refund)

        Returns:
            Dict containing:
                - success: bool
                - refund_id: str
                - message: str
        """
        pass

    def validate_config(self) -> bool:
        """
        Validate that the gateway configuration is complete and correct.

        Returns:
            bool: True if configuration is valid
        """
        required_keys = self.get_required_config_keys()
        for key in required_keys:
            if key not in self.config or not self.config[key]:
                return False
        return True

    @abstractmethod
    def get_required_config_keys(self) -> list:
        """
        Return list of required configuration keys for this gateway.

        Returns:
            List of required config key names
        """
        pass

    def format_amount(self, amount: Decimal, currency: str = 'USD') -> int:
        """
        Convert decimal amount to gateway's expected format (usually cents).

        Args:
            amount: Decimal amount
            currency: Currency code

        Returns:
            Amount in smallest currency unit (cents for USD)
        """
        return int(amount * 100)

    def parse_amount(self, amount: int, currency: str = 'USD') -> Decimal:
        """
        Convert gateway amount (cents) back to decimal.

        Args:
            amount: Amount in smallest currency unit
            currency: Currency code

        Returns:
            Decimal amount
        """
        return Decimal(amount) / 100
