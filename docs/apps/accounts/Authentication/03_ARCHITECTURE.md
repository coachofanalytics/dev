# Authentication System - Architecture

**Feature:** Login, Logout, Session Management  
**Status:** Phase 1 Complete, Phase 2-3 Designed  
**Last Updated:** October 22, 2025

---

## 🏗️ AUTHENTICATION ARCHITECTURE

### Phase 1: Current System (Password-Based)

```
┌──────────────┐
│ User Browser │
└──────┬───────┘
       │
       ↓ (POST /accounts/login/)
┌────────────────────┐
│ login_view()       │
│ - Get credentials  │
│ - Call authenticate│
└──────┬─────────────┘
       │
       ↓
┌────────────────────┐
│ Django Auth        │
│ authenticate()     │
│ - Find user        │
│ - Check password   │
└──────┬─────────────┘
       │
       ├─ Invalid → Return None → Show Error
       │
       ↓ Valid
┌────────────────────┐
│ Check Email        │
│ Verified           │
└──────┬─────────────┘
       │
       ├─ Not Verified → Block Login → Show Message
       │
       ↓ Verified
┌────────────────────┐
│ django.login()     │
│ - Create session   │
│ - Set cookies      │
└──────┬─────────────┘
       │
       ↓
┌────────────────────┐
│ Log Login Event    │
│ LoginHistory.create│
└──────┬─────────────┘
       │
       ↓
┌────────────────────┐
│ Redirect to        │
│ Dashboard          │
└────────────────────┘
```

---

### Phase 2: Enhanced System (2FA + OAuth)

```
User Browser
     ↓
Login Page
     ↓
┌─────────────────────────────┐
│ Choose Auth Method:         │
│ 1. Username/Password        │
│ 2. Google OAuth             │
│ 3. GitHub OAuth             │
└─────────────────────────────┘
     │
     ├─ Option 1: Password ────────┐
     │                              │
     │                              ↓
     │                  ┌────────────────────┐
     │                  │ Authenticate       │
     │                  │ username + password│
     │                  └──────┬─────────────┘
     │                         │
     │                         ↓ (If 2FA enabled)
     │                  ┌────────────────────┐
     │                  │ Prompt for TOTP    │
     │                  │ 6-digit code       │
     │                  └──────┬─────────────┘
     │                         │
     │                         ↓ (Validate code)
     │                  ┌────────────────────┐
     │                  │ Check Risk Score   │
     │                  │ (AI Analysis)      │
     │                  └──────┬─────────────┘
     │                         │
     ├─ Option 2: Google ──────┼─────────────┐
     │                         │             │
     │                         ↓             ↓
     │              ┌──────────────┐  ┌──────────────┐
     │              │ OAuth Flow   │  │ Create       │
     │              │ Redirect to  │  │ Session      │
     │              │ Provider     │  └──────┬───────┘
     │              └──────┬───────┘         │
     │                     │                 │
     │                     ↓                 │
     │              ┌──────────────┐         │
     │              │ User Approves│         │
     │              │ Access       │         │
     │              └──────┬───────┘         │
     │                     │                 │
     │                     ↓                 │
     │              ┌──────────────┐         │
     │              │ Callback     │         │
     │              │ with Token   │         │
     │              └──────┬───────┘         │
     │                     │                 │
     │                     ↓                 │
     │              ┌──────────────┐         │
     └──────────────│ Create/Link  │─────────┤
                    │ User Account │         │
                    └──────┬───────┘         │
                           │                 │
                           ↓                 ↓
                    ┌──────────────┐  ┌──────────────┐
                    │ Log Event    │  │ Redirect to  │
                    │ LoginHistory │  │ Dashboard    │
                    └──────────────┘  └──────────────┘
```

---

## 📊 DATA MODELS

### CustomerUser (Authentication Fields)

```python
class CustomerUser(AbstractUser):
    """User model with authentication support"""
    
    # Django AbstractUser provides:
    username = CharField(max_length=150, unique=True)
    password = CharField(max_length=128)  # Hashed
    is_active = BooleanField(default=True)
    last_login = DateTimeField(null=True)
    
    # CODA additions:
    email_verified = BooleanField(default=False)
    
    def check_password(self, raw_password):
        """Verify password against hashed value"""
        return super().check_password(raw_password)
```

### LoginHistory Model

```python
class LoginHistory(models.Model):
    """Track all login attempts"""
    
    user = ForeignKey(
        CustomerUser,
        on_delete=models.CASCADE,
        related_name='login_history'
    )
    
    # Login Details
    login_time = DateTimeField(auto_now_add=True)
    logout_time = DateTimeField(null=True, blank=True)
    
    # Security Metadata
    ip_address = GenericIPAddressField(null=True, blank=True)
    user_agent = TextField(null=True, blank=True)
    
    # Status
    success = BooleanField(default=True)
    failure_reason = CharField(max_length=255, null=True, blank=True)
    
    # Indexes for performance
    class Meta:
        indexes = [
            models.Index(fields=['user', '-login_time']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['success']),
        ]
```

### Session Model (Django Built-in)

```python
# Django's session framework
# Table: django_session

session_key = CharField(40, primary_key=True)  # Random token
session_data = TextField()  # Encrypted session data
expire_date = DateTimeField()  # Expiration timestamp
```

---

### Phase 2 Models (To Be Added):

#### TwoFactorAuth Model
```python
class TwoFactorAuth(models.Model):
    """2FA configuration per user"""
    
    user = OneToOneField(CustomerUser, on_delete=models.CASCADE)
    
    # TOTP Configuration
    totp_secret = CharField(max_length=32)  # Base32 secret
    is_enabled = BooleanField(default=False)
    enabled_at = DateTimeField(null=True)
    
    # Backup Codes
    backup_codes = JSONField(default=list)  # List of 10 codes
    
    # Recovery
    last_verified = DateTimeField(null=True)
```

#### OAuthConnection Model
```python
class OAuthConnection(models.Model):
    """OAuth provider connections"""
    
    user = ForeignKey(CustomerUser, on_delete=models.CASCADE)
    
    # Provider Info
    provider = CharField(max_length=50)  # google, github, microsoft
    provider_user_id = CharField(max_length=255)  # External ID
    
    # Tokens
    access_token = TextField()
    refresh_token = TextField(null=True)
    token_expires = DateTimeField(null=True)
    
    # Metadata
    connected_at = DateTimeField(auto_now_add=True)
    last_used = DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['provider', 'provider_user_id']]
```

---

## 🔄 AUTHENTICATION FLOWS

### Flow 1: Password Login (Current)

```python
def login_view(request):
    if request.method == 'POST':
        # 1. Get credentials
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember_me')
        
        # 2. Authenticate
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # 3. Check email verified
            if not user.email_verified:
                messages.error(request, 'Please verify your email first.')
                return redirect('accounts:email-verification-notice', user.id)
            
            # 4. Login user (create session)
            login(request, user)
            
            # 5. Set session expiry
            if not remember:
                request.session.set_expiry(0)  # Browser close
            else:
                request.session.set_expiry(2592000)  # 30 days
            
            # 6. Log event
            LoginHistory.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                success=True
            )
            
            # 7. Redirect based on category
            redirect_url = get_redirect_url(user)
            return redirect(redirect_url)
        else:
            # Failed login
            messages.error(request, 'Invalid credentials.')
            # Log failed attempt...
```

---

### Flow 2: 2FA Login (Phase 2 - Planned)

```python
def login_with_2fa(request):
    # Step 1: Password authentication (same as above)
    user = authenticate(username=username, password=password)
    
    if user and user.email_verified:
        # Step 2: Check if 2FA enabled
        try:
            twofa = TwoFactorAuth.objects.get(user=user, is_enabled=True)
            
            # Step 3: Show 2FA prompt
            request.session['pending_user_id'] = user.id
            return render(request, 'accounts/2fa_prompt.html')
            
        except TwoFactorAuth.DoesNotExist:
            # No 2FA, proceed to login
            login(request, user)
            return redirect_to_dashboard()

def verify_2fa_code(request):
    # Get pending user
    user_id = request.session.get('pending_user_id')
    user = CustomerUser.objects.get(id=user_id)
    
    # Get submitted code
    code = request.POST.get('totp_code')
    
    # Verify TOTP
    twofa = TwoFactorAuth.objects.get(user=user)
    if verify_totp(twofa.totp_secret, code):
        # Code valid - complete login
        login(request, user)
        del request.session['pending_user_id']
        return redirect_to_dashboard()
    else:
        messages.error(request, 'Invalid code. Try again.')
        return render(request, 'accounts/2fa_prompt.html')
```

---

### Flow 3: OAuth Login (Phase 2 - Planned)

```python
def oauth_login(request, provider):
    """
    Initiate OAuth flow
    Provider: google, github, microsoft
    """
    
    # 1. Generate state token (CSRF protection)
    state = secrets.token_urlsafe(32)
    request.session['oauth_state'] = state
    
    # 2. Build authorization URL
    auth_url = build_oauth_url(provider, state)
    
    # 3. Redirect to provider
    return redirect(auth_url)

def oauth_callback(request, provider):
    """Handle OAuth callback"""
    
    # 1. Verify state (CSRF protection)
    if request.GET.get('state') != request.session.get('oauth_state'):
        return HttpResponse('Invalid state', status=400)
    
    # 2. Exchange code for access token
    code = request.GET.get('code')
    tokens = exchange_code_for_tokens(provider, code)
    
    # 3. Get user info from provider
    profile = get_user_profile(provider, tokens['access_token'])
    
    # 4. Find or create user
    try:
        # Try to find existing connection
        connection = OAuthConnection.objects.get(
            provider=provider,
            provider_user_id=profile['id']
        )
        user = connection.user
        
    except OAuthConnection.DoesNotExist:
        # Create new user or link to existing
        user, created = CustomerUser.objects.get_or_create(
            email=profile['email'],
            defaults={
                'username': profile['email'].split('@')[0],
                'first_name': profile.get('given_name', ''),
                'last_name': profile.get('family_name', ''),
                'email_verified': True,  # Trust provider verification
            }
        )
        
        # Create OAuth connection
        OAuthConnection.objects.create(
            user=user,
            provider=provider,
            provider_user_id=profile['id'],
            access_token=tokens['access_token'],
            refresh_token=tokens.get('refresh_token'),
        )
    
    # 5. Login user
    login(request, user, backend='accounts.backends.OAuthBackend')
    
    # 6. Log event
    LoginHistory.objects.create(user=user, success=True)
    
    # 7. Redirect to dashboard
    return redirect(get_redirect_url(user))
```

---

## 🔐 SESSION ARCHITECTURE

### Session Storage

**Backend:** Database (default)  
**Table:** `django_session`  
**Encryption:** Yes (Django encrypts session data)

```python
# settings.py
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1800  # 30 minutes default
SESSION_SAVE_EVERY_REQUEST = True  # Extend on activity
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
```

### Session Data Structure

```python
# Stored in session:
request.session = {
    '_auth_user_id': '123',  # User ID
    '_auth_user_backend': 'django.contrib.auth.backends.ModelBackend',
    '_auth_user_hash': 'abc...',  # Password hash verification
    
    # Custom data:
    'user_category': 1,  # Employee
    'last_activity': '2025-10-22 20:00:00',
}
```

---

## 🔑 PASSWORD HASHING

### Algorithm: PBKDF2 with SHA256

```python
# settings.py
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',  # Default
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',  # Fallback
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # Future
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',  # Fallback
]

# Password format in database:
# pbkdf2_sha256$260000$salt$hash
# - Algorithm: pbkdf2_sha256
# - Iterations: 260,000
# - Salt: Random per user
# - Hash: Computed value
```

### Password Verification

```python
# When user logs in:
def authenticate(username, password):
    try:
        user = CustomerUser.objects.get(username=username)
        
        # Check password (automatic hash comparison)
        if user.check_password(password):
            return user
        else:
            return None
            
    except CustomerUser.DoesNotExist:
        # Run dummy check to prevent timing attack
        CustomerUser().set_password(password)
        return None
```

---

## 🔄 LOGOUT FLOW

```python
def logout_view(request):
    """Secure logout"""
    
    # 1. Get user before logout
    user = request.user
    
    # 2. Update login history (set logout time)
    LoginHistory.objects.filter(
        user=user,
        logout_time__isnull=True
    ).update(logout_time=timezone.now())
    
    # 3. Django logout (clears session)
    logout(request)
    
    # 4. Clear any custom cookies
    response = redirect('accounts:account-login')
    response.delete_cookie('custom_cookie')
    
    # 5. Log event
    logger.info(f'User {user.username} logged out')
    
    return response
```

---

## 🔌 AUTHENTICATION BACKENDS

### Current Backend: Django Default

```python
# Django's ModelBackend
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
```

### Phase 2: Custom Backend (Planned)

```python
# Custom backend for OAuth
class OAuthBackend(ModelBackend):
    """Custom backend for OAuth authentication"""
    
    def authenticate(self, request, oauth_token=None, provider=None):
        if oauth_token and provider:
            # Verify token with provider
            user_info = verify_oauth_token(provider, oauth_token)
            
            # Find or create user
            user = get_or_create_oauth_user(user_info, provider)
            return user
        
        return None

# Update settings
AUTHENTICATION_BACKENDS = [
    'accounts.backends.OAuthBackend',  # Try OAuth first
    'django.contrib.auth.backends.ModelBackend',  # Fallback to password
]
```

---

## 📊 2FA ARCHITECTURE (Phase 2)

### TOTP (Time-Based One-Time Password)

**Algorithm:** RFC 6238  
**Library:** pyotp or django-otp

```python
import pyotp

# Generate secret (once per user)
secret = pyotp.random_base32()  # Example: "JBSWY3DPEHPK3PXP"

# Generate QR code
totp = pyotp.TOTP(secret)
qr_uri = totp.provisioning_uri(
    name=user.email,
    issuer_name='CODA'
)
# qr_uri used to generate QR code for Google Authenticator

# Verify code (on each login)
code = request.POST.get('totp_code')  # User enters 6-digit code
totp = pyotp.TOTP(user.twofa.totp_secret)
if totp.verify(code, valid_window=1):
    # Code valid (within 30-second window + 1 window grace)
    proceed_with_login()
```

### Backup Codes

```python
import secrets

def generate_backup_codes(count=10):
    """Generate one-time backup codes"""
    codes = []
    for _ in range(count):
        code = secrets.token_hex(4)  # 8-character code
        codes.append(code)
    return codes

# Store hashed
hashed_codes = [make_password(code) for code in codes]
user.twofa.backup_codes = hashed_codes
user.twofa.save()

# Verify backup code
def verify_backup_code(user, submitted_code):
    for stored_hash in user.twofa.backup_codes:
        if check_password(submitted_code, stored_hash):
            # Valid! Remove from list (one-time use)
            user.twofa.backup_codes.remove(stored_hash)
            user.twofa.save()
            return True
    return False
```

---

## 🔌 OAUTH ARCHITECTURE (Phase 2)

### OAuth 2.0 Flow (Authorization Code Grant)

**Providers:**
- Google (OAuth 2.0 / OpenID Connect)
- GitHub (OAuth 2.0)
- Microsoft (OAuth 2.0 / OpenID Connect)

**Flow:**
1. User clicks "Login with Google"
2. Redirect to Google with client_id, redirect_uri, state
3. User authorizes CODA access
4. Google redirects back with authorization code
5. Exchange code for access_token + refresh_token
6. Use access_token to get user profile
7. Create/link user account
8. Login user

**Configuration Per Provider:**
```python
OAUTH_PROVIDERS = {
    'google': {
        'client_id': os.environ.get('GOOGLE_OAUTH_CLIENT_ID'),
        'client_secret': os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET'),
        'authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_url': 'https://oauth2.googleapis.com/token',
        'userinfo_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
        'scope': 'openid email profile',
    },
    'github': {
        'client_id': os.environ.get('GITHUB_OAUTH_CLIENT_ID'),
        'client_secret': os.environ.get('GITHUB_OAUTH_CLIENT_SECRET'),
        'authorize_url': 'https://github.com/login/oauth/authorize',
        'token_url': 'https://github.com/login/oauth/access_token',
        'userinfo_url': 'https://api.github.com/user',
        'scope': 'read:user user:email',
    },
}
```

---

## 🔒 SECURITY ARCHITECTURE

### Multi-Layer Security

```
Layer 1: HTTPS (Transport Security)
    ↓
Layer 2: CSRF Protection (Request Validation)
    ↓
Layer 3: Password Hashing (Credential Security)
    ↓
Layer 4: Email Verification (Identity Validation)
    ↓
Layer 5: 2FA (Phase 2) (Additional Factor)
    ↓
Layer 6: Session Security (Access Control)
    ↓
Layer 7: Login History (Audit Trail)
    ↓
Layer 8: AI Anomaly Detection (Phase 2) (Threat Intelligence)
```

---

**See:** 04_IMPLEMENTATION.md for code details



