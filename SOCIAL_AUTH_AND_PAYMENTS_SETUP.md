# Social Authentication & Payment Integration Setup Guide

This guide covers the setup and configuration for Google/Facebook social authentication and the CashApp/Venmo payment systems added to Biashara Bridges.

## Table of Contents
1. [Social Authentication Setup](#social-authentication-setup)
2. [Payment Gateway Setup](#payment-gateway-setup)
3. [Database Migrations](#database-migrations)
4. [Testing](#testing)
5. [Production Deployment](#production-deployment)

---

## Social Authentication Setup

### Overview
Biashara Bridges now supports social authentication through:
- **Google OAuth2** - Login/Register with Google
- **Facebook OAuth2** - Login/Register with Facebook

### Prerequisites
- Python package `social-auth-app-django` (already added to requirements.txt)
- Google Cloud Console account
- Facebook Developer account

### 1. Google OAuth2 Setup

#### Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth 2.0 Client ID**
5. Configure the consent screen if you haven't already
6. For **Application type**, select **Web application**
7. Add **Authorized redirect URIs**:
   - Development: `http://localhost:8000/oauth/complete/google-oauth2/`
   - Production: `https://yourdomain.com/oauth/complete/google-oauth2/`
8. Save and copy your **Client ID** and **Client Secret**

#### Step 2: Update .env File

```bash
GOOGLE_OAUTH2_CLIENT_ID=your_google_client_id_here
GOOGLE_OAUTH2_CLIENT_SECRET=your_google_client_secret_here
```

### 2. Facebook OAuth2 Setup

#### Step 1: Create Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/apps/)
2. Click **Create App**
3. Select app type: **Consumer** or **Business**
4. Fill in app details and create the app
5. In the app dashboard, go to **Settings** > **Basic**
6. Copy your **App ID** and **App Secret**
7. Add **Facebook Login** product to your app
8. In **Facebook Login** settings, add **Valid OAuth Redirect URIs**:
   - Development: `http://localhost:8000/oauth/complete/facebook/`
   - Production: `https://yourdomain.com/oauth/complete/facebook/`

#### Step 2: Update .env File

```bash
FACEBOOK_APP_ID=your_facebook_app_id_here
FACEBOOK_APP_SECRET=your_facebook_app_secret_here
```

### 3. Social Auth Configuration

The following has been configured in `config/settings.py`:

```python
AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',       # Google OAuth2
    'social_core.backends.facebook.FacebookOAuth2',   # Facebook OAuth2
    'accounts.backends.CaseInsensitiveAuthBackend',   # Custom backend
    'django.contrib.auth.backends.ModelBackend',      # Default backend
]

INSTALLED_APPS = [
    ...
    'social_django',  # Social auth app
    ...
]
```

### 4. How It Works

- Users can click "Continue with Google" or "Continue with Facebook" on login/register pages
- Social auth creates a user account automatically if it doesn't exist
- Custom pipeline (`accounts/pipeline.py`) creates a UserProfile for social auth users
- Users are redirected to `/edit-profile/` after first social login to complete their profile

---

## Payment Gateway Setup

### Overview
Biashara Bridges now supports **5 payment gateways**:
1. **Stripe** - Card payments (Visa, Mastercard, etc.)
2. **PayPal** - PayPal account payments
3. **M-Pesa** - Kenya mobile money
4. **CashApp** - Cash App Pay (via Square)
5. **Venmo** - Venmo payments (via Braintree)

### 1. CashApp (Square) Setup

#### Step 1: Create Square Developer Account

1. Go to [Square Developer Portal](https://developer.squareup.com/apps)
2. Create a new application or use an existing one
3. Navigate to **Credentials** tab
4. Copy the following:
   - **Application ID** (Sandbox and Production)
   - **Access Token** (Sandbox and Production)
5. Create a location (if you don't have one):
   - Go to **Locations** in your Square dashboard
   - Copy the **Location ID**

#### Step 2: Configure OAuth (Optional for advanced features)

1. In your app settings, configure **OAuth** section
2. Set redirect URLs if needed
3. Copy **OAuth Client ID** and **Client Secret**

#### Step 3: Update .env File

```bash
# For Sandbox/Testing
CASHAPP_APP_ID=sandbox-sq0idb-xxxxx
CASHAPP_CLIENT_ID=sandbox-sq0idc-xxxxx
CASHAPP_CLIENT_SECRET=sandbox-sq0csb-xxxxx
CASHAPP_ACCESS_TOKEN=EAAAxxxxx (Sandbox Access Token)
CASHAPP_LOCATION_ID=LOCATION_ID_HERE

# For Production, use production credentials
```

#### Step 4: Enable Cash App Pay

1. In your Square dashboard, go to **Payment Methods**
2. Enable **Cash App Pay**
3. Verify your business information

### 2. Venmo (Braintree) Setup

#### Step 1: Create Braintree Account

1. Go to [Braintree](https://www.braintreepayments.com/)
2. Sign up for a merchant account (or use sandbox for testing)
3. For testing, go to [Braintree Sandbox](https://sandbox.braintreegateway.com/)

#### Step 2: Get API Credentials

1. Log in to your Braintree account
2. Navigate to **Account** > **API Keys, Tokenization Keys, Encryption Keys**
3. View or generate your API keys
4. Copy the following:
   - **Merchant ID**
   - **Public Key**
   - **Private Key**

#### Step 3: Enable Venmo

1. In your Braintree account, go to **Settings** > **Payment Methods**
2. Enable **Venmo**
3. Configure Venmo settings:
   - Business profile name
   - Logo (optional)
   - Support information

#### Step 4: Update .env File

```bash
# For Sandbox
VENMO_MERCHANT_ID=your_sandbox_merchant_id
VENMO_PUBLIC_KEY=your_sandbox_public_key
VENMO_PRIVATE_KEY=your_sandbox_private_key

# For Production, use production credentials
```

### 3. Payment Gateway Feature Flags

Enable/disable payment gateways in .env:

```bash
ENABLE_STRIPE=True
ENABLE_PAYPAL=True
ENABLE_MPESA=True
ENABLE_CASHAPP=True
ENABLE_VENMO=True
ENABLE_WALLET_PAYMENTS=True
```

### 4. Webhook Configuration

#### CashApp (Square) Webhooks

1. In Square Developer Portal, go to **Webhooks**
2. Add webhook URL:
   - Development: `http://your-ngrok-url.com/payments/webhooks/cashapp/`
   - Production: `https://yourdomain.com/payments/webhooks/cashapp/`
3. Subscribe to events:
   - `payment.created`
   - `payment.updated`
   - `refund.created`

#### Venmo (Braintree) Webhooks

1. In Braintree dashboard, go to **Settings** > **Webhooks**
2. Add webhook URL:
   - Development: `http://your-ngrok-url.com/payments/webhooks/venmo/`
   - Production: `https://yourdomain.com/payments/webhooks/venmo/`
3. Subscribe to events:
   - `transaction_settled`
   - `transaction_settlement_declined`

---

## Database Migrations

### Run Migrations

After setting up social auth and payment integrations:

```bash
# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows

# Run migrations
python manage.py migrate

# Create social_django tables
python manage.py migrate social_django
```

### Create Payment Gateway Configurations

You need to create `PaymentGatewayConfig` objects in the database for each gateway:

```bash
python manage.py shell
```

Then run:

```python
from payments.models import PaymentGatewayConfig

# CashApp Gateway
PaymentGatewayConfig.objects.create(
    gateway_name='cashapp',
    is_active=True,
    is_test_mode=True,  # Set to False for production
    config_data={
        'app_id': 'your_cashapp_app_id',
        'client_id': 'your_cashapp_client_id',
        'client_secret': 'your_cashapp_client_secret',
        'access_token': 'your_cashapp_access_token',
        'location_id': 'your_cashapp_location_id',
    }
)

# Venmo Gateway
PaymentGatewayConfig.objects.create(
    gateway_name='venmo',
    is_active=True,
    is_test_mode=True,  # Set to False for production
    config_data={
        'merchant_id': 'your_venmo_merchant_id',
        'public_key': 'your_venmo_public_key',
        'private_key': 'your_venmo_private_key',
    }
)
```

---

## Testing

### Test Social Authentication

1. Start the development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to:
   - Login page: `http://localhost:8000/login/`
   - Register page: `http://localhost:8000/register/`

3. Click **"Continue with Google"** or **"Continue with Facebook"**

4. Authorize the app and verify:
   - User account is created
   - UserProfile is created
   - User is redirected to profile edit page

### Test Payment Integrations

1. Log in to your account

2. Navigate to: `http://localhost:8000/payments/wallet/`

3. Click **"Deposit Funds"**

4. Test each payment method:

#### Testing CashApp (Square Sandbox)

- Use Square's test card numbers:
  - **Success**: `4111 1111 1111 1111`
  - **Declined**: `4000 0000 0000 0002`
- Or use the Square Web Payment SDK testing flow

#### Testing Venmo (Braintree Sandbox)

- Use Braintree's test nonces
- Or use the Braintree Drop-in UI with sandbox credentials
- Test Venmo username: Use any sandbox Venmo account

### Webhook Testing (Local Development)

Use ngrok to expose your local server:

```bash
# Install ngrok: https://ngrok.com/
ngrok http 8000
```

Use the ngrok URL for webhook configuration in Square/Braintree dashboards.

---

## Production Deployment

### 1. Environment Variables

Set all production environment variables:

```bash
# Social Auth
GOOGLE_OAUTH2_CLIENT_ID=production_google_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=production_google_client_secret
FACEBOOK_APP_ID=production_facebook_app_id
FACEBOOK_APP_SECRET=production_facebook_app_secret

# CashApp (Production)
CASHAPP_APP_ID=production_app_id
CASHAPP_ACCESS_TOKEN=production_access_token
CASHAPP_LOCATION_ID=production_location_id

# Venmo (Production)
VENMO_MERCHANT_ID=production_merchant_id
VENMO_PUBLIC_KEY=production_public_key
VENMO_PRIVATE_KEY=production_private_key
```

### 2. Update OAuth Redirect URIs

Add production URLs to:
- Google Cloud Console (Authorized redirect URIs)
- Facebook App Settings (Valid OAuth Redirect URIs)

Example:
```
https://yourdomain.com/oauth/complete/google-oauth2/
https://yourdomain.com/oauth/complete/facebook/
```

### 3. Update Webhook URLs

Update webhook URLs in:
- Square Developer Portal → Webhooks
- Braintree Dashboard → Settings → Webhooks

Example:
```
https://yourdomain.com/payments/webhooks/cashapp/
https://yourdomain.com/payments/webhooks/venmo/
```

### 4. Set Production Mode

Update `.env`:

```bash
DEBUG=False
ENABLE_CASHAPP=True
ENABLE_VENMO=True
```

Update `PaymentGatewayConfig` in database:

```python
# Set is_test_mode to False for all production gateways
PaymentGatewayConfig.objects.filter(gateway_name__in=['cashapp', 'venmo']).update(is_test_mode=False)
```

### 5. SSL/HTTPS

Ensure your production site uses HTTPS for:
- OAuth redirects
- Payment processing
- Webhook callbacks

---

## Troubleshooting

### Social Auth Issues

**Issue**: "Redirect URI mismatch"
- **Solution**: Verify the redirect URI in Google/Facebook matches exactly (including trailing slash)

**Issue**: User created but no UserProfile
- **Solution**: Check `accounts/pipeline.py` is working correctly

### Payment Issues

**Issue**: CashApp payment fails
- **Solution**:
  - Verify access token is not expired
  - Check location ID is correct
  - Ensure Cash App Pay is enabled in Square dashboard

**Issue**: Venmo not showing in Braintree Drop-in
- **Solution**:
  - Enable Venmo in Braintree payment methods
  - Verify merchant account is approved for Venmo
  - Check client token generation

**Issue**: Webhook not receiving events
- **Solution**:
  - Verify webhook URL is publicly accessible
  - Check webhook signature verification (if implemented)
  - Review webhook logs in Square/Braintree dashboard

---

## Additional Resources

### Social Authentication
- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Facebook Login Documentation](https://developers.facebook.com/docs/facebook-login/)
- [Python Social Auth Documentation](https://python-social-auth.readthedocs.io/)

### Payment Gateways
- [Square API Documentation](https://developer.squareup.com/docs)
- [Square Web Payment SDK](https://developer.squareup.com/docs/web-payments/overview)
- [Braintree Documentation](https://developer.paypal.com/braintree/docs)
- [Braintree Drop-in UI](https://developer.paypal.com/braintree/docs/guides/drop-in/overview)
- [Venmo with Braintree](https://developer.paypal.com/braintree/docs/guides/venmo/overview)

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the official documentation links
3. Check application logs: `python manage.py check`
4. Test in sandbox/development first before going to production

---

**Last Updated**: December 2024
**Version**: 1.0
