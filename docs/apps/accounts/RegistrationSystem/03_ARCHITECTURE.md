# Registration System - Architecture

**Feature:** User Registration & Onboarding  
**Status:** ✅ Production Ready  
**Last Updated:** October 22, 2025

---

## 🏗️ SYSTEM ARCHITECTURE

### High-Level Architecture

```
User Browser
     ↓
Registration Form (/accounts/join/)
     ↓
Django View (join)
     ↓
UserForm Validation
     ↓
CustomerUser Model
     ↓
Email Verification Service
     ↓
Verification Email Sent
     ↓
User Clicks Link
     ↓
verify_email View
     ↓
Email Marked Verified
     ↓
User Can Login
```

---

## 📊 DATA MODELS

### CustomerUser Model (Registration Fields)

**File:** `coda/accounts/models.py`

```python
class CustomerUser(AbstractUser):
    """
    Extended user model for registration
    Inherits from Django's AbstractUser
    """
    
    # Primary Key
    id = AutoField(primary_key=True)
    
    # Registration Required Fields
    username = CharField(max_length=150, unique=True)  # From AbstractUser
    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)
    email = CharField(max_length=255)  # Must be unique
    password = CharField(max_length=128)  # From AbstractUser (hashed)
    
    # Category Selection
    category = IntegerField(
        choices=CategoryChoices.choices,
        default=999  # Unknown
    )
    sub_category = IntegerField(blank=True, null=True)
    
    # Email Verification
    email_verified = BooleanField(default=False)
    verification_token = UUIDField(unique=True, null=True, blank=True)
    
    # Resume (Applicants)
    resume_file = FileField(
        upload_to="resumes/doc/",
        blank=True,
        null=True
    )
    
    # Metadata
    date_joined = DateTimeField(default=timezone.now)
    is_active = BooleanField(default=True)
    
    class Meta:
        ordering = ["username"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
            models.Index(fields=["email_verified"]),
            models.Index(fields=["category", "sub_category"]),
        ]
```

### Category Choices

**File:** `coda/accounts/choices.py`

```python
class UserCategory(models.IntegerChoices):
    """User category choices for registration"""
    
    EMPLOYEE = 1, "Employee"
    CLIENT = 2, "Client"
    APPLICANT = 3, "Applicant"
    INVESTOR = 4, "Investor"
    UNKNOWN = 999, "Unknown"
```

### UserProfile Model (Created Post-Registration)

**File:** `coda/accounts/models.py`

```python
class UserProfile(models.Model):
    """
    Extended profile information
    Created automatically after registration
    """
    
    user = OneToOneField(
        CustomerUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Contact Information
    phone = CharField(max_length=255, default="90001")
    address = CharField(max_length=255, blank=True, null=True)
    city = CharField(max_length=255, blank=True, null=True)
    state = CharField(max_length=255, blank=True, null=True)
    zipcode = CharField(max_length=255, blank=True, null=True)
    country = CountryField(blank=True, null=True)
    
    # Demographics
    gender = IntegerField(
        choices=CustomerUser.Score.choices,
        blank=True,
        null=True
    )
    
    # Computed Properties
    @property
    def is_complete(self):
        """Check if profile is fully filled"""
        required_fields = [self.phone, self.city]
        return all(required_fields)
```

---

## 🔄 DATA FLOW

### Registration Flow (Detailed)

```
Step 1: User Visits /accounts/join/
    ↓
Step 2: Django renders join.html template
    ↓
Step 3: User fills form:
    - Username
    - First Name, Last Name
    - Email
    - Password, Password Confirmation
    - Category (Employee/Client/Applicant/Investor)
    - Resume (if Applicant)
    ↓
Step 4: User submits form (POST request)
    ↓
Step 5: join() view processes request:
    a) Validate form data (UserForm)
    b) Check username uniqueness
    c) Check email uniqueness
    d) Validate password strength
    e) Check CSRF token
    ↓
Step 6: If validation passes:
    a) Create CustomerUser record
    b) Hash password (PBKDF2 with 260K iterations)
    c) Generate verification token (UUID4)
    d) Set email_verified = False
    e) Save user to database
    ↓
Step 7: Create UserProfile record
    a) Link to CustomerUser
    b) Set default values
    ↓
Step 8: Send verification email
    a) Get email template
    b) Generate verification link
    c) Send via Django email backend
    ↓
Step 9: Redirect to email verification notice
    ↓
Step 10: User receives email
    ↓
Step 11: User clicks verification link
    ↓
Step 12: verify_email() view:
    a) Extract token from URL
    b) Find user by token
    c) Set email_verified = True
    d) Clear verification token
    e) Save user
    ↓
Step 13: Display success message
    ↓
Step 14: Redirect to login page
    ↓
Step 15: User can now login
```

---

## 🖥️ VIEWS & URLS

### Registration View

**File:** `coda/accounts/views.py`

```python
def join(request):
    """
    User registration view
    Handles both GET (display form) and POST (process registration)
    """
    
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Create user (don't save yet)
            user = form.save(commit=False)
            
            # Hash password
            user.set_password(form.cleaned_data['password'])
            
            # Generate verification token
            user.verification_token = uuid.uuid4()
            user.email_verified = False
            
            # Save user
            user.save()
            
            # Create UserProfile
            UserProfile.objects.create(user=user)
            
            # Send verification email
            send_verification_email(user)
            
            # Redirect to verification notice
            return redirect('accounts:email-verification-notice', user_id=user.id)
        
    else:
        form = UserForm()
    
    return render(request, 'accounts/registration/join.html', {'form': form})
```

### Email Verification View

```python
def verify_email(request, token):
    """
    Email verification handler
    Validates token and marks email as verified
    """
    
    try:
        user = CustomerUser.objects.get(verification_token=token)
        user.email_verified = True
        user.verification_token = None
        user.save()
        
        messages.success(request, "Email verified successfully! You can now login.")
        return redirect('accounts:account-login')
        
    except CustomerUser.DoesNotExist:
        messages.error(request, "Invalid verification token.")
        return redirect('accounts:home')
```

### URL Configuration

**File:** `coda/accounts/urls.py`

```python
urlpatterns = [
    # Registration
    path("join/", views.join, name="join"),
    
    # Email Verification
    path(
        "verify-email/<uuid:token>/",
        verify_email,
        name="verify-email"
    ),
    path(
        "email-verification-notice/<int:user_id>/",
        views.email_verification_notice,
        name="email-verification-notice"
    ),
    
    # Resend verification
    path(
        "populate-tokens/",
        populate_tokens_view,
        name="populate_tokens"
    ),
]
```

---

## 🎨 TEMPLATES

### Registration Form Template

**File:** `coda/accounts/templates/accounts/registration/join.html`

**Structure:**
```html
{% extends "base.html" %}

{% block content %}
<div class="registration-container">
    <h1>Create Your Account</h1>
    
    <form method="POST" enctype="multipart/form-data">
        {% csrf_token %}
        
        <!-- Username -->
        {{ form.username }}
        
        <!-- Name Fields -->
        {{ form.first_name }}
        {{ form.last_name }}
        
        <!-- Email -->
        {{ form.email }}
        
        <!-- Password -->
        {{ form.password1 }}
        {{ form.password2 }}
        
        <!-- Category -->
        {{ form.category }}
        
        <!-- Resume (conditional - for applicants) -->
        <div id="resume-upload" style="display: none;">
            {{ form.resume_file }}
        </div>
        
        <!-- Submit -->
        <button type="submit">Register</button>
    </form>
</div>

<script>
// Show resume upload for applicants
document.getElementById('id_category').addEventListener('change', function() {
    if (this.value == '3') {  // Applicant category
        document.getElementById('resume-upload').style.display = 'block';
    } else {
        document.getElementById('resume-upload').style.display = 'none';
    }
});
</script>
{% endblock %}
```

### Email Verification Notice

**File:** `coda/accounts/templates/accounts/registration/email_verification_notice.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="verification-notice">
    <h1>Please Verify Your Email</h1>
    
    <p>We've sent a verification email to: <strong>{{ user.email }}</strong></p>
    
    <p>Please check your inbox and click the verification link to activate your account.</p>
    
    <div class="help-text">
        <h3>Didn't receive the email?</h3>
        <ul>
            <li>Check your spam/junk folder</li>
            <li>Wait a few minutes (delivery can take up to 5 minutes)</li>
            <li><a href="{% url 'accounts:populate_tokens' %}">Resend verification email</a></li>
        </ul>
    </div>
</div>
{% endblock %}
```

### Verification Email Template

**File:** `coda/accounts/templates/accounts/admin/email_verification.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Verify Your CODA Account</title>
</head>
<body>
    <h2>Welcome to CODA, {{ user.first_name }}!</h2>
    
    <p>Thank you for registering. Please click the link below to verify your email address:</p>
    
    <p>
        <a href="{{ verification_url }}" style="
            background-color: #4CAF50;
            color: white;
            padding: 14px 20px;
            text-decoration: none;
            border-radius: 4px;
        ">Verify Email Address</a>
    </p>
    
    <p>Or copy and paste this link into your browser:</p>
    <p>{{ verification_url }}</p>
    
    <p>This link will expire in 24 hours.</p>
    
    <p>
        If you did not create this account, please ignore this email.
    </p>
    
    <p>
        Best regards,<br>
        The CODA Team
    </p>
</body>
</html>
```

---

## 📝 FORMS

### UserForm

**File:** `coda/accounts/forms.py`

```python
from django import forms
from .models import CustomerUser

class UserForm(forms.ModelForm):
    """
    Registration form with validation
    """
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        min_length=8
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput
    )
    
    class Meta:
        model = CustomerUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'category',
            'sub_category',
            'resume_file',
        ]
    
    def clean_username(self):
        """Validate username uniqueness"""
        username = self.cleaned_data.get('username')
        if CustomerUser.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already taken")
        return username
    
    def clean_email(self):
        """Validate email uniqueness and format"""
        email = self.cleaned_data.get('email')
        if CustomerUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered")
        return email.lower()
    
    def clean(self):
        """Validate password match"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data
```

---

## 🔐 SECURITY ARCHITECTURE

### Password Hashing

**Algorithm:** PBKDF2 with SHA256  
**Iterations:** 260,000  
**Salt:** Random per user

```python
# Django settings
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

# Usage in code
user.set_password(raw_password)  # Automatically hashes
```

### Verification Token Generation

```python
import uuid

# Generate cryptographically random token
user.verification_token = uuid.uuid4()

# Token format: 
# Example: 550e8400-e29b-41d4-a716-446655440000
```

### CSRF Protection

```html
<form method="POST">
    {% csrf_token %}  <!-- Required on all forms -->
    ...
</form>
```

---

## 📧 EMAIL SYSTEM

### Email Backend Configuration

**File:** `coda_project/settings.py`

```python
# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'noreply@codanalytics.net'
```

### Send Verification Email Function

**File:** `coda/accounts/utils.py`

```python
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_verification_email(user):
    """Send email verification link to user"""
    
    # Generate verification URL
    verification_url = f"{settings.SITE_URL}/accounts/verify-email/{user.verification_token}/"
    
    # Render email template
    html_message = render_to_string(
        'accounts/admin/email_verification.html',
        {
            'user': user,
            'verification_url': verification_url,
        }
    )
    
    # Send email
    send_mail(
        subject='Verify Your CODA Account',
        message='',  # Plain text version
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
```

---

## 🔄 STATE DIAGRAM

```
┌─────────────┐
│   Visitor   │
└──────┬──────┘
       │
       ↓ (Clicks Register)
┌─────────────────┐
│ Registration    │
│ Form Displayed  │
└──────┬──────────┘
       │
       ↓ (Submits Form)
┌─────────────────┐
│  Validation     │
└──────┬──────────┘
       │
       ├─ Invalid → Show Errors → Back to Form
       │
       ↓ Valid
┌─────────────────┐
│ User Created    │
│ email_verified  │
│ = False         │
└──────┬──────────┘
       │
       ↓
┌─────────────────┐
│ Verification    │
│ Email Sent      │
└──────┬──────────┘
       │
       ↓ (User clicks link)
┌─────────────────┐
│ Email Verified  │
│ email_verified  │
│ = True          │
└──────┬──────────┘
       │
       ↓
┌─────────────────┐
│ Can Login       │
│ (Active User)   │
└─────────────────┘
```

---

## 📊 DATABASE SCHEMA

### Tables Involved

1. **accounts_customeruser**
   - Primary registration data
   - Indexed on: email, username, email_verified

2. **accounts_userprofile**
   - Extended user information
   - One-to-one with CustomerUser

3. **django_session** (Django built-in)
   - Session management post-login

---

## 🔌 INTEGRATIONS

### Current Integrations:
- ✅ Django authentication system
- ✅ Django email system
- ✅ File upload (resume storage)

### Future Integrations (Phase 2-3):
- ⏳ AI duplicate detection service
- ⏳ Resume parsing API
- ⏳ Email validation service (ZeroBounce)
- ⏳ LinkedIn API (profile import)
- ⏳ Google OAuth (social registration)

---

**See:** 04_IMPLEMENTATION.md for code details and file locations



