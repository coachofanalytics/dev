"""Automated smoke script for Stripe server-side checks.

Run this from repository root (PowerShell examples included):
  & C:/path/to/venv/Scripts/Activate.ps1
  python Tests/smoke_tests/stripe_smoke.py

What it does:
- Loads Django settings and `.env` via decouple
- Verifies Stripe secret key is available
- Creates a PaymentIntent (amount $1.00) using the Stripe SDK and prints result
- Optionally attempts to call `stripe` CLI to trigger a webhook (only if stripe CLI available)

Note: This script does not depend on client-side or webhooks to succeed; it only verifies server-side API calls.
"""
import os
import sys
import json
import subprocess

# Ensure project root is on sys.path so `config` package can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from decouple import config

try:
    import stripe
except Exception as exc:
    print('stripe SDK not installed. Install with: pip install stripe')
    raise


def main():
    sk = config('STRIPE_TEST_SECRET_KEY', default='')
    if not sk:
        print('ERROR: STRIPE_TEST_SECRET_KEY not found in .env. Aborting.')
        sys.exit(2)

    stripe.api_key = sk

    print('Creating a test PaymentIntent (USD $1.00)...')
    try:
        pi = stripe.PaymentIntent.create(
            amount=100,
            currency='usd',
            payment_method_types=['card'],
            description='Smoke test PaymentIntent',
        )
    except Exception as exc:
        print('Stripe API call failed:', exc)
        sys.exit(3)

    print('PaymentIntent created:')
    print(json.dumps({'id': pi.id, 'status': pi.status, 'amount': pi.amount}, indent=2))

    # Check for stripe CLI and offer to trigger a test event (non-blocking)
    try:
        subprocess.run(['stripe', '--version'], check=True, stdout=subprocess.DEVNULL)
        print('\nstripe CLI detected. You can trigger a webhook event using:')
        print(f"stripe trigger payment_intent.succeeded --forward-to http://localhost:8000/webhooks/stripe/\n(ensure your server and stripe listen are running)")
    except Exception:
        print('\nstripe CLI not detected. To exercise webhooks locally, install the stripe CLI and run:')
        print('  https://stripe.com/docs/stripe-cli')


if __name__ == '__main__':
    main()
