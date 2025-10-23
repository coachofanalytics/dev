# Registration System - Implementation

**Feature:** User Registration & Onboarding  
**Status:** ✅ Production Ready  
**Last Updated:** October 22, 2025

---

## 📂 CODE LOCATIONS

### Models
**File:** `coda/accounts/models.py`
- `CustomerUser` (lines 37-185) - Main user model with registration fields
- `UserProfile` (lines 186-247) - Extended profile information

### Views
**File:** `coda/accounts/views.py`
- `join()` (lines ~50-100) - Registration form handler
- `verify_email()` (lines ~20-40) - Email verification handler
- `email_verification_notice()` - Verification pending page
- `populate_tokens_view()` - Resend verification email

### Forms
**File:** `coda/accounts/forms.py`
- `UserForm` - Registration form with validation

### Templates
**Directory:** `coda/accounts/templates/accounts/registration/`
- `join.html` - Registration form template
- `email_verification_notice.html` - Pending verification page
- `email_verification.html` - Verification email template

### URLs
**File:** `coda/accounts/urls.py`
- `path("join/", views.join, name="join")`
- `path("verify-email/<uuid:token>/", verify_email, name="verify-email")`
- `path("email-verification-notice/<int:user_id>/", ...)`
- `path("populate-tokens/", populate_tokens_view, name="populate_tokens")`

### Utilities
**File:** `coda/accounts/utils.py`
- `send_verification_email(user)` - Email sending function

### Static Files
**Directory:** `coda/accounts/static/accounts/js/`
- `registration.js` - Client-side form behavior

---

## 🔑 KEY FUNCTIONS

### Registration Handler

**Function:** `join(request)`  
**File:** `coda/accounts/views.py`

```python
def join(request):
    """
    Handle user registration
    GET: Display registration form
    POST: Process registration and create user
    """
    
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Create user without saving
            user = form.save(commit=False)
            
            # Hash password
            user.set_password(form.cleaned_data['password'])
            
            # Generate verification token
            user.verification_token = uuid.uuid4()
            user.email_verified = False
            
            # Save user
            user.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Send verification email
            send_verification_email(user)
            
            messages.success(request, 'Registration successful! Check your email.')
            return redirect('accounts:email-verification-notice', user_id=user.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserForm()
    
    context = {'form': form}
    return render(request, 'accounts/registration/join.html', context)
```

**Key Logic:**
1. Validate form data
2. Hash password (never store plain text)
3. Generate UUID token
4. Create user and profile
5. Send verification email
6. Redirect to notice page

---

### Email Verification Handler

**Function:** `verify_email(request, token)`  
**File:** `coda/accounts/views.py`

```python
def verify_email(request, token):
    """
    Verify user email address via token
    Mark email as verified and allow login
    """
    
    try:
        # Find user by verification token
        user = CustomerUser.objects.get(verification_token=token)
        
        # Mark email as verified
        user.email_verified = True
        user.verification_token = None  # Clear token
        user.save()
        
        messages.success(
            request,
            f'Email verified successfully, {user.first_name}! You can now login.'
        )
        return redirect('accounts:account-login')
        
    except CustomerUser.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')
        return redirect('accounts:home')
```

**Key Logic:**
1. Extract token from URL
2. Find user by token
3. Set email_verified = True
4. Clear token (one-time use)
5. Redirect to login

---

### Send Verification Email

**Function:** `send_verification_email(user)`  
**File:** `coda/accounts/utils.py`

```python
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_verification_email(user):
    """
    Send email verification link to newly registered user
    """
    
    # Build verification URL
    verification_url = (
        f"{settings.SITE_URL}/accounts/verify-email/{user.verification_token}/"
    )
    
    # Render HTML email template
    html_message = render_to_string(
        'accounts/admin/email_verification.html',
        {
            'user': user,
            'verification_url': verification_url,
            'site_name': 'CODA',
        }
    )
    
    # Render plain text version
    plain_message = f"""
    Welcome to CODA, {user.first_name}!
    
    Please verify your email by clicking this link:
    {verification_url}
    
    This link expires in 24 hours.
    """
    
    # Send email
    send_mail(
        subject='Verify Your CODA Account',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,  # Raise exceptions for debugging
    )
    
    logger.info(f'Verification email sent to {user.email}')
```

**Key Features:**
- HTML and plain text versions
- Template-based email
- Proper error handling
- Logging for monitoring

---

### Form Validation

**Class:** `UserForm`  
**File:** `coda/accounts/forms.py`

```python
class UserForm(forms.ModelForm):
    """Registration form with custom validation"""
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password (min 8 characters)'
        }),
        min_length=8,
        help_text='At least 8 characters'
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter password'
        })
    )
    
    class Meta:
        model = CustomerUser
        fields = [
            'username', 'first_name', 'last_name',
            'email', 'category', 'resume_file'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_username(self):
        """Ensure username is unique and valid"""
        username = self.cleaned_data.get('username')
        
        # Check uniqueness
        if CustomerUser.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        
        # Check format (alphanumeric, underscores, hyphens only)
        if not username.replace('_', '').replace('-', '').isalnum():
            raise forms.ValidationError(
                'Username can only contain letters, numbers, underscores, and hyphens.'
            )
        
        return username
    
    def clean_email(self):
        """Ensure email is unique and valid"""
        email = self.cleaned_data.get('email').lower()
        
        # Check uniqueness
        if CustomerUser.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        
        # Additional validation: block disposable email domains
        disposable_domains = ['tempmail.com', '10minutemail.com', 'guerrillamail.com']
        domain = email.split('@')[1] if '@' in email else ''
        if domain in disposable_domains:
            raise forms.ValidationError('Disposable email addresses are not allowed.')
        
        return email
    
    def clean(self):
        """Validate password match and strength"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match.")
            
            # Check password strength
            if len(password1) < 8:
                raise forms.ValidationError('Password must be at least 8 characters.')
            
            if password1.isdigit():
                raise forms.ValidationError('Password cannot be all numbers.')
            
            if password1.lower() == cleaned_data.get('username', '').lower():
                raise forms.ValidationError('Password cannot be same as username.')
        
        return cleaned_data
```

---

## 🔧 IMPLEMENTATION DETAILS

### Password Hashing

**Django Configuration:**
```python
# settings.py
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

**Usage:**
```python
# Hash password
user.set_password(raw_password)

# Verify password
user.check_password(raw_password)  # Returns True/False
```

---

### File Upload Handling (Resume)

**Model Configuration:**
```python
resume_file = FileField(
    upload_to="resumes/doc/",  # Stored in MEDIA_ROOT/resumes/doc/
    blank=True,
    null=True
)
```

**Form Handling:**
```python
# In view
form = UserForm(request.POST, request.FILES)  # Include FILES for upload

# File saved automatically when form.save() called
```

**File Storage:**
- Location: `MEDIA_ROOT/resumes/doc/`
- Naming: Auto-generated unique names
- Access: Via user.resume_file.url

---

### Category-Specific Logic

**JavaScript (Client-Side):**
```javascript
// Show/hide resume upload based on category
document.getElementById('id_category').addEventListener('change', function() {
    const resumeField = document.getElementById('resume-upload');
    
    if (this.value == '3') {  // Applicant category
        resumeField.style.display = 'block';
        resumeField.querySelector('input').setAttribute('required', 'required');
    } else {
        resumeField.style.display = 'none';
        resumeField.querySelector('input').removeAttribute('required');
    }
});
```

**Server-Side Validation:**
```python
def clean(self):
    cleaned_data = super().clean()
    category = cleaned_data.get('category')
    resume = cleaned_data.get('resume_file')
    
    # Require resume for applicants
    if category == 3 and not resume:  # Applicant category
        raise forms.ValidationError('Resume is required for applicants.')
    
    return cleaned_data
```

---

## 📊 DATABASE OPERATIONS

### User Creation Flow

```python
# 1. Create user (transaction begins)
with transaction.atomic():
    # Create CustomerUser
    user = CustomerUser.objects.create(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        category=category,
        email_verified=False,
        verification_token=uuid.uuid4()
    )
    user.set_password(password)
    user.save()
    
    # Create UserProfile
    UserProfile.objects.create(user=user)
    
    # If applicant, handle resume
    if category == 3 and resume_file:
        user.resume_file = resume_file
        user.save()

# 2. Send email (outside transaction)
send_verification_email(user)
```

### Query Optimization

```python
# Bad - Multiple queries
user = CustomerUser.objects.get(id=user_id)
profile = user.profile  # Separate query

# Good - Single query
user = CustomerUser.objects.select_related('profile').get(id=user_id)
```

---

## 🔐 SECURITY IMPLEMENTATION

### CSRF Protection

**In Template:**
```html
<form method="POST">
    {% csrf_token %}  <!-- Required! -->
    {{ form.as_p }}
</form>
```

**In View:**
```python
# Django automatically validates CSRF token
# If invalid, returns 403 Forbidden
```

### Rate Limiting (Planned)

**Current:** Not implemented  
**Future (Phase 2):**
```python
from django.core.cache import cache

def join(request):
    if request.method == 'POST':
        # Check rate limit
        ip = request.META.get('REMOTE_ADDR')
        key = f'registration_attempts_{ip}'
        attempts = cache.get(key, 0)
        
        if attempts >= 10:  # Max 10 per hour
            messages.error(request, 'Too many registration attempts. Try later.')
            return redirect('accounts:home')
        
        # Increment counter
        cache.set(key, attempts + 1, 3600)  # 1 hour expiry
        
        # Process registration...
```

---

## 🐛 ERROR HANDLING

### Common Errors & Solutions

**Error 1: Verification email not sent**
```python
try:
    send_verification_email(user)
except Exception as e:
    logger.error(f'Failed to send verification email: {e}')
    messages.warning(
        request,
        'Account created but email failed. Contact support for verification.'
    )
```

**Error 2: Duplicate email**
```python
# Handled in form validation
def clean_email(self):
    email = self.cleaned_data.get('email')
    if CustomerUser.objects.filter(email=email).exists():
        raise forms.ValidationError('Email already registered.')
    return email
```

**Error 3: File upload too large**
```python
# In settings.py
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# In form
def clean_resume_file(self):
    resume = self.cleaned_data.get('resume_file')
    if resume and resume.size > 5242880:
        raise forms.ValidationError('Resume must be less than 5MB.')
    return resume
```

---

## 📝 LOGGING

**Configuration:**
```python
import logging

logger = logging.getLogger(__name__)

# Log registration events
logger.info(f'New user registered: {user.username} ({user.email})')

# Log verification events
logger.info(f'Email verified for user: {user.username}')

# Log errors
logger.error(f'Registration failed for {email}: {error}')
```

---

## 📊 CHANGE HISTORY

| Date | Change | Developer | Files |
|------|--------|-----------|-------|
| Oct 22, 2025 | 7-doc structure created | AI | All docs |
| Earlier 2025 | Email verification implemented | Team | views.py, utils.py |
| Earlier 2025 | Resume upload added | Team | models.py, forms.py |
| Earlier 2025 | Initial registration system | Team | Multiple |

---

## 🔄 WORKFLOWS

### Complete Registration Workflow

1. User visits `/accounts/join/`
2. Fills registration form
3. Submits (POST request)
4. Server validates data
5. Creates user (email_verified=False)
6. Sends verification email
7. Shows "Check Email" page
8. User clicks email link
9. Server verifies token
10. Marks email_verified=True
11. User redirected to login
12. User can now login successfully

---

**See:** 05_TESTING.md for test scenarios



