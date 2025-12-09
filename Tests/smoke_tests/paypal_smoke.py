"""Automated smoke script for PayPal server-side checks.

Run this from repository root:
  & C:/path/to/venv/Scripts/Activate.ps1
  python Tests/smoke_tests/paypal_smoke.py

What it does:
- Loads Django and reads `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` from `.env`
- Verifies credentials exist and prints sandbox/test guidance
"""
import os
import sys

# Ensure project root is on sys.path so `config` package can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from decouple import config


def main():
    client_id = config('PAYPAL_CLIENT_ID', default='')
    client_secret = config('PAYPAL_CLIENT_SECRET', default='')
    mode = config('PAYPAL_MODE', default='sandbox')

    if not client_id or not client_secret:
        print('ERROR: PAYPAL_CLIENT_ID or PAYPAL_CLIENT_SECRET not found in .env. Aborting.')
        sys.exit(2)

    print('PayPal credentials found.')
    print(f'PAYPAL_MODE={mode}')

    print('\nTo perform a full PayPal redirect test:')
    print('- Start Django server: python manage.py runserver')
    print('- Open the PayPal deposit page in the app and follow the sandbox redirect/approve flow')
    print("- If you need IPN/webhook tests, expose your server (ngrok) and configure PayPal sandbox webhooks")


if __name__ == '__main__':
    main()
