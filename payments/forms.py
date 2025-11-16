from django import forms
from decimal import Decimal
from django.conf import settings


class DepositForm(forms.Form):
    """Form for initiating a wallet deposit"""
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal(str(settings.MINIMUM_DEPOSIT_AMOUNT)),
        max_value=Decimal(str(settings.MAXIMUM_DEPOSIT_AMOUNT)),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': f'Min: {settings.MINIMUM_DEPOSIT_AMOUNT}, Max: {settings.MAXIMUM_DEPOSIT_AMOUNT}',
            'step': '0.01',
        }),
        label='Deposit Amount (USD)',
    )
    
    payment_gateway = forms.ChoiceField(
        choices=[
            ('stripe', 'Credit/Debit Card (Stripe)'),
            ('paypal', 'PayPal'),
            ('mpesa', 'M-Pesa (Kenya)'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Payment Method',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter payment gateways based on settings
        available_choices = []
        if settings.ENABLE_STRIPE:
            available_choices.append(('stripe', 'Credit/Debit Card (Stripe)'))
        if settings.ENABLE_PAYPAL:
            available_choices.append(('paypal', 'PayPal'))
        if settings.ENABLE_MPESA:
            available_choices.append(('mpesa', 'M-Pesa (Kenya)'))
        
        self.fields['payment_gateway'].choices = available_choices


class MPesaDepositForm(forms.Form):
    """Additional form for M-Pesa phone number"""
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '254712345678 or 0712345678',
        }),
        label='M-Pesa Phone Number',
        help_text='Enter your Safaricom phone number (Kenyan format)',
    )
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        # Remove any spaces or dashes
        phone = phone.replace(' ', '').replace('-', '')
        
        # Ensure it starts with 254 or 0
        if not phone.startswith('254') and not phone.startswith('0'):
            raise forms.ValidationError('Phone number must start with 254 or 0')
        
        return phone


class StripePaymentMethodForm(forms.Form):
    """Form for Stripe payment method ID (from frontend Stripe.js)"""
    payment_method_id = forms.CharField(
        widget=forms.HiddenInput(),
        required=True,
    )

class SubscriptionPaymentForm(forms.Form):
    """Form for selecting payment method for subscription purchase"""
    payment_method = forms.ChoiceField(
        choices=[
            ('wallet', 'Pay from Wallet Balance'),
            ('stripe', 'Credit/Debit Card (Stripe)'),
            ('paypal', 'PayPal'),
            ('mpesa', 'M-Pesa (Kenya)'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Payment Method',
    )

    def __init__(self, *args, wallet_balance=None, plan_price=None, **kwargs):
        super().__init__(*args, **kwargs)
        available_choices = []

        # Only show wallet option if user has sufficient balance for the plan
        if wallet_balance and plan_price and wallet_balance >= plan_price:
            available_choices.append(('wallet', f'Pay from Wallet Balance (${wallet_balance})'))
        elif wallet_balance and wallet_balance > 0:
            # Show wallet option but with insufficient balance message
            pass  # Don't add wallet option if insufficient

        # Add other payment gateways based on settings
        if settings.ENABLE_STRIPE:
            available_choices.append(('stripe', 'Credit/Debit Card (Stripe)'))
        if settings.ENABLE_PAYPAL:
            available_choices.append(('paypal', 'PayPal'))
        if settings.ENABLE_MPESA:
            available_choices.append(('mpesa', 'M-Pesa (Kenya)'))

        self.fields['payment_method'].choices = available_choices
        
        # Set help text if wallet has insufficient balance
        if wallet_balance and plan_price and wallet_balance < plan_price:
            self.fields['payment_method'].help_text = f'Your wallet balance (${wallet_balance}) is insufficient. Please use another payment method or deposit funds first.'


