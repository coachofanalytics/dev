# Profile Management - Architecture

**Feature:** User Profiles & Settings  
**Status:** Phase 1 Complete, Phase 2 Designed  
**Last Updated:** October 22, 2025

---

## 🏗️ SYSTEM ARCHITECTURE

### Data Model Structure

```
CustomerUser (Core Model)
    ↓ OneToOne
UserProfile (Extended Info)
    ↓ Optional
ProfilePicture (Phase 2)
    ↓ Optional
NotificationPreferences (Phase 2)
    ↓ Optional
PrivacySettings (Phase 2)
```

---

## 📊 DATA MODELS

### CustomerUser (Profile Core)

**File:** `coda/accounts/models.py`

```python
class CustomerUser(AbstractUser):
    """User model with profile fields"""
    
    # Basic Info (from AbstractUser)
    username = CharField(max_length=150, unique=True)
    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)
    email = CharField(max_length=255)
    
    # Contact Info
    phone = CharField(default="90001", max_length=255)
    address = CharField(blank=True, null=True, max_length=255)
    city = CharField(blank=True, null=True, max_length=255)
    state = CharField(blank=True, null=True, max_length=255)
    zipcode = CharField(blank=True, null=True, max_length=255)
    country = CountryField(blank=True, null=True)
    
    # Demographics
    gender = IntegerField(choices=Score.choices, blank=True, null=True)
    
    # Category/Role
    category = IntegerField(choices=CategoryChoices.choices, default=999)
    sub_category = IntegerField(blank=True, null=True)
    
    # File Uploads
    resume_file = FileField(upload_to="resumes/doc/", blank=True, null=True)
    
    # Computed Properties
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def user_details(self):
        return f"Username: {self.username}\nPhone: {self.phone}\nEmail: {self.email}\nCity: {self.city}"
    
    @property
    def tenure(self):
        """Months since joining"""
        days = (timezone.now().date() - self.date_joined.date()).days
        return days / 30
```

---

### UserProfile (Extended Information)

**File:** `coda/accounts/models.py`

```python
class UserProfile(models.Model):
    """Extended user profile information"""
    
    user = OneToOneField(
        CustomerUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Professional (Employees)
    job_title = CharField(max_length=200, blank=True, null=True)
    department = ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    manager = ForeignKey(
        CustomerUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_employees'
    )
    hire_date = DateField(null=True, blank=True)
    
    # Business (Clients)
    company_name = CharField(max_length=200, blank=True, null=True)
    industry = CharField(max_length=100, blank=True, null=True)
    account_manager = ForeignKey(
        CustomerUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_clients'
    )
    
    # Skills (Applicants)
    skills = TextField(blank=True, null=True)  # JSON or comma-separated
    experience_years = IntegerField(blank=True, null=True)
    education = TextField(blank=True, null=True)
    
    # Social Links (Phase 2)
    linkedin_url = URLField(blank=True, null=True)
    github_url = URLField(blank=True, null=True)
    twitter_url = URLField(blank=True, null=True)
    
    # Metadata
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    @property
    def is_complete(self):
        """Check if profile is fully filled"""
        required = [self.user.phone, self.user.city]
        return all(required)
    
    @property
    def completion_percentage(self):
        """Calculate profile completion 0-100%"""
        fields = [
            self.user.phone, self.user.address, self.user.city,
            self.user.state, self.user.zipcode, self.user.country,
            self.user.gender, self.job_title, self.company_name
        ]
        filled = sum(1 for field in fields if field)
        return int((filled / len(fields)) * 100)
```

---

### Phase 2 Models (Planned)

#### ProfilePicture Model
```python
class ProfilePicture(models.Model):
    """User profile pictures"""
    
    user = OneToOneField(CustomerUser, on_delete=models.CASCADE)
    image = ImageField(upload_to='profile_pictures/')
    thumbnail = ImageField(upload_to='profile_pictures/thumbnails/')
    uploaded_at = DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        """Auto-generate thumbnail"""
        if self.image:
            # Resize to 200x200
            self.thumbnail = resize_image(self.image, (200, 200))
        super().save(*args, **kwargs)
```

#### NotificationPreferences Model
```python
class NotificationPreferences(models.Model):
    """User notification settings"""
    
    user = OneToOneField(CustomerUser, on_delete=models.CASCADE)
    
    # Email Preferences
    email_on_comment = BooleanField(default=True)
    email_on_mention = BooleanField(default=True)
    email_on_task_assigned = BooleanField(default=True)
    email_on_payment = BooleanField(default=True)
    email_digest_frequency = CharField(
        max_length=20,
        choices=[
            ('never', 'Never'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='daily'
    )
    
    # SMS Preferences
    sms_enabled = BooleanField(default=False)
    sms_on_urgent = BooleanField(default=False)
    
    # In-App
    in_app_notifications = BooleanField(default=True)
```

#### PrivacySettings Model
```python
class PrivacySettings(models.Model):
    """User privacy controls"""
    
    user = OneToOneField(CustomerUser, on_delete=models.CASCADE)
    
    # Profile Visibility
    profile_visibility = CharField(
        max_length=20,
        choices=[
            ('public', 'Everyone'),
            ('colleagues', 'CODA Colleagues Only'),
            ('private', 'Only Me'),
        ],
        default='colleagues'
    )
    
    # Field-Level Privacy
    show_email = BooleanField(default=False)
    show_phone = BooleanField(default=True)
    show_address = BooleanField(default=False)
    
    # Activity Privacy
    show_in_search = BooleanField(default=True)
    show_login_status = BooleanField(default=True)
```

---

## 🔄 DATA FLOW

### Profile Update Flow

```
User Views Profile
    ↓
Clicks "Edit Profile"
    ↓
profile_update View Loads Form
    ↓
User Updates Fields
    ↓
Submits Form (POST)
    ↓
UserProfileUpdateView validates
    ↓
Save to UserProfile model
    ↓
Save to CustomerUser model (if changed)
    ↓
Success Message
    ↓
Redirect to Profile View
    ↓
Changes Reflected
```

---

## 🖥️ VIEWS & URLs

### Current Views

**File:** `coda/accounts/views.py`

```python
@login_required
def profile(request, username):
    """View user profile"""
    user = get_object_or_404(CustomerUser, username=username)
    
    # Privacy check
    if user != request.user and not request.user.is_staff:
        return HttpResponseForbidden()
    
    context = {
        'profile_user': user,
        'profile': user.profile,
    }
    return render(request, 'accounts/profile.html', context)

class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Edit user profile"""
    model = CustomerUser
    fields = ['first_name', 'last_name', 'phone', 'address', 'city', 'state', 'zipcode', 'country', 'gender']
    template_name = 'accounts/admin/user_update_form.html'
    
    def get_success_url(self):
        return reverse('accounts:account-profile', kwargs={'username': self.object.username})
```

---

### URLs

```python
path("profile/<str:username>", views.profile, name="account-profile"),
path("profile/<int:pk>/update/", UserProfileUpdateView.as_view(), name="profile-update"),
```

---

## 🎨 TEMPLATES

**File:** `coda/accounts/templates/accounts/profile.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="profile-container">
    <div class="profile-header">
        <div class="profile-picture">
            <!-- Phase 2: Show uploaded picture -->
            <!-- Phase 1: Show initials -->
            <div class="avatar">{{ profile_user.first_name.0 }}{{ profile_user.last_name.0 }}</div>
        </div>
        
        <div class="profile-info">
            <h1>{{ profile_user.full_name }}</h1>
            <p>@{{ profile_user.username }}</p>
            <p>{{ profile_user.get_category_display_name }}</p>
        </div>
        
        {% if request.user == profile_user %}
        <a href="{% url 'accounts:profile-update' profile_user.id %}" class="btn-edit">
            Edit Profile
        </a>
        {% endif %}
    </div>
    
    <div class="profile-details">
        <h3>Contact Information</h3>
        <ul>
            <li><strong>Email:</strong> {{ profile_user.email }}</li>
            <li><strong>Phone:</strong> {{ profile_user.phone }}</li>
            <li><strong>City:</strong> {{ profile_user.city }}</li>
            <li><strong>Country:</strong> {{ profile_user.country.name }}</li>
        </ul>
        
        {% if profile_user.is_staff %}
        <h3>Employment</h3>
        <ul>
            <li><strong>Department:</strong> {{ profile_user.profile.department }}</li>
            <li><strong>Tenure:</strong> {{ profile_user.tenure|floatformat:1 }} months</li>
        </ul>
        {% endif %}
        
        {% if profile_user.resume_file %}
        <h3>Resume</h3>
        <a href="{{ profile_user.resume_file.url }}" class="btn">Download Resume</a>
        {% endif %}
    </div>
</div>
{% endblock %}
```

---

## 📝 FORMS

### ProfileUpdateForm (Current)

Used by `UserProfileUpdateView` - ModelForm using CustomerUser fields

### ProfilePictureForm (Phase 2)

```python
class ProfilePictureForm(forms.ModelForm):
    """Upload and crop profile picture"""
    
    class Meta:
        model = ProfilePicture
        fields = ['image']
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        
        # Validate file type
        if not image.name.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            raise forms.ValidationError('Only JPG, PNG, GIF allowed')
        
        # Validate file size (max 2MB)
        if image.size > 2097152:
            raise forms.ValidationError('Image must be less than 2MB')
        
        return image
```

---

## 🔐 SECURITY ARCHITECTURE

### Access Control

```python
# Users can only edit own profile
def dispatch(self, request, *args, **kwargs):
    obj = self.get_object()
    if obj != request.user and not request.user.is_staff:
        return HttpResponseForbidden()
    return super().dispatch(request, *args, **kwargs)
```

### Data Validation

All fields validated before save:
- Phone: Format check
- Email: Uniqueness + format
- Country: Valid country code
- File uploads: Type and size validation

---

**See:** 04_IMPLEMENTATION.md for code details



