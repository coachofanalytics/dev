from django.core.management.base import BaseCommand
from decouple import config
from django.contrib.auth import get_user_model

from payments.models import PaymentGatewayConfig


class Command(BaseCommand):
    help = 'Seed PaymentGatewayConfig rows from environment variables for local development'

    def handle(self, *args, **options):
        User = get_user_model()
        admin = User.objects.filter(is_superuser=True).first()

        # Stripe
        stripe_secret = config('STRIPE_SECRET_KEY', default='')
        stripe_pub = config('STRIPE_PUBLIC_KEY', default='')
        stripe_test_secret = config('STRIPE_TEST_SECRET_KEY', default='')
        if not stripe_secret and stripe_test_secret:
            stripe_secret = stripe_test_secret

        if stripe_secret:
            config_data = {'secret_key': stripe_secret}
            if stripe_pub:
                config_data['publishable_key'] = stripe_pub

            obj, created = PaymentGatewayConfig.objects.update_or_create(
                gateway_name='stripe',
                defaults={
                    'is_active': config('ENABLE_STRIPE', default=True, cast=bool),
                    'is_test_mode': config('ENABLE_STRIPE', default=True, cast=bool),
                    'config_data': config_data,
                    'last_updated_by': admin,
                }
            )
            self.stdout.write(self.style.SUCCESS(f"Stripe config {'created' if created else 'updated'}"))
        else:
            self.stdout.write(self.style.WARNING('No Stripe secret key found in env; skipping Stripe'))

        # PayPal
        paypal_client = config('PAYPAL_CLIENT_ID', default='')
        paypal_secret = config('PAYPAL_CLIENT_SECRET', default='')
        if paypal_client and paypal_secret:
            obj, created = PaymentGatewayConfig.objects.update_or_create(
                gateway_name='paypal',
                defaults={
                    'is_active': config('ENABLE_PAYPAL', default=True, cast=bool),
                    'is_test_mode': config('PAYPAL_MODE', default='sandbox') == 'sandbox',
                    'config_data': {'client_id': paypal_client, 'client_secret': paypal_secret},
                    'last_updated_by': admin,
                }
            )
            self.stdout.write(self.style.SUCCESS(f"PayPal config {'created' if created else 'updated'}"))
        else:
            self.stdout.write(self.style.WARNING('No PayPal credentials found in env; skipping PayPal'))

        # M-Pesa
        mpesa_consumer = config('MPESA_CONSUMER_KEY', default='')
        mpesa_secret = config('MPESA_CONSUMER_SECRET', default='')
        mpesa_shortcode = config('MPESA_SHORTCODE', default=config('MPESA_BUSINESS_SHORTCODE', default=''))
        mpesa_passkey = config('MPESA_PASSKEY', default='')
        mpesa_callback = config('MPESA_CALLBACK_URL', default='')

        if mpesa_consumer and mpesa_secret and mpesa_shortcode and mpesa_passkey:
            obj, created = PaymentGatewayConfig.objects.update_or_create(
                gateway_name='mpesa',
                defaults={
                    'is_active': config('ENABLE_MPESA', default=False, cast=bool),
                    'is_test_mode': config('ENABLE_MPESA', default=False, cast=bool),
                    'config_data': {
                        'consumer_key': mpesa_consumer,
                        'consumer_secret': mpesa_secret,
                        'business_shortcode': mpesa_shortcode,
                        'passkey': mpesa_passkey,
                        'callback_url': mpesa_callback,
                    },
                    'last_updated_by': admin,
                }
            )
            self.stdout.write(self.style.SUCCESS(f"M-Pesa config {'created' if created else 'updated'}"))
        else:
            self.stdout.write(self.style.WARNING('Incomplete M-Pesa credentials in env; skipping M-Pesa'))

        self.stdout.write(self.style.SUCCESS('Seeding payment gateway configs complete.'))
