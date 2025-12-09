from django.conf import settings


def payment_settings(request):
    """Expose minimal payment settings to templates.

    Returns public keys and client IDs needed by client-side JS (Stripe/PayPal).
    This is safe for local dev because values are non-secret (publishable keys).
    """
    return {
        'STRIPE_PUBLIC_KEY': getattr(settings, 'STRIPE_PUBLIC_KEY', ''),
        'PAYPAL_CLIENT_ID': getattr(settings, 'PAYPAL_CLIENT_ID', ''),
        'PAYPAL_MODE': getattr(settings, 'PAYPAL_MODE', 'sandbox'),
    }
