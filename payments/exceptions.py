"""
Custom Exceptions for Payments App
"""


class PaymentError(Exception):
    """Base exception for payment-related errors"""
    pass


class InsufficientFundsError(PaymentError):
    """Raised when wallet has insufficient funds"""
    pass


class PaymentGatewayError(PaymentError):
    """Raised when payment gateway returns an error"""

    def __init__(self, gateway: str, message: str, error_data: dict = None):
        self.gateway = gateway
        self.error_data = error_data or {}
        super().__init__(f"{gateway}: {message}")


class TransactionNotFoundError(PaymentError):
    """Raised when transaction cannot be found"""
    pass


class InvalidTransactionStateError(PaymentError):
    """Raised when transaction is in invalid state for operation"""
    pass


class SubscriptionError(Exception):
    """Base exception for subscription-related errors"""
    pass


class SubscriptionNotFoundError(SubscriptionError):
    """Raised when subscription cannot be found"""
    pass


class SubscriptionExpiredError(SubscriptionError):
    """Raised when subscription has expired"""
    pass


class InvalidSubscriptionStateError(SubscriptionError):
    """Raised when subscription is in invalid state for operation"""
    pass


class SubscriptionAlreadyActiveError(SubscriptionError):
    """Raised when user already has an active subscription"""
    pass


class WalletError(Exception):
    """Base exception for wallet-related errors"""
    pass


class WalletNotFoundError(WalletError):
    """Raised when wallet cannot be found"""
    pass


class InvalidAmountError(PaymentError):
    """Raised when amount is invalid (negative, zero, or exceeds limits)"""
    pass


class PaymentMethodNotSupportedError(PaymentError):
    """Raised when payment method is not supported or disabled"""
    pass


class RefundError(PaymentError):
    """Raised when refund operation fails"""
    pass


class InvoiceError(Exception):
    """Base exception for invoice-related errors"""
    pass


class InvoiceNotFoundError(InvoiceError):
    """Raised when invoice cannot be found"""
    pass
