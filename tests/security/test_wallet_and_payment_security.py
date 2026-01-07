from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model

User = get_user_model()
Wallet = apps.get_model('payments', 'Wallet')
PaymentGatewayConfig = apps.get_model('payments', 'PaymentGatewayConfig')


class SecurityTests(TestCase):
    def test_wallet_debit_safety(self):
        user = User.objects.create_user(username='sec', password='p')
        wallet, _ = Wallet.objects.get_or_create(user=user)
        # Ensure starting balance is zero for safety check
        from decimal import Decimal
        wallet.balance = Decimal('0.00')
        wallet.save()
        self.assertFalse(wallet.debit(1))

    def test_payment_gateway_config_decrypt_safe(self):
        # instantiate without saving to avoid depending on DB columns in some test environments
        pg = PaymentGatewayConfig(gateway_name='stripe', is_active=True)
        # without config_data_encrypted expect empty dict
        self.assertEqual(pg.config_data, {})
