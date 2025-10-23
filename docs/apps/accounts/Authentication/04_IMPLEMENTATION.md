# Authentication System - Implementation

**Feature:** Login, Logout, Session Management  
**Status:** Phase 1 Complete, Phase 2 Planned  
**Last Updated:** October 22, 2025

---

## 📂 CODE LOCATIONS

### Views
**File:** `coda/accounts/views.py`

**Implemented:**
- `login_view()` (lines ~100-150) - Login form and authentication
- `logout_view()` (lines ~160-180) - Logout handler
- `user_login_history()` (lines ~200-230) - View login history
- `edit_login_logout_time()` (lines ~240-260) - Admin edit times

**To Be Added (Phase 2):**
- `enable_2fa()` - Enable 2FA for user
- `disable_2fa()` - Disable 2FA
- `verify_2fa_code()` - Validate TOTP code
- `oauth_login()` - Initiate OAuth flow
- `oauth_callback()` - Handle OAuth callback
- `generate_backup_codes()` - Create 2FA backup codes

### Models
**File:** `coda/accounts/models.py`

**Existing:**
- `CustomerUser` (lines 37-185) - User model with auth fields
- `LoginHistory` (lines 440-456) - Login tracking

**To Be Added (Phase 2):**
- `TwoFactorAuth` - 2FA configuration
- `OAuthConnection` - OAuth provider links
- `AuthenticationLog` - Enhanced audit trail

### Forms
**File:** `coda/accounts/forms.py`

**Existing:**
- `LoginForm` - Basic login form
- `LoginHistoryForm` - Login history management

**To Be Added (Phase 2):**
- `TwoFactorEnableForm` - Enable 2FA
- `TwoFactorVerifyForm` - Verify TOTP code
- `BackupCodeForm` - Use backup code

### Templates
**Directory:** `coda/accounts/templates/accounts/registration/`

**Existing:**
- `login_page.html` - Login form
- `logout.html` - Logout confirmation
- `password_reset.html` - Password reset request
- `password_reset_confirm.html` - Set new password
- `password_reset_done.html` - Email sent confirmation
- `password_reset_complete.html` - Password changed success

**To Be Added (Phase 2):**
- `2fa_setup.html` - QR code for Google Authenticator
- `2fa_prompt.html` - Enter 6-digit code
- `backup_codes.html` - Display backup codes
- `oauth_buttons.html` - Social login buttons

### URLs
**File:** `coda/accounts/urls.py`

**Existing:**
```python
path("login/", views.login_view, name="account-login"),
path("logout/", views.logout_view, name="account-logout"),
path("login_history/<str:username>", views.user_login_history, name="login_history"),
# Password reset URLs (Django built-in)
```

**To Be Added (Phase 2):**
```python
path("2fa/enable/", views.enable_2fa, name="2fa-enable"),
path("2fa/verify/", views.verify_2fa_code, name="2fa-verify"),
path("2fa/backup-codes/", views.generate_backup_codes, name="2fa-backup"),
path("oauth/<str:provider>/", views.oauth_login, name="oauth-login"),
path("oauth/<str:provider>/callback/", views.oauth_callback, name="oauth-callback"),
```

---

## 🔑 KEY FUNCTIONS

### Login Handler (Current)

**Function:** `login_view(request)`  
**File:** `coda/accounts/views.py`

```python
def login_view(request):
    """
    Handle user authentication
    GET: Display login form
    POST: Authenticate and create session
    """
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember = form.cleaned_data.get('remember_me', False)
            
            # Authenticate (username or email)
            user = authenticate(
                request,
                username=username,
                password=password
            )
            
            if user is not None:
                # Check email verified
                if not user.email_verified:
                    messages.error(
                        request,
                        'Please verify your email before logging in.'
                    )
                    return redirect('accounts:email-verification-notice', user.id)
                
                # Create session
                login(request, user)
                
                # Set session expiry
                if not remember:
                    request.session.set_expiry(0)  # Browser close
                else:
                    request.session.set_expiry(2592000)  # 30 days
                
                # Log successful login
                LoginHistory.objects.create(
                    user=user,
                    login_time=timezone.now(),
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    success=True
                )
                
                # Redirect to appropriate dashboard
                redirect_url = get_redirect_url(user)
                return redirect(redirect_url)
                
            else:
                # Failed authentication
                messages.error(request, 'Invalid username or password.')
                
                # Log failed attempt
                LoginHistory.objects.create(
                    user=None,  # Unknown user
                    login_time=timezone.now(),
                    ip_address=request.META.get('REMOTE_ADDR'),
                    success=False,
                    failure_reason='Invalid credentials'
                )
    else:
        form = LoginForm()
    
    return render(request, 'accounts/registration/login_page.html', {'form': form})
```

---

### Redirect After Login

**Function:** `get_redirect_url(user)`  
**File:** `coda/accounts/user_utils.py`

```python
def get_redirect_url(user):
    """Determine dashboard based on user category"""
    
    if user.is_staff:
        # Staff users → Main dashboard
        return '/dashboard/'
    
    elif user.category == 2:  # Client
        return '/client/dashboard/'
    
    elif user.category == 3:  # Applicant
        return '/applicant/portal/'
    
    elif user.category == 4:  # Investor
        return '/investing/portfolio/'
    
    else:
        # Default dashboard
        return '/dashboard/'
```

---

### Logout Handler

**Function:** `logout_view(request)`  
**File:** `coda/accounts/views.py`

```python
from django.contrib.auth import logout

def logout_view(request):
    """Handle user logout"""
    
    user = request.user
    
    # Update login history (set logout time)
    LoginHistory.objects.filter(
        user=user,
        logout_time__isnull=True
    ).order_by('-login_time').first().update(
        logout_time=timezone.now()
    )
    
    # Logout (clear session)
    logout(request)
    
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:account-login')
```

---

## 🔐 SECURITY IMPLEMENTATION

### Prevent Brute Force Attacks

**Current:** Basic rate limiting at server level  
**Future (Phase 2):**

```python
from django.core.cache import cache

def login_view(request):
    if request.method == 'POST':
        # Check failed attempts
        ip = request.META.get('REMOTE_ADDR')
        key = f'failed_login_{ip}'
        failed_attempts = cache.get(key, 0)
        
        if failed_attempts >= 5:
            # Lockout for 15 minutes
            messages.error(request, 'Too many failed attempts. Try again in 15 minutes.')
            return redirect('accounts:account-login')
        
        # Attempt authentication...
        user = authenticate(username=username, password=password)
        
        if user:
            # Success - clear failed attempts
            cache.delete(key)
        else:
            # Failed - increment counter
            cache.set(key, failed_attempts + 1, 900)  # 15 min expiry
```

---

### Session Fixation Prevention

**Django Automatically:**
- Changes session ID on login
- Prevents session fixation attacks

```python
# Django does this automatically in login():
request.session.cycle_key()
```

---

### CSRF Protection

**All Forms:**
```html
<form method="POST">
    {% csrf_token %}  <!-- Required -->
    ...
</form>
```

**AJAX Requests:**
```javascript
// Include CSRF token in AJAX headers
$.ajax({
    headers: {
        'X-CSRFToken': getCookie('csrftoken')
    },
    ...
});
```

---

## 📊 LOGIN HISTORY TRACKING

### Create Login Record

```python
# On successful login
LoginHistory.objects.create(
    user=user,
    login_time=timezone.now(),
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT'),
    success=True
)

# On failed login
LoginHistory.objects.create(
    user=None,  # Or identified user if known
    login_time=timezone.now(),
    ip_address=request.META.get('REMOTE_ADDR'),
    success=False,
    failure_reason='Invalid password'
)
```

### View Login History

```python
def user_login_history(request, username):
    """Display user's login history"""
    
    user = get_object_or_404(CustomerUser, username=username)
    
    # Security check: users can only view own history
    if request.user != user and not request.user.is_staff:
        return HttpResponseForbidden()
    
    # Get last 50 logins
    history = LoginHistory.objects.filter(user=user).order_by('-login_time')[:50]
    
    context = {
        'user': user,
        'login_history': history,
    }
    return render(request, 'accounts/login_history.html', context)
```

---

## 🔄 PASSWORD RESET FLOW

### Reset Request

**URL:** `/accounts/password-reset/`  
**View:** Django built-in `PasswordResetView`

```python
# User submits email
# Django:
# 1. Finds user by email
# 2. Generates reset token
# 3. Sends email with reset link
# 4. Shows "Email sent" page
```

### Reset Confirmation

**URL:** `/accounts/password-reset-confirm/<uidb64>/<token>/`  
**View:** Django built-in `PasswordResetConfirmView`

```python
# User clicks link in email
# Django:
# 1. Validates token
# 2. Shows password change form
# 3. User sets new password
# 4. Password hashed and saved
# 5. Shows "Password changed" page
```

---

## 📊 CHANGE HISTORY

| Date | Change | Files | Developer |
|------|--------|-------|-----------|
| Oct 22, 2025 | 7-doc structure created | All docs | AI |
| Earlier 2025 | Login history tracking added | views.py, models.py | Team |
| Earlier 2025 | Email verification check | views.py | Team |
| Earlier 2025 | Initial auth system | Multiple | Team |

### Planned Changes (Phase 2):
- Add TwoFactorAuth model
- Add 2FA views and templates
- Integrate django-otp library
- Add OAuthConnection model
- Integrate django-allauth
- Configure OAuth providers
- Add AI anomaly detection

---

## 🔧 MIDDLEWARE

### Authentication Middleware

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # ← Auth
    'django.contrib.messages.middleware.MessageMiddleware',
    ...
]
```

**What it does:**
- Adds `request.user` to every request
- Populates user from session
- Provides `request.user.is_authenticated`

---

## 🔐 DECORATORS

### @login_required

```python
from django.contrib.auth.decorators import login_required

@login_required
def protected_view(request):
    """Only authenticated users can access"""
    # request.user is guaranteed to be authenticated
    ...
```

### Custom Permission Decorators

```python
from functools import wraps

def staff_required(view_func):
    """Require staff user"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden('Staff access only')
        return view_func(request, *args, **kwargs)
    return wrapper

# Usage
@staff_required
def admin_view(request):
    ...
```

---

**See:** 05_TESTING.md for authentication test scenarios


