from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Category(models.Model):
    """
    Dynamic registration categories that can be managed by superadmin.
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(max_length=200, blank=True)
    icon = models.CharField(max_length=50, default='bi-tag', help_text='Bootstrap icon class')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Role(models.Model):
    """
    Staff roles with different permissions.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=300, blank=True)
    can_manage_users = models.BooleanField(default=False, help_text='Can add, edit, delete users')
    can_manage_categories = models.BooleanField(default=False, help_text='Can add, edit, delete categories')
    can_manage_staff = models.BooleanField(default=False, help_text='Can add, edit, delete staff members')
    can_view_reports = models.BooleanField(default=True, help_text='Can view system reports')
    can_moderate_content = models.BooleanField(default=False, help_text='Can moderate user content')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['name']

    def __str__(self):
        return self.name


class Staff(models.Model):
    """
    Internal staff members with assigned roles.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='staff_members')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    hired_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text='Internal notes about this staff member')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Staff'
        verbose_name_plural = 'Staff'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.role}"


class UserProfile(models.Model):
    """
    Extended user profile model with category and document upload.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    # Profile Image
    profile_image = models.ImageField(
        upload_to='profile_images/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text='Upload your profile picture'
    )

    # Documents
    document = models.FileField(
        upload_to='user_documents/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text='Upload your resume (for individuals), business profile (for businesses), or portfolio (for investors)'
    )

    # Basic Information
    bio = models.TextField(max_length=500, blank=True, help_text='Tell us about yourself or your business')
    company_name = models.CharField(max_length=200, blank=True, help_text='Company or Organization name')
    job_title = models.CharField(max_length=100, blank=True, help_text='Your current job title or position')

    # Contact Information
    country = models.CharField(max_length=100, blank=True, help_text='Country')
    phone = models.CharField(max_length=20, blank=True, help_text='Contact phone number')
    alternate_email = models.EmailField(max_length=200, blank=True, help_text='Alternative email address')
    location = models.CharField(max_length=100, blank=True, help_text='City, Country')
    address = models.TextField(max_length=300, blank=True, help_text='Full address (optional)')

    # Online Presence
    website = models.URLField(max_length=200, blank=True, help_text='Your website or company website')
    linkedin_url = models.URLField(max_length=200, blank=True, help_text='LinkedIn profile URL')
    twitter_handle = models.CharField(max_length=50, blank=True, help_text='Twitter username (without @)')
    facebook_url = models.URLField(max_length=200, blank=True, help_text='Facebook profile or page URL')

    # Professional Details
    years_of_experience = models.IntegerField(blank=True, null=True, help_text='Years of professional experience')
    industry = models.CharField(max_length=100, blank=True, help_text='Industry or sector')
    skills = models.TextField(max_length=500, blank=True, help_text='Your skills or areas of expertise (comma separated)')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['-created_at']

    def __str__(self):
        category_name = self.category.name if self.category else 'No Category'
        return f"{self.user.username} - {category_name}"

    @property
    def dashboard_url(self):
        """
        Return the appropriate dashboard URL name based on user category.
        """
        if not self.category:
            return 'home'

        dashboard_urls = {
            'investor': 'investor_dashboard',
            'business': 'business_dashboard',
            'individual': 'individual_dashboard',
        }
        return dashboard_urls.get(self.category.slug, 'home')


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a UserProfile when a new User is created.
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile when the User is saved.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
